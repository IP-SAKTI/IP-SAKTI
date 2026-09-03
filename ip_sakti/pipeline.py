"""
ip_sakti.pipeline — Core Pipeline Coordinator.

Wires together the full IP-SAKTI Sahayak core application workflow:
  QueryRequest
    │
    ▼
  Stage 2: MultilingualService (Language Detection, Normalization, Translation)
    │
    ▼
  Stage 4: Orchestrator (Intent, Jurisdiction, Formulation classification -> QueryContext)
    │
    ▼
  Stage 4: RuleEngine (YAML rule evaluation)
    │
    ▼
  Stage 4: AgentRouter (Routes to IPAgent, RegulatoryAgent, or TKABSAgent)
    │
    ▼
  Stage 4: Specialist Agent(s) -> Stage 3 HybridRAGPipeline (FAISS + BM25 -> RRF -> Reranker)
    │
    ▼
  Stage 4: AnswerSynthesisService (Gemini LLM -> Citation Validation -> Confidence Assessment -> Safe Abstention)
    │
    ▼
  Stage 2: Response Translation (translates answer back to user language if non-English)
    │
    ▼
  FinalResponse
"""

from __future__ import annotations

import logging
from typing import Sequence

from ip_sakti.agents import BaseAgent, IPAgent, RegulatoryAgent, TKABSAgent
from ip_sakti.llm import AnswerSynthesisService
from ip_sakti.models.query import AgentType, EvidenceChunk, FinalResponse, QueryRequest
from ip_sakti.multilingual import MultilingualService
from ip_sakti.orchestrator import Orchestrator
from ip_sakti.retrieval import HybridRAGPipeline
from ip_sakti.rule_engine import AgentRouter, RuleEngine

logger = logging.getLogger(__name__)


class PipelineCoordinator:
    """
    Coordinates end-to-end query execution across Multilingual, Orchestration,
    Rule Engine, Specialist Agents, Hybrid RAG, and LLM Synthesis layers.
    """

    def __init__(
        self,
        multilingual_service: MultilingualService | None = None,
        orchestrator: Orchestrator | None = None,
        rule_engine: RuleEngine | None = None,
        agent_router: AgentRouter | None = None,
        rag_pipeline: HybridRAGPipeline | None = None,
        synthesis_service: AnswerSynthesisService | None = None,
        agents: dict[AgentType, BaseAgent] | None = None,
    ) -> None:
        """Initialise pipeline coordinator with optional component overrides."""
        self.multilingual_service = multilingual_service or MultilingualService()
        self.orchestrator = orchestrator or Orchestrator()
        self.rule_engine = rule_engine or RuleEngine()
        self.agent_router = agent_router or AgentRouter()
        self.rag_pipeline = rag_pipeline or HybridRAGPipeline()
        self.synthesis_service = synthesis_service or AnswerSynthesisService()

        # Specialist agents mapping
        if agents is not None:
            self.agents = agents
        else:
            self.agents = {
                AgentType.IP_AGENT: IPAgent(),
                AgentType.REGULATORY_AGENT: RegulatoryAgent(),
                AgentType.TK_ABS_AGENT: TKABSAgent(),
            }

        logger.debug("PipelineCoordinator initialised")

    def execute(self, request: QueryRequest) -> FinalResponse:
        """
        Execute full end-to-end pipeline for an incoming QueryRequest.

        Parameters
        ----------
        request :
            Incoming QueryRequest model.

        Returns
        -------
        FinalResponse
            Source-grounded answer or safe abstention response with metadata.
        """
        logger.info(
            "Executing core pipeline",
            extra={"query_id": str(request.query_id), "raw_query": request.raw_query[:50]},
        )

        # Step 1: Multilingual Layer (Detection, Normalization, Query Translation)
        m_ctx = self.multilingual_service.process(request)

        # Step 2: Orchestrator (Classification -> QueryContext)
        q_ctx = self.orchestrator.process(request, m_ctx)

        # Step 3: Rule Engine Evaluation
        applied_rules = self.rule_engine.evaluate_rules(q_ctx)

        # Step 4: Agent Routing
        target_agent_types = self.agent_router.route(q_ctx)

        # Step 5: Specialist Agent Execution & Evidence Retrieval
        collected_evidence: list[EvidenceChunk] = []
        seen_chunk_ids: set[str] = set()
        primary_agent_type: AgentType = target_agent_types[0] if target_agent_types else AgentType.IP_AGENT

        for agent_type in target_agent_types:
            agent = self.agents.get(agent_type)
            if agent is None:
                logger.warning(f"Agent for type {agent_type.value} not registered in coordinator.")
                continue

            agent_result = agent.process(
                context=q_ctx,
                pipeline=self.rag_pipeline,
                applied_rules=applied_rules,
            )

            for chunk in agent_result.evidence:
                if chunk.chunk_id not in seen_chunk_ids:
                    seen_chunk_ids.add(chunk.chunk_id)
                    collected_evidence.append(chunk)

        # Step 6: LLM Synthesis & Safety Validation
        final_response = self.synthesis_service.synthesize(
            context=q_ctx,
            evidence=collected_evidence,
            agent_type=primary_agent_type,
            applied_rules=applied_rules,
        )

        # Step 7: Response Translation (if user language is non-English and not an abstention)
        if (
            not final_response.is_abstention
            and m_ctx.effective_language != "en"
            and final_response.answer
        ):
            try:
                updated_m_ctx = self.multilingual_service.translate_response(
                    response_text=final_response.answer,
                    context=m_ctx,
                )
                if (
                    updated_m_ctx.response_translation
                    and updated_m_ctx.response_translation.was_translated
                ):
                    final_response = final_response.model_copy(
                        update={"answer": updated_m_ctx.response_translation.translated_text}
                    )
            except Exception as exc:
                logger.error(f"Response translation failed: {exc}")

        logger.info(
            "Pipeline execution completed",
            extra={
                "query_id": str(request.query_id),
                "is_abstention": final_response.is_abstention,
                "evidence_count": len(final_response.evidence),
            },
        )
        return final_response

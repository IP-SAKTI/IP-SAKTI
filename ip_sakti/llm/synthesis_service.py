"""
ip_sakti.llm.synthesis_service — End-to-end response synthesis & validation service.

Wired together:
  GeminiLLMAdapter (LLM Answer Generation)
    │
    ▼
  CitationValidator (Evidence Grounding)
    │
    ▼
  ConfidenceAssessor (Score & Threshold Evaluation)
    │
    ├── [High Confidence] ──> FinalResponse (Answer)
    └── [Low Confidence]  ──> SafeAbstentionHandler (Safe Abstention & Escalation)
"""

from __future__ import annotations

import logging
from typing import Sequence

from ip_sakti.llm.abstention import SafeAbstentionHandler
from ip_sakti.llm.citation_validator import CitationValidator
from ip_sakti.llm.confidence_assessor import ConfidenceAssessor
from ip_sakti.llm.gemini_adapter import GeminiLLMAdapter
from ip_sakti.models.query import AgentType, EvidenceChunk, FinalResponse, QueryContext

logger = logging.getLogger(__name__)


class AnswerSynthesisService:
    """
    Coordinates LLM generation, citation validation, confidence calculation,
    and safe abstention fallback.
    """

    def __init__(
        self,
        llm_adapter: GeminiLLMAdapter | None = None,
        citation_validator: CitationValidator | None = None,
        confidence_assessor: ConfidenceAssessor | None = None,
        abstention_handler: SafeAbstentionHandler | None = None,
    ) -> None:
        """Initialise synthesis service with optional injections."""
        self.llm_adapter = llm_adapter or GeminiLLMAdapter()
        self.citation_validator = citation_validator or CitationValidator()
        self.confidence_assessor = confidence_assessor or ConfidenceAssessor()
        self.abstention_handler = abstention_handler or SafeAbstentionHandler()

    def synthesize(
        self,
        context: QueryContext,
        evidence: Sequence[EvidenceChunk],
        agent_type: AgentType | None = None,
        applied_rules: Sequence[str] | None = None,
    ) -> FinalResponse:
        """
        Generate and validate response for QueryContext and retrieved EvidenceChunk list.

        Parameters
        ----------
        context :
            Enriched QueryContext model.
        evidence :
            Retrieved evidence chunks from Stage 3 RAG.
        agent_type :
            Specialist agent originating the retrieval.
        applied_rules :
            Domain guidance rules.

        Returns
        -------
        FinalResponse
            Final response object with answer or safe abstention.
        """
        logger.info(
            "Synthesizing answer",
            extra={"query_id": str(context.query_id), "evidence_count": len(evidence)},
        )

        if not evidence:
            return self.abstention_handler.handle_abstention(
                query_id=context.query_id,
                reason="No evidence chunks retrieved from knowledge base.",
                agent_type=agent_type,
            )

        # 1. LLM Answer Generation
        raw_answer = self.llm_adapter.generate_answer(
            context=context,
            evidence=evidence,
            applied_rules=applied_rules,
        )

        # 2. Citation Validation
        citations = self.citation_validator.validate_citations(
            answer_text=raw_answer,
            evidence_chunks=evidence,
        )

        # 3. Confidence Assessment
        confidence_res = self.confidence_assessor.assess_confidence(
            evidence=evidence,
            citations=citations,
        )

        # 4. Safety Threshold Evaluation
        if confidence_res.below_threshold:
            logger.warning(
                "Triggering safe abstention due to low confidence",
                extra={
                    "query_id": str(context.query_id),
                    "score": confidence_res.score,
                    "reason": confidence_res.reason,
                },
            )
            return self.abstention_handler.handle_abstention(
                query_id=context.query_id,
                reason=confidence_res.reason,
                agent_type=agent_type,
            )

        agents_invoked = [agent_type] if agent_type else []

        return FinalResponse(
            query_id=context.query_id,
            answer=raw_answer,
            is_abstention=False,
            confidence=confidence_res,
            evidence=list(evidence),
            citations=citations,
            agents_invoked=agents_invoked,
        )

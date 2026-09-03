"""
ip_sakti.llm.citation_validator — Citation and evidence grounding validator.

Approved per AGENTS.md §7: Citation validation must be a required step before
any answer is returned to the user. Every factual claim must be grounded in retrieved evidence.
"""

from __future__ import annotations

import logging
import re
from typing import Sequence

from ip_sakti.models.query import CitationRecord, EvidenceChunk

logger = logging.getLogger(__name__)


class CitationValidator:
    """Validates source citations and claim grounding in generated answers."""

    def validate_citations(
        self,
        answer_text: str,
        evidence_chunks: Sequence[EvidenceChunk],
    ) -> list[CitationRecord]:
        """
        Extract citations and check if claims are grounded in evidence.

        Parameters
        ----------
        answer_text :
            Generated answer text.
        evidence_chunks :
            Retrieved EvidenceChunk list.

        Returns
        -------
        list[CitationRecord]
            List of CitationRecord objects tracking grounding status.
        """
        records: list[CitationRecord] = []
        if not answer_text or not evidence_chunks:
            return records

        chunk_map = {chunk.source_label: chunk for chunk in evidence_chunks}

        # Split answer into sentences / claims
        sentences = [s.strip() for s in re.split(r"[.!?]\s+", answer_text) if s.strip()]

        for sentence in sentences:
            # Find citation labels like [SOURCE_1], [SOURCE_2]
            labels = re.findall(r"\[SOURCE_\d+\]", sentence)
            if not labels:
                continue

            for label in labels:
                matching_chunk = chunk_map.get(label)
                if matching_chunk is None:
                    # Citation label does not exist in retrieved evidence
                    records.append(
                        CitationRecord(
                            claim_snippet=sentence[:150],
                            source_label=label,
                            chunk_id="unknown",
                            is_grounded=False,
                            grounding_method="substring",
                        )
                    )
                    continue

                # Grounding check: substring or token overlap between sentence and chunk content
                clean_sentence = re.sub(r"\[SOURCE_\d+\]", "", sentence).lower().strip()
                sentence_words = set(re.findall(r"\w+", clean_sentence))
                chunk_words = set(re.findall(r"\w+", matching_chunk.content.lower()))

                overlap = len(sentence_words.intersection(chunk_words))
                is_grounded = overlap > 0 or len(sentence_words) == 0

                records.append(
                    CitationRecord(
                        claim_snippet=sentence[:150],
                        source_label=label,
                        chunk_id=matching_chunk.chunk_id,
                        is_grounded=is_grounded,
                        grounding_method="substring",
                    )
                )

        logger.debug(
            "Validated citations in answer",
            extra={"num_claims": len(records), "grounded_count": sum(1 for r in records if r.is_grounded)},
        )
        return records

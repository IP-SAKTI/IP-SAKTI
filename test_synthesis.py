from uuid import uuid4

from ip_sakti.models.query import (
    QueryContext,
    Intent,
    Jurisdiction,
    FormulationCategory,
)
from ip_sakti.retrieval.pipeline import HybridRAGPipeline
from ip_sakti.llm.synthesis_service import AnswerSynthesisService

# --------------------------------------------------
# 1. Load existing RAG index
# --------------------------------------------------
rag = HybridRAGPipeline()
rag.load_index()

query = "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?"

# --------------------------------------------------
# 2. Retrieve evidence
# --------------------------------------------------
evidence = rag.search(query, rerank_top_k=5)

print("=" * 80)
print("RETRIEVED EVIDENCE:", len(evidence))
print("=" * 80)

for i, chunk in enumerate(evidence, 1):
    print(f"\n[{i}] {chunk.title}")
    print("Source:", chunk.source_name)
    print("Label:", chunk.source_label)

# --------------------------------------------------
# 3. Build QueryContext
# --------------------------------------------------
context = QueryContext(
    query_id=uuid4(),
    raw_query=query,
    normalised_query=query.lower(),
    detected_language="en",
    lang_detect_confidence=1.0,
    translated_query=query,
    intent=Intent.REGULATORY,
    jurisdiction=Jurisdiction.INDIA,
    formulation_category=FormulationCategory.CLASSICAL,
)

# --------------------------------------------------
# 4. Run complete synthesis pipeline
# --------------------------------------------------
service = AnswerSynthesisService()

result = service.synthesize(
    context=context,
    evidence=evidence,
)

# --------------------------------------------------
# 5. Display final response
# --------------------------------------------------
print("\n" + "=" * 80)
print("FINAL RESPONSE")
print("=" * 80)

print("\nAnswer:")
print(result.answer)

print("\nAbstention:", result.is_abstention)

print("\nConfidence:")
print(result.confidence)

print("\nCitations:")
for citation in result.citations:
    print(citation)

print("\nEvidence used:", len(result.evidence))

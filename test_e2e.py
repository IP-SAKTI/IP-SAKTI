from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.models.query import QueryRequest

query = "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?"

request = QueryRequest(raw_query=query)

pipeline = PipelineCoordinator()

result = pipeline.execute(request)

print("=" * 80)
print("FINAL END-TO-END RESPONSE")
print("=" * 80)

print("\nAnswer:")
print(result.answer)

print("\nAbstention:", result.is_abstention)

print("\nConfidence:")
print(result.confidence)

print("\nEvidence used:", len(result.evidence))

print("\nCitations:")
for citation in result.citations:
    print(citation)

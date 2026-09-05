from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.models.query import QueryRequest

query = "आयुर्वेदिक दवाओं को बिक्री के लिए बनाने का लाइसेंस लेने के लिए कौन सा फॉर्म आवश्यक है?"

request = QueryRequest(
    raw_query=query,
    user_language="hi",
)

pipeline = PipelineCoordinator()

result = pipeline.execute(request)

print("=" * 80)
print("MULTILINGUAL END-TO-END TEST")
print("=" * 80)

print("\nOriginal Hindi Query:")
print(query)

print("\nFinal Answer:")
print(result.answer)

print("\nAbstention:", result.is_abstention)

print("\nConfidence:")
print(result.confidence)

print("\nEvidence used:", len(result.evidence))

print("\nCitations:")
for citation in result.citations:
    print(citation)

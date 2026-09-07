import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from ip_sakti.models.query import QueryRequest
from ip_sakti.pipeline import PipelineCoordinator

coordinator = PipelineCoordinator()
response = coordinator.execute(QueryRequest(raw_query="What is Section 3(p) of the Patents Act?"))

print("=== PIPELINE EXECUTION RESULT ===")
print(f"Is Abstention: {response.is_abstention}")
print(f"Confidence: {response.confidence.score if response.confidence else None}")
print(f"Evidence chunks count: {len(response.evidence)}")

for i, chunk in enumerate(response.evidence, 1):
    chunk_dict = chunk if isinstance(chunk, dict) else chunk.model_dump()
    print(f"\nChunk [{i}]:")
    print(f"  Title: {chunk_dict.get('title')}")
    print(f"  Source ID: {chunk_dict.get('source_id') or chunk_dict.get('doc_id')}")
    print(f"  Source URL: {chunk_dict.get('source_url')}")
    meta = chunk_dict.get("metadata", {})
    if isinstance(meta, dict):
        print(f"  Meta Source URL: {meta.get('source_url')}")

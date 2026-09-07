import os
import sys
sys.path.insert(0, ".")

from sentence_transformers import CrossEncoder
from ip_sakti.retrieval.pipeline import HybridRAGPipeline
from ip_sakti.models.query import KnowledgeDocument

os.environ["HF_HUB_OFFLINE"] = "1"

model = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

query = "manu anuty"
france_query = "What is the capital of France?"
laptop_query = "How do I repair my laptop?"
valid_query = "What form is required to apply for a licence to manufacture Ayurvedic drugs for sale?"

# Sample chunk content from Rule 158-B
chunk_content = "Rule 158-B. Licensing requirements for Ayurveda, Siddha and Unani (ASU) drugs. Form 24-D application to State Licensing Authority."

print("Cross-encoder scores against Rule 158-B chunk:")
print(f"manu anuty: {model.predict([[query, chunk_content]])[0]:.4f}")
print(f"France query: {model.predict([[france_query, chunk_content]])[0]:.4f}")
print(f"Laptop query: {model.predict([[laptop_query, chunk_content]])[0]:.4f}")
print(f"Valid AYUSH query: {model.predict([[valid_query, chunk_content]])[0]:.4f}")

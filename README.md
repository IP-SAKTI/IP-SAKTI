# IP-SAKTI

IP-SAKTI Sahayak

Multilingual RAG-based AI Assistant for Intellectual Property and Regulatory Guidance in Ayurveda

Overview

IP-SAKTI Sahayak is an AI-powered assistant designed to help users find information related to:

Ayurveda and Traditional Knowledge
Intellectual Property and Patents
Biodiversity and Access & Benefit Sharing (ABS)
Indian and International Regulations
Scientific evidence and research

The system provides multilingual, source-grounded answers with citations.

Architecture
User
↓
Language Detection
↓
Query Normalization
↓
Orchestrator
↓
Intent + Jurisdiction + Classification
↓
Rule Engine
↓
Specialist Agents
├── IP Agent
├── Regulatory Agent
└── TK/ABS Agent
↓
Hybrid Retrieval
├── FAISS
└── BM25
↓
RRF
↓
Cross-Encoder Reranker
↓
Top Evidence
↓
Citation Mapping
↓
LLM Reasoning
↓
Citation Validation
↓
Translation
↓
User
Tech Stack
Component Technology
UI Streamlit
Backend FastAPI
Language Detection Pretrained NLP
Translation Pretrained/API Translation
LLM Pluggable Instruction Model
Agents Python
Embeddings Multilingual Embedding Model
Vector Search FAISS
Keyword Search BM25
Fusion RRF
Reranking Cross-Encoder
Rules Python + YAML
Metadata SQLite
Validation Pydantic + Citation Checks
Logging Python Structured Logging
Deployment Docker
Knowledge Sources

The knowledge base will use authorized and authoritative sources such as:

TKDL / CSIR-TKDL where access is permitted
Ministry of AYUSH
CCRAS
AYUSH Research Portal
IP India
WIPO
India Code
PubMed / NCBI
GBIF
Authorized/licensed academic datasets
Project Structure
ip-sakti-sahayak/
│
├── app/
│ ├── agents/
│ ├── api/
│ ├── ingestion/
│ ├── retrieval/
│ ├── rules/
│ ├── llm/
│ ├── language/
│ ├── validation/
│ └── orchestration/
│
├── frontend/
│ └── streamlit_app.py
│
├── data/
├── indexes/
├── evaluation/
├── tests/
├── configs/
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
Installation

1. Clone the repository
   git clone <repository-url>
   cd ip-sakti-sahayak
2. Create virtual environment

Windows

python -m venv .venv
.venv\Scripts\activate

Linux/macOS

python3 -m venv .venv
source .venv/bin/activate 3. Install dependencies
pip install -r requirements.txt 4. Configure environment
copy .env.example .env

Add the required model/API configuration to .env.

Run the Application
Start FastAPI
uvicorn app.api.main:app --reload

API:

http://localhost:8000

Swagger:

http://localhost:8000/docs
Start Streamlit
streamlit run frontend/streamlit_app.py

UI:

http://localhost:8501
Docker

Build:

docker build -t ip-sakti-sahayak .

Run:

docker compose up --build
Important

IP-SAKTI Sahayak is an information and decision-support system, not a substitute for professional legal, regulatory, medical, or scientific advice.

The system prioritizes authoritative sources, citations, provenance, and transparent uncertainty.

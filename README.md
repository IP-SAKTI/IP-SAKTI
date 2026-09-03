IP-SAKTI Sahayak

Multilingual, RAG-Based AI Assistant for Intellectual Property and Regulatory Guidance in Ayurveda

Smart India Hackathon 2026 --- Problem Statement 26045
Organization: Ministry of AYUSH
Department: All India Institute of Ayurveda
Category: Software
Theme: MedTech / BioTech / HealthTech

1. Overview

IP-SAKTI Sahayak is a multilingual, source-grounded AI assistant for
navigating Ayurvedic traditional knowledge (TK), intellectual property
(IP), patents, biodiversity/access-and-benefit-sharing (ABS), and
regulatory information across Indian and international jurisdictions.

The system combines multilingual NLP, query normalization, jurisdiction
and intent classification, specialist workflows, hybrid retrieval,
deterministic rules, LLM reasoning, citation mapping, and citation
validation.

Core principle

The LLM reasons over authoritative retrieved evidence; it does not
invent legal, regulatory, or traditional-knowledge facts.

2. Problem Statement

Ayurveda is supported by extensive codified and community-held
traditional knowledge and by therapeutic knowledge involving plant,
microbial, and animal resources.

Protecting and commercialising an Ayurvedic product can require
navigating:

Traditional knowledge and prior art

Ayurvedic formulations and ingredients

Intellectual property rights

Patents and patent-related information

Traditional Knowledge Resource Classification (TKRC)

International Patent Classification (IPC)

Biodiversity and ABS requirements

Indian laws and regulations

International traditional-knowledge frameworks

Jurisdiction-specific regulatory requirements

Scientific evidence

This information is fragmented across different databases, documents,
terminology systems, jurisdictions, and languages.

IP-SAKTI Sahayak provides a unified multilingual interface that
retrieves relevant evidence and explains it with traceable citations.

3. Objectives

Accept multilingual user queries.

Detect and normalize language and terminology.

Identify intent, entities, domain, and jurisdiction.

Route questions to appropriate specialist workflows.

Retrieve authoritative evidence using hybrid search.

Apply deterministic regulatory rules.

Generate source-grounded explanations using a pluggable
instruction-tuned LLM.

Map factual claims to supporting sources.

Validate citations before responding.

Translate the final response into the user's language.

Example questions

Is this Ayurvedic formulation already documented as traditional knowledge?

What plants are present in this formulation?

Are there similar patents for these ingredients?

What Indian regulations may apply to commercialization?

Does access to this biological resource require additional compliance?

What evidence exists for this medicinal plant?

What changes if the intended market is another country?

4. Key Features

Multilingual Interaction

User Query
↓
Language Detection
↓
Query Normalization
↓
Evidence Retrieval
↓
Answer Generation
↓
Translation
↓
User

Query Understanding

The system extracts:

Classification

Jurisdiction

Intent

Entities

Domain

Potential entities include Ayurvedic formulations, medicinal plants,
botanical names, compounds, patents, countries, regulations, biological
resources, traditional knowledge, communities, and indications.

Specialist Workflows

IP Agent

Handles patent, prior-art, IPC/CPC, patent similarity, applicant, and
jurisdiction-related questions.

Regulatory Agent

Handles laws, regulations, authorities, compliance requirements, and
jurisdiction-specific requirements.

TK/ABS Agent

Handles traditional knowledge, Ayurvedic formulations, biological
resources, traditional uses, biodiversity, and ABS-related evidence.

Agents use lightweight Python orchestration rather than unnecessary
autonomous-agent infrastructure.

5.  System Architecture

                              USER
                                │
                                ▼
                       LANGUAGE DETECTION
                                │
                                ▼
                       QUERY NORMALIZATION
                                │
                                ▼
                         ORCHESTRATOR
                                │
                  ┌─────────────┼─────────────┐
                  ▼             ▼             ▼
            CLASSIFICATION  JURISDICTION    INTENT
                  │             │             │
                  └─────────────┼─────────────┘
                                ▼
                           RULE ENGINE
                                │
                         TRIGGERED RULES
                                │
                                ▼
                       SPECIALIST AGENTS
                    ┌───────────┼───────────┐
                    ▼           ▼           ▼
                   IP         REG         TK/ABS
                 AGENT       AGENT        AGENT
                    │           │           │
                    └───────────┼───────────┘
                                ▼
                         RETRIEVAL TOOL
                                │
                       ┌────────┴────────┐
                       ▼                 ▼
                  DENSE SEARCH         BM25
                       │                 │
                       └────────┬────────┘
                                ▼
                               RRF
                                │
                                ▼
                            RERANKER
                                │
                                ▼
                          TOP EVIDENCE
                                │
                                ▼
                       CITATION MAPPING
                                │
                                ▼
                        AGENT REASONING
                                │
                                ▼
                       STRUCTURED OUTPUT
                                │
                                ▼
                          ORCHESTRATOR
                                │
                                ▼
                       ANSWER SYNTHESIS
                                │
                                ▼
                       CITATION VALIDATOR
                                │
                                ▼
                           TRANSLATION
                                │
                                ▼
                              USER

6.  Technology Stack

Layer Technology

UI Streamlit
API FastAPI
Language Detection Pretrained NLP
Translation Pretrained multilingual model / authorized API
LLM Pluggable pretrained instruction-tuned model
Agents Python / lightweight orchestration
Embeddings Multilingual embedding model
Vector Search FAISS
Keyword Search BM25
Fusion Reciprocal Rank Fusion (RRF)
Reranking Cross-encoder
Rules Python + YAML
Metadata SQLite
Knowledge Curated authoritative documents
Validation Pydantic + citation checks
Logging Python structured logging
Packaging Docker

7. Retrieval Architecture

IP-SAKTI uses hybrid retrieval because IP, legal, regulatory,
scientific, and traditional-knowledge queries require both semantic and
exact-term matching.

Dense Search

Query
↓
Multilingual Embedding Model
↓
Vector
↓
FAISS
↓
Semantic Candidates

BM25

Query
↓
BM25
↓
Keyword Candidates

BM25 is especially useful for patent numbers, legal sections, botanical
names, formulation names, IPC codes, and exact terminology.

RRF

Dense Results ─────┐
├──→ RRF ──→ Combined Ranking
BM25 Results ──────┘

Cross-Encoder Reranking

RRF Candidates
↓
Cross-Encoder
↓
Relevance Scores
↓
Top Evidence

8. Knowledge Architecture

Knowledge should be separated by domain:

knowledge/
│
├── ayurveda/
│ ├── formulations/
│ ├── medicinal_plants/
│ ├── traditional_uses/
│ └── classical_sources/
│
├── patents/
│ ├── india/
│ ├── international/
│ └── wipo/
│
├── regulations/
│ ├── india/
│ ├── international/
│ └── jurisdiction_rules/
│
├── biodiversity/
│ └── abs/
│
└── research/
├── pubmed/
└── ayush/

9. Authoritative Knowledge Sources

The project should prioritize official, authoritative, or appropriately
licensed sources.

Traditional Knowledge / Ayurveda

TKDL / CSIR-TKDL, subject to access and usage conditions

Ministry of AYUSH resources

CCRAS resources

Authoritative classical/public-domain sources

Licensed academic datasets

CSIR-NEIST herbal formulation resources where permitted

Intellectual Property

IP India official resources

WIPO PATENTSCOPE and WIPO resources

Official international patent-office resources where appropriate

Regulatory / Legal

India Code

Ministry of AYUSH and Government of India notifications/regulations

WIPO traditional knowledge/GRTKF legal resources

Official foreign regulator/legal sources

Scientific Evidence

PubMed / NCBI

AYUSH Research Portal

Peer-reviewed literature

Other authoritative scientific repositories

Biodiversity

National Biodiversity Authority resources

GBIF for biodiversity/taxonomic information

Official biodiversity and ABS documents

10. TKDL Data Policy

IP-SAKTI must not use unauthorized copies, leaked datasets, or
uncontrolled redistribution of TKDL data.

The full TKDL database is controlled-access information. If
project-specific access is granted, it must be used according to the
applicable agreement and restrictions.

For the prototype, the system may use:

Authorized TKDL access where available

Publicly available representative TKDL information

Public-domain underlying source literature

Authoritative AYUSH/CCRAS resources

Licensed academic datasets

Other permitted sources

Each source should retain provenance and access/licensing metadata.

11. Data and Provenance Model

Every document/chunk should retain provenance.

{
"document_id": "WIPO_00125",
"chunk_id": "WIPO_00125_CH_04",
"title": "Example document",
"source": "WIPO",
"source_type": "official",
"document_type": "patent",
"jurisdiction": "International",
"language": "en",
"publication_date": "2026-01-20",
"section": "Claims",
"page": 12,
"source_url": "OFFICIAL_SOURCE_URL",
"accessed_at": "2026-09-03"
}

Recommended metadata:

document_id
chunk_id
title
source
source_type
publisher
jurisdiction
document_type
language
publication_date
effective_date
section
page
source_url
license/access_rights
retrieved_at

12. Regulatory Rule Engine

Regulatory logic should not be left entirely to the LLM.

Rules are maintained separately using:

Python + YAML

Example:

india:
biodiversity:
source_validation: required

traditional_knowledge:
source_validation: required

regulatory_guidance:
cite_primary_source: true

The actual rules used in the application must be derived from applicable
authoritative legal/regulatory sources.

The LLM explains retrieved rules; it does not invent them.

13. Citation and Trust Layer

Because IP-SAKTI provides IP and regulatory information, important
factual claims should be traceable to evidence.

Retrieved Evidence
↓
Claim Generation
↓
Citation Mapping
↓
Citation Validation
↓
Structured Answer

A citation should identify, where available:

Source
Title
Section/Page
Jurisdiction
URL

The system should distinguish:

Authoritative fact

Retrieved evidence

Model-generated explanation

Inference

Uncertain / insufficient evidence

14. Structured Output

The reasoning layer should produce validated structured output rather
than unrestricted text.

{
"summary": "Potential traditional-knowledge overlap identified.",
"jurisdiction": "India",
"intent": "IP prior-art assessment",
"findings": [
{
"claim": "Relevant traditional-use evidence was identified.",
"supported": true,
"citations": [
{
"source": "Authoritative Source",
"section": "Relevant Section"
}
]
}
],
"patent_findings": [],
"regulatory_findings": [],
"confidence": "high",
"limitations": [
"This is an information-support result and not legal advice."
]
}

Pydantic validates the response schema before it reaches the UI.

15. Example End-to-End Query

User

I have an Ayurvedic formulation containing
Withania somnifera and Curcuma longa.
I want to know whether relevant traditional knowledge exists
and what IP/regulatory issues I should investigate
for commercialization in India.

Pipeline

User Query
↓
Language Detection
↓
Query Normalization
↓
Entity Extraction
↓
Withania somnifera / Curcuma longa
↓
Intent = IP + TK + Regulatory
↓
Jurisdiction = India
↓
IP Agent + Regulatory Agent + TK/ABS Agent
↓
FAISS + BM25
↓
RRF
↓
Cross-Encoder
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

The result presents:

Traditional-knowledge evidence

Potentially relevant patent evidence

Regulatory information

Biodiversity/ABS considerations where applicable

Source citations

Confidence/limitations

16. Recommended Repository Structure

ip-sakti-sahayak/
│
├── app/
│ ├── api/
│ │ ├── routes/
│ │ └── schemas/
│ ├── agents/
│ │ ├── ip_agent.py
│ │ ├── regulatory_agent.py
│ │ └── tk_abs_agent.py
│ ├── core/
│ │ ├── config.py
│ │ └── logging.py
│ ├── ingestion/
│ │ ├── loaders.py
│ │ ├── chunking.py
│ │ └── metadata.py
│ ├── retrieval/
│ │ ├── embeddings.py
│ │ ├── faiss_store.py
│ │ ├── bm25.py
│ │ ├── rrf.py
│ │ └── reranker.py
│ ├── rules/
│ │ ├── engine.py
│ │ └── yaml/
│ ├── llm/
│ │ ├── provider.py
│ │ └── prompts.py
│ ├── language/
│ │ ├── detection.py
│ │ └── translation.py
│ ├── validation/
│ │ ├── schemas.py
│ │ └── citations.py
│ └── orchestration/
│ └── orchestrator.py
│
├── frontend/
│ └── streamlit_app.py
│
├── data/
│ ├── raw/
│ ├── processed/
│ └── metadata/
│
├── indexes/
│ ├── faiss/
│ └── bm25/
│
├── evaluation/
│ ├── test_questions.json
│ ├── retrieval_eval.py
│ ├── citation_eval.py
│ └── groundedness_eval.py
│
├── tests/
├── configs/
│ ├── settings.yaml
│ └── jurisdictions/
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md

17. Installation

Prerequisites

Python 3.11+

Docker Desktop

Git

Clone:

git clone <YOUR_REPOSITORY_URL>
cd ip-sakti-sahayak

Create environment:

Windows

python -m venv .venv
.venv\Scriptsctivate

Linux/macOS

python3 -m venv .venv
source .venv/bin/activate

Install:

pip install -r requirements.txt

18. Environment Configuration

Create .env from .env.example.

Example:

APP_ENV=development
API_HOST=0.0.0.0
API_PORT=8000

LLM_PROVIDER=local
LLM_MODEL=<MODEL_NAME>

EMBEDDING_MODEL=<MULTILINGUAL_EMBEDDING_MODEL>
RERANKER_MODEL=<CROSS_ENCODER_MODEL>

SQLITE_PATH=data/metadata/ip_sakti.db

FAISS_INDEX_PATH=indexes/faiss/index.faiss
BM25_INDEX_PATH=indexes/bm25/index.pkl

Never commit API keys or credentials.

19. Knowledge Ingestion

Recommended pipeline:

Authoritative Documents
↓
Source/License Validation
↓
Text Extraction
↓
Cleaning
↓
Chunking
↓
Metadata Assignment
↓
Embeddings
↓
FAISS +
BM25

Example:

python -m app.ingestion.build_index

Exact ingestion commands depend on each source's permitted access and
format.

20. Running the Application

FastAPI

uvicorn app.api.main:app --reload --host 0.0.0.0 --port 8000

API:

http://localhost:8000

Swagger:

http://localhost:8000/docs

Streamlit

streamlit run frontend/streamlit_app.py

UI:

http://localhost:8501

21. Docker

Build:

docker build -t ip-sakti-sahayak .

Run:

docker run --env-file .env -p 8000:8000 -p 8501:8501 ip-sakti-sahayak

Or:

docker compose up --build

22. API Flow

Example:

POST /api/v1/query
Content-Type: application/json

{
"query": "What IP and regulatory requirements may apply to this Ayurvedic formulation?",
"language": "en",
"jurisdiction": "India"
}

Processing:

API
↓
Language Detection
↓
Normalization
↓
Orchestrator
↓
Classification / Intent / Jurisdiction
↓
Rule Engine
↓
Specialist Agents
↓
Hybrid Retrieval
↓
RRF
↓
Reranking
↓
Evidence
↓
Reasoning
↓
Citation Validation
↓
Translation
↓
Response

23. Security and Responsible Use

IP-SAKTI is an information and decision-support system, not a
replacement for qualified legal, regulatory, medical, or scientific
professionals.

The system should:

Prefer primary/official sources.

Display source provenance.

Avoid unsupported legal conclusions.

Distinguish evidence from inference.

Report uncertainty when evidence is insufficient.

Avoid fabricated citations.

Avoid unauthorized TKDL data.

Protect API keys and credentials.

Avoid unnecessarily storing sensitive user information.

Apply access controls to restricted datasets.

Respect source-specific licenses and terms of use.

24. Limitations

Potential limitations include:

Restricted access to some authoritative databases

Availability of structured public APIs

Incomplete patent metadata

Multilingual terminology ambiguity

Differences between jurisdictions

Changes in laws and regulations

Limited machine-readable legal documents

Gaps in traditional-knowledge documentation

LLM reasoning errors

The system should therefore prefer wording such as:

"Based on the retrieved sources..."

rather than presenting model-generated conclusions as definitive legal
advice.

25. Evaluation

Evaluation should cover retrieval, grounding, generation, and
multilingual performance.

Retrieval

Recall@K

Precision@K

MRR

nDCG

Grounding

Citation accuracy

Citation completeness

Evidence-to-claim alignment

Groundedness

Generation

Answer relevance

Factual consistency

Hallucination rate

Structured-output validity

Multilingual

Language-detection accuracy

Translation quality

Cross-lingual retrieval performance

Create a benchmark set covering:

Traditional Knowledge
Ayurveda
Medicinal Plants
Patents
Prior Art
IP Classification
Biodiversity
ABS
Indian Regulations
International Regulations
Multilingual Queries

26. Development Roadmap

Phase 1 --- Core MVP

Streamlit UI

FastAPI backend

Language detection

Query normalization

Basic orchestrator

Document ingestion

FAISS

BM25

RRF

Basic LLM integration

Citation display

Phase 2 --- Intelligence

IP Agent

Regulatory Agent

TK/ABS Agent

Cross-encoder reranking

Rule engine

Jurisdiction handling

Structured outputs

Citation validation

Phase 3 --- Hackathon Demonstration

Multilingual interaction

Patent comparison

Regulatory explanation

Source provenance

Evaluation dashboard

Docker deployment

End-to-end demonstration scenarios

27. Future Enhancements

PostgreSQL + pgvector for production

Knowledge graph for plant/formulation/patent relationships

Patent-claim similarity

Automated prior-art comparison

More international jurisdictions

Advanced multilingual retrieval

OCR for scanned documents

Document version tracking

Regulatory-change monitoring

Expert review workflows

Role-based access control

Enterprise deployment

Continuous model evaluation

28. Expected Impact

IP-SAKTI Sahayak aims to reduce the effort required to navigate
fragmented Ayurveda, traditional-knowledge, IP, biodiversity, and
regulatory information.

Instead of manually searching multiple databases:

User
↓
One multilingual interface
↓
Query understanding
↓
Specialist workflows
↓
Authoritative sources
↓
Hybrid retrieval
↓
Evidence ranking
↓
Rule processing
↓
Citation-validated reasoning
↓
Source-grounded response

29. Conclusion

IP-SAKTI Sahayak combines multilingual NLP, retrieval-augmented
generation, hybrid search, specialist workflows, deterministic rules,
and citation validation into a unified assistant for Ayurveda-related IP
and regulatory information.

The system follows a transparent workflow:

Retrieve authoritative evidence → apply explicit rules → reason with
the evidence → validate citations → explain in the user's language.

This makes the system more transparent, auditable, and reliable than a
conventional chatbot while remaining lightweight enough for rapid SIH
prototyping.

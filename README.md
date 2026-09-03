# IP-SAKTI

IP-SAKTI Sahayak

Multilingual AI Assistant for Intellectual Property and Regulatory Guidance in Ayurveda

## Overview

IP-SAKTI Sahayak is a multilingual, RAG-based AI assistant designed
to help users navigate Ayurvedic Traditional Knowledge, Intellectual
Property, patents, biodiversity/ABS, and regulatory information.

The system combines multilingual NLP, hybrid information retrieval,
specialist agents, rule-based processing, and a pretrained
instruction-tuned LLM to provide source-grounded and
citation-supported responses.

## Key Capabilities

Multilingual query support

Ayurveda and Traditional Knowledge search

Patent and prior-art information retrieval

Regulatory and jurisdiction-based guidance

Biodiversity and ABS information

Hybrid semantic + keyword search

Source citations and evidence validation

## Technology Stack

### Frontend

- **Streamlit** — User interface and interactive dashboard

### Backend

- **FastAPI** — REST API and backend services
- **Pydantic** — Request/response validation and structured data models

### Language Processing

- **Pretrained NLP Models** — Language detection and query understanding
- **Multilingual Translation Model / API** — Query and response translation

### AI & LLM

- **Pretrained Instruction-Tuned LLM** — Evidence-based answer generation
- **Multilingual Embedding Model** — Semantic representation of queries and documents
- **Cross-Encoder** — Evidence reranking

### Agent & Orchestration

- **Python** — Core orchestration and agent workflows
- **IP Agent** — Intellectual property and patent-related queries
- **Regulatory Agent** — Regulatory and jurisdiction-specific queries
- **TK/ABS Agent** — Traditional Knowledge and Access & Benefit Sharing queries

### Information Retrieval

- **FAISS** — Dense vector similarity search
- **BM25** — Keyword-based retrieval
- **RRF (Reciprocal Rank Fusion)** — Combines dense and keyword search results
- **Cross-Encoder Reranker** — Ranks retrieved evidence by relevance

### Rule Engine

- **Python** — Regulatory rule processing
- **YAML** — Jurisdiction-specific rules and configurations

### Data & Storage

- **SQLite** — Metadata and application data
- **JSON** — Structured configuration and knowledge metadata
- **FAISS Index** — Vector embeddings
- **BM25 Index** — Keyword search index

### Knowledge Sources

- **TKDL / CSIR-TKDL** — Traditional Knowledge
- **Ministry of AYUSH** — Ayurveda and AYUSH resources
- **CCRAS** — Ayurvedic research and medicinal plant information
- **AYUSH Research Portal** — Research literature
- **IP India** — Indian patent information
- **WIPO** — International IP and patent information
- **India Code** — Indian laws and regulations
- **PubMed / NCBI** — Scientific literature
- **GBIF** — Biodiversity and taxonomic information

### Validation & Observability

- **Pydantic** — Schema validation
- **Citation Validation** — Evidence-to-claim verification
- **Python Structured Logging** — Application logging and monitoring

### Deployment

- **Docker** — Containerization and deployment
- **Docker Compose** — Local multi-service orchestration

## Architecture

```text
User
 │
 ▼
Language Detection
 │
 ▼
Query Normalization
 │
 ▼
Orchestrator
 │
 ├──────────────┬──────────────┐
 ▼              ▼              ▼
Intent       Jurisdiction   Classification
 │              │              │
 └──────────────┴──────────────┘
                │
                ▼
         Specialist Agents
        ┌────────┼─────────┐
        ▼        ▼         ▼
     IP Agent  Regulatory  TK/ABS
                Agent       Agent
        └────────┼─────────┘
                 ▼
         Hybrid Retrieval
          ┌──────┴──────┐
          ▼             ▼
        FAISS          BM25
          │             │
          └──────┬──────┘
                 ▼
                RRF
                 │
                 ▼
       Cross-Encoder Reranking
                 │
                 ▼
              Evidence
                 │
                 ▼
           LLM Reasoning
                 │
                 ▼
         Citation Validation
                 │
                 ▼
            Translation
                 │
                 ▼
                User

## Knowledge Sources

The knowledge base is built from authorized and authoritative
sources, including:

TKDL / CSIR-TKDL

Ministry of AYUSH

CCRAS

AYUSH Research Portal

IP India

WIPO

India Code

PubMed / NCBI

GBIF

Other permitted/licensed datasets

## Project Status

Smart India Hackathon 2026 --- Problem Statement 26045

Project: IP-SAKTI Sahayak
Theme: MedTech / BioTech / HealthTech
```

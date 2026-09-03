# IP-SAKTI

IP-SAKTI Sahayak

Multilingual AI Assistant for Intellectual Property and Regulatory Guidance in Ayurveda

Overview

IP-SAKTI Sahayak is a multilingual, RAG-based AI assistant designed
to help users navigate Ayurvedic Traditional Knowledge, Intellectual
Property, patents, biodiversity/ABS, and regulatory information.

The system combines multilingual NLP, hybrid information retrieval,
specialist agents, rule-based processing, and a pretrained
instruction-tuned LLM to provide source-grounded and
citation-supported responses.

Key Capabilities

Multilingual query support

Ayurveda and Traditional Knowledge search

Patent and prior-art information retrieval

Regulatory and jurisdiction-based guidance

Biodiversity and ABS information

Hybrid semantic + keyword search

Source citations and evidence validation

Technology Stack

Component Technology

Frontend / UI Streamlit
Backend / API FastAPI
Language Detection Pretrained NLP Model
Translation Pretrained / Translation API
LLM Pluggable Pretrained Instruction-Tuned Model
Agent Orchestration Python
Embeddings Multilingual Embedding Model
Vector Search FAISS
Keyword Search BM25
Search Fusion Reciprocal Rank Fusion (RRF)
Reranking Cross-Encoder
Rule Engine Python + YAML
Metadata Storage SQLite
Validation Pydantic + Citation Validation
Logging Python Structured Logging
Deployment Docker

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
Cross-Encoder Reranking
↓
Evidence
↓
LLM Reasoning
↓
Citation Validation
↓
Translation
↓
User

Knowledge Sources

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

Project Status

Smart India Hackathon 2026 --- Problem Statement 26045

Project: IP-SAKTI Sahayak
Theme: MedTech / BioTech / HealthTech

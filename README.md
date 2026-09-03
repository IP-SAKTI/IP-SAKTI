# IP-SAKTI Sahayak

### Multilingual AI Assistant for Intellectual Property and Regulatory Guidance in Ayurveda

IP-SAKTI Sahayak is a multilingual, evidence-grounded AI assistant designed to help users navigate Intellectual Property (IP), Ayurveda Traditional Knowledge (TK), biodiversity and Access & Benefit Sharing (ABS), patent/prior-art information, and regulatory guidance.

The system combines multilingual NLP, agentic query orchestration, formulation classification, jurisdiction-aware rule processing, hybrid Retrieval-Augmented Generation (RAG), evidence reranking, citation validation, confidence assessment, and safe abstention.

The MVP is designed around authoritative and permitted knowledge sources and provides source-grounded responses rather than unsupported legal or regulatory claims.

---

## 1. Problem

Ayurvedic formulations and Traditional Knowledge involve complex interactions between:

- Intellectual Property
- Traditional Knowledge
- Patents and prior art
- Biodiversity
- Access and Benefit Sharing (ABS)
- Drug and formulation classification
- National and international regulations

Users may struggle to determine which rules, authorities, databases, and procedures are relevant to a particular formulation or IP question.

IP-SAKTI Sahayak aims to provide a single multilingual interface that helps users identify relevant information and authoritative evidence.

The system is an informational decision-support assistant and does not replace professional legal, regulatory, or IP advice.

---

# 2. Core Objectives

The MVP focuses on:

1. Multilingual query understanding
2. Ayurveda and Traditional Knowledge information retrieval
3. Formulation/product classification
4. Patent and prior-art information retrieval
5. Jurisdiction-aware regulatory guidance
6. Biodiversity and ABS guidance
7. Hybrid semantic + keyword retrieval
8. Evidence reranking
9. Source-grounded answer generation
10. Citation and evidence validation
11. Confidence estimation
12. Safe abstention for unsupported or uncertain queries
13. Human/IP facilitator escalation pathway

---

# 3. Key Capabilities

### Multilingual Interaction

Users can submit queries in supported Indian and international languages.

The system performs:

- Language detection
- Query normalization
- Translation into the retrieval/processing language when required
- Response translation back to the user's language

Translation is performed using pretrained multilingual models or approved translation APIs.

---

### Formulation Classification

The system identifies or asks for clarification about the relevant formulation/product category.

Potential categories include:

- Classical / generic Ayurvedic medicine
- Proprietary medicine
- New / non-classical drug
- Phytopharmaceutical
- Ayurveda-Aahar / nutraceutical
- Cosmetic

Classification is used to improve downstream regulatory and IP routing.

---

### Jurisdiction Awareness

The user can explicitly select:

- India
- International
- Both

Jurisdiction is treated as a first-class input to prevent national and international rules from being conflated.

---

### Intellectual Property Guidance

The IP workflow can assist with:

- Patent-related queries
- Prior-art discovery
- Traditional Knowledge and patentability considerations
- IP authority information
- Relevant patent databases
- TKDL/prior-art pointers where permitted

---

### Traditional Knowledge and ABS

The TK/ABS workflow can assist with:

- Ayurveda Traditional Knowledge
- Traditional knowledge references
- Biodiversity-related information
- Access and Benefit Sharing concepts
- Relevant authorities and regulatory information
- Source-grounded pointers to applicable information

---

### Regulatory Guidance

The regulatory workflow provides:

- Jurisdiction-aware regulatory information
- Formulation-category-aware guidance
- Relevant authority identification
- Relevant rules and provisions from the curated knowledge base
- Source citations

---

# 4. System Architecture

                              USER
                                │
                                ▼
                    ┌──────────────────────┐
                    │    STREAMLIT UI      │
                    │                      │
                    │ • Query              │
                    │ • Language           │
                    │ • Jurisdiction       │
                    │ • Formulation info   │
                    └──────────┬───────────┘
                               │
                               ▼
                    LANGUAGE DETECTION
                               │
                               ▼
                    MULTILINGUAL LAYER
                               │
                               ▼
                    QUERY NORMALIZATION
                               │
                               ▼
                        ORCHESTRATOR
                               │
               ┌───────────────┼────────────────┐
               │               │                │
               ▼               ▼                ▼
            INTENT       JURISDICTION       FORMULATION
        CLASSIFICATION      ANALYSIS        CLASSIFICATION
               │               │                │
               └───────────────┼────────────────┘
                               │
                               ▼
                         RULE ENGINE
                               │
                               ▼
                        AGENT ROUTER
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
            IP AGENT       REGULATORY      TK / ABS
                             AGENT           AGENT
                │              │              │
                └──────────────┼──────────────┘
                               │
                               ▼
                         HYBRID RAG
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
            DENSE SEARCH                BM25 SEARCH
               FAISS
                 │                           │
                 └─────────────┬─────────────┘
                               │
                               ▼
                         RRF FUSION
                               │
                               ▼
                  CROSS-ENCODER RERANKER
                               │
                               ▼
                         TOP EVIDENCE
                               │
                               ▼
                 PRETRAINED INSTRUCTION
                         TUNED LLM
                               │
                               ▼
                  EVIDENCE / CITATION
                         VALIDATION
                               │
                               ▼
                    CONFIDENCE ASSESSMENT
                         │          │
                       HIGH      LOW/UNCERTAIN
                         │          │
                         ▼          ▼
                       ANSWER    SAFE ABSTENTION
                                      │
                                      ▼
                                   HUMAN / IP
                                   FACILITATOR
                                   ESCALATION
                         │
                         ▼
                  RESPONSE TRANSLATION
                         │
                         ▼
                        USER
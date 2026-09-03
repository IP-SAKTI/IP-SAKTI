# IP-SAKTI Sahayak — Agent & Developer Rules

> These rules govern all AI-assisted and human development on the `johney/antigravity` branch.
> They are derived from the frozen MVP specification in `README.md` and the project constraints
> agreed by the lead engineer. They take precedence over any general defaults.

---

## 1. Source of Truth

- `README.md` is the **frozen MVP specification**. It defines scope, architecture, and technology choices.
- Do **not** extend, redesign, or contradict anything in `README.md` without explicit written approval from the project lead.
- If a new implementation decision is not covered by `README.md`, default to the simplest option that is consistent with the existing architecture.

---

## 2. Branch & Git Rules

- Work **only** on branch `johney/antigravity`. Never switch, create, or delete branches.
- Never force-push or rewrite Git history (`git rebase`, `git commit --amend` on pushed commits, `git push --force`).
- Make **small, meaningful commits** after each completed stage or logical unit of work.
- Commit messages must follow the pattern: `<type>(<scope>): <short description>` (e.g., `feat(retrieval): add BM25 indexer`).
- **Never commit**: `.env` files, API keys, credentials, model weights, FAISS index binaries, SQLite database files, large generated artifacts.
- Keep `.gitignore` up to date to exclude the above.

---

## 3. Architecture Rules

The following architecture is **frozen** and must not be changed:

```
User -> Streamlit UI -> Language Detection -> Multilingual Layer -> Query Normalization
     -> Orchestrator -> Intent Classification | Jurisdiction Analysis | Formulation Classification
     -> Rule Engine -> Agent Router
     -> IP Agent | Regulatory Agent | TK-ABS Agent
     -> Shared Hybrid RAG (FAISS + BM25 -> RRF -> Cross-Encoder Reranker -> Top Evidence)
     -> Pretrained Instruction-Tuned LLM
     -> Evidence/Citation Validation -> Confidence Assessment
     -> Answer OR Safe Abstention -> Human/IP Facilitator Escalation
     -> Response Translation -> User
```

- There are exactly **three specialist agents**: IP Agent, Regulatory Agent, TK/ABS Agent.
- There is exactly **one Orchestrator** and exactly **one Agent Router**.
- Retrieval is exactly: **FAISS (dense) + BM25 (sparse) -> RRF fusion -> Cross-Encoder reranking**.
- The Rule Engine uses **Python + YAML** configuration only.

---

## 4. Technology Constraints

| Layer | Approved Technology | Prohibited |
|---|---|---|
| Frontend | Streamlit | React, Vue, Angular, any non-Streamlit UI |
| Backend | Python, FastAPI, Pydantic | Node.js, Go, Ruby, Django, Flask (except for tests) |
| Storage | SQLite, JSON files, FAISS index, BM25 index | PostgreSQL, MySQL, MongoDB, Redis, any cloud DB |
| Retrieval | FAISS, BM25 (rank_bm25), RRF, Cross-Encoder | Elasticsearch, Pinecone, Weaviate, Qdrant |
| Config | YAML | TOML, INI, JSON-only config |
| Deployment | Docker, Docker Compose | Kubernetes, serverless, managed cloud services |
| NLP / LLM | Pretrained models / approved APIs only | Training from scratch, fine-tuning without approval |
| Translation | Pretrained multilingual models or APIs | Custom-trained translation models |

---

## 5. Model & ML Rules

- **Do not train any model from scratch.**
- Use pretrained models for: embeddings, translation, language detection, reranking, LLM generation.
- Preferred pretrained embedding model: `sentence-transformers` (e.g., `all-MiniLM-L6-v2` or multilingual variant).
- Preferred cross-encoder: `cross-encoder/ms-marco-MiniLM-L-6-v2` or equivalent.
- LLM: Use a pretrained instruction-tuned model (e.g., via Hugging Face Transformers or an approved API such as Google Gemini, OpenAI GPT). Do not build or train a custom LLM.
- Language detection: Use `langdetect` or `lingua` (pretrained).
- Translation: Use `deep-translator`, `googletrans`, or an approved multilingual model.

---

## 6. Scope Rules

- **Do not implement future-scope features** not listed in `README.md` Section 2 (Core Objectives) or Section 3 (Key Capabilities).
- The MVP has a **six-day development constraint**. Prefer simple, working, modular implementations over over-engineered production code.
- Do not add new agent types, new retrieval backends, new databases, or new infrastructure without explicit approval.
- The system is an **informational decision-support assistant**. It must never present itself as a replacement for professional legal or regulatory advice.

---

## 7. Safety & Accuracy Rules

- **Do not fabricate** legal, patent, regulatory, or scientific information.
- Every response that makes a factual claim must be grounded in retrieved evidence with source citations.
- Implement **safe abstention**: if confidence is below threshold or evidence is insufficient, the system must decline to answer and escalate to the human/IP facilitator pathway.
- **Citation validation** must be a required step before any answer is returned to the user.
- **Confidence assessment** must be computed and returned as part of every response object.

---

## 8. Docker & Deployment Rules

- The entire application must be runnable via `docker-compose up`.
- Keep the system Docker-compatible at all times. Never introduce dependencies that cannot run in a Linux container.
- Do not use Windows-only paths or scripts in production code.

---

## 9. Code Quality Rules

- All Python code must be compatible with **Python 3.10+**.
- Use **Pydantic v2** for data models and validation.
- Use **type hints** on all function signatures.
- Write **docstrings** for all public classes and functions.
- Preserve existing comments and docstrings unrelated to a code change.
- Modular structure: one responsibility per module. Do not create monolithic files.
- Use **absolute imports** within the package.

---

## 10. File & Directory Conventions

```
ip_sakti/               # Main Python package
  ui/                   # Streamlit frontend
  api/                  # FastAPI backend
  orchestrator/         # Orchestrator, intent classification, routing
  agents/               # IP, Regulatory, TK-ABS agents
  retrieval/            # FAISS, BM25, RRF, cross-encoder
  rule_engine/          # YAML-based rule engine
  multilingual/         # Language detection, translation, normalization
  models/               # Pydantic data models
  utils/                # Shared utilities
config/                 # YAML config files
data/                   # Curated knowledge base documents (not committed if large)
indexes/                # FAISS and BM25 indexes (not committed)
db/                     # SQLite database files (not committed)
docker/                 # Dockerfiles
docker-compose.yml
requirements.txt
.env.example            # Template only -- never commit .env
```

---

## 11. Knowledge Base Rules

- All knowledge base documents must come from **authoritative and permitted sources**.
- Document provenance (source URL, authority name, publication date) must be stored and retrievable.
- Do not include documents whose copyright or usage terms prohibit inclusion.
- TKDL references may only be included where explicitly permitted.

---

## 12. What Agents Must Always Do

When writing or reviewing code for this project:

1. Check that the change does not violate any rule in this file.
2. Check that the change is consistent with the frozen architecture in `README.md`.
3. Prefer the simplest correct implementation.
4. Commit only when a stage or logical unit is complete.
5. Never break the Docker build.
6. Never remove evidence grounding, citation validation, confidence assessment, or safe abstention.

import json
from pathlib import Path

from ip_sakti.models.document import KnowledgeDocument


def load_knowledge_documents(
    knowledge_dir: str | Path = "data/knowledge",
) -> list[KnowledgeDocument]:
    """Load all authorised JSON knowledge documents from the knowledge directory."""
    knowledge_path = Path(knowledge_dir)

    if not knowledge_path.exists():
        raise FileNotFoundError(
            f"Knowledge directory not found: {knowledge_path}"
        )

    documents: list[KnowledgeDocument] = []

    for json_file in sorted(knowledge_path.glob("*.json")):
        try:
            with json_file.open("r", encoding="utf-8-sig") as fh:
                raw_data = json.load(fh)

            document = KnowledgeDocument.model_validate(raw_data)
            documents.append(document)

        except Exception as exc:
            print(f"WARNING: Could not load {json_file.name}: {exc}")

    return documents

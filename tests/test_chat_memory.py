"""
tests/test_chat_memory.py — Tests for Chat History & Session Memory.

Validates conversation management, SQLite persistence, deterministic title generation,
contextual follow-up memory, citation preservation, and storage error fallback.
"""

from __future__ import annotations

import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from ip_sakti.models.query import (
    AgentType,
    CitationRecord,
    ConfidenceResult,
    ConversationMessageModel,
    EvidenceChunk,
    FinalResponse,
    FormulationCategory,
    Jurisdiction,
    QueryContext,
    QueryRequest,
)
from ip_sakti.pipeline import PipelineCoordinator
from ip_sakti.utils.chat_storage import ChatStorageService, generate_title
from ip_sakti.utils.db import DatabaseManager


@pytest.fixture
def temp_db_manager():
    """Create a temporary SQLite database manager for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test_chat.db"
        db = DatabaseManager(db_path=str(db_path))
        db.initialise()
        try:
            yield db
        finally:
            db.close()



@pytest.fixture
def storage_service(temp_db_manager):
    """Create a ChatStorageService bound to the temporary database."""
    return ChatStorageService(db_manager=temp_db_manager)


# ---------------------------------------------------------------------------
# 1. Deterministic Title Generation
# ---------------------------------------------------------------------------


def test_generate_title():
    """Test deterministic title generation from various user queries."""
    assert generate_title("Can I patent an Ayurvedic formulation?") == "Ayurvedic Patent Eligibility"
    assert generate_title("What are the requirements for Form 24D?") == "Form 24D Requirements"
    assert generate_title("How does TKDL affect patentability?") == "TKDL & Patentability"
    assert generate_title("What are ABS obligations under Biodiversity Act?") == "NBA & ABS Compliance"
    assert generate_title("Can I get an Ayurvedic manufacturing licence under Rule 158B?") == "Ayurvedic Manufacturing License"
    assert generate_title("Is it possible to trademark an Ayurvedic brand?") == "Ayurvedic Trademark & Brand"
    assert generate_title("Explain Section 3(p) provisions.") == "Section 3(p) TK Guidance"
    assert generate_title("") == "New Chat"


# ---------------------------------------------------------------------------
# 2. Conversation & Message Persistence
# ---------------------------------------------------------------------------


def test_create_and_load_conversation(storage_service):
    """Test creating a conversation and fetching it back."""
    conv = storage_service.create_conversation(title="Test Chat")
    assert conv["id"] is not None
    assert conv["title"] == "Test Chat"

    loaded = storage_service.get_conversation(conv["id"])
    assert loaded is not None
    assert loaded["id"] == conv["id"]
    assert loaded["title"] == "Test Chat"
    assert loaded["messages"] == []


def test_create_new_chat(storage_service):
    """Test creating a new chat without deleting previous chats."""
    c1 = storage_service.create_conversation(title="Chat 1")
    c2 = storage_service.create_conversation(title="Chat 2")

    conversations = storage_service.list_conversations()
    ids = [c["id"] for c in conversations]
    assert c1["id"] in ids
    assert c2["id"] in ids


def test_save_user_and_assistant_messages(storage_service):
    """Test saving user and assistant messages, auto-generating title on first user turn."""
    conv = storage_service.create_conversation()
    cid = conv["id"]

    # 1. Save user message
    u_msg = storage_service.add_message(
        conversation_id=cid,
        role="user",
        content="Can I patent an Ayurvedic formulation containing Ashwagandha?",
    )
    assert u_msg["id"] is not None
    assert u_msg["role"] == "user"

    # Verify conversation title was auto-generated
    c_updated = storage_service.get_conversation(cid)
    assert c_updated["title"] == "Ayurvedic Patent Eligibility"

    # 2. Save assistant message with citation & confidence metadata
    assist_meta = {
        "answer": "An Ayurvedic formulation containing Ashwagandha may be eligible for patent protection under specific conditions [SOURCE_1].",
        "is_abstention": False,
        "confidence": {"score": 0.95, "evidence_count": 1, "citation_coverage": 1.0, "avg_rerank_score": 0.88, "below_threshold": False, "reason": "High confidence"},
        "evidence": [{"chunk_id": "c1", "doc_id": "d1", "source_name": "IP India Guidelines", "source_label": "[SOURCE_1]", "content": "Ashwagandha patents."}],
        "citations": [{"claim_snippet": "eligible for patent protection", "source_label": "[SOURCE_1]", "chunk_id": "c1", "is_grounded": True}],
    }
    a_msg = storage_service.add_message(
        conversation_id=cid,
        role="assistant",
        content=assist_meta,
    )
    assert a_msg["id"] is not None
    assert a_msg["role"] == "assistant"

    # 3. Reload conversation and check messages
    loaded = storage_service.get_conversation(cid)
    assert len(loaded["messages"]) == 2
    assert loaded["messages"][0]["role"] == "user"
    assert loaded["messages"][1]["role"] == "assistant"
    assert loaded["messages"][1]["metadata"]["confidence"]["score"] == 0.95


def test_switch_and_delete_conversations(storage_service):
    """Test switching between conversations and deleting one."""
    c1 = storage_service.create_conversation(title="Chat 1")
    c2 = storage_service.create_conversation(title="Chat 2")

    storage_service.add_message(c1["id"], "user", "Hello in Chat 1")
    storage_service.add_message(c2["id"], "user", "Hello in Chat 2")

    loaded_c1 = storage_service.get_conversation(c1["id"])
    loaded_c2 = storage_service.get_conversation(c2["id"])

    assert len(loaded_c1["messages"]) == 1
    assert loaded_c1["messages"][0]["content"] == "Hello in Chat 1"
    assert len(loaded_c2["messages"]) == 1
    assert loaded_c2["messages"][0]["content"] == "Hello in Chat 2"

    # Delete c1
    deleted = storage_service.delete_conversation(c1["id"])
    assert deleted is True

    assert storage_service.get_conversation(c1["id"]) is None
    assert storage_service.get_conversation(c2["id"]) is not None


def test_persistence_across_restart(temp_db_manager):
    """Test that conversations persist when creating a new service instance attached to same DB."""
    db_path = temp_db_manager.db_path
    svc1 = ChatStorageService(db_manager=temp_db_manager)
    c = svc1.create_conversation(title="Persistent Chat")
    svc1.add_message(c["id"], "user", "Can I patent Ashwagandha?")
    svc1.db.close()

    # Re-instantiate service with same DB file
    db2 = DatabaseManager(db_path=str(db_path))
    svc2 = ChatStorageService(db_manager=db2)

    try:
        loaded = svc2.get_conversation(c["id"])
        assert loaded is not None
        assert loaded["title"] == "Persistent Chat"
        assert len(loaded["messages"]) == 1
        assert loaded["messages"][0]["content"] == "Can I patent Ashwagandha?"
    finally:
        svc2.db.close()




# ---------------------------------------------------------------------------
# 3. Contextual Session Memory & Pipeline Follow-up Queries
# ---------------------------------------------------------------------------


def test_bounded_session_context_in_pipeline():
    """Test that PipelineCoordinator processes follow-up queries with bounded context."""
    coordinator = PipelineCoordinator()

    history = [
        ConversationMessageModel(
            role="user",
            content="I developed an Ayurvedic formulation containing Ashwagandha and Tulsi.",
        ),
        ConversationMessageModel(
            role="assistant",
            content="An Ayurvedic formulation containing Ashwagandha and Tulsi is subject to Section 3(p) of the Patents Act.",
        ),
    ]

    req = QueryRequest(
        raw_query="Can I patent it?",
        jurisdiction=Jurisdiction.INDIA,
        formulation_category=FormulationCategory.PROPRIETARY,
        conversation_history=history,
    )

    response = coordinator.execute(req)
    assert response is not None
    assert response.query_id == req.query_id


def test_empty_or_new_conversation(storage_service):
    """Test that a new/empty conversation loads cleanly with zero messages."""
    c = storage_service.create_conversation()
    conv_data = storage_service.get_conversation(c["id"])
    assert conv_data["messages"] == []


def test_citation_preservation(storage_service):
    """Test that citations and source labels are preserved exactly as saved."""
    c = storage_service.create_conversation(title="Citation Test")
    meta = {
        "answer": "According to Section 3(p) [SOURCE_1], traditional knowledge is not patentable.",
        "citations": [
            {
                "claim_snippet": "traditional knowledge is not patentable",
                "source_label": "[SOURCE_1]",
                "chunk_id": "chunk_3p_1",
                "is_grounded": True,
            }
        ],
        "evidence": [
            {
                "chunk_id": "chunk_3p_1",
                "doc_id": "doc_3p",
                "source_name": "Patents Act 1970",
                "source_label": "[SOURCE_1]",
                "content": "Section 3(p) excludes traditional knowledge.",
            }
        ],
    }

    storage_service.add_message(c["id"], "user", "What is Section 3(p)?")
    storage_service.add_message(c["id"], "assistant", meta)

    loaded = storage_service.get_conversation(c["id"])
    ast_msg = loaded["messages"][1]
    saved_meta = ast_msg["metadata"]

    assert saved_meta["citations"][0]["source_label"] == "[SOURCE_1]"
    assert saved_meta["evidence"][0]["source_name"] == "Patents Act 1970"


def test_storage_failure_fallback():
    """Test that database error in ChatStorageService does not raise exceptions."""
    invalid_db = DatabaseManager(db_path="/invalid_dir/non_existent/db.sqlite")
    svc = ChatStorageService(db_manager=invalid_db)

    # All methods should return safe fallbacks without crashing
    res_list = svc.list_conversations()
    assert isinstance(res_list, list)

    res_get = svc.get_conversation("non_existent_id")
    assert res_get is None

    res_del = svc.delete_conversation("non_existent_id")
    assert res_del is False

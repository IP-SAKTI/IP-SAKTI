"""
tests/test_db.py — Unit tests for ip_sakti.utils.db.

Tests that the DatabaseManager:
  - creates the SQLite file on initialise()
  - creates all required tables
  - is idempotent (initialise() can be called multiple times)
  - provides a working connection for basic SQL operations
"""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest

from ip_sakti.utils.db import DatabaseManager


class TestDatabaseManager:
    """Tests for DatabaseManager schema initialisation and connection."""

    def test_initialise_creates_file(self, tmp_db_path: Path) -> None:
        """initialise() creates the SQLite database file."""
        assert not tmp_db_path.exists()
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        assert tmp_db_path.exists()

    def test_initialise_is_idempotent(self, tmp_db_path: Path) -> None:
        """Calling initialise() twice does not raise an error."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        db.initialise()  # second call — must not raise

    def test_queries_table_exists(self, tmp_db_path: Path) -> None:
        """The 'queries' table is created after initialise()."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        cursor = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='queries';"
        )
        assert cursor.fetchone() is not None

    def test_escalations_table_exists(self, tmp_db_path: Path) -> None:
        """The 'escalations' table is created after initialise()."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        cursor = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='escalations';"
        )
        assert cursor.fetchone() is not None

    def test_documents_table_exists(self, tmp_db_path: Path) -> None:
        """The 'documents' table is created after initialise()."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        cursor = db.connection.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='documents';"
        )
        assert cursor.fetchone() is not None

    def test_queries_table_columns(self, tmp_db_path: Path) -> None:
        """The 'queries' table has the expected columns."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        cursor = db.connection.execute("PRAGMA table_info(queries);")
        columns = {row["name"] for row in cursor.fetchall()}
        expected = {
            "query_id", "raw_query", "detected_lang", "translated_query",
            "intent", "jurisdiction", "formulation_cat", "agents_invoked",
            "is_abstention", "confidence_score", "created_at",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_escalations_table_columns(self, tmp_db_path: Path) -> None:
        """The 'escalations' table has the expected columns."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        cursor = db.connection.execute("PRAGMA table_info(escalations);")
        columns = {row["name"] for row in cursor.fetchall()}
        expected = {"escalation_id", "query_id", "agent_type", "reason", "escalated_at"}
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_documents_table_columns(self, tmp_db_path: Path) -> None:
        """The 'documents' table has the expected columns."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        cursor = db.connection.execute("PRAGMA table_info(documents);")
        columns = {row["name"] for row in cursor.fetchall()}
        expected = {
            "doc_id", "title", "source_id", "source_name", "source_url",
            "authority", "document_type", "jurisdiction", "language",
            "publication_date", "permitted_use", "tags", "chunk_index",
            "parent_doc_id", "indexed_at",
        }
        assert expected.issubset(columns), f"Missing columns: {expected - columns}"

    def test_insert_and_query_queries_table(self, tmp_db_path: Path) -> None:
        """Basic INSERT and SELECT works on the 'queries' table."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.initialise()
        conn = db.connection
        conn.execute(
            """
            INSERT INTO queries (query_id, raw_query, is_abstention, created_at)
            VALUES (?, ?, ?, ?)
            """,
            ("test-uuid-001", "What is the patent procedure in India?", 0, "2026-09-03T00:00:00"),
        )
        conn.commit()
        cursor = conn.execute(
            "SELECT raw_query FROM queries WHERE query_id = ?", ("test-uuid-001",)
        )
        row = cursor.fetchone()
        assert row is not None
        assert row["raw_query"] == "What is the patent procedure in India?"

    def test_db_path_property(self, tmp_db_path: Path) -> None:
        """db_path property returns the configured path."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        assert db.db_path == tmp_db_path

    def test_close_does_not_raise(self, tmp_db_path: Path) -> None:
        """close() can be called safely even when no connection has been opened."""
        db = DatabaseManager(db_path=str(tmp_db_path))
        db.close()  # no connection yet — must not raise

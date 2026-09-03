"""
ip_sakti.utils.db — SQLite database manager.

Creates and manages the SQLite database schema required by the
frozen MVP architecture.

Tables
------
queries         — one row per user query; links to responses.
escalations     — safe-abstention escalation events.
documents       — lightweight registry of knowledge-base documents
                  (full content lives in FAISS/BM25 indexes).

Usage
-----
    from ip_sakti.utils.db import DatabaseManager

    db = DatabaseManager()
    db.initialise()        # idempotent — creates tables if absent
    conn = db.connection   # thread-local sqlite3.Connection
"""

from __future__ import annotations

import logging
import sqlite3
import threading
from pathlib import Path
from typing import Optional

from ip_sakti.utils.config import get_settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# DDL — kept here so schema and manager stay in one place
# ---------------------------------------------------------------------------

_CREATE_QUERIES_TABLE = """
CREATE TABLE IF NOT EXISTS queries (
    query_id        TEXT        PRIMARY KEY,
    raw_query       TEXT        NOT NULL,
    detected_lang   TEXT,
    translated_query TEXT,
    intent          TEXT,
    jurisdiction    TEXT,
    formulation_cat TEXT,
    agents_invoked  TEXT,           -- JSON array of agent ids
    is_abstention   INTEGER     NOT NULL DEFAULT 0,
    confidence_score REAL,
    created_at      TEXT        NOT NULL
);
"""

_CREATE_ESCALATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS escalations (
    escalation_id   INTEGER     PRIMARY KEY AUTOINCREMENT,
    query_id        TEXT        NOT NULL,
    agent_type      TEXT,
    reason          TEXT        NOT NULL,
    escalated_at    TEXT        NOT NULL,
    FOREIGN KEY (query_id) REFERENCES queries (query_id)
);
"""

_CREATE_DOCUMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS documents (
    doc_id          TEXT        PRIMARY KEY,
    title           TEXT        NOT NULL,
    source_id       TEXT        NOT NULL,
    source_name     TEXT        NOT NULL,
    source_url      TEXT,
    authority       TEXT,
    document_type   TEXT,
    jurisdiction    TEXT,
    language        TEXT        NOT NULL DEFAULT 'en',
    publication_date TEXT,
    permitted_use   INTEGER     NOT NULL DEFAULT 1,
    tags            TEXT,           -- JSON array
    chunk_index     INTEGER     NOT NULL DEFAULT 0,
    parent_doc_id   TEXT,
    indexed_at      TEXT
);
"""

_ALL_DDL = [
    _CREATE_QUERIES_TABLE,
    _CREATE_ESCALATIONS_TABLE,
    _CREATE_DOCUMENTS_TABLE,
]


class DatabaseManager:
    """
    Manages the SQLite connection and schema lifecycle.

    Thread-safety
    -------------
    Each thread gets its own ``sqlite3.Connection`` via a
    ``threading.local()`` store.  The schema is created on first
    access from any thread.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        """
        Initialise the manager.

        Parameters
        ----------
        db_path:
            Absolute or relative path to the SQLite file.
            If None, derived from ``config/settings.yaml``
            (``paths.db_dir`` / ``paths.db_name``).
        """
        if db_path is not None:
            self._db_path = Path(db_path)
        else:
            cfg = get_settings()
            self._db_path = (
                Path(cfg["paths"]["db_dir"]) / cfg["paths"]["db_name"]
            )

        self._local = threading.local()
        self._schema_created = False

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    @property
    def db_path(self) -> Path:
        """Resolved path to the SQLite database file."""
        return self._db_path

    def initialise(self) -> None:
        """
        Ensure the database file and all required tables exist.

        Idempotent — safe to call multiple times.
        """
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = self._get_connection()
        self._apply_schema(conn)
        logger.info("Database initialised", extra={"db_path": str(self._db_path)})

    @property
    def connection(self) -> sqlite3.Connection:
        """
        Return a thread-local SQLite connection, creating it if needed.

        The schema is applied lazily on first access per thread.
        """
        conn = self._get_connection()
        if not self._schema_created:
            self._apply_schema(conn)
        return conn

    def close(self) -> None:
        """Close the connection for the current thread, if open."""
        conn: sqlite3.Connection | None = getattr(self._local, "conn", None)
        if conn is not None:
            conn.close()
            self._local.conn = None
            logger.debug("Database connection closed")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_connection(self) -> sqlite3.Connection:
        """Return (or create) the thread-local connection."""
        if not hasattr(self._local, "conn") or self._local.conn is None:
            self._db_path.parent.mkdir(parents=True, exist_ok=True)
            conn = sqlite3.connect(
                str(self._db_path),
                check_same_thread=False,
                detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES,
            )
            conn.row_factory = sqlite3.Row
            # Enable WAL mode for better concurrent read performance
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA foreign_keys=ON;")
            self._local.conn = conn
            logger.debug(
                "Opened database connection",
                extra={"db_path": str(self._db_path), "thread": threading.current_thread().name},
            )
        return self._local.conn

    def _apply_schema(self, conn: sqlite3.Connection) -> None:
        """Execute all DDL statements if they have not been applied yet."""
        with conn:
            for ddl in _ALL_DDL:
                conn.execute(ddl)
        self._schema_created = True
        logger.debug("Schema applied", extra={"db_path": str(self._db_path)})

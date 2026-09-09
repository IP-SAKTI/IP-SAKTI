"""
ip_sakti.utils.db — Persistent Database Manager (Supabase PostgreSQL / Memory-Only).

Supabase PostgreSQL is the primary single source of truth for persistent application data.
SQLite file persistence has been removed per architecture requirements.
"""

from __future__ import annotations

import logging
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    In-memory / Supabase compatibility layer.

    Does not create or write to disk-based SQLite .db files.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._local = threading.local()
        self._schema_created = True

    def initialise(self) -> None:
        """Idempotent initialisation no-op."""
        logger.info("DatabaseManager initialised (Supabase PostgreSQL / Memory-Only mode).")

    def close(self) -> None:
        """Close connection no-op."""
        pass



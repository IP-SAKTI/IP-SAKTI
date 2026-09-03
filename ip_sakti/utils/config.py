"""
ip_sakti.utils.config — YAML configuration loader.

Loads config/settings.yaml (and optionally merges environment-variable
overrides) into a typed, cached settings object.  Every module should
import `get_settings()` rather than reading YAML directly.
"""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

# Load .env file if present (development convenience; never committed)
load_dotenv()

# Default path to the master settings file, relative to the repository root.
_DEFAULT_SETTINGS_PATH = Path(__file__).parent.parent.parent / "config" / "settings.yaml"


def _load_yaml(path: Path) -> dict[str, Any]:
    """Read and parse a YAML file, returning a plain dict."""
    if not path.exists():
        raise FileNotFoundError(
            f"Configuration file not found: {path}. "
            "Ensure config/settings.yaml exists in the repository root."
        )
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data or {}


def _apply_env_overrides(cfg: dict[str, Any]) -> dict[str, Any]:
    """
    Merge environment variable overrides into the loaded config dict.

    Supported env var → config path mappings:
      LOG_LEVEL           → logging.level
      LOG_FORMAT          → logging.format
      INDEX_DIR           → paths.index_dir
      DB_DIR              → paths.db_dir
      DATA_DIR            → paths.data_dir
      DB_NAME             → paths.db_name
      GEMINI_MODEL        → models.llm_model
      FAISS_TOP_K         → retrieval.faiss_top_k
      BM25_TOP_K          → retrieval.bm25_top_k
      RERANK_TOP_K        → retrieval.rerank_top_k
      CONFIDENCE_THRESHOLD→ safety.confidence_threshold
      API_HOST            → api.host
      API_PORT            → api.port
      API_BASE_URL        → ui.api_base_url
    """
    overrides: list[tuple[list[str], str, type]] = [
        (["logging", "level"], "LOG_LEVEL", str),
        (["logging", "format"], "LOG_FORMAT", str),
        (["paths", "index_dir"], "INDEX_DIR", str),
        (["paths", "db_dir"], "DB_DIR", str),
        (["paths", "data_dir"], "DATA_DIR", str),
        (["paths", "db_name"], "DB_NAME", str),
        (["models", "llm_model"], "GEMINI_MODEL", str),
        (["retrieval", "faiss_top_k"], "FAISS_TOP_K", int),
        (["retrieval", "bm25_top_k"], "BM25_TOP_K", int),
        (["retrieval", "rerank_top_k"], "RERANK_TOP_K", int),
        (["safety", "confidence_threshold"], "CONFIDENCE_THRESHOLD", float),
        (["api", "host"], "API_HOST", str),
        (["api", "port"], "API_PORT", int),
        (["ui", "api_base_url"], "API_BASE_URL", str),
    ]

    for key_path, env_var, cast in overrides:
        raw = os.environ.get(env_var)
        if raw is not None:
            node = cfg
            for key in key_path[:-1]:
                node = node.setdefault(key, {})
            try:
                node[key_path[-1]] = cast(raw)
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"Environment variable {env_var}={raw!r} cannot be cast to {cast.__name__}: {exc}"
                ) from exc

    return cfg


@lru_cache(maxsize=1)
def get_settings(settings_path: str | None = None) -> dict[str, Any]:
    """
    Load, cache, and return the application settings dictionary.

    Parameters
    ----------
    settings_path:
        Absolute or relative path to a settings YAML file.
        Defaults to ``config/settings.yaml`` at the repository root.

    Returns
    -------
    dict[str, Any]
        Merged settings with environment variable overrides applied.

    Raises
    ------
    FileNotFoundError
        If the settings file does not exist.
    """
    path = Path(settings_path) if settings_path else _DEFAULT_SETTINGS_PATH
    cfg = _load_yaml(path)
    cfg = _apply_env_overrides(cfg)
    return cfg


def reload_settings(settings_path: str | None = None) -> dict[str, Any]:
    """
    Clear the settings cache and reload from disk.

    Useful in tests where the config path changes between test cases.
    """
    get_settings.cache_clear()
    return get_settings(settings_path)

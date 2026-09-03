"""
tests/test_ui/test_ui_helpers.py

Unit tests for Streamlit UI helper functions.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from ip_sakti.ui.app import query_backend_api


class TestUIHelpers:
    @patch("ip_sakti.ui.app.httpx.post")
    def test_query_backend_api_success(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "query_id": "test-uuid",
            "answer": "Test answer",
            "is_abstention": False,
            "evidence": [],
            "citations": [],
            "agents_invoked": ["ip_agent"],
            "disclaimer": "Test disclaimer",
        }
        mock_post.return_value = mock_response

        res = query_backend_api(
            raw_query="Test query",
            jurisdiction="india",
            formulation_category="classical",
            user_language="en",
            api_base_url="http://localhost:8000",
        )

        assert res["answer"] == "Test answer"
        assert res["is_abstention"] is False
        mock_post.assert_called_once()

    @patch("ip_sakti.ui.app.httpx.post")
    def test_query_backend_api_auto_language_conversion(self, mock_post: MagicMock) -> None:
        mock_response = MagicMock()
        mock_response.json.return_value = {"answer": "OK"}
        mock_post.return_value = mock_response

        query_backend_api(
            raw_query="Test query",
            jurisdiction="india",
            formulation_category="classical",
            user_language="auto",
            api_base_url="http://localhost:8000",
        )

        args, kwargs = mock_post.call_args
        assert kwargs["json"]["user_language"] is None

"""
tests/test_retrieval/test_embeddings.py

Unit tests for ip_sakti.retrieval.embeddings.EmbeddingGenerator.
Uses mocking to avoid downloading real model weights during unit testing.
"""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import numpy as np
import pytest

from ip_sakti.retrieval.embeddings import EmbeddingGenerator
from ip_sakti.retrieval.exceptions import RetrievalError


@pytest.fixture()
def mock_sentence_transformer() -> MagicMock:
    model = MagicMock()
    model.get_sentence_embedding_dimension.return_value = 384
    # Mock encode to return normalized 384-dim mock vectors
    def fake_encode(texts, **kwargs): # noqa: ANN001, ANN003
        n = len(texts)
        vecs = np.ones((n, 384), dtype=np.float32)
        # Normalize rows
        norms = np.linalg.norm(vecs, axis=1, keepdims=True)
        return vecs / norms

    model.encode.side_effect = fake_encode
    return model


class TestEmbeddingGenerator:
    @patch("ip_sakti.retrieval.embeddings.SentenceTransformer")
    def test_embed_texts_returns_normalized_array(
        self, mock_st_cls: MagicMock, mock_sentence_transformer: MagicMock
    ) -> None:
        mock_st_cls.return_value = mock_sentence_transformer
        gen = EmbeddingGenerator(model_name="dummy-model")

        texts = ["Patent application for Ayurveda", "Access and benefit sharing"]
        embeddings = gen.embed_texts(texts)

        assert isinstance(embeddings, np.ndarray)
        assert embeddings.shape == (2, 384)
        assert embeddings.dtype == np.float32

        # Check normalization (L2 norm ≈ 1.0)
        norms = np.linalg.norm(embeddings, axis=1)
        np.testing.assert_allclose(norms, 1.0, rtol=1e-5)

    @patch("ip_sakti.retrieval.embeddings.SentenceTransformer")
    def test_embed_query_returns_1d_array(
        self, mock_st_cls: MagicMock, mock_sentence_transformer: MagicMock
    ) -> None:
        mock_st_cls.return_value = mock_sentence_transformer
        gen = EmbeddingGenerator(model_name="dummy-model")

        q_vec = gen.embed_query("ayush regulations")

        assert isinstance(q_vec, np.ndarray)
        assert q_vec.shape == (384,)
        assert q_vec.dtype == np.float32

    def test_embed_empty_texts_returns_empty_array(self) -> None:
        gen = EmbeddingGenerator()
        empty_res = gen.embed_texts([])
        assert empty_res.shape[0] == 0

    def test_embed_empty_query_raises_error(self) -> None:
        gen = EmbeddingGenerator()
        with pytest.raises(RetrievalError, match="empty query"):
            gen.embed_query("   ")

    @patch("ip_sakti.retrieval.embeddings.SentenceTransformer")
    def test_model_load_failure_raises_retrieval_error(self, mock_st_cls: MagicMock) -> None:
        mock_st_cls.side_effect = RuntimeError("Model file corrupt")
        gen = EmbeddingGenerator(model_name="corrupt-model")

        with pytest.raises(RetrievalError, match="Failed to load embedding model"):
            gen.embed_texts(["test"])

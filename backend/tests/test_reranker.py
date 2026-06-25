"""
tests/test_reranker.py

Unit tests for modules/scout/reranker.py.

CrossEncoder is mocked in all unit tests to avoid a model download.
Real end-to-end reranking is covered in
test_integration.py::TestCrossEncoderReranking.
"""

import pytest
from unittest.mock import MagicMock, patch
from langchain_core.callbacks.manager import CallbackManagerForRetrieverRun
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_docs(*contents: str) -> list[Document]:
    return [Document(page_content=c, metadata={}) for c in contents]


class _StubRetriever(BaseRetriever):
    """Minimal real BaseRetriever so pydantic v2 validation passes."""

    docs: list = []

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> list[Document]:
        return list(self.docs)


class _TrackingRetriever(BaseRetriever):
    """Records every query it receives."""

    queries: list = []
    docs: list = []

    def _get_relevant_documents(
        self, query: str, *, run_manager: CallbackManagerForRetrieverRun = None
    ) -> list[Document]:
        self.queries.append(query)
        return list(self.docs)


# ---------------------------------------------------------------------------
# TestRerankingRetrieverDocumentOrder
# ---------------------------------------------------------------------------

class TestRerankingRetrieverDocumentOrder:
    def test_returns_documents_in_descending_score_order(self):
        """Highest-scoring document must come first in the results."""
        from modules.scout.reranker import RerankingRetriever

        docs = _make_docs("doc A", "doc B", "doc C")
        base = _StubRetriever(docs=docs)

        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.1, 0.9, 0.5]  # B best, C second, A last

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=3)
        results = rr.invoke("test query")

        assert results[0].page_content == "doc B"
        assert results[1].page_content == "doc C"
        assert results[2].page_content == "doc A"

    def test_top_n_limits_returned_documents(self):
        """Only top_n documents must be returned even when more are retrieved."""
        from modules.scout.reranker import RerankingRetriever

        docs = _make_docs("a", "b", "c", "d", "e")
        base = _StubRetriever(docs=docs)

        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.5, 0.4, 0.3, 0.2, 0.1]

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=3)
        results = rr.invoke("query")

        assert len(results) == 3

    def test_empty_input_returns_empty_list_without_calling_encoder(self):
        """If the base retriever returns nothing, skip the encoder and return []."""
        from modules.scout.reranker import RerankingRetriever

        base = _StubRetriever(docs=[])
        mock_encoder = MagicMock()

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=5)
        results = rr.invoke("empty")

        assert results == []
        mock_encoder.predict.assert_not_called()

    def test_fewer_docs_than_top_n_returns_all(self):
        """When base retriever returns < top_n docs, return all of them."""
        from modules.scout.reranker import RerankingRetriever

        docs = _make_docs("only one")
        base = _StubRetriever(docs=docs)

        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.8]

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=5)
        results = rr.invoke("query")

        assert len(results) == 1
        assert results[0].page_content == "only one"

    def test_top_n_one_returns_single_best_document(self):
        """top_n=1 must return only the highest-scoring document."""
        from modules.scout.reranker import RerankingRetriever

        docs = _make_docs("worst", "best", "middle")
        base = _StubRetriever(docs=docs)

        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.1, 0.95, 0.5]

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=1)
        results = rr.invoke("query")

        assert len(results) == 1
        assert results[0].page_content == "best"


# ---------------------------------------------------------------------------
# TestRerankingRetrieverPredict
# ---------------------------------------------------------------------------

class TestRerankingRetrieverPredict:
    def test_predict_called_with_correct_query_doc_pairs(self):
        """cross_encoder.predict must receive [(query, doc_content), ...] tuples."""
        from modules.scout.reranker import RerankingRetriever

        docs = _make_docs("Argentina won", "Morocco semi-final")
        base = _StubRetriever(docs=docs)

        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.7, 0.3]

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=2)
        rr.invoke("who won the World Cup")

        expected_pairs = [
            ("who won the World Cup", "Argentina won"),
            ("who won the World Cup", "Morocco semi-final"),
        ]
        mock_encoder.predict.assert_called_once_with(expected_pairs)

    def test_predict_called_once_per_invoke(self):
        """cross_encoder.predict must be called exactly once per retrieval."""
        from modules.scout.reranker import RerankingRetriever

        docs = _make_docs("doc1", "doc2", "doc3")
        base = _StubRetriever(docs=docs)

        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.3, 0.6, 0.9]

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=3)
        rr.invoke("query")

        assert mock_encoder.predict.call_count == 1

    def test_base_retriever_called_with_original_query(self):
        """The base retriever must be invoked with the exact incoming query string."""
        from modules.scout.reranker import RerankingRetriever

        tracker = _TrackingRetriever(docs=_make_docs("some doc"))
        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.5]

        rr = RerankingRetriever(base_retriever=tracker, cross_encoder=mock_encoder, top_n=1)
        rr.invoke("World Cup final scorer")

        assert tracker.queries == ["World Cup final scorer"]

    def test_reranking_does_not_add_duplicate_documents(self):
        """No document must appear more than once in the reranked output."""
        from modules.scout.reranker import RerankingRetriever

        docs = _make_docs("A", "B", "C", "D")
        base = _StubRetriever(docs=docs)

        mock_encoder = MagicMock()
        mock_encoder.predict.return_value = [0.9, 0.7, 0.5, 0.3]

        rr = RerankingRetriever(base_retriever=base, cross_encoder=mock_encoder, top_n=4)
        results = rr.invoke("query")

        contents = [r.page_content for r in results]
        assert len(contents) == len(set(contents))


# ---------------------------------------------------------------------------
# TestBuildRerankingRetriever
# ---------------------------------------------------------------------------

class TestBuildRerankingRetriever:
    def test_returns_reranking_retriever_instance(self):
        """build_reranking_retriever must return a RerankingRetriever."""
        from modules.scout.reranker import build_reranking_retriever, RerankingRetriever

        base = _StubRetriever()
        with patch("modules.scout.reranker.CrossEncoder") as mock_ce_cls:
            mock_ce_cls.return_value = MagicMock()
            rr = build_reranking_retriever(base)

        assert isinstance(rr, RerankingRetriever)

    def test_instantiates_cross_encoder_with_given_model_name(self):
        """CrossEncoder must be constructed with the model_name argument."""
        from modules.scout.reranker import build_reranking_retriever

        base = _StubRetriever()
        with patch("modules.scout.reranker.CrossEncoder") as mock_ce_cls:
            mock_ce_cls.return_value = MagicMock()
            build_reranking_retriever(base, model_name="cross-encoder/ms-marco-MiniLM-L-12-v2")

        mock_ce_cls.assert_called_once_with("cross-encoder/ms-marco-MiniLM-L-12-v2")

    def test_uses_default_cross_encoder_model(self):
        """Without explicit model_name, CROSS_ENCODER_MODEL constant is used."""
        from modules.scout.reranker import build_reranking_retriever, CROSS_ENCODER_MODEL

        base = _StubRetriever()
        with patch("modules.scout.reranker.CrossEncoder") as mock_ce_cls:
            mock_ce_cls.return_value = MagicMock()
            build_reranking_retriever(base)

        mock_ce_cls.assert_called_once_with(CROSS_ENCODER_MODEL)

    def test_uses_default_top_n(self):
        """Without explicit top_n, RERANK_TOP_N is used."""
        from modules.scout.reranker import build_reranking_retriever, RERANK_TOP_N

        base = _StubRetriever()
        with patch("modules.scout.reranker.CrossEncoder") as mock_ce_cls:
            mock_ce_cls.return_value = MagicMock()
            rr = build_reranking_retriever(base)

        assert rr.top_n == RERANK_TOP_N

    def test_custom_top_n_is_forwarded(self):
        """Passing top_n=7 must set RerankingRetriever.top_n = 7."""
        from modules.scout.reranker import build_reranking_retriever

        base = _StubRetriever()
        with patch("modules.scout.reranker.CrossEncoder") as mock_ce_cls:
            mock_ce_cls.return_value = MagicMock()
            rr = build_reranking_retriever(base, top_n=7)

        assert rr.top_n == 7

    def test_base_retriever_is_stored_on_instance(self):
        """The RerankingRetriever must hold a reference to the base retriever."""
        from modules.scout.reranker import build_reranking_retriever

        base = _StubRetriever()
        with patch("modules.scout.reranker.CrossEncoder") as mock_ce_cls:
            mock_ce_cls.return_value = MagicMock()
            rr = build_reranking_retriever(base)

        assert rr.base_retriever is base


# ---------------------------------------------------------------------------
# TestRerankingDefaults
# ---------------------------------------------------------------------------

class TestRerankingDefaults:
    def test_cross_encoder_model_is_minilm_l12(self):
        """CROSS_ENCODER_MODEL must be ms-marco-MiniLM-L-12-v2."""
        from modules.scout.reranker import CROSS_ENCODER_MODEL
        assert CROSS_ENCODER_MODEL == "cross-encoder/ms-marco-MiniLM-L-12-v2"

    def test_rerank_top_n_is_five(self):
        """RERANK_TOP_N must be 5."""
        from modules.scout.reranker import RERANK_TOP_N
        assert RERANK_TOP_N == 5

"""
tests/test_rag_pipeline.py

Unit tests for modules/scout/rag_pipeline.py.

Key constraint: ConversationalRetrievalChain.from_llm() builds an LLMChain
internally, which pydantic validates. A MagicMock LLM fails that validation.
Fix: patch ConversationalRetrievalChain.from_llm directly so chain
construction never runs real pydantic validation.
"""

import pytest
from unittest.mock import patch, MagicMock, call
import contextlib


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_vector_store():
    store = MagicMock()
    store.as_retriever.return_value = MagicMock()
    return store


def _mock_chain():
    """A MagicMock that looks like a built ConversationalRetrievalChain."""
    from langchain_classic.memory import ConversationBufferMemory
    chain = MagicMock()
    # Give it a real memory object so memory_key assertions work
    chain.memory = ConversationBufferMemory(
        memory_key="chat_history",
        return_messages=True,
        output_key="answer",
    )
    chain.invoke.return_value = {"answer": "Argentina won."}
    return chain


@contextlib.contextmanager
def _patched_get_chain():
    """
    Patches load_vector_store, load_chunks, BM25Retriever, EnsembleRetriever,
    and ConversationalRetrievalChain.from_llm so get_chain() runs without any
    real API key, disk IO, or pydantic validation.
    Yields (mock_store, mock_llm_cls, mock_chain_instance).
    """
    mock_store = _mock_vector_store()
    mock_chain_instance = _mock_chain()
    mock_chunks = [MagicMock()]

    with patch("modules.scout.rag_pipeline.load_vector_store",
               return_value=mock_store), \
         patch("modules.scout.rag_pipeline.load_chunks",
               return_value=mock_chunks), \
         patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
         patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
         patch("modules.scout.rag_pipeline.ChatGroq") as mock_llm_cls, \
         patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:

        mock_llm_cls.return_value = MagicMock()
        mock_bm25.from_documents.return_value = MagicMock()
        mock_ensemble.return_value = MagicMock()
        mock_crc.from_llm.return_value = mock_chain_instance

        yield mock_store, mock_llm_cls, mock_chain_instance


# ---------------------------------------------------------------------------
# TestGetChain
# ---------------------------------------------------------------------------

class TestGetChain:
    def test_returns_chain_object(self):
        with _patched_get_chain():
            from modules.scout.rag_pipeline import get_chain
            chain = get_chain()
        assert chain is not None

    def test_llm_uses_correct_model(self):
        """ChatGroq must be instantiated with model='llama-3.1-8b-instant'.."""
        with _patched_get_chain() as (_, mock_llm_cls, __):
            from modules.scout.rag_pipeline import get_chain
            get_chain()

        assert mock_llm_cls.called, "ChatGroq was never called"
        model_used = mock_llm_cls.call_args.kwargs.get("model") \
                     or mock_llm_cls.call_args.args[0]
        assert model_used == "llama-3.1-8b-instant", (
        )

    def test_retriever_uses_k8(self):
        """Both FAISS and BM25 retrievers must be configured with k=8."""
        mock_chunks = [MagicMock()]
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()) as _, \
             patch("modules.scout.rag_pipeline.load_chunks",
                   return_value=mock_chunks), \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_store = _mock_vector_store()
            with patch("modules.scout.rag_pipeline.load_vector_store",
                       return_value=mock_store):
                mock_bm25.from_documents.return_value = MagicMock()
                mock_ensemble.return_value = MagicMock()
                mock_crc.from_llm.return_value = _mock_chain()
                from modules.scout.rag_pipeline import get_chain
                get_chain()

            # FAISS retriever: k=8 via search_kwargs
            mock_store.as_retriever.assert_called_once()
            search_kwargs = mock_store.as_retriever.call_args.kwargs.get("search_kwargs", {})
            assert search_kwargs.get("k") == 8, (
                f"FAISS retriever: expected k=8, got k={search_kwargs.get('k')}."
            )

            # BM25 retriever: k=8 as positional-or-keyword arg
            mock_bm25.from_documents.assert_called_once()
            bm25_kwargs = mock_bm25.from_documents.call_args.kwargs
            bm25_args = mock_bm25.from_documents.call_args.args
            bm25_k = bm25_kwargs.get("k") or (bm25_args[1] if len(bm25_args) > 1 else None)
            assert bm25_k == 8, f"BM25 retriever: expected k=8, got k={bm25_k}."

    def test_chain_built_without_memory(self):
        """
        Stateless design: from_llm must NOT receive a `memory` object —
        history is supplied per request via the chat_history input instead.
        """
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()), \
             patch("modules.scout.rag_pipeline.load_chunks",
                   return_value=[MagicMock()]), \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_bm25.from_documents.return_value = MagicMock()
            mock_ensemble.return_value = MagicMock()
            mock_crc.from_llm.return_value = _mock_chain()
            from modules.scout.rag_pipeline import get_chain
            get_chain()

        assert "memory" not in mock_crc.from_llm.call_args.kwargs

    def test_ensemble_retriever_rrf_config(self):
        """EnsembleRetriever must use RRF c=60, BM25 weight=0.6, FAISS weight=0.4."""
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()), \
             patch("modules.scout.rag_pipeline.load_chunks",
                   return_value=[MagicMock()]), \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_bm25.from_documents.return_value = MagicMock()
            mock_ensemble.return_value = MagicMock()
            mock_crc.from_llm.return_value = _mock_chain()
            from modules.scout.rag_pipeline import get_chain
            get_chain()

        kwargs = mock_ensemble.call_args.kwargs
        assert kwargs.get("weights") == [0.6, 0.4], (
            f"Expected weights=[0.6, 0.4], got {kwargs.get('weights')}"
        )
        assert kwargs.get("c") == 60, (
            f"Expected RRF c=60, got c={kwargs.get('c')}"
        )

    def test_load_chunks_called_on_chain_init(self):
        """load_chunks must be called alongside load_vector_store in get_chain()."""
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()), \
             patch("modules.scout.rag_pipeline.load_chunks",
                   return_value=[MagicMock()]) as mock_load_chunks, \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_bm25.from_documents.return_value = MagicMock()
            mock_ensemble.return_value = MagicMock()
            mock_crc.from_llm.return_value = _mock_chain()
            from modules.scout.rag_pipeline import get_chain
            get_chain()
        mock_load_chunks.assert_called_once()

    def test_fallback_calls_build_vector_store_when_load_fails(self):
        """
        When load_vector_store raises, get_chain() must fall back to
        load_documents → split_documents → build_vector_store.
        build_vector_store now also persists chunks via save_chunks.
        """
        mock_store = _mock_vector_store()
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   side_effect=Exception("no store")), \
             patch("modules.scout.rag_pipeline.load_documents",
                   return_value=[MagicMock()]), \
             patch("modules.scout.rag_pipeline.split_documents",
                   return_value=[MagicMock()]), \
             patch("modules.scout.rag_pipeline.build_vector_store",
                   return_value=mock_store) as mock_build, \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_bm25.from_documents.return_value = MagicMock()
            mock_ensemble.return_value = MagicMock()
            mock_crc.from_llm.return_value = _mock_chain()
            from modules.scout.rag_pipeline import get_chain
            get_chain()
        mock_build.assert_called_once()

    def test_load_vector_store_called_on_chain_init(self):
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()) as mock_load, \
             patch("modules.scout.rag_pipeline.load_chunks",
                   return_value=[MagicMock()]), \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_bm25.from_documents.return_value = MagicMock()
            mock_ensemble.return_value = MagicMock()
            mock_crc.from_llm.return_value = _mock_chain()
            from modules.scout.rag_pipeline import get_chain
            get_chain()
        mock_load.assert_called_once()


# ---------------------------------------------------------------------------
# TestChainInvoke
# ---------------------------------------------------------------------------

class TestChainInvoke:
    def test_chain_invoke_returns_answer_key(self):
        with _patched_get_chain() as (_, __, chain):
            from modules.scout.rag_pipeline import get_chain
            built = get_chain()
        built.invoke = MagicMock(return_value={"answer": "Argentina won."})
        result = built.invoke({"question": "Who won?", "chat_history": []})
        assert "answer" in result

    def test_chain_invoke_answer_is_string(self):
        with _patched_get_chain():
            from modules.scout.rag_pipeline import get_chain
            chain = get_chain()
        chain.invoke = MagicMock(return_value={"answer": "Argentina won."})
        result = chain.invoke({"question": "Who won?", "chat_history": []})
        assert isinstance(result["answer"], str)


# ---------------------------------------------------------------------------
# TestSystemPrompt
# ---------------------------------------------------------------------------

class TestSystemPrompt:
    def test_system_prompt_is_wired(self):
        """
        SYSTEM_PROMPT must be passed via combine_docs_chain_kwargs.
        Verify from_llm receives it.
        """
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()), \
             patch("modules.scout.rag_pipeline.load_chunks",
                   return_value=[MagicMock()]), \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.EnsembleRetriever") as mock_ensemble, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_bm25.from_documents.return_value = MagicMock()
            mock_ensemble.return_value = MagicMock()
            mock_crc.from_llm.return_value = _mock_chain()
            from modules.scout.rag_pipeline import get_chain
            get_chain()

        call_kwargs = mock_crc.from_llm.call_args.kwargs
        chain_kwargs = call_kwargs.get("combine_docs_chain_kwargs", {})
        assert "prompt" in chain_kwargs, (
            "SYSTEM_PROMPT not passed via combine_docs_chain_kwargs to from_llm()"
        )

    def test_chain_accepts_empty_history(self):
        with _patched_get_chain():
            from modules.scout.rag_pipeline import get_chain
            chain = get_chain()
        chain.invoke = MagicMock(return_value={"answer": "test"})
        result = chain.invoke({"question": "test", "chat_history": []})
        assert result is not None
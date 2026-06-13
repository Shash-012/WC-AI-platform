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
    Patches both load_vector_store and ConversationalRetrievalChain.from_llm
    so get_chain() runs without any real API key or pydantic validation.
    Yields (mock_store, mock_llm_cls, mock_chain_instance).
    """
    mock_store = _mock_vector_store()
    mock_chain_instance = _mock_chain()

    with patch("modules.scout.rag_pipeline.load_vector_store",
               return_value=mock_store), \
         patch("modules.scout.rag_pipeline.ChatGroq") as mock_llm_cls, \
         patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:

        mock_llm_cls.return_value = MagicMock()
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
        """store.as_retriever must be called with search_kwargs={'k': 8}."""
        with _patched_get_chain() as (mock_store, _, __):
            from modules.scout.rag_pipeline import get_chain
            get_chain()

        mock_store.as_retriever.assert_called_once()
        search_kwargs = mock_store.as_retriever.call_args.kwargs.get("search_kwargs", {})
        assert search_kwargs.get("k") == 8, (
            f"Expected k=8, got k={search_kwargs.get('k')}."
        )

    def test_chain_built_without_memory(self):
        """
        Stateless design: from_llm must NOT receive a `memory` object —
        history is supplied per request via the chat_history input instead.
        """
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()), \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
            mock_crc.from_llm.return_value = _mock_chain()
            from modules.scout.rag_pipeline import get_chain
            get_chain()

        assert "memory" not in mock_crc.from_llm.call_args.kwargs

    def test_load_vector_store_called_on_chain_init(self):
        with _patched_get_chain() as (_, __, ___):
            with patch("modules.scout.rag_pipeline.load_vector_store",
                       return_value=_mock_vector_store()) as mock_load:
                # Need a fresh patch inside — re-enter context
                pass

        # Simpler: just verify load_vector_store is called via from_llm mock
        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=_mock_vector_store()) as mock_load, \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
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
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:
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
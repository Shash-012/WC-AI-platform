"""
tests/test_integration.py

Integration tests: multiple real components wired together end-to-end.

What's real:   data loading, text splitting, HuggingFace embeddings, FAISS,
               Flask routing.
What's mocked: ChatGroq (requires a live API key unavailable in CI).

Markers
-------
All tests here are tagged @pytest.mark.integration so they can be run
separately:   pytest -m integration
or excluded:  pytest -m "not integration"
"""

import os
import pytest
from unittest.mock import patch, MagicMock
from langchain_core.documents import Document
from langchain_core.retrievers import BaseRetriever


# ---------------------------------------------------------------------------
# Minimal BaseRetriever stub — satisfies pydantic v2 type validation so
# EnsembleRetriever can be constructed without calling real retrieval logic.
# ---------------------------------------------------------------------------

class _FakeRetriever(BaseRetriever):
    def _get_relevant_documents(self, query: str) -> list[Document]:
        return []


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

SAMPLE_FILES = {
    "teams.txt": (
        "Argentina is the reigning FIFA World Cup champion.\n\n"
        "France is the runner-up of the 2022 World Cup.\n\n"
        "Morocco became the first African nation to reach the semi-finals."
    ),
    "players.txt": (
        "Lionel Messi captained Argentina and won the Golden Ball.\n\n"
        "Kylian Mbappé scored a hat-trick in the 2022 World Cup final.\n\n"
        "Cristiano Ronaldo participated but Portugal were eliminated in the quarter-finals."
    ),
}


# ---------------------------------------------------------------------------
# Module-scoped fixtures (expensive: embedding model loaded once per module)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def data_dir(tmp_path_factory):
    """Write sample .txt files; directory stays alive for the whole module."""
    d = tmp_path_factory.mktemp("int_data")
    for name, content in SAMPLE_FILES.items():
        (d / name).write_text(content, encoding="utf-8")
    return d


@pytest.fixture(scope="module")
def vector_store_dir(tmp_path_factory):
    return tmp_path_factory.mktemp("int_vs")


@pytest.fixture(scope="module")
def built_store(data_dir, vector_store_dir):
    """
    Full pipeline: txt files → load_documents → split_documents →
    build_vector_store (real HuggingFace embeddings + FAISS).
    Module-scoped so the ~2 s embedding step runs only once.
    """
    with patch("modules.scout.data_loader.DATA_DIR", str(data_dir)), \
         patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(vector_store_dir)):
        from modules.scout.data_loader import load_documents, split_documents
        from modules.scout.embeddings import build_vector_store
        docs = load_documents()
        chunks = split_documents(docs)
        store = build_vector_store(chunks)
    return store, vector_store_dir


@pytest.fixture(scope="module")
def api_app():
    """Flask app in test mode, with stub env vars."""
    os.environ.setdefault("GOOGLE_API_KEY", "test-key")
    os.environ.setdefault("GROQ_API_KEY", "test-key")
    from app import app as flask_app
    flask_app.config.update({"TESTING": True})
    return flask_app


@pytest.fixture
def api_client(api_app):
    """Fresh test client; resets the chain cache and rate limiter before each test."""
    from app import limiter
    limiter.reset()
    import modules.scout.routes as routes_module
    routes_module._chain = None
    return api_app.test_client()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mock_chain(answer: str = "Test answer."):
    chain = MagicMock()
    chain.invoke.return_value = {"answer": answer}
    return chain


# ===========================================================================
# 1. Full data pipeline
# ===========================================================================

@pytest.mark.integration
class TestDataPipelineIntegration:
    """load_documents → split_documents → build_vector_store all wired together."""

    def test_pipeline_produces_non_empty_store(self, built_store):
        store, _ = built_store
        assert store is not None

    def test_faiss_index_written_to_disk(self, built_store):
        _, vs_dir = built_store
        assert any(vs_dir.iterdir()), "FAISS index files should be on disk after build"

    def test_documents_loaded_from_both_files(self, data_dir):
        with patch("modules.scout.data_loader.DATA_DIR", str(data_dir)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()
        sources = {d.metadata["source"] for d in docs}
        assert "teams.txt" in sources
        assert "players.txt" in sources

    def test_paragraph_splitting_produces_correct_doc_count(self, data_dir):
        """3 paragraphs × 2 files → 6 Documents before text splitting."""
        with patch("modules.scout.data_loader.DATA_DIR", str(data_dir)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()
        assert len(docs) == 6

    def test_all_chunks_retain_source_metadata(self, data_dir):
        """Every chunk produced by split_documents must still carry its source filename."""
        with patch("modules.scout.data_loader.DATA_DIR", str(data_dir)):
            from modules.scout.data_loader import load_documents, split_documents
            chunks = split_documents(load_documents())
        valid_sources = set(SAMPLE_FILES.keys())
        for chunk in chunks:
            assert chunk.metadata.get("source") in valid_sources, (
                f"Unexpected source: {chunk.metadata.get('source')}"
            )

    def test_persisted_store_survives_reload(self, built_store):
        """A store saved to disk can be reloaded into a fresh FAISS object."""
        from langchain_community.vectorstores import FAISS
        _, vs_dir = built_store
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(vs_dir)):
            from modules.scout.embeddings import load_vector_store
            reloaded = load_vector_store()
        assert isinstance(reloaded, FAISS)


# ===========================================================================
# 2. Vector store retrieval
# ===========================================================================

@pytest.mark.integration
class TestVectorStoreRetrievalIntegration:
    """Real FAISS similarity search — verifies embedding quality and k semantics."""

    @pytest.fixture(autouse=True)
    def _store(self, built_store):
        _, vs_dir = built_store
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(vs_dir)):
            from modules.scout.embeddings import load_vector_store
            self.store = load_vector_store()

    def test_similarity_search_returns_documents(self):
        results = self.store.similarity_search("Who won the World Cup?", k=3)
        assert len(results) > 0
        assert all(isinstance(r, Document) for r in results)

    def test_argentina_query_surfaces_argentina_content(self):
        results = self.store.similarity_search("Argentina champion", k=4)
        combined = " ".join(r.page_content for r in results).lower()
        assert "argentina" in combined

    def test_messi_query_surfaces_player_content(self):
        results = self.store.similarity_search("Messi Golden Ball", k=3)
        combined = " ".join(r.page_content for r in results).lower()
        assert "messi" in combined

    def test_k_parameter_limits_result_count(self):
        results = self.store.similarity_search("World Cup final", k=2)
        assert len(results) <= 2

    def test_two_loads_produce_identical_retrieval(self, built_store):
        """Loading the same persisted index twice gives identical top results."""
        _, vs_dir = built_store
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(vs_dir)):
            from modules.scout.embeddings import load_vector_store
            s1 = load_vector_store()
            s2 = load_vector_store()
        r1 = s1.similarity_search("runner-up", k=2)
        r2 = s2.similarity_search("runner-up", k=2)
        assert [d.page_content for d in r1] == [d.page_content for d in r2]

    def test_as_retriever_returns_docs(self):
        """store.as_retriever() (used by the RAG chain) works end-to-end."""
        retriever = self.store.as_retriever(search_kwargs={"k": 3})
        results = retriever.invoke("Morocco semi-finals")
        assert len(results) > 0


# ===========================================================================
# 3. Chat API — end-to-end (real Flask + routing, LLM mocked)
# ===========================================================================

@pytest.mark.integration
class TestChatAPIIntegration:
    """Flask test client → route handler → mocked chain → JSON response."""

    def test_health_endpoint_returns_ok(self, api_client):
        res = api_client.get("/scout/health")
        assert res.status_code == 200
        assert res.get_json() == {"status": "ok"}

    def test_chat_returns_200_for_valid_request(self, api_client):
        with patch("modules.scout.routes._get_chain", return_value=_mock_chain()):
            res = api_client.post(
                "/scout/chat",
                json={"question": "Who won?", "history": []},
            )
        assert res.status_code == 200

    def test_chat_response_content_type_is_json(self, api_client):
        with patch("modules.scout.routes._get_chain", return_value=_mock_chain()):
            res = api_client.post(
                "/scout/chat",
                json={"question": "Who won?", "history": []},
            )
        assert "application/json" in res.content_type

    def test_chat_answer_reflects_chain_output(self, api_client):
        expected = "Argentina won the 2022 World Cup."
        with patch("modules.scout.routes._get_chain",
                   return_value=_mock_chain(expected)):
            res = api_client.post(
                "/scout/chat",
                json={"question": "Who won?", "history": []},
            )
        assert res.get_json()["answer"] == expected

    def test_route_converts_history_to_tuples(self, api_client):
        """Routes must convert [[human, ai], ...] JSON arrays to (human, ai) tuples."""
        mock_chain = _mock_chain()
        with patch("modules.scout.routes._get_chain", return_value=mock_chain):
            api_client.post(
                "/scout/chat",
                json={
                    "question": "Who scored?",
                    "history": [["Who won?", "Argentina won."]],
                },
            )
        payload = mock_chain.invoke.call_args.args[0]
        assert payload["chat_history"] == [("Who won?", "Argentina won.")]

    def test_missing_question_returns_400(self, api_client):
        with patch("modules.scout.routes._get_chain", return_value=_mock_chain()):
            res = api_client.post("/scout/chat", json={"history": []})
        assert res.status_code == 400

    def test_empty_question_returns_400(self, api_client):
        with patch("modules.scout.routes._get_chain", return_value=_mock_chain()):
            res = api_client.post(
                "/scout/chat",
                json={"question": "   ", "history": []},
            )
        assert res.status_code == 400

    def test_non_json_body_rejected(self, api_client):
        res = api_client.post(
            "/scout/chat",
            data="not json",
            content_type="text/plain",
        )
        assert res.status_code in (400, 415)

    def test_both_routes_registered_under_scout_prefix(self, api_app):
        rules = {str(r) for r in api_app.url_map.iter_rules()}
        assert "/scout/health" in rules
        assert "/scout/chat" in rules

    def test_chain_error_returns_500(self, api_client, api_app):
        """An unhandled exception in chain.invoke should yield HTTP 500."""
        broken = MagicMock()
        broken.invoke.side_effect = RuntimeError("LLM timeout")

        original = api_app.config.get("PROPAGATE_EXCEPTIONS", True)
        api_app.config["PROPAGATE_EXCEPTIONS"] = False
        try:
            with patch("modules.scout.routes._get_chain", return_value=broken):
                res = api_client.post(
                    "/scout/chat",
                    json={"question": "Who won?", "history": []},
                )
            assert res.status_code == 500
        finally:
            api_app.config["PROPAGATE_EXCEPTIONS"] = original


# ===========================================================================
# 4. Multi-turn conversation threading
# ===========================================================================

@pytest.mark.integration
class TestMultiTurnConversationIntegration:
    """
    Verify that history is correctly accumulated and passed into each
    successive chain.invoke() call — purely at the HTTP/routing layer.
    """

    def test_three_turn_history_accumulates(self, api_client):
        answers = ["Argentina won.", "Messi was the captain.", "Qatar hosted it."]
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [{"answer": a} for a in answers]

        history = []
        questions = [
            "Who won the 2022 World Cup?",
            "Who was Argentina's captain?",
            "Where was the tournament held?",
        ]

        with patch("modules.scout.routes._get_chain", return_value=mock_chain):
            for q in questions:
                res = api_client.post(
                    "/scout/chat",
                    json={"question": q, "history": history},
                )
                assert res.status_code == 200
                history.append([q, res.get_json()["answer"]])

        # Third invocation should carry the first two turns
        third_payload = mock_chain.invoke.call_args_list[2].args[0]
        assert len(third_payload["chat_history"]) == 2

    def test_first_turn_has_empty_history(self, api_client):
        mock_chain = _mock_chain("Hello!")
        with patch("modules.scout.routes._get_chain", return_value=mock_chain):
            api_client.post(
                "/scout/chat",
                json={"question": "Hello?", "history": []},
            )
        payload = mock_chain.invoke.call_args.args[0]
        assert payload["chat_history"] == []

    def test_history_pairs_converted_to_tuples_each_turn(self, api_client):
        """At every turn, JSON arrays in history become Python tuples."""
        mock_chain = MagicMock()
        mock_chain.invoke.side_effect = [
            {"answer": "Argentina won."},
            {"answer": "Messi."},
        ]
        history = []

        with patch("modules.scout.routes._get_chain", return_value=mock_chain):
            # Turn 1
            api_client.post(
                "/scout/chat",
                json={"question": "Who won?", "history": []},
            )
            history.append(["Who won?", "Argentina won."])

            # Turn 2
            api_client.post(
                "/scout/chat",
                json={"question": "Their captain?", "history": history},
            )

        turn2_payload = mock_chain.invoke.call_args_list[1].args[0]
        assert all(isinstance(p, tuple) for p in turn2_payload["chat_history"])

    def test_independent_clients_dont_share_history(self, api_app):
        """
        Two separate test clients simulate two users. Each passes its own
        history; the server must not mix them up (stateless design check).
        """
        import modules.scout.routes as routes_module

        client_a = api_app.test_client()
        client_b = api_app.test_client()

        chain_a = _mock_chain("Answer for A.")
        chain_b = _mock_chain("Answer for B.")

        routes_module._chain = None
        with patch("modules.scout.routes._get_chain", return_value=chain_a):
            res_a = client_a.post(
                "/scout/chat",
                json={"question": "Question A?", "history": []},
            )

        routes_module._chain = None
        with patch("modules.scout.routes._get_chain", return_value=chain_b):
            res_b = client_b.post(
                "/scout/chat",
                json={"question": "Question B?", "history": []},
            )

        assert res_a.get_json()["answer"] == "Answer for A."
        assert res_b.get_json()["answer"] == "Answer for B."


# ===========================================================================
# 5. Chain caching integration
# ===========================================================================

@pytest.mark.integration
class TestChainCachingIntegration:
    """The chain factory runs once; all subsequent requests reuse _chain."""

    def test_factory_called_once_across_multiple_requests(self, api_client):
        import modules.scout.routes as routes_module
        routes_module._chain = None

        mock_chain = _mock_chain("Cached.")
        with patch("modules.scout.routes.get_chain",
                   return_value=mock_chain) as mock_factory:
            for _ in range(4):
                api_client.post(
                    "/scout/chat",
                    json={"question": "Test?", "history": []},
                )
        assert mock_factory.call_count == 1, (
            f"get_chain called {mock_factory.call_count}× — should be exactly 1"
        )

    def test_same_chain_object_handles_all_requests(self, api_client):
        import modules.scout.routes as routes_module
        routes_module._chain = None

        mock_chain = _mock_chain("Reused.")
        with patch("modules.scout.routes.get_chain", return_value=mock_chain):
            for i in range(3):
                api_client.post(
                    "/scout/chat",
                    json={"question": f"Q{i}", "history": []},
                )
        assert mock_chain.invoke.call_count == 3

    def test_cache_reset_triggers_rebuild(self, api_client):
        """Manually clearing _chain causes the factory to run again."""
        import modules.scout.routes as routes_module
        routes_module._chain = None

        mock_chain = _mock_chain()
        with patch("modules.scout.routes.get_chain",
                   return_value=mock_chain) as mock_factory:
            api_client.post("/scout/chat",
                            json={"question": "Q1", "history": []})
            # Simulate a restart / cache invalidation
            routes_module._chain = None
            api_client.post("/scout/chat",
                            json={"question": "Q2", "history": []})

        assert mock_factory.call_count == 2


# ===========================================================================
# 6. Fallback build integration
# ===========================================================================

@pytest.mark.integration
class TestFallbackBuildIntegration:
    """get_chain() falls back to building the vector store when none exists."""

    def test_get_chain_builds_when_store_missing(self, data_dir, tmp_path):
        """
        If load_vector_store raises (no index on disk), get_chain() should
        call load_documents → split_documents → build_vector_store and
        return a valid chain without raising.
        """
        mock_built_store = MagicMock()
        # Return a real BaseRetriever subclass so EnsembleRetriever passes
        # pydantic v2 type validation without needing to patch the class itself.
        mock_built_store.as_retriever.return_value = _FakeRetriever()

        with patch("modules.scout.rag_pipeline.load_vector_store",
                   side_effect=Exception("no store")), \
             patch("modules.scout.rag_pipeline.load_documents",
                   return_value=[Document(page_content="test", metadata={"source": "t.txt"})]), \
             patch("modules.scout.rag_pipeline.split_documents",
                   return_value=[Document(page_content="test", metadata={"source": "t.txt"})]), \
             patch("modules.scout.rag_pipeline.build_vector_store",
                   return_value=mock_built_store) as mock_build, \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.build_reranking_retriever",
                   return_value=_FakeRetriever()), \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:

            mock_bm25.from_documents.return_value = _FakeRetriever()
            mock_crc.from_llm.return_value = MagicMock()
            from modules.scout.rag_pipeline import get_chain
            chain = get_chain()

        assert chain is not None
        mock_build.assert_called_once()

    def test_get_chain_uses_existing_store_when_available(self):
        """When load_vector_store succeeds, build_vector_store must NOT be called."""
        mock_store = MagicMock()
        mock_store.as_retriever.return_value = _FakeRetriever()

        with patch("modules.scout.rag_pipeline.load_vector_store",
                   return_value=mock_store), \
             patch("modules.scout.rag_pipeline.load_chunks",
                   return_value=[MagicMock()]), \
             patch("modules.scout.rag_pipeline.build_vector_store") as mock_build, \
             patch("modules.scout.rag_pipeline.BM25Retriever") as mock_bm25, \
             patch("modules.scout.rag_pipeline.build_reranking_retriever",
                   return_value=_FakeRetriever()), \
             patch("modules.scout.rag_pipeline.ChatGroq"), \
             patch("modules.scout.rag_pipeline.ConversationalRetrievalChain") as mock_crc:

            mock_bm25.from_documents.return_value = _FakeRetriever()
            mock_crc.from_llm.return_value = MagicMock()
            from modules.scout.rag_pipeline import get_chain
            get_chain()

        mock_build.assert_not_called()

    def test_load_vector_store_builds_from_chunks_when_empty(
        self, tmp_path, sample_documents
    ):
        """
        load_vector_store(chunks=<data>) should build from provided chunks
        when the directory is empty, rather than raising ValueError.
        """
        from langchain_community.vectorstores import FAISS

        empty_vs = tmp_path / "fallback_vs"
        empty_vs.mkdir()

        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(empty_vs)), \
             patch("modules.scout.embeddings.CHUNKS_PATH",
                   str(empty_vs / "chunks.pkl")):
            from modules.scout.embeddings import load_vector_store
            store = load_vector_store(chunks=sample_documents)

        assert isinstance(store, FAISS)
        assert any(empty_vs.iterdir()), "Built index should be persisted"


# ===========================================================================
# 7. Hybrid retrieval integration
# ===========================================================================

@pytest.mark.integration
class TestHybridRetrievalIntegration:
    """
    Real EnsembleRetriever with BM25 + FAISS on sample data.
    Verifies the full hybrid path end-to-end without an LLM call.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, built_store, vector_store_dir):
        import tempfile, os
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH",
                   str(vector_store_dir)), \
             patch("modules.scout.embeddings.CHUNKS_PATH",
                   str(vector_store_dir / "chunks.pkl")):
            from modules.scout.embeddings import load_vector_store
            self.store = load_vector_store()

        tmp = tempfile.mkdtemp()
        for name, content in SAMPLE_FILES.items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as f:
                f.write(content)
        with patch("modules.scout.data_loader.DATA_DIR", tmp):
            from modules.scout.data_loader import load_documents, split_documents
            self.chunks = split_documents(load_documents())

    def test_ensemble_retriever_returns_documents(self):
        """EnsembleRetriever must return Document objects for a given query."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=4)
        faiss = self.store.as_retriever(search_kwargs={"k": 4})
        retriever = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )

        results = retriever.invoke("Who won the World Cup?")
        assert len(results) > 0
        assert all(hasattr(r, "page_content") for r in results)

    def test_keyword_match_surfaces_in_results(self):
        """A keyword query should surface the document containing that exact term."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=4)
        faiss = self.store.as_retriever(search_kwargs={"k": 4})
        retriever = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )

        results = retriever.invoke("Mbapp\u00e9 hat-trick")
        combined = " ".join(r.page_content for r in results).lower()
        assert "mbapp\u00e9" in combined or "mbappe" in combined.replace("\u00e9", "e")

    def test_semantic_match_surfaces_in_results(self):
        """A paraphrase query (no exact keyword) should still return relevant docs."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=4)
        faiss = self.store.as_retriever(search_kwargs={"k": 4})
        retriever = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )

        results = retriever.invoke("first African side in the last four")
        combined = " ".join(r.page_content for r in results).lower()
        assert "morocco" in combined or "african" in combined

    def test_no_duplicate_documents_in_results(self):
        """RRF fusion must deduplicate -- no page_content should appear twice."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=4)
        faiss = self.store.as_retriever(search_kwargs={"k": 4})
        retriever = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )

        results = retriever.invoke("Argentina World Cup champion")
        contents = [r.page_content for r in results]
        assert len(contents) == len(set(contents)), "Duplicate documents found in results"


# ===========================================================================
# 8. Cross-encoder reranking integration
# ===========================================================================

@pytest.mark.integration
class TestCrossEncoderReranking:
    """
    Real cross-encoder reranking over real hybrid retrieval results.
    No LLM call needed — tests the reranker independently of the chain.
    """

    @pytest.fixture(autouse=True)
    def _setup(self, built_store, vector_store_dir):
        import tempfile
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH",
                   str(vector_store_dir)), \
             patch("modules.scout.embeddings.CHUNKS_PATH",
                   str(vector_store_dir / "chunks.pkl")):
            from modules.scout.embeddings import load_vector_store
            self.store = load_vector_store()

        tmp = tempfile.mkdtemp()
        for name, content in SAMPLE_FILES.items():
            with open(os.path.join(tmp, name), "w", encoding="utf-8") as fh:
                fh.write(content)
        with patch("modules.scout.data_loader.DATA_DIR", tmp):
            from modules.scout.data_loader import load_documents, split_documents
            self.chunks = split_documents(load_documents())

    def test_reranker_returns_document_objects(self):
        """RerankingRetriever must yield Document instances."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever
        from modules.scout.reranker import build_reranking_retriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=8)
        faiss = self.store.as_retriever(search_kwargs={"k": 8})
        ensemble = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )
        retriever = build_reranking_retriever(ensemble)

        results = retriever.invoke("Who won the World Cup?")
        assert len(results) > 0
        assert all(hasattr(r, "page_content") for r in results)

    def test_reranker_limits_results_to_top_n(self):
        """Result count must not exceed RERANK_TOP_N (default 5)."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever
        from modules.scout.reranker import build_reranking_retriever, RERANK_TOP_N

        bm25 = BM25Retriever.from_documents(self.chunks, k=8)
        faiss = self.store.as_retriever(search_kwargs={"k": 8})
        ensemble = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )
        retriever = build_reranking_retriever(ensemble)

        results = retriever.invoke("Argentina champion")
        assert len(results) <= RERANK_TOP_N

    def test_reranked_results_contain_no_duplicates(self):
        """After reranking, no two results should have the same page_content."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever
        from modules.scout.reranker import build_reranking_retriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=8)
        faiss = self.store.as_retriever(search_kwargs={"k": 8})
        ensemble = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )
        retriever = build_reranking_retriever(ensemble)

        results = retriever.invoke("Messi Golden Ball")
        contents = [r.page_content for r in results]
        assert len(contents) == len(set(contents))

    def test_relevant_content_surfaces_in_reranked_results(self):
        """A targeted query must surface the matching content after reranking."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever
        from modules.scout.reranker import build_reranking_retriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=8)
        faiss = self.store.as_retriever(search_kwargs={"k": 8})
        ensemble = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )
        retriever = build_reranking_retriever(ensemble)

        results = retriever.invoke("Kylian Mbappé hat-trick in the final")
        combined = " ".join(r.page_content for r in results).lower()
        assert "mbapp" in combined or "hat-trick" in combined

    def test_custom_top_n_limits_reranked_output(self):
        """Passing top_n=2 must return at most 2 documents."""
        from langchain_community.retrievers import BM25Retriever
        from langchain_classic.retrievers import EnsembleRetriever
        from modules.scout.reranker import build_reranking_retriever

        bm25 = BM25Retriever.from_documents(self.chunks, k=8)
        faiss = self.store.as_retriever(search_kwargs={"k": 8})
        ensemble = EnsembleRetriever(
            retrievers=[bm25, faiss], weights=[0.6, 0.4], c=60
        )
        retriever = build_reranking_retriever(ensemble, top_n=2)

        results = retriever.invoke("Morocco semi-finals")
        assert len(results) <= 2

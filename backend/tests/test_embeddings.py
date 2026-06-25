"""
tests/test_embeddings.py

Unit tests for modules/scout/embeddings.py.
Week 2 update: get_embeddings() now returns HuggingFaceEmbeddings,
not GoogleGenerativeAIEmbeddings -- tests updated accordingly.
"""

import os
import pytest
from unittest.mock import patch, MagicMock


class TestGetEmbeddings:
    def test_returns_huggingface_embeddings_object(self):
        """get_embeddings() must return a HuggingFaceEmbeddings instance."""
        from langchain_huggingface import HuggingFaceEmbeddings
        from modules.scout.embeddings import get_embeddings

        embeddings = get_embeddings()
        assert isinstance(embeddings, HuggingFaceEmbeddings)

    def test_uses_correct_model_name(self):
        """Model must be all-MiniLM-L6-v2 (384-dim, local, no API calls)."""
        from modules.scout.embeddings import get_embeddings

        embeddings = get_embeddings()
        assert embeddings.model_name == "sentence-transformers/all-MiniLM-L6-v2"

    def test_get_embeddings_returns_new_instance_each_time(self):
        """get_embeddings() is a factory -- each call returns a fresh object."""
        from modules.scout.embeddings import get_embeddings

        e1 = get_embeddings()
        e2 = get_embeddings()
        assert e1 is not e2


class TestBuildVectorStore:
    def test_build_creates_vector_store_directory(self, tmp_path, sample_documents):
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)):
            from modules.scout.embeddings import build_vector_store
            build_vector_store(sample_documents)

        assert any(tmp_path.iterdir()), "vector_store directory should not be empty after build"

    def test_build_saves_faiss_index_file(self, tmp_path, sample_documents):
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)):
            from modules.scout.embeddings import build_vector_store
            build_vector_store(sample_documents)

        files = list(tmp_path.iterdir())
        names = [f.name for f in files]
        assert any("index" in n for n in names), f"Expected FAISS index file, found: {names}"

    def test_build_accepts_non_empty_document_list(self, tmp_path, sample_documents):
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)):
            from modules.scout.embeddings import build_vector_store
            # Should not raise
            build_vector_store(sample_documents)


class TestLoadVectorStore:
    def test_load_returns_faiss_object(self, tmp_path, sample_documents):
        from langchain_community.vectorstores import FAISS

        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)):
            from modules.scout.embeddings import build_vector_store, load_vector_store
            build_vector_store(sample_documents)
            store = load_vector_store()

        assert isinstance(store, FAISS)

    def test_load_accepts_chunks_none(self, tmp_path, sample_documents):
        """load_vector_store(chunks=None) must not raise -- regression for Week 2 bug."""
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)):
            from modules.scout.embeddings import build_vector_store, load_vector_store
            build_vector_store(sample_documents)
            # Should not raise TypeError
            store = load_vector_store(chunks=None)

        assert store is not None

    def test_load_without_prior_build_raises(self, tmp_path):
        """Loading from an empty directory should raise, not silently return None."""
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)):
            from modules.scout.embeddings import load_vector_store
            with pytest.raises(Exception):
                load_vector_store()

    def test_load_with_chunks_builds_when_dir_missing(self, tmp_path, sample_documents):
        """
        load_vector_store(chunks=<data>) should build and return a FAISS store
        when the vector store directory is empty -- instead of raising.
        This exercises the fallback branch: chunks is not None -> build.
        """
        from langchain_community.vectorstores import FAISS

        empty_dir = tmp_path / "empty_vs"
        empty_dir.mkdir()

        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(empty_dir)):
            from modules.scout.embeddings import load_vector_store
            store = load_vector_store(chunks=sample_documents)

        assert isinstance(store, FAISS)

    def test_load_with_chunks_persists_to_disk(self, tmp_path, sample_documents):
        """After load_vector_store builds from chunks, files should be on disk."""
        empty_dir = tmp_path / "vs2"
        empty_dir.mkdir()

        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(empty_dir)), \
             patch("modules.scout.embeddings.CHUNKS_PATH",
                   str(empty_dir / "chunks.pkl")):
            from modules.scout.embeddings import load_vector_store
            load_vector_store(chunks=sample_documents)

        assert any(empty_dir.iterdir()), "FAISS files should be written to disk"


# ---------------------------------------------------------------------------
# TestSaveChunks / TestLoadChunks
# ---------------------------------------------------------------------------

class TestSaveChunks:
    def test_creates_chunks_pkl_file(self, tmp_path, sample_documents):
        """save_chunks must write chunks.pkl inside VECTOR_STORE_PATH."""
        chunks_path = tmp_path / "chunks.pkl"
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)), \
             patch("modules.scout.embeddings.CHUNKS_PATH", str(chunks_path)):
            from modules.scout.embeddings import save_chunks
            save_chunks(sample_documents)

        assert chunks_path.exists()

    def test_creates_directory_if_missing(self, tmp_path, sample_documents):
        """save_chunks must create VECTOR_STORE_PATH if it doesn't exist yet."""
        new_dir = tmp_path / "new_vs"
        chunks_path = new_dir / "chunks.pkl"
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(new_dir)), \
             patch("modules.scout.embeddings.CHUNKS_PATH", str(chunks_path)):
            from modules.scout.embeddings import save_chunks
            save_chunks(sample_documents)

        assert chunks_path.exists()

    def test_saved_content_is_non_empty(self, tmp_path, sample_documents):
        """The pickle file should not be empty."""
        chunks_path = tmp_path / "chunks.pkl"
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)), \
             patch("modules.scout.embeddings.CHUNKS_PATH", str(chunks_path)):
            from modules.scout.embeddings import save_chunks
            save_chunks(sample_documents)

        assert chunks_path.stat().st_size > 0


class TestLoadChunks:
    def test_load_returns_same_documents(self, tmp_path, sample_documents):
        """Round-trip: save then load must return equivalent documents."""
        chunks_path = tmp_path / "chunks.pkl"
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)), \
             patch("modules.scout.embeddings.CHUNKS_PATH", str(chunks_path)):
            from modules.scout.embeddings import save_chunks, load_chunks
            save_chunks(sample_documents)
            loaded = load_chunks()

        assert len(loaded) == len(sample_documents)
        assert [d.page_content for d in loaded] == \
               [d.page_content for d in sample_documents]

    def test_load_preserves_metadata(self, tmp_path, sample_documents):
        """Metadata (e.g. source filename) must survive the pickle round-trip."""
        chunks_path = tmp_path / "chunks.pkl"
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)), \
             patch("modules.scout.embeddings.CHUNKS_PATH", str(chunks_path)):
            from modules.scout.embeddings import save_chunks, load_chunks
            save_chunks(sample_documents)
            loaded = load_chunks()

        for orig, got in zip(sample_documents, loaded):
            assert got.metadata == orig.metadata

    def test_load_raises_when_file_missing(self, tmp_path):
        """load_chunks must raise FileNotFoundError when chunks.pkl doesn't exist."""
        missing = tmp_path / "chunks.pkl"
        with patch("modules.scout.embeddings.CHUNKS_PATH", str(missing)):
            from modules.scout.embeddings import load_chunks
            with pytest.raises(FileNotFoundError):
                load_chunks()


class TestBuildVectorStoreAlsoSavesChunks:
    def test_build_writes_chunks_pkl(self, tmp_path, sample_documents):
        """build_vector_store must also persist chunks.pkl for BM25 reuse."""
        chunks_path = tmp_path / "chunks.pkl"
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)), \
             patch("modules.scout.embeddings.CHUNKS_PATH", str(chunks_path)):
            from modules.scout.embeddings import build_vector_store
            build_vector_store(sample_documents)

        assert chunks_path.exists(), "chunks.pkl must be written by build_vector_store"

    def test_chunks_pkl_content_matches_input(self, tmp_path, sample_documents):
        """Chunks saved during build must match the documents passed in."""
        chunks_path = tmp_path / "chunks.pkl"
        with patch("modules.scout.embeddings.VECTOR_STORE_PATH", str(tmp_path)), \
             patch("modules.scout.embeddings.CHUNKS_PATH", str(chunks_path)):
            from modules.scout.embeddings import build_vector_store, load_chunks
            build_vector_store(sample_documents)
            loaded = load_chunks()

        assert len(loaded) == len(sample_documents)

"""
Unit tests for modules/scout/data_loader.py

Tests load_documents() and split_documents() without touching
the real backend/data/ directory.
"""
import os
import pytest
from unittest.mock import patch
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_data_dir(tmp_path, files: dict[str, str]) -> str:
    """Write a dict of {filename: content} into tmp_path and return the path."""
    for name, content in files.items():
        (tmp_path / name).write_text(content, encoding="utf-8")
    return str(tmp_path)


# ---------------------------------------------------------------------------
# load_documents()
# ---------------------------------------------------------------------------

class TestLoadDocuments:

    def test_loads_txt_files(self, tmp_path):
        make_data_dir(tmp_path, {
            "teams.txt": "Brazil is a top football nation.",
            "players.txt": "Lionel Messi plays for Argentina.",
        })
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()

        assert len(docs) == 2
        sources = {d.metadata["source"] for d in docs}
        assert sources == {"teams.txt", "players.txt"}

    def test_ignores_non_txt_files(self, tmp_path):
        make_data_dir(tmp_path, {
            "groups.txt": "Group A contains Qatar.",
            "README.md": "This is a readme.",
            "notes.json": '{"key": "value"}',
        })
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()

        assert len(docs) == 1
        assert docs[0].metadata["source"] == "groups.txt"

    def test_skips_empty_txt_files(self, tmp_path):
        make_data_dir(tmp_path, {
            "empty.txt": "",
            "whitespace.txt": "   \n\n   ",
            "valid.txt": "Argentina won the 2022 World Cup.",
        })
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()

        assert len(docs) == 1
        assert docs[0].metadata["source"] == "valid.txt"

    def test_returns_document_objects(self, tmp_path):
        make_data_dir(tmp_path, {"fixtures.txt": "Match 1: Brazil vs Serbia."})
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()

        assert all(isinstance(d, Document) for d in docs)

    def test_page_content_matches_file(self, tmp_path):
        content = "France won the 2018 World Cup in Russia."
        make_data_dir(tmp_path, {"history.txt": content})
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()

        assert docs[0].page_content == content

    def test_empty_directory_returns_empty_list(self, tmp_path):
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()

        assert docs == []


# ---------------------------------------------------------------------------
# split_documents()
# ---------------------------------------------------------------------------

class TestSplitDocuments:

    def _make_docs(self, texts: list[str]) -> list[Document]:
        return [Document(page_content=t, metadata={"source": "test.txt"}) for t in texts]

    def test_returns_list_of_documents(self):
        from modules.scout.data_loader import split_documents
        docs = self._make_docs(["Argentina won the 2022 FIFA World Cup held in Qatar."])
        chunks = split_documents(docs)
        assert isinstance(chunks, list)
        assert all(isinstance(c, Document) for c in chunks)

    def test_short_text_stays_as_single_chunk(self):
        from modules.scout.data_loader import split_documents
        docs = self._make_docs(["Short text."])
        chunks = split_documents(docs)
        assert len(chunks) == 1

    def test_long_text_is_split(self):
        from modules.scout.data_loader import split_documents
        # 600 chars — should split at chunk_size=500
        long_text = "Word " * 120
        docs = self._make_docs([long_text])
        chunks = split_documents(docs)
        assert len(chunks) > 1

    def test_chunks_do_not_exceed_chunk_size(self):
        from modules.scout.data_loader import split_documents
        long_text = "Argentina " * 200
        docs = self._make_docs([long_text])
        chunks = split_documents(docs)
        # Allow slight overage at word boundaries but nothing egregious
        for chunk in chunks:
            assert len(chunk.page_content) <= 600

    def test_metadata_preserved_after_split(self):
        from modules.scout.data_loader import split_documents
        long_text = "Brazil " * 150
        docs = [Document(page_content=long_text, metadata={"source": "teams.txt"})]
        chunks = split_documents(docs)
        for chunk in chunks:
            assert chunk.metadata["source"] == "teams.txt"

    def test_empty_list_returns_empty_list(self):
        from modules.scout.data_loader import split_documents
        assert split_documents([]) == []

    def test_multiple_docs_all_chunked(self, tmp_path):
        from modules.scout.data_loader import split_documents
        docs = self._make_docs([
            "Germany " * 120,
            "France " * 120,
        ])
        chunks = split_documents(docs)
        assert len(chunks) >= 2


# ---------------------------------------------------------------------------
# Paragraph-splitting behaviour in load_documents()
# ---------------------------------------------------------------------------

class TestLoadDocumentsParagraphSplitting:
    """
    load_documents() splits each file on double-newlines (\n\n), producing
    one Document per paragraph rather than one per file.
    These tests exercise that core behaviour, which the existing suite misses.
    """

    def test_multi_paragraph_file_creates_multiple_documents(self, tmp_path):
        """A file with three paragraphs should yield three Documents."""
        content = "Para one.\n\nPara two.\n\nPara three."
        (tmp_path / "multi.txt").write_text(content, encoding="utf-8")
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()
        assert len(docs) == 3

    def test_each_paragraph_is_separate_document(self, tmp_path):
        """Each paragraph becomes its own page_content string."""
        (tmp_path / "p.txt").write_text(
            "First paragraph.\n\nSecond paragraph.", encoding="utf-8"
        )
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()
        contents = [d.page_content for d in docs]
        assert "First paragraph." in contents
        assert "Second paragraph." in contents

    def test_blank_paragraphs_between_content_are_skipped(self, tmp_path):
        """Extra blank lines between paragraphs should not create empty Documents."""
        (tmp_path / "blanks.txt").write_text(
            "Real para.\n\n\n\nAnother real para.", encoding="utf-8"
        )
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()
        assert len(docs) == 2
        assert all(d.page_content.strip() for d in docs)

    def test_multi_paragraph_all_share_same_source(self, tmp_path):
        """Every paragraph Document from the same file carries that file's name."""
        (tmp_path / "teams.txt").write_text(
            "Brazil is great.\n\nGermany is strong.", encoding="utf-8"
        )
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()
        assert all(d.metadata["source"] == "teams.txt" for d in docs)

    def test_windows_line_endings_handled(self, tmp_path):
        """CRLF line endings (\r\n\r\n) should split into paragraphs the same way."""
        (tmp_path / "win.txt").write_text(
            "Para A.\r\n\r\nPara B.", encoding="utf-8"
        )
        with patch("modules.scout.data_loader.DATA_DIR", str(tmp_path)):
            from modules.scout.data_loader import load_documents
            docs = load_documents()
        assert len(docs) == 2

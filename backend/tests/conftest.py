"""
tests/conftest.py

Shared pytest fixtures.
Week 2 additions: `app` and `client` fixtures for Flask route tests.
"""

import os
import pytest
import tempfile


# ---------------------------------------------------------------------------
# Existing fixtures (Week 1) — surgical fix: build docs before tmpdir closes
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_text():
    return (
        "Argentina won the 2022 FIFA World Cup.\n\n"
        "Lionel Messi was the captain of Argentina.\n\n"
        "The final was played in Lusail, Qatar.\n\n"
        "France was the runner-up.\n\n"
        "Kylian Mbappé scored a hat-trick in the final.\n\n"
        "The tournament was held from November to December 2022.\n\n"
        "Morocco became the first African team to reach the semi-finals.\n\n"
        "Croatia finished in third place.\n\n"
        "Adidas Al Rihla was the official match ball.\n\n"
        "Qatar was the first Middle Eastern country to host the World Cup."
    )


@pytest.fixture
def sample_documents(sample_text, tmp_path):
    """
    Write sample_text to a temp .txt file and return split Document objects.
    Uses pytest's tmp_path (stays alive for the test) instead of
    tempfile.TemporaryDirectory (which deletes on __exit__).
    """
    fpath = tmp_path / "test.txt"
    fpath.write_text(sample_text, encoding="utf-8")

    import modules.scout.data_loader as dl
    original_dir = dl.DATA_DIR
    dl.DATA_DIR = str(tmp_path)
    try:
        from modules.scout.data_loader import load_documents, split_documents
        docs = split_documents(load_documents())
    finally:
        dl.DATA_DIR = original_dir

    return docs


# ---------------------------------------------------------------------------
# Week 2 fixtures — Flask test client
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def app():
    """
    Flask app in test mode. Session-scoped so it's created once.
    Stubs API key env vars so the import works without real keys.
    """
    os.environ.setdefault("GOOGLE_API_KEY", "test-key")
    os.environ.setdefault("GROQ_API_KEY", "test-key")

    from app import app as flask_app
    flask_app.config.update({"TESTING": True})
    yield flask_app


@pytest.fixture
def client(app):
    """
    Flask test client. Resets the module-level _chain cache before each
    test so tests don't bleed into each other.
    """
    import modules.scout.routes as routes_module
    routes_module._chain = None
    return app.test_client()
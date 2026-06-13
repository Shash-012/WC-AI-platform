"""
tests/test_routes.py

Unit tests for modules/scout/routes.py (Week 2).

Patch target: modules.scout.routes._get_chain
  routes.py imports get_chain from rag_pipeline and wraps it in _get_chain().
  We patch _get_chain directly so the chain mock is returned without any
  real LLM or vector store instantiation.

Cache attribute: _chain (confirmed in routes.py line 10)
"""

import pytest
from unittest.mock import patch, MagicMock


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_ANSWER = "Argentina won the 2022 World Cup."


def _make_mock_chain(answer=MOCK_ANSWER):
    """MagicMock that behaves like a ConversationalRetrievalChain."""
    chain = MagicMock()
    chain.invoke.return_value = {"answer": answer}
    return chain


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        res = client.get("/scout/health")
        assert res.status_code == 200

    def test_health_returns_ok(self, client):
        res = client.get("/scout/health")
        assert res.get_json() == {"status": "ok"}


# ---------------------------------------------------------------------------
# Chat endpoint
# ---------------------------------------------------------------------------

class TestChatEndpoint:
    def test_valid_request_returns_200(self, client):
        with patch("modules.scout.routes._get_chain",
                   return_value=_make_mock_chain()):
            res = client.post(
                "/scout/chat",
                json={"question": "Who won the 2022 World Cup?", "history": []},
            )
        assert res.status_code == 200

    def test_valid_request_returns_answer_string(self, client):
        with patch("modules.scout.routes._get_chain",
                   return_value=_make_mock_chain()):
            res = client.post(
                "/scout/chat",
                json={"question": "Who won the 2022 World Cup?", "history": []},
            )
        data = res.get_json()
        assert "answer" in data
        assert isinstance(data["answer"], str)
        assert len(data["answer"]) > 0

    def test_missing_question_field_returns_400(self, client):
        with patch("modules.scout.routes._get_chain",
                   return_value=_make_mock_chain()):
            res = client.post("/scout/chat", json={"history": []})
        assert res.status_code == 400

    def test_empty_question_returns_400(self, client):
        with patch("modules.scout.routes._get_chain",
                   return_value=_make_mock_chain()):
            res = client.post(
                "/scout/chat",
                json={"question": "", "history": []},
            )
        assert res.status_code == 400

    def test_no_json_body_returns_400_or_415(self, client):
        """
        Flask returns 415 for wrong Content-Type before the view runs.
        Both 400 and 415 are valid rejections for a missing JSON body.
        """
        res = client.post(
            "/scout/chat",
            data="not json",
            content_type="text/plain",
        )
        assert res.status_code in (400, 415)

    def test_history_passed_to_invoke(self, client):
        """
        Stateless design: the request's history must be passed to
        chain.invoke as a `chat_history` list of (human, ai) tuples.
        Nothing is written to a server-side memory object.
        """
        mock_chain = _make_mock_chain()

        with patch("modules.scout.routes._get_chain",
                   return_value=mock_chain):
            client.post(
                "/scout/chat",
                json={
                    "question": "Who was their captain?",
                    "history": [["Who won the 2022 World Cup?", MOCK_ANSWER]],
                },
            )

        mock_chain.invoke.assert_called_once()
        payload = mock_chain.invoke.call_args.args[0]
        assert payload["question"] == "Who was their captain?"
        assert payload["chat_history"] == [
            ("Who won the 2022 World Cup?", MOCK_ANSWER)
        ]
        # No server-side memory should be touched.
        assert not mock_chain.memory.clear.called

    def test_response_content_type_is_json(self, client):
        """Successful chat response must have Content-Type: application/json."""
        with patch("modules.scout.routes._get_chain",
                   return_value=_make_mock_chain()):
            res = client.post(
                "/scout/chat",
                json={"question": "Who won?", "history": []},
            )
        assert "application/json" in res.content_type

    def test_chain_error_propagates_as_500(self, client):
        """
        If chain.invoke raises an unhandled exception, Flask returns 500.
        In TESTING mode Flask re-raises by default; we disable propagation
        temporarily to assert on the HTTP status code.
        """
        from app import app as flask_app
        broken = MagicMock()
        broken.invoke.side_effect = RuntimeError("LLM unavailable")

        original = flask_app.config.get("PROPAGATE_EXCEPTIONS", True)
        flask_app.config["PROPAGATE_EXCEPTIONS"] = False
        try:
            with patch("modules.scout.routes._get_chain", return_value=broken):
                res = client.post(
                    "/scout/chat",
                    json={"question": "Who won?", "history": []},
                )
            assert res.status_code == 500
        finally:
            flask_app.config["PROPAGATE_EXCEPTIONS"] = original

    def test_chain_is_cached_across_requests(self, client):
        """
        get_chain() (the factory imported from rag_pipeline) must be called
        only once. _get_chain() in routes.py caches the result in _chain --
        the second request reuses it without calling the factory again.
        Patch routes.get_chain (the imported name), not _get_chain (the
        wrapper), so the real caching logic in _get_chain() executes.
        """
        import modules.scout.routes as routes_module
        routes_module._chain = None

        with patch("modules.scout.routes.get_chain",
                   return_value=_make_mock_chain()) as mock_factory:
            client.post("/scout/chat",
                        json={"question": "Q1", "history": []})
            client.post("/scout/chat",
                        json={"question": "Q2", "history": []})

        assert mock_factory.call_count == 1, (
            f"get_chain called {mock_factory.call_count}x -- expected 1. "
            "The _chain cache in routes.py should prevent re-initialisation."
        )

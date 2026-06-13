"""
Flask blueprint for the scout chatbot.
Week 2: stateless REST API — history travels with every request.

The chain is cached once per process for speed, but it holds no conversation
state: each request passes its own `chat_history` straight into invoke(), so
overlapping requests from different clients can never see each other's history.
"""
from flask import Blueprint, request, jsonify
from .rag_pipeline import get_chain

scout_bp = Blueprint("scout", __name__)

# Module-level chain cache — built once, reused for every request.
# Safe to share because the chain carries no per-request state.
_chain = None


def _get_chain():
    global _chain
    if _chain is None:
        _chain = get_chain()
    return _chain


@scout_bp.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@scout_bp.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    if not data:
        return jsonify({"error": "JSON body required"}), 400

    question = data.get("question", "").strip()
    if not question:
        return jsonify({"error": "question is required"}), 400

    # History arrives as a list of [human, ai] pairs from the frontend.
    # Convert to (human, ai) tuples for ConversationalRetrievalChain.
    raw_history = data.get("history", [])
    chat_history = [tuple(pair) for pair in raw_history]

    chain = _get_chain()

    # Stateless: the request's history is passed straight into the call.
    # Nothing is stored on the chain between requests.
    result = chain.invoke({"question": question, "chat_history": chat_history})
    return jsonify({"answer": result["answer"]})

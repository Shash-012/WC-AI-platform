# WC-AI-Platform

AI-powered 2026 FIFA World Cup platform — RAG chatbot, match predictor, and sentiment analyser built with LangChain, Groq, FAISS, and React.

## Modules

| Module | Status | Description |
|--------|--------|-------------|
| `scout` | ✅ Live | RAG chatbot — LangChain + FAISS + Groq `llama-3.1-8b-instant` |
| `predictor` | Planned | Match outcome predictor |
| `sentiment` | Planned | Fan sentiment tracker |

## Stack

| Layer | Technology |
|-------|-----------|
| LLM | Groq `llama-3.1-8b-instant` (14,400 RPD free tier) |
| Embeddings | HuggingFace `all-MiniLM-L6-v2` (local, 384-dim, no API key) |
| Vector store | FAISS (pre-built locally, loaded on server) |
| RAG | LangChain `ConversationalRetrievalChain` |
| Backend | Flask, stateless REST API |
| Frontend | React + TypeScript + Vite + Tailwind |
| Deployment | AWS EC2 t2.micro, Nginx, systemd |

## Vector Store

`backend/vector_store/` is pre-built locally using HuggingFace `all-MiniLM-L6-v2` (384-dim) and committed to the repo. **Do not rebuild on EC2 — PyTorch is not installed there.** The server only loads the index at startup.

To rebuild locally after updating `backend/data/*.txt`:

```bash
cd backend
python -m modules.scout.rag_pipeline  # rebuilds vector_store/ on first run if missing
```

## Local Development

```bash
# Backend
cd backend
python -m venv venv && source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env   # add your GROQ_API_KEY
flask run

# Frontend
cd frontend
npm install
npm run dev
```

## Running Tests

```bash
cd backend
pytest                          # all tests
pytest -m "not integration"     # unit tests only
pytest -m integration           # integration tests (needs sentence-transformers)
```

## Deployment (EC2)

EC2 installs from `requirements.server.txt` — PyTorch, sentence-transformers, and transformers are excluded since the server only loads the pre-built FAISS index.

```bash
pip install -r requirements.server.txt
```

See `deploy.sh` at the project root for the full deploy workflow.

## Environment Variables

| Variable | Used by |
|----------|---------|
| `GROQ_API_KEY` | `rag_pipeline.py` — Groq LLM |

Copy `.env.example` to `.env` and fill in your key. Never commit `.env`.

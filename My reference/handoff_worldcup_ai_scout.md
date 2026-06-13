# Handoff — World Cup 2026 AI Scout (Project 1)

## Context

This handoff is for a new agent continuing work with Shashwat Tripathi, a 2nd-year ITNS student at NSUT (CGPA 9.0+). The previous session was a resume audit and recruiter keyword analysis. The outcome was a recommendation to build a portfolio project that covers missing resume keywords for SWE Intern / ML-AI Intern applications at Big Tech and Fintech companies.

Project 1 is the first of a planned three-module platform (Projects 1, 2, 5 will eventually be combined). The codebase should be structured modularly from day one so Projects 2 and 5 can be added later as separate modules.

---

## Project Brief — World Cup 2026 AI Scout

A RAG-based AI chatbot that answers natural language questions about the 2026 FIFA World Cup (teams, players, fixtures, group standings, historical stats) using real data collected and indexed by the user.

### Why This Project
- Covers the maximum number of missing resume keywords in one build
- Football is a genuine interest (Shashwat plays at school and college level, previously built FUTZONE)
- Timely — the 2026 World Cup is happening now, making it a live, relevant project
- Designed to expand: Projects 2 (match predictor) and 5 (sentiment tracker) will be added as modules later

---

## Resume Keywords This Project Must Cover

The following keywords are currently missing from the resume and must appear in the final project (used genuinely, not just listed):

- `PyTorch` — via HuggingFace sentence-transformer for generating embeddings
- `HuggingFace Transformers` — `all-MiniLM-L6-v2` as the embedding model
- `LLMs / Generative AI` — OpenAI API or Gemini API for answer generation
- `LangChain` — orchestrates the RAG pipeline
- `FAISS` — vector store for document embeddings
- `RAG (Retrieval-Augmented Generation)` — the core architecture
- `prompt engineering` — system prompt and context injection design
- `TypeScript` — frontend language
- `React` — frontend framework
- `Docker` — containerise the Flask backend
- `deployment` — live URL via Render, Railway, or AWS EC2 (EC2 preferred for the AWS keyword)
- `embeddings` — explicitly mentioned in code and resume bullet
- `REST APIs` — Flask API endpoint connecting backend to frontend

Already on resume (should still appear in this project's context): `Python`, `Flask`, `MySQL/SQL`, `Git/GitHub`.

---

## Planned Tech Stack

| Layer | Technology | Notes |
|---|---|---|
| Language | Python | Backend and ML pipeline |
| LLM Orchestration | LangChain | RAG pipeline |
| Embedding Model | HuggingFace `all-MiniLM-L6-v2` | Runs on PyTorch |
| Vector Store | FAISS | Local, no paid tier needed |
| LLM API | OpenAI API or Gemini API | Free tier sufficient for dev |
| Backend | Flask (REST API) | Familiar to user |
| Frontend | React + TypeScript | Chat UI + live standings table |
| Football Data API | API-Football (free tier) | Live fixtures and standings |
| Containerisation | Docker + docker-compose | Backend + frontend together |
| Deployment | AWS EC2 (free tier) or Render | Live URL for resume |
| Version Control | Git + GitHub | Public repo for resume link |

---

## 4-Week Build Plan

### Week 1 — Data + RAG Pipeline (no UI)
- Collect World Cup 2026 data: team rosters, group fixtures, historical stats, player info
- Format as text chunks suitable for embedding
- Set up LangChain + FAISS locally in a Python script
- Integrate OpenAI/Gemini API for answer generation
- Goal: chatbot answers questions correctly in a terminal/script — no frontend yet

### Week 2 — PyTorch Embeddings + Flask API
- Swap default LangChain embeddings for HuggingFace `all-MiniLM-L6-v2` (PyTorch-backed)
- Wrap the RAG pipeline in a Flask REST API (`POST /chat` endpoint)
- Test endpoint with Postman or curl
- Goal: working API that accepts a question and returns an answer

### Week 3 — React + TypeScript Frontend
- Build a chat UI in React/TypeScript (input box + response panel)
- Add a live standings/fixtures table using API-Football
- Connect frontend to the Flask API
- Goal: working end-to-end in local browser

### Week 4 — Docker + Deployment
- Write Dockerfile for the Flask backend
- Write docker-compose.yml for backend + frontend
- Deploy to AWS EC2 (free tier) or Render
- Get a live public URL
- Goal: shareable link, push everything to GitHub with a good README

---

## Modular Architecture Note

Design the repo structure so Projects 2 and 5 slot in cleanly later:

```
worldcup-ai-platform/
├── backend/
│   ├── app.py                  # Flask app, route registration
│   ├── modules/
│   │   ├── scout/              # Project 1 — RAG chatbot (build this now)
│   │   ├── predictor/          # Project 2 — match outcome predictor (later)
│   │   └── sentiment/          # Project 5 — sentiment tracker (later)
│   ├── data/                   # World Cup data chunks
│   ├── vector_store/           # FAISS index files
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Chat.tsx        # Project 1 UI
│   │   │   ├── Standings.tsx   # Live standings table
│   │   │   ├── Predictor.tsx   # Project 2 UI (later)
│   │   │   └── Sentiment.tsx   # Project 5 UI (later)
│   └── package.json
├── docker-compose.yml
└── README.md
```

---

## Target Resume Bullet (to write toward)

> Built a RAG-based AI chatbot for the 2026 FIFA World Cup using LangChain, FAISS, and the OpenAI API, enabling natural language queries over team, player, and fixture data. Generated document embeddings using a HuggingFace sentence-transformer (PyTorch). Built a React/TypeScript frontend with live standings via a football data API. Containerised with Docker and deployed to AWS EC2.

---

## User Background

- **Comfort level with new tech:** Never used PyTorch, LLMs, Docker, or TypeScript before this project
- **Familiar tech:** Python, Flask, React (JS), MySQL, HTML/CSS, REST APIs, Git
- **Time available:** ~1-2 weekends per week (realistic pace = 4 weeks total)
- **Prior football project:** FUTZONE (Flask + MySQL + Scoreaxis API) — can reference for football API patterns
- **Goal:** Intern applications at Google, Microsoft, Goldman Sachs, JP Morgan, and Indian Big Tech/Fintech

---

## Suggested Skills for Next Agent

- `/karpathy-guidelines` — apply before writing any code to avoid overcomplication and make surgical, well-scoped decisions
- `/resume-rewriter` — once the project is complete, rewrite the project bullet using the XYZ formula

---

## What the Next Agent Should Do First

1. Ask Shashwat which LLM API he wants to use — OpenAI (requires a paid key after free limits) or Gemini (generous free tier, good for students)
2. Ask whether he wants AWS EC2 or Render for deployment (EC2 = AWS keyword on resume, Render = simpler setup)
3. Start with Week 1: help set up the Python environment, data collection strategy, and first LangChain + FAISS script
4. Keep the scope ruthlessly contained to Week 1 deliverables — do not build the frontend or Docker setup until the RAG pipeline works end-to-end in a script

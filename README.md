# ClauseClear Mini Backend (MVP)

This is the minimal backend for **ClauseClear – AI-powered legal clause simplifier & risk detector**.

## What it does

- Accepts PDF uploads (rental / loan contracts).
- Extracts text and splits into simple clause chunks.
- Builds a **TF-IDF + cosine similarity** index for semantic search.
- Runs a **rule-based severity engine** using an India-specific legal knowledge base.
- Exposes a **unified query endpoint** that returns:
  - Relevant clauses (`matches`)
  - Risk level (GREEN / YELLOW / RED) with human-readable reasons
  - A short `answer` string summarizing the situation.

## Tech Stack (Backend)

- Python 3.11
- FastAPI + Uvicorn
- PyPDF2
- scikit-learn (TF-IDF + cosine)
- loguru
- Local storage under `storage/` and `embeddings/`
- JSON knowledge base under `knowledge/legal_kb.json`

## Quickstart (Local)

```bash
# 1. Create & activate venv (example for Windows PowerShell)
python -m venv .venv
.venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run server
python app.py
```

Server runs on http://localhost:5055.

Basic flow (for testing with curl or frontend):

`POST /files/upload` → get `job_id`.

`POST /process/{job_id}/parse`

`POST /rag/{job_id}/index`

`POST /query/{job_id}` with:

`{ "query": "security deposit", "top_k": 3 }`

The response includes `answer` and `matches` with risk levels and reasons.
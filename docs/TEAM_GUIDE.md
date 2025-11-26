# ClauseClear — Team Guide (Backend + Future Integration)

## Tech Stack (Backend MVP)

- **Language**: Python 3.11
- **Framework**: FastAPI (served by Uvicorn)
- **RAG / Search**: TF-IDF vectorizer + cosine similarity (scikit-learn)
- **PDF Parsing**: PyPDF2 (text extraction from PDF pages)
- **Risk / Severity Engine**: Custom rule-based engine in `services/severity.py`
- **Knowledge Base**: JSON file in `knowledge/legal_kb.json` (India rental/loan norms)
- **Logging**: Loguru → `logs/app.log`
- **Storage (MVP)**:
  - Local disk under `storage/uploads/<job_id>/...`
  - Local TF-IDF artifacts in `embeddings/<job_id>_*`
- **No external LLM/embedding API** in MVP → fully offline and cloud-friendly.

## Implemented Backend Flow (MVP)

1. `POST /files/upload`
   - Input: PDF file (e.g. rental agreement).
   - Output: `job_id`.
   - Saves file under `storage/uploads/<job_id>/`.

2. `POST /process/{job_id}/parse`
   - Uses `PyPDF2` to extract text.
   - Splits into simple clauses (sentence-like chunks).
   - Writes `clauses.json` under `storage/uploads/<job_id>/`.

3. `POST /rag/{job_id}/index`
   - Builds a **TF-IDF matrix** over all clause texts.
   - Stores:
     - `embeddings/<job_id>_tfidf.pkl` (fitted vectorizer)
     - `embeddings/<job_id>_matrix.pkl` (clause vectors)
     - `embeddings/<job_id>_meta.json` (clause IDs/pages).

4. `POST /query/{job_id}`
   - Body: `{ "query": "security deposit", "top_k": 3 }`.
   - Steps:
     - Uses TF-IDF + cosine similarity to find top-k clauses.
     - For each matched clause, runs the **rule-based severity engine**.
     - Severity engine uses `knowledge/legal_kb.json` thresholds (max deposit months, late fee %, etc.).
   - Response:
     - `answer`: human-friendly summary.
     - `matches`: list of clauses with:
       - `text`, `score` (similarity),
       - `risk_score`, `risk_level` (GREEN/YELLOW/RED),
       - `triggered_rules`, `reasons`.

## Notes for Future NoSQL + Frontend

- NoSQL teammate can store:
  - `job_id`, `user_id`, original filename, timestamps, status.
- Frontend teammate just needs to call:
  - `POST /files/upload`
  - `POST /process/{job_id}/parse`
  - `POST /rag/{job_id}/index`
  - `POST /query/{job_id}` and display:
    - `answer` (main heading text)
    - `matches` as clause cards.

## Frontend handoff (simple)
- Expect JSON only.
- CORS: add `fastapi.middleware.cors` later if needed.
- Flow to call from UI:
  1. `POST /files/upload` (multipart `file`) → get `job_id`
  2. `POST /process/{job_id}/parse`
  3. `POST /rag/{job_id}/index`
  4. `POST /rag/{job_id}/search` with `{"query": "...", "top_k": 3}`

## Future DB (Mongo/Firestore) — safe points
- Store only metadata + pointers (path, job_id, created_at).
- Do NOT store PDFs in DB. Keep files in object storage later.
- Add a `repositories/` layer to abstract writes so we can swap local → NoSQL easily.

## Cloud deploy (Google Cloud Run later)
- Keep `requirements.txt` small → faster builds.
- Add `Dockerfile` (later). Simple base: `python:3.11-slim`, copy app, `pip install -r requirements.txt`, `CMD ["python","app.py"]`.
- Expose port 8080 for Cloud Run (later we’ll switch `uvicorn.run(... port=8080)` or set env PORT).
- No secrets needed yet (good for first deploy).
- Health: `/health` is ready for Cloud Run.

## CI/CD (later, beginner flow)
- GitHub Actions: python setup → cache pip → run `flake8`/`pytest` (optional) → build image → deploy to Cloud Run.
- Keep artifacts (`embeddings/`, `storage/`) **NOT** committed—use `.gitignore`.
- Add a “demo dataset” folder for judges (tiny PDFs) or drive link.

## Conventions
- Keep functions small + pure.
- Avoid global state—job_id always in path.
- Log milestones (index built, parse ok).
- If any key/secret is added later, load from env (never commit).
## Severity Engine & Risk Scoring (v0.4)

- File: `services/severity.py`
- Approach: **rule-based + weighted scoring** (no LLM required for MVP).
- For each clause, we:
  - Extract simple signals: months, percentages, keywords (lock-in, notice, deposit, late fee, arbitration, etc.).
  - Apply a set of rules, each with a weight:
    - `lockin_gt_notice` (+0.50) → lock-in months > notice months.
    - `large_deposit` (+0.20) → security deposit >= ~2 months rent (or unclear but mentioned).
    - `unilateral_termination` (+0.40) → landlord/owner/lender can terminate at any time / without notice.
    - `high_late_fee` (+0.20) → late fee / penalty > ~3% per month.
    - `far_arbitration_maybe` (+0.20) → arbitration venue specified (may be far from user).
  - Sum weights → `risk_score` in [0, 1].
  - Map to `risk_level`:
    - 0–0.33 → GREEN
    - 0.34–0.66 → YELLOW
    - 0.67–1.0 → RED

- API:
  - `POST /analyze/{job_id}/clauses`
    - Input: `job_id` with existing `clauses.json`.
    - Output:
      - `summary` (counts of GREEN/YELLOW/RED)
      - `clauses` array with:
        - `risk_score`, `risk_level`, `triggered_rules`, `reasons`.
    - Side-effect:
      - Writes `storage/uploads/<job_id>/analysis.json` (for demo + future DB storage).

### Frontend usage

1. After upload + parse:
   - Call `POST /analyze/{job_id}/clauses`.
2. Use `summary` to show an overall risk bar or donut chart.
3. Use `risk_level` + `reasons` to color-code clauses and show short explanations.
4. Later, LLM (Gemini/OpenAI) can refine extraction, but the **rules and weights remain the same** for explainability.
## Unified Query Endpoint (v0.5)

- Route: `POST /query/{job_id}`
- Request body:
  ```json
  { "query": "security deposit", "top_k": 3 }
  ```

- Pipeline:
  - Reads `storage/uploads/<job_id>/clauses.json`.
  - Uses TF-IDF cosine search (`services/tfidf_index.search`) to get top-k clause indices.
  - For each matched clause, runs `services.severity.score_clause(...)`.

- Response:
  ```json
  {
    "job_id": "...",
    "query": "...",
    "top_k": 3,
    "matches": [
      {
        "id": "P01_C004",
        "page": 1,
        "text": "...",
        "score": 0.98,
        "risk_score": 0.7,
        "risk_level": "RED",
        "triggered_rules": ["large_deposit"],
        "reasons": ["Security deposit appears heavy compared to rent."]
      }
    ]
  }
  ```

- Frontend usage:
  - Call `/query/{job_id}` after:
    - upload → parse → rag index.
  - Show matches list with:
    - clause text
    - similarity score (optional)
    - color-coded risk_level + reasons.
## Legal Knowledge Base + KB-driven Severity Engine (v0.6)

- `knowledge/legal_kb.json` defines:
  - thresholds (deposit limit, late-fee limit)
  - severity rule weights
  - KB references for each rule
- Severity engine now loads values dynamically from JSON
  - Changing JSON changes severity output without code changes
- Future raw legal PDFs stored in `knowledge/pdfs/` (optional)
- Query fallback:
  - If similarity < 0.15 → return UNKNOWN
## How frontend + DB teammates should use this backend (MVP)

- What the backend does right now:
  - Upload file → gets a `job_id`.
  - Parse PDF → `clauses.json`.
  - Build TF-IDF index.
  - Run `/query/{job_id}` to:
    - Get top clauses (semantic search).
    - Get risk score + risk level per clause.
    - Get a friendly answer string.

- Which endpoints frontend will typically call:
  - `POST /files/upload` → show `job_id` or store it.
  - `POST /process/{job_id}/parse` → show “parsing…” and then “ready”.
  - `POST /rag/{job_id}/index` → build search index.
  - `POST /query/{job_id}` with `{ "query": "…" }` → show:
    - `answer` at the top (main text).
    - `matches` below as a list (clause text + risk color).

- Where future NoSQL integration fits:
  - They can store:
    - `job_id`, `user_id`, uploaded filename.
    - Timestamps and basic status.
  - But they don’t have to change backend routes; they just call the existing APIs.

- Where the legal knowledge base lives:
  - `knowledge/legal_kb.json` → thresholds (like max deposit months, max late fee %) and rule descriptions.
  - Severity engine uses this so they don’t need to touch it to build UI.
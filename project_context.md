# Project Context: ClauseClear Mini Backend (MVP)

## 1. Project Overview

**ClauseClear Mini Backend** is a lightweight FastAPI service designed for legal document analysis. It acts as an MVP (Minimum Viable Product) to demonstrate core capabilities like document ingestion, clause extraction, and semantic search (RAG) without heavy external dependencies like OpenAI or Pinecone.

## 2. Tech Stack

- **Framework:** FastAPI (Python)
- **PDF Parsing:** PyPDF2
- **Search/Indexing:** scikit-learn (TF-IDF Vectorizer + Cosine Similarity)
- **Storage:** Local filesystem (JSON files for metadata, `.pkl` files for indices)
- **Knowledge Base:** Local JSON (`knowledge/legal_kb.json`)

## 3. Core Workflow

The application follows a linear data processing pipeline:

1.  **Ingest:** `POST /files/upload` - Uploads a PDF.
2.  **Parse:** `POST /process/{job_id}/parse` - Extracts text and splits it into clauses (heuristics based on punctuation).
3.  **Index:** `POST /rag/{job_id}/index` - Builds a TF-IDF matrix for the clauses.
4.  **Analyze/Query:**
    - `POST /analyze/{job_id}/clauses`: Scores clauses against a "Legal Knowledge Base" to determine severity (Low/Medium/High/Critical).
    - `POST /query/{job_id}`: Combines RAG search with severity analysis to answer user questions about the document.

## 4. Implementation Details

### 4.1. Clause Extraction (`services/clauses.py`)

- **Logic**: Simple heuristic splitting based on punctuation (`.`, `;`, `\n`).
- **Filter**: Ignores segments shorter than 10 characters.
- **Goal**: To break large legal texts into atomic, analyzable units.

### 4.2. TF-IDF Search Index (`services/tfidf_index.py`)

- **Algorithm**: `TfidfVectorizer` (scikit-learn) with `ngram_range=(1,2)` (unigrams + bigrams).
- **Features**: Max 20,000 features to keep it lightweight.
- **Storage**:
  - `.tfidf.pkl`: The trained vectorizer model.
  - `.matrix.pkl`: The sparse matrix of document vectors.
  - `.meta.json`: Metadata mapping matrix rows to clause IDs and page numbers.
- **Search**: Computes **cosine similarity** between the query vector and all clause vectors to find the best matches.

### 4.3. Severity Engine (`services/severity.py` & `knowledge/legal_kb.json`)

- **Concept**: A rule-based system that scores clauses based on specific keywords and patterns defined in `legal_kb.json`.
- **Knowledge Base Rules**:
  - `lockin_gt_notice` (Weight 0.5): Lock-in period > Notice period.
  - `large_deposit` (Weight 0.2): Deposit > 3 months (configurable threshold).
  - `large_deposit_unsure` (Weight 0.1): Deposit mentioned but amount is unclear.
  - `unilateral_termination` (Weight 0.4): One-sided termination rights (e.g., "sole discretion").
  - `high_late_fee` (Weight 0.2): Late fee > 3% (configurable threshold).

### 4.4. Authentication & Developer Access

- **Firebase Auth**: Used for standard user authentication (Email/Password).
- **Developer Bypass**:

  - **Credentials**: Email: `dev@clauseclear.com`, Password: `dev123`
  - **Function**: Allows access to the dashboard without requiring a valid Firebase configuration or internet connection.
  - **Implementation**: Uses `sessionStorage` flag `dev_bypass` to skip auth checks on frontend pages.

- **Risk Calculation**:
  - **Score**: Sum of weights of triggered rules (capped at 1.0).
  - **Levels**:
    - **RED**: Score >= 0.67
    - **YELLOW**: Score >= 0.34
    - **GREEN**: Score < 0.34

## 5. Current Status (v0.8)

- **Completed:**
  - Basic API endpoints (Upload, Parse, Index, Search).
  - Root endpoint (`/`) and Health check (`/health`).
  - "Severity Engine" (Key-value matching against `legal_kb.json`).
  - "Unknown" fallback logic for queries that don't match the context.
  - Developer documentation (`README.md`, `docs/TEAM_GUIDE.md`).
- **Data Structure:**
  - Input: PDF Documents.
  - Intermediate: `clauses.json` (parsed text).
  - Output: JSON responses with semantic matches and severity scores.

## 6. Directory Structure Key

- `app.py`: Main entry point and API route definitions.
- `create_dummy_pdf_with_text.py`: Script to generate test PDFs.
- `upload_pdf.py`: Helper script to upload PDFs via API.
- `services/`: Core logic modules.
  - `parse_pdf.py`: PDF text extraction.
  - `clauses.py`: Text segmentation logic.
  - `tfidf_index.py`: RAG implementation using scikit-learn.
  - `severity.py`: Rule-based risk scoring engine.
  - `kb_loader.py`: Loads the legal knowledge base.
- `knowledge/`: Static data (KB) and storage for uploaded PDFs.
  - `legal_kb.json`: Defines risk rules and thresholds (e.g., max deposit months).

## 7. Run Requirements

To run this project, you need:

**Prerequisites:**

- **Python 3.11** (recommended)
- **Git** (to clone the repo)

**Dependencies (install via `pip install -r requirements.txt`):**

- `fastapi`, `uvicorn[standard]` (Web server)
- `PyPDF2` (PDF handling)
- `scikit-learn`, `joblib` (ML/Search)
- `loguru` (Logging)
- `requests`, `reportlab` (Utilities)

**Quick Start Command:**

```bash
# 1. Create/Activate virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run Server
python -m uvicorn app:app --host 127.0.0.1 --port 5055 --reload
```

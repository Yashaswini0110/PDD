# ClauseClear Project Report

## Project Overview

ClauseClear is an AI-powered legal clause analysis tool designed to help tenants and borrowers in India understand rental agreements and loan contracts. The system analyzes uploaded PDF documents, extracts clauses, assigns risk levels (GREEN/YELLOW/RED) based on India-specific rules, and provides plain-English explanations at an 8th-grade reading level. Users can ask questions about their contracts and receive answers with exact clause citations, making complex legal language accessible to non-experts.

The backend uses a rule-based severity engine combined with TF-IDF search for clause retrieval, and optionally leverages Google Gemini to rewrite technical explanations into simple, tenant-friendly language. The system is deployed on Google Cloud Run with a Jenkins CI/CD pipeline.

## System Architecture (High-Level)

The main flow follows this pipeline:

1. **PDF Upload** → User uploads a contract PDF via the frontend
2. **Parse** → PDF text is extracted page-by-page using PyPDF2
3. **Clause Splitting** → Text is split into individual clauses using sentence boundaries
4. **TF-IDF Indexing** → Clauses are indexed for semantic search using scikit-learn
5. **Severity Scoring** → Each clause is analyzed against India-specific rules (security deposits, lock-in periods, termination clauses, etc.) to assign risk levels
6. **Query & RAG** → User queries are matched to relevant clauses using TF-IDF cosine similarity
7. **LLM Explanation** (optional) → Gemini rewrites rule-based answers into simple, 8th-grade language
8. **Frontend UI** → Results are displayed with risk flags, explanations, and clause citations

## Backend Pipeline (FastAPI + Services)

### Core Components

**`app.py`** - Main FastAPI application that orchestrates the entire pipeline. Defines REST endpoints for:
- File uploads (`/files/upload`)
- PDF parsing (`/process/{job_id}/parse`)
- RAG indexing (`/rag/{job_id}/index`)
- Query with risk scoring (`/query/{job_id}`)
- LLM-powered explanations (`/query_llm/{job_id}`)
- User management and job history endpoints

**`services/clauses.py`** - Splits document text into individual clauses using regex patterns (splits on periods, semicolons, or line breaks). Filters out very short fragments (< 10 characters).

**`services/parse_pdf.py`** - Extracts text from PDF files using PyPDF2. Returns a list of page texts, preserving page numbers for clause citation.

**`services/tfidf_index.py`** - Builds TF-IDF vectorization models for semantic search:
- Uses scikit-learn's `TfidfVectorizer` with unigrams and bigrams
- Saves vectorizer and matrix to disk (`embeddings/{job_id}.tfidf.pkl`)
- Implements cosine similarity search to find top-k matching clauses for user queries

**`services/severity.py` + `knowledge/legal_kb.json`** - Rule-based risk scoring engine:
- Loads severity rules and thresholds from `legal_kb.json` (India-specific: max security deposit months, late fee percentages, etc.)
- Applies weighted rules to each clause (e.g., "lockin_gt_notice", "very_large_deposit", "unilateral_termination")
- Calculates risk scores and assigns GREEN/YELLOW/RED levels based on thresholds
- Returns structured results with risk level, score, and reasons

**`services/llm_explainer.py`** - Calls Google Gemini API (via REST) to rewrite rule-based answers into simple language:
- Uses Gemini API endpoint: `https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent`
- Takes the base answer from the severity engine and top matching clauses
- Sends a carefully crafted prompt to Gemini with system instructions for 8th-grade explanations
- Uses API key authentication (not Vertex AI SDK)
- Returns plain-English text that explains what the clause means in everyday terms
- Falls back to base_answer if API key is missing or API call fails

**`services/db.py`** - MongoDB connection management:
- Connects to MongoDB using `MONGO_URI` environment variable
- Stores user profiles, job history, and chat history
- Gracefully handles connection failures (app continues in mock mode)

**`services/kb_loader.py`** - Loads the legal knowledge base JSON file from `knowledge/legal_kb.json`

**`utils.py`** - Utility functions:
- `safe_filename()` - Sanitizes filenames for safe storage
- `ensure_dirs()` - Creates necessary directories (storage/uploads, embeddings, logs)

### Main API Endpoints

- `POST /files/upload` - Upload a PDF file, returns `job_id`
- `POST /process/{job_id}/parse` - Extract text and split into clauses
- `POST /rag/{job_id}/index` - Build TF-IDF index for semantic search
- `POST /query/{job_id}` - Query clauses with risk scoring (returns base_answer)
- `POST /query_llm/{job_id}` - Query with LLM explanation (returns base_answer + answer_llm)
- `GET /users/{uid}/history` - Get user's job history from MongoDB
- `POST /analyze/{job_id}/clauses` - Run severity analysis on all clauses

## LLM Explanation Layer (Gemini API)

The `/query_llm/{job_id}` endpoint enhances the standard query flow by adding a Gemini-powered explanation layer. Here's how it works:

1. **Reuses existing pipeline**: First runs the same TF-IDF search and severity scoring as `/query/{job_id}`
2. **Builds context**: Collects top-k matching clauses with their risk levels, scores, and reasons
3. **Calls Gemini API (REST)**: Makes HTTP POST request to `https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent` with:
   - API key authentication via `x-goog-api-key` header
   - System instruction: "Explain rental terms in simple, everyday language like helping a friend"
   - User message: The query, matched clause text, and risk level
   - Constraints: Must only use information from the provided clauses, no invention
4. **Returns dual answers**: 
   - `base_answer`: Rule-based technical explanation
   - `answer_llm`: Gemini-generated, 8th-grade friendly explanation

**Important**: Gemini API is used ONLY to rewrite existing explanations into simpler language. It does not invent new clauses or add information not present in the document. If the document doesn't clearly answer the question, the LLM is instructed to say so.

**Note**: This implementation uses Gemini API via REST (not Vertex AI SDK), making it simpler to deploy and manage.

**Environment Variables**:
- `GEMINI_API_KEY` - Required for LLM features (falls back to base_answer if missing)
- `GEMINI_MODEL_NAME` - Optional, defaults to "gemini-2.0-flash"

## DevOps: Docker, Jenkins, and Cloud Run

### Dockerfile

The `Dockerfile` creates a slim Python 3.11 container:
- Installs dependencies from `requirements.txt`
- Copies all project files into `/app`
- Sets `PORT=5055` as environment variable
- Runs `uvicorn app:app --host 0.0.0.0 --port ${PORT:-5055}` (Cloud Run sets PORT dynamically)

### Jenkinsfile

The Jenkins pipeline automates CI/CD with 4 stages:

1. **Checkout** - Clones the repository
2. **Docker Build** - Builds Docker image tagged for GCP Artifact Registry (`us-central1-docker.pkg.dev/productdesigndev/clauseclear/clauseclear-backend:latest`)
3. **Push to Artifact Registry** - Authenticates with GCP service account, configures Docker, and pushes the image
4. **Deploy to Cloud Run** - Deploys the service with:
   - Environment variables injected from Jenkins credentials: `GEMINI_API_KEY`, `MONGO_URI`, `GEMINI_MODEL_NAME=gemini-2.0-flash`
   - Port 5055 exposed
   - Unauthenticated access enabled (public endpoint)

### Cloud Run Deployment

Cloud Run runs the container as a stateless service:
- Listens on `0.0.0.0:PORT` (PORT set by Cloud Run, defaults to 5055)
- Local storage directories (`storage/uploads/`, `embeddings/`, `logs/`) are ephemeral (lost on container restart)
- Auto-scales based on traffic
- Each request is independent (no shared state between requests)

## File-by-File Overview (Key Files Table)

| File / Folder | Purpose |
|--------------|---------|
| `app.py` | Main FastAPI application, defines all REST endpoints (upload, parse, index, query, query_llm) |
| `PDD/app.py` | Enhanced version with LLM explainer support (includes `/query_llm` endpoint) |
| `services/clauses.py` | Splits document text into individual clauses using regex patterns |
| `services/parse_pdf.py` | Extracts text from PDF files using PyPDF2, returns page-by-page text |
| `services/tfidf_index.py` | Builds TF-IDF vectorization models and implements cosine similarity search |
| `services/severity.py` | Rule-based risk scoring engine, applies India-specific rules to clauses |
| `services/llm_explainer.py` | Calls Google Gemini API to rewrite answers in simple, 8th-grade language |
| `services/db.py` | MongoDB connection management, handles user profiles and job history |
| `services/kb_loader.py` | Loads legal knowledge base JSON file |
| `utils.py` | Utility functions (safe_filename, ensure_dirs) |
| `knowledge/legal_kb.json` | India-specific severity rules, thresholds, and risk patterns |
| `evaluate_severity.py` | Developer test script: evaluates severity engine accuracy against labeled test data |
| `test_full_flow.py` | End-to-end pipeline test: upload → parse → index → query (requires server running) |
| `PDD/test_llm_flow.py` | LLM endpoint test: tests `/query_llm` with base_answer vs answer_llm comparison |
| `Dockerfile` | Container build instructions (Python 3.11-slim, uvicorn) |
| `PDD/Dockerfile` | Enhanced Dockerfile with PORT environment variable support |
| `Jenkinsfile` | CI/CD pipeline: build → push to Artifact Registry → deploy to Cloud Run |
| `PDD/Jenkinsfile` | Jenkins pipeline with environment variable injection (GEMINI_API_KEY, MONGO_URI) |
| `requirements.txt` | Python dependencies (FastAPI, uvicorn, PyPDF2, scikit-learn, pymongo, requests, etc.) |
| `static/` | Frontend HTML/CSS/JS files (index.html, home.html, uploads.html, results.html, etc.) |
| `storage/uploads/` | Temporary storage for uploaded PDFs and generated JSON files (clauses.json, analysis.json) |
| `embeddings/` | TF-IDF vectorizer and matrix files (`.tfidf.pkl`, `.matrix.pkl`) |
| `logs/` | Application logs (app.log) |

## How to Run Locally (Developer Guide)

### Step 1: Create Virtual Environment

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\activate
# Linux/macOS:
# source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Set Environment Variables

Create a `.env` file in the project root with:

```
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI=mongodb://localhost:27017
GEMINI_MODEL_NAME=gemini-2.0-flash
FIREBASE_API_KEY=your_firebase_key
FIREBASE_AUTH_DOMAIN=your_firebase_domain
FIREBASE_PROJECT_ID=your_firebase_project
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
```

### Step 4: Start the FastAPI Server

```bash
# From root directory:
python -m uvicorn app:app --host 0.0.0.0 --port 5055 --reload

# Or from PDD directory (if using PDD/app.py):
cd PDD
python -m uvicorn app:app --host 0.0.0.0 --port 5055 --reload
```

The API will be accessible at `http://localhost:5055`.

### Step 5: Run Test Scripts

In separate terminal windows (with server running):

```bash
# Test severity engine (requires tests/tests/labeled_clauses_sample.json):
python evaluate_severity.py

# Test full pipeline (requires server on port 5055):
python test_full_flow.py

# Test LLM flow (requires server on port 5055 and GEMINI_API_KEY):
cd PDD
python test_llm_flow.py
```

## How to Trigger CI/CD and Check Cloud Run

### Triggering Jenkins Pipeline

The Jenkins pipeline can be triggered:
- **Automatically**: On push to the main branch (if configured in Jenkins)
- **Manually**: Via Jenkins UI by clicking "Build Now" on the job

### Pipeline Stages

1. **Checkout**: Clones repository from SCM
2. **Docker Build**: Builds image with tag for Artifact Registry
3. **Push to Artifact Registry**: Authenticates with GCP, pushes image to `us-central1-docker.pkg.dev/productdesigndev/clauseclear/clauseclear-backend:latest`
4. **Deploy to Cloud Run**: Deploys service `clauseclear-backend` to `us-central1` region with environment variables from Jenkins credentials

### Verifying Deployment

After deployment, check the Cloud Run service:
- Visit GCP Console → Cloud Run → `clauseclear-backend`
- Verify the service URL (e.g., `https://clauseclear-backend-xxx-uc.a.run.app`)
- Test the health endpoint: `GET https://your-service-url/health` (should return `{"status": "ok"}`)
- Check logs in Cloud Run console for any startup errors

## Future Work / Limitations

- **Limited Contract Types**: Currently optimized for rental and loan contracts; support for employment, sales agreements, etc. would require expanding the knowledge base
- **English Only**: No multilingual support; contracts in Hindi or other Indian languages are not supported
- **Basic UI**: Frontend is functional but could benefit from richer UX, better mobile responsiveness, and more interactive visualizations
- **No PDF Export**: Users cannot export analysis results as PDF reports (only JSON data available)
- **Ephemeral Storage**: Uploaded files and embeddings are stored locally (`storage/uploads/`, `embeddings/`) and lost on container restart; persistent cloud storage integration would provide better durability
- **Limited Legal KB**: Knowledge base has basic rules; expanding with more India-specific regulations (RERA, consumer protection laws) would improve accuracy
- **No Multi-Document Support**: Users can only analyze one document at a time; batch processing or comparison features would be valuable

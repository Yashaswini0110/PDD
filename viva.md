# ClauseClear - Viva Examination Q&A Guide

This document contains comprehensive answers to potential examiner questions for the Product Design & Development viva demo.

---

## 1. Architecture & Workflow

### Q: Explain the full system architecture.

**Answer:**

The system follows a **three-tier architecture**:

1. **Frontend Layer**: Static HTML/CSS/JS files served by FastAPI (`static/` directory)
   - Firebase Auth for user authentication (with dev bypass for testing)
   - Single-page application for document upload, analysis, and Q&A

2. **Backend Layer** (FastAPI application deployed on Cloud Run):
   - **API Endpoints** (`app.py`): RESTful endpoints for upload, parse, index, query
   - **Service Modules** (`services/`):
     - `parse_pdf.py`: PyPDF2 text extraction
     - `clauses.py`: Regex-based clause splitting
     - `tfidf_index.py`: TF-IDF vectorization and search
     - `severity.py`: Rule-based risk scoring engine
     - `llm_explainer.py`: Gemini API integration for simplification
     - `db.py`: MongoDB connection (optional, graceful degradation)

3. **Data Layer**:
   - **Local Filesystem**: `storage/uploads/{job_id}/` for PDFs and JSON artifacts
   - **Embeddings**: `embeddings/{job_id}.pkl` for TF-IDF indices
   - **MongoDB** (optional): User profiles, job history, chat logs
   - **Knowledge Base**: `knowledge/legal_kb.json` with India-specific rules

**Technical Stack:**
- Backend: FastAPI, Python 3.11, Uvicorn
- PDF Processing: PyPDF2
- Search: scikit-learn TF-IDF + Cosine Similarity
- AI: Google Gemini API (optional)
- Database: MongoDB (optional)
- Deployment: Docker, Google Cloud Run
- CI/CD: Jenkins

---

### Q: Draw and explain the data flow.

**Answer:**

```
User Upload (PDF)
    ↓
[POST /files/upload]
    ↓
storage/uploads/{job_id}/document.pdf + created_at.txt
    ↓
[POST /process/{job_id}/parse]
    ↓
PyPDF2 → Page texts → Clause splitting → clauses.json
    ↓
[POST /rag/{job_id}/index]
    ↓
TF-IDF Vectorizer → embeddings/{job_id}.{tfidf,matrix,meta}.pkl
    ↓
[POST /analyze/{job_id}/clauses]
    ↓
Severity Engine (legal_kb.json) → analysis.json → MongoDB (job summary)
    ↓
[POST /query/{job_id} or /query_llm/{job_id}]
    ↓
Query Vectorization → Cosine Similarity → Top-K Matches
    ↓
Risk Enrichment (score_clause) → Base Answer
    ↓
[Optional: Gemini LLM] → Simplified Answer
    ↓
JSON Response → Frontend Display
```

**Explanation:**
- Each step is a separate API endpoint, allowing for modular processing
- `job_id` (UUID) tracks the document through the entire pipeline
- Intermediate results are saved as JSON files for debugging and recovery
- TF-IDF index enables fast semantic search
- Severity engine applies India-specific legal rules
- LLM is optional and only used for final language simplification

---

### Q: What happens from PDF upload to result display?

**Answer:**

**Step-by-Step Process:**

1. **Upload** (`POST /files/upload`):
   - Validates file (max 10MB, PDF/DOCX only)
   - Generates unique UUID `job_id`
   - Saves file to `storage/uploads/{job_id}/` with timestamp

2. **Parse** (`POST /process/{job_id}/parse`):
   - PyPDF2 extracts text page-by-page
   - Splits text into clauses using punctuation heuristics (`.`, `;`, `\n`)
   - Creates `clauses.json` with structure: `{id: "P01_C001", page: 1, text: "..."}`

3. **Index** (`POST /rag/{job_id}/index`):
   - Builds TF-IDF matrix (unigrams + bigrams, max 20K features)
   - Saves vectorizer, matrix, and metadata to `embeddings/` directory

4. **Analyze** (`POST /analyze/{job_id}/clauses`):
   - Scores each clause against `legal_kb.json` rules
   - Assigns GREEN/YELLOW/RED risk levels
   - Saves `analysis.json` and stores summary in MongoDB

5. **Query** (`POST /query/{job_id}`):
   - Vectorizes user query
   - Computes cosine similarity to find top-K matching clauses
   - Enriches matches with risk scores
   - Builds answer with exact clause citations

6. **LLM Enhancement** (optional, `POST /query_llm/{job_id}`):
   - Sends matches to Gemini with strict prompt
   - Rewrites answer into simple, 8th-grade language
   - Returns plain-English explanation

7. **Frontend Display**:
   - Shows risk flags (GREEN/YELLOW/RED)
   - Displays clause citations with page numbers
   - Presents simplified answers
   - Maintains chat history

---

## 2. AI vs Non-AI Logic

### Q: Why are we using TF-IDF and isn't it not suitable for production scale?

**Answer:**

**Why TF-IDF was chosen (for MVP):**

1. **Simplicity & Speed**:
   - No external API dependencies (unlike OpenAI embeddings or Pinecone)
   - Fast indexing and search (cosine similarity is O(n) for n clauses)
   - Works offline without internet connection

2. **Cost Efficiency**:
   - Completely free (no API costs)
   - No per-query charges
   - Suitable for MVP budget constraints

3. **Deterministic & Explainable**:
   - Same query always returns same results (no randomness)
   - Scores are interpretable (TF-IDF weights)
   - Easier to debug and validate

4. **Lightweight**:
   - Max 20,000 features (keeps memory footprint small)
   - Sparse matrix representation (efficient storage)
   - Fast startup time

5. **Good Enough for MVP**:
   - Works well for keyword-based queries ("security deposit", "termination")
   - Unigrams + bigrams capture phrase-level semantics
   - Sufficient for document-specific retrieval (not general knowledge)

**Production Scale Limitations:**

1. **Semantic Understanding**:
   - TF-IDF is keyword-based, not semantic
   - Can't understand synonyms or paraphrases well
   - Example: "rental fee" vs "monthly rent" may not match well

2. **Context Limitations**:
   - Doesn't understand word order or context deeply
   - "No deposit required" vs "Deposit required" might have similar vectors

3. **Scalability Concerns**:
   - Linear search through all clauses (O(n) for n clauses)
   - For 10,000+ clauses, search becomes slower
   - No approximate nearest neighbor (ANN) optimization

4. **No Cross-Document Learning**:
   - Each document indexed independently
   - Can't leverage patterns across multiple contracts

**Production Alternatives:**

1. **Dense Embeddings** (e.g., Sentence-BERT, OpenAI embeddings):
   - Better semantic understanding
   - Can use vector databases (Pinecone, Weaviate, Qdrant)
   - Approximate nearest neighbor search (much faster)
   - **Trade-off**: API costs, external dependencies

2. **Hybrid Approach** (TF-IDF + Embeddings):
   - Use TF-IDF for exact keyword matches
   - Use embeddings for semantic similarity
   - Combine results (best of both worlds)

3. **Fine-tuned Models**:
   - Train domain-specific embeddings on legal documents
   - Better understanding of legal terminology
   - **Trade-off**: Requires training data and infrastructure

**Current Implementation Strategy:**

- **MVP Phase**: TF-IDF is appropriate because:
  - Fast to implement
  - No external dependencies
  - Works for proof-of-concept
  - Cost-effective for demo

- **Production Phase**: Would migrate to:
  - Dense embeddings (e.g., `sentence-transformers/all-MiniLM-L6-v2`)
  - Vector database (Pinecone or self-hosted Qdrant)
  - Hybrid retrieval (keyword + semantic)

**Code Evidence:**
```python
# services/tfidf_index.py line 20-24
vectorizer = TfidfVectorizer(
    lowercase=True,
    ngram_range=(1,2),      # unigrams + bigrams for better recall
    max_features=20000,     # small, deploy-friendly
)
```

The comment "small, deploy-friendly" indicates this was a conscious MVP choice.

---

### Q: Which parts are AI-based?

**Answer:**

**Only ONE component uses AI (generative):**

1. **Gemini LLM** (`services/llm_explainer.py`):
   - **Purpose**: Rewrites rule-based answers into simple, 8th-grade language
   - **Usage**: Only in `/query_llm/{job_id}` endpoint (optional)
   - **Input**: User query + matched clauses + risk scores
   - **Output**: Plain-English explanation
   - **NOT used for**: Clause extraction, risk scoring, or document parsing

**Note:** TF-IDF is statistical (not generative AI) - it's deterministic vectorization.

---

### Q: Which parts are deterministic?

**Answer:**

**All core components are deterministic (non-AI):**

1. **PDF Parsing** (`services/parse_pdf.py`):
   - PyPDF2 text extraction (deterministic library)

2. **Clause Splitting** (`services/clauses.py`):
   - Regex-based splitting on punctuation (`.`, `;`, `\n`)
   - Filters segments <10 characters

3. **TF-IDF Search** (`services/tfidf_index.py`):
   - Statistical vectorization (not generative AI)
   - Cosine similarity matching (deterministic algorithm)
   - Returns exact clause matches from document

4. **Severity Engine** (`services/severity.py`):
   - **Rule-based pattern matching** against `legal_kb.json`:
     - Regex patterns for lock-in periods, deposits, termination clauses
     - Weighted scoring (sum of rule weights, capped at 1.0)
     - Threshold-based classification:
       - GREEN: score < 0.3
       - YELLOW: 0.3 ≤ score < 0.69
       - RED: score ≥ 0.69

**All of these produce the same output for the same input - no randomness.**

---

### Q: Why did you not rely purely on AI?

**Answer:**

**Hybrid approach for accuracy, cost, and reliability:**

1. **Accuracy & Reliability**:
   - Rule-based scoring provides consistent, explainable risk flags
   - Based on India-specific legal norms (Model Tenancy Act, RBI guidelines)
   - No hallucination risk in core analysis

2. **Cost Efficiency**:
   - TF-IDF is free and fast (no API costs)
   - LLM only used for final simplification (optional)
   - Can run core pipeline without any AI costs

3. **Hallucination Prevention**:
   - Rules ground answers in actual document text
   - LLM only rewrites existing answers, doesn't generate new information
   - Strict prompts prevent invention of clauses

4. **Transparency**:
   - Users see which rules triggered (e.g., "Security deposit >= 4 months" → RED)
   - Risk scores are explainable (sum of weighted rules)
   - Exact clause citations provided

5. **Offline Capability**:
   - Core pipeline works without LLM
   - Gemini is optional enhancement for user experience

**Philosophy**: Rules for accuracy, AI for accessibility.

---

## 3. Testing & Validation

### Q: How did you test the system?

**Answer:**

**Three testing approaches:**

1. **Integration Tests**:
   - `test_full_flow.py`: End-to-end pipeline test
     - Uploads `sample.1.pdf`
     - Tests: upload → parse → index → query with multiple questions
     - Validates response structure, clause counts, risk levels
   - `test_llm_flow.py`: LLM endpoint test
     - Tests `/query_llm/{job_id}` with sample queries
     - Compares `base_answer` vs `answer_llm` (rule-based vs LLM-enhanced)

2. **Severity Engine Evaluation**:
   - `evaluate_severity.py`: Validates rule-based scoring
     - Loads labeled test cases from `tests/labeled_clauses_sample.json`
     - Computes accuracy and confusion matrix (GREEN/YELLOW/RED)
     - Reports mismatches with expected vs predicted labels

3. **Manual Testing**:
   - Test scripts run against local server (`http://127.0.0.1:5055`)
   - Validates each endpoint individually

**Note**: No unit tests found - testing is integration-based.

---

### Q: What test cases were used?

**Answer:**

**From `test_full_flow.py`:**
- Query: "security deposit" → Validates deposit detection
- Query: "termination" → Validates termination clause detection
- Query: "general clause" → Validates GREEN risk classification

**From `test_llm_flow.py`:**
- "What is the monthly rent?"
- "What happens if I pay rent late?"
- "Can I leave early before the lock-in period ends?"

**From `evaluate_severity.py`:**
- Labeled clauses with expected risk levels (GREEN/YELLOW/RED)
- Tests rule matching accuracy

---

### Q: How do you validate correctness of answers?

**Answer:**

**Multiple validation mechanisms:**

1. **Rule-Based Grounding**:
   - Answers cite exact clause IDs and page numbers from document
   - No information generated without document evidence

2. **Risk Score Transparency**:
   - Each match shows `risk_score`, `risk_level`, and `reasons`
   - Users can verify which rules triggered

3. **Fallback Logic**:
   - If no matches found, returns: "UNKNOWN – this clause does not exist clearly in your document"
   - Prevents hallucination

4. **LLM Prompt Constraints**:
   - System instruction explicitly forbids inventing clauses
   - Must say "document doesn't clearly talk about this" if ambiguous

5. **Evaluation Metrics**:
   - `evaluate_severity.py` measures accuracy against labeled test cases
   - Confusion matrix shows classification performance

---

### Q: How do you handle wrong or unclear documents?

**Answer:**

**Error handling at multiple levels:**

1. **Invalid File Types**: `HTTPException(400)` if not PDF/DOCX

2. **File Too Large**: `HTTPException(413)` if >10MB

3. **Empty/Corrupted PDFs**:
   - PyPDF2 may return empty text
   - Clause splitting filters segments <10 characters

4. **Unclear Queries**:
   - Empty query returns `HTTPException(400)`
   - No matches returns "UNKNOWN" message

5. **Ambiguous Clauses**:
   - Severity engine assigns lower weights for unclear cases
   - `large_deposit_unsure` (weight 0.2) if deposit mentioned but amount unclear
   - May classify as GREEN if insufficient evidence

---

## 4. Docker & Deployment

### Q: Why did you use Docker?

**Answer:**

**Four key reasons:**

1. **Consistency**: Same environment across dev, staging, production
2. **Cloud Run Requirement**: Cloud Run requires containerized applications
3. **Dependency Isolation**: Python 3.11, FastAPI, scikit-learn bundled together
4. **Portability**: Image runs on any Docker-compatible platform

---

### Q: What is inside your Dockerfile?

**Answer:**

```dockerfile
FROM python:3.11-slim          # Base image (lightweight Python)
WORKDIR /app                   # Working directory
COPY requirements.txt .         # Copy dependency list
RUN pip install --no-cache-dir -r requirements.txt  # Install deps
COPY . .                       # Copy entire codebase
ENV PORT=5055                  # Set default port
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "5055"]  # Start server
```

**Optimization**: Uses `python:3.11-slim` (smaller than full Python image).

---

### Q: How does containerization help deployment?

**Answer:**

**Five benefits:**

1. **Artifact Registry**: Single image pushed to GCP Artifact Registry, versioned with tags
2. **Cloud Run Deployment**: Cloud Run pulls image and runs container; no server management
3. **Scaling**: Cloud Run auto-scales containers based on traffic
4. **Environment Variables**: Injected at deployment time (GEMINI_API_KEY, MONGO_URI, etc.)
5. **Isolation**: Each request runs in isolated container; failures don't affect others

---

## 5. CI/CD (Jenkins)

### Q: What triggers your pipeline?

**Answer:**

- **Manual**: "Build Now" button in Jenkins UI
- **Automatic** (if configured): Webhook on push to repository (not explicitly configured in Jenkinsfile)

---

### Q: What stages exist in your Jenkinsfile?

**Answer:**

**4 Stages:**

1. **Checkout**:
   - `checkout scm` clones repository
   - `ls -la` for debugging

2. **Docker Build**:
   - `docker build -t ${IMAGE}:latest .`
   - Image tag: `us-central1-docker.pkg.dev/productdesigndev/clauseclear/clauseclear-backend:latest`

3. **Push to Artifact Registry**:
   - Authenticates with GCP service account (Jenkins credential `gcp-sa-json`)
   - `gcloud auth configure-docker` for Artifact Registry
   - `docker push ${IMAGE}:latest`

4. **Deploy to Cloud Run**:
   - Authenticates with GCP
   - `gcloud run deploy clauseclear-backend` with:
     - `--image ${IMAGE}:latest`
     - `--region us-central1`
     - `--platform managed`
     - `--allow-unauthenticated`
     - `--port 5055`

---

### Q: How do you handle secrets?

**Answer:**

- **GCP Service Account Key**: Stored as Jenkins file credential `gcp-sa-json`
- **Environment Variables**: Injected at Cloud Run deployment (GEMINI_API_KEY, MONGO_URI, GEMINI_MODEL_NAME) via Cloud Run service configuration

**Note**: Secrets are not hardcoded in Jenkinsfile; they're stored in Jenkins credential manager.

---

### Q: How do you know the deployment succeeded?

**Answer:**

**Four verification methods:**

1. **Cloud Run Console**: Check service status in GCP Console → Cloud Run → `clauseclear-backend`
2. **Health Endpoint**: `GET https://service-url/health` should return `{"status": "ok"}`
3. **Logs**: Cloud Run logs show startup errors or successful deployment
4. **Service URL**: Cloud Run provides public URL (e.g., `https://clauseclear-backend-xxx-uc.a.run.app`)

---

## 6. Cloud Run & Google Cloud

### Q: Why Cloud Run instead of VM?

**Answer:**

**Five advantages:**

1. **Serverless**: No VM management; Cloud Run handles infrastructure
2. **Auto-Scaling**: Scales to zero when idle; scales up to handle traffic
3. **Cost Efficiency**: Pay per request (not for idle time)
4. **Fast Deployment**: Container deployment in seconds (vs VM provisioning)
5. **Managed Service**: Automatic health checks, logging, monitoring

---

### Q: How does scaling work?

**Answer:**

- **Request-Based**: Cloud Run spins up containers on incoming requests
- **Concurrency**: Each container handles multiple requests (default 80, configurable)
- **Auto-Scale**: Scales from 0 to N based on traffic
- **Cold Starts**: First request may have latency; subsequent requests are fast

---

### Q: How are environment variables handled?

**Answer:**

- **Set at Deployment**: `gcloud run deploy` accepts `--set-env-vars` (configured separately, not in Jenkinsfile)
- **Secrets**: Can use Secret Manager (not implemented; currently uses plain env vars)
- **Runtime Access**: FastAPI reads via `os.getenv()` (e.g., `GEMINI_API_KEY`, `MONGO_URI`)

---

## 7. Privacy & Security

### Q: Where is the document stored?

**Answer:**

- **Local Filesystem**: `storage/uploads/{job_id}/document.pdf` (ephemeral on Cloud Run; lost on container restart)
- **Note**: README mentions GCS, but implementation uses local filesystem only

---

### Q: When is it deleted?

**Answer:**

- **Current Implementation**: No delete endpoint implemented (despite README mentioning "Delete Now")
- **Ephemeral Storage**: Files automatically lost on Cloud Run container restart (not persistent)
- **No TTL Mechanism**: No automatic expiry implemented

**Limitation**: Delete endpoint not implemented; manual cleanup or container restart required.

---

### Q: How do you prove privacy in demo?

**Answer:**

**Four privacy measures:**

1. **Temporary Storage**: Files stored per `job_id` (UUID), not by user identity
2. **Timestamp Tracking**: `created_at.txt` records upload time (could be used for TTL)
3. **MongoDB**: Stores job summaries and chat history (optional; app degrades gracefully if DB unavailable)
4. **No Cross-User Access**: Each `job_id` is unique; no shared storage between users

**Note**: Delete endpoint mentioned in README but not implemented in code.

---

## 8. Failure & Edge Cases

### Q: What if OCR fails?

**Answer:**

- **Not Applicable**: System uses PyPDF2 (text extraction, not OCR)
- **Scanned PDFs**: PyPDF2 may return empty text; clause splitting filters empty segments
- **Future**: Would need Document AI OCR (mentioned in README but not implemented)

---

### Q: What if the clause is ambiguous?

**Answer:**

**Three handling mechanisms:**

1. **Severity Engine**: Assigns lower weights for unclear cases
   - `large_deposit_unsure` (weight 0.2) if deposit mentioned but amount unclear
2. **Risk Score Aggregation**: Multiple rules contribute; ambiguous clauses get lower scores (may classify as GREEN)
3. **LLM Handling**: LLM prompt instructs to say "document doesn't clearly talk about this" if ambiguous

---

### Q: How does the system avoid wrong answers?

**Answer:**

**Five prevention mechanisms:**

1. **Grounding in Document**: Answers cite exact clause text, page numbers, clause IDs
2. **No Generation Without Matches**: If TF-IDF returns no matches, returns "UNKNOWN"
3. **Strict LLM Prompts**: System instruction forbids inventing clauses
4. **Fallback to Rule-Based**: If LLM API fails, returns `base_answer` (rule-based)
5. **Transparency**: Each answer shows `risk_score`, `reasons`, and `triggered_rules` (users can verify)

---

## 9. Innovation & Product Thinking

### Q: Why is this not a chatbot?

**Answer:**

**Four key differences:**

1. **Document-Specific**: Answers grounded in uploaded contract (not general knowledge)
2. **Evidence-Based**: Every answer cites exact clause IDs and page numbers
3. **Risk Scoring**: Rule-based severity flags (GREEN/YELLOW/RED) based on India-specific legal norms
4. **Structured Workflow**: Upload → Parse → Analyze → Query (not free-form conversation)

**Differentiation**: Combines RAG (document retrieval) + rule-based risk analysis + optional LLM simplification.

---

### Q: What differentiates it from existing tools?

**Answer:**

**Four unique features:**

1. **India-Specific Rules**: `legal_kb.json` based on Model Tenancy Act, RBI guidelines (not generic)
2. **Hybrid Approach**: Rule-based accuracy + AI accessibility (not pure LLM)
3. **Transparency**: Shows which rules triggered, risk scores, exact citations
4. **Privacy-First**: Temporary storage, job-based isolation (though delete endpoint not implemented)

---

### Q: How is this scalable?

**Answer:**

**Four scalability features:**

1. **Cloud Run Auto-Scaling**: Handles traffic spikes automatically
2. **Stateless Design**: Each request is independent; no shared state (except MongoDB for history)
3. **TF-IDF Efficiency**: Lightweight indexing (max 20K features); fast cosine similarity
4. **Optional LLM**: Core pipeline works without LLM; Gemini only for enhancement

**Limitations for Scale:**
- Local filesystem storage (not persistent; would need GCS for production)
- MongoDB connection not required (graceful degradation, but history lost if DB unavailable)

---

## 10. Future Scope

### Q: What will you add next?

**Answer:**

**From README (Future Work section):**

1. **Wider Contract Types**: Employment, sales agreements (expand `legal_kb.json`)
2. **Multilingual Support**: Hindi and other Indian languages
3. **Enhanced UI/UX**: Richer UX, better mobile responsiveness
4. **Advanced NLP Models**: More nuanced clause understanding
5. **User Authentication**: Full user management features

---

### Q: What did you intentionally not include and why?

**Answer:**

**Six intentional omissions:**

1. **Document AI OCR** (mentioned in README but not implemented):
   - **Reason**: MVP uses PyPDF2 for text-based PDFs; OCR adds cost/complexity
   - **Current**: Works for text-based PDFs only

2. **Persistent Cloud Storage** (GCS mentioned but not implemented):
   - **Reason**: MVP uses ephemeral storage for simplicity; production would need GCS
   - **Current**: Files lost on container restart

3. **Delete Endpoint** (mentioned in README but not implemented):
   - **Reason**: Privacy feature planned but not prioritized for MVP
   - **Current**: Manual cleanup or container restart

4. **PDF Export of Reports**:
   - **Reason**: JSON responses sufficient for MVP; PDF export adds complexity
   - **Current**: Only JSON data available

5. **Multi-Document Support**:
   - **Reason**: MVP focuses on single-document analysis; batch processing adds complexity
   - **Current**: One document at a time

6. **Unit Tests** (only integration tests exist):
   - **Reason**: Integration tests validate end-to-end flow; unit tests would add coverage but not critical for MVP

---

## Summary

**ClauseClear** is a hybrid rule-based + AI system for legal document analysis, deployed on Cloud Run via Jenkins. Core functionality is deterministic (rules + TF-IDF); LLM only for simplification. Privacy relies on temporary storage (delete endpoint not implemented). Testing is integration-based. Scalable via Cloud Run, but storage is ephemeral (GCS not implemented).

**Key Strengths:**
- India-specific legal rules
- Transparent risk scoring
- Evidence-based answers
- Cost-efficient (optional LLM)

**Key Limitations:**
- Ephemeral storage
- No delete endpoint
- English only
- Rental/loan contracts only

---

*This document is based on actual codebase analysis. All answers reflect what is implemented, not what is planned.*



# System Diagrams

This document provides visual explanations of the ClauseClear system's key workflows and architecture using Mermaid diagrams.

## Simple App Workflow (for non-technical users)

This diagram shows what happens when a user uploads a rental agreement PDF and asks questions about it.

```mermaid
flowchart LR
    U["User uploads PDF & asks question"] --> F["Web App Frontend (Ask the AI Lawyer)"]
    F --> B["Backend API (FastAPI)"]

    B --> UP["1. Store file in uploads/"]
    B --> PP["2. Read PDF & split into clauses"]
    B --> IDX["3. Build search index (TF-IDF)"]
    B --> SEV["4. Check each clause with rule-based risk engine"]
    B --> LLM["5. Ask Gemini to explain in simple language"]

    SEV --> LLM
    IDX --> LLM

    LLM --> A["Answer shown to user (simple 8th-grade English)"]
```

## How the Code Goes Live (Jenkins + Cloud Run)

This diagram shows how our code goes from GitHub → Jenkins → Google Cloud Run.

```mermaid
flowchart LR
    DEV["Developer pushes code to GitHub"] --> JEN["Jenkins CI/CD server"]

    JEN --> BLD["Build Docker image (backend + app)"]
    BLD --> AR["Push image to Artifact Registry"]
    AR --> CR["Deploy image to Cloud Run service"]

    CR --> USR["Users open website and use the app"]
```

## End-to-End Flow (User → Backend → LLM → Result)

This diagram shows the complete flow from user upload through PDF parsing, clause extraction, indexing, querying, and LLM-powered explanation.

```mermaid
flowchart TD
    User[User uploads PDF] --> Upload[POST /files/upload]
    Upload --> Storage[storage/uploads/job_id/]
    Storage --> Parse[POST /process/job_id/parse]
    Parse --> PyPDF2[PyPDF2 extracts text]
    PyPDF2 --> Clauses[Split into clauses]
    Clauses --> ClausesJSON[clauses.json saved]
    ClausesJSON --> Index[POST /rag/job_id/index]
    Index --> TFIDF[TF-IDF vectorization]
    TFIDF --> Embeddings[embeddings/job_id.pkl]
    Embeddings --> Query[POST /query/job_id]
    Query --> Search[TF-IDF cosine similarity]
    Search --> Severity[Severity engine + legal_kb.json]
    Severity --> RiskScore[Risk level + score + reasons]
    RiskScore --> BaseAnswer[base_answer generated]
    BaseAnswer --> LLMQuery[POST /query_llm/job_id]
    LLMQuery --> Gemini[Gemini API call]
    Gemini --> SimpleAnswer[answer_llm: simple explanation]
    SimpleAnswer --> UserResult[User receives result]
```

The flow starts with PDF upload, extracts text using PyPDF2, splits into clauses, builds a TF-IDF index for semantic search, scores clauses for risk using India-specific rules, and optionally uses Gemini to rewrite explanations in simple language.

## Severity Engine Workflow

This diagram details how the rule-based severity engine analyzes clauses against India-specific rules to assign risk levels.

```mermaid
flowchart TD
    Input[Input: Clause Text] --> LoadKB[Load legal_kb.json]
    LoadKB --> Rules[Severity Rules + Thresholds]
    Rules --> Match1[Match: lockin_gt_notice?]
    Rules --> Match2[Match: very_large_deposit?]
    Rules --> Match3[Match: large_deposit?]
    Rules --> Match4[Match: unilateral_termination?]
    Rules --> Match5[Match: high_late_fee?]
    Match1 --> Weight1[Weight: 0.6]
    Match2 --> Weight2[Weight: 0.7]
    Match3 --> Weight3[Weight: 0.4]
    Match4 --> Weight4[Weight: 0.8]
    Match5 --> Weight5[Weight: 0.35]
    Weight1 --> Compute[Compute risk_score]
    Weight2 --> Compute
    Weight3 --> Compute
    Weight4 --> Compute
    Weight5 --> Compute
    Compute --> Threshold{Check Thresholds}
    Threshold -->|score < 0.3| Green[GREEN: Low Risk]
    Threshold -->|0.3 <= score < 0.6| Yellow[YELLOW: Medium Risk]
    Threshold -->|score >= 0.6| Red[RED: High Risk]
    Green --> Output[Output: risk_level + risk_score + reasons]
    Yellow --> Output
    Red --> Output
```

The severity engine loads rules from legal_kb.json, matches patterns in clause text (security deposits, lock-in periods, termination clauses, etc.), applies weighted scoring, and maps the final score to GREEN/YELLOW/RED risk levels with explanatory reasons.

## CI/CD Pipeline (Jenkins → Artifact Registry → Cloud Run)

This diagram shows the automated deployment pipeline from code push to Cloud Run service deployment.

```mermaid
flowchart LR
    Developer[Developer] -->|Push to GitHub| GitHub[GitHub Repository]
    GitHub -->|Webhook/Manual Trigger| Jenkins[Jenkins Pipeline]
    Jenkins --> Stage1[Stage 1: Checkout]
    Stage1 --> Stage2[Stage 2: Docker Build]
    Stage2 --> Stage3[Stage 3: Push to Artifact Registry]
    Stage3 --> Auth[GCP Service Account Auth]
    Auth --> ArtifactReg[us-central1-docker.pkg.dev/productdesigndev/clauseclear/clauseclear-backend]
    ArtifactReg --> Stage4[Stage 4: Deploy to Cloud Run]
    Stage4 --> EnvVars[Inject Env Vars: GEMINI_API_KEY, MONGO_URI, GEMINI_MODEL_NAME]
    EnvVars --> CloudRun[Cloud Run Service: clauseclear-backend]
    CloudRun --> Users[Users access service]
```

The Jenkins pipeline checks out code, builds a Docker image, pushes it to GCP Artifact Registry, and deploys to Cloud Run with environment variables injected from Jenkins credentials. The service is then live and accessible to users.

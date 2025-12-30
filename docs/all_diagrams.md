# ClauseClear – All System Diagrams (For Easy Sharing)

## 1. Simple Application Workflow (Easy for Everyone)

This diagram shows what happens when a user uploads a rental agreement PDF and asks questions about it.

```mermaid
flowchart LR
    U["User uploads PDF and asks a question"] --> F["Frontend Web App"]
    F --> API["Backend API (FastAPI)"]

    API --> STORE["1. Save file"]
    API --> PARSE["2. Extract clauses from PDF"]
    API --> INDEX["3. Create search index (TF-IDF)"]
    API --> RISK["4. Apply rule-based risk scoring"]
    API --> LLM["5. Ask Gemini for simple explanation"]

    RISK --> LLM
    INDEX --> LLM

    LLM --> OUT["Final answer shown to the user (simple 8th-grade English)"]
```

## 2. Backend Architecture (Technical Overview)

This diagram shows the technical components and how they interact.

```mermaid
flowchart TB
    FE["Frontend (HTML/CSS/JS)"] --> API["FastAPI Backend"]

    API --> UP["File Uploads"]
    API --> PDF["PDF Parser"]
    PDF --> CLAUSE["Clause Extractor"]

    CLAUSE --> TFIDF["TF-IDF Vector Index"]
    CLAUSE --> RISK["Severity Engine (Rule-based detector)"]

    API --> LLM["Gemini LLM Explainer"]
    TFIDF --> LLM
    RISK --> LLM

    LLM --> RESP["Response returned to user"]
```

## 3. CI/CD Pipeline (Jenkins → Artifact Registry → Cloud Run)

This diagram shows how code changes are automatically deployed to production.

```mermaid
flowchart LR
    DEV["Developer pushes code to GitHub"] --> JEN["Jenkins Pipeline"]

    JEN --> BUILD["Build Docker Image"]
    BUILD --> PUSH["Push to Artifact Registry"]

    PUSH --> DEPLOY["Deploy to Cloud Run"]

    DEPLOY --> USERS["Users access the live application"]
```

## 4. Severity Engine Workflow

This diagram shows how the system analyzes clauses to assign risk levels (GREEN/YELLOW/RED).

```mermaid
flowchart TB
    C[Extracted Clause] --> CLEAN[Text Cleaning]
    CLEAN --> MATCH[Rule Matching]
    MATCH --> SCORE[Assign Risk Score]
    SCORE --> LABEL["Label as GREEN / YELLOW / RED"]
```

## 5. LLM Explanation Layer (Gemini)

This sequence diagram shows how the system uses Gemini to convert technical explanations into simple language.

```mermaid
sequenceDiagram
    participant API as Backend API
    participant LLM as Gemini LLM
    participant USER as User

    USER->>API: Ask a question
    API->>API: Retrieve relevant clauses + risk info
    API->>LLM: Send simplified prompt package
    LLM->>API: Return 8th-grade explanation
    API->>USER: Final simplified answer
```


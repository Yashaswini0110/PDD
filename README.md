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

## Getting Started for Teammates

This guide provides a step-by-step process to set up, run, and test the ClauseClear Mini Backend.

### Prerequisites

- Python 3.11 installed.
- Git installed.
- Familiarity with PowerShell (for Windows users) or Bash (for Linux/macOS users).

### 1. Clone the Repository

First, clone the GitHub repository to your local machine:

```bash
git clone https://github.com/Yashaswini0110/PDD.git
cd PDD/clauseclear-mini-backend
```

### 2. Set up a Virtual Environment

It's highly recommended to use a virtual environment to manage dependencies:

```bash
# Create a virtual environment
python -m venv .venv

# Activate the virtual environment (Windows PowerShell)
.venv\Scripts\activate

# Activate the virtual environment (Linux/macOS Bash)
# source .venv/bin/activate
```

### 3. Install Dependencies

With your virtual environment activated, install the required Python packages:

```bash
pip install -r requirements.txt
```

### 4. Run the FastAPI Server

Open a **new terminal** and navigate to the `clauseclear-mini-backend` directory. Run the server using Uvicorn:

```powershell
# In the clauseclear-mini-backend directory
python -m uvicorn app:app --host 127.0.0.1 --port 5055 --reload
```

**Leave this terminal running.** It will continuously display server logs.

### 5. Create a Dummy PDF (for testing)

Open **another new terminal** and navigate to the `clauseclear-mini-backend` directory. Create a PDF with sample text:

```powershell
# In the clauseclear-mini-backend directory
python create_dummy_pdf_with_text.py
```

Expected output: `Created PDF with text at ...\dummy_with_text.pdf`

### 6. Upload a Document

In the same terminal where you created the dummy PDF, upload the document to the backend. This will return a `job_id` which is crucial for subsequent steps.

```powershell
# In the clauseclear-mini-backend directory
python upload_pdf.py dummy_with_text.pdf
```

Expected output:

```json
Upload successful: {"job_id": "...", "filename": "dummy_with_text.pdf", "size_bytes": ..., "path": "..."}
Job ID: <YOUR_JOB_ID_HERE>
```

**Note down the `job_id` from the output.**

### 7. Parse the Document

Use the `job_id` from the previous step to parse the document and extract clauses.

```powershell
# Replace <YOUR_JOB_ID_HERE> with the actual job_id
$job_id = "<YOUR_JOB_ID_HERE>"
Invoke-RestMethod -Uri "http://127.0.0.1:5055/process/$job_id/parse" -Method Post
```

Expected output:

```
job_id                               pages clauses_count
------                               ----- -------------
<YOUR_JOB_ID_HERE>                     1             7
```

### 8. Build the TF-IDF Index

Build the search index for the parsed clauses.

```powershell
# Replace <YOUR_JOB_ID_HERE> with the actual job_id
$job_id = "<YOUR_JOB_ID_HERE>"
Invoke-RestMethod -Uri "http://127.0.0.1:5055/rag/$job_id/index" -Method Post
```

Expected output:

```
job_id                               clauses shape
------                               ------- -----
<YOUR_JOB_ID_HERE>                       7 @{rows=7; cols=...}
```

### 9. Query the Document

Perform a unified query to get relevant clauses, risk analysis, and a friendly answer.

```powershell
# Replace <YOUR_JOB_ID_HERE> with the actual job_id
$job_id = "<YOUR_JOB_ID_HERE>"
$body = @{
    query = "security deposit" # You can change this query
    top_k = 3
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5055/query/$job_id" -Method Post -ContentType "application/json" -Body $body
```

Expected output (example, actual content may vary):

```json
{
  "job_id": "<YOUR_JOB_ID_HERE>",
  "query": "security deposit",
  "top_k": 3,
  "answer": "I found clause P01_C004 on page 1 related to your query 'security deposit'. Risk level: GREEN (score 0.1). Reason: Security deposit is mentioned but amount unclear..",
  "matches": [
    {
      "id": "P01_C004",
      "page": 1,
      "text": "Security deposit is required for all new tenants",
      "score": 0.4567831782555151,
      "risk_score": 0.1,
      "risk_level": "GREEN",
      "triggered_rules": [
        "large_deposit_unsure"
      ],
      "reasons": [
        "Security deposit is mentioned but amount unclear."
      ]
    },
    ...
  ]
}
```

### 10. Test UNKNOWN Fallback

Test a query that should not find any relevant clauses.

```powershell
# Replace <YOUR_JOB_ID_HERE> with the actual job_id
$job_id = "<YOUR_JOB_ID_HERE>"
$body = @{
    query = "xyzzy plugh" # An obscure query
    top_k = 3
} | ConvertTo-Json
Invoke-RestMethod -Uri "http://127.0.0.1:5055/query/$job_id" -Method Post -ContentType "application/json" -Body $body
```

Expected output:

```json
{
  "job_id": "<YOUR_JOB_ID_HERE>",
  "query": "xyzzy plugh",
  "answer": "UNKNOWN – this clause does not exist clearly in your document.",
  "matches": []
}
```

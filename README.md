# ClauseClear – AI-Powered Legal Clause Simplifier

## Problem

Many individuals in India enter into rental agreements and loan contracts without fully understanding critical clauses such as lock-in periods, notice requirements, high security deposits, hidden fees, or arbitration clauses located in inconvenient jurisdictions. This lack of clarity can lead to unforeseen financial burdens and legal complications.

## Solution

ClauseClear is a web application designed to demystify legal contracts. Users can upload a contract PDF, and the system will provide clause-by-clause summaries in plain English, flag clauses with Green, Yellow, or Red severity indicators based on India-specific rules, and offer a Q&A feature with evidence from the document. A downloadable report with a "Not legal advice" banner is available, and user privacy is ensured through temporary storage and a "Delete Now" option.

## Key Features

*   Clause-by-clause summaries in plain English
*   Severity scoring (Green/Yellow/Red) with India-specific rules
*   Q&A with exact clause citations from the document
*   Exportable report (PDF/HTML) for easy review
*   Privacy features: temporary storage and a user-triggered delete-now endpoint

## Architecture Overview

The backend is a FastAPI application deployed on Google Cloud Run. It leverages Google Cloud Document AI for parsing PDF documents, Vertex AI Gemini for generating clause summaries and powering the Q&A feature, and a custom Severity Engine with rule-based logic. Temporarily stores documents in Google Cloud Storage. The frontend is a single-page application built with HTML, CSS, and JavaScript, providing an intuitive user interface for document uploads and result visualization.

### System Architecture

```mermaid
flowchart LR
    User -->|Upload PDF| Frontend
    Frontend -->|Send file| Backend[FastAPI App]
    Backend -->|Store temporarily| GCS[(Cloud Storage)]
    Backend -->|Parse| DocAI[(Document AI)]
    Backend -->|Summaries + Q&A| Gemini[(Vertex AI Gemini)]
    Backend --> SeverityEngine[(Severity Rules)]
    Backend -->|JSON response| Frontend
    Frontend -->|Show flags & answers| User
    Backend -->|Delete or auto-expire| GCS
```

## Diagrams

For more detailed architectural and workflow diagrams, please refer to the [System Diagrams](PDD/docs/diagrams.md) document.

## Tech Stack

*   **Backend:** FastAPI, Python, Google Cloud Run, Google Cloud Document AI, Vertex AI Gemini, Google Cloud Storage, `scikit-learn` (for TF-IDF).
*   **Frontend:** HTML, CSS, JavaScript (static files served by FastAPI).
*   **CI/CD:** Jenkins, Docker, Google Cloud Artifact Registry (potential for GitHub Actions integration).

## Getting Started (Local Development)

### Prerequisites

*   Python 3.11 installed
*   Node.js (for frontend dependencies if developing the static assets locally, though not strictly required for backend only)
*   Git installed

### Backend Setup

1.  **Clone the Repository:**
    ```bash
    git clone https://github.com/Yashaswini0110/PDD.git
    cd PDD
    ```
2.  **Set up a Virtual Environment:**
    ```bash
    python -m venv .venv
    # Activate for Windows PowerShell:
    .venv\Scripts\activate
    # Activate for Linux/macOS Bash:
    # source .venv/bin/activate
    ```
3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```
4.  **Set Environment Variables:**
    Create a `.env` file in the `PDD/` directory (if it doesn't exist) and add necessary environment variables, such as API keys or configuration settings for Google Cloud services (e.g., `GOOGLE_APPLICATION_CREDENTIALS`).
    ```
    # Example (adjust as needed for your specific setup)
    # GOOGLE_APPLICATION_CREDENTIALS=/path/to/your/service-account-key.json
    ```
5.  **Run the FastAPI Server:**
    ```bash
    python -m uvicorn app:app --host 0.0.0.0 --port 5055 --reload
    ```
    The API will be accessible at `http://localhost:5055`.

### Frontend Setup

The frontend consists of static HTML, CSS, and JavaScript files located in `PDD/static/`. These are served directly by the FastAPI backend. No separate build step is required for basic local development.

To access the frontend, once the backend is running, navigate your browser to `http://localhost:5055/static/index.html`.

## Deployment (Cloud Run + Jenkins)

This project is designed for deployment on Google Cloud Run with a Jenkins-driven CI/CD pipeline.

1.  **Docker Image Build:** A Docker image is built from the `PDD/Dockerfile` within this repository.
2.  **Image Push:** The built Docker image is pushed to Google Cloud Artifact Registry.
3.  **Cloud Run Deployment:** A Google Cloud Run service (e.g., `clauseclear-backend`) is deployed using the image from Artifact Registry.
4.  **Jenkins Pipeline:** The Jenkins pipeline is triggered on code pushes to the repository, automating the steps: `checkout` → `docker build` → `push to Artifact Registry` → `deploy to Cloud Run`.

## Limitations & Future Work

### Current Limitations

*   **Contract Types:** Currently optimized for rental and loan contracts.
*   **Language Support:** English language contracts only.
*   **UI/UX:** Basic user interface.

### Future Work

*   Support for a wider range of contract types (e.g., employment, sales agreements).
*   Multilingual support for contract analysis.
*   Enhanced UI/UX for a more intuitive user experience.
*   Integration of advanced NLP models for more nuanced clause understanding.
*   User authentication and management features.

## Disclaimer

This tool does not provide legal advice. Always consult a qualified lawyer for legal decisions.

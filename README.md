# DOCSENSE: Your AI Assistant for Rental & Loan Agreements

DOCSENSE is a powerful, AI-powered web application designed to help users understand complex legal documents. It uses a sophisticated **Hybrid Retrieval-Augmented Generation (RAG)** system to analyze contracts, provide simple-English summaries, identify potential risks, and answer user questions with evidence-backed responses.

The application is built with a modern tech stack, featuring a Python/FastAPI backend and a React/TypeScript frontend.

## Key Features

*   **Multi-File Support:** Analyze `.pdf`, `.docx`, and `.txt` documents.
*   **Hybrid Analysis Engine:** Combines fast, rule-based checks for common risks with deep AI analysis for complex clauses.
*   **Legally-Aware Context:** Cross-references user documents against a custom legal knowledge base that you provide.
*   **Overall Safety Score:** Provides an intuitive, at-a-glance score from 0-100 to gauge document risk.
*   **Evidence-Backed Q&A:** Ask questions in plain English and get AI-generated answers with a direct link to the source clause.
*   **Professional Reports:** Export a clean, detailed HTML summary of the analysis.

## Architecture Overview

The application uses a decoupled frontend/backend architecture.

*   **Frontend:** A single-page application built with **React** and **TypeScript**, using **Vite** for a fast development experience. It communicates with the backend via a REST API.
*   **Backend:** A powerful API built with **Python** and **FastAPI**. Its core is the Hybrid Analysis Engine, which uses the **Cohere API** for state-of-the-art embedding, reranking, and language generation.

The analysis logic is designed to be fast and efficient, using simple rules to catch obvious issues and batching the remaining clauses for AI analysis to stay within free-tier API limits.

## Project Structure

```
RAG/
├── backend/
│   ├── app/                # Core application logic
│   │   ├── ai_core.py      # Manages all Cohere API interactions
│   │   ├── parser.py       # Extracts text from uploaded files
│   │   ├── qa.py           # Handles the Q&A logic
│   │   └── severity.py     # The Hybrid Analysis Engine
│   ├── legal_kb/           # Place your legal knowledge base PDFs here
│   ├── templates/
│   │   └── report.html     # Jinja2 template for the exported report
│   ├── build_kb.py         # Script to build the AI's knowledge base
│   ├── evaluate.py         # Script to test the AI's accuracy
│   ├── main.py             # FastAPI application entry point
│   └── requirements.txt    # Python dependencies
└── frontend/
    ├── src/
    │   ├── App.tsx         # Main React component and UI
    │   └── App.css         # Styles for the application
    └── package.json        # Frontend dependencies
```

## Setup and Running the Application

Follow these steps to get the application running on your local machine.

### Prerequisites

*   **Python** (3.9+)
*   **Node.js** (v18+) and **npm**
*   **Git**

### 1. Clone the Repository

Clone this project to your local machine.

### 2. Set Up the Backend

1.  **Navigate to the Backend Directory:**
    ```bash
    cd RAG/backend
    ```

2.  **Create and Activate a Virtual Environment:**
    ```bash
    python -m venv venv
    .\venv\Scripts\activate
    ```

3.  **Install Python Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Your API Key:**
    *   Rename the `.env.example` file to `.env`.
    *   Open the `.env` file and add your Cohere API key and a new API key for the application:
        ```
        COHERE_API_KEY="YOUR_COHERE_API_KEY_HERE"
        API_KEY="YOUR_APPLICATION_API_KEY_HERE"
        ```

5.  **Populate and Build the Knowledge Base:**
    *   Place your legal PDF documents (e.g., `The_Indian_Contract_Act_1872.pdf`) inside the `legal_kb/` directory.
    *   Run the build script. This will read your PDFs, embed them, and create the `legal_kb.json` file. This may take a few minutes depending on the size of your documents.
        ```bash
        python build_kb.py
        ```

6.  **Run the Backend Server:**
    ```bash
    uvicorn main:app --reload
    ```
    The backend will be running at `http://127.0.0.1:8000`.

### 3. Set Up the Frontend

1.  **Navigate to the Frontend Directory:**
    *   Open a **new terminal**.
    ```bash
    cd RAG/backend/frontend
    ```

2.  **Install Node.js Dependencies:**
    ```bash
    npm install
    ```

3.  **Set Your API Key:**
    *   Create a new file named `.env` in the `frontend` directory.
    *   Open the `.env` file and add your application API key. This must match the `API_KEY` in the backend's `.env` file.
        ```
        VITE_API_KEY="YOUR_APPLICATION_API_KEY_HERE"
        ```

4.  **Run the Frontend Server:**
    ```bash
    npm run dev
    ```
    The frontend will be running at `http://localhost:5173`.

### 4. Use the Application

Open your web browser and navigate to `http://localhost:5173` to start analyzing documents.
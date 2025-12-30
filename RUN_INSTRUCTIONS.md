# How to Run PDD (ClauseClear Mini)

## Prerequisites

- **Python 3.11+** installed on your machine.
- **Docker** (Optional, if you prefer running via Docker).

## Option 1: Running with Docker (Recommended)

1.  **Build the image:**

    ```bash
    docker build -t pdd-app .
    ```

2.  **Run the container:**

    ```bash
    docker run -p 5055:5055 pdd-app
    ```

3.  Access the application at [http://localhost:5055](http://localhost:5055).

## Option 2: Running Locally (Python)

1.  **Create a virtual environment:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the application:**

    ```bash
    uvicorn app:app --host 0.0.0.0 --port 5055 --reload
    ```

4.  Access the application at [http://localhost:5055](http://localhost:5055).

## Configuration

The project uses a `.env` file for configuration (MongoDB, Firebase, API Keys). This file has been included in the package.

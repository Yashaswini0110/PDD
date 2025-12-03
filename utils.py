from pathlib import Path
import re
import os
from dotenv import load_dotenv

load_dotenv()

def safe_filename(filename: str) -> str:
    """Sanitizes a filename to contain only alphanumeric, dashes, and dots."""
    filename = re.sub(r'[^\w\s.-]', '', filename)
    filename = re.sub(r'\s+', '_', filename)
    return filename

def ensure_dirs():
    """Ensures that necessary directories exist."""
    Path("storage/uploads").mkdir(parents=True, exist_ok=True)
    Path("embeddings").mkdir(parents=True, exist_ok=True)
    Path("logs").mkdir(parents=True, exist_ok=True)

def get_gcp_config():
    """Get GCP configuration from environment variables."""
    return {
        "project_id": os.getenv("GCP_PROJECT_ID"),
        "location": os.getenv("GCP_LOCATION", "us-central1"),
        "model_name": os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),
    }
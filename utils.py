from pathlib import Path
import re

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
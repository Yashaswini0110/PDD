import json
from pathlib import Path

def load_kb():
    current_file_dir = Path(__file__).parent
    kb_path = current_file_dir.parent / "knowledge" / "legal_kb.json" # Go up one level (from services to PDD), then into knowledge
    if not kb_path.exists():
        raise FileNotFoundError("legal_kb.json not found")
    return json.loads(kb_path.read_text(encoding="utf-8"))
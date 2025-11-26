import json
from pathlib import Path

def load_kb():
    kb_path = Path("knowledge") / "legal_kb.json"
    if not kb_path.exists():
        raise FileNotFoundError("legal_kb.json not found")
    return json.loads(kb_path.read_text(encoding="utf-8"))
import re

def split_into_clauses(text: str) -> list[str]:
    if not text.strip():
        return []
    # split on full stops, semicolons, or line breaks (simple heuristic)
    parts = re.split(r'[.;\n]\s+', text)
    return [p.strip() for p in parts if len(p.strip()) > 10]
from typing import List, Dict, Any
from pypdf import PdfReader
import re


import docx

def extract_text_from_file(file_path: str) -> str:
	"""
	Extracts text from a file based on its extension (.pdf, .docx, .txt).
	"""
	if file_path.lower().endswith(".pdf"):
		reader = PdfReader(file_path)
		texts: List[str] = []
		for page in reader.pages:
			texts.append(page.extract_text() or "")
		return "\n\n".join(texts)
	
	elif file_path.lower().endswith(".docx"):
		doc = docx.Document(file_path)
		texts: List[str] = []
		for para in doc.paragraphs:
			texts.append(para.text)
		return "\n\n".join(texts)

	elif file_path.lower().endswith(".txt"):
		with open(file_path, "r", encoding="utf-8") as f:
			return f.read()
			
	else:
		raise ValueError(f"Unsupported file type: {file_path}")


CLAUSE_SPLIT_RE = re.compile(r"\n\s*\n+|(?<=\.)\s{2,}")


def split_into_clauses(text: str) -> List[Dict[str, Any]]:
	clauses: List[Dict[str, Any]] = []
	start = 0
	for part in CLAUSE_SPLIT_RE.split(text):
		part = part.strip()
		if not part:
			continue
		idx = text.find(part, start)
		if idx == -1:
			idx = start
		end = idx + len(part)
		clauses.append({
			"id": len(clauses),
			"text": part,
			"start": idx,
			"end": end,
		})
		start = end
	return clauses


def parse_file_to_clauses(file_path: str) -> Dict[str, Any]:
	full_text = extract_text_from_file(file_path)
	clauses = split_into_clauses(full_text)
	return {"text": full_text, "clauses": clauses}

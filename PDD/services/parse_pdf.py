from pathlib import Path
from PyPDF2 import PdfReader

def extract_text_from_pdf(pdf_path: Path) -> list[str]:
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        pages.append(text)
    return pages
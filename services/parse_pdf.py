from pathlib import Path
import re
from PyPDF2 import PdfReader
from loguru import logger

def extract_text_from_pdf(pdf_path: Path) -> list[str]:
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)
    reader = PdfReader(str(pdf_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        # DEBUGGING: Track extraction quality
        logger.info(f"Page {i} extracted text length: {len(text)}")
        
        # Log if key terms are found
        text_lower = text.lower()
        if "security deposit" in text_lower or "advance" in text_lower:
            logger.info(f"Page {i} contains deposit/advance info - sample: {text[:500]}")
        if "monthly rent" in text_lower or "rent" in text_lower:
            # Try to find rent amount in the text
            rent_match = re.search(r'rent\s+of\s+Rs\.?\s*(\d+(?:,\d+)*)', text, re.IGNORECASE)
            if rent_match:
                logger.info(f"Page {i} contains rent amount: Rs. {rent_match.group(1)}")
            else:
                logger.info(f"Page {i} mentions rent but amount not clearly found - sample: {text[:500]}")
        
        pages.append(text)
    return pages
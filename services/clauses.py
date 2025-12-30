import re
from loguru import logger

def split_into_clauses(text: str) -> list[str]:
    if not text.strip():
        return []
    
    # Normalize whitespace first (replace multiple spaces/newlines with single space)
    text = re.sub(r'\s+', ' ', text)
    
    # Better splitting that preserves amounts and abbreviations
    # Strategy: Split on sentence boundaries (period + space + capital letter)
    # BUT avoid splitting:
    # - Periods in amounts (Rs. 14500, $1.50)
    # - Periods in abbreviations (e.g., i.e., etc., Dr., Mr.)
    # - Periods after single letters (A. B. C.)
    
    # Pattern: period, space, then capital letter starting a new sentence
    # Exclude if period is preceded by:
    # - Single letter (A. B.)
    # - Common abbreviation (Rs., Dr., Mr., etc.)
    # - Number (1.5, 14500.00)
    
    # First, protect common patterns
    # Replace "Rs. " temporarily to avoid splitting
    text = re.sub(r'Rs\.\s+', 'Rs_AMOUNT_', text)
    
    # Split on sentence boundaries: period + space + capital letter
    # But not if it's a single letter abbreviation
    parts = re.split(r'\.\s+(?=[A-Z][a-z])', text)
    
    # Restore the protected patterns
    parts = [p.replace('Rs_AMOUNT_', 'Rs. ') for p in parts]
    
    # Also split on semicolons
    all_parts = []
    for part in parts:
        semicolon_parts = re.split(r';\s+', part)
        all_parts.extend(semicolon_parts)
    
    # Filter out very short fragments and clean up
    clauses = []
    for p in all_parts:
        cleaned = p.strip()
        # Remove leading paragraph numbers (like "1. ", "Para 1. ", "Para. 1 ")
        cleaned = re.sub(r'^(?:Para(?:graph)?\s*\d+|(?:\d+|[A-Z])\s*\.)\s*', '', cleaned, flags=re.IGNORECASE)
        if len(cleaned) > 10:
            clauses.append(cleaned)
            # Debug: Log clauses containing key terms
            if any(term in cleaned.lower() for term in ['rent', 'deposit', 'advance', 'monthly']):
                logger.debug(f"Clause created with key term: {cleaned[:100]}...")
    
    return clauses
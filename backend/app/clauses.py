from typing import List, Dict, Any
import re

def generate_simple_summary(clause_text: str) -> str:
    """
    Generate a simple English summary of a legal clause.
    In a real implementation, this would use Gemini 1.5 Flash.
    For now, we'll use a simple rule-based approach.
    """
    # Simplified summary generation
    text = clause_text.lower()
    
    if "lock-in" in text or "lock in" in text:
        return "This clause restricts you from leaving early without penalties."
    
    if "deposit" in text and "rent" in text:
        return "This clause explains how much security deposit you need to pay."
    
    if "terminate" in text:
        return "This clause explains how the agreement can be ended."
    
    if "processing fee" in text:
        return "This clause describes fees for processing your application."
    
    if "late fee" in text or "penal interest" in text:
        return "This clause explains penalties for late payments."
    
    if "arbitration" in text:
        return "This clause explains how disputes will be resolved."
    
    # Default summary for other clauses
    return "This clause contains legal terms about your agreement."

def process_clauses(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process clauses to add summaries in simple English.
    """
    for clause in clauses:
        clause["summary"] = generate_simple_summary(clause["text"])
    
    return clauses
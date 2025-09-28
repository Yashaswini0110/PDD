import json
import re
from typing import List, Dict, Any
from .ai_core import co

# --- Configuration ---
TRIVIAL_WORD_COUNT = 15
BATCH_SIZE = 15

# --- Rule-Based Checks ---

def apply_rule_based_checks(clauses: List[Dict[str, Any]]) -> tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Applies a set of simple, fast regex rules to catch common risks.
    Returns a tuple of (found_flags, remaining_clauses).
    """
    flags = []
    remaining_clauses = []
    
    rules = [
        {
            "name": "High Security Deposit",
            "pattern": r"security deposit of (\d+) month",
            "severity": "High",
            "negotiation_hint": "In many places, the security deposit is legally capped at 2-3 months' rent. Consider negotiating this down."
        },
        {
            "name": "Unfair Lock-in vs. Notice Period",
            "pattern": r"lock-in period of (\d+) months and a notice period of (\d+) month",
            "severity": "High",
            "negotiation_hint": "A long lock-in period with a short notice period can be restrictive. Try to align these more closely."
        },
        {
            "name": "High Late Fee",
            "pattern": r"late fee of (\d+)%",
            "severity": "Medium",
            "negotiation_hint": "A high percentage-based late fee can be costly. Suggest a smaller, fixed fee instead."
        }
    ]

    for clause in clauses:
        matched = False
        for rule in rules:
            match = re.search(rule["pattern"], clause["text"], re.IGNORECASE)
            if match:
                flags.append({
                    "clause_id": clause["id"],
                    "evidence": clause["text"],
                    "reason": f"Rule-based flag: {rule['name']}",
                    "severity": rule["severity"],
                    "negotiation_hint": rule["negotiation_hint"]
                })
                matched = True
                break
        if not matched:
            remaining_clauses.append(clause)
            
    return flags, remaining_clauses

# --- AI-Powered Batch Analysis ---

def analyze_clauses_in_batch(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Sends a batch of clauses to the Cohere API for analysis and expects a JSON array back.
    """
    if not clauses:
        return []

    # Create a numbered list of clauses for the prompt
    clauses_text = "\n".join([f'{c["id"]}. {c["text"]}' for c in clauses])
    
    prompt = f"""
    You are a helpful assistant who explains complex legal documents in simple, plain English.
    Your goal is to make the content understandable to a 14-year-old.

    Analyze the following numbered list of contract clauses. For each clause, identify any potential risks, unfair terms, or important points.

    You MUST respond with a valid JSON array of objects, where each object has the keys "id" (the original clause number as an integer), "severity" ("Low", "Medium", "High", or "Info"), and "justification" (your simple, plain-English explanation).

    Example Response:
    [
        {{"id": 1, "severity": "Medium", "justification": "This clause says you have to pay for all repairs, which could be expensive."}},
        {{"id": 2, "severity": "Info", "justification": "This just explains the address of the property."}}
    ]

    Here are the clauses to analyze:
    {clauses_text}

    JSON Response:
    """

    try:
        response = co.chat(message=prompt, model="command-r-plus-08-2024")
        cleaned_response = response.text.strip().replace("```json", "").replace("```", "").strip()
        ai_results = json.loads(cleaned_response)
        
        # Map the AI results back to the original clause data
        clause_map = {c["id"]: c for c in clauses}
        final_flags = []
        for result in ai_results:
            clause_id = result.get("id")
            if clause_id in clause_map:
                original_clause = clause_map[clause_id]
                final_flags.append({
                    "clause_id": original_clause["id"],
                    "evidence": original_clause["text"],
                    "reason": result.get("justification", "No justification provided."),
                    "severity": result.get("severity", "Info"),
                    "negotiation_hint": None
                })
        return final_flags

    except (json.JSONDecodeError, Exception) as e:
        print(f"Error processing AI batch: {e}")
        return []

# --- Main Hybrid Function ---

def analyze_clauses_with_hybrid_model(clauses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    The main function that orchestrates the full hybrid analysis pipeline.
    """
    print(f"Analyzing {len(clauses)} clauses with Hybrid Model...")

    # 1. Filter out trivial clauses
    substantive_clauses = [c for c in clauses if len(c["text"].split()) > TRIVIAL_WORD_COUNT]
    
    # 2. Apply fast, rule-based checks
    rule_based_flags, clauses_for_ai = apply_rule_based_checks(substantive_clauses)
    print(f"Found {len(rule_based_flags)} flags with simple rules.")

    # 3. Batch process the remaining clauses with the AI
    ai_flags = []
    for i in range(0, len(clauses_for_ai), BATCH_SIZE):
        batch = clauses_for_ai[i:i + BATCH_SIZE]
        print(f"Sending batch of {len(batch)} clauses to AI...")
        ai_flags.extend(analyze_clauses_in_batch(batch))
        
    # 4. Combine all flags
    all_flags = rule_based_flags + ai_flags
    return sorted(all_flags, key=lambda x: x["clause_id"])

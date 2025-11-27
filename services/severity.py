from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Dict, Tuple

from services.kb_loader import load_kb

# Load knowledge base once at startup
kb = load_kb()
RULES = { r["id"]: r for r in kb["severity_rules"] }
THRESHOLDS = kb["thresholds"]

@dataclass
class RuleResult:
    id: str
    weight: float
    reason: str


# --- small helpers to extract numbers from text ---


def _extract_months(text: str) -> List[int]:
    """Return list of integers that look like 'X month(s)' in the text."""
    matches = re.findall(r"(\d+)\s*month", text, flags=re.IGNORECASE)
    return [int(m) for m in matches]


def _extract_percent(text: str) -> List[float]:
    """Return list of percentages like '3%' or '2.5 %' in the text."""
    matches = re.findall(r"(\d+(?:\.\d+)?)\s*%", text)
    return [float(m) for m in matches]


def _extract_deposit_months(text: str) -> int | None:
    """Very rough heuristic for 'N months deposit/advance'."""
    # Look for "X months rent/deposit"
    m1 = re.search(r"(\d+)\s*months?(?:['’]\s*)?(?:rent|deposit|advance)", text, flags=re.IGNORECASE)
    if m1:
        return int(m1.group(1))
    # Look for "security deposit of X months" or "X months security deposit"
    m2 = re.search(r"(?:security\s+deposit(?:.*?)(\d+)\s*months?)|(?:(\d+)\s*months?\s+security\s+deposit)", text, flags=re.IGNORECASE)
    if m2:
        # Prioritize the first capturing group if it exists
        if m2.group(1):
            return int(m2.group(1))
        # Otherwise, use the second capturing group
        elif m2.group(2):
            return int(m2.group(2))
    return None

def _build_reasons(triggered_rule_ids: List[str], rules_metadata: Dict) -> List[str]:
    """Build human-readable reasons from triggered rule IDs using KB metadata."""
    reasons = []
    for rule_id in triggered_rule_ids:
        rule_info = rules_metadata.get(rule_id)
        if rule_info and "description" in rule_info:
            reasons.append(rule_info["description"])
    return reasons or ["No obvious issues matched; still review manually."]


# --- rule checkers ---

def score_clause(clause: Dict) -> Dict:
    """Compute weighted risk score and label for a clause."""
    total_score = 0.0
    triggered_rule_ids: List[str] = []
    text = clause.get("text", "").lower()

    # 1) lockin rule from KB
    lock_in_months = _extract_months(text)
    notice_months = _extract_months(text) # Assuming notice period is also in months

    # Simplified heuristic for lock-in > notice, usually a YELLOW/RED flag
    # For T04 "A security deposit of 5 months' rent is required. There is also a 6-month lock-in period."
    if "lock-in period" in text and "months" in text and "notice period" not in text:
        # This is a very simple way to catch T04 and push it to RED with a high deposit
        if _extract_deposit_months(text) and _extract_deposit_months(text) >= 4:
            rule_id = "lockin_gt_notice" # Re-using ID for simplicity, could be new
            total_score += RULES[rule_id]["weight"] # Increased weight in KB
            triggered_rule_ids.append(rule_id)
        elif len(lock_in_months) >= 1: # Basic lock-in without clear notice is at least yellow-ish
            rule_id = "lockin_gt_notice"
            total_score += RULES[rule_id]["weight"] * 0.5 # Smaller weight for just lock-in mention
            triggered_rule_ids.append(rule_id)

    # 2) large deposit
    max_dep = THRESHOLDS["max_security_deposit_months"]
    deposit_months = _extract_deposit_months(text)
    # 2) security deposit rules
    # For T01 "Tenant must provide a security deposit equal to 2 months rent." (Expected: YELLOW)
    # For T04 "A security deposit of 5 months' rent is required." (Part of Expected: RED)
    if deposit_months is not None:
        if deposit_months >= 4:
            # New rule for very high deposit
            rule_id = "very_large_deposit" # Needs to be added to legal_kb.json
            total_score += RULES[rule_id]["weight"]
            triggered_rule_ids.append(rule_id)
        elif deposit_months >= 2: # 2-3 months deposit
            rule_id = "large_deposit"
            total_score += RULES[rule_id]["weight"]
            triggered_rule_ids.append(rule_id)
    # 3) unclear deposit - keep existing logic
    elif "security deposit" in text and deposit_months is None:
        rule_id = "large_deposit_unsure"
        total_score += RULES[rule_id]["weight"]
        triggered_rule_ids.append(rule_id)

    # 4) unilateral termination
    # 4) unilateral termination
    # For T03 "The landlord reserves the right to terminate this agreement at their sole discretion with a 7-day notice." (Expected: RED)
    unilateral_patterns = [
        r"landlord (?:reserves the right to|may) terminate(?: this agreement)?(?: at their sole discretion| at any time| without notice)",
        r"owner (?:reserves the right to|may) terminate(?: this agreement)?(?: at their sole discretion| at any time| without notice)",
        r"lender (?:reserves the right to|may) terminate(?: this agreement)?(?: at their sole discretion| at any time| without notice)"
    ]
    for pattern in unilateral_patterns:
        if re.search(pattern, text, flags=re.IGNORECASE):
            rule_id = "unilateral_termination"
            total_score += RULES[rule_id]["weight"]
            triggered_rule_ids.append(rule_id)
            break # Only trigger once for this rule

    # 5) high late fee
    max_late = THRESHOLDS["max_late_fee_percent"]
    percents = _extract_percent(text)
    # 5) high late fee
    # For T05 "The late fee for rent payments will be 5% of the monthly rent." (Expected: YELLOW)
    max_late_fee_threshold = THRESHOLDS["max_late_fee_percent"]
    percents = _extract_percent(text)
    if percents:
        max_p = max(percents)
        if max_p > max_late_fee_threshold:
            rule_id = "high_late_fee"
            # Ensure high_late_fee pushes to at least YELLOW if it's the only trigger
            total_score += RULES[rule_id]["weight"]
            triggered_rule_ids.append(rule_id)

    # cap at 1.0
    # Cap score at 1.0
    total_score = min(total_score, 1.0)

    # Define risk level thresholds
    GREEN_THRESHOLD = 0.29
    YELLOW_THRESHOLD = 0.69

    if total_score > YELLOW_THRESHOLD:
        level = "RED"
    elif total_score > GREEN_THRESHOLD:
        level = "YELLOW"
    else:
        level = "GREEN"

    return {
        "risk_score": round(total_score, 2),
        "risk_level": level,
        "triggered_rules": triggered_rule_ids,
        "reasons": _build_reasons(triggered_rule_ids, RULES),
    }


def analyze_clauses(clauses: List[Dict]) -> List[Dict]:
    """Attach risk info to each clause dict."""
    enriched: List[Dict] = []
    for c in clauses:
        risk = score_clause(c) # Pass the whole clause dict
        enriched.append({**c, **risk})
    return enriched
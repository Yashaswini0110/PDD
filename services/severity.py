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
    m = re.search(r"(\d+)\s*(months?|month)\s+(?:rent\s+as\s+)?(security\s+deposit|advance)",
                  text,
                  flags=re.IGNORECASE)
    if m:
        return int(m.group(1))
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

    if len(lock_in_months) >= 1 and len(notice_months) >= 2: # Simplified heuristic
        lock_in = lock_in_months[0]
        notice = notice_months[1] # Assuming second month is notice
        if lock_in > notice:
            rule_id = "lockin_gt_notice"
            total_score += RULES[rule_id]["weight"]
            triggered_rule_ids.append(rule_id)

    # 2) large deposit
    max_dep = THRESHOLDS["max_security_deposit_months"]
    deposit_months = _extract_deposit_months(text)
    if deposit_months is not None and deposit_months > max_dep:
        rule_id = "large_deposit"
        total_score += RULES[rule_id]["weight"]
        triggered_rule_ids.append(rule_id)
    # 3) unclear deposit
    elif "security deposit" in text and deposit_months is None:
        rule_id = "large_deposit_unsure"
        total_score += RULES[rule_id]["weight"]
        triggered_rule_ids.append(rule_id)

    # 4) unilateral termination
    if ("landlord may terminate" in text or
        "owner may terminate" in text or
        "lender may terminate" in text) and (
        "at any time" in text or "without notice" in text or "sole discretion" in text):
        rule_id = "unilateral_termination"
        total_score += RULES[rule_id]["weight"]
        triggered_rule_ids.append(rule_id)

    # 5) high late fee
    max_late = THRESHOLDS["max_late_fee_percent"]
    percents = _extract_percent(text)
    if percents:
        max_p = max(percents)
        if max_p > max_late:
            rule_id = "high_late_fee"
            total_score += RULES[rule_id]["weight"]
            triggered_rule_ids.append(rule_id)

    # cap at 1.0
    if total_score > 1.0:
        total_score = 1.0

    if total_score >= 0.67:
        level = "RED"
    elif total_score >= 0.34:
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
import json
from collections import defaultdict
from pathlib import Path
# No need to modify sys.path if run from PDD directory or PDD is in PYTHONPATH
# The knowledge base loader already handles its path relative to itself.

from services.kb_loader import load_kb
from services.severity import score_clause

def evaluate_severity_engine():
    # Load labeled clauses from the tests/ folder
    # Use __file__ to get the script's directory, then navigate to tests/
    try:
        base = Path(__file__).parent
        labeled_data_path = base / "tests" / "labeled_clauses_sample.json"
        with open(labeled_data_path, "r", encoding="utf-8") as f:
            labeled_data = json.load(f)
    except FileNotFoundError:
        print(f"Error: Labeled data file not found at {labeled_data_path.resolve()}")
        return
    except json.JSONDecodeError:
        print(f"Error: Could not parse JSON from {labeled_data_path.resolve()}")
        return

    items = labeled_data.get("items", [])
    labels = labeled_data.get("meta", {}).get("labels", ["GREEN", "YELLOW", "RED"])

    if not items:
        print("No labeled clauses found to evaluate.")
        return

    # Load the knowledge base using the application's loader
    try:
        kb = load_kb()
    except FileNotFoundError:
        print("Error: Knowledge base (legal_kb.json) not found in the 'knowledge' directory.")
        return

    correct_predictions = 0
    # Initialize confusion matrix with all possible label pairs
    confusion_matrix = defaultdict(lambda: defaultdict(int))
    for expected_lbl in labels:
        for predicted_lbl in labels:
            confusion_matrix[expected_lbl][predicted_lbl] = 0

    print(f"Starting evaluation of {len(items)} samples...")

    for item in items:
        clause_text = item["text"]
        expected_level = item["expected_level"].upper()

        # Score the clause using the severity engine
        result = score_clause({"text": clause_text}) # kb is loaded globally in severity.py
        predicted_level = result["risk_level"].upper()

        confusion_matrix[expected_level][predicted_level] += 1

        if predicted_level == expected_level:
            correct_predictions += 1
        else:
            print(f"  Mismatch for ID {item['id']}: Expected '{expected_level}', Got '{predicted_level}'")
            print(f"    Text: '{clause_text}'")
            print(f"    Reasons: {result['reasons']}")

    total_samples = len(items)
    accuracy = correct_predictions / total_samples if total_samples > 0 else 0.0

    print(f"\nTotal samples: {total_samples}")
    print(f"Accuracy: {accuracy:.2f}\n")

    print("Confusion matrix:")
    header = "expected \\ predicted " + " ".join(f"{lbl:8}" for lbl in labels)
    print(header)
    print("-" * len(header))

    for expected_lbl in labels:
        row_str = f"{expected_lbl:20}"
        for predicted_lbl in labels:
            row_str += f"{confusion_matrix[expected_lbl][predicted_lbl]:<9}"
        print(row_str)

if __name__ == "__main__":
    evaluate_severity_engine()
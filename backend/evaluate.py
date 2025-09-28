import json
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from app.parser import parse_pdf_to_clauses
from app.ai_core import get_embedding_model

def evaluate_retrieval(test_data_path: str, document_path: str):
    """
    Evaluates the retrieval accuracy of the RAG system.
    """
    print("--- Starting Retrieval Evaluation ---")

    # 1. Load the test data (golden dataset)
    try:
        with open(test_data_path, 'r', encoding='utf-8') as f:
            test_data = json.load(f)
        print(f"Loaded {len(test_data)} test cases from '{test_data_path}'")
    except FileNotFoundError:
        print(f"ERROR: Test data file not found at '{test_data_path}'")
        return

    # 2. Parse the document to get all clauses
    try:
        document_clauses = parse_pdf_to_clauses(document_path)["clauses"]
        if not document_clauses:
            print(f"ERROR: No clauses extracted from '{document_path}'")
            return
        print(f"Parsed {len(document_clauses)} clauses from '{document_path}'")
    except Exception as e:
        print(f"ERROR: Failed to parse PDF document: {e}")
        return

    embedding_model = get_embedding_model()
    
    # 3. Pre-embed all document clauses for efficiency
    print("Embedding all document clauses...")
    clause_texts = [c["text"] for c in document_clauses]
    clause_embeddings = embedding_model.embed_contents(clause_texts)['embedding']
    clause_embeddings = np.array(clause_embeddings)
    print("Embedding complete.")

    hits = 0
    total = len(test_data)

    print("\n--- Running Test Cases ---")
    for i, item in enumerate(test_data):
        question = item["question"]
        expected_clause_text = item["expected_clause"]

        # 4. Embed the question
        question_embedding = embedding_model.embed_content(question)['embedding']
        question_embedding = np.array(question_embedding).reshape(1, -1)

        # 5. Find the most similar clause
        similarities = cosine_similarity(question_embedding, clause_embeddings)[0]
        best_match_index = np.argmax(similarities)
        retrieved_clause = document_clauses[best_match_index]

        # 6. Check if the retrieved clause is the correct one
        # We check if the expected text is contained within the retrieved text for flexibility.
        is_hit = expected_clause_text.strip() in retrieved_clause["text"].strip()
        
        print(f"\nTest Case {i+1}: {question}")
        print(f"  - Expected: '{expected_clause_text[:80]}...'")
        print(f"  - Retrieved: '{retrieved_clause['text'][:80]}...'")
        print(f"  - HIT: {is_hit}")

        if is_hit:
            hits += 1

    # 7. Calculate and print the final score
    hit_rate = (hits / total) * 100 if total > 0 else 0
    print("\n--- Evaluation Complete ---")
    print(f"Total Test Cases: {total}")
    print(f"Correctly Retrieved: {hits}")
    print(f"Retrieval Hit Rate: {hit_rate:.2f}%")


if __name__ == "__main__":
    # You need to create these files to run the evaluation
    TEST_DATA_FILE = "evaluation_data.json"
    TEST_DOCUMENT_FILE = "uploads/sample_contract.pdf" # Make sure a sample PDF exists here
    
    # Check if placeholder files exist
    if not os.path.exists(TEST_DATA_FILE) or not os.path.exists(TEST_DOCUMENT_FILE):
        print("\nWARNING: Please create 'evaluation_data.json' and place a 'sample_contract.pdf' in the 'uploads' directory to run the evaluation.")
    else:
        evaluate_retrieval(test_data_path=TEST_DATA_FILE, document_path=TEST_DOCUMENT_FILE)
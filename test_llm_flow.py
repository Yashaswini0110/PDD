"""
Test script for LLM explanation flow.
Tests the /query_llm endpoint with sample queries and shows base_answer vs answer_llm comparison.
"""
import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:5055"
PDF_PATH = Path("sample.1.pdf")

def run_llm_flow_test():
    print("=== Running LLM explanation flow test ===\n")

    job_id = None

    # Step 1: Upload PDF
    try:
        print("--- Step 1: Upload PDF ---")
        if not PDF_PATH.exists():
            print(f"ERROR: PDF file not found at {PDF_PATH.resolve()}")
            return

        with open(PDF_PATH, "rb") as f:
            files = {'file': (PDF_PATH.name, f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/files/upload", files=files)
            if response.status_code != 200:
                print(f"ERROR: Upload failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return
            data = response.json()
            job_id = data.get("job_id")
            print(f"Upload successful: job_id = {job_id}\n")
            if not job_id:
                print("ERROR: job_id not returned from upload.")
                return

    except requests.exceptions.RequestException as e:
        print(f"ERROR during PDF upload: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return
    except Exception as e:
        print(f"ERROR during PDF upload: {e}")
        return

    # Step 2: Parse the PDF
    try:
        print(f"--- Step 2: Parse PDF for job_id {job_id} ---")
        response = requests.post(f"{BASE_URL}/process/{job_id}/parse")
        if response.status_code != 200:
            print(f"ERROR: Parse failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        data = response.json()
        print(f"Parse successful: {data.get('clauses_count', 0)} clauses found\n")

    except requests.exceptions.RequestException as e:
        print(f"ERROR during PDF parsing: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return
    except Exception as e:
        print(f"ERROR during PDF parsing: {e}")
        return

    # Step 3: Index the clauses for RAG
    try:
        print(f"--- Step 3: Index clauses for RAG for job_id {job_id} ---")
        response = requests.post(f"{BASE_URL}/rag/{job_id}/index")
        if response.status_code != 200:
            print(f"ERROR: Indexing failed with status {response.status_code}")
            print(f"Response: {response.text}")
            return
        data = response.json()
        print(f"Indexing successful: {data.get('clauses', 0)} clauses indexed\n")

    except requests.exceptions.RequestException as e:
        print(f"ERROR during RAG indexing: {e}")
        if hasattr(e, 'response') and e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return
    except Exception as e:
        print(f"ERROR during RAG indexing: {e}")
        return

    # Step 4: Query with LLM endpoint
    queries = [
        "What is the monthly rent?",
        "What happens if I pay rent late?",
        "Can I leave early before the lock-in period ends?"
    ]

    for query in queries:
        try:
            print(f"--- Step 4: Query LLM for '{query}' (job_id {job_id}) ---")
            payload = {"query": query, "top_k": 3}
            response = requests.post(f"{BASE_URL}/query_llm/{job_id}", json=payload)
            
            if response.status_code != 200:
                print(f"ERROR: Query failed with status {response.status_code}")
                print(f"Response: {response.text}")
                return
            
            data = response.json()
            
            print(f"Query: {query}")
            print(f"BASE: {data.get('base_answer', 'N/A')}")
            print(f"LLM : {data.get('answer_llm', 'N/A')}")
            
            matches = data.get('matches', [])
            if matches:
                first_match = matches[0]
                print(f"First match: id={first_match.get('id', 'N/A')}, "
                      f"page={first_match.get('page', 'N/A')}, "
                      f"risk_level={first_match.get('risk_level', 'N/A')}, "
                      f"risk_score={first_match.get('risk_score', 'N/A')}")
            else:
                print("First match: No matches found")
            
            print()  # Empty line between queries

        except requests.exceptions.RequestException as e:
            print(f"ERROR during query '{query}': {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response: {e.response.text}")
            return
        except Exception as e:
            print(f"ERROR during query '{query}': {e}")
            return

    print("=== LLM explanation flow test completed successfully ===")


if __name__ == "__main__":
    run_llm_flow_test()


import requests
import json
from pathlib import Path
import os
import sys
import time

BASE_URL = "http://127.0.0.1:5055"
PDF_PATH = Path("sample.1.pdf")

def run_full_flow_test():
    print("=== Running full ClauseClear pipeline test ===")

    # --- 1. Upload the PDF ---
    job_id = None
    try:
        print("\n--- Step 1: Upload PDF ---")
        if not PDF_PATH.exists():
            print(f"ERROR: PDF file not found at {PDF_PATH.resolve()}")
            return

        with open(PDF_PATH, "rb") as f:
            files = {'file': (PDF_PATH.name, f, 'application/pdf')}
            response = requests.post(f"{BASE_URL}/files/upload", files=files)
            response.raise_for_status() # Raise an exception for HTTP errors
            data = response.json()
            print(f"Upload successful: {json.dumps(data, indent=2)}")
            job_id = data.get("job_id")
            if not job_id:
                print("ERROR: job_id not returned from upload.")
                return

    except requests.exceptions.RequestException as e:
        print(f"ERROR during PDF upload: {e}")
        if e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return
    except Exception as e:
        print(f"ERROR during PDF upload: {e}")
        return

    # --- 2. Parse the PDF ---
    try:
        print(f"\n--- Step 2: Parse PDF for job_id {job_id} ---")
        response = requests.post(f"{BASE_URL}/process/{job_id}/parse")
        response.raise_for_status()
        data = response.json()
        print(f"Parse successful: {json.dumps(data, indent=2)}")
        if data.get("clauses_count", 0) == 0:
            print("WARNING: clauses_count is 0 after parsing.")

    except requests.exceptions.RequestException as e:
        print(f"ERROR during PDF parsing: {e}")
        if e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return
    except Exception as e:
        print(f"ERROR during PDF parsing: {e}")
        return

    # --- 3. Index the clauses for RAG ---
    try:
        print(f"\n--- Step 3: Index clauses for RAG for job_id {job_id} ---")
        response = requests.post(f"{BASE_URL}/rag/{job_id}/index")
        response.raise_for_status()
        data = response.json()
        print(f"Indexing successful: {json.dumps(data, indent=2)}")
        if data.get("shape", {}).get("rows", 0) == 0:
            print("WARNING: Index rows count is 0 after indexing.")

    except requests.exceptions.RequestException as e:
        print(f"ERROR during RAG indexing: {e}")
        if e.response:
            print(f"Status Code: {e.response.status_code}")
            print(f"Response: {e.response.text}")
        return
    except Exception as e:
        print(f"ERROR during RAG indexing: {e}")
        return

    # --- 4. Query with sample questions ---
    queries = [
        "security deposit",
        "termination",
        "general clause" # Added for a likely GREEN case
    ]

    for q in queries:
        try:
            print(f"\n--- Step 4: Querying for '{q}' (job_id {job_id}) ---")
            payload = {"query": q, "top_k": 1} # Using top_k=1 for simplified output
            response = requests.post(f"{BASE_URL}/query/{job_id}", json=payload)
            response.raise_for_status()
            data = response.json()
            # print(f"Query successful: {json.dumps(data, indent=2)}") # uncomment for full response

            print(f"  Answer: {data.get('answer', 'N/A')}")
            matches = data.get('matches', [])
            print(f"  Number of matches: {len(matches)}")

            if matches:
                first_match = matches[0]
                print(f"  First match ID: {first_match.get('id', 'N/A')}")
                print(f"  First match Page: {first_match.get('page', 'N/A')}")
                print(f"  First match Risk Level: {first_match.get('risk_level', 'N/A')}")
                print(f"  First match Risk Score: {first_match.get('risk_score', 'N/A'):.2f}")
            else:
                print("  No matches found for this query.")

        except requests.exceptions.RequestException as e:
            print(f"ERROR during query '{q}': {e}")
            if e.response:
                print(f"Status Code: {e.response.status_code}")
                print(f"Response: {e.response.text}")
            return
        except Exception as e:
            print(f"ERROR during query '{q}': {e}")
            return

    print("\n=== Full ClauseClear pipeline test completed successfully ===")


if __name__ == "__main__":
    run_full_flow_test()
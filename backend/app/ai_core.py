import os
import pickle
import numpy as np
import cohere
from dotenv import load_dotenv
from sklearn.metrics.pairwise import cosine_similarity

# Load environment variables from .env file
load_dotenv()

# Get the API key from the environment
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

if not COHERE_API_KEY:
    raise ValueError("COHERE_API_KEY not found in environment variables. Please set it in the .env file.")

# Initialize the Cohere client
co = cohere.Client(COHERE_API_KEY)

# --- Legal Knowledge Base Integration ---

LEGAL_KB_FILE = "legal_kb.pkl"
_legal_kb = None

def _load_legal_kb():
    """Loads the legal knowledge base from the pickle file."""
    global _legal_kb
    if _legal_kb is None:
        print("Loading Legal Knowledge Base...")
        try:
            with open(LEGAL_KB_FILE, "rb") as f:
                _legal_kb = pickle.load(f)
            # Convert embeddings to a NumPy array for efficient calculations
            _legal_kb["embeddings"] = np.array(_legal_kb["embeddings"])
            print("Legal Knowledge Base loaded successfully.")
        except FileNotFoundError:
            print(f"WARNING: '{LEGAL_KB_FILE}' not found. Legal context analysis will be disabled.")
            _legal_kb = {"chunks": [], "embeddings": np.array([])}
    return _legal_kb

def find_relevant_legal_clauses(query_text: str, top_k: int = 10) -> list[dict]:
    """
    Finds the most relevant legal clauses from the knowledge base for a given query text.
    Note: We retrieve more (top_k=10) to feed into the reranker later.
    """
    kb = _load_legal_kb()
    if kb is None or not kb["chunks"]:
        return []

    # 1. Generate embedding for the query
    response = co.embed(texts=[query_text], model='embed-english-v3.0', input_type='search_query')
    query_embedding = np.array(response.embeddings[0]).reshape(1, -1)

    # 2. Calculate cosine similarity between the query and all legal clauses
    similarities = cosine_similarity(query_embedding, kb["embeddings"])[0]

    # 3. Get the indices of the top_k most similar clauses
    top_k_indices = similarities.argsort()[-top_k:][::-1]

    # 4. Return the corresponding clauses
    relevant_clauses = [kb["chunks"][i] for i in top_k_indices]
    return relevant_clauses

# Pre-load the knowledge base when the application starts
_load_legal_kb()

from typing import List, Dict, Any
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from .ai_core import co

def answer_question_with_context(clauses: List[Dict[str, Any]], question: str, threshold: float = 0.7) -> Dict[str, Any]:
    """
    Answers a user's question by retrieving, reranking, and generating an
    answer with Cohere's models.
    """
    if not clauses:
        return {"answer": "The document contains no text to search.", "source_clause": None}

    # 1. Embed the user's question and all document clauses
    clause_texts = [c["text"] for c in clauses]
    response = co.embed(
        texts=[question] + clause_texts,
        model='embed-english-v3.0',
        input_type='search_document' # Use 'search_document' for all for simplicity here
    )
    question_embedding = np.array(response.embeddings[0]).reshape(1, -1)
    clause_embeddings = np.array(response.embeddings[1:])

    # 2. Find the top 10 most similar clauses (initial retrieval)
    similarities = cosine_similarity(question_embedding, clause_embeddings)[0]
    top_k_indices = similarities.argsort()[-10:][::-1]
    
    retrieved_docs = [clauses[i] for i in top_k_indices]
    retrieved_texts = [doc["text"] for doc in retrieved_docs]

    # 3. Use Cohere's rerank model to find the single best match
    rerank_response = co.rerank(
        query=question,
        documents=retrieved_texts,
        top_n=1,
        model="rerank-english-v3.0"
    )

    if not rerank_response.results or rerank_response.results[0].relevance_score < threshold:
        return {
            "answer": "I could not find a relevant clause in the document to answer your question.",
            "source_clause": None
        }

    best_doc_index = rerank_response.results[0].index
    best_clause = retrieved_docs[best_doc_index]

    # 4. Generate an answer using the chat model with the best clause as context
    prompt = f"""
    You are a helpful assistant. Your task is to answer a user's question based *only* on the provided clause from a contract.

    **Instructions:**
    1.  Read the user's question and the provided clause.
    2.  Generate an answer in **simple, plain English**, as if you were explaining it to a middle school student.
    3.  Do not use legal jargon.
    4.  If the clause does not contain the answer, simply say so.

    **User's Question:**
    {question}

    **Provided Clause:**
    "{best_clause['text']}"

    **Answer:**
    """

    try:
        response = co.chat(message=prompt, model="command-r-plus-08-2024")
        generated_answer = response.text
    except Exception as e:
        print(f"Error during answer generation: {e}")
        generated_answer = "There was an error generating the answer."

    return {
        "answer": generated_answer,
        "source_clause": best_clause
    }

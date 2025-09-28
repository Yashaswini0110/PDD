import os
import pickle
from tqdm import tqdm
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pypdf import PdfReader

# --- Configuration ---
LEGAL_KB_DIR = "legal_kb"
OUTPUT_FILE = "legal_kb.pkl"
CHUNK_SIZE = 1000  # The size of each text chunk in characters
CHUNK_OVERLAP = 100 # The overlap between consecutive chunks

def load_and_split_pdfs():
    """
    Loads all PDF files from the legal_kb directory, extracts their text,
    and splits the text into smaller, manageable chunks.
    """
    docs = []
    print(f"Scanning for PDF documents in '{LEGAL_KB_DIR}/'...")
    
    for filename in os.listdir(LEGAL_KB_DIR):
        if filename.lower().endswith(".pdf"):
            filepath = os.path.join(LEGAL_KB_DIR, filename)
            print(f"  - Processing {filename}...")
            try:
                reader = PdfReader(filepath)
                text = "".join(page.extract_text() or "" for page in reader.pages)
                if text:
                    docs.append({
                        "source": filename,
                        "text": text
                    })
                else:
                    print(f"    - WARNING: No text could be extracted from {filename}.")
            except Exception as e:
                print(f"    - ERROR: Failed to read or process {filename}. Reason: {e}")

    if not docs:
        return []

    print("\nSplitting extracted text into chunks...")
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    
    all_chunks = []
    for doc in docs:
        split_texts = text_splitter.split_text(doc["text"])
        for split_text in split_texts:
            all_chunks.append({
                "source": doc["source"],
                "text": split_text
            })
            
    print(f"Created {len(all_chunks)} text chunks from {len(docs)} document(s).")
    return all_chunks

from app.ai_core import co

def embed_chunks(chunks):
    """
    Generates embeddings for a list of text chunks using Cohere's
    embedding model.
    """
    print("\nGenerating embeddings for all chunks...")
    
    texts_to_embed = [chunk["text"] for chunk in chunks]
    
    # Cohere's API can handle batching automatically.
    response = co.embed(
        texts=texts_to_embed,
        model='embed-english-v3.0',
        input_type='search_document'
    )
    
    embeddings = response.embeddings
    print(f"Successfully generated {len(embeddings)} embeddings.")
    return embeddings

def build_knowledge_base():
    """
    Main function to build and save the legal knowledge base from PDF files.
    """
    print("--- Starting Legal Knowledge Base Build (Automated PDF Pipeline) ---")
    
    # 1. Load and split PDFs into chunks
    chunks = load_and_split_pdfs()
    if not chunks:
        print("No legal documents found or processed. Exiting.")
        return

    # 2. Generate embeddings for each chunk
    embeddings = embed_chunks(chunks)
    
    # 3. Combine chunks with their embeddings
    knowledge_base = {
        "chunks": chunks,
        "embeddings": embeddings
    }
    
    # 4. Save to a pickle file
    with open(OUTPUT_FILE, "wb") as f:
        pickle.dump(knowledge_base, f)
        
    print(f"\n--- Knowledge Base build complete! ---")
    print(f"Saved {len(chunks)} chunks and {len(embeddings)} embeddings to '{OUTPUT_FILE}'")

if __name__ == "__main__":
    build_knowledge_base()
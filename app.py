import os
from pathlib import Path
import json

from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel
from loguru import logger

from services.tfidf_index import build_index as build_tfidf_index, search as tfidf_search
from services.db import init_db, get_db
from services.parse_pdf import extract_text_from_pdf
from services.clauses import split_into_clauses
from services.severity import analyze_clauses, score_clause

from time import perf_counter
from uuid import uuid4
from datetime import datetime, timezone
from utils import safe_filename, ensure_dirs

# --- init ---
ensure_dirs()
logger.remove()
logger.add("logs/app.log", level="INFO",
           rotation="5 MB", retention=5,
           format='{{"time":"{time:YYYY-MM-DDTHH:mm:ss.SSSZ}","level":"{level}","msg":"{message}"}}')

load_dotenv()
app = FastAPI(title="ClauseClear Mini", version="0.1.0")

app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
def startup_db_client():
    init_db()

@app.get("/config/firebase")
def get_firebase_config():
    return {
        "apiKey": os.getenv("FIREBASE_API_KEY"),
        "authDomain": os.getenv("FIREBASE_AUTH_DOMAIN"),
        "projectId": os.getenv("FIREBASE_PROJECT_ID"),
        "messagingSenderId": os.getenv("FIREBASE_MESSAGING_SENDER_ID"),
        "appId": os.getenv("FIREBASE_APP_ID")
    }

@app.middleware("http")
async def access_log(request: Request, call_next):
    start = perf_counter()
    resp = await call_next(request)
    dur = int((perf_counter() - start) * 1000)
    logger.info(f'req method={request.method} path={request.url.path} status={resp.status_code} ms={dur}')
    return resp

@app.get("/")
def read_root():
    # Serve the login page as the entry point
    return FileResponse("static/index.html")

class UserProfile(BaseModel):
    uid: str
    email: str
    firstName: str
    lastName: str
    dob: str
    phone: str
    address: str
    pan: str
    aadhaar: str

@app.post("/users/register")
def register_user(user: UserProfile):
    db = get_db()
    if db is None:
        logger.warning("MongoDB not connected, skipping user save")
        return {"status": "ok", "msg": "User data received (mock mode)"}
    
    try:
        users_collection = db["users"]
        users_collection.update_one(
            {"uid": user.uid},
            {"$set": user.model_dump()},
            upsert=True
        )
        return {"status": "ok", "msg": "User saved"}
    except Exception as e:
        logger.error(f"Error saving user: {e}")
        raise HTTPException(status_code=500, detail="Failed to save user profile")

@app.put("/users/update")
def update_user(user: UserProfile):
    db = get_db()
    if db is None:
        return {"status": "ok", "msg": "Mock update"}
    
    try:
        users_collection = db["users"]
        result = users_collection.update_one(
            {"uid": user.uid},
            {"$set": user.model_dump()}
        )
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="User not found")
        return {"status": "ok", "msg": "User updated"}
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail="Failed to update user profile")

@app.get("/users/{uid}")
def get_user(uid: str):
    db = get_db()
    if db is None:
        # Return mock data if DB not connected
        return {
            "uid": uid,
            "firstName": "Developer",
            "lastName": "User",
            "email": "dev@clauseclear.com",
            "phone": "0000000000",
            "address": "Mock Address",
            "dob": "2000-01-01",
            "pan": "ABCDE1234F",
            "aadhaar": "123456789012"
        }
    
    user = db["users"].find_one({"uid": uid}, {"_id": 0})
    if not user:
         raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return {}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/knowledge/kb")
def get_legal_kb():
    kb_path = Path("knowledge") / "legal_kb.json"
    if not kb_path.exists():
        raise HTTPException(status_code=500, detail="Knowledge base file not found.")
    data = json.loads(kb_path.read_text(encoding="utf-8"))
    return data

ALLOWED = {"pdf", "docx"}
MAX_MB = 10

@app.post("/files/upload")
async def upload(file: UploadFile = File(...)):
    raw = await file.read()
    if len(raw) > MAX_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large (>{MAX_MB} MB)")
    fname = safe_filename(file.filename)
    ext = fname.split(".")[-1].lower()
    if ext not in ALLOWED:
        raise HTTPException(400, f"Only {sorted(ALLOWED)} allowed")

    job_id = str(uuid4())
    job_dir = Path("storage/uploads") / job_id
    job_dir.mkdir(parents=True, exist_ok=True)
    (job_dir / "created_at.txt").write_text(datetime.now(timezone.utc).isoformat())
    (job_dir / fname).write_bytes(raw)

    return {
        "job_id": job_id,
        "filename": fname,
        "size_bytes": len(raw),
        "path": (job_dir / fname).as_posix()
    }

@app.get("/files/{job_id}/status")
def status(job_id: str):
    jd = Path("storage/uploads") / job_id
    if not jd.exists():
        return {"exists": False}
    files = [p.name for p in jd.iterdir() if p.is_file()]
@app.post("/process/{job_id}/parse")
def parse(job_id: str):
    job_dir = Path("storage/uploads") / job_id
    if not job_dir.exists():
        raise HTTPException(404, "job_id not found")
    # find first PDF in folder
    pdfs = list(job_dir.glob("*.pdf"))
    if not pdfs:
        raise HTTPException(400, "no PDF file found for job")
    pdf_path = pdfs[0]
    logger.info(f"parse_job job_id={job_id} pdf_path={pdf_path}")
    pages = extract_text_from_pdf(pdf_path)
    logger.info(f"parse_job job_id={job_id} extracted_pages={len(pages)}")
    all_clauses = []
    for page_num, text in enumerate(pages, start=1):
        clauses = split_into_clauses(text)
        for i, clause in enumerate(clauses, start=1):
            all_clauses.append({
                "id": f"P{page_num:02d}_C{i:03d}",
                "page": page_num,
                "text": clause
            })
    logger.info(f"parse_job job_id={job_id} total_clauses={len(all_clauses)}")
    out = {
        "job_id": job_id,
        "pages": len(pages),
        "clauses_count": len(all_clauses),
        "clauses": all_clauses
    }
    (job_dir / "clauses.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    return {"job_id": job_id, "pages": len(pages), "clauses_count": len(all_clauses)}
    size = sum(p.stat().st_size for p in jd.iterdir() if p.is_file())
    created = (jd / "created_at.txt").read_text() if (jd / "created_at.txt").exists() else None
    return {"exists": True, "bytes": size, "files": files, "created_at_iso": created}

@app.post("/rag/{job_id}/index")
def rag_index(job_id: str):
    job_dir = Path("storage/uploads") / job_id
    cj = job_dir / "clauses.json"
    if not cj.exists():
        raise HTTPException(404, "clauses.json not found. Run /process/{job_id}/parse first.")
    data = json.loads(cj.read_text(encoding="utf-8"))
    clauses = data.get("clauses", [])
    info = build_tfidf_index(job_id, clauses)
    return {"job_id": job_id, "clauses": len(clauses), "shape": info}

@app.post("/rag/{job_id}/search")
def rag_search(job_id: str, payload: dict):
    query = (payload or {}).get("query", "").strip()
    top_k = int((payload or {}).get("top_k", 5))
    if not query:
        raise HTTPException(400, "query is required")

    job_dir = Path("storage/uploads") / job_id
    cj = job_dir / "clauses.json"
    if not cj.exists():
        raise HTTPException(404, "clauses.json not found. Run /process/{job_id}/parse first.")
    data = json.loads(cj.read_text())
    clauses = data.get("clauses", [])

    try:
        matches = tfidf_search(job_id, query, clauses, top_k=top_k)
    except FileNotFoundError:
        raise HTTPException(404, "index not built. Call /rag/{job_id}/index first.")
    return {"job_id": job_id, "query": query, "matches": matches}

@app.post("/analyze/{job_id}/clauses")
def analyze_job_clauses(job_id: str, uid: str = "dev-user"):
    """
    Load clauses.json for this job_id, run the weighted rules-based severity engine,
    save analysis.json, and return basic stats + enriched clauses.
    Also saves the job summary to MongoDB for the user history.
    """
    job_dir = Path("storage/uploads") / job_id
    cj = job_dir / "clauses.json"
    if not cj.exists():
        raise HTTPException(status_code=404, detail="clauses.json not found. Run /process/{job_id}/parse first.")

    data = json.loads(cj.read_text(encoding="utf-8"))
    clauses = data.get("clauses", [])

    analyzed = analyze_clauses(clauses)

    aj = job_dir / "analysis.json"
    aj.write_text(json.dumps({"job_id": job_id, "clauses": analyzed}, ensure_ascii=False, indent=2), encoding="utf-8")

    summary = {"GREEN": 0, "YELLOW": 0, "RED": 0}
    for c in analyzed:
        lvl = c.get("risk_level", "GREEN")
        if lvl in summary:
            summary[lvl] += 1

    # Save to History (MongoDB)
    db = get_db()
    if db is not None:
        # Get filename from folder (assuming first file besides created_at/clauses etc is the doc)
        # Or parse from a metadata file if we had one. We can look for known extensions.
        filename = "Document"
        for p in job_dir.iterdir():
            if p.suffix.lower() in ['.pdf', '.docx']:
                filename = p.name
                break
        
        db["jobs"].update_one(
            {"job_id": job_id},
            {"$set": {
                "job_id": job_id,
                "uid": uid,
                "filename": filename,
                "summary": summary,
                "created_at": datetime.now(timezone.utc).isoformat()
            }},
            upsert=True
        )

    logger.info(f"analyze_ok job_id={job_id} total={len(analyzed)} summary={summary}")

    return {
        "job_id": job_id,
        "total_clauses": len(analyzed),
        "summary": summary,
        "clauses": analyzed,
    }

@app.get("/users/{uid}/history")
def get_user_history(uid: str):
    db = get_db()
    if db is None:
        return []
    
    cursor = db["jobs"].find({"uid": uid}).sort("created_at", -1).limit(20)
    history = []
    for doc in cursor:
        doc.pop("_id", None)
        history.append(doc)
    return history

def build_answer_for_query(query: str, matches: list[dict]) -> str:
    if not matches:
        return "UNKNOWN – this clause does not exist clearly in your document."

    best = matches[0]
    cid = best.get("id", "N/A")
    page = best.get("page", "N/A")
    risk_level = best.get("risk_level", "UNKNOWN").upper()
    risk_score = best.get("risk_score", 0.0)
    reasons = best.get("reasons", [])
    clause_text = best.get("text", "")

    main_reason = reasons[0] if reasons else "Please review this clause carefully."

    if risk_level == "GREEN":
        answer_string = (
            f"Your document does talk about '{query}'. Clause {cid} on page {page} mentions it as: '{clause_text}'. "
            f"Our rules currently mark this as GREEN (low risk, score {risk_score:.2f}). {main_reason}"
        )
    elif risk_level == "YELLOW":
        answer_string = (
            f"I found a clause about '{query}' (clause {cid}, page {page}): '{clause_text}'. "
            f"This looks like a MEDIUM risk (YELLOW, score {risk_score:.2f}). {main_reason}"
        )
    elif risk_level == "RED":
        answer_string = (
            f"Warning: clause {cid} on page {page} seems HIGH risk (RED, score {risk_score:.2f}) regarding '{query}'. "
            f"Text: '{clause_text}'. {main_reason}"
        )
    else: # Fallback for UNKNOWN or unexpected risk levels
        answer_string = (
            f"I found clause {cid} on page {page} related to your query '{query}'. "
            f"Text: '{clause_text}'. Risk level: {risk_level} (score {risk_score:.2f}). {main_reason}"
        )
    return answer_string

@app.post("/query/{job_id}")
def query_job(job_id: str, payload: dict):
    """
    Unified endpoint for frontend:
    - uses TF-IDF RAG to find top-k clauses
    - attaches risk info for each match.
    - saves chat history to MongoDB
    """
    query = (payload or {}).get("query", "").strip()
    top_k = int((payload or {}).get("top_k", 5))
    if not query:
        raise HTTPException(status_code=400, detail="query is required")

    job_dir = Path("storage/uploads") / job_id
    clauses_path = job_dir / "clauses.json"
    if not clauses_path.exists():
        raise HTTPException(status_code=404, detail="clauses.json not found. Run /process/{job_id}/parse first.")

    # load all clauses
    data = json.loads(clauses_path.read_text(encoding="utf-8"))
    clauses = data.get("clauses", [])

    try:
        # use existing TF-IDF search helper
        results = tfidf_search(job_id, query, clauses, top_k=top_k)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="RAG index not built. Call /rag/{job_id}/index first.")

    # `results` should be a list of dicts with at least: id, page, text, score
    enriched_matches = []
    for r in results:
        # Find the original clause using its ID to ensure we have all original metadata
        original_clause = next((c for c in clauses if c.get("id") == r.get("id")), None)
        if original_clause:
            risk = score_clause(original_clause) # Pass the whole clause dict
            enriched_matches.append({
                "id": original_clause.get("id"),
                "page": original_clause.get("page"),
                "text": original_clause.get("text"),
                "score": r.get("score"),
                **risk,
            })

    answer = build_answer_for_query(query, enriched_matches)

    # Save chat to DB
    db = get_db()
    if db is not None:
        db["jobs"].update_one(
            {"job_id": job_id},
            {"$push": {"chat_history": {"query": query, "answer": answer, "timestamp": datetime.now(timezone.utc).isoformat()}}}
        )

    logger.info(f"query_ok job_id={job_id} q={query!r} top_k={top_k} returned={len(enriched_matches)}")

    return {
        "job_id": job_id,
        "query": query,
        "top_k": top_k,
        "answer": answer,
        "matches": enriched_matches,
    }

@app.get("/analyze/{job_id}/chat")
def get_job_chat(job_id: str):
    db = get_db()
    if db is None:
        return []
    job = db["jobs"].find_one({"job_id": job_id}, {"chat_history": 1, "_id": 0})
    return job.get("chat_history", []) if job else []

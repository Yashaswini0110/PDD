from pathlib import Path
import json

from fastapi import FastAPI, UploadFile, File, HTTPException, Request
from loguru import logger

from services.tfidf_index import build_index as build_tfidf_index, search as tfidf_search
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

app = FastAPI(title="ClauseClear Mini", version="0.1.0")

@app.middleware("http")
async def access_log(request: Request, call_next):
    start = perf_counter()
    resp = await call_next(request)
    dur = int((perf_counter() - start) * 1000)
    logger.info(f'req method={request.method} path={request.url.path} status={resp.status_code} ms={dur}')
    return resp

@app.get("/health")
def health():
    return {
        "status": "ok",
        "app": "ClauseClear Mini",
        "version": "0.1.0",
        "time": datetime.now(timezone.utc).isoformat()
    }

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
    pages = extract_text_from_pdf(pdf_path)
    all_clauses = []
    for page_num, text in enumerate(pages, start=1):
        clauses = split_into_clauses(text)
        for i, clause in enumerate(clauses, start=1):
            all_clauses.append({
                "id": f"P{page_num:02d}_C{i:03d}",
                "page": page_num,
                "text": clause
            })
    out = {
        "job_id": job_id,
        "pages": len(pages),
        "clauses_count": len(all_clauses),
        "clauses": all_clauses
    }
    (job_dir / "clauses.json").write_text(json.dumps(out, ensure_ascii=False, indent=2))
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
    data = json.loads(cj.read_text())
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
def analyze_job_clauses(job_id: str):
    """
    Load clauses.json for this job_id, run the weighted rules-based severity engine,
    save analysis.json, and return basic stats + enriched clauses.
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

    logger.info(f"analyze_ok job_id={job_id} total={len(analyzed)} summary={summary}")

    return {
        "job_id": job_id,
        "total_clauses": len(analyzed),
        "summary": summary,
        "clauses": analyzed,
    }

def build_answer(query: str, matches: list[dict]) -> str:
    if not matches:
        return "UNKNOWN – this clause does not exist clearly in your document."

    best = matches[0]
    clause_id = best.get("id", "N/A")
    page = best.get("page", "N/A")
    risk_level = best.get("risk_level", "N/A")
    risk_score = best.get("risk_score", "N/A")
    reasons = best.get("reasons", ["no specific reason available"])

    answer_string = (
        f"I found clause {clause_id} on page {page} related to your query '{query}'. "
        f"Risk level: {risk_level} (score {risk_score}). "
        f"Reason: {reasons[0]}."
    )
    return answer_string

@app.post("/query/{job_id}")
def query_job(job_id: str, payload: dict):
    """
    Unified endpoint for frontend:
    - uses TF-IDF RAG to find top-k clauses
    - attaches risk info for each match.
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

    answer = build_answer(query, enriched_matches)

    logger.info(f"query_ok job_id={job_id} q={query!r} top_k={top_k} returned={len(enriched_matches)}")

    return {
        "job_id": job_id,
        "query": query,
        "top_k": top_k,
        "answer": answer,
        "matches": enriched_matches,
    }

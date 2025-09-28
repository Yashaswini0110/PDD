from fastapi import APIRouter, UploadFile, File, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Dict, Any
import datetime
import os

from . import storage, parser, severity, qa, export, clauses

router = APIRouter(prefix="/api", tags=["api"]) 


@router.post("/upload")
async def upload_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
	allowed_extensions = {".pdf", ".docx", ".txt"}
	file_extension = os.path.splitext(file.filename)[1].lower()
	if file_extension not in allowed_extensions:
		raise HTTPException(status_code=400, detail=f"File type not supported. Please upload a .pdf, .docx, or .txt file.")
	object_name = storage.generate_object_name(file.filename)
	data = await file.read()
	storage.save_bytes(object_name, data)
	# Set expiration time for 24 hours from now
	expiration_time = datetime.datetime.now() + datetime.timedelta(hours=24)
	storage.set_expiration(object_name, expiration_time)
	return {"object_name": object_name, "expires_at": expiration_time.isoformat()}


@router.post("/analyze")
async def analyze(object_name: str = Query(...)) -> Dict[str, Any]:
	if not storage.file_exists(object_name):
		raise HTTPException(status_code=404, detail="Object not found")
	pdf_path = storage.get_local_path(object_name)
	doc = parser.parse_file_to_clauses(pdf_path)
	
	# Analyze for severity flags using the new, fast hybrid model
	flags = severity.analyze_clauses_with_hybrid_model(doc["clauses"])
	
	# The old summaries are no longer needed as the new flags contain richer justifications.
	# We can reconstruct summaries on the frontend if needed from the flags.
	
	return {
		"text": doc["text"],
		"clauses": doc["clauses"],
		"flags": flags,
		"summaries": [] # Return an empty list for now
	}


@router.get("/qa")
async def question(object_name: str = Query(...), q: str = Query(...)) -> Dict[str, Any]:
	if not storage.file_exists(object_name):
		raise HTTPException(status_code=404, detail="Object not found")
	pdf_path = storage.get_local_path(object_name)
	# Note: For a real application, you'd cache the parsed document
	# to avoid re-parsing it for every single question.
	doc = parser.parse_file_to_clauses(pdf_path)
	res = qa.answer_question_with_context(doc["clauses"], q)
	return res


@router.get("/export", response_class=HTMLResponse)
async def export_report(object_name: str = Query(...), contract_type: str = Query("UNKNOWN")):
	if not storage.file_exists(object_name):
		raise HTTPException(status_code=404, detail="Object not found")
	pdf_path = storage.get_local_path(object_name)
	doc = parser.parse_file_to_clauses(pdf_path)
	flags = severity.analyze_clauses_with_hybrid_model(doc["clauses"])
	html = export.generate_report_html(doc, flags, contract_type)
	return HTMLResponse(content=html, status_code=200, headers={"Content-Disposition": f"attachment; filename=report.html"})
	
@router.delete("/delete")
async def delete_file(object_name: str = Query(...)) -> Dict[str, Any]:
	if not storage.file_exists(object_name):
		raise HTTPException(status_code=404, detail="Object not found")
	success = storage.delete_file(object_name)
	return {"success": success, "message": "File deleted successfully"}
	summaries = []
	for c in doc["clauses"][:20]:
		text = c["text"].split(".")[0].strip()
		if text:
			summaries.append(text)
	html = export.render_report(contract_type, summaries, flags)
	return HTMLResponse(content=html)


@router.delete("/delete_now") # Renamed to avoid conflict
async def delete_now(object_name: str = Query(...)) -> Dict[str, Any]:
	deleted = storage.delete_object(object_name)
	if not deleted:
		raise HTTPException(status_code=404, detail="Object not found")
	return {"deleted": True}

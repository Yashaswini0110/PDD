# Manual Testing Guide - ClauseClear Backend

## 🚀 Server Status

✅ **Server is running on:** `http://localhost:5055`

---

## 🌐 Access Points

### Frontend (Web UI)
- **Main Page:** http://localhost:5055/
- **Login Page:** http://localhost:5055/static/index.html
- **Home Page:** http://localhost:5055/static/home.html
- **Upload Page:** http://localhost:5055/static/uploads.html

### API Documentation
- **Swagger UI (Interactive):** http://localhost:5055/docs
- **ReDoc (Alternative):** http://localhost:5055/redoc

### Health Check
- **Health Endpoint:** http://localhost:5055/health

---

## 📋 Manual Testing Steps

### 1. Test via Web UI (Frontend)

1. **Open Browser:**
   - Navigate to: http://localhost:5055/
   - You should see the login/index page

2. **Upload a PDF:**
   - Go to upload page: http://localhost:5055/static/uploads.html
   - Upload a PDF file (use `sample.1.pdf` from the repo root for testing)
   - Note the `job_id` returned

3. **View Results:**
   - After upload, parse, and analyze, view results at: http://localhost:5055/static/results.html

---

### 2. Test via API (Using Swagger UI)

1. **Open Swagger UI:**
   - Go to: http://localhost:5055/docs
   - You'll see all available endpoints

2. **Test Upload Endpoint:**
   - Find `POST /files/upload`
   - Click "Try it out"
   - Upload `sample.1.pdf` (located in repo root)
   - Click "Execute"
   - Copy the `job_id` from the response

3. **Test Parse Endpoint:**
   - Find `POST /process/{job_id}/parse`
   - Replace `{job_id}` with the job_id from step 2
   - Click "Execute"
   - Should return: `{"job_id": "...", "pages": 4, "clauses_count": 42}`

4. **Test Index Endpoint:**
   - Find `POST /rag/{job_id}/index`
   - Replace `{job_id}` with your job_id
   - Click "Execute"
   - Should return indexing success message

5. **Test Query Endpoint:**
   - Find `POST /query/{job_id}`
   - Replace `{job_id}` with your job_id
   - In the request body, enter:
     ```json
     {
       "query": "security deposit",
       "top_k": 3
     }
     ```
   - Click "Execute"
   - Should return answer with risk level and matches

6. **Test LLM Query Endpoint:**
   - Find `POST /query_llm/{job_id}`
   - Replace `{job_id}` with your job_id
   - In the request body, enter:
     ```json
     {
       "query": "What is the monthly rent?",
       "top_k": 3
     }
     ```
   - Click "Execute"
   - Should return both `base_answer` and `answer_llm` (simple language)

---

### 3. Test via Command Line (Python Scripts)

**In a new terminal window:**

```bash
cd "C:\Users\yasha\Desktop\pdd final"

# Test full pipeline
python test_full_flow.py

# Test LLM flow
python test_llm_flow.py
```

---

### 4. Test Individual Endpoints (cURL/PowerShell)

**Health Check:**
```powershell
Invoke-WebRequest -Uri "http://localhost:5055/health" -Method GET
```

**Upload PDF:**
```powershell
$filePath = "sample.1.pdf"
$uri = "http://localhost:5055/files/upload"
$form = @{
    file = Get-Item -Path $filePath
}
Invoke-RestMethod -Uri $uri -Method Post -Form $form
```

**Query (after upload, parse, index):**
```powershell
$jobId = "YOUR_JOB_ID_HERE"
$uri = "http://localhost:5055/query/$jobId"
$body = @{
    query = "security deposit"
    top_k = 3
} | ConvertTo-Json
Invoke-RestMethod -Uri $uri -Method Post -Body $body -ContentType "application/json"
```

---

## 🧪 Test Scenarios

### Scenario 1: Full Document Analysis
1. Upload a PDF
2. Parse it
3. Index clauses
4. Analyze clauses (get risk levels)
5. Query multiple questions

### Scenario 2: LLM Explanations
1. Upload a PDF
2. Parse and index
3. Query with `/query_llm/{job_id}`
4. Verify `answer_llm` is in simple language

### Scenario 3: Error Handling
1. Try querying without parsing (should get 404)
2. Try querying without indexing (should get 404)
3. Try invalid job_id (should get 404)

---

## 📊 Expected Results

### Successful Upload:
```json
{
  "job_id": "uuid-here",
  "filename": "sample.1.pdf",
  "size_bytes": 43671,
  "path": "storage/uploads/..."
}
```

### Successful Parse:
```json
{
  "job_id": "uuid-here",
  "pages": 4,
  "clauses_count": 42
}
```

### Successful Query:
```json
{
  "job_id": "uuid-here",
  "query": "security deposit",
  "top_k": 3,
  "answer": "Your document does talk about 'security deposit'...",
  "matches": [
    {
      "id": "P02_C006",
      "page": 2,
      "text": "...",
      "score": 0.85,
      "risk_level": "GREEN",
      "risk_score": 0.20,
      "reasons": ["..."]
    }
  ]
}
```

### Successful LLM Query:
```json
{
  "job_id": "uuid-here",
  "query": "What is the monthly rent?",
  "top_k": 3,
  "base_answer": "Your document does talk about...",
  "answer_llm": "Okay, so your monthly rent is...",
  "matches": [...]
}
```

---

## 🛑 Stopping the Server

To stop the server:
1. Go to the server window (PowerShell window running uvicorn)
2. Press `Ctrl+C`
3. Or close the window

---

## 📝 Notes

- The server must stay running while you test
- Test PDF file: `sample.1.pdf` is in the repo root
- All endpoints are documented in Swagger UI at `/docs`
- MongoDB connection is optional (app works without it)
- GEMINI_API_KEY is required for LLM features (check `.env` file)

---

## ✅ Quick Verification Checklist

- [ ] Server responds to `/health`
- [ ] Swagger UI loads at `/docs`
- [ ] Frontend loads at `/`
- [ ] Can upload PDF via API
- [ ] Can parse uploaded PDF
- [ ] Can index clauses
- [ ] Can query with `/query/{job_id}`
- [ ] Can query with `/query_llm/{job_id}`
- [ ] LLM returns simple language explanations

---

**Happy Testing! 🎉**


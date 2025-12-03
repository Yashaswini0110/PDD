# Final Test Checklist - ClauseClear Backend

## ✅ Status Summary

### 1️⃣ Local Sanity Check Results

#### ✅ Step 1: Severity Engine Test - PASSED
```bash
python evaluate_severity.py
```

**Result:**
```
Starting evaluation of 8 samples...
Total samples: 8
Accuracy: 1.00

Confusion matrix:
expected \ predicted GREEN    YELLOW   RED
-----------------------------------------------
GREEN               4        0        0
YELLOW              0        2        0
RED                 0        0        2
```

**Status:** ✅ **100% accuracy - All test cases passed!**

---

#### ⏳ Step 2-3: Full Flow & LLM Tests - REQUIRES MANUAL SERVER START

**To complete these tests, you need to:**

1. **Open Terminal 1** (PowerShell or Command Prompt):
   ```bash
   cd "C:\Users\yasha\Desktop\pdd final"
   uvicorn app:app --host 0.0.0.0 --port 5055
   ```
   Leave this running - you should see:
   ```
   INFO:     Started server process
   INFO:     Waiting for application startup.
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:5055
   ```

2. **Open Terminal 2** (new PowerShell/Command Prompt window):
   ```bash
   cd "C:\Users\yasha\Desktop\pdd final"
   
   # Test full flow
   python test_full_flow.py
   
   # Test LLM flow
   python test_llm_flow.py
   ```

---

### Expected Test Results

#### `test_full_flow.py` - Expected Output:
```
=== Running full ClauseClear pipeline test ===

--- Step 1: Upload PDF ---
Upload successful: {
  "job_id": "...",
  "filename": "sample.1.pdf",
  ...
}

--- Step 2: Parse PDF for job_id ... ---
Parse successful: {
  "job_id": "...",
  "pages": 4,
  "clauses_count": 42
}

--- Step 3: Index clauses for RAG for job_id ... ---
Indexing successful: {
  "job_id": "...",
  "clauses": 42,
  "shape": {"rows": 42, "cols": 1301}
}

--- Step 4: Querying for 'security deposit' (job_id ...) ---
  Answer: Your document does talk about 'security deposit'...
  Number of matches: 1
  First match ID: P01_C001
  First match Page: 1
  First match Risk Level: YELLOW
  First match Risk Score: 0.40

--- Step 4: Querying for 'termination' (job_id ...) ---
  Answer: Warning: clause ... seems HIGH risk (RED, score ...)...
  ...

--- Step 4: Querying for 'general clause' (job_id ...) ---
  Answer: Your document does talk about 'general clause'...
  ...

=== Full ClauseClear pipeline test completed successfully ===
```

**✅ Success Criteria:**
- All 4 steps complete without errors
- Upload returns job_id
- Parse extracts clauses
- Index builds successfully
- Query returns answers with risk levels (GREEN/YELLOW/RED)

---

#### `test_llm_flow.py` - Expected Output:
```
=== Running LLM explanation flow test ===

--- Step 1: Upload PDF ---
Upload successful: job_id = ...

--- Step 2: Parse PDF for job_id ... ---
Parse successful: 42 clauses found

--- Step 3: Index clauses for RAG for job_id ... ---
Indexing successful: 42 clauses indexed

--- Step 4: Query LLM for 'What is the monthly rent?' (job_id ...) ---
Query: What is the monthly rent?
BASE: Your document does talk about 'What is the monthly rent?'...
LLM : Hey, so basically your rent is $X per month. You need to pay this on the first of each month...
First match: id=P01_C002, page=1, risk_level=GREEN, risk_score=0.15

--- Step 4: Query LLM for 'What happens if I pay rent late?' (job_id ...) ---
Query: What happens if I pay rent late?
BASE: I found a clause about 'What happens if I pay rent late?'...
LLM : If you pay your rent late, you'll have to pay an extra fee of X%. Make sure to pay on time to avoid this...
First match: id=P02_C005, page=2, risk_level=YELLOW, risk_score=0.35

--- Step 4: Query LLM for 'Can I leave early before the lock-in period ends?' (job_id ...) ---
Query: Can I leave early before the lock-in period ends?
BASE: Warning: clause ... seems HIGH risk (RED, score ...)...
LLM : This is important - you're locked into this agreement for X months. If you try to leave early, you might have to pay a penalty...
First match: id=P03_C010, page=3, risk_level=RED, risk_score=0.75

=== LLM explanation flow test completed successfully ===
```

**✅ Success Criteria:**
- All 4 steps complete without errors
- Both `base_answer` and `answer_llm` are returned
- `answer_llm` is in simple, friendly language (8th-grade level)
- No 404 or 500 errors

---

## 2️⃣ Docker Check (When Docker Desktop is ON)

### Build and Run:
```bash
# From repo root
docker build -t clauseclear-backend:clean-test .
docker run --rm -p 5055:5055 --env-file .env clauseclear-backend:clean-test
```

### Test Against Container:
In another terminal:
```bash
python test_full_flow.py
python test_llm_flow.py
```

**Expected:** Same results as local tests, but running against Docker container.

---

## 3️⃣ Git + Jenkins

### Commit Changes:
```bash
git status           # Confirm only expected files changed
git add .
git commit -m "fix: safe TF-IDF search & LLM query endpoint

- Fixed /query endpoint: Changed to ID-based matching in tfidf_index.py
- Fixed /query_llm endpoint: Added comprehensive error handling
- Both endpoints now handle edge cases gracefully
- No business logic changes, only safety improvements"
git push
```

### Jenkins Pipeline Check:
After pushing, trigger Jenkins job and verify:
- ✅ Docker build stage completes
- ✅ Push to Artifact Registry succeeds
- ✅ Deploy to Cloud Run succeeds

---

## 📋 Files Changed Summary

### Modified Files:
1. **services/tfidf_index.py**
   - Fixed `search()` to use ID-based matching instead of index-based
   - Prevents IndexError when clause order differs

2. **app.py**
   - Added error handling to `/query/{job_id}` endpoint
   - Fixed `/query_llm/{job_id}` endpoint (changed to sync, added error handling)

### No Changes To:
- Business logic
- API response structure
- Dockerfile
- Jenkinsfile
- Other endpoints

---

## ✅ Verification Checklist

- [x] Severity engine test passes (100% accuracy)
- [ ] Full flow test passes (requires server running)
- [ ] LLM flow test passes (requires server running)
- [ ] Docker build succeeds (when Docker Desktop is on)
- [ ] Docker tests pass (when Docker Desktop is on)
- [ ] Git commit ready
- [ ] Jenkins pipeline ready

---

## 🎯 Next Steps

1. **Start server manually** in Terminal 1
2. **Run tests** in Terminal 2
3. **Verify all tests pass**
4. **Commit and push** changes
5. **Trigger Jenkins** pipeline

Once you run the tests, paste the **last few lines** of each test output here for final verification! 🚀


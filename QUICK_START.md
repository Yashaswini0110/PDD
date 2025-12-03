# Quick Start Guide - Running ClauseClear

## 🚀 Quick Commands

### 1. Start the Server

**Windows PowerShell:**
```powershell
cd "C:\Users\yasha\Desktop\pdd final"
uvicorn app:app --host 0.0.0.0 --port 5055
```

**Linux/macOS:**
```bash
cd /path/to/pdd\ final
uvicorn app:app --host 0.0.0.0 --port 5055
```

**With auto-reload (for development):**
```bash
uvicorn app:app --host 0.0.0.0 --port 5055 --reload
```

---

## 📋 Complete Setup (First Time Only)

### Step 1: Install Dependencies
```bash
cd "C:\Users\yasha\Desktop\pdd final"
pip install -r requirements.txt
```

### Step 2: Set Environment Variables
Create a `.env` file in the repo root with:
```
GEMINI_API_KEY=your_gemini_api_key_here
MONGO_URI=mongodb://localhost:27017
GEMINI_MODEL_NAME=gemini-2.0-flash
FIREBASE_API_KEY=your_firebase_key
FIREBASE_AUTH_DOMAIN=your_firebase_domain
FIREBASE_PROJECT_ID=your_firebase_project
FIREBASE_MESSAGING_SENDER_ID=your_sender_id
FIREBASE_APP_ID=your_app_id
```

### Step 3: Start the Server
```bash
uvicorn app:app --host 0.0.0.0 --port 5055
```

---

## 🌐 Access Points

Once the server is running:

- **Frontend:** http://localhost:5055/
- **API Docs (Swagger):** http://localhost:5055/docs
- **ReDoc:** http://localhost:5055/redoc
- **Health Check:** http://localhost:5055/health

---

## 🧪 Test Commands

### Run Tests (in a separate terminal)

**Severity Engine Test:**
```bash
python evaluate_severity.py
```

**Full Flow Test:**
```bash
python test_full_flow.py
```

**LLM Flow Test:**
```bash
python test_llm_flow.py
```

---

## 🐳 Docker Commands (Optional)

### Build Docker Image
```bash
docker build -t clauseclear-backend:clean-test .
```

### Run Docker Container
```bash
docker run --rm -p 5055:5055 --env-file .env clauseclear-backend:clean-test
```

---

## ⚙️ Common Commands

### Stop the Server
Press `Ctrl+C` in the terminal where uvicorn is running

### Check if Server is Running
```powershell
# Windows PowerShell
Invoke-WebRequest -Uri "http://localhost:5055/health"

# Linux/macOS
curl http://localhost:5055/health
```

### Check Port Usage
```powershell
# Windows PowerShell
Get-NetTCPConnection -LocalPort 5055

# Linux/macOS
lsof -i :5055
```

---

## 📝 Notes

- The server must stay running while you use the app
- Default port is **5055**
- MongoDB is optional (app works without it)
- GEMINI_API_KEY is required for LLM features
- Test PDF file: `sample.1.pdf` is in the repo root

---

## 🆘 Troubleshooting

### Port Already in Use
```powershell
# Find and stop process using port 5055
$port = Get-NetTCPConnection -LocalPort 5055 -ErrorAction SilentlyContinue
if ($port) { Stop-Process -Id $port.OwningProcess -Force }
```

### Dependencies Not Installed
```bash
pip install -r requirements.txt
```

### Server Won't Start
- Check if Python 3.11 is installed: `python --version`
- Check if all dependencies are installed
- Verify `.env` file exists (optional, but recommended)


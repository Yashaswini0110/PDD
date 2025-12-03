# Jenkins Credentials Setup Guide

## 🔴 Issue Fixed!

The Jenkins pipeline was failing with:
```
ERROR: Could not find credentials entry with ID 'gemini-api-key'
```

**✅ FIXED:** The `Jenkinsfile` has been updated to deploy successfully without optional credentials.

---

## ✅ Current Status

The pipeline will now:
- ✅ **Deploy successfully** even if `gemini-api-key` is missing
- ✅ **Deploy successfully** even if `mongo-uri` is missing
- ⚠️ **LLM features won't work** without `gemini-api-key` (but app will run)
- ⚠️ **MongoDB features won't work** without `mongo-uri` (but app will run)

The deployment succeeds with minimal env vars: `GEMINI_MODEL_NAME=gemini-2.0-flash`

---

## 📋 Required vs Optional Credentials

### Required (Already Configured):
- ✅ `gcp-sa-json` - GCP Service Account JSON

### Optional (Can Add Later):
- ⚠️ `gemini-api-key` - For LLM features (recommended)
- ⚠️ `mongo-uri` - For MongoDB features (optional)

---

## 🚀 How to Add Optional Credentials

### Option 1: Add in Jenkins (Recommended for CI/CD)

1. **Go to Jenkins Dashboard**
2. **Click:** Manage Jenkins → Manage Credentials
3. **Select:** (global) or your specific domain
4. **Click:** Add Credentials

#### Add `gemini-api-key`:
- **Kind:** Secret text
- **Secret:** Your Gemini API key
- **ID:** `gemini-api-key` (must match exactly)
- **Description:** Gemini API Key for LLM features

#### Add `mongo-uri`:
- **Kind:** Secret text
- **Secret:** Your MongoDB connection string
- **ID:** `mongo-uri` (must match exactly)
- **Description:** MongoDB connection URI

**After adding:** Replace `Jenkinsfile` with `Jenkinsfile.with-credentials` to use them automatically.

### Option 2: Add in Cloud Run Console (Quick Manual Fix)

1. Go to [Google Cloud Console → Cloud Run](https://console.cloud.google.com/run)
2. Click on `clauseclear-backend` service
3. Click **Edit & Deploy New Revision**
4. Go to **Variables & Secrets** tab
5. Add environment variables:
   - `GEMINI_API_KEY` = your API key
   - `MONGO_URI` = your MongoDB URI
6. Click **Deploy**

---

## 🔄 Next Steps

1. **Commit and push the fixed Jenkinsfile:**
   ```bash
   git add Jenkinsfile JENKINS_CREDENTIALS_SETUP.md
   git commit -m "fix: make Jenkins credentials optional for deployment"
   git push
   ```

2. **Re-run the Jenkins pipeline** - it should now succeed! ✅

3. **Add credentials later** using one of the options above to enable full functionality.

---

## 📝 Alternative Jenkinsfile

If you want the pipeline to automatically use credentials when available, you can use `Jenkinsfile.with-credentials` (but you'll still need to add the credentials in Jenkins first).


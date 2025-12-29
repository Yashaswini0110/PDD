FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Default port (Cloud Run will override PORT env var if needed)
ENV PORT=5055

# Use Python to read PORT env var (Cloud Run-safe, no shell expansion)
# Reads PORT from environment with fallback to 5055 for local development
CMD ["python", "-c", "import os; import subprocess; port = int(os.getenv('PORT', '5055')); subprocess.run(['uvicorn', 'app:app', '--host', '0.0.0.0', '--port', str(port)])"]
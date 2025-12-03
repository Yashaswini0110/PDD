FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=5055

# Use PORT env var for Cloud Run compatibility (Cloud Run sets PORT dynamically)
CMD sh -c "uvicorn app:app --host 0.0.0.0 --port ${PORT:-5055}"
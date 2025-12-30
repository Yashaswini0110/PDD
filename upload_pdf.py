import requests
from pathlib import Path

import sys

# Get the file path from command line arguments
if len(sys.argv) < 2:
    print("Usage: python upload_pdf.py <path_to_your_document.pdf_or_docx>")
    sys.exit(1)

document_path = Path(sys.argv[1])
url = "http://127.0.0.1:5055/files/upload"

if not document_path.exists():
    print(f"Error: Document not found at {document_path}")
    sys.exit(1)

# Determine content type based on file extension
file_extension = document_path.suffix.lower()
if file_extension == ".pdf":
    content_type = "application/pdf"
elif file_extension == ".docx":
    content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
else:
    print(f"Error: Unsupported file type '{file_extension}'. Only PDF and DOCX are allowed.")
    sys.exit(1)

with open(document_path, "rb") as f:
    files = {'file': (document_path.name, f, content_type)}
    response = requests.post(url, files=files)
    response.raise_for_status() # Raise an exception for HTTP errors
    data = response.json()
    print(f"Upload successful: {data}")
    print(f"Job ID: {data['job_id']}")

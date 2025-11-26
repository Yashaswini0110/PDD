from PyPDF2 import PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from pathlib import Path
import io

def create_pdf_with_text(output_path: Path, text_content: str):
    c = canvas.Canvas(str(output_path), pagesize=letter)
    y_coordinate = 750 # Starting Y coordinate
    for line in text_content.split('\n'):
        c.drawString(50, y_coordinate, line)
        y_coordinate -= 14 # Move down for next line
    c.showPage()
    c.save()

    print(f"Created PDF with text at {output_path.resolve()}")

if __name__ == "__main__":
    sample_text = """
    This is a sample document for testing purposes.
    It contains several sentences that can be split into clauses.
    The quick brown fox jumps over the lazy dog.
    Security deposit is required for all new tenants.
    The lease agreement specifies the terms and conditions.
    Payment must be made by the first of each month.
    Failure to comply may result in penalties.
    """
    create_pdf_with_text(Path("dummy_with_text.pdf"), sample_text)
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
    This is a general clause and has no specific risk.
    The tenant must provide a notice period of 1 month before vacating the premises.
    The landlord reserves the right to terminate this agreement at their sole discretion with a 7-day notice.
    A security deposit of 5 months' rent is required for all new tenants. There is a 6-month lock-in period.
    The late fee for rent payments will be 5% of the monthly rent.
    """
    create_pdf_with_text(Path("dummy_with_text.pdf"), sample_text)
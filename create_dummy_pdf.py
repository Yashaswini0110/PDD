from PyPDF2 import PdfWriter
from pathlib import Path

writer = PdfWriter()
writer.add_blank_page(72, 72)
writer.add_blank_page(72, 72)
writer.add_blank_page(72, 72)

output_path = Path("dummy.pdf")
with open(output_path, "wb") as f:
    writer.write(f)

print(f"Created dummy PDF at {output_path.resolve()}")
import os
from io import BytesIO
from PyPDF2 import PdfMerger
from PIL import Image


def merge_files(files, output_path):
    merger = PdfMerger()
    temp_buffers = []

    os.makedirs("output", exist_ok=True)

    for f in files:

        # CAS PDF
        if f.lower().endswith(".pdf"):
            merger.append(f)

        # CAS IMAGE
        else:
            img = Image.open(f).convert("RGB")
            img.thumbnail((1200, 1200))

            temp_pdf = BytesIO()
            img.save(temp_pdf, "PDF", resolution=100.0)
            temp_pdf.seek(0)

            temp_buffers.append(temp_pdf)
            merger.append(temp_pdf)

    merger.write(output_path)
    merger.close()

    for buf in temp_buffers:
        try:
            buf.close()
        except Exception:
            pass
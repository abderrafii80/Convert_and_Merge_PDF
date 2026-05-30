import os
from PIL import Image

def compress_image(input_path, output_path, quality=50):
    img = Image.open(input_path).convert("RGB")
    img.thumbnail((1200, 1200))

    img.save(output_path, "JPEG", quality=quality, optimize=True)
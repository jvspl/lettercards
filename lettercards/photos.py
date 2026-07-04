"""Prepare a photo for use as a card image.

Fixes EXIF orientation, crops to a square (biased toward the top for
portrait shots, where faces usually are), resizes, and saves as PNG.
"""

from pathlib import Path

from PIL import Image, ImageOps

DEFAULT_SIZE = 800  # card image area is ~5.2cm; 800px leaves 300dpi headroom


def process_photo(source: Path, output: Path, size: int = DEFAULT_SIZE) -> Path:
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Portrait shots crop from the top (faces); landscape crops center.
    w, h = img.size
    centering = (0.5, 0.0) if h > w else (0.5, 0.5)
    img = ImageOps.fit(img, (size, size), Image.LANCZOS, centering=centering)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "PNG")
    return output

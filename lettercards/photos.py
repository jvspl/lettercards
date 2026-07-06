"""Prepare a photo for use as a card image.

Fixes EXIF orientation, crops to a square (biased toward the top for
portrait shots, where faces usually are), resizes, and saves as PNG.
"""

from collections import deque
from pathlib import Path

from PIL import Image, ImageOps

PHOTO_SIZE = 800      # card image area is ~5.2cm; 800px leaves 300dpi headroom
PICTOGRAM_SIZE = 800  # ~300dpi in the image area; existing 400px starter images
                      # are upgraded opportunistically when regenerated
CARD_CREAM = (255, 248, 240)


def flatten_background(img: Image.Image, tol: int = 45) -> Image.Image:
    """Flood-fill near-cream background to exactly the card cream.

    Fills only the region connected to the borders, so subject-interior
    highlights survive; generated pictograms often carry low-amplitude
    background mottling. (Hand-rolled BFS: ImageDraw.floodfill refuses
    to fill when the target color is within thresh of the seed.)
    """
    px = img.load()
    w, h = img.size

    def near(p):
        return sum(abs(a - b) for a, b in zip(p, CARD_CREAM)) <= tol

    seen = bytearray(w * h)
    queue = deque()
    for x, y in ([(x, y) for x in range(w) for y in (0, h - 1)]
                 + [(x, y) for x in (0, w - 1) for y in range(h)]):
        if not seen[y * w + x] and near(px[x, y]):
            seen[y * w + x] = 1
            queue.append((x, y))
    while queue:
        x, y = queue.popleft()
        px[x, y] = CARD_CREAM
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < w and 0 <= ny < h and not seen[ny * w + nx] and near(px[nx, ny]):
                seen[ny * w + nx] = 1
                queue.append((nx, ny))
    return img


def process_photo(source: Path, output: Path, size: int | None = None,
                  pictogram: bool = False) -> Path:
    img = Image.open(source)
    img = ImageOps.exif_transpose(img)
    if img.mode != "RGB":
        img = img.convert("RGB")
    # Portrait shots crop from the top (faces); landscape crops center.
    w, h = img.size
    centering = (0.5, 0.0) if h > w else (0.5, 0.5)
    size = size or (PICTOGRAM_SIZE if pictogram else PHOTO_SIZE)
    img = ImageOps.fit(img, (size, size), Image.LANCZOS, centering=centering)
    if pictogram:
        img = flatten_background(img)
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "PNG")
    return output

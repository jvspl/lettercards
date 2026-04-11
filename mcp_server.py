#!/usr/bin/env python3
"""
Lettercards MCP Server

Tools for any MCP-capable AI to guide the personal photo card workflow:
- Open a native file picker to select candidate photos
- Preview candidates as a numbered thumbnail grid (AI selects best 2-3)
- Render selected photos as actual lettercards for final comparison
- Save the chosen photo to the personal library

Setup: see docs/mcp-setup.md
Run via: venv-mcp/bin/python mcp_server.py
"""

import io
import os
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Image as MCPImage
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_DIR     = Path(__file__).parent
PERSONAL_DIR = (
    Path(os.environ['LETTERCARDS_PERSONAL_DIR'])
    if 'LETTERCARDS_PERSONAL_DIR' in os.environ
    else Path.home() / '.lettercards' / 'personal'
)
STAGING_DIR = (
    Path(os.environ['LETTERCARDS_STAGING_DIR'])
    if 'LETTERCARDS_STAGING_DIR' in os.environ
    else Path.home() / '.lettercards' / 'staging'
)
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.heic', '.webp'}

# ── Card rendering constants (matches generate.py) ────────────────────────────

CARD_W, CARD_H = 300, 450
BG_PICTURE     = (245, 242, 225)   # warm cream
CORNER_R       = 16
DEFAULT_COLOR  = (220, 100, 40)    # orange fallback

# Letter accent colours — same palette as generate.py
LETTER_COLORS = {
    'a': (220, 80,  50),  'b': (50,  120, 200), 'c': (180, 140, 40),
    'd': (80,  160, 80),  'e': (200, 80,  150), 'f': (100, 60,  180),
    'g': (220, 120, 40),  'h': (40,  160, 160), 'i': (180, 60,  60),
    'j': (60,  140, 100), 'k': (160, 40,  120), 'l': (40,  100, 200),
    'm': (200, 140, 40),  'n': (80,  60,  180), 'o': (60,  160, 120),
    'p': (180, 80,  40),  'q': (120, 40,  160), 'r': (40,  140, 60),
    's': (200, 60,  100), 't': (60,  120, 200), 'u': (160, 160, 40),
    'v': (120, 80,  160), 'w': (40,  160, 80),  'x': (200, 100, 60),
    'y': (80,  40,  200), 'z': (60,  180, 140),
}

# ── Fonts (cross-platform) ────────────────────────────────────────────────────

# Searched in order; first match wins. PIL default is the final fallback.
_FONT_CANDIDATES = [
    str(REPO_DIR / "fonts" / "DejaVuSans-Bold.ttf"),           # in-repo (any OS)
    # macOS
    "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "/System/Library/Fonts/Helvetica.ttc",
    # Linux
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    # Windows
    "C:/Windows/Fonts/arialbd.ttf",
    "C:/Windows/Fonts/calibrib.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for path in _FONT_CANDIDATES:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ── MCP server ────────────────────────────────────────────────────────────────

mcp = FastMCP("lettercards", instructions="""
You are helping select and process personal photos for letter learning cards.

## Workflow

**Step 1 — pick photos:** Call pick_photos(name). A native file picker opens and
the user selects candidate photos from anywhere on their computer.
The tool returns a numbered list of absolute file paths.

**Step 2 — evaluate and compare:**
- 1–3 photos selected: call generate_comparison(name, file_paths) immediately.
- 4+ photos selected: call generate_photo_grid(file_paths) first. Evaluate the
  returned grid image with your vision — look for face clearly visible, clean
  background, good lighting. Pick the best 2–3, then call
  generate_comparison(name, best_file_paths) with only those.

**Step 3 — present:** After generate_comparison returns, tell the user to expand
the tool output section in their AI client to see the rendered card previews.
Add a brief note on each candidate (lighting, face visibility, background).

**Step 4 — save:** When the user confirms a choice, call save_photo(name, file_path)
with the path of the chosen photo. Report the path where it was saved and the
generate command to rebuild the PDF.

## Quality criteria

A good card photo: face clearly visible, person recognisable, clean or simple
background preferred. Cards are for a toddler learning letter-sound associations.

## Fallback: directory listing

If the file picker cannot open (headless / no display), call
pick_photos(name, directory="/path/to/photos") to list photos from a directory.
""")


# ── Image processing ──────────────────────────────────────────────────────────

def _normalise(img: Image.Image) -> Image.Image:
    """Normalise colour mode and correct EXIF orientation."""
    if img.mode in ('RGBA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        img = img.convert('RGBA')
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    try:
        from PIL import ExifTags
        orientation_tag = next(
            tag for tag, name in ExifTags.TAGS.items() if name == 'Orientation'
        )
        exif = img._getexif()
        if exif:
            val = exif.get(orientation_tag)
            if val == 3:   img = img.rotate(180, expand=True)
            elif val == 6: img = img.rotate(270, expand=True)
            elif val == 8: img = img.rotate(90,  expand=True)
    except Exception:
        pass

    return img


def _crop_and_enhance(img: Image.Image, size: int = 400) -> Image.Image:
    """Crop to square, resize, auto-enhance."""
    w, h = img.size
    if h > w:
        img = img.crop((0, 0, w, w))               # portrait: top crop
    else:
        s = min(w, h)
        img = img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))  # landscape: centre
    img = img.resize((size, size), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Sharpness(img).enhance(1.3)
    return img


def load_and_process(file_path: str, size: int = 400) -> Image.Image:
    """Load from file, correct orientation, crop to square, auto-enhance."""
    img = Image.open(Path(file_path).expanduser())
    return _crop_and_enhance(_normalise(img), size)


def decode_and_process(image_data: str, size: int = 400) -> Image.Image:
    """Decode base64 image, correct orientation, crop to square, auto-enhance.

    Kept for backward compatibility and testing.
    New tools use load_and_process() directly.
    """
    import base64
    img = Image.open(io.BytesIO(base64.b64decode(image_data)))
    return _crop_and_enhance(_normalise(img), size)


def render_card(photo: Image.Image, word: str) -> Image.Image:
    """Render a picture card with the given photo and word label."""
    letter = word[0].lower()
    color  = LETTER_COLORS.get(letter, DEFAULT_COLOR)

    card = Image.new('RGB', (CARD_W, CARD_H), BG_PICTURE)
    draw = ImageDraw.Draw(card)

    # Rounded-rect background mask
    mask = Image.new('L', (CARD_W, CARD_H), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, CARD_W-1, CARD_H-1], radius=CORNER_R, fill=255)
    card.putalpha(mask)

    # Photo — upper portion of card
    pad      = 16
    img_size = CARD_W - 2 * pad
    photo_rs = photo.resize((img_size, img_size), Image.LANCZOS)
    photo_y  = int(CARD_H * 0.06)
    card.paste(photo_rs, (pad, photo_y))

    # Word label — first letter in accent colour, rest dark
    font       = _load_font(28)
    badge_font = _load_font(14)
    word_y     = int(CARD_H * 0.80)
    first      = word[0]
    rest       = word[1:]

    bbox_first = draw.textbbox((0, 0), first, font=font)
    bbox_rest  = draw.textbbox((0, 0), rest,  font=font)
    w_first    = bbox_first[2] - bbox_first[0]
    w_rest     = bbox_rest[2]  - bbox_rest[0]
    text_x     = (CARD_W - w_first - w_rest) // 2

    draw.text((text_x,           word_y), first, fill=color,        font=font)
    draw.text((text_x + w_first, word_y), rest,  fill=(40, 40, 40), font=font)

    # Letter badge — top-left corner
    badge_r = 12
    draw.ellipse([8, 8, 8+badge_r*2, 8+badge_r*2], fill=color)
    bb = draw.textbbox((0, 0), letter, font=badge_font)
    bx = 8 + badge_r - (bb[2]-bb[0])//2
    by = 8 + badge_r - (bb[3]-bb[1])//2
    draw.text((bx, by), letter, fill=(255, 255, 255), font=badge_font)

    return card


def _pil_to_mcp(img: Image.Image) -> MCPImage:
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return MCPImage(data=buf.getvalue(), format='png')


def _open_file_picker(title: str) -> list[str]:
    """Open a native OS file picker dialog. Returns list of selected paths."""
    import tkinter as tk
    from tkinter import filedialog

    root = tk.Tk()
    root.withdraw()
    try:
        root.wm_attributes('-topmost', True)  # bring dialog to front on macOS/Windows
    except Exception:
        pass
    paths = filedialog.askopenfilenames(
        title=title,
        filetypes=[
            ("Images", "*.jpg *.jpeg *.png *.heic *.webp *.JPG *.JPEG *.PNG *.HEIC *.WEBP"),
            ("All files", "*.*"),
        ],
    )
    root.destroy()
    return list(paths)


# ── Tools ─────────────────────────────────────────────────────────────────────

@mcp.tool()
def pick_photos(name: str, directory: str | None = None) -> str:
    """
    Select candidate photos for a letter card.

    Opens a native OS file picker dialog so the user can choose photos from
    anywhere on their computer. Returns a numbered list of absolute paths that
    you can pass directly to generate_photo_grid() or generate_comparison().

    If the file picker is unavailable (headless environment / no display),
    provide a directory path and this tool will list all photos found there.

    Args:
        name:      Person's name — used in the dialog title.
        directory: Optional. List photos from this directory instead of
                   opening a picker dialog. Use in headless environments or
                   when photos are already in a known folder.
    """
    if directory is not None:
        d = Path(directory).expanduser()
        if not d.is_dir():
            return f"Directory not found: {d}"
        photos = sorted(p for p in d.iterdir() if p.suffix.lower() in SUPPORTED_FORMATS)
        if not photos:
            return f"No photos found in {d}."
        lines = [f"Found {len(photos)} photo(s) in {d}:"]
        for i, p in enumerate(photos, 1):
            lines.append(f"  {i}. {p}")
        return "\n".join(lines)

    try:
        paths = _open_file_picker(f"Select candidate photos for '{name}'")
    except Exception as exc:
        return (
            f"File picker unavailable ({exc}).\n"
            f"Use: pick_photos(name='{name}', directory='/path/to/photos')"
        )

    if not paths:
        return "No photos selected."

    lines = [f"Selected {len(paths)} photo(s):"]
    for i, p in enumerate(paths, 1):
        lines.append(f"  {i}. {p}")
    return "\n".join(lines)


@mcp.tool()
def generate_photo_grid(file_paths: list[str]) -> MCPImage:
    """
    Render a numbered thumbnail grid of the raw candidate photos.

    Use this when 4 or more photos were selected so you can evaluate them
    with your vision before deciding which 2–3 to render as full lettercards.

    Evaluate the grid and pick the best candidates based on:
    - Face clearly visible and well-framed
    - Clean or simple background
    - Good lighting — no heavy shadows or overexposure

    The numbers in the grid match the position in file_paths (1-indexed).
    Pass the corresponding paths of your picks to generate_comparison().

    Args:
        file_paths: Ordered list of absolute paths (as returned by pick_photos).
    """
    CELL  = 200
    PAD   = 8
    COLS  = 3
    LABEL = 28
    font  = _load_font(13)
    fn    = _load_font(18)

    rows   = (len(file_paths) + COLS - 1) // COLS
    cell_w = CELL + PAD * 2
    cell_h = CELL + LABEL + PAD * 2
    grid   = Image.new('RGB', (COLS * cell_w, rows * cell_h), (230, 228, 215))
    draw   = ImageDraw.Draw(grid)

    for i, path_str in enumerate(file_paths):
        col = i % COLS
        row = i // COLS
        x   = col * cell_w + PAD
        y   = row * cell_h + PAD
        num = str(i + 1)

        try:
            thumb = _normalise(Image.open(Path(path_str).expanduser()))
            tw, th = thumb.size
            s = min(tw, th)
            thumb = thumb.crop(((tw-s)//2, (th-s)//2, (tw+s)//2, (th+s)//2))
            thumb = thumb.resize((CELL, CELL), Image.LANCZOS)
            grid.paste(thumb, (x, y))
        except Exception:
            draw.rectangle([x, y, x+CELL, y+CELL], fill=(180, 175, 165))
            draw.text((x+4, y+4), f"error: {Path(path_str).name}", fill=(80, 70, 60), font=font)

        # Number badge
        draw.rectangle([x, y, x+24, y+22], fill=DEFAULT_COLOR)
        draw.text((x+3, y+2), num, fill=(255, 255, 255), font=fn)

        # Filename label
        short = Path(path_str).name
        if len(short) > 30:
            short = short[:27] + '...'
        draw.text((x+2, y+CELL+4), short, fill=(60, 55, 50), font=font)

        # Border
        draw.rectangle([x, y, x+CELL, y+CELL], outline=(170, 165, 155))

    return _pil_to_mcp(grid)


@mcp.tool()
def generate_comparison(name: str, file_paths: list[str]) -> MCPImage:
    """
    Render 2–4 photos as actual lettercards side-by-side for final comparison.

    Call this after selecting candidates — either directly from the pick_photos
    result (1–3 photos) or after narrowing down with generate_photo_grid (4+).

    The returned image shows each photo rendered as a real lettercard so the
    user can see exactly how it will look when printed.

    Args:
        name:       Person's name as it will appear on the card label.
        file_paths: 1–4 absolute paths to the candidate photos.
    """
    PAD   = 12
    cards = []
    for path_str in file_paths:
        photo = load_and_process(path_str)
        cards.append(render_card(photo, name))

    total_w = sum(c.width for c in cards) + PAD * (len(cards) + 1)
    total_h = max(c.height for c in cards) + PAD * 2
    grid    = Image.new('RGB', (total_w, total_h), (230, 228, 215))

    x = PAD
    for card in cards:
        if card.mode == 'RGBA':
            bg = Image.new('RGB', card.size, (230, 228, 215))
            bg.paste(card, mask=card.split()[-1])
            card = bg
        grid.paste(card, (x, PAD))
        x += card.width + PAD

    return _pil_to_mcp(grid)


@mcp.tool()
def save_photo(name: str, file_path: str) -> str:
    """
    Save the chosen photo to the personal library.

    Call this once the user has confirmed which photo to use. The photo is
    processed (orientation-corrected, cropped to square, auto-enhanced) and
    saved to the personal photo directory.

    Args:
        name:      Person's name — saved as {name}.png (lowercased).
        file_path: Absolute path to the chosen photo on disk.
    """
    photo = load_and_process(file_path)
    PERSONAL_DIR.mkdir(parents=True, exist_ok=True)
    out = PERSONAL_DIR / f"{name.lower()}.png"
    photo.save(out, 'PNG')
    return (
        f"Saved to {out}\n"
        f"To regenerate the PDF: lettercards generate --letters {name[0].lower()}"
    )


@mcp.tool()
def list_staging_photos() -> str:
    """
    List photos in the staging folder (~/.lettercards/staging/).

    Fallback for users who prefer copying photos to a staging folder rather
    than using the file picker. Returns a numbered list of paths you can pass
    to generate_comparison() or generate_photo_grid().
    """
    if not STAGING_DIR.exists():
        return f"Staging folder not found: {STAGING_DIR}"
    photos = sorted(p for p in STAGING_DIR.iterdir() if p.suffix.lower() in SUPPORTED_FORMATS)
    if not photos:
        return f"No photos in {STAGING_DIR}."
    lines = [f"Found {len(photos)} photo(s) in {STAGING_DIR}:"]
    for i, p in enumerate(photos, 1):
        lines.append(f"  {i}. {p}  ({p.stat().st_size // 1024} KB)")
    return "\n".join(lines)


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    mcp.run(transport='stdio')

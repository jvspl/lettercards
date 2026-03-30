#!/usr/bin/env python3
"""
Lettercards MCP Server

Exposes tools for Claude Desktop to guide the personal photo card workflow:
- Drop photos into the Claude Desktop conversation
- Claude calls generate_card_preview() to see the actual card
- Claude calls save_photo() when you confirm

Setup: see docs/mcp-setup.md
Run via: venv-mcp/bin/python mcp_server.py
"""

import base64
import io
import os
import subprocess
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Image as MCPImage
from PIL import Image, ImageDraw, ImageEnhance, ImageFont, ImageOps

# ── Paths ────────────────────────────────────────────────────────────────────

REPO_DIR    = Path(__file__).parent
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

# ── Card rendering constants (matches generate.py) ──────────────────────────

CARD_W, CARD_H = 300, 450          # px at preview resolution
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

# ── MCP server ───────────────────────────────────────────────────────────────

mcp = FastMCP("lettercards", instructions="""
You are helping select and process personal photos for Dutch letter learning cards.

Workflow:
1. Call list_staging_photos() to see what photos are in the staging folder
2. Call generate_card_preview() for each photo to review them all
3. Pick your top 2–4 candidates based on face visibility and crop quality
4. Call generate_comparison() with those top picks — this shows them side-by-side
5. Recommend the best one with brief reasoning
6. When the user confirms, call save_photo() with that file_path

Photos must be on disk in the staging folder (~/.lettercards/staging/).
Do NOT ask the user to upload photos inline — that does not work with these tools.
If staging is empty, tell the user to copy photos there first.

The cards are for a toddler (Lena, ~2 years old) learning letter-sound associations.
A good card photo: face clearly visible, person recognisable, clean background preferred.

Note: card preview images appear inside the "Used lettercards integration" section in
Claude Desktop — not inline in the chat. Always tell the user to click that section header
to expand it and see the cards. Say something like: "Click 'Used lettercards integration'
above to see the card previews."
""")

# ── Image processing ─────────────────────────────────────────────────────────

def decode_and_process(image_data: str, size: int = 400) -> Image.Image:
    """Decode base64 image, correct orientation, crop to square, auto-enhance."""
    img = Image.open(io.BytesIO(base64.b64decode(image_data)))

    # Normalise colour mode
    if img.mode in ('RGBA', 'P'):
        bg = Image.new('RGB', img.size, (255, 255, 255))
        img = img.convert('RGBA')
        bg.paste(img, mask=img.split()[-1])
        img = bg
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # EXIF orientation
    try:
        from PIL import ExifTags
        for tag in ExifTags.TAGS:
            if ExifTags.TAGS[tag] == 'Orientation':
                break
        exif = img._getexif()
        if exif:
            val = exif.get(tag)
            if val == 3:   img = img.rotate(180, expand=True)
            elif val == 6: img = img.rotate(270, expand=True)
            elif val == 8: img = img.rotate(90,  expand=True)
    except Exception:
        pass

    w, h = img.size
    if h > w:
        img = img.crop((0, 0, w, w))          # portrait: top crop
    else:
        s = min(w, h)
        img = img.crop(((w-s)//2, (h-s)//2, (w+s)//2, (h+s)//2))  # landscape: centre

    img = img.resize((size, size), Image.LANCZOS)
    img = ImageOps.autocontrast(img, cutoff=2)
    img = ImageEnhance.Sharpness(img).enhance(1.3)
    return img


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

    # Photo — centred in upper 68% of card
    pad        = 16
    img_size   = CARD_W - 2 * pad
    photo_rs   = photo.resize((img_size, img_size), Image.LANCZOS)
    photo_y    = int(CARD_H * 0.06)
    card.paste(photo_rs, (pad, photo_y))

    # Word label — first letter in accent colour, rest dark
    try:
        font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
    except Exception:
        font = ImageFont.load_default()

    word_y = int(CARD_H * 0.80)
    first  = word[0]
    rest   = word[1:]

    # Measure to centre
    bbox_first = draw.textbbox((0, 0), first, font=font)
    bbox_rest  = draw.textbbox((0, 0), rest,  font=font)
    w_first    = bbox_first[2] - bbox_first[0]
    w_rest     = bbox_rest[2]  - bbox_rest[0]
    total_w    = w_first + w_rest
    text_x     = (CARD_W - total_w) // 2

    draw.text((text_x,           word_y), first, fill=color,         font=font)
    draw.text((text_x + w_first, word_y), rest,  fill=(40, 40, 40),  font=font)

    # Small letter badge — top-left corner
    try:
        badge_font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 14)
    except Exception:
        badge_font = ImageFont.load_default()

    badge_r = 12
    draw.ellipse([8, 8, 8+badge_r*2, 8+badge_r*2], fill=color)
    bb = draw.textbbox((0, 0), letter, font=badge_font)
    bx = 8 + badge_r - (bb[2]-bb[0])//2
    by = 8 + badge_r - (bb[3]-bb[1])//2
    draw.text((bx, by), letter, fill=(255, 255, 255), font=badge_font)

    return card


def pil_to_mcp_image(img: Image.Image) -> MCPImage:
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    return MCPImage(data=buf.getvalue(), format='png')


# ── Tools ────────────────────────────────────────────────────────────────────

@mcp.tool()
def list_staging_photos() -> str:
    """
    List photos available in the staging folder (~/.lettercards/staging/).
    Call this first to see what photos are available before generating previews.
    Returns a list of file paths you can pass to generate_card_preview().
    """
    if not STAGING_DIR.exists():
        return f"Staging folder does not exist: {STAGING_DIR}\nAsk the user to create it and copy photos there."
    extensions = {'.jpg', '.jpeg', '.png', '.heic', '.webp'}
    photos = sorted(p for p in STAGING_DIR.iterdir() if p.suffix.lower() in extensions)
    if not photos:
        return f"No photos found in {STAGING_DIR}\nAsk the user to copy photos there first."
    lines = [f"Found {len(photos)} photo(s) in {STAGING_DIR}:"]
    for p in photos:
        size_kb = p.stat().st_size // 1024
        lines.append(f"  {p}  ({size_kb} KB)")
    return "\n".join(lines)


@mcp.tool()
def generate_card_preview(name: str, file_path: str) -> MCPImage:
    """
    Process a photo and render it as an actual letter card preview.
    Call this for each candidate photo so the user can compare real cards.

    Args:
        name: Person's name as it should appear on the card (e.g. 'Tata', 'mama')
        file_path: Absolute path to the image file on disk (JPEG or PNG)
    """
    image_data = base64.b64encode(Path(file_path).read_bytes()).decode()
    photo = decode_and_process(image_data)
    card  = render_card(photo, name)
    return pil_to_mcp_image(card)


@mcp.tool()
def generate_comparison(name: str, file_paths: list[str]) -> MCPImage:
    """
    Render multiple photos as cards side-by-side for easy comparison.
    Call this with your top 2–4 candidates after reviewing all previews.
    Returns a single image showing all cards next to each other.

    Args:
        name: Person's name as it should appear on each card
        file_paths: List of absolute paths to the candidate photos
    """
    cards = []
    for fp in file_paths:
        image_data = base64.b64encode(Path(fp).read_bytes()).decode()
        photo = decode_and_process(image_data)
        cards.append(render_card(photo, name))

    pad = 12
    total_w = sum(c.width for c in cards) + pad * (len(cards) + 1)
    total_h = max(c.height for c in cards) + pad * 2

    grid = Image.new('RGB', (total_w, total_h), (230, 228, 215))
    x = pad
    for card in cards:
        # Strip alpha before pasting
        if card.mode == 'RGBA':
            bg = Image.new('RGB', card.size, (230, 228, 215))
            bg.paste(card, mask=card.split()[-1])
            card = bg
        grid.paste(card, (x, pad))
        x += card.width + pad

    return pil_to_mcp_image(grid)


@mcp.tool()
def save_photo(name: str, file_path: str) -> str:
    """
    Save the chosen photo to the personal library.
    Call this once the user has confirmed which photo to use.

    Args:
        name: Person's name — saved as {name}.png (e.g. 'tata' → tata.png)
        file_path: Absolute path to the chosen image file on disk
    """
    image_data = base64.b64encode(Path(file_path).read_bytes()).decode()
    photo = decode_and_process(image_data)
    PERSONAL_DIR.mkdir(parents=True, exist_ok=True)
    out = PERSONAL_DIR / f"{name.lower()}.png"
    photo.save(out, 'PNG')
    return f"Saved to {out}. Run: python generate.py --letters {name[0].lower()}"


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == '__main__':
    mcp.run(transport='stdio')

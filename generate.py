#!/usr/bin/env python3
"""
Letter Card Generator for Toddlers
Generates printable PDF cards from a CSV config + images folder.

Each word produces TWO cards:
  1. Picture card: image + word (first letter highlighted)
  2. Letter card: just the big letter

Cards are ~6x9cm (playing card size), laid out on A4 pages.

Usage:
    python generate.py                      # Generate all cards
    python generate.py --letters a,d,o      # Only specific letters
    python generate.py --font Lato          # Override font for all
    python generate.py --personal-dir /path # Override personal images location
    python generate.py --safe-letters-only  # Exclude letters with personal=yes cards

Personal images location (for photos marked personal=yes in CSV):
  1. CLI flag: --personal-dir /custom/path
  2. Environment variable: LETTERCARDS_PERSONAL_DIR=/custom/path
  3. Default: ~/.lettercards/personal/
"""

import csv
import os
import sys
import argparse
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.lib.colors import HexColor, white, black, Color
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

# ── Config ──────────────────────────────────────────────────────────

CARD_W = 6 * cm
CARD_H = 9 * cm
CORNER_R = 3 * mm          # rounded corner radius
PAGE_W, PAGE_H = A4

# Fixed 3x3 grid with uniform spacing for easy cutting
# Cut lines go through the middle of the gaps
# Edge margins = gap/2 so all cuts are equidistant
COLS = 3
ROWS = 3

# Calculate spacing to fill page uniformly
# Page = margin + card + gap + card + gap + card + margin
# Where margin = gap/2, so: gap/2 + card + gap + card + gap + card + gap/2
# = 3*card + 3*gap, therefore gap = (page - 3*card) / 3
SPACING_X = (PAGE_W - COLS * CARD_W) / COLS
SPACING_Y = (PAGE_H - ROWS * CARD_H) / ROWS

# Edge margins are half the inter-card spacing
MARGIN_X = SPACING_X / 2
MARGIN_Y = SPACING_Y / 2

# Colors
HIGHLIGHT_COLOR = HexColor("#E63946")   # red for the first letter
BG_PICTURE = HexColor("#FFF8F0")        # warm cream for picture cards
BG_LETTER = HexColor("#F0F7FF")         # light blue for letter cards
BORDER_COLOR = HexColor("#CCCCCC")
WORD_COLOR = HexColor("#2B2D42")

# Letter-specific accent colors (optional fun touch)
LETTER_COLORS = {
    'a': HexColor("#E63946"),  # red
    'b': HexColor("#457B9D"),  # blue
    'c': HexColor("#E9C46A"),  # yellow
    'd': HexColor("#2A9D8F"),  # teal
    'e': HexColor("#F4A261"),  # orange
    'f': HexColor("#6A4C93"),  # purple
    'g': HexColor("#1D3557"),  # dark blue
    'h': HexColor("#E76F51"),  # coral
    'i': HexColor("#264653"),  # dark teal
    'j': HexColor("#A8DADC"),  # light blue
    'k': HexColor("#F4A261"),  # orange
    'l': HexColor("#2A9D8F"),  # teal
    'm': HexColor("#E63946"),  # red
    'n': HexColor("#457B9D"),  # blue
    'o': HexColor("#E9C46A"),  # gold
    'p': HexColor("#6A4C93"),  # purple
    'r': HexColor("#E76F51"),  # coral
    's': HexColor("#2A9D8F"),  # teal
    't': HexColor("#F4A261"),  # orange
    'v': HexColor("#457B9D"),  # blue
    'w': HexColor("#1D3557"),  # dark blue
    'z': HexColor("#E63946"),  # red
}

# ── Font Setup ──────────────────────────────────────────────────────

FONT_DIR = Path(__file__).parent / "fonts"
SYSTEM_FONTS = {
    # macOS — visually distinct, child-friendly
    "ArialRounded": "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "ComicSans":    "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf",
    "GeorgiaBold":  "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "BradleyHand":  "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
    # Linux fallbacks
    "DejaVuSans":     "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "Lato":           "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "DejaVuSerif":    "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "Caladea":        "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf",
}

# Default rotation — ordered by visual distinctiveness.
# pick_font() filters to only registered fonts, so missing paths are skipped gracefully.
# macOS: rounded sans / playful / serif / handwritten — four clearly different styles
# Linux: sans / sans / serif / serif — better variety than four identical sans-serifs
DEFAULT_FONTS = [
    "ArialRounded", "ComicSans", "GeorgiaBold", "BradleyHand",  # macOS
    "DejaVuSerif", "Caladea", "DejaVuSans", "Lato",             # Linux
]


# ── Personal Images Directory ──────────────────────────────────────

def get_personal_images_dir(cli_arg=None):
    """Get personal images directory using layered config: CLI > env > default."""
    if cli_arg:
        return Path(cli_arg)
    if env_dir := os.environ.get('LETTERCARDS_PERSONAL_DIR'):
        return Path(env_dir)
    return Path.home() / '.lettercards' / 'personal'

def get_safe_letters(cards_csv_path):
    """Return the set of letters that have NO personal=yes entries in the CSV.

    Useful for generating screenshots or previews that must not include
    personal family photos. Any letter with at least one personal=yes word
    is considered unsafe and excluded from the result.
    """
    unsafe = set()
    all_letters = set()
    try:
        with open(cards_csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                letter = row.get('letter', '').strip()
                if not letter or letter.startswith('#'):
                    continue
                word = row.get('word', '').strip()
                if not word or 'geen voorbeeld' in word:
                    continue
                letter_lower = letter.lower()
                all_letters.add(letter_lower)
                if row.get('personal', 'no').strip().lower() == 'yes':
                    unsafe.add(letter_lower)
    except FileNotFoundError:
        return set()
    return all_letters - unsafe


def register_fonts():
    """Register system fonts and any custom fonts in fonts/ folder."""
    registered = []
    for name, path in SYSTEM_FONTS.items():
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered.append(name)
            except Exception:
                pass

    # Also register any TTF files dropped into fonts/
    if FONT_DIR.exists():
        for ttf in FONT_DIR.glob("*.ttf"):
            name = ttf.stem
            if name not in registered:
                try:
                    pdfmetrics.registerFont(TTFont(name, str(ttf)))
                    registered.append(name)
                except Exception:
                    pass

    return registered


def pick_font(word, font_override, available_fonts):
    """Pick a font for this card. Uses override, or rotates based on word hash."""
    if font_override and font_override in available_fonts:
        return font_override
    if not available_fonts:
        return "Helvetica"
    usable = [f for f in DEFAULT_FONTS if f in available_fonts] or available_fonts
    idx = hash(word) % len(usable)
    return usable[idx]


# ── Card Drawing ────────────────────────────────────────────────────

def draw_rounded_rect(c, x, y, w, h, r, fill_color, stroke_color=BORDER_COLOR):
    """Draw a rounded rectangle."""
    c.setStrokeColor(stroke_color)
    c.setLineWidth(0.5)
    c.setFillColor(fill_color)
    c.roundRect(x, y, w, h, r, fill=1, stroke=1)


def draw_picture_card(c, x, y, word, image_path, font_name, letter):
    """Draw a picture card: image + word with highlighted first letter."""
    # Background
    draw_rounded_rect(c, x, y, CARD_W, CARD_H, CORNER_R, BG_PICTURE)

    accent = LETTER_COLORS.get(letter, HIGHLIGHT_COLOR)

    # Image area (top portion)
    img_margin = 4 * mm
    img_area_x = x + img_margin
    img_area_y = y + CARD_H * 0.28
    img_area_w = CARD_W - 2 * img_margin
    img_area_h = CARD_H * 0.65

    if image_path and os.path.exists(image_path):
        try:
            # Get image dimensions to maintain aspect ratio
            with Image.open(image_path) as img:
                iw, ih = img.size
            aspect = iw / ih
            target_aspect = img_area_w / img_area_h

            if aspect > target_aspect:
                # Image is wider — fit to width
                draw_w = img_area_w
                draw_h = draw_w / aspect
            else:
                # Image is taller — fit to height
                draw_h = img_area_h
                draw_w = draw_h * aspect

            draw_x = img_area_x + (img_area_w - draw_w) / 2
            draw_y = img_area_y + (img_area_h - draw_h) / 2

            c.drawImage(image_path, draw_x, draw_y, draw_w, draw_h,
                        preserveAspectRatio=True, mask='auto')
        except Exception as e:
            # Fallback: draw placeholder
            draw_placeholder(c, img_area_x, img_area_y, img_area_w, img_area_h, word, accent)
    else:
        draw_placeholder(c, img_area_x, img_area_y, img_area_w, img_area_h, word, accent)

    # Word area (bottom portion)
    word_y = y + CARD_H * 0.08
    display_word = word.lower()
    first_letter = display_word[0]
    rest = display_word[1:]

    # Calculate font size to fit the card width
    max_width = CARD_W - 2 * img_margin
    font_size = 28
    while font_size > 12:
        first_w = pdfmetrics.stringWidth(first_letter, font_name, font_size)
        rest_w = pdfmetrics.stringWidth(rest, font_name, font_size)
        if first_w + rest_w <= max_width:
            break
        font_size -= 1

    total_w = pdfmetrics.stringWidth(first_letter, font_name, font_size) + \
              pdfmetrics.stringWidth(rest, font_name, font_size)
    text_x = x + (CARD_W - total_w) / 2

    # Draw first letter in accent color
    c.setFont(font_name, font_size)
    c.setFillColor(accent)
    c.drawString(text_x, word_y, first_letter)
    first_w = pdfmetrics.stringWidth(first_letter, font_name, font_size)

    # Draw rest of word in dark color
    c.setFillColor(WORD_COLOR)
    c.drawString(text_x + first_w, word_y, rest)

    # Badge: colored circle with white lowercase letter, top-left corner
    badge_r = 6 * mm
    badge_cx = x + 3 * mm + badge_r
    badge_cy = y + CARD_H - 3 * mm - badge_r
    c.setFillColor(accent)
    c.circle(badge_cx, badge_cy, badge_r, fill=1, stroke=0)
    badge_font_size = 16
    c.setFont(font_name, badge_font_size)
    c.setFillColor(white)
    lw = pdfmetrics.stringWidth(letter, font_name, badge_font_size)
    c.drawString(badge_cx - lw / 2, badge_cy - badge_font_size * 0.32, letter)

    # Uppercase badge in top-right corner — outlined circle, accent color letter
    upper = letter.upper()
    upper_cx = x + CARD_W - 3 * mm - badge_r
    upper_cy = badge_cy
    c.setStrokeColor(accent)
    c.setFillColor(white)
    c.circle(upper_cx, upper_cy, badge_r, fill=1, stroke=1)
    c.setFont(font_name, badge_font_size)
    c.setFillColor(accent)
    uw = pdfmetrics.stringWidth(upper, font_name, badge_font_size)
    c.drawString(upper_cx - uw / 2, upper_cy - badge_font_size * 0.32, upper)


def draw_letter_card(c, x, y, letter, font_name):
    """Draw a letter-only card: big letter centered."""
    accent = LETTER_COLORS.get(letter, HIGHLIGHT_COLOR)
    draw_rounded_rect(c, x, y, CARD_W, CARD_H, CORNER_R, BG_LETTER)

    # Big letter, centered
    font_size = 120
    c.setFont(font_name, font_size)
    letter_w = pdfmetrics.stringWidth(letter, font_name, font_size)

    # Center horizontally and vertically
    lx = x + (CARD_W - letter_w) / 2
    ly = y + (CARD_H - font_size * 0.7) / 2

    c.setFillColor(accent)
    c.drawString(lx, ly, letter)

    # Also show lowercase if the main display is uppercase, or vice versa
    small_size = 24
    c.setFont(font_name, small_size)
    other = letter.upper() if letter == letter.lower() else letter.lower()
    ow = pdfmetrics.stringWidth(other, font_name, small_size)
    c.setFillColor(Color(accent.red, accent.green, accent.blue, alpha=0.4))
    c.drawString(x + (CARD_W - ow) / 2, y + 5 * mm, other)


def draw_placeholder(c, x, y, w, h, word, accent):
    """Draw a simple placeholder with an emoji-style icon and text."""
    # Light background
    c.setFillColor(Color(accent.red, accent.green, accent.blue, alpha=0.08))
    c.roundRect(x, y, w, h, 2 * mm, fill=1, stroke=0)

    # Centered label: "[foto: word]"
    c.setFont("Helvetica", 10)
    c.setFillColor(Color(accent.red, accent.green, accent.blue, alpha=0.5))
    label = f"[foto: {word}]"
    lw = pdfmetrics.stringWidth(label, "Helvetica", 10)
    c.drawString(x + (w - lw) / 2, y + h / 2 - 5, label)


# ── Placeholder Image Generator ────────────────────────────────────

EMOJI_MAP = {
    'appel': '🍎', 'auto': '🚗', 'banaan': '🍌', 'beer': '🧸',
    'bal': '⚽', 'boom': '🌳', 'bad': '🛁', 'deur': '🚪',
    'draak': '🐉', 'druif': '🍇', 'eend': '🦆', 'fiets': '🚲',
    'huis': '🏠', 'hand': '✋', 'jas': '🧥', 'kat': '🐱',
    'koe': '🐄', 'leeuw': '🦁', 'lamp': '💡', 'melk': '🥛',
    'muis': '🐭', 'neus': '👃', 'oog': '👁', 'olifant': '🐘',
    'peer': '🍐', 'regen': '🌧', 'sok': '🧦', 'schoen': '👟',
    'tand': '🦷', 'tafel': '🪑', 'vis': '🐟', 'vlinder': '🦋',
    'water': '💧', 'zon': '☀️', 'zebra': '🦓',
}


def generate_placeholder_images(cards, images_dir):
    """Generate simple placeholder PNG images for cards that don't have one yet."""
    from PIL import Image, ImageDraw, ImageFont

    os.makedirs(images_dir, exist_ok=True)

    for card in cards:
        img_path = os.path.join(images_dir, card['image']) if card['image'] else None
        if not img_path or os.path.exists(img_path):
            continue
        if card['personal'] == 'yes':
            continue  # Don't generate placeholders for personal photos

        word = card['word'].lower()
        emoji = EMOJI_MAP.get(word, '?')

        # Create a simple image
        size = (400, 400)
        img = Image.new('RGB', size, '#FFFAF0')
        draw = ImageDraw.Draw(img)

        # Try to use a font that supports emoji, fall back to text
        try:
            # Draw emoji large
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/noto/NotoColorEmoji.ttf", 120)
            bbox = draw.textbbox((0, 0), emoji, font=font_large)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
            draw.text(((size[0] - tw) / 2, (size[1] - th) / 2 - 30), emoji, font=font_large, fill='black')
        except Exception:
            # Fallback: just draw text
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 100)
            except:
                font_large = ImageFont.load_default()
            draw.text((size[0] // 2, size[1] // 2 - 40), emoji, font=font_large, fill='#333', anchor='mm')

        img.save(img_path)
        print(f"  Created placeholder: {card['image']}")


# ── Main PDF Generation ────────────────────────────────────────────

def load_cards(csv_path, letters_filter=None):
    """Load card entries from CSV.

    Supports both legacy format (letter,word,image,font,personal) and the
    deck format that adds status, notes, language. Missing columns default
    to sensible values so old CSVs keep working.

    Cards with status 'retired' or 'pending' are skipped — they are not
    printed.
    """
    cards = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip comments
            letter = row.get('letter', '').strip()
            if not letter or letter.startswith('#'):
                continue
            word = row.get('word', '').strip()
            if not word or 'geen voorbeeld' in word:
                continue
            if letters_filter and letter.lower() not in letters_filter:
                continue
            status = row.get('status', 'active').strip()
            if status in ('retired', 'pending'):
                continue
            cards.append({
                'letter': letter.lower(),
                'word': word,
                'image': row.get('image', '').strip(),
                'font': row.get('font', '').strip(),
                'personal': row.get('personal', 'no').strip(),
                'status': status,
                'notes': row.get('notes', '').strip(),
                'language': row.get('language', 'nl').strip(),
            })
    return cards


def get_image_path(card, images_dir, personal_dir):
    """Get the image path for a card, checking personal dir first for personal photos."""
    if not card['image']:
        return None

    # For personal photos, check personal dir first
    if card['personal'] == 'yes':
        personal_path = personal_dir / card['image']
        if personal_path.exists():
            return str(personal_path)
        # Fall back to images/ if not found in personal dir

    # Check images/ folder
    images_path = os.path.join(images_dir, card['image'])
    if os.path.exists(images_path):
        return images_path

    return None


def generate_pdf(cards, output_path, images_dir, personal_dir, available_fonts, font_override=None):
    """Generate the printable PDF with all cards."""
    c = canvas.Canvas(str(output_path), pagesize=A4)
    c.setTitle("Letterkaarten")

    # We'll place cards in a grid. Each word produces 2 cards (picture + letter).
    # But letter cards can be deduplicated (one per unique letter).
    seen_letters = set()
    all_items = []  # list of (type, data) where type is 'picture' or 'letter'

    for card in cards:
        font_name = pick_font(card['word'], card['font'] or font_override, available_fonts)
        img_path = get_image_path(card, images_dir, personal_dir)

        all_items.append(('picture', card, font_name, img_path))

        if card['letter'] not in seen_letters:
            seen_letters.add(card['letter'])
            all_items.append(('letter', card, font_name, None))

    # Lay out cards on pages
    card_idx = 0
    total = len(all_items)

    while card_idx < total:
        # Start a new page
        for row in range(ROWS):
            for col in range(COLS):
                if card_idx >= total:
                    break

                x = MARGIN_X + col * (CARD_W + SPACING_X)
                y = PAGE_H - MARGIN_Y - (row + 1) * CARD_H - row * SPACING_Y

                item_type, card, font_name, img_path = all_items[card_idx]

                if item_type == 'picture':
                    draw_picture_card(c, x, y, card['word'], img_path, font_name, card['letter'])
                else:
                    draw_letter_card(c, x, y, card['letter'], font_name)

                card_idx += 1

        if card_idx < total:
            c.showPage()

    c.save()
    print(f"\n✓ Generated {output_path}")
    print(f"  {total} cards ({total - len(seen_letters)} picture + {len(seen_letters)} letter)")
    print(f"  Pages: {(total + COLS * ROWS - 1) // (COLS * ROWS)}")


def main():
    parser = argparse.ArgumentParser(description="Generate letter learning cards as PDF")
    parser.add_argument('--letters', type=str, default=None,
                        help='Comma-separated letters to include (e.g., a,d,o)')
    parser.add_argument('--font', type=str, default=None,
                        help='Override font for all cards')
    parser.add_argument('--output', type=str, default='letterkaarten.pdf',
                        help='Output PDF filename')
    parser.add_argument('--no-placeholders', action='store_true',
                        help='Skip generating placeholder images')
    parser.add_argument('--csv', type=str, default='deck.csv',
                        help='Path to the CSV config file')
    parser.add_argument('--personal-dir', type=str, default=None,
                        help='Directory for personal photos (default: ~/.lettercards/personal/)')
    parser.add_argument('--safe-letters-only', action='store_true',
                        help='Exclude any letter that has at least one personal=yes card (useful for screenshots)')
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    csv_path = base_dir / args.csv
    images_dir = base_dir / "images"
    personal_dir = get_personal_images_dir(args.personal_dir)
    output_path = base_dir / args.output

    # Register fonts
    available_fonts = register_fonts()
    print(f"Available fonts: {', '.join(available_fonts) or 'Helvetica (built-in)'}")

    # Parse letter filter
    letters_filter = None
    if args.safe_letters_only:
        safe = get_safe_letters(csv_path)
        letters_filter = sorted(safe)
        print(f"Safe letters (no personal=yes entries): {', '.join(letters_filter)}")
    elif args.letters:
        letters_filter = [l.strip().lower() for l in args.letters.split(',')]
        print(f"Filtering letters: {', '.join(letters_filter)}")

    # Load cards
    cards = load_cards(csv_path, letters_filter)
    if not cards:
        print("No cards found! Check your CSV file.")
        sys.exit(1)

    print(f"Loaded {len(cards)} card entries")

    # Generate placeholder images
    if not args.no_placeholders:
        print("\nGenerating placeholder images...")
        generate_placeholder_images(cards, images_dir)

    # Generate PDF
    print(f"\nPersonal images dir: {personal_dir}")
    print("Generating PDF...")
    generate_pdf(cards, output_path, images_dir, personal_dir, available_fonts, args.font)


if __name__ == '__main__':
    main()

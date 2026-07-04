"""Card design: 'Kleurblok' (chosen July 2026, v2 redesign).

Picture cards are the stable anchor: always the same font (Andika, made
for beginning readers), always lowercase, accent color band behind the
word, a language pill on every card (no language is the default). Letter
cards are "letter family" cards: the big canonical lowercase form plus a
specimen row showing the letter's other real-life shapes (uppercase,
double-story print sans, serif). Deliberate variation lives there, and
only there.

Fonts are bundled so every machine renders identical cards.
"""

from pathlib import Path

from reportlab.lib.colors import Color, HexColor
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

CARD_W = 6 * cm
CARD_H = 9 * cm
CORNER_R = 3 * mm
PAGE_W, PAGE_H = A4

# 3x3 grid, uniform spacing so cut lines are equidistant
COLS, ROWS = 3, 3
SPACING_X = (PAGE_W - COLS * CARD_W) / COLS
SPACING_Y = (PAGE_H - ROWS * CARD_H) / ROWS
MARGIN_X, MARGIN_Y = SPACING_X / 2, SPACING_Y / 2

HIGHLIGHT = HexColor("#E63946")
BG_CARD = HexColor("#FFF8F0")
BORDER = HexColor("#E0DAD2")
WORD_COLOR = HexColor("#2B2D42")
BAND_ALPHA = 0.14
LETTER_BG_ALPHA = 0.12

# Vowels get warm hues (each unique), consonants cool ones — a soft
# Montessori-style vowel/consonant cue. Two invariants (tested): alphabet
# neighbors never share a color, and every color is dark enough to work
# both as word text on cream and as a ~14% background tint.
LETTER_COLORS = {
    'a': HexColor("#E63946"), 'b': HexColor("#457B9D"), 'c': HexColor("#6A4C93"),
    'd': HexColor("#2A9D8F"), 'e': HexColor("#F4A261"), 'f': HexColor("#6A4C93"),
    'g': HexColor("#1D3557"), 'h': HexColor("#2A9D8F"), 'i': HexColor("#E76F51"),
    'j': HexColor("#3D8EB9"), 'k': HexColor("#6A4C93"), 'l': HexColor("#2A9D8F"),
    'm': HexColor("#264653"), 'n': HexColor("#457B9D"), 'o': HexColor("#E9C46A"),
    'p': HexColor("#6A4C93"), 'q': HexColor("#3D8EB9"), 'r': HexColor("#1D3557"),
    's': HexColor("#2A9D8F"), 't': HexColor("#457B9D"), 'u': HexColor("#9C6644"),
    'v': HexColor("#457B9D"), 'w': HexColor("#1D3557"), 'x': HexColor("#6A4C93"),
    'y': HexColor("#2A9D8F"), 'z': HexColor("#1D3557"),
}
VOWELS = set("aeiou")

LANGUAGE_COLORS = {
    "nl": HexColor("#3E6CB0"),
    "es": HexColor("#C77B30"),
}
LANGUAGE_DEFAULT = HexColor("#8A8A8A")

FONT_DIR = Path(__file__).parent / "fonts"
PRIMARY = "Andika"
PILL_FONT = "AndikaRegular"

# Letter-family specimen rows, curated per letter from two sources:
# allograph variation (letters whose *construction* differs across common
# typefaces: single/double-story a and g, tailed vs bare l, serif I/J,
# hooked f/t/y) and the handwriting model taught in Dutch schools
# (Playwrite NL). Highly variable letters get a longer row; stable
# letters (o, s, v, ...) only show their capital and handwritten form.
# Entries are (font, case): "u" = uppercase, "l" = lowercase.
_AND, _LATO, _SER, _HAND = "Andika", "Lato", "DejaVuSerif", "Playwrite"
SPECIMEN_DEFAULT = ((_AND, "u"), (_HAND, "l"))
SPECIMENS = {
    "a": ((_AND, "u"), (_LATO, "l"), (_SER, "l"), (_HAND, "l")),
    "f": ((_AND, "u"), (_SER, "l"), (_HAND, "l")),
    "g": ((_AND, "u"), (_SER, "l"), (_HAND, "l")),
    "i": ((_AND, "u"), (_SER, "u"), (_HAND, "l")),
    "j": ((_AND, "u"), (_SER, "u"), (_HAND, "l")),
    "l": ((_AND, "u"), (_LATO, "l"), (_SER, "l"), (_HAND, "l")),
    "t": ((_AND, "u"), (_SER, "l"), (_HAND, "l")),
    "y": ((_AND, "u"), (_SER, "l"), (_HAND, "l")),
}

_fonts_ready = False


def register_fonts():
    """Register the bundled fonts (idempotent)."""
    global _fonts_ready
    if _fonts_ready:
        return
    for name, filename in (
        ("Andika", "Andika-Bold.ttf"),
        ("AndikaRegular", "Andika-Regular.ttf"),
        ("Lato", "Lato-Bold.ttf"),
        ("DejaVuSerif", "DejaVuSerif-Bold.ttf"),
        ("Playwrite", "PlaywriteNL.ttf"),
    ):
        pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / filename)))
    _fonts_ready = True


def _tint(color, alpha):
    return Color(color.red, color.green, color.blue, alpha=alpha)


def _card_base(c, x, y, fill):
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.setFillColor(fill)
    c.roundRect(x, y, CARD_W, CARD_H, CORNER_R, fill=1, stroke=1)


def _draw_image(c, path, ax, ay, aw, ah):
    c.setFillAlpha(1)  # clear any alpha left in the graphics state
    with Image.open(path) as img:
        iw, ih = img.size
    aspect = iw / ih
    if aspect > aw / ah:
        dw, dh = aw, aw / aspect
    else:
        dw, dh = ah * aspect, ah
    c.drawImage(str(path), ax + (aw - dw) / 2, ay + (ah - dh) / 2, dw, dh,
                preserveAspectRatio=True, mask='auto')


def _language_pill(c, x, y, language):
    color = LANGUAGE_COLORS.get(language, LANGUAGE_DEFAULT)
    w, h = 8.5 * mm, 4.5 * mm
    px, py = x + CARD_W - 3 * mm - w, y + 3 * mm
    c.setFillColor(_tint(color, 0.18))
    c.roundRect(px, py, w, h, h / 2, fill=1, stroke=0)
    c.setFont(PILL_FONT, 8)
    c.setFillColor(color)
    tw = pdfmetrics.stringWidth(language, PILL_FONT, 8)
    c.drawString(px + (w - tw) / 2, py + 1.2 * mm, language)


def draw_picture_card(c, x, y, word, image_path, letter, language):
    """Image on cream, word on an accent-tinted band, language pill."""
    register_fonts()
    accent = LETTER_COLORS.get(letter, HIGHLIGHT)
    _card_base(c, x, y, BG_CARD)

    band_h = CARD_H * 0.24
    c.setFillColor(_tint(accent, BAND_ALPHA))
    c.roundRect(x, y, CARD_W, band_h, CORNER_R, fill=1, stroke=0)
    c.rect(x, y + band_h - CORNER_R, CARD_W, CORNER_R, fill=1, stroke=0)

    _draw_image(c, image_path, x + 4 * mm, y + CARD_H * 0.27,
                CARD_W - 8 * mm, CARD_H * 0.68)

    display = word.lower()
    size = 34
    max_w = CARD_W - 23 * mm  # keeps the centered word clear of the language pill
    while size > 12 and pdfmetrics.stringWidth(display, PRIMARY, size) > max_w:
        size -= 1
    first, rest = display[0], display[1:]
    tx = x + (CARD_W - pdfmetrics.stringWidth(display, PRIMARY, size)) / 2
    ty = y + band_h / 2 - size * 0.32
    c.setFont(PRIMARY, size)
    c.setFillColor(accent)
    c.drawString(tx, ty, first)
    c.setFillColor(WORD_COLOR)
    c.drawString(tx + pdfmetrics.stringWidth(first, PRIMARY, size), ty, rest)

    _language_pill(c, x, y, language)


def draw_letter_card(c, x, y, letter):
    """Letter family: big canonical lowercase + specimen row of other shapes."""
    register_fonts()
    accent = LETTER_COLORS.get(letter, HIGHLIGHT)
    _card_base(c, x, y, BG_CARD)
    c.setFillColor(_tint(accent, LETTER_BG_ALPHA))
    c.roundRect(x, y, CARD_W, CARD_H, CORNER_R, fill=1, stroke=0)

    size = 110
    c.setFont(PRIMARY, size)
    w = pdfmetrics.stringWidth(letter, PRIMARY, size)
    c.setFillColor(accent)
    c.drawString(x + (CARD_W - w) / 2, y + (CARD_H - size * 0.7) / 2 + 4 * mm, letter)

    spec_size = 21
    gap = 4 * mm
    glyphs = [(font, letter.upper() if case == "u" else letter.lower())
              for font, case in SPECIMENS.get(letter, SPECIMEN_DEFAULT)]
    total = sum(pdfmetrics.stringWidth(g, f, spec_size) for f, g in glyphs)
    total += gap * (len(glyphs) - 1)
    gx = x + (CARD_W - total) / 2
    c.setFillColor(_tint(accent, 0.55))
    for font, glyph in glyphs:
        c.setFont(font, spec_size)
        c.drawString(gx, y + 6 * mm, glyph)
        gx += pdfmetrics.stringWidth(glyph, font, spec_size) + gap

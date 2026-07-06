"""Card design: 'Kleurblok' (chosen July 2026, v2 redesign).

Picture cards are the stable anchor: always the same font (Andika, made
for beginning readers), always lowercase, accent color band behind the
word, and an optional tag pill (a short colored label — a language like
``nl``, or any deck marker; blank renders pill-free). Letter cards are
"letter family" cards: the big canonical lowercase form plus a specimen
row showing the letter's other real-life shapes (uppercase, double-story
print sans, serif). Deliberate variation lives there, and only there.

Fonts are bundled so every machine renders identical cards.
"""

import hashlib
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
# Montessori-style vowel/consonant cue. Three invariants (tested): alphabet
# neighbors never share a color; warm iff vowel; and every color clears
# WCAG 3:1 contrast on the cream card, so the highlighted first letter — the
# phonics cue — stays legible as word text.
LETTER_COLORS = {
    'a': HexColor("#E63946"), 'b': HexColor("#457B9D"), 'c': HexColor("#6A4C93"),
    'd': HexColor("#2A9D8F"), 'e': HexColor("#D8680F"), 'f': HexColor("#6A4C93"),
    'g': HexColor("#1D3557"), 'h': HexColor("#2A9D8F"), 'i': HexColor("#E45C3B"),
    'j': HexColor("#3D8EB9"), 'k': HexColor("#6A4C93"), 'l': HexColor("#2A9D8F"),
    'm': HexColor("#264653"), 'n': HexColor("#457B9D"), 'o': HexColor("#AB8119"),
    'p': HexColor("#6A4C93"), 'q': HexColor("#3D8EB9"), 'r': HexColor("#1D3557"),
    's': HexColor("#2A9D8F"), 't': HexColor("#457B9D"), 'u': HexColor("#9C6644"),
    'v': HexColor("#457B9D"), 'w': HexColor("#1D3557"), 'x': HexColor("#6A4C93"),
    'y': HexColor("#2A9D8F"), 'z': HexColor("#1D3557"),
}
VOWELS = set("aeiou")

# Tag pills: known languages keep a fixed color; any other tag is hashed
# to a stable color from a small palette, so two children's decks get
# visibly different pills with no config. Palette hues are spread apart and
# all clear WCAG 3:1 on the cream card (tested) so pill text stays legible.
TAG_COLORS = {
    "nl": HexColor("#3E6CB0"),
    "es": HexColor("#C77B30"),
}
TAG_PALETTE = (
    HexColor("#C1443C"), HexColor("#2A7F62"), HexColor("#6A4C93"),
    HexColor("#B07A12"), HexColor("#3D6CB0"), HexColor("#A0416F"),
)


def tag_color(tag):
    """Stable pill color for a tag: fixed for known languages, else hashed."""
    if tag in TAG_COLORS:
        return TAG_COLORS[tag]
    idx = int(hashlib.md5(tag.encode("utf-8")).hexdigest(), 16) % len(TAG_PALETTE)
    return TAG_PALETTE[idx]

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
    """An alpha tint of ``color`` precomputed over the cream card as an opaque
    color. Print-shop RIPs flatten live PDF transparency unpredictably, so we
    never emit it: composite here instead. Backdrop is the card cream, which is
    exactly what sits behind the band and letter background."""
    return Color(*(bg + (ch - bg) * alpha for ch, bg in (
        (color.red, BG_CARD.red), (color.green, BG_CARD.green),
        (color.blue, BG_CARD.blue))))


def _wrap(text, font, size, max_w):
    """Greedy word-wrap to lines no wider than max_w."""
    lines, cur = [], ""
    for word in text.split():
        trial = f"{cur} {word}".strip()
        if pdfmetrics.stringWidth(trial, font, size) <= max_w or not cur:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def draw_howto_page(c):
    """A single-page parent guide, drawn from lettercards.howto (shared source).
    Deliberately minimal — the staged pedagogy is frozen for v3 (see #26)."""
    from . import howto
    register_fonts()
    mx = 20 * mm
    max_w = PAGE_W - 2 * mx
    y = PAGE_H - 26 * mm

    def paragraph(text):
        nonlocal y
        c.setFont(PILL_FONT, 12)
        c.setFillColor(WORD_COLOR)
        for line in _wrap(text, PILL_FONT, 12, max_w):
            c.drawString(mx, y, line)
            y -= 12 * 1.45

    c.setFillColor(WORD_COLOR)
    c.setFont(PRIMARY, 26)
    c.drawString(mx, y, howto.TITLE)
    y -= 13 * mm
    paragraph(howto.INTRO)
    y -= 6 * mm
    paragraph(howto.OUTRO)


def _card_base(c, x, y, fill, radius=CORNER_R):
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.setFillColor(fill)
    c.roundRect(x, y, CARD_W, CARD_H, radius, fill=1, stroke=1)


def draw_cut_lines(c):
    """Dashed guides along every card edge, for straight-cutting a full sheet."""
    c.saveState()
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.4)
    c.setDash(2, 3)
    xs = sorted({MARGIN_X + col * (CARD_W + SPACING_X) + dx
                 for col in range(COLS) for dx in (0, CARD_W)})
    ys = sorted({PAGE_H - MARGIN_Y - (row + 1) * CARD_H - row * SPACING_Y + dy
                 for row in range(ROWS) for dy in (0, CARD_H)})
    for x in xs:
        c.line(x, ys[0], x, ys[-1])
    for y in ys:
        c.line(xs[0], y, xs[-1], y)
    c.restoreState()


def _draw_image(c, path, ax, ay, aw, ah):
    with Image.open(path) as img:
        iw, ih = img.size
    aspect = iw / ih
    if aspect > aw / ah:
        dw, dh = aw, aw / aspect
    else:
        dw, dh = ah * aspect, ah
    c.drawImage(str(path), ax + (aw - dw) / 2, ay + (ah - dh) / 2, dw, dh,
                preserveAspectRatio=True, mask='auto')


PILL_MARGIN = 3 * mm


def _pill_width(tag):
    """Rendered width of a tag pill (0 for a blank tag)."""
    if not tag:
        return 0
    tw = pdfmetrics.stringWidth(tag, PILL_FONT, 8)
    return max(8.5 * mm, tw + 3 * mm)


def _tag_pill(c, x, y, tag):
    """A short colored label in the card's bottom-right. Blank tag: no pill."""
    if not tag:
        return
    color = tag_color(tag)
    tw = pdfmetrics.stringWidth(tag, PILL_FONT, 8)
    w, h = _pill_width(tag), 4.5 * mm
    px, py = x + CARD_W - PILL_MARGIN - w, y + 3 * mm
    c.setFillColor(_tint(color, 0.18))
    c.roundRect(px, py, w, h, h / 2, fill=1, stroke=0)
    c.setFont(PILL_FONT, 8)
    c.setFillColor(color)
    c.drawString(px + (w - tw) / 2, py + 1.2 * mm, tag)


def draw_picture_card(c, x, y, word, image_path, letter, tag="", radius=CORNER_R):
    """Image on cream, word on an accent-tinted band, optional tag pill."""
    register_fonts()
    accent = LETTER_COLORS.get(letter, HIGHLIGHT)
    _card_base(c, x, y, BG_CARD, radius)

    band_h = CARD_H * 0.24
    c.setFillColor(_tint(accent, BAND_ALPHA))
    c.roundRect(x, y, CARD_W, band_h, radius, fill=1, stroke=0)
    c.rect(x, y + band_h - radius, CARD_W, radius, fill=1, stroke=0)

    _draw_image(c, image_path, x + 4 * mm, y + CARD_H * 0.27,
                CARD_W - 8 * mm, CARD_H * 0.68)

    display = word.lower()
    size = 34
    max_w = CARD_W - 23 * mm  # keeps the centered word clear of the tag pill
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

    _tag_pill(c, x, y, tag)


def draw_letter_card(c, x, y, letter, tag="", radius=CORNER_R):
    """Letter family: big canonical lowercase + specimen row of other shapes.

    Carries the same tag pill as picture cards: letter cards are the ones
    most likely to get mixed up when two decks share a box."""
    register_fonts()
    accent = LETTER_COLORS.get(letter, HIGHLIGHT)
    _card_base(c, x, y, BG_CARD, radius)
    c.setFillColor(_tint(accent, LETTER_BG_ALPHA))
    c.roundRect(x, y, CARD_W, CARD_H, radius, fill=1, stroke=0)

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
    # Center the row, but keep it clear of the tag pill it shares the bottom
    # edge with (reserve the pill's width plus its margins when a tag is set).
    reserve = _pill_width(tag) + PILL_MARGIN + 2 * mm if tag else 0
    gx = x + (CARD_W - reserve - total) / 2
    c.setFillColor(_tint(accent, 0.55))
    for font, glyph in glyphs:
        c.setFont(font, spec_size)
        c.drawString(gx, y + 6 * mm, glyph)
        gx += pdfmetrics.stringWidth(glyph, font, spec_size) + gap

    _tag_pill(c, x, y, tag)

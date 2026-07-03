"""Card design: dimensions, colors, fonts, and the two card faces.

Ported unchanged from the v1 design so printed batches keep matching.
The Phase 2 redesign happens here and only here.
"""

import os
import zlib
from pathlib import Path

from reportlab.lib.colors import Color, HexColor, white
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
BG_PICTURE = HexColor("#FFF8F0")
BG_LETTER = HexColor("#F0F7FF")
BORDER = HexColor("#CCCCCC")
WORD_COLOR = HexColor("#2B2D42")

LETTER_COLORS = {
    'a': HexColor("#E63946"), 'b': HexColor("#457B9D"), 'c': HexColor("#E9C46A"),
    'd': HexColor("#2A9D8F"), 'e': HexColor("#F4A261"), 'f': HexColor("#6A4C93"),
    'g': HexColor("#1D3557"), 'h': HexColor("#E76F51"), 'i': HexColor("#264653"),
    'j': HexColor("#A8DADC"), 'k': HexColor("#F4A261"), 'l': HexColor("#2A9D8F"),
    'm': HexColor("#E63946"), 'n': HexColor("#457B9D"), 'o': HexColor("#E9C46A"),
    'p': HexColor("#6A4C93"), 'r': HexColor("#E76F51"), 's': HexColor("#2A9D8F"),
    't': HexColor("#F4A261"), 'v': HexColor("#457B9D"), 'w': HexColor("#1D3557"),
    'z': HexColor("#E63946"),
}

SYSTEM_FONTS = {
    # macOS — visually distinct, child-friendly
    "ArialRounded": "/System/Library/Fonts/Supplemental/Arial Rounded Bold.ttf",
    "ComicSans":    "/System/Library/Fonts/Supplemental/Comic Sans MS Bold.ttf",
    "GeorgiaBold":  "/System/Library/Fonts/Supplemental/Georgia Bold.ttf",
    "BradleyHand":  "/System/Library/Fonts/Supplemental/Bradley Hand Bold.ttf",
    # Linux fallbacks
    "DejaVuSans":   "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "Lato":         "/usr/share/fonts/truetype/lato/Lato-Bold.ttf",
    "DejaVuSerif":  "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf",
    "Caladea":      "/usr/share/fonts/truetype/crosextra/Caladea-Bold.ttf",
}
FONT_ROTATION = ["ArialRounded", "ComicSans", "GeorgiaBold", "BradleyHand",
                 "DejaVuSerif", "Caladea", "DejaVuSans", "Lato"]


def register_fonts() -> list[str]:
    registered = []
    for name, path in SYSTEM_FONTS.items():
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                registered.append(name)
            except Exception:
                pass
    return registered


def pick_font(word: str, override: str | None, available: list[str]) -> str:
    """Rotate fonts per word, deterministically (stable across runs)."""
    if override and override in available:
        return override
    usable = [f for f in FONT_ROTATION if f in available] or available
    if not usable:
        return "Helvetica"
    return usable[zlib.crc32(word.encode("utf-8")) % len(usable)]


def _rounded_card(c, x, y, fill):
    c.setStrokeColor(BORDER)
    c.setLineWidth(0.5)
    c.setFillColor(fill)
    c.roundRect(x, y, CARD_W, CARD_H, CORNER_R, fill=1, stroke=1)


def draw_picture_card(c, x, y, word: str, image_path: Path, font: str, letter: str):
    """Image on top, word below with accent first letter, letter badges in corners."""
    _rounded_card(c, x, y, BG_PICTURE)
    accent = LETTER_COLORS.get(letter, HIGHLIGHT)

    img_margin = 4 * mm
    area_x, area_y = x + img_margin, y + CARD_H * 0.28
    area_w, area_h = CARD_W - 2 * img_margin, CARD_H * 0.65
    with Image.open(image_path) as img:
        iw, ih = img.size
    aspect = iw / ih
    if aspect > area_w / area_h:
        draw_w, draw_h = area_w, area_w / aspect
    else:
        draw_w, draw_h = area_h * aspect, area_h
    c.drawImage(str(image_path),
                area_x + (area_w - draw_w) / 2, area_y + (area_h - draw_h) / 2,
                draw_w, draw_h, preserveAspectRatio=True, mask='auto')

    # Word with accent-colored first letter, sized to fit
    display = word.lower()
    first, rest = display[0], display[1:]
    max_width = CARD_W - 2 * img_margin
    size = 28
    while size > 12 and pdfmetrics.stringWidth(display, font, size) > max_width:
        size -= 1
    total_w = pdfmetrics.stringWidth(display, font, size)
    text_x, text_y = x + (CARD_W - total_w) / 2, y + CARD_H * 0.08
    c.setFont(font, size)
    c.setFillColor(accent)
    c.drawString(text_x, text_y, first)
    c.setFillColor(WORD_COLOR)
    c.drawString(text_x + pdfmetrics.stringWidth(first, font, size), text_y, rest)

    # Corner badges: filled lowercase top-left, outlined uppercase top-right
    badge_r, badge_size = 6 * mm, 16
    cy = y + CARD_H - 3 * mm - badge_r
    for cx, fill, text_color, char in (
        (x + 3 * mm + badge_r, accent, white, letter),
        (x + CARD_W - 3 * mm - badge_r, white, accent, letter.upper()),
    ):
        c.setStrokeColor(accent)
        c.setFillColor(fill)
        c.circle(cx, cy, badge_r, fill=1, stroke=int(fill is white))
        c.setFont(font, badge_size)
        c.setFillColor(text_color)
        w = pdfmetrics.stringWidth(char, font, badge_size)
        c.drawString(cx - w / 2, cy - badge_size * 0.32, char)


def draw_letter_card(c, x, y, letter: str, font: str):
    """Big accent-colored letter, faint opposite case at the bottom."""
    _rounded_card(c, x, y, BG_LETTER)
    accent = LETTER_COLORS.get(letter, HIGHLIGHT)

    size = 120
    c.setFont(font, size)
    w = pdfmetrics.stringWidth(letter, font, size)
    c.setFillColor(accent)
    c.drawString(x + (CARD_W - w) / 2, y + (CARD_H - size * 0.7) / 2, letter)

    other = letter.upper() if letter.islower() else letter.lower()
    small = 24
    c.setFont(font, small)
    ow = pdfmetrics.stringWidth(other, font, small)
    c.setFillColor(Color(accent.red, accent.green, accent.blue, alpha=0.4))
    c.drawString(x + (CARD_W - ow) / 2, y + 5 * mm, other)

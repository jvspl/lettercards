"""PDF assembly: lay printable cards out on A4 pages."""

from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from . import layout
from .deck import Card, resolve_image


def render_pdf(cards: list[Card], deck_dir: Path, output: Path,
               font_override: str | None = None) -> dict:
    """Render picture + letter cards to an A4 PDF. Returns stats.

    Each word gets a picture card; each distinct letter additionally
    gets one letter card (drawn in the font of its first word).
    """
    available = layout.register_fonts()
    c = canvas.Canvas(str(output), pagesize=A4)
    c.setTitle("Letterkaarten")

    items = []
    seen_letters = set()
    for card in cards:
        font = layout.pick_font(card.word, font_override, available)
        image = resolve_image(card, deck_dir)
        items.append(("picture", card, font, image))
        if card.letter not in seen_letters:
            seen_letters.add(card.letter)
            items.append(("letter", card, font, None))

    per_page = layout.COLS * layout.ROWS
    for i, (kind, card, font, image) in enumerate(items):
        if i and i % per_page == 0:
            c.showPage()
        col, row = i % per_page % layout.COLS, i % per_page // layout.COLS
        x = layout.MARGIN_X + col * (layout.CARD_W + layout.SPACING_X)
        y = layout.PAGE_H - layout.MARGIN_Y - (row + 1) * layout.CARD_H - row * layout.SPACING_Y
        if kind == "picture":
            layout.draw_picture_card(c, x, y, card.word, image, font, card.letter)
        else:
            layout.draw_letter_card(c, x, y, card.letter, font)

    c.save()
    return {
        "cards": len(items),
        "picture_cards": len(items) - len(seen_letters),
        "letter_cards": len(seen_letters),
        "pages": (len(items) + per_page - 1) // per_page,
        "fonts": available or ["Helvetica"],
    }

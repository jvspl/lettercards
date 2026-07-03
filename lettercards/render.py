"""PDF assembly: lay printable cards out on A4 pages."""

from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from . import layout
from .deck import Card, resolve_image


def render_pdf(cards: list[Card], deck_dir: Path, output: Path) -> dict:
    """Render picture + letter cards to an A4 PDF. Returns stats.

    Each word gets a picture card; each distinct letter additionally
    gets one letter-family card.
    """
    c = canvas.Canvas(str(output), pagesize=A4)
    c.setTitle("Letterkaarten")

    items = []
    seen_letters = set()
    for card in cards:
        items.append(("picture", card))
        if card.letter not in seen_letters:
            seen_letters.add(card.letter)
            items.append(("letter", card))

    per_page = layout.COLS * layout.ROWS
    for i, (kind, card) in enumerate(items):
        if i and i % per_page == 0:
            c.showPage()
        col, row = i % per_page % layout.COLS, i % per_page // layout.COLS
        x = layout.MARGIN_X + col * (layout.CARD_W + layout.SPACING_X)
        y = layout.PAGE_H - layout.MARGIN_Y - (row + 1) * layout.CARD_H - row * layout.SPACING_Y
        if kind == "picture":
            layout.draw_picture_card(c, x, y, card.word,
                                     resolve_image(card, deck_dir),
                                     card.letter, card.language)
        else:
            layout.draw_letter_card(c, x, y, card.letter)

    c.save()
    return {
        "cards": len(items),
        "picture_cards": len(items) - len(seen_letters),
        "letter_cards": len(seen_letters),
        "pages": (len(items) + per_page - 1) // per_page,
    }

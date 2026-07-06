"""PDF assembly: lay printable cards out on A4 pages."""

from pathlib import Path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

from . import layout
from .deck import Card, resolve_image


def render_pdf(cards: list[Card], deck_dir: Path, output: Path,
               rounded: bool = True, cut_lines: bool = False,
               howto: bool = False) -> dict:
    """Render picture + letter cards to an A4 PDF. Returns stats.

    Each word gets a picture card; each distinct letter additionally
    gets one letter-family card. ``rounded=False`` draws square-cornered
    cards and ``cut_lines=True`` adds dashed cutting guides — both for
    straight-cutting a sheet with a guillotine. ``howto=True`` appends a
    final parent how-to page so the guidance travels with the printout.
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
    radius = layout.CORNER_R if rounded else 0
    for i, (kind, card) in enumerate(items):
        if i % per_page == 0:
            if i:
                c.showPage()
            if cut_lines:
                layout.draw_cut_lines(c)
        col, row = i % per_page % layout.COLS, i % per_page // layout.COLS
        x = layout.MARGIN_X + col * (layout.CARD_W + layout.SPACING_X)
        y = layout.PAGE_H - layout.MARGIN_Y - (row + 1) * layout.CARD_H - row * layout.SPACING_Y
        if kind == "picture":
            layout.draw_picture_card(c, x, y, card.word,
                                     resolve_image(card, deck_dir),
                                     card.letter, card.language, radius)
        else:
            layout.draw_letter_card(c, x, y, card.letter, radius)

    pages = (len(items) + per_page - 1) // per_page
    if howto:
        c.showPage()
        pages += layout.draw_howto_page(c)

    c.save()
    return {
        "cards": len(items),
        "picture_cards": len(items) - len(seen_letters),
        "letter_cards": len(seen_letters),
        "pages": pages,
    }

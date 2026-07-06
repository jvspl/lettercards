"""Command-line interface: lettercards render / check."""

import argparse
import sys
from pathlib import Path

from . import __version__
from .deck import check_deck, load_deck, printable_cards, resolve_deck_dir
from .photos import process_photo
from .render import render_pdf


def _render(args) -> int:
    deck_dir = resolve_deck_dir(args.deck)
    cards = load_deck(deck_dir)
    letters = [l.strip().lower() for l in args.letters.split(",")] if args.letters else None
    words = [w.strip().lower() for w in args.cards.split(",")] if args.cards else None
    selected = printable_cards(cards, deck_dir, letters, words)
    if not selected:
        print("No printable cards match (need status=active and a resolvable image).")
        return 1

    output = Path(args.output)
    # The how-to page rides along on a full deck render; skip it for filtered
    # reprints (--letters/--cards) so a single-letter reprint stays clean.
    include_howto = not args.no_howto and not (letters or words)
    stats = render_pdf(selected, deck_dir, output, howto=include_howto)
    print(f"✓ {output} — {stats['cards']} cards "
          f"({stats['picture_cards']} picture + {stats['letter_cards']} letter), "
          f"{stats['pages']} page(s)")

    skipped = [c.word for c in cards if c.status == "idea"]
    if skipped and not (letters or words):
        print(f"  ideas waiting for an image: {', '.join(skipped)}")
    return 0


def _check(args) -> int:
    deck_dir = resolve_deck_dir(args.deck)
    cards, problems = check_deck(deck_dir)
    by_status = {}
    for card in cards:
        by_status.setdefault(card.status, []).append(card)
    printable = printable_cards(cards, deck_dir)
    print(f"{len(cards)} cards: "
          + ", ".join(f"{len(v)} {k}" for k, v in sorted(by_status.items())))
    print(f"{len(printable)} printable now")
    ideas = by_status.get("idea", [])
    if ideas:
        print("ideas: " + ", ".join(c.word for c in ideas))
    if problems:
        print(f"\n{len(problems)} problem(s):")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    print("deck is valid")
    return 0


def _photo(args) -> int:
    out = process_photo(Path(args.source), Path(args.output), args.size, args.pictogram)
    print(f"✓ {out} — square card image")
    print("  next: add/update the row in deck.csv and set its status to active")
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="lettercards",
        description="Generate printable letter-learning cards for toddlers.")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)

    p_render = sub.add_parser("render", help="render a deck to a printable A4 PDF")
    p_render.add_argument("deck", help="deck directory, or 'starter' for the bundled deck")
    p_render.add_argument("--letters", help="only these letters, comma-separated (a,d,o)")
    p_render.add_argument("--cards", help="only these words, comma-separated (zebra,kat)")
    p_render.add_argument("-o", "--output", default="cards.pdf", help="output PDF path")
    p_render.add_argument("--no-howto", action="store_true",
                          help="omit the parent how-to page from a full-deck render")
    p_render.set_defaults(func=_render)

    p_check = sub.add_parser("check", help="validate a deck and summarize its state")
    p_check.add_argument("deck", help="deck directory, or 'starter'")
    p_check.set_defaults(func=_check)

    p_photo = sub.add_parser("photo", help="prepare a photo as a square card image")
    p_photo.add_argument("source", help="source photo (jpg/png; convert heic first)")
    p_photo.add_argument("output", help="output PNG path, e.g. images/oma.png")
    p_photo.add_argument("--size", type=int, help="output size in px (default 800, pictogram 400)")
    p_photo.add_argument("--pictogram", action="store_true",
                         help="intake a generated pictogram: 400px, background flattened to card cream")
    p_photo.set_defaults(func=_photo)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except OSError as e:
        # Deck/image not found, unreadable file, wrong format (e.g. heic) —
        # the commands know what they need, so show one line, not a traceback.
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())

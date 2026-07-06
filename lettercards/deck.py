"""Deck loading, image resolution, and validation.

A deck is a directory containing a ``deck.csv`` and optionally an
``images/`` directory. Card images resolve against the deck's own
``images/`` first, then the bundled starter images.
"""

import csv
from dataclasses import dataclass
from importlib import resources
from pathlib import Path

from PIL import Image

STATUSES = ("idea", "active", "retired")


@dataclass
class Card:
    letter: str
    word: str
    image: str
    language: str
    status: str
    notes: str
    line: int  # 1-based line number in deck.csv, for check messages


def starter_dir() -> Path:
    return Path(str(resources.files("lettercards"))) / "starter"


def resolve_deck_dir(arg: str) -> Path:
    """Resolve a deck argument: 'starter' means the bundled starter deck."""
    if str(arg) == "starter":
        return starter_dir()
    return Path(arg)


def load_deck(deck_dir: Path) -> list[Card]:
    """Load all cards from deck.csv, regardless of status.

    Lines whose letter field starts with '#' are comments. Missing
    status defaults to 'active', missing language to 'nl'.
    """
    path = Path(deck_dir) / "deck.csv"
    cards = []
    with open(path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for lineno, row in enumerate(reader, start=2):
            letter = (row.get("letter") or "").strip()
            if not letter or letter.startswith("#"):
                continue
            cards.append(Card(
                letter=letter.lower(),
                word=(row.get("word") or "").strip(),
                image=(row.get("image") or "").strip(),
                language=(row.get("language") or "").strip() or "nl",
                status=(row.get("status") or "").strip() or "active",
                notes=(row.get("notes") or "").strip(),
                line=lineno,
            ))
    return cards


def resolve_image(card: Card, deck_dir: Path) -> Path | None:
    """Find a card's image: deck images/ first, then starter images/."""
    if not card.image:
        return None
    for base in (Path(deck_dir) / "images", starter_dir() / "images"):
        candidate = base / card.image
        if candidate.exists():
            return candidate
    return None


def printable_cards(cards: list[Card], deck_dir: Path,
                    letters: list[str] | None = None,
                    words: list[str] | None = None) -> list[Card]:
    """Active cards with a resolvable image, optionally filtered."""
    result = []
    for card in cards:
        if card.status != "active":
            continue
        if letters and card.letter not in letters:
            continue
        if words and card.word.lower() not in words:
            continue
        if resolve_image(card, deck_dir) is None:
            continue
        result.append(card)
    return result


def check_deck(deck_dir: Path) -> tuple[list[Card], list[str]]:
    """Validate a deck. Returns (cards, problems)."""
    deck_dir = Path(deck_dir)
    problems = []
    if not (deck_dir / "deck.csv").exists():
        return [], [f"no deck.csv in {deck_dir}"]

    cards = load_deck(deck_dir)
    seen = {}
    for card in cards:
        where = f"line {card.line} ({card.word or '?'})"
        if not card.word:
            problems.append(f"{where}: missing word")
        if len(card.letter) != 1 or not card.letter.isalpha():
            problems.append(f"{where}: letter must be a single letter, got '{card.letter}'")
        if card.status not in STATUSES:
            problems.append(f"{where}: unknown status '{card.status}'")
        if len(card.letter) == 1 and card.word and card.word[0].lower() != card.letter \
                and not card.notes:
            problems.append(f"{where}: word starts with '{card.word[0].lower()}', "
                            f"not letter '{card.letter}' (add a note to allow an exception)")
        if card.status == "active":
            if not card.image:
                problems.append(f"{where}: active card has no image (should it be an idea?)")
            else:
                image_path = resolve_image(card, deck_dir)
                if image_path is None:
                    problems.append(f"{where}: image '{card.image}' not found in deck or starter images")
                else:
                    with Image.open(image_path) as img:
                        w, h = img.size
                    if w != h or min(w, h) < 400:
                        problems.append(f"{where}: image '{card.image}' is {w}x{h}px, "
                                        f"must be square and at least 400x400")
        key = (card.word.lower(), card.language)
        if card.word and key in seen:
            problems.append(f"{where}: duplicate of line {seen[key]}")
        seen.setdefault(key, card.line)
    return cards, problems

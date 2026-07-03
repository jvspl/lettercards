"""Tests against the bundled starter deck and synthetic decks."""

import shutil

import pytest

from lettercards.cli import main
from lettercards.deck import (check_deck, load_deck, printable_cards,
                              resolve_image, starter_dir)


@pytest.fixture
def deck(tmp_path):
    """A tiny deck: one own-image card, one starter-image card, one idea, one broken."""
    (tmp_path / "images").mkdir()
    shutil.copy(starter_dir() / "images" / "zon.png", tmp_path / "images" / "eigen.png")
    (tmp_path / "deck.csv").write_text(
        "letter,word,image,language,status,notes\n"
        "# a comment line\n"
        "e,eigen,eigen.png,nl,active,\n"
        "z,zebra,zebra.png,nl,active,\n"
        "k,kasteel,,nl,idea,needs image\n"
        "w,wolf,wolf.png,nl,retired,\n",
        encoding="utf-8")
    return tmp_path


def test_load_deck_skips_comments(deck):
    cards = load_deck(deck)
    assert [c.word for c in cards] == ["eigen", "zebra", "kasteel", "wolf"]
    assert cards[0].language == "nl"


def test_image_resolution_prefers_deck_then_starter(deck):
    cards = {c.word: c for c in load_deck(deck)}
    assert resolve_image(cards["eigen"], deck) == deck / "images" / "eigen.png"
    assert resolve_image(cards["zebra"], deck) == starter_dir() / "images" / "zebra.png"
    assert resolve_image(cards["kasteel"], deck) is None


def test_printable_excludes_ideas_retired_and_filters(deck):
    cards = load_deck(deck)
    assert {c.word for c in printable_cards(cards, deck)} == {"eigen", "zebra"}
    assert [c.word for c in printable_cards(cards, deck, letters=["z"])] == ["zebra"]
    assert [c.word for c in printable_cards(cards, deck, words=["eigen"])] == ["eigen"]


def test_check_reports_problems(deck):
    (deck / "deck.csv").write_text(
        "letter,word,image,language,status,notes\n"
        "z,zebra,zebra.png,nl,active,\n"
        "z,zebra,zebra.png,nl,active,duplicate\n"
        "b,bal,missing.png,nl,active,\n"
        "q,quark,,nl,bogus,\n",
        encoding="utf-8")
    _, problems = check_deck(deck)
    text = "\n".join(problems)
    assert "duplicate" in text
    assert "missing.png" in text
    assert "bogus" in text


def test_starter_deck_is_valid():
    cards, problems = check_deck(starter_dir())
    assert problems == []
    assert len(cards) == 34


def test_cli_render_starter(tmp_path, capsys):
    out = tmp_path / "out.pdf"
    assert main(["render", "starter", "--letters", "a,z", "-o", str(out)]) == 0
    assert out.stat().st_size > 1000
    assert out.read_bytes()[:5] == b"%PDF-"
    # 4 picture cards (appel, auto, zebra, zon) + 2 letter cards
    assert "6 cards" in capsys.readouterr().out


def test_cli_check_starter(capsys):
    assert main(["check", "starter"]) == 0
    assert "deck is valid" in capsys.readouterr().out


def test_cli_render_no_match(tmp_path):
    assert main(["render", "starter", "--letters", "q",
                 "-o", str(tmp_path / "x.pdf")]) == 1

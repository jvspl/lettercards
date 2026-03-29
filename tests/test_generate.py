"""Tests for generate.py — CSV parsing, image path resolution, safe-letters filter."""
import os
import pytest
from pathlib import Path
from unittest.mock import patch

from generate import load_cards, get_personal_images_dir, get_safe_letters, get_image_path


# ── load_cards ──────────────────────────────────────────────────────────────

def write_csv(tmp_path, content):
    """Write a legacy 5-column CSV (used to verify backward compatibility)."""
    csv_file = tmp_path / "cards.csv"
    csv_file.write_text("letter,word,image,font,personal\n" + content)
    return csv_file


def test_load_cards_basic(tmp_path):
    csv = write_csv(tmp_path, "a,appel,appel.png,,no\n")
    cards = load_cards(csv)
    assert len(cards) == 1
    assert cards[0]['letter'] == 'a'
    assert cards[0]['word'] == 'appel'
    assert cards[0]['personal'] == 'no'


def test_load_cards_skips_comment_rows(tmp_path):
    csv = write_csv(tmp_path, "# this is a comment\na,appel,appel.png,,no\n")
    cards = load_cards(csv)
    assert len(cards) == 1


def test_load_cards_skips_geen_voorbeeld(tmp_path):
    csv = write_csv(tmp_path, "q,geen voorbeeld,,\n,a,appel,appel.png,,no\n")
    cards = load_cards(csv)
    # Only the non-geen-voorbeeld row (and non-blank letter rows) are returned
    assert all('geen voorbeeld' not in c['word'] for c in cards)


def test_load_cards_letter_filter(tmp_path):
    csv = write_csv(tmp_path, "a,appel,appel.png,,no\nd,deur,deur.png,,no\n")
    cards = load_cards(csv, letters_filter={'a'})
    assert len(cards) == 1
    assert cards[0]['letter'] == 'a'


def test_load_cards_letter_normalised_to_lowercase(tmp_path):
    csv = write_csv(tmp_path, "A,Appel,appel.png,,no\n")
    cards = load_cards(csv)
    assert cards[0]['letter'] == 'a'


def test_load_cards_personal_flag(tmp_path):
    csv = write_csv(tmp_path, "o,oma,oma.png,,yes\n")
    cards = load_cards(csv)
    assert cards[0]['personal'] == 'yes'


def test_load_cards_missing_personal_defaults_to_no(tmp_path):
    # Write CSV without personal column
    f = tmp_path / "deck.csv"
    f.write_text("letter,word,image,font\na,appel,appel.png,\n")
    cards = load_cards(f)
    assert cards[0]['personal'] == 'no'


# ── get_personal_images_dir ─────────────────────────────────────────────────

def test_personal_dir_cli_arg_wins(tmp_path):
    cli_path = str(tmp_path / "cli")
    result = get_personal_images_dir(cli_arg=cli_path)
    assert result == Path(cli_path)


def test_personal_dir_env_var_used_when_no_cli(tmp_path, monkeypatch):
    env_path = str(tmp_path / "env")
    monkeypatch.setenv("LETTERCARDS_PERSONAL_DIR", env_path)
    result = get_personal_images_dir(cli_arg=None)
    assert result == Path(env_path)


def test_personal_dir_cli_wins_over_env(tmp_path, monkeypatch):
    cli_path = str(tmp_path / "cli")
    env_path = str(tmp_path / "env")
    monkeypatch.setenv("LETTERCARDS_PERSONAL_DIR", env_path)
    result = get_personal_images_dir(cli_arg=cli_path)
    assert result == Path(cli_path)


def test_personal_dir_default_when_nothing_set(monkeypatch):
    monkeypatch.delenv("LETTERCARDS_PERSONAL_DIR", raising=False)
    result = get_personal_images_dir(cli_arg=None)
    assert result == Path.home() / '.lettercards' / 'personal'


# ── get_safe_letters ─────────────────────────────────────────────────────────

def test_safe_letters_excludes_personal(tmp_path):
    csv = write_csv(tmp_path, "a,appel,appel.png,,no\no,oma,oma.png,,yes\n")
    safe = get_safe_letters(csv)
    assert 'a' in safe
    assert 'o' not in safe


def test_safe_letters_letter_with_mixed_personal(tmp_path):
    # Letter 'a' has one personal and one non-personal — should be excluded
    csv = write_csv(tmp_path, "a,appel,appel.png,,no\na,abu,abu.png,,yes\n")
    safe = get_safe_letters(csv)
    assert 'a' not in safe


def test_safe_letters_all_safe(tmp_path):
    csv = write_csv(tmp_path, "d,deur,deur.png,,no\ne,eend,eend.png,,no\n")
    safe = get_safe_letters(csv)
    assert safe == {'d', 'e'}


def test_safe_letters_missing_csv_returns_empty():
    safe = get_safe_letters(Path('/nonexistent/deck.csv'))
    assert safe == set()


def test_safe_letters_skips_comments_and_geen_voorbeeld(tmp_path):
    csv = write_csv(tmp_path, "# comment\nq,geen voorbeeld,,,\nd,deur,deur.png,,no\n")
    safe = get_safe_letters(csv)
    assert 'd' in safe
    assert 'q' not in safe


# ── get_image_path ────────────────────────────────────────────────────────────

def test_image_path_personal_card_uses_personal_dir(tmp_path):
    personal_dir = tmp_path / "personal"
    personal_dir.mkdir()
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (personal_dir / "oma.png").write_bytes(b"")

    card = {'image': 'oma.png', 'personal': 'yes'}
    result = get_image_path(card, str(images_dir), personal_dir)
    assert result == str(personal_dir / "oma.png")


def test_image_path_personal_falls_back_to_images(tmp_path):
    personal_dir = tmp_path / "personal"
    personal_dir.mkdir()
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "oma.png").write_bytes(b"")

    card = {'image': 'oma.png', 'personal': 'yes'}
    result = get_image_path(card, str(images_dir), personal_dir)
    assert result == str(images_dir / "oma.png")


def test_image_path_non_personal_uses_images_dir(tmp_path):
    personal_dir = tmp_path / "personal"
    personal_dir.mkdir()
    images_dir = tmp_path / "images"
    images_dir.mkdir()
    (images_dir / "appel.png").write_bytes(b"")
    # Also put a copy in personal to confirm it's NOT used for non-personal cards
    (personal_dir / "appel.png").write_bytes(b"personal-version")

    card = {'image': 'appel.png', 'personal': 'no'}
    result = get_image_path(card, str(images_dir), personal_dir)
    assert result == str(images_dir / "appel.png")


def test_image_path_missing_image_returns_none(tmp_path):
    personal_dir = tmp_path / "personal"
    personal_dir.mkdir()
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    card = {'image': 'missing.png', 'personal': 'no'}
    result = get_image_path(card, str(images_dir), personal_dir)
    assert result is None


def test_image_path_no_image_field_returns_none(tmp_path):
    card = {'image': '', 'personal': 'no'}
    result = get_image_path(card, str(tmp_path), tmp_path)
    assert result is None


# ── deck.csv new fields ───────────────────────────────────────────────────────

def write_deck_csv(tmp_path, content):
    csv_file = tmp_path / "deck.csv"
    csv_file.write_text("letter,word,image,font,personal,status,notes,language\n" + content)
    return csv_file


def test_load_cards_status_defaults_to_active(tmp_path):
    """Old-format CSV (no status column) should default status to 'active'."""
    csv = write_csv(tmp_path, "a,appel,appel.png,,no\n")
    cards = load_cards(csv)
    assert cards[0]['status'] == 'active'


def test_load_cards_language_defaults_to_nl(tmp_path):
    """Old-format CSV (no language column) should default language to 'nl'."""
    csv = write_csv(tmp_path, "a,appel,appel.png,,no\n")
    cards = load_cards(csv)
    assert cards[0]['language'] == 'nl'


def test_load_cards_notes_defaults_to_empty(tmp_path):
    """Old-format CSV (no notes column) should default notes to ''."""
    csv = write_csv(tmp_path, "a,appel,appel.png,,no\n")
    cards = load_cards(csv)
    assert cards[0]['notes'] == ''


def test_load_cards_reads_status_field(tmp_path):
    csv = write_deck_csv(tmp_path, "a,appel,appel.png,,no,testing,,nl\n")
    cards = load_cards(csv)
    assert cards[0]['status'] == 'testing'


def test_load_cards_reads_language_field(tmp_path):
    csv = write_deck_csv(tmp_path, "d,deur,deur.png,,no,active,,es\n")
    cards = load_cards(csv)
    assert cards[0]['language'] == 'es'


def test_load_cards_reads_notes_field(tmp_path):
    csv = write_deck_csv(tmp_path, "d,deur,deur.png,,no,active,she says doo,nl\n")
    cards = load_cards(csv)
    assert cards[0]['notes'] == 'she says doo'


def test_load_cards_skips_retired(tmp_path):
    csv = write_deck_csv(
        tmp_path,
        "a,appel,appel.png,,no,active,,nl\n"
        "d,deur,deur.png,,no,retired,,nl\n",
    )
    cards = load_cards(csv)
    assert len(cards) == 1
    assert cards[0]['word'] == 'appel'


def test_load_cards_skips_pending(tmp_path):
    csv = write_deck_csv(
        tmp_path,
        "a,appel,appel.png,,no,active,,nl\n"
        "w,winkel,,,no,pending,,nl\n",
    )
    cards = load_cards(csv)
    assert len(cards) == 1
    assert cards[0]['word'] == 'appel'


def test_load_cards_includes_testing(tmp_path):
    csv = write_deck_csv(
        tmp_path,
        "a,appel,appel.png,,no,testing,,nl\n",
    )
    cards = load_cards(csv)
    assert len(cards) == 1
    assert cards[0]['status'] == 'testing'

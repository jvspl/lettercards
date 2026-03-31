"""Tests for deck_state.py — load and validate deck-state.json."""
import json

from deck_state import load_deck_state, read_deck_state, validate_deck_state


# ── Helpers ──────────────────────────────────────────────────────────────────

def write_state(tmp_path, data):
    p = tmp_path / "deck-state.json"
    p.write_text(json.dumps(data))
    return p


# ── load_deck_state ───────────────────────────────────────────────────────────

def test_load_deck_state_returns_dict_for_valid_file(tmp_path):
    p = write_state(tmp_path, {"deck_protocol": "1.0", "printed_cards": []})
    result = load_deck_state(p)
    assert isinstance(result, dict)
    assert result["deck_protocol"] == "1.0"


def test_load_deck_state_returns_none_when_file_missing(tmp_path):
    result = load_deck_state(tmp_path / "nonexistent.json")
    assert result is None


def test_load_deck_state_returns_none_for_invalid_json(tmp_path):
    p = tmp_path / "deck-state.json"
    p.write_text("not valid json {{{")
    result = load_deck_state(p)
    assert result is None


def test_read_deck_state_returns_error_for_invalid_json(tmp_path):
    p = tmp_path / "deck-state.json"
    p.write_text("not valid json {{{")
    state, error = read_deck_state(p)
    assert state is None
    assert error is not None


# ── validate_deck_state ───────────────────────────────────────────────────────

def test_validate_no_warnings_for_valid_state(tmp_path):
    state = {
        "deck_protocol": "1.0",
        "printed_cards": [{"word": "appel"}, {"word": "deur"}],
    }
    csv_words = {"appel", "deur", "eend"}
    warnings = validate_deck_state(state, csv_words)
    assert warnings == []


def test_validate_warns_when_deck_protocol_missing():
    state = {"printed_cards": []}
    warnings = validate_deck_state(state, set())
    assert any("deck_protocol" in w for w in warnings)


def test_validate_warns_when_deck_protocol_version_mismatch():
    state = {"deck_protocol": "99.0", "printed_cards": []}
    warnings = validate_deck_state(state, set())
    assert any("99.0" in w for w in warnings)


def test_validate_no_warning_for_supported_protocol():
    state = {"deck_protocol": "1.0", "printed_cards": []}
    warnings = validate_deck_state(state, set())
    assert not any("deck_protocol" in w for w in warnings)


def test_validate_warns_for_printed_card_not_in_csv():
    state = {
        "deck_protocol": "1.0",
        "printed_cards": [{"word": "wolf"}],
    }
    csv_words = {"appel", "deur"}
    warnings = validate_deck_state(state, csv_words)
    assert any("wolf" in w for w in warnings)


def test_validate_no_warning_when_printed_cards_empty():
    state = {"deck_protocol": "1.0", "printed_cards": []}
    warnings = validate_deck_state(state, {"appel"})
    assert warnings == []


def test_validate_returns_empty_for_none_state():
    warnings = validate_deck_state(None, {"appel"})
    assert warnings == []


def test_validate_warns_when_printed_cards_not_a_list():
    state = {"deck_protocol": "1.0", "printed_cards": "not a list"}
    warnings = validate_deck_state(state, set())
    assert any("not a list" in w or "corrupt" in w for w in warnings)


def test_validate_warns_when_printed_card_entry_malformed():
    state = {"deck_protocol": "1.0", "printed_cards": ["wolf", {"printed_date": "2026-03-20"}]}
    warnings = validate_deck_state(state, {"wolf"})
    assert any("printed_cards[0]" in w for w in warnings)
    assert any("printed_cards[1]" in w for w in warnings)


# ── generate.py integration ───────────────────────────────────────────────────

import subprocess
import sys


def write_csv_for_status(tmp_path, rows="a,appel,appel.png,,no\nd,deur,deur.png,,no\n"):
    csv_file = tmp_path / "cards.csv"
    csv_file.write_text("letter,word,image,font,personal\n" + rows, encoding="utf-8")
    return csv_file


def test_status_flag_prints_summary(tmp_path):
    write_csv_for_status(tmp_path)
    state = {
        "deck_protocol": "1.0",
        "printed_cards": [{"word": "appel", "printed_date": "2026-03-20"}],
        "sessions": [],
    }
    (tmp_path / "deck-state.json").write_text(json.dumps(state), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "generate.py", "--status",
         "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(tmp_path / "deck-state.json")],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "Active cards in selected deck: 2" in result.stdout
    assert "Printed cards in inventory: 1" in result.stdout
    assert "Distinct printed words: 1" in result.stdout


def test_status_flag_does_not_warn_for_retired_printed_cards_still_in_csv(tmp_path):
    csv_file = tmp_path / "deck.csv"
    csv_file.write_text(
        "letter,word,image,font,personal,status,notes,language\n"
        "w,wolf,wolf.png,,no,retired,,nl\n"
        "a,appel,appel.png,,no,active,,nl\n",
        encoding="utf-8",
    )
    (tmp_path / "deck-state.json").write_text(
        json.dumps({"deck_protocol": "1.0", "printed_cards": [{"word": "wolf"}], "sessions": []}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "generate.py", "--status",
         "--csv", str(csv_file),
         "--deck-state", str(tmp_path / "deck-state.json")],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "not in cards.csv" not in result.stdout


def test_status_flag_works_without_deck_state_file(tmp_path):
    write_csv_for_status(tmp_path)

    result = subprocess.run(
        [sys.executable, "generate.py", "--status",
         "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(tmp_path / "nonexistent.json")],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "no deck-state" in result.stdout.lower() or "not found" in result.stdout.lower()


def test_status_flag_fails_when_csv_missing_even_if_deck_state_missing(tmp_path):
    result = subprocess.run(
        [sys.executable, "generate.py", "--status",
         "--csv", str(tmp_path / "missing.csv"),
         "--deck-state", str(tmp_path / "nonexistent.json")],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "deck CSV not found" in result.stdout


def test_status_flag_reports_corrupt_deck_state(tmp_path):
    write_csv_for_status(tmp_path)
    p = tmp_path / "deck-state.json"
    p.write_text("not valid json {{{", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, "generate.py", "--status",
         "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(p)],
        capture_output=True, text=True
    )
    assert result.returncode != 0
    assert "could not read deck-state.json" in result.stdout


def test_startup_validation_prints_warning_for_unknown_protocol(tmp_path):
    write_csv_for_status(tmp_path)
    state = {"deck_protocol": "99.0", "printed_cards": []}
    (tmp_path / "deck-state.json").write_text(json.dumps(state), encoding="utf-8")
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    result = subprocess.run(
        [sys.executable, "generate.py", "--no-placeholders",
         "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(tmp_path / "deck-state.json"),
         "--output", str(tmp_path / "out.pdf")],
        capture_output=True, text=True
    )
    assert "99.0" in result.stdout or "99.0" in result.stderr


def test_startup_validation_no_warning_when_state_missing(tmp_path):
    write_csv_for_status(tmp_path)
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    result = subprocess.run(
        [sys.executable, "generate.py", "--no-placeholders",
         "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(tmp_path / "nonexistent.json"),
         "--output", str(tmp_path / "out.pdf")],
        capture_output=True, text=True
    )
    assert "deck_protocol" not in result.stdout
    assert "deck_protocol" not in result.stderr


def test_startup_validation_warns_for_corrupt_deck_state(tmp_path):
    write_csv_for_status(tmp_path)
    p = tmp_path / "deck-state.json"
    p.write_text("not valid json {{{", encoding="utf-8")
    images_dir = tmp_path / "images"
    images_dir.mkdir()

    result = subprocess.run(
        [sys.executable, "generate.py", "--no-placeholders",
         "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(p),
         "--output", str(tmp_path / "out.pdf")],
        capture_output=True, text=True
    )
    assert "could not read" in result.stdout or "could not read" in result.stderr

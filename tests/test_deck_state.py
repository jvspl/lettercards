"""Tests for deck_state.py — load and validate deck-state.json."""
import json
import pytest
from pathlib import Path

from deck_state import load_deck_state, validate_deck_state


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

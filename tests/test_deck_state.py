"""Tests for deck_state.py — load, validate, and write deck-state.json."""
import json

from deck_state import (
    add_review_session,
    format_progress_summary,
    load_deck_state,
    new_deck_state,
    read_deck_state,
    update_letter_progress,
    validate_deck_state,
    VALID_LETTER_STATUSES,
    write_deck_state,
)


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


# ── new_deck_state ────────────────────────────────────────────────────────────

def test_new_deck_state_has_required_keys():
    state = new_deck_state()
    assert state["deck_protocol"] == "1.0"
    assert state["printed_cards"] == []
    assert state["sessions"] == []
    assert "progress" in state
    assert state["progress"]["letters"] == {}


# ── write_deck_state ──────────────────────────────────────────────────────────

def test_write_deck_state_creates_file(tmp_path):
    path = tmp_path / "deck-state.json"
    state = new_deck_state()
    write_deck_state(path, state)
    assert path.exists()
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert loaded["deck_protocol"] == "1.0"


def test_write_deck_state_overwrites_existing(tmp_path):
    path = tmp_path / "deck-state.json"
    write_deck_state(path, {"deck_protocol": "1.0", "printed_cards": []})
    write_deck_state(path, {"deck_protocol": "1.0", "printed_cards": [{"word": "appel"}]})
    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert len(loaded["printed_cards"]) == 1


def test_write_deck_state_leaves_no_tmp_file(tmp_path):
    path = tmp_path / "deck-state.json"
    write_deck_state(path, new_deck_state())
    assert not (tmp_path / "deck-state.json.tmp").exists()


# ── add_review_session ────────────────────────────────────────────────────────

def test_add_review_session_appends_entry():
    state = new_deck_state()
    add_review_session(state, {"type": "review", "date": "2026-04-11", "letters_played": ["a"]})
    assert len(state["sessions"]) == 1
    assert state["sessions"][0]["date"] == "2026-04-11"


def test_add_review_session_preserves_existing_sessions():
    state = new_deck_state()
    state["sessions"].append({"type": "print", "date": "2026-04-01"})
    add_review_session(state, {"type": "review", "date": "2026-04-11"})
    assert len(state["sessions"]) == 2


def test_add_review_session_works_when_sessions_key_missing():
    state = {"deck_protocol": "1.0"}
    add_review_session(state, {"type": "review", "date": "2026-04-11"})
    assert len(state["sessions"]) == 1


# ── update_letter_progress ────────────────────────────────────────────────────

def test_update_letter_progress_creates_new_entry():
    state = new_deck_state()
    update_letter_progress(state, "a", "recognized", date_str="2026-04-11")
    entry = state["progress"]["letters"]["a"]
    assert entry["status"] == "recognized"
    assert entry["first_introduced"] == "2026-04-11"


def test_update_letter_progress_updates_existing_status():
    state = new_deck_state()
    update_letter_progress(state, "a", "introduced", date_str="2026-04-01")
    update_letter_progress(state, "a", "recognized", date_str="2026-04-11")
    assert state["progress"]["letters"]["a"]["status"] == "recognized"
    assert state["progress"]["letters"]["a"]["first_introduced"] == "2026-04-01"


def test_update_letter_progress_appends_note():
    state = new_deck_state()
    update_letter_progress(state, "a", "learning", note="points at A on box", date_str="2026-04-11")
    obs = state["progress"]["letters"]["a"]["observations"]
    assert len(obs) == 1
    assert obs[0]["note"] == "points at A on box"
    assert obs[0]["date"] == "2026-04-11"


def test_update_letter_progress_no_note_leaves_observations_empty():
    state = new_deck_state()
    update_letter_progress(state, "d", "introduced", date_str="2026-04-11")
    assert state["progress"]["letters"]["d"]["observations"] == []


def test_update_letter_progress_multiple_notes_accumulate():
    state = new_deck_state()
    update_letter_progress(state, "a", "learning", note="first obs", date_str="2026-04-10")
    update_letter_progress(state, "a", "recognized", note="second obs", date_str="2026-04-11")
    obs = state["progress"]["letters"]["a"]["observations"]
    assert len(obs) == 2


def test_update_letter_progress_works_when_progress_key_missing():
    state = {"deck_protocol": "1.0"}
    update_letter_progress(state, "a", "introduced", date_str="2026-04-11")
    assert state["progress"]["letters"]["a"]["status"] == "introduced"


# ── VALID_LETTER_STATUSES ─────────────────────────────────────────────────────

def test_valid_letter_statuses_contains_expected_values():
    assert "not_introduced" in VALID_LETTER_STATUSES
    assert "introduced" in VALID_LETTER_STATUSES
    assert "learning" in VALID_LETTER_STATUSES
    assert "recognized" in VALID_LETTER_STATUSES
    assert "mastered" in VALID_LETTER_STATUSES


# ── format_progress_summary ───────────────────────────────────────────────────

def test_format_progress_summary_no_progress():
    state = new_deck_state()
    result = format_progress_summary(state)
    assert "No progress" in result


def test_format_progress_summary_shows_letter_statuses():
    state = new_deck_state()
    update_letter_progress(state, "a", "recognized", date_str="2026-04-11")
    update_letter_progress(state, "d", "learning", date_str="2026-04-11")
    result = format_progress_summary(state)
    assert "recognized: a" in result
    assert "learning: d" in result


def test_format_progress_summary_shows_last_review():
    state = new_deck_state()
    update_letter_progress(state, "a", "recognized", date_str="2026-04-11")
    add_review_session(state, {
        "type": "review", "date": "2026-04-11",
        "letters_played": ["a", "d"], "duration_minutes": 15,
    })
    result = format_progress_summary(state)
    assert "Last review: 2026-04-11" in result
    assert "Letters played: a, d" in result
    assert "Duration: 15 minutes" in result


def test_format_progress_summary_no_review_in_sessions():
    state = new_deck_state()
    update_letter_progress(state, "a", "recognized", date_str="2026-04-11")
    add_review_session(state, {"type": "print", "date": "2026-04-10"})
    result = format_progress_summary(state)
    assert "Last review" not in result

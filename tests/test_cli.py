"""Tests for the unified lettercards CLI."""

import json
import subprocess
import sys


def run_cli(*args):
    return subprocess.run([sys.executable, "-m", "lettercards", *args], capture_output=True, text=True)


def test_top_level_help_works():
    result = run_cli("--help")
    assert result.returncode == 0
    assert "generate" in result.stdout
    assert "status" in result.stdout
    assert "photo" in result.stdout
    assert "pictogram" in result.stdout
    assert "deck" in result.stdout


def test_generate_help_works():
    result = run_cli("generate", "--help")
    assert result.returncode == 0
    assert "--letters" in result.stdout
    assert "--no-placeholders" in result.stdout


def test_status_help_works():
    result = run_cli("status", "--help")
    assert result.returncode == 0
    assert "--deck-state" in result.stdout


def test_photo_process_help_works():
    result = run_cli("photo", "process", "--help")
    assert result.returncode == 0
    assert "--preview" in result.stdout
    assert "--force" in result.stdout


def test_pictogram_prompt_help_works():
    result = run_cli("pictogram", "prompt", "--help")
    assert result.returncode == 0
    assert "--missing" in result.stdout


def test_deck_check_help_works():
    result = run_cli("deck", "check", "--help")
    assert result.returncode == 0
    assert "Validate deck integrity" in result.stdout


def test_status_command_runs_with_explicit_paths(tmp_path):
    csv_file = tmp_path / "deck.csv"
    csv_file.write_text(
        "letter,word,image,font,personal,status,notes,language\n"
        "a,appel,appel.png,,no,active,,nl\n"
        "d,deur,deur.png,,no,active,,nl\n",
        encoding="utf-8",
    )
    deck_state = tmp_path / "deck-state.json"
    deck_state.write_text(
        json.dumps({"deck_protocol": "1.0", "printed_cards": [{"word": "appel"}], "sessions": []}),
        encoding="utf-8",
    )

    result = run_cli("status", "--csv", str(csv_file), "--deck-state", str(deck_state))
    assert result.returncode == 0
    assert "Active cards in selected deck: 2" in result.stdout


def test_deck_check_reports_missing_images(tmp_path):
    csv_file = tmp_path / "deck.csv"
    csv_file.write_text(
        "letter,word,image,font,personal,status,notes,language\n"
        "a,appel,missing.png,,no,active,,nl\n",
        encoding="utf-8",
    )

    result = run_cli("deck", "check", "--csv", str(csv_file))
    assert result.returncode != 0
    assert "Missing image for 'appel'" in result.stdout


# ── progress commands ─────────────────────────────────────────────────────────

def test_progress_show_help_works():
    result = run_cli("progress", "show", "--help")
    assert result.returncode == 0
    assert "--deck-state" in result.stdout


def test_progress_update_letter_help_works():
    result = run_cli("progress", "update-letter", "--help")
    assert result.returncode == 0
    assert "--note" in result.stdout


def test_progress_log_review_help_works():
    result = run_cli("progress", "log-review", "--help")
    assert result.returncode == 0
    assert "--letters" in result.stdout
    assert "--duration" in result.stdout


def test_progress_show_no_state_file(tmp_path):
    result = run_cli("progress", "show", "--deck-state", str(tmp_path / "nonexistent.json"))
    assert result.returncode == 0
    assert "No deck-state" in result.stdout or "No progress" in result.stdout


def test_progress_update_letter_creates_state_file(tmp_path):
    path = tmp_path / "deck-state.json"
    result = run_cli(
        "progress", "update-letter", "a", "recognized",
        "--note", "points at A on cereal box",
        "--date", "2026-04-11",
        "--deck-state", str(path),
    )
    assert result.returncode == 0
    assert "Updated letter 'a'" in result.stdout
    assert path.exists()
    import json
    state = json.loads(path.read_text())
    assert state["progress"]["letters"]["a"]["status"] == "recognized"
    assert state["progress"]["letters"]["a"]["observations"][0]["note"] == "points at A on cereal box"


def test_progress_update_letter_rejects_invalid_status(tmp_path):
    result = run_cli(
        "progress", "update-letter", "a", "flying",
        "--deck-state", str(tmp_path / "deck-state.json"),
    )
    assert result.returncode != 0
    assert "Invalid status" in result.stdout


def test_progress_log_review_creates_session(tmp_path):
    path = tmp_path / "deck-state.json"
    result = run_cli(
        "progress", "log-review",
        "--date", "2026-04-11",
        "--duration", "15",
        "--letters", "a,d,o",
        "--notes", "she loved appel",
        "--deck-state", str(path),
    )
    assert result.returncode == 0
    assert "Review session logged" in result.stdout
    assert "Letters played: a, d, o" in result.stdout
    import json
    state = json.loads(path.read_text())
    session = state["sessions"][0]
    assert session["type"] == "review"
    assert session["letters_played"] == ["a", "d", "o"]
    assert session["duration_minutes"] == 15
    assert session["notes"] == "she loved appel"


def test_progress_log_review_appends_to_existing_sessions(tmp_path):
    path = tmp_path / "deck-state.json"
    run_cli("progress", "log-review", "--date", "2026-04-10", "--deck-state", str(path))
    run_cli("progress", "log-review", "--date", "2026-04-11", "--deck-state", str(path))
    import json
    state = json.loads(path.read_text())
    assert len(state["sessions"]) == 2


def test_progress_show_displays_summary(tmp_path):
    path = tmp_path / "deck-state.json"
    run_cli("progress", "update-letter", "a", "recognized", "--date", "2026-04-11", "--deck-state", str(path))
    run_cli("progress", "update-letter", "d", "learning", "--date", "2026-04-11", "--deck-state", str(path))
    result = run_cli("progress", "show", "--deck-state", str(path))
    assert result.returncode == 0
    assert "recognized: a" in result.stdout
    assert "learning: d" in result.stdout

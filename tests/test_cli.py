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


def test_deck_review_log_help_works():
    result = run_cli("deck", "review", "log", "--help")
    assert result.returncode == 0
    assert "--observe" in result.stdout


def test_deck_review_summary_help_works():
    result = run_cli("deck", "review", "summary", "--help")
    assert result.returncode == 0
    assert "--deck-state" in result.stdout


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


def test_deck_review_log_creates_state_and_updates_progress(tmp_path):
    deck_state = tmp_path / "deck-state.json"
    result = run_cli(
        "deck",
        "review",
        "log",
        "--deck-state",
        str(deck_state),
        "--date",
        "2026-04-11",
        "--duration",
        "15",
        "--letters",
        "a,d",
        "--observe",
        "appel:positive:points and smiles",
        "--observe",
        "deur:confused:mixes with dier",
    )
    assert result.returncode == 0
    state = json.loads(deck_state.read_text(encoding="utf-8"))
    assert state["sessions"][-1]["type"] == "review"
    assert "a" in state["progress"]["letters"]
    assert "d" in state["progress"]["letters"]


def test_deck_review_summary_outputs_recommendation(tmp_path):
    deck_state = tmp_path / "deck-state.json"
    deck_state.write_text(
        json.dumps(
            {
                "deck_protocol": "1.0",
                "printed_cards": [],
                "sessions": [],
                "progress": {
                    "letters": {
                        "a": {"status": "recognized", "observations": [{"note": "good"}]},
                        "d": {"status": "learning", "observations": [{"note": "confused"}]},
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    result = run_cli("deck", "review", "summary", "--deck-state", str(deck_state))
    assert result.returncode == 0
    assert "LEARNING PROGRESS SUMMARY" in result.stdout
    assert "Recommendation:" in result.stdout

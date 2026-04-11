"""
deck_state.py — load and validate deck-state.json.

The deck state file is machine-managed operational memory. It lives alongside
deck.csv (default: ~/.lettercards/) and tracks printed cards, sessions, and
learning progress. It is NOT checked into the engine repo.
"""

from __future__ import annotations

import json
from pathlib import Path

SUPPORTED_PROTOCOL = "1.0"
LETTER_STATUSES = [
    "not_introduced",
    "introduced",
    "learning",
    "recognized",
    "mastered",
]


def read_deck_state(path: Path) -> tuple[dict | None, str | None]:
    """
    Read deck-state.json from path.

    Returns:
        (state, error_message)
        - missing file -> (None, None)
        - valid file -> (dict, None)
        - invalid file -> (None, <message>)
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8")), None
    except FileNotFoundError:
        return None, None
    except json.JSONDecodeError as exc:
        return None, f"could not parse JSON: {exc.msg}"
    except OSError:
        return None, "could not read file"


def load_deck_state(path: Path) -> dict | None:
    """Load deck-state.json, returning None when the file is missing or invalid."""
    state, _error = read_deck_state(path)
    return state


def default_deck_state() -> dict:
    """Return a minimal valid deck-state structure."""
    return {
        "deck_protocol": SUPPORTED_PROTOCOL,
        "printed_cards": [],
        "sessions": [],
        "progress": {"letters": {}, "summary_snapshots": []},
    }


def write_deck_state(path: Path, state: dict) -> None:
    """Persist deck-state.json atomically."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    temp = target.with_suffix(".tmp")
    temp.write_text(json.dumps(state, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temp.replace(target)


def validate_deck_state(state: dict | None, csv_words: set[str]) -> list[str]:
    """
    Validate deck state against the current deck.csv word list.

    Args:
        state: Parsed deck-state.json dict, or None if the file was missing/corrupt.
        csv_words: Set of word strings from the selected deck CSV.

    Returns:
        List of warning strings. Empty list means no issues found.
    """
    if state is None:
        return []
    warnings = []

    # Check deck_protocol presence and version
    protocol = state.get("deck_protocol")
    if protocol is None:
        warnings.append(
            "deck-state.json is missing 'deck_protocol' field. "
            f"Expected \"{SUPPORTED_PROTOCOL}\". File may be from an older version."
        )
    elif protocol != SUPPORTED_PROTOCOL:
        warnings.append(
            f"deck-state.json has deck_protocol \"{protocol}\" but this engine supports "
            f"\"{SUPPORTED_PROTOCOL}\". Some features may not work correctly."
        )

    # Check that all printed_cards words exist in deck.csv
    printed_cards = state.get("printed_cards", [])
    if not isinstance(printed_cards, list):
        warnings.append(
            "deck-state.json 'printed_cards' is not a list — file may be corrupt."
        )
    else:
        for index, entry in enumerate(printed_cards):
            if not isinstance(entry, dict):
                warnings.append(
                    f"printed_cards[{index}] is malformed — expected an object."
                )
                continue

            word = entry.get("word", "")
            if not isinstance(word, str) or not word.strip():
                warnings.append(
                    f"printed_cards[{index}] is missing a valid 'word' field."
                )
                continue

            if word not in csv_words:
                warnings.append(
                    f"printed_cards contains '{word}' which is not in cards.csv. "
                    "The card may have been removed or renamed."
                )

    return warnings


def _ensure_progress_letter(state: dict, letter: str, date: str) -> dict:
    progress = state.setdefault("progress", {})
    letters = progress.setdefault("letters", {})
    letter_progress = letters.setdefault(
        letter,
        {
            "status": "not_introduced",
            "first_introduced": date,
            "observations": [],
            "evidence_count": 0,
        },
    )
    letter_progress.setdefault("status", "not_introduced")
    letter_progress.setdefault("first_introduced", date)
    letter_progress.setdefault("observations", [])
    letter_progress.setdefault("evidence_count", 0)
    return letter_progress


def _step_status(current: str, delta: int) -> str:
    if current not in LETTER_STATUSES:
        current = "not_introduced"
    index = LETTER_STATUSES.index(current)
    next_index = max(0, min(len(LETTER_STATUSES) - 1, index + delta))
    return LETTER_STATUSES[next_index]


def append_review_session(state: dict, session: dict, *, date: str) -> dict:
    """Append a normalized review session to deck-state and update letter progress."""
    sessions = state.setdefault("sessions", [])
    sessions.append(
        {
            "date": date,
            "type": "review",
            "duration_minutes": session.get("duration_minutes"),
            "letters_played": session.get("letters_played", []),
            "observations": session.get("observations", []),
        }
    )
    update_progress_from_review(state, session, date=date)
    return state


def update_progress_from_review(state: dict, session: dict, *, date: str) -> dict:
    """
    Update per-letter learning progress from a review session.

    Positive reactions gradually move a letter forward up to mastered.
    Confused/avoidant reactions move a letter one step backward (never below not_introduced).
    """
    for letter in session.get("letters_played", []):
        letter_progress = _ensure_progress_letter(state, letter, date)
        if letter_progress["status"] == "not_introduced":
            letter_progress["status"] = "introduced"

    for observation in session.get("observations", []):
        card = observation.get("card", "")
        reaction = observation.get("reaction", "")
        note = observation.get("notes", "")
        if not isinstance(card, str) or not card:
            continue
        letter = card[0].lower()
        letter_progress = _ensure_progress_letter(state, letter, date)
        letter_progress["observations"].append({"date": date, "note": note or reaction})

        if reaction in {"positive", "recognized"}:
            letter_progress["evidence_count"] += 1
            if letter_progress["evidence_count"] >= 4:
                letter_progress["status"] = "mastered"
            elif letter_progress["evidence_count"] >= 2:
                letter_progress["status"] = _step_status(letter_progress["status"], 2)
            else:
                letter_progress["status"] = _step_status(letter_progress["status"], 1)
        elif reaction in {"confused", "avoidant"}:
            letter_progress["status"] = _step_status(letter_progress["status"], -1)
    return state


def summarize_learning_progress(state: dict) -> dict:
    """Return a compact progress summary suitable for caregiver-facing reporting."""
    letters = state.get("progress", {}).get("letters", {})
    recognized = sorted([k for k, v in letters.items() if v.get("status") in {"recognized", "mastered"}])
    learning = sorted([k for k, v in letters.items() if v.get("status") in {"introduced", "learning"}])
    confused_recent = sorted(
        [
            k
            for k, v in letters.items()
            if any("confused" in str(o.get("note", "")).lower() for o in v.get("observations", [])[-3:])
        ]
    )
    recommendation = (
        "Focus next sessions on letters in progress."
        if learning
        else "Introduce one new letter with familiar words."
    )
    return {
        "recognized_or_mastered": recognized,
        "in_progress": learning,
        "confused_recently": confused_recent,
        "recommendation": recommendation,
    }

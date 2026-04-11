"""
deck_state.py — load, validate, and write deck-state.json.

The deck state file is machine-managed operational memory. It lives alongside
deck.csv (default: ~/.lettercards/) and tracks printed cards, sessions, and
learning progress. It is NOT checked into the engine repo.
"""

from __future__ import annotations

import json
from datetime import date as _date
from pathlib import Path

SUPPORTED_PROTOCOL = "1.0"

VALID_LETTER_STATUSES = frozenset({
    "not_introduced", "introduced", "learning", "recognized", "mastered"
})


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


def new_deck_state() -> dict:
    """Return a fresh, empty deck state with the current protocol version."""
    return {
        "deck_protocol": SUPPORTED_PROTOCOL,
        "next_batch": [],
        "printed_cards": [],
        "sessions": [],
        "progress": {"letters": {}, "summary_snapshots": []},
    }


def write_deck_state(path: Path, state: dict) -> None:
    """Write deck-state.json atomically (write to .tmp then rename)."""
    content = json.dumps(state, indent=2, ensure_ascii=False) + "\n"
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(content, encoding="utf-8")
    tmp.replace(path)


def add_review_session(state: dict, session: dict) -> None:
    """Append a review session entry to state['sessions'] in-place."""
    state.setdefault("sessions", []).append(session)


def update_letter_progress(
    state: dict,
    letter: str,
    status: str,
    note: str | None = None,
    date_str: str | None = None,
) -> None:
    """Update or create a letter's progress entry in-place.

    If the letter has no entry yet, creates one with ``first_introduced`` set
    to today (or ``date_str``). Always sets ``status``. Appends ``note`` to
    observations when provided.
    """
    today = date_str or str(_date.today())
    letters = state.setdefault("progress", {}).setdefault("letters", {})
    entry = letters.get(letter)
    if entry is None:
        entry = {"status": status, "first_introduced": today, "observations": []}
        letters[letter] = entry
    else:
        entry["status"] = status
    if note:
        entry.setdefault("observations", []).append({"date": today, "note": note})


def format_progress_summary(state: dict) -> str:
    """Return a human-readable progress summary string."""
    letters = state.get("progress", {}).get("letters", {})

    if not letters:
        return "No progress recorded yet."

    by_status: dict[str, list[str]] = {}
    for letter, entry in sorted(letters.items()):
        s = entry.get("status", "unknown")
        by_status.setdefault(s, []).append(letter)

    lines = ["Progress summary:"]
    for s in ("mastered", "recognized", "learning", "introduced", "not_introduced"):
        lts = by_status.get(s, [])
        if lts:
            lines.append(f"  {s}: {', '.join(lts)}")
    unknown = by_status.get("unknown", [])
    if unknown:
        lines.append(f"  unknown: {', '.join(unknown)}")

    reviews = [s for s in state.get("sessions", []) if s.get("type") == "review"]
    if reviews:
        last = reviews[-1]
        lines.append(f"\nLast review: {last.get('date', 'unknown')}")
        if last.get("letters_played"):
            lines.append(f"  Letters played: {', '.join(last['letters_played'])}")
        if last.get("duration_minutes"):
            lines.append(f"  Duration: {last['duration_minutes']} minutes")

    return "\n".join(lines)

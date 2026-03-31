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

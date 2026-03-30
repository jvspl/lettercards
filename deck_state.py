"""
deck_state.py — load and validate deck-state.json.

The deck state file is machine-managed operational memory. It lives alongside
deck.csv (default: ~/.lettercards/) and tracks printed cards, sessions, and
learning progress. It is NOT checked into the engine repo.

Usage:
    from deck_state import load_deck_state, validate_deck_state

    state = load_deck_state(path)          # Returns dict or None
    warnings = validate_deck_state(state, csv_words)  # Returns list of strings
"""

import json
from pathlib import Path
from typing import Optional

SUPPORTED_PROTOCOL = "1.0"


def load_deck_state(path: Path) -> Optional[dict]:
    """
    Load deck-state.json from path.

    Returns the parsed dict, or None if the file does not exist or cannot be parsed.
    Never raises — a missing or corrupt deck-state.json is handled gracefully.
    """
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (json.JSONDecodeError, OSError):
        return None


def validate_deck_state(state: Optional[dict], csv_words: set) -> list:
    """
    Validate deck state against the current deck.csv word list.

    Args:
        state: Parsed deck-state.json dict, or None if the file was missing/corrupt.
        csv_words: Set of word strings from cards.csv (all active words).

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
        for entry in printed_cards:
            word = entry.get("word", "")
            if word and word not in csv_words:
                warnings.append(
                    f"printed_cards contains '{word}' which is not in cards.csv. "
                    "The card may have been removed or renamed."
                )

    return warnings

# Phase 1b: deck-state.json Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Introduce `deck-state.json` as machine-managed operational memory — tracking printed cards, sessions, and learning progress — and wire it into the generate.py startup validation and `--status` command.

**Architecture:** A new `deck_state.py` module handles all loading and validation of `deck-state.json`, keeping that logic out of `generate.py`. The `generate.py` main() function calls this module on startup to print warnings, and exposes a `--status` flag that prints a human-readable summary. The file is added to `.gitignore` because it belongs to the user deck, not the engine repo.

**Tech Stack:** Python 3.10+, stdlib only (`json`, `pathlib`). No new dependencies. Tests use `pytest` with `tmp_path` fixture. Run tests via `venv/bin/pytest tests/`.

---

## File Structure

| File | Action | Responsibility |
|------|--------|----------------|
| `deck_state.py` | Create | Load and validate `deck-state.json`; return structured data and warnings |
| `deck-state.example.json` | Create | Schema reference / documentation artifact |
| `generate.py` | Modify | Add `--status` flag; call validation on startup; import from `deck_state` |
| `.gitignore` | Modify | Add `deck-state.json` |
| `tests/test_deck_state.py` | Create | All tests for `deck_state.py` and generate.py integration |

---

## Task 1: deck_state.py — load and validate

**Files:**
- Create: `deck_state.py`
- Create: `tests/test_deck_state.py`

- [ ] **Step 1: Write the failing tests**

Create `tests/test_deck_state.py`:

```python
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
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
venv/bin/pytest tests/test_deck_state.py -v
```

Expected: `ModuleNotFoundError: No module named 'deck_state'`

- [ ] **Step 3: Create deck_state.py**

```python
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

SUPPORTED_PROTOCOL = "1.0"


def load_deck_state(path: Path) -> dict | None:
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


def validate_deck_state(state: dict, csv_words: set) -> list:
    """
    Validate deck state against the current deck.csv word list.

    Args:
        state: Parsed deck-state.json dict.
        csv_words: Set of word strings from cards.csv (all active words).

    Returns:
        List of warning strings. Empty list means no issues found.
    """
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
    for entry in state.get("printed_cards", []):
        word = entry.get("word", "")
        if word and word not in csv_words:
            warnings.append(
                f"printed_cards contains '{word}' which is not in cards.csv. "
                "The card may have been removed or renamed."
            )

    return warnings
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
venv/bin/pytest tests/test_deck_state.py -v
```

Expected: All 10 tests pass.

- [ ] **Step 5: Commit**

```bash
git add deck_state.py tests/test_deck_state.py
git commit -m "feat: add deck_state module — load and validate deck-state.json (#101)"
```

---

## Task 2: deck-state.example.json and .gitignore

**Files:**
- Create: `deck-state.example.json`
- Modify: `.gitignore`

- [ ] **Step 1: Create deck-state.example.json**

This file documents the schema and ships as a reference. It is NOT the actual user file.

```json
{
  "deck_protocol": "1.0",
  "next_batch": ["h", "k", "n"],
  "printed_cards": [
    {"word": "appel", "printed_date": "2026-03-20"},
    {"word": "deur", "printed_date": "2026-03-20"},
    {"word": "eend", "printed_date": "2026-03-20"},
    {"word": "oma", "printed_date": "2026-03-20"}
  ],
  "sessions": [
    {
      "date": "2026-03-18",
      "type": "generation",
      "summary": "Added words: appel, aap, auto for letter A",
      "cards_added": ["appel", "aap", "auto"],
      "cards_modified": []
    },
    {
      "date": "2026-03-20",
      "type": "print",
      "letters": ["a", "d", "e", "o"],
      "card_count": 12,
      "notes": "Printed on 160gsm, laminated"
    },
    {
      "date": "2026-03-22",
      "type": "review",
      "duration_minutes": 15,
      "letters_played": ["a", "d", "o"],
      "observations": [
        {
          "card": "appel",
          "reaction": "positive",
          "notes": "Points and says 'appel!' immediately"
        },
        {
          "card": "wolf",
          "reaction": "confused",
          "notes": "Says 'hond' instead"
        }
      ]
    }
  ],
  "progress": {
    "letters": {
      "a": {
        "status": "recognized",
        "first_introduced": "2026-03-20",
        "observations": [
          {"date": "2026-03-22", "note": "Points at A on cereal box"}
        ]
      },
      "d": {
        "status": "learning",
        "first_introduced": "2026-03-20",
        "observations": [
          {"date": "2026-03-22", "note": "Knows 'deur' but doesn't connect to letter yet"}
        ]
      }
    },
    "summary_snapshots": [
      {
        "date": "2026-03-25",
        "total_letters_introduced": 6,
        "recognized": ["a", "o"],
        "learning": ["d", "e"],
        "not_yet": ["w", "z"],
        "notes": "Good progress on vowels"
      }
    ]
  }
}
```

- [ ] **Step 2: Add deck-state.json to .gitignore**

Current `.gitignore` contents:
```
*.pyc
__pycache__/
.DS_Store
venv/
letterkaarten.pdf
.tmp/
```

Add this line after `letterkaarten.pdf`:
```
deck-state.json
```

Final `.gitignore`:
```
*.pyc
__pycache__/
.DS_Store
venv/
letterkaarten.pdf
deck-state.json
.tmp/
```

- [ ] **Step 3: Verify deck-state.json is ignored**

```bash
echo '{}' > deck-state.json
git status
```

Expected: `deck-state.json` does NOT appear in git status output (it's ignored).

```bash
rm deck-state.json
```

- [ ] **Step 4: Commit**

```bash
git add deck-state.example.json .gitignore
git commit -m "chore: add deck-state.example.json schema reference and gitignore entry (#101)"
```

---

## Task 3: generate.py integration — startup validation and --status

**Files:**
- Modify: `generate.py`
- Modify: `tests/test_deck_state.py` (add integration tests)

The `--status` flag prints a deck summary and exits without generating a PDF.
On every normal run, if `deck-state.json` exists, validate it and print any warnings.

- [ ] **Step 1: Write the failing integration tests**

Append to `tests/test_deck_state.py`:

```python
# ── generate.py integration ───────────────────────────────────────────────────

import subprocess
import sys
from pathlib import Path


def write_csv_for_status(tmp_path, rows="a,appel,appel.png,,no\nd,deur,deur.png,,no\n"):
    csv_file = tmp_path / "cards.csv"
    csv_file.write_text("letter,word,image,font,personal\n" + rows)
    return csv_file


def test_status_flag_prints_summary(tmp_path):
    write_csv_for_status(tmp_path)
    state = {
        "deck_protocol": "1.0",
        "printed_cards": [{"word": "appel", "printed_date": "2026-03-20"}],
        "sessions": [],
    }
    (tmp_path / "deck-state.json").write_text(json.dumps(state))

    result = subprocess.run(
        [sys.executable, "generate.py", "--status", "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(tmp_path / "deck-state.json")],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "appel" in result.stdout
    assert "printed" in result.stdout.lower()


def test_status_flag_works_without_deck_state_file(tmp_path):
    write_csv_for_status(tmp_path)

    result = subprocess.run(
        [sys.executable, "generate.py", "--status", "--csv", str(tmp_path / "cards.csv"),
         "--deck-state", str(tmp_path / "nonexistent.json")],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "no deck-state" in result.stdout.lower() or "not found" in result.stdout.lower()


def test_startup_validation_prints_warning_for_unknown_protocol(tmp_path):
    write_csv_for_status(tmp_path)
    state = {"deck_protocol": "99.0", "printed_cards": []}
    (tmp_path / "deck-state.json").write_text(json.dumps(state))
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
    # Should complete without errors or protocol warnings
    assert "deck_protocol" not in result.stdout
    assert "deck_protocol" not in result.stderr
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
venv/bin/pytest tests/test_deck_state.py::test_status_flag_prints_summary -v
```

Expected: FAIL — `generate.py` doesn't accept `--deck-state` or `--status` yet.

- [ ] **Step 3: Modify generate.py**

Add the import at the top of the imports block (after `from PIL import Image`):

```python
from deck_state import load_deck_state, validate_deck_state
```

Add two new argparse arguments inside `main()`, after the `--safe-letters-only` argument:

```python
    parser.add_argument('--status', action='store_true',
                        help='Show deck status summary and exit (no PDF generated)')
    parser.add_argument('--deck-state', type=str, default=None,
                        help='Path to deck-state.json (default: deck-state.json next to cards.csv)')
```

Add the deck state path resolution after `personal_dir = get_personal_images_dir(args.personal_dir)`:

```python
    # Resolve deck state path
    deck_state_path = Path(args.deck_state) if args.deck_state else csv_path.parent / 'deck-state.json'
```

Add `--status` handling after `deck_state_path` resolution, before the font registration block:

```python
    # --status: print deck summary and exit
    if args.status:
        state = load_deck_state(deck_state_path)
        if state is None:
            print(f"No deck-state.json found at {deck_state_path}")
            print("Run some print sessions to start tracking your deck.")
        else:
            cards = load_cards(csv_path)
            csv_words = {c['word'] for c in cards}
            warnings = validate_deck_state(state, csv_words)
            if warnings:
                print("Warnings:")
                for w in warnings:
                    print(f"  ⚠ {w}")
                print()
            printed = state.get('printed_cards', [])
            active_words = csv_words
            not_printed = active_words - {e.get('word') for e in printed}
            print(f"Active cards in deck.csv: {len(active_words)}")
            print(f"Printed cards in inventory: {len(printed)}")
            if not_printed:
                print(f"Not yet printed ({len(not_printed)}): {', '.join(sorted(not_printed))}")
            else:
                print("All active cards have been printed.")
            sessions = state.get('sessions', [])
            print(f"Recorded sessions: {len(sessions)}")
            next_batch = state.get('next_batch', [])
            if next_batch:
                print(f"Next planned batch: {', '.join(next_batch)}")
        sys.exit(0)
```

Add startup validation after the `--status` block (still inside `main()`, before font registration):

```python
    # Startup validation: warn about deck state issues, but don't abort
    state = load_deck_state(deck_state_path)
    if state is not None:
        cards_for_validation = load_cards(csv_path)
        csv_words = {c['word'] for c in cards_for_validation}
        warnings = validate_deck_state(state, csv_words)
        for w in warnings:
            print(f"⚠ deck-state warning: {w}")
```

The final `main()` function should look like this (complete replacement from line 497):

```python
def main():
    parser = argparse.ArgumentParser(description="Generate letter learning cards as PDF")
    parser.add_argument('--letters', type=str, default=None,
                        help='Comma-separated letters to include (e.g., a,d,o)')
    parser.add_argument('--font', type=str, default=None,
                        help='Override font for all cards')
    parser.add_argument('--output', type=str, default='letterkaarten.pdf',
                        help='Output PDF filename')
    parser.add_argument('--no-placeholders', action='store_true',
                        help='Skip generating placeholder images')
    parser.add_argument('--csv', type=str, default='cards.csv',
                        help='Path to the CSV config file')
    parser.add_argument('--personal-dir', type=str, default=None,
                        help='Directory for personal photos (default: ~/.lettercards/personal/)')
    parser.add_argument('--safe-letters-only', action='store_true',
                        help='Exclude any letter that has at least one personal=yes card (useful for screenshots)')
    parser.add_argument('--status', action='store_true',
                        help='Show deck status summary and exit (no PDF generated)')
    parser.add_argument('--deck-state', type=str, default=None,
                        help='Path to deck-state.json (default: deck-state.json next to cards.csv)')
    args = parser.parse_args()

    base_dir = Path(__file__).parent
    csv_path = base_dir / args.csv
    images_dir = base_dir / "images"
    personal_dir = get_personal_images_dir(args.personal_dir)
    output_path = base_dir / args.output

    # Resolve deck state path
    deck_state_path = Path(args.deck_state) if args.deck_state else csv_path.parent / 'deck-state.json'

    # --status: print deck summary and exit
    if args.status:
        state = load_deck_state(deck_state_path)
        if state is None:
            print(f"No deck-state.json found at {deck_state_path}")
            print("Run some print sessions to start tracking your deck.")
        else:
            cards = load_cards(csv_path)
            csv_words = {c['word'] for c in cards}
            warnings = validate_deck_state(state, csv_words)
            if warnings:
                print("Warnings:")
                for w in warnings:
                    print(f"  ⚠ {w}")
                print()
            printed = state.get('printed_cards', [])
            active_words = csv_words
            not_printed = active_words - {e.get('word') for e in printed}
            print(f"Active cards in deck.csv: {len(active_words)}")
            print(f"Printed cards in inventory: {len(printed)}")
            if not_printed:
                print(f"Not yet printed ({len(not_printed)}): {', '.join(sorted(not_printed))}")
            else:
                print("All active cards have been printed.")
            sessions = state.get('sessions', [])
            print(f"Recorded sessions: {len(sessions)}")
            next_batch = state.get('next_batch', [])
            if next_batch:
                print(f"Next planned batch: {', '.join(next_batch)}")
        sys.exit(0)

    # Startup validation: warn about deck state issues, but don't abort
    state = load_deck_state(deck_state_path)
    if state is not None:
        cards_for_validation = load_cards(csv_path)
        csv_words = {c['word'] for c in cards_for_validation}
        warnings = validate_deck_state(state, csv_words)
        for w in warnings:
            print(f"⚠ deck-state warning: {w}")

    # Register fonts
    available_fonts = register_fonts()
    print(f"Available fonts: {', '.join(available_fonts) or 'Helvetica (built-in)'}")

    # Parse letter filter
    letters_filter = None
    if args.safe_letters_only:
        safe = get_safe_letters(csv_path)
        letters_filter = sorted(safe)
        print(f"Safe letters (no personal=yes entries): {', '.join(letters_filter)}")
    elif args.letters:
        letters_filter = [l.strip().lower() for l in args.letters.split(',')]
        print(f"Filtering letters: {', '.join(letters_filter)}")

    # Load cards
    cards = load_cards(csv_path, letters_filter)
    if not cards:
        print("No cards found! Check your CSV file.")
        sys.exit(1)

    print(f"Loaded {len(cards)} card entries")

    # Generate placeholder images
    if not args.no_placeholders:
        print("\nGenerating placeholder images...")
        generate_placeholder_images(cards, images_dir)

    # Generate PDF
    print(f"\nPersonal images dir: {personal_dir}")
    print("Generating PDF...")
    generate_pdf(cards, output_path, images_dir, personal_dir, available_fonts, args.font)


if __name__ == '__main__':
    main()
```

- [ ] **Step 4: Run all tests**

```bash
venv/bin/pytest tests/test_deck_state.py -v
```

Expected: All 14 tests pass.

Also run the full test suite to verify nothing is broken:

```bash
venv/bin/pytest tests/ -v
```

Expected: All tests pass.

- [ ] **Step 5: Manual smoke test**

```bash
python generate.py --status
```

Expected output (when no `deck-state.json` exists in repo root):
```
No deck-state.json found at /path/to/lettercards/deck-state.json
Run some print sessions to start tracking your deck.
```

```bash
cp deck-state.example.json deck-state.json
python generate.py --status
```

Expected: Shows counts of active cards, printed cards, sessions, and next batch.

```bash
rm deck-state.json
```

- [ ] **Step 6: Commit**

```bash
git add generate.py tests/test_deck_state.py
git commit -m "feat: add --status flag and startup validation to generate.py (#101)"
```

---

## Self-Review

### Spec coverage

| Acceptance criterion | Task |
|---------------------|------|
| `deck-state.json` schema defined | Task 2 (`deck-state.example.json`) |
| Engine validates `deck_protocol` version on startup; warns if missing | Task 3 (startup validation in `generate.py`) |
| Engine validates `printed_cards` words exist in `deck.csv` | Task 1 (`validate_deck_state`) + Task 3 |
| `lettercards status` (or equivalent) prints a summary | Task 3 (`--status` flag) |
| File in `.gitignore` | Task 2 |
| Tests: valid file, missing file (graceful), mismatched protocol version | Task 1 + Task 3 |

All criteria covered.

### Placeholder scan

No TBD, TODO, or vague placeholders found.

### Type consistency

- `load_deck_state(path: Path) -> dict | None` — used identically in Task 1 and Task 3
- `validate_deck_state(state: dict, csv_words: set) -> list` — used identically in Task 1 and Task 3
- `deck_state_path` — Path object in all uses
- `csv_words` — set of strings in all uses

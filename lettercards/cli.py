from __future__ import annotations

import argparse
from pathlib import Path

import generate
import pictogram_workflow
import process_photo
from deck_state import (
    add_review_session,
    format_progress_summary,
    new_deck_state,
    read_deck_state,
    update_letter_progress,
    validate_deck_state,
    VALID_LETTER_STATUSES,
    write_deck_state,
)


def default_csv_argument() -> str:
    base_dir = Path(generate.__file__).resolve().parent
    if (base_dir / "deck.csv").exists():
        return "deck.csv"
    if (base_dir / "cards.csv").exists():
        return "cards.csv"
    return "deck.csv"


def build_generate_argv(args: argparse.Namespace, *, status: bool = False) -> list[str]:
    argv: list[str] = []
    csv_value = args.csv if args.csv is not None else default_csv_argument()
    argv.extend(["--csv", csv_value])
    if status:
        argv.append("--status")
    elif args.letters:
        argv.extend(["--letters", args.letters])
    if getattr(args, "font", None):
        argv.extend(["--font", args.font])
    if getattr(args, "output", None):
        argv.extend(["--output", args.output])
    if getattr(args, "no_placeholders", False):
        argv.append("--no-placeholders")
    if getattr(args, "personal_dir", None):
        argv.extend(["--personal-dir", args.personal_dir])
    if getattr(args, "safe_letters_only", False):
        argv.append("--safe-letters-only")
    if getattr(args, "deck_state", None):
        argv.extend(["--deck-state", args.deck_state])
    return argv


def cmd_generate(args: argparse.Namespace) -> int:
    return generate.main(build_generate_argv(args))


def cmd_status(args: argparse.Namespace) -> int:
    return generate.main(build_generate_argv(args, status=True))


def cmd_photo_process(args: argparse.Namespace) -> int:
    argv: list[str] = []
    if args.list:
        argv.append("--list")
    if args.preview:
        argv.append("--preview")
    if args.size is not None:
        argv.extend(["--size", str(args.size)])
    if args.force:
        argv.append("--force")
    if args.name:
        argv.append(args.name)
    if args.source:
        argv.append(args.source)
    return process_photo.main(argv)


def cmd_pictogram_status(args: argparse.Namespace) -> int:
    argv = ["status"]
    if args.verbose:
        argv.append("--verbose")
    return pictogram_workflow.main(argv)


def cmd_pictogram_prompt(args: argparse.Namespace) -> int:
    argv = ["prompt"]
    if args.missing:
        argv.append("--missing")
    argv.extend(args.words)
    return pictogram_workflow.main(argv)


def cmd_pictogram_split(args: argparse.Namespace) -> int:
    argv = ["split"]
    argv.extend(args.names)
    if args.image:
        argv.extend(["--image", args.image])
    if args.grid:
        argv.extend(["--grid", args.grid])
    if args.preview:
        argv.append("--preview")
    if args.keep:
        argv.append("--keep")
    if args.remove_bg:
        argv.append("--remove-bg")
    return pictogram_workflow.main(argv)


def cmd_deck_check(args: argparse.Namespace) -> int:
    base_dir = Path(generate.__file__).resolve().parent
    csv_arg = args.csv if args.csv is not None else default_csv_argument()
    csv_path = base_dir / csv_arg
    deck_state_path = Path(args.deck_state) if args.deck_state else csv_path.parent / "deck-state.json"
    personal_dir = generate.get_personal_images_dir(args.personal_dir)
    images_dir = base_dir / "images"

    issues: list[str] = []

    try:
        csv_words = generate.load_all_deck_words(csv_path)
        cards = generate.load_cards(csv_path)
    except FileNotFoundError:
        print(f"Error: deck CSV not found: {csv_path}")
        return 1

    if not csv_words:
        issues.append("No deck words found in the selected CSV.")

    state, state_error = read_deck_state(deck_state_path)
    if state_error:
        issues.append(f"Could not read deck-state.json: {state_error}")
    elif state is not None:
        issues.extend(validate_deck_state(state, csv_words))

    for card in cards:
        image_path = generate.get_image_path(card, images_dir, personal_dir)
        if image_path is None:
            issues.append(f"Missing image for '{card['word']}' ({card['image'] or 'no image specified'}).")

    if issues:
        print("Deck check found issues:\n")
        for issue in issues:
            print(f"- {issue}")
        return 1

    print("Deck check passed.")
    print(f"Cards checked: {len(cards)}")
    print(f"CSV: {csv_path}")
    if state is not None:
        print(f"Deck state: {deck_state_path}")
    return 0


def _deck_state_path(args: argparse.Namespace) -> Path:
    """Resolve the deck-state.json path from CLI args."""
    if getattr(args, "deck_state", None):
        return Path(args.deck_state)
    csv_arg = args.csv if getattr(args, "csv", None) is not None else default_csv_argument()
    base_dir = Path(generate.__file__).resolve().parent
    csv_path = base_dir / csv_arg
    return csv_path.parent / "deck-state.json"


def cmd_progress_show(args: argparse.Namespace) -> int:
    path = _deck_state_path(args)
    state, error = read_deck_state(path)
    if error:
        print(f"Error reading deck-state.json: {error}")
        return 1
    if state is None:
        print("No deck-state.json found. No progress recorded yet.")
        return 0
    print(format_progress_summary(state))
    return 0


def cmd_progress_update_letter(args: argparse.Namespace) -> int:
    if args.status not in VALID_LETTER_STATUSES:
        print(f"Invalid status '{args.status}'. Valid values: {', '.join(sorted(VALID_LETTER_STATUSES))}")
        return 1
    path = _deck_state_path(args)
    state, error = read_deck_state(path)
    if error:
        print(f"Error reading deck-state.json: {error}")
        return 1
    if state is None:
        state = new_deck_state()
    update_letter_progress(state, args.letter, args.status, note=args.note, date_str=args.date)
    write_deck_state(path, state)
    print(f"Updated letter '{args.letter}' → {args.status}")
    if args.note:
        print(f"  Note: {args.note}")
    return 0


def cmd_progress_log_review(args: argparse.Namespace) -> int:
    from datetime import date as _date
    path = _deck_state_path(args)
    state, error = read_deck_state(path)
    if error:
        print(f"Error reading deck-state.json: {error}")
        return 1
    if state is None:
        state = new_deck_state()
    session: dict = {"type": "review", "date": args.date or str(_date.today())}
    if args.duration is not None:
        session["duration_minutes"] = args.duration
    if args.letters:
        session["letters_played"] = [lt.strip() for lt in args.letters.split(",")]
    if args.notes:
        session["notes"] = args.notes
    add_review_session(state, session)
    write_deck_state(path, state)
    print(f"Review session logged for {session['date']}")
    if session.get("letters_played"):
        print(f"  Letters played: {', '.join(session['letters_played'])}")
    if session.get("duration_minutes"):
        print(f"  Duration: {session['duration_minutes']} minutes")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Unified CLI for lettercards workflows")
    subparsers = parser.add_subparsers(dest="command")

    generate_parser = subparsers.add_parser("generate", help="Generate PDF cards")
    generate_parser.add_argument("--letters", type=str, default=None, help="Comma-separated letters to include (e.g., a,d,o)")
    generate_parser.add_argument("--font", type=str, default=None, help="Override font for all cards")
    generate_parser.add_argument("--output", type=str, default="letterkaarten.pdf", help="Output PDF filename")
    generate_parser.add_argument("--no-placeholders", dest="no_placeholders", action="store_true", help="Skip generating placeholder images")
    generate_parser.add_argument("--csv", type=str, default=None, help="Path to the deck CSV config file")
    generate_parser.add_argument("--personal-dir", type=str, default=None, help="Directory for personal photos")
    generate_parser.add_argument("--safe-letters-only", action="store_true", help="Exclude letters with personal cards")
    generate_parser.set_defaults(func=cmd_generate)

    status_parser = subparsers.add_parser("status", help="Show deck summary")
    status_parser.add_argument("--csv", type=str, default=None, help="Path to the deck CSV config file")
    status_parser.add_argument("--deck-state", type=str, default=None, help="Path to deck-state.json")
    status_parser.set_defaults(func=cmd_status)

    photo_parser = subparsers.add_parser("photo", help="Personal photo workflow")
    photo_subparsers = photo_parser.add_subparsers(dest="photo_command")
    photo_process_parser = photo_subparsers.add_parser("process", help="Process a personal photo")
    photo_process_parser.add_argument("name", nargs="?", help='Output name (without extension), e.g. "oma"')
    photo_process_parser.add_argument("source", nargs="?", help="Source filename in staging folder")
    photo_process_parser.add_argument("--list", "-l", action="store_true", help="List images in staging folder")
    photo_process_parser.add_argument("--preview", "-p", action="store_true", help="Preview only, do not save")
    photo_process_parser.add_argument("--size", "-s", type=int, default=process_photo.DEFAULT_SIZE, help=f"Output size in pixels (default: {process_photo.DEFAULT_SIZE})")
    photo_process_parser.add_argument("--force", "-f", action="store_true", help="Overwrite existing file")
    photo_process_parser.set_defaults(func=cmd_photo_process)

    pictogram_parser = subparsers.add_parser("pictogram", help="Pictogram workflow")
    pictogram_subparsers = pictogram_parser.add_subparsers(dest="pictogram_command")
    pictogram_status_parser = pictogram_subparsers.add_parser("status", help="Show image status")
    pictogram_status_parser.add_argument("--verbose", "-v", action="store_true", help="Show all images including OK ones")
    pictogram_status_parser.set_defaults(func=cmd_pictogram_status)

    pictogram_prompt_parser = pictogram_subparsers.add_parser("prompt", help="Generate ChatGPT prompts")
    pictogram_prompt_parser.add_argument("words", nargs="*", help="Words to generate images for")
    pictogram_prompt_parser.add_argument("--missing", "-m", action="store_true", help="Generate prompts for all missing images")
    pictogram_prompt_parser.set_defaults(func=cmd_pictogram_prompt)

    pictogram_split_parser = pictogram_subparsers.add_parser("split", help="Split grid image")
    pictogram_split_parser.add_argument("names", nargs="*", help="Names for each image (in order)")
    pictogram_split_parser.add_argument("--image", "-i", help="Specific image file in staging")
    pictogram_split_parser.add_argument("--grid", "-g", help="Grid layout, e.g., 3x2")
    pictogram_split_parser.add_argument("--preview", "-p", action="store_true", help="Preview without saving")
    pictogram_split_parser.add_argument("--keep", "-k", action="store_true", help="Keep staging image after processing")
    pictogram_split_parser.add_argument("--remove-bg", action="store_true", help="Remove white background")
    pictogram_split_parser.set_defaults(func=cmd_pictogram_split)

    deck_parser = subparsers.add_parser("deck", help="Deck maintenance commands")
    deck_subparsers = deck_parser.add_subparsers(dest="deck_command")
    deck_check_parser = deck_subparsers.add_parser(
        "check",
        help="Validate deck integrity",
        description="Validate deck integrity",
    )
    deck_check_parser.add_argument("--csv", type=str, default=None, help="Path to the deck CSV config file")
    deck_check_parser.add_argument("--deck-state", type=str, default=None, help="Path to deck-state.json")
    deck_check_parser.add_argument("--personal-dir", type=str, default=None, help="Directory for personal photos")
    deck_check_parser.set_defaults(func=cmd_deck_check)

    progress_parser = subparsers.add_parser("progress", help="Learning progress tracking")
    progress_subparsers = progress_parser.add_subparsers(dest="progress_command")

    progress_show_parser = progress_subparsers.add_parser("show", help="Show progress summary")
    progress_show_parser.add_argument("--deck-state", type=str, default=None, help="Path to deck-state.json")
    progress_show_parser.add_argument("--csv", type=str, default=None, help="Path to the deck CSV (used to locate deck-state.json)")
    progress_show_parser.set_defaults(func=cmd_progress_show)

    progress_update_parser = progress_subparsers.add_parser(
        "update-letter", help="Update a letter's learning status"
    )
    progress_update_parser.add_argument("letter", help="The letter to update (e.g. a)")
    progress_update_parser.add_argument(
        "status",
        help=f"New status. One of: {', '.join(sorted(VALID_LETTER_STATUSES))}",
    )
    progress_update_parser.add_argument("--note", type=str, default=None, help="Optional observation note")
    progress_update_parser.add_argument("--date", type=str, default=None, help="Date for the update (YYYY-MM-DD, default: today)")
    progress_update_parser.add_argument("--deck-state", type=str, default=None, help="Path to deck-state.json")
    progress_update_parser.add_argument("--csv", type=str, default=None, help="Path to the deck CSV (used to locate deck-state.json)")
    progress_update_parser.set_defaults(func=cmd_progress_update_letter)

    progress_log_parser = progress_subparsers.add_parser("log-review", help="Log a review session")
    progress_log_parser.add_argument("--date", type=str, default=None, help="Session date (YYYY-MM-DD, default: today)")
    progress_log_parser.add_argument("--duration", type=int, default=None, metavar="MINUTES", help="Duration in minutes")
    progress_log_parser.add_argument("--letters", type=str, default=None, help="Comma-separated letters played (e.g. a,d,o)")
    progress_log_parser.add_argument("--notes", type=str, default=None, help="Free-text session notes")
    progress_log_parser.add_argument("--deck-state", type=str, default=None, help="Path to deck-state.json")
    progress_log_parser.add_argument("--csv", type=str, default=None, help="Path to the deck CSV (used to locate deck-state.json)")
    progress_log_parser.set_defaults(func=cmd_progress_log_review)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)

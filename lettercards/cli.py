from __future__ import annotations

import argparse
import shutil
from pathlib import Path

import generate
import pictogram_workflow
import process_photo
from deck_state import read_deck_state, validate_deck_state


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
    images_dirs = [csv_path.parent / "images", base_dir / "starter-deck" / "images", base_dir / "images"]

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
        image_path = generate.get_image_path(card, images_dirs, personal_dir)
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


def cmd_deck_init(args: argparse.Namespace) -> int:
    base_dir = Path(generate.__file__).resolve().parent
    starter_dir = base_dir / "starter-deck"
    starter_csv = starter_dir / "deck.csv"
    starter_images = starter_dir / "images"

    if not starter_csv.exists() or not starter_images.exists():
        print(f"Error: starter deck assets not found in {starter_dir}")
        return 1

    target_dir = Path(args.path).resolve()
    target_csv = target_dir / "deck.csv"
    target_images = target_dir / "images"
    target_dir.mkdir(parents=True, exist_ok=True)

    if target_csv.exists() and not args.force:
        print(f"Error: {target_csv} already exists. Use --force to overwrite.")
        return 1
    if target_images.exists() and not args.force:
        print(f"Error: {target_images} already exists. Use --force to overwrite.")
        return 1

    if args.force and target_csv.exists():
        target_csv.unlink()
    if args.force and target_images.exists():
        shutil.rmtree(target_images)

    shutil.copy2(starter_csv, target_csv)
    shutil.copytree(starter_images, target_images)

    print(f"Initialized starter deck in {target_dir}")
    print(f"- {target_csv}")
    print(f"- {target_images}")
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

    deck_init_parser = deck_subparsers.add_parser(
        "init",
        help="Initialize a starter deck in a target directory",
        description="Initialize a starter deck in a target directory",
    )
    deck_init_parser.add_argument("--path", type=str, default=".", help="Target directory (default: current directory)")
    deck_init_parser.add_argument("--force", action="store_true", help="Overwrite existing deck.csv/images if present")
    deck_init_parser.set_defaults(func=cmd_deck_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not hasattr(args, "func"):
        parser.print_help()
        return 0
    return args.func(args)

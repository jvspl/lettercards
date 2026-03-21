#!/usr/bin/env python3
"""
Pictogram Workflow for Letter Cards

Helps generate child-friendly pictogram images using ChatGPT/DALL-E.

WHY CHATGPT?
    - ChatGPT/DALL-E produces high-quality, child-friendly illustrations
    - Claude's image generation doesn't match the quality we need
    - We use ChatGPT's free tier, which has rate limits
    - Grid images (6 per request) maximize efficiency within rate limits
    - This script automates the splitting/processing to make the workflow fast

Usage:
    python pictogram_workflow.py status              # Show which images need work
    python pictogram_workflow.py prompt WORD...      # Generate ChatGPT prompt for words
    python pictogram_workflow.py prompt --missing    # Generate prompt for all missing images
    python pictogram_workflow.py split               # Split grid image(s) from staging
    python pictogram_workflow.py split --preview     # Preview split without saving

Workflow:
    1. Run 'status' to see what images are missing or need improvement
    2. Run 'prompt appel auto deur' to get a ChatGPT prompt
    3. Paste prompt in ChatGPT, download the grid image
    4. Drop grid image in ~/.lettercards/staging/
    5. Run 'split' to extract individual images
"""

import argparse
import csv
import os
import sys
from pathlib import Path

try:
    from PIL import Image
except ImportError:
    print("Pillow not installed. Run: pip install Pillow")
    sys.exit(1)


# ── Configuration ──────────────────────────────────────────────────────────

STAGING_DIR = Path.home() / '.lettercards' / 'staging'
IMAGES_DIR = Path(__file__).parent / 'images'
CARDS_CSV = Path(__file__).parent / 'cards.csv'
SOURCES_MD = Path(__file__).parent / 'images' / 'SOURCES.md'

# Style guidance for consistent illustrations
# Inspired by Dutch children's books that Lena loves:
# - Nijntje (Miffy): simple, rounded, minimalist
# - Dikkie Dik: warm, friendly, slightly more detail
# - Bobbie: colorful, appealing to toddlers
# This prompt produces consistent, high-quality results in ChatGPT/DALL-E
STYLE_PROMPT = """cute, simple, child-friendly illustration style similar to Dutch children's books like Nijntje (Miffy) or Dikkie Dik. Soft rounded shapes, warm colors, gentle outlines, pure white (#FFFFFF) background. The style should be appealing to toddlers (age 2). No text, labels, or captions in the image."""

# Grid layouts for ChatGPT image generation
# We use grids to maximize efficiency with ChatGPT's free tier rate limits.
# 6 images (3x2) is the sweet spot: enough images per request, good quality per cell.
GRID_LAYOUTS = {
    2: (2, 1),  # 2 images: 2 columns, 1 row
    3: (3, 1),  # 3 images: 3 columns, 1 row
    4: (2, 2),  # 4 images: 2x2 grid
    6: (3, 2),  # 6 images: 3x2 grid (recommended)
    9: (3, 3),  # 9 images: 3x3 grid
}

SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.heic', '.webp'}


# ── Status Command ─────────────────────────────────────────────────────────

def load_cards():
    """Load cards from CSV, return list of (letter, word, image, personal)."""
    cards = []
    with open(CARDS_CSV, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            letter = row['letter'].strip()
            # Skip comments and empty lines
            if letter.startswith('#') or not letter:
                continue
            word = row['word'].strip()
            # Skip placeholder entries
            if 'geen voorbeeld' in word.lower():
                continue
            image = row.get('image', '').strip()
            personal = row.get('personal', 'no').strip().lower() == 'yes'
            cards.append((letter, word, image, personal))
    return cards


def check_image_status(image_name, personal=False):
    """
    Check if an image exists and assess its quality.
    Returns: (exists, quality_note)
    """
    if personal:
        personal_dir = Path.home() / '.lettercards' / 'personal'
        path = personal_dir / image_name
    else:
        path = IMAGES_DIR / image_name

    if not path.exists():
        return False, "missing"

    # Check if it's a placeholder (small file, likely geometric)
    try:
        size = path.stat().st_size
        if size < 5000:  # Less than 5KB is likely a simple placeholder
            return True, "placeholder (needs upgrade)"

        # Check image dimensions
        img = Image.open(path)
        w, h = img.size
        if w < 200 or h < 200:
            return True, f"low-res ({w}x{h})"
        if abs(w - h) > 50:
            return True, f"not square ({w}x{h})"

        return True, "ok"
    except Exception as e:
        return True, f"error: {e}"


def cmd_status(args):
    """Show status of all images."""
    cards = load_cards()

    missing = []
    placeholders = []
    ok = []
    personal_needed = []

    for letter, word, image, personal in cards:
        if not image:
            missing.append((letter, word, "no image specified"))
            continue

        if personal:
            exists, note = check_image_status(image, personal=True)
            if not exists:
                personal_needed.append((letter, word, image))
            elif note != "ok":
                personal_needed.append((letter, word, f"{image} ({note})"))
            else:
                ok.append((letter, word))
        else:
            exists, note = check_image_status(image, personal=False)
            if not exists:
                missing.append((letter, word, image))
            elif "placeholder" in note or note != "ok":
                placeholders.append((letter, word, f"{image} ({note})"))
            else:
                ok.append((letter, word))

    print("=" * 60)
    print("PICTOGRAM STATUS")
    print("=" * 60)

    if missing:
        print(f"\n❌ MISSING ({len(missing)}):")
        for letter, word, note in missing:
            print(f"   {letter}: {word} - {note}")

    if placeholders:
        print(f"\n⚠️  NEED UPGRADE ({len(placeholders)}):")
        for letter, word, note in placeholders:
            print(f"   {letter}: {word} - {note}")

    if personal_needed:
        print(f"\n📷 PERSONAL PHOTOS NEEDED ({len(personal_needed)}):")
        for letter, word, note in personal_needed:
            print(f"   {letter}: {word} - {note}")

    if ok:
        print(f"\n✓ OK ({len(ok)})")
        if args.verbose:
            for letter, word in ok:
                print(f"   {letter}: {word}")

    # Summary
    total = len(cards)
    done = len(ok)
    print(f"\n{'-' * 60}")
    print(f"Progress: {done}/{total} images ready ({100*done//total}%)")

    if missing or placeholders:
        words = [w for _, w, _ in missing + placeholders]
        print(f"\nTo generate prompts for missing/placeholder images:")
        print(f"  python pictogram_workflow.py prompt --missing")
        print(f"\nOr for specific words:")
        print(f"  python pictogram_workflow.py prompt {' '.join(words[:6])}")


# ── Prompt Command ─────────────────────────────────────────────────────────

def cmd_prompt(args):
    """Generate ChatGPT prompt for creating pictograms."""
    words = args.words

    # If --missing flag, find all missing/placeholder images
    if args.missing:
        cards = load_cards()
        words = []
        for letter, word, image, personal in cards:
            if personal:
                continue  # Skip personal photos
            if not image:
                words.append(word)
                continue
            exists, note = check_image_status(image, personal=False)
            if not exists or "placeholder" in note:
                words.append(word)

        if not words:
            print("All non-personal images are ready!")
            return

        print(f"Found {len(words)} images that need generation.\n")

    if not words:
        print("No words specified. Use: python pictogram_workflow.py prompt WORD...")
        print("Or use --missing to generate for all missing images.")
        return

    # Split into batches of 6 (optimal grid size)
    batch_size = 6
    batches = [words[i:i+batch_size] for i in range(0, len(words), batch_size)]

    print("=" * 60)
    print("CHATGPT PROMPTS")
    print("=" * 60)

    for i, batch in enumerate(batches):
        cols, rows = GRID_LAYOUTS.get(len(batch), (3, 2))
        grid_desc = f"{cols}x{rows} grid" if len(batch) > 1 else "single image"

        print(f"\n{'─' * 60}")
        print(f"BATCH {i+1}/{len(batches)}: {', '.join(batch)}")
        print(f"{'─' * 60}")
        print()

        # Build the prompt
        items = ", ".join(batch)
        if len(batch) == 1:
            prompt = f"""Create a {STYLE_PROMPT}

Draw: {batch[0]}

Make it centered on a cream/beige background, simple and recognizable for a toddler."""
        else:
            prompt = f"""Create a {cols}x{rows} grid of {STYLE_PROMPT}

The {len(batch)} items to draw (left to right, top to bottom):
{', '.join(batch)}

Each item should be in its own cell with a cream/beige background. Keep items centered and recognizable for a toddler."""

        print(prompt)
        print()
        print("─" * 40)
        print("INSTRUCTIONS:")
        print("1. Copy the prompt above and paste it in ChatGPT")
        print("2. Download the generated image")
        print(f"3. Drop it in: {STAGING_DIR}/")
        if len(batch) > 1:
            print(f"4. Run: python pictogram_workflow.py split {' '.join(batch)}")
        else:
            print(f"4. Run: python pictogram_workflow.py split {batch[0]}")
        print()


# ── Split Command ──────────────────────────────────────────────────────────

def find_grid_image():
    """Find the most recent image in staging folder."""
    if not STAGING_DIR.exists():
        return None

    images = []
    for f in STAGING_DIR.iterdir():
        if f.suffix.lower() in SUPPORTED_FORMATS:
            images.append((f.stat().st_mtime, f))

    if not images:
        return None

    # Return most recent
    images.sort(reverse=True)
    return images[0][1]


def detect_grid_layout(img):
    """
    Try to detect grid layout by analyzing the image.
    Returns (cols, rows) or None if can't detect.
    """
    # For now, use simple heuristics based on aspect ratio
    w, h = img.size
    ratio = w / h

    if 0.9 < ratio < 1.1:  # Square
        # Could be 1x1, 2x2, 3x3
        # Check for grid lines or just return common layouts
        return None  # Let user specify
    elif ratio > 1.3:  # Wide
        return (3, 1) if ratio > 2 else (2, 1)
    else:  # Tall
        return (1, 3) if ratio < 0.5 else (1, 2)


def center_crop_to_square(img):
    """Center-crop image to square."""
    w, h = img.size
    min_dim = min(w, h)
    left = (w - min_dim) // 2
    top = (h - min_dim) // 2
    return img.crop((left, top, left + min_dim, top + min_dim))


def split_grid(img, names, cols, rows):
    """
    Split a grid image into individual images.
    Returns list of (name, processed_image) tuples.
    """
    width, height = img.size
    cell_w = width // cols
    cell_h = height // rows

    results = []
    for i, name in enumerate(names):
        if i >= cols * rows:
            print(f"  Warning: more names than grid cells, skipping '{name}'")
            continue

        row = i // cols
        col = i % cols

        left = col * cell_w
        top = row * cell_h
        right = left + cell_w
        bottom = top + cell_h

        cell = img.crop((left, top, right, bottom))

        # Center-crop to square
        square = center_crop_to_square(cell)

        # Resize to 400x400
        final = square.resize((400, 400), Image.LANCZOS)

        results.append((name, final))

    return results


def update_sources_md(names, prompt_words):
    """
    Update SOURCES.md table with full prompt for generated images.

    Args:
        names: List of image names that were generated
        prompt_words: The words used in the ChatGPT prompt
    """
    from datetime import date
    today = date.today().isoformat()

    # Build the full prompt (escaped for markdown table)
    cols, rows = GRID_LAYOUTS.get(len(prompt_words), (3, 2))
    if len(prompt_words) == 1:
        full_prompt = f"Create a {STYLE_PROMPT} Draw: {prompt_words[0]}. Make it centered on a cream/beige background, simple and recognizable for a toddler."
    else:
        full_prompt = f"Create a {cols}x{rows} grid of {STYLE_PROMPT} The {len(prompt_words)} items to draw (left to right, top to bottom): {', '.join(prompt_words)}. Each item should be in its own cell with a cream/beige background. Keep items centered and recognizable for a toddler."

    # Read existing file
    if not SOURCES_MD.exists():
        print(f"  Warning: {SOURCES_MD} not found")
        return

    lines = SOURCES_MD.read_text().splitlines(keepends=True)

    # Update matching rows
    images_to_update = {name for name in names}
    updated = []
    new_lines = []

    for line in lines:
        # Check if this is a table row for one of our images
        matched = False
        for name in list(images_to_update):
            if f"| {name} |" in line or f"![{name}]" in line:
                # Replace with updated entry
                new_lines.append(f"| ![{name}]({name}.png) | {name} | ChatGPT/DALL-E | {today} | {full_prompt} |\n")
                images_to_update.remove(name)
                updated.append(name)
                matched = True
                break
        if not matched:
            new_lines.append(line)

    # Write back
    SOURCES_MD.write_text(''.join(new_lines))

    if updated:
        print(f"  Updated SOURCES.md: {', '.join(updated)}")


def remove_background(img, threshold=20):
    """
    Remove near-white background, returning an RGBA image with transparency.

    Samples the four corner pixels to detect the background colour, then
    makes any pixel within `threshold` of that colour transparent.

    Use only on freshly-generated pictograms with a clean white/near-white
    background. For existing images with complex content, prefer regeneration
    over post-processing — background removal can damage illustration detail.

    Args:
        img: PIL Image (RGB or RGBA)
        threshold: Maximum colour distance from background to treat as transparent (0-255)

    Returns:
        PIL Image in RGBA mode
    """
    img = img.convert("RGBA")
    pixels = img.load()
    w, h = img.size

    corners = [pixels[0, 0], pixels[w - 1, 0], pixels[0, h - 1], pixels[w - 1, h - 1]]
    bg_r = sum(c[0] for c in corners) // 4
    bg_g = sum(c[1] for c in corners) // 4
    bg_b = sum(c[2] for c in corners) // 4

    if bg_r < 220 or bg_g < 220 or bg_b < 220:
        print(f"  Warning: background doesn't look white (avg corner: {bg_r},{bg_g},{bg_b}). Skipping.")
        return img

    for y in range(h):
        for x in range(w):
            r, g, b, a = pixels[x, y]
            dist = max(abs(r - bg_r), abs(g - bg_g), abs(b - bg_b))
            if dist <= threshold:
                pixels[x, y] = (r, g, b, 0)

    return img


def cmd_split(args):
    """Split a grid image from staging into individual pictograms."""
    # Find grid image
    if args.image:
        grid_path = STAGING_DIR / args.image
        if not grid_path.exists():
            print(f"Image not found: {grid_path}")
            sys.exit(1)
    else:
        grid_path = find_grid_image()
        if not grid_path:
            print(f"No images found in staging folder: {STAGING_DIR}")
            print(f"\nDrop a grid image there first, then run this command again.")
            sys.exit(1)

    print(f"Processing: {grid_path.name}")

    # Get names
    names = args.names
    if not names:
        print("\nNo names specified. Please provide the word names in order:")
        print("  python pictogram_workflow.py split appel auto deur draak druif water")
        print("\nOr specify names in the order they appear (left-to-right, top-to-bottom)")
        sys.exit(1)

    # Open and analyze image
    img = Image.open(grid_path)
    print(f"  Image size: {img.size}")

    # Determine grid layout
    if args.grid:
        cols, rows = map(int, args.grid.split('x'))
    else:
        # Auto-detect based on number of names
        layout = GRID_LAYOUTS.get(len(names))
        if layout:
            cols, rows = layout
        else:
            print(f"\nCan't auto-detect grid for {len(names)} images.")
            print("Specify grid layout with --grid, e.g., --grid 3x2")
            sys.exit(1)

    print(f"  Grid layout: {cols}x{rows}")
    print(f"  Names: {', '.join(names)}")

    # Convert to RGB if needed
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # Split the grid
    results = split_grid(img, names, cols, rows)

    if args.preview:
        print(f"\nPreview mode - showing results without saving")
        for name, processed in results:
            print(f"  {name}: {processed.size}")
            processed.show()
        return

    # Save results
    IMAGES_DIR.mkdir(exist_ok=True)
    print(f"\nSaving images:")
    if args.remove_bg:
        print("  Background removal enabled (--remove-bg)")
    saved_names = []
    for name, processed in results:
        if args.remove_bg:
            processed = remove_background(processed)
        output_path = IMAGES_DIR / f"{name}.png"
        processed.save(output_path, 'PNG')
        saved_names.append(name)
        print(f"  ✓ {output_path}")

    # Update SOURCES.md with copyright/source info
    update_sources_md(saved_names, names)

    # Clean up staging (unless --keep)
    if not args.keep:
        grid_path.unlink()
        print(f"  Removed {grid_path.name} from staging")

    print(f"\nDone! Generated {len(results)} images.")
    print(f"\nNext steps:")
    print(f"  1. Verify images look good")
    print(f"  2. Run: python generate.py")
    print(f"  3. Check the PDF")


# ── Main ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Pictogram workflow for letter cards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest='command', help='Commands')

    # Status command
    status_parser = subparsers.add_parser('status', help='Show image status')
    status_parser.add_argument('-v', '--verbose', action='store_true',
                               help='Show all images including OK ones')

    # Prompt command
    prompt_parser = subparsers.add_parser('prompt', help='Generate ChatGPT prompts')
    prompt_parser.add_argument('words', nargs='*', help='Words to generate images for')
    prompt_parser.add_argument('--missing', '-m', action='store_true',
                               help='Generate prompts for all missing images')

    # Split command
    split_parser = subparsers.add_parser('split', help='Split grid image')
    split_parser.add_argument('names', nargs='*', help='Names for each image (in order)')
    split_parser.add_argument('--image', '-i', help='Specific image file in staging')
    split_parser.add_argument('--grid', '-g', help='Grid layout, e.g., 3x2')
    split_parser.add_argument('--preview', '-p', action='store_true',
                              help='Preview without saving')
    split_parser.add_argument('--keep', '-k', action='store_true',
                              help='Keep staging image after processing')
    split_parser.add_argument('--remove-bg', action='store_true',
                              help='Remove white background (opt-in). Use on fresh ChatGPT images only.')

    args = parser.parse_args()

    if args.command == 'status':
        cmd_status(args)
    elif args.command == 'prompt':
        cmd_prompt(args)
    elif args.command == 'split':
        cmd_split(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()

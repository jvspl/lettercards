#!/usr/bin/env python3
"""
Personal Photo Processor for Letter Cards

Helps prepare personal photos for use in letter cards. Takes a source image,
crops it to a square, resizes it, and saves it to the personal photos folder.

Usage:
    python process_photo.py --list                    # Show staging folder contents
    python process_photo.py oma                       # Process first image in staging as oma.png
    python process_photo.py oma photo.jpg             # Process specific file as oma.png
    python process_photo.py oma photo.jpg --preview   # Show result without saving

The staging folder is: ~/.lettercards/staging/
The output folder is:  ~/.lettercards/personal/
"""

import argparse
import os
import sys
from pathlib import Path
from PIL import Image

# ── Configuration ──────────────────────────────────────────────────────

DEFAULT_SIZE = 400  # Output size in pixels (square)
SUPPORTED_FORMATS = {'.jpg', '.jpeg', '.png', '.heic', '.webp', '.gif', '.bmp'}


def get_dirs():
    """Get staging and personal directories."""
    base = Path.home() / '.lettercards'
    staging = base / 'staging'
    personal = base / 'personal'
    return staging, personal


def ensure_dirs():
    """Create directories if they don't exist."""
    staging, personal = get_dirs()
    staging.mkdir(parents=True, exist_ok=True)
    personal.mkdir(parents=True, exist_ok=True)
    return staging, personal


def list_staging():
    """List images in staging folder."""
    staging, _ = get_dirs()

    if not staging.exists():
        print(f"Staging folder doesn't exist: {staging}")
        print(f"Create it with: mkdir -p {staging}")
        return []

    images = []
    for f in sorted(staging.iterdir()):
        if f.suffix.lower() in SUPPORTED_FORMATS:
            size = f.stat().st_size / 1024  # KB
            images.append((f.name, size))

    if not images:
        print(f"No images in staging folder: {staging}")
        print(f"\nDrop photos there to process them.")
    else:
        print(f"Images in {staging}:\n")
        for name, size in images:
            print(f"  {name} ({size:.0f} KB)")

    return images


def find_source_image(staging, filename=None):
    """Find source image in staging folder."""
    if filename:
        # Specific file requested
        source = staging / filename
        if not source.exists():
            print(f"File not found: {source}")
            return None
        return source

    # Find first image in staging
    for f in sorted(staging.iterdir()):
        if f.suffix.lower() in SUPPORTED_FORMATS:
            return f

    print(f"No images found in staging folder: {staging}")
    return None


def process_image(source_path, output_size=DEFAULT_SIZE):
    """
    Process an image: crop to square (center) and resize.

    Returns the processed PIL Image.
    """
    img = Image.open(source_path)

    # Convert to RGB if necessary (handles RGBA, P mode, etc.)
    if img.mode in ('RGBA', 'P'):
        # Create white background for transparency
        background = Image.new('RGB', img.size, (255, 255, 255))
        if img.mode == 'P':
            img = img.convert('RGBA')
        background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
        img = background
    elif img.mode != 'RGB':
        img = img.convert('RGB')

    # Handle EXIF orientation
    try:
        from PIL import ExifTags
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == 'Orientation':
                break
        exif = img._getexif()
        if exif:
            orientation_value = exif.get(orientation)
            if orientation_value == 3:
                img = img.rotate(180, expand=True)
            elif orientation_value == 6:
                img = img.rotate(270, expand=True)
            elif orientation_value == 8:
                img = img.rotate(90, expand=True)
    except (AttributeError, KeyError, IndexError):
        pass

    width, height = img.size

    # Crop to square (center crop)
    # For portraits, take upper portion (likely where face is)
    # For landscapes, take center
    min_dim = min(width, height)

    if height > width:
        # Portrait: take upper portion (face usually in top half)
        left = 0
        top = 0
        right = width
        bottom = width
    else:
        # Landscape or square: center crop
        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim

    cropped = img.crop((left, top, right, bottom))

    # Resize to output size
    resized = cropped.resize((output_size, output_size), Image.LANCZOS)

    return resized


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Process personal photos for letter cards",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python process_photo.py --list              # See what's in staging
  python process_photo.py oma                 # Process first staged image as oma.png
  python process_photo.py opa IMG_123.jpg     # Process specific file as opa.png
  python process_photo.py mama --preview      # Preview without saving
        """
    )
    parser.add_argument('name', nargs='?', help='Output name (without extension), e.g., "oma"')
    parser.add_argument('source', nargs='?', help='Source filename in staging folder (optional)')
    parser.add_argument('--list', '-l', action='store_true', help='List images in staging folder')
    parser.add_argument('--preview', '-p', action='store_true', help='Preview only, do not save')
    parser.add_argument('--size', '-s', type=int, default=DEFAULT_SIZE,
                        help=f'Output size in pixels (default: {DEFAULT_SIZE})')
    parser.add_argument('--force', '-f', action='store_true', help='Overwrite existing file')

    args = parser.parse_args(argv)

    # List mode
    if args.list:
        list_staging()
        return 0

    # Need a name to process
    if not args.name:
        parser.print_help()
        return 0

    staging, personal = ensure_dirs()

    # Find source image
    source = find_source_image(staging, args.source)
    if not source:
        return 1

    # Check output path
    output_path = personal / f"{args.name}.png"
    if output_path.exists() and not args.force and not args.preview:
        print(f"Output file already exists: {output_path}")
        print(f"Use --force to overwrite, or --preview to see result first")
        return 1

    # Process the image
    print(f"Processing: {source.name}")
    print(f"  Source: {source}")

    try:
        result = process_image(source, args.size)
    except Exception as e:
        print(f"Error processing image: {e}")
        return 1

    print(f"  Size: {result.size[0]}x{result.size[1]}")

    if args.preview:
        print(f"\nPreview mode - not saving.")
        print(f"Would save to: {output_path}")
        result.show()
    else:
        result.save(output_path, 'PNG')
        print(f"\nSaved: {output_path}")
        print(f"\nNext steps:")
        print(f"  1. Verify the image looks good")
        print(f"  2. Run: python generate.py --letters {args.name[0]}")
        print(f"  3. Check the PDF")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

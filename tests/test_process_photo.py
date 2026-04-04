"""Tests for process_photo.py — square crop and resize logic."""
import pytest
from PIL import Image
from pathlib import Path

from process_photo import process_image, DEFAULT_SIZE


def make_image(tmp_path, width, height, color=(200, 100, 50)):
    """Create a solid-color test image and return its path."""
    img = Image.new('RGB', (width, height), color)
    path = tmp_path / f"test_{width}x{height}.jpg"
    img.save(path)
    return path


# ── Output dimensions ────────────────────────────────────────────────────────

def test_portrait_output_is_square(tmp_path):
    path = make_image(tmp_path, 300, 500)
    result = process_image(path)
    assert result.size == (DEFAULT_SIZE, DEFAULT_SIZE)


def test_landscape_output_is_square(tmp_path):
    path = make_image(tmp_path, 500, 300)
    result = process_image(path)
    assert result.size == (DEFAULT_SIZE, DEFAULT_SIZE)


def test_square_input_output_is_square(tmp_path):
    path = make_image(tmp_path, 400, 400)
    result = process_image(path)
    assert result.size == (DEFAULT_SIZE, DEFAULT_SIZE)


def test_custom_output_size(tmp_path):
    path = make_image(tmp_path, 300, 500)
    result = process_image(path, output_size=200)
    assert result.size == (200, 200)


# ── Crop region ──────────────────────────────────────────────────────────────

def test_portrait_crops_from_top(tmp_path):
    """Portrait crop should take the top square (width x width), not center."""
    # Make a 100x200 image: top half red, bottom half blue
    img = Image.new('RGB', (100, 200))
    for y in range(100):
        for x in range(100):
            img.putpixel((x, y), (255, 0, 0))    # top: red
    for y in range(100, 200):
        for x in range(100):
            img.putpixel((x, y), (0, 0, 255))    # bottom: blue
    path = tmp_path / "portrait.png"
    img.save(path)

    result = process_image(path, output_size=100)
    # After top-crop of 100x100, the result should be all red (upscaled to 100x100 = same size)
    pixel = result.getpixel((50, 50))
    assert pixel[0] > 200  # dominant red channel
    assert pixel[2] < 50   # low blue channel


def test_landscape_crops_center(tmp_path):
    """Landscape crop should take the center square (height x height)."""
    # Make a 300x100 image: left third red, center green, right third blue
    img = Image.new('RGB', (300, 100))
    for y in range(100):
        for x in range(100):
            img.putpixel((x, y), (255, 0, 0))      # left: red
        for x in range(100, 200):
            img.putpixel((x, y), (0, 200, 0))      # center: green
        for x in range(200, 300):
            img.putpixel((x, y), (0, 0, 255))      # right: blue

    path = tmp_path / "landscape.png"
    img.save(path)

    result = process_image(path, output_size=100)
    # Center 100x100 should be green
    pixel = result.getpixel((50, 50))
    assert pixel[1] > 150  # dominant green channel
    assert pixel[0] < 50   # low red
    assert pixel[2] < 50   # low blue


# ── Output format ────────────────────────────────────────────────────────────

def test_rgba_input_converted_to_rgb(tmp_path):
    img = Image.new('RGBA', (200, 200), (100, 150, 200, 128))
    path = tmp_path / "rgba.png"
    img.save(path)
    result = process_image(path)
    assert result.mode == 'RGB'


def test_result_is_pil_image(tmp_path):
    path = make_image(tmp_path, 300, 400)
    result = process_image(path)
    assert isinstance(result, Image.Image)


# ── auto_enhance ─────────────────────────────────────────────────────────────

from process_photo import auto_enhance, make_comparison_grid


def test_auto_enhance_returns_pil_image():
    img = Image.new('RGB', (200, 200), (100, 100, 100))
    result = auto_enhance(img)
    assert isinstance(result, Image.Image)


def test_auto_enhance_same_size():
    img = Image.new('RGB', (200, 200), (100, 100, 100))
    result = auto_enhance(img)
    assert result.size == img.size


def test_auto_enhance_returns_rgb():
    img = Image.new('RGB', (200, 200), (100, 100, 100))
    result = auto_enhance(img)
    assert result.mode == 'RGB'


# ── make_comparison_grid ─────────────────────────────────────────────────────

def make_thumb(color=(200, 100, 50), size=100):
    return Image.new('RGB', (size, size), color)


def test_make_comparison_grid_single_entry():
    entries = [('1', 'photo.jpg', make_thumb())]
    grid = make_comparison_grid(entries, cell_size=100, cols=3)
    assert isinstance(grid, Image.Image)


def test_make_comparison_grid_multiple_entries_wraps_rows():
    entries = [(str(i), f'photo{i}.jpg', make_thumb()) for i in range(4)]
    grid = make_comparison_grid(entries, cell_size=100, cols=3)
    assert isinstance(grid, Image.Image)
    assert grid.height > 0


def test_make_comparison_grid_truncates_long_filename():
    """Filenames longer than 36 chars should not raise."""
    long_name = 'a' * 40 + '.jpg'
    entries = [('1', long_name, make_thumb())]
    grid = make_comparison_grid(entries, cell_size=100, cols=1)
    assert isinstance(grid, Image.Image)

"""Tests for mcp_server.py — image processing and MCP tool behaviour."""
import base64
import io
import os
import pytest
from pathlib import Path
from PIL import Image

import mcp_server


# ── helpers ──────────────────────────────────────────────────────────────────

def make_b64_image(width=300, height=400, color=(200, 100, 50)):
    """Return a base64-encoded JPEG of the given dimensions."""
    img = Image.new('RGB', (width, height), color)
    buf = io.BytesIO()
    img.save(buf, format='JPEG')
    return base64.b64encode(buf.getvalue()).decode()


def make_image_file(path, width=300, height=400, color=(200, 100, 50)):
    """Write a JPEG image to path and return the path."""
    img = Image.new('RGB', (width, height), color)
    img.save(path, 'JPEG')
    return path


# ── PERSONAL_DIR env var ─────────────────────────────────────────────────────

def test_personal_dir_uses_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv('LETTERCARDS_PERSONAL_DIR', str(tmp_path / 'custom'))
    import importlib
    importlib.reload(mcp_server)
    assert mcp_server.PERSONAL_DIR == tmp_path / 'custom'


def test_personal_dir_default_when_env_not_set(monkeypatch):
    monkeypatch.delenv('LETTERCARDS_PERSONAL_DIR', raising=False)
    import importlib
    importlib.reload(mcp_server)
    assert mcp_server.PERSONAL_DIR == Path.home() / '.lettercards' / 'personal'


# ── decode_and_process ───────────────────────────────────────────────────────

def test_decode_portrait_crops_to_square():
    """Portrait (tall) image: crop takes top square (width × width)."""
    b64 = make_b64_image(300, 500)
    result = mcp_server.decode_and_process(b64, size=100)
    assert result.size == (100, 100)


def test_decode_landscape_crops_center():
    """Landscape (wide) image: crop takes centre square."""
    b64 = make_b64_image(600, 300)
    result = mcp_server.decode_and_process(b64, size=100)
    assert result.size == (100, 100)


def test_decode_square_unchanged_crop():
    b64 = make_b64_image(400, 400)
    result = mcp_server.decode_and_process(b64, size=100)
    assert result.size == (100, 100)


def test_decode_rgba_converted_to_rgb():
    img = Image.new('RGBA', (300, 300), (100, 150, 200, 128))
    buf = io.BytesIO()
    img.save(buf, format='PNG')
    b64 = base64.b64encode(buf.getvalue()).decode()
    result = mcp_server.decode_and_process(b64, size=100)
    assert result.mode == 'RGB'


def test_decode_returns_pil_image():
    b64 = make_b64_image(300, 300)
    result = mcp_server.decode_and_process(b64)
    assert isinstance(result, Image.Image)


# ── load_and_process ─────────────────────────────────────────────────────────

def test_load_portrait_crops_to_square(tmp_path):
    p = make_image_file(tmp_path / 'p.jpg', 300, 500)
    result = mcp_server.load_and_process(str(p), size=100)
    assert result.size == (100, 100)


def test_load_landscape_crops_center(tmp_path):
    p = make_image_file(tmp_path / 'l.jpg', 600, 300)
    result = mcp_server.load_and_process(str(p), size=100)
    assert result.size == (100, 100)


def test_load_returns_pil_image(tmp_path):
    p = make_image_file(tmp_path / 'sq.jpg', 300, 300)
    result = mcp_server.load_and_process(str(p))
    assert isinstance(result, Image.Image)


# ── render_card ──────────────────────────────────────────────────────────────

def make_photo(size=200):
    return Image.new('RGB', (size, size), (180, 120, 60))


def test_render_card_returns_image():
    photo = make_photo()
    card = mcp_server.render_card(photo, 'appel')
    assert isinstance(card, Image.Image)


def test_render_card_correct_dimensions():
    photo = make_photo()
    card = mcp_server.render_card(photo, 'deur')
    assert card.size == (mcp_server.CARD_W, mcp_server.CARD_H)


def test_render_card_uses_letter_color_for_known_letter():
    """Card for letter 'a' uses the 'a' accent colour somewhere in the image."""
    photo = make_photo()
    card = mcp_server.render_card(photo, 'appel')
    expected_color = mcp_server.LETTER_COLORS['a']
    card_rgb = card.convert('RGB')
    pixels = [card_rgb.getpixel((x, y)) for x in range(card_rgb.width) for y in range(card_rgb.height)]
    assert any(p[:3] == expected_color for p in pixels)


def test_render_card_unknown_letter_uses_default_color():
    """Card for a word with no letter mapping falls back gracefully."""
    photo = make_photo()
    card = mcp_server.render_card(photo, '1ding')
    assert card.size == (mcp_server.CARD_W, mcp_server.CARD_H)


# ── pick_photos (directory mode — no dialog needed) ──────────────────────────

def test_pick_photos_directory_lists_images(tmp_path):
    make_image_file(tmp_path / 'a.jpg')
    make_image_file(tmp_path / 'b.png')
    (tmp_path / 'notes.txt').write_text('ignore me')

    result = mcp_server.pick_photos('test', directory=str(tmp_path))
    assert '1.' in result
    assert '2.' in result
    assert 'notes.txt' not in result


def test_pick_photos_directory_not_found():
    result = mcp_server.pick_photos('test', directory='/nonexistent/definitely/not/here')
    assert 'not found' in result.lower()


def test_pick_photos_directory_empty(tmp_path):
    result = mcp_server.pick_photos('test', directory=str(tmp_path))
    assert 'No photos' in result


def test_pick_photos_directory_returns_absolute_paths(tmp_path):
    make_image_file(tmp_path / 'photo.jpg')
    result = mcp_server.pick_photos('test', directory=str(tmp_path))
    assert str(tmp_path) in result


# ── generate_photo_grid ──────────────────────────────────────────────────────

def test_generate_photo_grid_returns_mcp_image(tmp_path):
    paths = []
    for i in range(3):
        p = tmp_path / f'photo{i}.jpg'
        make_image_file(p, 300, 300, color=(50 * i, 80, 120))
        paths.append(str(p))

    from mcp.server.fastmcp import Image as MCPImage
    result = mcp_server.generate_photo_grid(paths)
    assert result is not None


def test_generate_photo_grid_single_photo(tmp_path):
    p = make_image_file(tmp_path / 'solo.jpg', 300, 300)
    result = mcp_server.generate_photo_grid([str(p)])
    assert result is not None


def test_generate_photo_grid_bad_path_does_not_raise(tmp_path):
    p = make_image_file(tmp_path / 'good.jpg', 300, 300)
    result = mcp_server.generate_photo_grid([str(p), '/nonexistent/photo.jpg'])
    assert result is not None


# ── generate_comparison ───────────────────────────────────────────────────────

def test_generate_comparison_returns_mcp_image(tmp_path):
    paths = []
    for i in range(2):
        p = tmp_path / f'cand{i}.jpg'
        make_image_file(p, 300, 400, color=(100 + 30 * i, 80, 60))
        paths.append(str(p))

    result = mcp_server.generate_comparison('Tata', paths)
    assert result is not None


def test_generate_comparison_single_photo(tmp_path):
    p = make_image_file(tmp_path / 'one.jpg', 300, 400)
    result = mcp_server.generate_comparison('mama', [str(p)])
    assert result is not None


# ── save_photo ───────────────────────────────────────────────────────────────

def test_save_photo_writes_file(tmp_path, monkeypatch):
    monkeypatch.setenv('LETTERCARDS_PERSONAL_DIR', str(tmp_path / 'personal'))
    import importlib
    importlib.reload(mcp_server)

    src = make_image_file(tmp_path / 'tata.jpg', 300, 400)
    mcp_server.save_photo(name='tata', file_path=str(src))

    out = tmp_path / 'personal' / 'tata.png'
    assert out.exists()
    assert Image.open(out).format == 'PNG'


def test_save_photo_lowercases_name(tmp_path, monkeypatch):
    monkeypatch.setenv('LETTERCARDS_PERSONAL_DIR', str(tmp_path / 'personal'))
    import importlib
    importlib.reload(mcp_server)

    src = make_image_file(tmp_path / 'mama.jpg', 300, 300)
    mcp_server.save_photo(name='Mama', file_path=str(src))

    assert (tmp_path / 'personal' / 'mama.png').exists()


def test_save_photo_creates_personal_dir(tmp_path, monkeypatch):
    personal_dir = tmp_path / 'new' / 'nested' / 'personal'
    monkeypatch.setenv('LETTERCARDS_PERSONAL_DIR', str(personal_dir))
    import importlib
    importlib.reload(mcp_server)

    src = make_image_file(tmp_path / 'opa.jpg', 300, 300)
    mcp_server.save_photo(name='opa', file_path=str(src))

    assert (personal_dir / 'opa.png').exists()


def test_save_photo_returns_string_with_path(tmp_path, monkeypatch):
    monkeypatch.setenv('LETTERCARDS_PERSONAL_DIR', str(tmp_path / 'personal'))
    import importlib
    importlib.reload(mcp_server)

    src = make_image_file(tmp_path / 'oma.jpg', 300, 300)
    result = mcp_server.save_photo(name='oma', file_path=str(src))

    assert 'oma.png' in result
    assert isinstance(result, str)

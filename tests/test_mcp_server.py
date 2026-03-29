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

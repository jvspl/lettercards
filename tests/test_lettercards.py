"""Tests against the bundled starter deck and synthetic decks."""

import shutil

import pytest

from lettercards.cli import main
from lettercards.deck import (check_deck, load_deck, printable_cards,
                              resolve_image, starter_dir)


@pytest.fixture
def deck(tmp_path):
    """A tiny deck: one own-image card, one starter-image card, one idea, one broken."""
    (tmp_path / "images").mkdir()
    shutil.copy(starter_dir() / "images" / "zon.png", tmp_path / "images" / "eigen.png")
    (tmp_path / "deck.csv").write_text(
        "letter,word,image,language,status,notes\n"
        "# a comment line\n"
        "e,eigen,eigen.png,nl,active,\n"
        "z,zebra,zebra.png,nl,active,\n"
        "k,kasteel,,nl,idea,needs image\n"
        "w,wolf,wolf.png,nl,retired,\n",
        encoding="utf-8")
    return tmp_path


def test_load_deck_skips_comments(deck):
    cards = load_deck(deck)
    assert [c.word for c in cards] == ["eigen", "zebra", "kasteel", "wolf"]
    assert cards[0].language == "nl"


def test_image_resolution_prefers_deck_then_starter(deck):
    cards = {c.word: c for c in load_deck(deck)}
    assert resolve_image(cards["eigen"], deck) == deck / "images" / "eigen.png"
    assert resolve_image(cards["zebra"], deck) == starter_dir() / "images" / "zebra.png"
    assert resolve_image(cards["kasteel"], deck) is None


def test_printable_excludes_ideas_retired_and_filters(deck):
    cards = load_deck(deck)
    assert {c.word for c in printable_cards(cards, deck)} == {"eigen", "zebra"}
    assert [c.word for c in printable_cards(cards, deck, letters=["z"])] == ["zebra"]
    assert [c.word for c in printable_cards(cards, deck, words=["eigen"])] == ["eigen"]


def test_check_reports_problems(deck):
    (deck / "deck.csv").write_text(
        "letter,word,image,language,status,notes\n"
        "z,zebra,zebra.png,nl,active,\n"
        "z,zebra,zebra.png,nl,active,duplicate\n"
        "b,bal,missing.png,nl,active,\n"
        "q,quark,,nl,bogus,\n",
        encoding="utf-8")
    _, problems = check_deck(deck)
    text = "\n".join(problems)
    assert "duplicate" in text
    assert "missing.png" in text
    assert "bogus" in text


def test_check_flags_letter_word_mismatch(deck):
    (deck / "deck.csv").write_text(
        "letter,word,image,language,status,notes\n"
        "b,kat,zebra.png,nl,active,\n"                      # wrong: kat under b
        "d,dolfijn,,nl,idea,\n"                             # wrong but noted -> allowed
        "d,dolfijn2,,nl,idea,ij digraph exception\n",
        encoding="utf-8")
    _, problems = check_deck(deck)
    text = "\n".join(problems)
    assert "not letter 'b'" in text
    assert "dolfijn" not in text  # noted exceptions are suppressed


def test_check_flags_bad_image_dimensions(deck):
    from PIL import Image
    Image.new("RGB", (400, 300), "#3366AA").save(deck / "images" / "wide.png")
    (deck / "deck.csv").write_text(
        "letter,word,image,language,status,notes\n"
        "w,wide,wide.png,nl,active,\n",
        encoding="utf-8")
    _, problems = check_deck(deck)
    assert any("400x300" in p and "square" in p for p in problems)


def test_starter_deck_is_valid():
    cards, problems = check_deck(starter_dir())
    assert problems == []
    assert len(cards) == 54


def test_cli_render_starter(tmp_path, capsys):
    out = tmp_path / "out.pdf"
    assert main(["render", "starter", "--letters", "a,z", "-o", str(out)]) == 0
    assert out.stat().st_size > 1000
    assert out.read_bytes()[:5] == b"%PDF-"
    # 4 picture cards (appel, auto, zebra, zon) + 2 letter cards
    assert "6 cards" in capsys.readouterr().out


def test_cli_check_starter(capsys):
    assert main(["check", "starter"]) == 0
    assert "deck is valid" in capsys.readouterr().out


def test_cli_render_no_match(tmp_path):
    assert main(["render", "starter", "--letters", "q",
                 "-o", str(tmp_path / "x.pdf")]) == 1


def test_letter_colors_vowel_consonant_split():
    """Vowels warm, consonants cool; alphabet neighbors never share a color."""
    from lettercards.layout import LETTER_COLORS, VOWELS
    alphabet = "abcdefghijklmnopqrstuvwxyz"
    assert set(LETTER_COLORS) == set(alphabet)
    for letter, color in LETTER_COLORS.items():
        warm = color.red > color.blue
        assert warm == (letter in VOWELS), f"{letter} breaks the warm/cool rule"
    for a, b in zip(alphabet, alphabet[1:]):
        assert LETTER_COLORS[a] != LETTER_COLORS[b], f"{a}/{b} share a color"


def test_letter_colors_meet_contrast_on_cream():
    """Every accent clears WCAG 3:1 on the cream card, so the highlighted
    first letter — the phonics cue — stays legible (guards o/e/i regressions)."""
    from lettercards.layout import LETTER_COLORS, BG_CARD

    def rel_lum(c):
        ch = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
              for v in (c.red, c.green, c.blue)]
        return 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2]

    cream = rel_lum(BG_CARD)
    for letter, color in LETTER_COLORS.items():
        lo, hi = sorted((cream, rel_lum(color)))
        assert (hi + 0.05) / (lo + 0.05) >= 3.0, f"{letter} fails 3:1 on cream"


def test_rendered_page_actually_shows_a_card(tmp_path):
    """Guard the central rule: a rendered page contains card ink and words,
    not just a valid %PDF- header. Catches white-on-white and missing draws."""
    fitz = pytest.importorskip("fitz")  # pymupdf, dev extra
    from lettercards import layout as L
    out = tmp_path / "z.pdf"
    assert main(["render", "starter", "--cards", "zebra", "-o", str(out)]) == 0
    page = fitz.open(out)[0]
    assert "zebra" in page.get_text().lower()            # the word made it in
    scale = 150 / 72
    pix = page.get_pixmap(dpi=150)
    x0, y0, cw, ch = (L.MARGIN_X * scale, L.MARGIN_Y * scale,  # top-left card box
                      L.CARD_W * scale, L.CARD_H * scale)

    def region(fx0, fy0, fx1, fy1):
        xs = range(int(x0 + fx0 * cw), int(x0 + fx1 * cw), 2)
        ys = range(int(y0 + fy0 * ch), int(y0 + fy1 * ch), 2)
        px = [pix.pixel(x, y) for y in ys for x in xs]
        return [sum(p[i] for p in px) / len(px) for i in range(3)], px

    _, image_px = region(0.25, 0.15, 0.75, 0.6)          # picture area
    assert min(sum(p) / 3 for p in image_px) < 120       # real ink, not white-on-cream
    band, _ = region(0.2, 0.8, 0.8, 0.95)                # accent band
    corner, _ = region(0.02, 0.02, 0.06, 0.08)           # bare card cream
    assert corner[0] - band[0] > 20                      # band tint differs from background


def test_cli_render_missing_deck_is_friendly(tmp_path, capsys):
    """A missing deck exits 1 with one error line, not a raw traceback."""
    rc = main(["render", str(tmp_path / "nope"), "-o", str(tmp_path / "x.pdf")])
    assert rc == 1
    assert "error:" in capsys.readouterr().err


def test_render_rect_and_cut_lines(tmp_path):
    """--rect and --cut-lines both render; cut guides add vector paths."""
    fitz = pytest.importorskip("fitz")
    plain, cut = tmp_path / "plain.pdf", tmp_path / "cut.pdf"
    assert main(["render", "starter", "--cards", "zebra", "-o", str(plain)]) == 0
    assert main(["render", "starter", "--cards", "zebra",
                 "--rect", "--cut-lines", "-o", str(cut)]) == 0
    n_plain = len(fitz.open(plain)[0].get_drawings())
    n_cut = len(fitz.open(cut)[0].get_drawings())
    assert n_cut > n_plain  # dashed guides are extra strokes on the page


def test_version_is_single_sourced(capsys):
    """--version, package metadata, and __version__ come from one place, so a
    downstream git-install can trust the reported version (guards a1/a2 drift)."""
    from importlib.metadata import version
    import lettercards

    with pytest.raises(SystemExit):        # argparse --version exits 0 after printing
        main(["--version"])
    printed = capsys.readouterr().out.strip()
    assert printed == lettercards.__version__ == version("lettercards")


def test_cli_photo_crops_square(tmp_path):
    from PIL import Image
    src = tmp_path / "portrait.jpg"
    Image.new("RGB", (600, 900), "#3366AA").save(src)
    out = tmp_path / "images" / "oma.png"
    assert main(["photo", str(src), str(out), "--size", "400"]) == 0
    with Image.open(out) as img:
        assert img.size == (400, 400)


def test_cli_photo_pictogram_flattens_background(tmp_path):
    from PIL import Image, ImageDraw
    src = tmp_path / "raw.png"
    img = Image.new("RGB", (1024, 1024), (250, 244, 235))  # mottled-ish, near cream
    ImageDraw.Draw(img).ellipse((300, 300, 724, 724), fill="#E8503A")
    img.save(src)
    out = tmp_path / "vis.png"
    assert main(["photo", str(src), str(out), "--pictogram"]) == 0
    with Image.open(out) as result:
        assert result.size == (800, 800)                     # PICTOGRAM_SIZE, ~300dpi
        assert result.getpixel((2, 2)) == (255, 248, 240)   # background now card cream
        assert result.getpixel((400, 400)) != (255, 248, 240)  # subject untouched

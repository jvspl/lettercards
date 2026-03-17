# Project: Letterkaarten (Dutch Letter Learning Cards)

## What is this?

A card generator for teaching a toddler (almost 2 years old) to associate letter sounds with words she already knows — in Dutch. Inspired by physical puzzles she already uses (e.g., "l is for leeuw" with a lion picture).

Each word produces **two cards**:
1. **Picture card**: image + word (first letter in accent color) + small letter indicator in corner
2. **Letter card**: big letter centered, with uppercase/lowercase variant shown small

The output is a **printable A4 PDF** with 9 cards per page (3×3 grid, playing card size ~6×9cm).

## Who is this for?

Jeroen's daughter. The words are chosen because she knows them — not from a generic word list. This means:
- Many cards use **personal photos** (oma, opa, papa, mama, abu, Mees, Lena, Laura)
- Other cards use simple drawn illustrations or eventually real photos/clipart
- The word list will grow over time as she learns new words

## How it works

1. Edit `cards.csv` to add/remove words
2. Drop images in `images/` folder
3. Run `python generate.py` to produce `letterkaarten.pdf`
4. Print on A4 paper (ideally 160+ g/m² or laminated)

### Key commands

```bash
python generate.py                      # All cards
python generate.py --letters a,d,o      # Specific letters only
python generate.py --font Lato          # Override font for all cards
python generate.py --no-placeholders    # Skip placeholder image generation
```

## Architecture

```
cards.csv              # Word list config (letter, word, image filename, font, personal flag)
generate.py            # Main PDF generator (reportlab + Pillow)
draw_placeholders.py   # Generates simple hand-drawn placeholder PNGs
images/                # All card images (personal photos + generated placeholders)
fonts/                 # Drop custom .ttf files here, they're auto-registered
letterkaarten.pdf      # Generated output (gitignored)
```

### cards.csv format

```csv
letter,word,image,font,personal
a,appel,appel.png,,no
o,oma,oma.png,,yes
```

- Lines starting with `#` in the letter column are treated as comments/headers
- `personal=yes` means a real photo is needed; the generator won't create a placeholder
- `font` column is optional; leave blank for automatic rotation between available fonts
- Words with "geen voorbeeld" are skipped

### Font system

The script auto-registers:
- System fonts: DejaVuSans, Lato, Carlito, LiberationSans, DejaVuSerif, Caladea
- Any .ttf files dropped in `fonts/`
- Cards automatically rotate between fonts (based on word hash) for variety
- Font can be overridden per-card in CSV or globally via `--font` flag

### Color system

Each letter has a unique accent color defined in `LETTER_COLORS` in generate.py. This color is used for:
- The highlighted first letter in the word
- The big letter on letter cards
- The small letter indicator in the corner of picture cards
- Placeholder image tinting

## Design decisions

- **Playing card size (6×9cm)**: good for small hands, fits 9 per A4 page
- **First letter in color, rest in dark**: makes the letter-sound connection visual
- **Warm cream background for picture cards, light blue for letter cards**: easy to tell apart
- **Different fonts per card**: deliberate — she should learn to recognize letters in multiple forms
- **One letter card per unique letter** (not per word): avoids too many duplicate letter cards
- **Lowercase is primary**: the big letter on letter cards is lowercase, with uppercase shown small below. This is because lowercase is what she'll encounter most in reading.

## Current word list

### Priority letters (she knows these ~5): A, D, E, O, W, Z
### Secondary letters: F, K, M, N, P, S
### Skipped: Q, X, Y (not useful in Dutch for a toddler)

### Personal photo cards needed
- abu, oma, opa, mama, papa, Mees, Lena, Laura

## Working style

- Jeroen will add words and ideas over time
- When adding a new word: add CSV row + image, regenerate PDF, verify it looks right
- For personal photo cards: Jeroen provides the photos, they get cropped/placed in images/
- For generic words: draw_placeholders.py creates simple Pillow-drawn illustrations; these can be upgraded to better images over time

## Workflow

### Backlog
- **GitHub Issues** is the backlog: https://github.com/jvspl/lettercards/issues
- Jeroen can add issues directly on GitHub or ask Claude to create them
- Labels: `new-letter`, `personal-photo`, `enhancement`

### Making changes
1. Pick an issue from the backlog
2. Create a feature branch: `git checkout -b issue-3-letter-i`
3. Make changes, test with `python generate.py`
4. Create PR referencing the issue (e.g., "Fixes #3")
5. Merge when ready — issue auto-closes

### Communication via GitHub
- Jeroen may comment on issues/PRs from the web
- Claude can check comments with `gh issue view #N --comments` or `gh pr view`
- At session start, Jeroen can point Claude to new comments to review

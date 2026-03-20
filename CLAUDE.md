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

## Personas

Consider these perspectives when planning, building, and reviewing changes.

### Lena (the learner)
Almost 2 years old. The whole point of this project.
- **Needs**: Cards that are fun, colorful, and show things she recognizes
- **Approves**: Bright colors, clear images of familiar things, her favorite people
- **Rejects**: Confusing images, abstract concepts, things she doesn't know yet
- **Favorite styles**: Nijntje (Miffy), Dikkie Dik, Bobbie - use these as reference for illustrations
- **Ask**: "Will Lena smile when she sees this card? Will she point and say the word?"

### Jeroen (the parent/operator)
Creates and prints the cards. Uses Claude to help build and maintain this.
- **Needs**: Quick iteration, easy photo workflow, minimal friction
- **Approves**: Simple commands, clear docs, things that just work
- **Rejects**: Complex setup, manual repetitive tasks, unclear errors
- **Ask**: "Can I add a new word in under 2 minutes? Is this obvious how to use?"

### The Pedagogue
Ensures cards actually help a toddler learn letter-sound associations.
- **Needs**: Age-appropriate design, clear letter prominence, known words only
- **Approves**: First letter visually distinct, lowercase primary, words she speaks
- **Rejects**: Uppercase-focused design, abstract words, cluttered layouts
- **Ask**: "Does this reinforce the connection between the letter sound and the word?"

### The Designer
Cares about visual appeal and consistency across all cards.
- **Needs**: Good typography, balanced layouts, appealing color palette
- **Approves**: Professional look, visual variety without chaos, readable fonts
- **Rejects**: Cluttered cards, inconsistent styling, poor image quality
- **Ask**: "Would I be proud to show these cards to someone? Do they look intentional?"

### The Engineer
Keeps the codebase healthy and maintainable.
- **Needs**: Clean code, good documentation, no over-engineering
- **Approves**: Simple solutions, clear naming, appropriate abstractions
- **Rejects**: Premature optimization, unnecessary complexity, copy-paste code
- **Ask**: "Will I understand this code in 6 months? Is this the simplest solution?"

### The Architect
Oversees the project holistically and keeps all personas aligned.
- **Needs**: Clear direction, manageable scope, personas working together
- **Approves**: Features that serve multiple personas, good tradeoffs
- **Rejects**: Scope creep, features that harm one persona for another
- **Ask**: "Are we still building letter cards for Lena? Is everyone happy?"

### Using personas

When writing issues or PRs:
- Consider which personas are affected
- Note any tradeoffs between personas
- The Architect resolves conflicts (usually: Lena > Jeroen > Pedagogue > Designer > Engineer)

## Setup

```bash
# Clone and enter the repo
git clone https://github.com/jvspl/lettercards.git
cd lettercards

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Create personal photos directories
mkdir -p ~/.lettercards/personal ~/.lettercards/staging
```

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
python generate.py --personal-dir /path # Custom personal photos location
```

## Architecture

```
cards.csv              # Word list config (letter, word, image filename, font, personal flag)
generate.py            # Main PDF generator (reportlab + Pillow)
process_photo.py       # Personal photo processor (crop, resize, save)
pictogram_workflow.py  # ChatGPT pictogram generator workflow
draw_placeholders.py   # Generates simple hand-drawn placeholder PNGs (legacy)
images/                # Generic card images (placeholders, clipart)
fonts/                 # Drop custom .ttf files here, they're auto-registered
requirements.txt       # Python dependencies (pillow, reportlab)
venv/                  # Virtual environment (gitignored, create with setup)
letterkaarten.pdf      # Generated output (gitignored)
```

### What goes where

**In the repo (public):**
- Code: `generate.py`, `pictogram_workflow.py`, `process_photo.py`, `draw_placeholders.py`
- Config: `cards.csv`, `CLAUDE.md`
- Fonts: `fonts/` folder
- Generic images: `images/` (placeholders, non-personal illustrations)

**Outside the repo (private):**
- Personal photos: `~/.lettercards/personal/` (or custom location)
- Generated PDF: `letterkaarten.pdf` (gitignored)

### Personal images folder

Personal photos (family members, etc.) are stored outside the repo for privacy.

**Default location:** `~/.lettercards/personal/`

**Override via environment variable:**
```bash
export LETTERCARDS_PERSONAL_DIR=/custom/path
```

**Override via CLI flag:**
```bash
python generate.py --personal-dir /custom/path
```

The lookup order is: CLI flag > environment variable > default path.

For cards marked `personal=yes` in `cards.csv`, the generator looks for the image in the personal folder first, then falls back to `images/`.

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

## Personal photo workflow

For cards that need real photos (family members, etc.), there's a workflow to help select and process photos.

### Directories
- **Staging:** `~/.lettercards/staging/` — drop candidate photos here
- **Personal:** `~/.lettercards/personal/` — processed photos go here (used by generator)

### Quick workflow

```bash
# 1. See what's in staging
python process_photo.py --list

# 2. Process a photo (crops to square, resizes to 400x400)
python process_photo.py oma                    # Uses first image in staging
python process_photo.py oma IMG_1234.jpg       # Uses specific image

# 3. Preview without saving
python process_photo.py oma --preview

# 4. Verify by generating the card
python generate.py --letters o
```

### With Claude assistance

When working with Claude (CLI, Desktop, or web), you can get help selecting the best photo:

1. Drop multiple candidate photos into `~/.lettercards/staging/`
2. Tell Claude who they're for (e.g., "photos of oma in staging")
3. Claude reviews and recommends the best one
4. Claude processes and saves it
5. Generate PDF to verify

### Tips

- **Portrait photos work best** — faces should be in the upper portion
- **Multiple candidates are fine** — Claude can help pick the best one
- **Photos app limitation:** Can't drag directly from macOS Photos app. Export first (File > Export) or use Share > Save to Files.

### Photos status

| Person | Filename | Status |
|--------|----------|--------|
| abu | abu.png | Done |
| oma | oma.png | Pending |
| opa | opa.png | Pending |
| mama | mama.png | Pending |
| papa | papa.png | Pending |
| Mees | mees.png | Pending |
| Lena | lena.png | Pending |
| Laura | laura.png | Pending |

## Pictogram workflow

For generating child-friendly illustrations using ChatGPT/DALL-E. This replaces the simple geometric placeholders with proper illustrations.

### Why ChatGPT?

- **Quality**: ChatGPT/DALL-E produces high-quality, child-friendly illustrations in the style we need
- **Claude limitation**: Claude's image generation doesn't match the quality needed for toddler-friendly illustrations
- **Free tier**: We use ChatGPT's free tier, which has rate limits on image generation
- **Grid optimization**: Generating 6 images in a 3x2 grid maximizes efficiency within rate limits
- **Automation**: This script handles the splitting/processing so the manual work is minimal

### Quick workflow

```bash
# 1. Check which images need work
python pictogram_workflow.py status

# 2. Generate a ChatGPT prompt for specific words
python pictogram_workflow.py prompt eend zon fiets

# 3. Paste the prompt in ChatGPT, download the grid image

# 4. Drop the image in staging folder
# Move/copy to ~/.lettercards/staging/

# 5. Split the grid into individual images
python pictogram_workflow.py split eend zon fiets

# 6. Verify and generate PDF
python generate.py
```

### Commands

```bash
# Status - see which images are missing or need improvement
python pictogram_workflow.py status
python pictogram_workflow.py status -v  # Include OK images

# Prompt - generate ChatGPT prompts
python pictogram_workflow.py prompt WORD WORD...  # Specific words
python pictogram_workflow.py prompt --missing     # All missing images

# Split - extract images from a ChatGPT grid
python pictogram_workflow.py split NAMES...           # Auto-detect grid
python pictogram_workflow.py split NAMES... --grid 3x2  # Specify grid
python pictogram_workflow.py split NAMES... --preview   # Preview first
```

### Style guidance

The prompts use a style inspired by Dutch children's books:
- **Nijntje (Miffy)**: simple, rounded, minimalist
- **Dikkie Dik**: warm, friendly, slightly more detail
- **Bobbie**: colorful, appealing to toddlers

All images use a cream/beige background for consistency.

### Tips

- ChatGPT generates 1024x1024 images
- Grids of 6 (3x2) work well - saves on rate limits
- The split command center-crops to square and resizes to 400x400
- Keep staging images until verified (use `--keep` flag)

## Working style

- Jeroen will add words and ideas over time
- When adding a new word: add CSV row + image, regenerate PDF, verify it looks right
- For personal photo cards: Jeroen provides the photos, they go in `~/.lettercards/personal/`
- For generic words: use `pictogram_workflow.py` to generate illustrations via ChatGPT

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
5. Wait for review/approval, then merge — issue auto-closes

**Important:** Direct pushes to `master` are blocked. All changes must go through a PR with at least one approval.

### PR best practices
- **Don't force-push or amend** — make new commits instead to preserve history
- **Don't close and reopen PRs** — add new commits to the existing PR to preserve review context
- **Update PR description** when making significant changes
- **Reply to comments** explaining what was changed and how it addresses the feedback
- **Check for comments** before pushing: `gh pr view --comments`
- Keep commits focused and descriptive

### Shell command conventions
- **No compound commands** — never chain with `&&` or `;`; use separate Bash calls instead (permission matching breaks on compound commands)
- **`gh pr create` / `gh issue create` body** — write body to `.tmp/pr-body.md`, use `--body-file .tmp/pr-body.md`; never inline `--body` with `#` or newlines (breaks permission matching), never heredocs

### Communication via GitHub
- Jeroen may comment on issues/PRs from the web
- Claude can check comments with `gh issue view #N --comments` or `gh pr view`
- At session start, Jeroen can point Claude to new comments to review

### Session startup routine
At the start of each session, Claude should:
1. **Check the backlog** - `gh issue list --state open`
2. **Review new issues/comments** - look for recent activity
3. **Check open PRs** - `gh pr list --state open`
4. **Think from personas** - what would Lena, Jeroen, Pedagogue want?
5. **Clean up stale issues** - close completed work, update status
6. **Suggest next steps** - offer 2-3 options based on priority

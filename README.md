# lettercards

Generate printable A4 letter-learning cards for toddlers: picture cards (image + word, first letter in an accent color — warm for vowels, cool for consonants) and letter-family cards (one big letter plus a specimen row of its other everyday shapes — capital, serif, handwritten). Feed it a deck — a `deck.csv` word list plus images — and it renders a print-ready PDF. Fonts are bundled, so cards render identically everywhere.

## Usage

```bash
pip install git+https://github.com/jvspl/lettercards.git
lettercards render starter -o cards.pdf     # render the bundled starter deck
lettercards render path/to/your-deck -o cards.pdf
lettercards render starter --letters a,z    # only some letters
lettercards render starter --cards zebra    # reprint specific cards
lettercards check path/to/your-deck         # validate deck.csv and images
lettercards photo IMG_1234.jpg images/oma.png   # crop a photo into a square card image
```

## Deck format

A deck is a directory with a `deck.csv` and (optionally) an `images/` directory:

```csv
letter,word,image,language,status,notes
a,appel,appel.png,nl,active,
k,kasteel,,nl,idea,needs image
```

- `status`: `idea` (word without image yet), `active` (rendered), `retired` (skipped).
- `image` resolves against the deck's own `images/` first, then the bundled starter images.
- `language`: BCP-47-ish code (`nl`, `es`); shown as a small colored pill on each picture card. Defaults to `nl`.
- Lines starting with `#` are comments.

## Starter deck

`lettercards/starter/` is a complete, ready-to-print Dutch deck: 37 words with child-friendly pictograms (Nijntje-ish style), bundled with the package so `lettercards render starter` works anywhere after install. It covers every native-Dutch initial letter; `c`, `q`, `x`, and `y` are consciously skipped as loanword-only letters (native `c` occurs only in the `ch` digraph, and `q`/`x`/`y` appear essentially only in loanwords — no toddler-pointable native word). Image provenance and licensing are tracked in [lettercards/starter/images/SOURCES.md](lettercards/starter/images/SOURCES.md).

## Using the cards

Print on thick paper (≥ 200 g/m²) or laminate — plain paper doesn't survive toddlers.

The rest is what to do once you have the deck in hand, and it prints as the final page so it travels with the cards:

The deck grows with the child — don't use all of it at once. Show a card, say the word, and let the child point and name it; a handful of cards at a time, led by the child's interest. Keep it playful, and stop before it becomes a drill.

Say letter sounds, not names — “mmm”, not “em”. The colored first letter is that sound — the first sound of the word — and every card for a letter shares its band color, so the cards sort into families.

Filtered reprints (`--letters`/`--cards`) skip the how-to page; `--no-howto` omits it from a full render too.

> The staged letter-learning progression (ages, voices, blending) is deliberately **not** here — it's the v3 pedagogy, tracked in [#26](https://github.com/jvspl/lettercards/issues/26). v2 keeps this page small and practical.

## Project rules

- **Line budget: ≤ 1,000 lines of Python including tests.** A feature that threatens the budget gets questioned before the budget does.
- **No deck-management commands.** Adding words or changing statuses is editing `deck.csv` directly — by hand or by an assistant — not CLI work.
- **PRs only for changes that could break rendering.** Docs and starter-deck tweaks go straight to `main`.

## Privacy rule

This repo is public and generic. Personal data — family photos, names, per-child progress — never goes here, not in code, fixtures, issues, or commit messages. Keep your own deck in a private repo or local directory.

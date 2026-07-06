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

`lettercards/starter/` is a complete, ready-to-print Dutch deck: 32 words with child-friendly pictograms (Nijntje-ish style), bundled with the package so `lettercards render starter` works anywhere after install. Image provenance and licensing are tracked in [lettercards/starter/images/SOURCES.md](lettercards/starter/images/SOURCES.md).

## Using the cards

Print on thick paper (≥ 200 g/m²) or laminate — plain paper doesn't survive toddlers. The deck grows with the child; don't use all of it at once. The ages below are the roughest of guides: children vary enormously and many are keen on letters long before they're "supposed" to be — follow the child, not the number. Say letter sounds, not names — “mmm”, not “em”. The word list is curated for this: the first letter is the first sound.

- **Naming from ~1:** As soon as the child points at and names pictures — often early in the second year — start here. Picture cards only; letter cards stay in the drawer. Show a card, say the word, let the child point and name. A handful of cards at a time, led by the child's interest. The printed word is for you, not them.
- **First sounds from ~2:** Sound games with the picture cards: “b-b-b… bal!” The colored first letter shows what to stress. Sort cards by first sound — all cards for a letter share their band color.
- **Letters child-led, often 2–5:** Bring in the letter-family cards; match picture cards to their letter. Plenty of children are fascinated by letters as toddlers — if she's already pointing at them, follow her lead. The specimen row is the same letter in different clothes.

The same guidance prints as the final page of a full `lettercards render`, so it travels with the deck. Filtered reprints (`--letters`/`--cards`) skip it; `--no-howto` omits it from a full render too.

## Project rules

- **Line budget: ≤ 1,000 lines of Python including tests.** A feature that threatens the budget gets questioned before the budget does.
- **No deck-management commands.** Adding words or changing statuses is editing `deck.csv` directly — by hand or by an assistant — not CLI work.
- **PRs only for changes that could break rendering.** Docs and starter-deck tweaks go straight to `main`.

## Privacy rule

This repo is public and generic. Personal data — family photos, names, per-child progress — never goes here, not in code, fixtures, issues, or commit messages. Keep your own deck in a private repo or local directory.

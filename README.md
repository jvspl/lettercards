# lettercards

Generate printable A4 letter-learning cards for toddlers: picture cards (image + word, first letter in an accent color) and letter cards (one big letter). Feed it a deck — a `deck.csv` word list plus images — and it renders a print-ready PDF.

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
- `language`: BCP-47-ish code (`nl`, `es`); used for per-language card styling.
- Lines starting with `#` are comments.

## Starter deck

`lettercards/starter/` is a complete, ready-to-print Dutch deck: 34 words with child-friendly pictograms (Nijntje-ish style), bundled with the package so `lettercards render starter` works anywhere after install. Image provenance and licensing are tracked in [lettercards/starter/images/SOURCES.md](lettercards/starter/images/SOURCES.md). The rewrite plan for this project lives in [REWRITE-PLAN.md](REWRITE-PLAN.md).

## Privacy rule

This repo is public and generic. Personal data — family photos, names, per-child progress — never goes here, not in code, fixtures, issues, or commit messages. Keep your own deck in a private repo or local directory.

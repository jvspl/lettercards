# lettercards

Generate printable A4 letter-learning cards for toddlers: picture cards (image + word, first letter in an accent color) and letter cards (one big letter). Feed it a deck — a `deck.csv` word list plus images — and it renders a print-ready PDF.

**Status: v2 rewrite in progress.** This repo currently ships the starter deck content; the renderer lands next (see [REWRITE-PLAN.md](REWRITE-PLAN.md), Phase 1). The v1 implementation lived in a previous repo and is being rewritten from scratch, smaller.

## Intended usage (Phase 1 target)

```bash
pip install git+https://github.com/jvspl/lettercards.git
lettercards render starter -o cards.pdf     # render the bundled starter deck
lettercards render path/to/your-deck -o cards.pdf
lettercards check path/to/your-deck         # validate deck.csv and images
```

## Deck format

A deck is a directory with a `deck.csv` and (optionally) an `images/` directory:

```csv
letter,word,image,language,status,notes
a,appel,appel.png,nl,active,
k,kasteel,,nl,idea,needs image
```

- `status`: `idea` (word without image yet), `active` (rendered), `retired` (skipped).
- `image` resolves against the deck's own `images/` first, then this repo's `starter/images/`.
- `language`: BCP-47-ish code (`nl`, `es`); used for per-language card styling.
- Lines starting with `#` are comments.

## Starter deck

`starter/` is a complete, ready-to-print Dutch deck: 34 words with child-friendly pictograms (Nijntje-ish style). Image provenance and licensing are tracked in [starter/images/SOURCES.md](starter/images/SOURCES.md).

## Privacy rule

This repo is public and generic. Personal data — family photos, names, per-child progress — never goes here, not in code, fixtures, issues, or commit messages. Keep your own deck in a private repo or local directory.

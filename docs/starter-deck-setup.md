# Starter deck repo setup (Issue #105)

This repo is the **engine** and also ships a reusable **starter deck**.
Use the steps below when you want to create a separate deck repo (for family-specific words/photos) while still using `lettercards` as the generator.

## What lives where

- **`lettercards` (this repo):** code + default starter deck assets.
- **your deck repo:** your custom `deck.csv`, optional `deck-state.json`, and personal images.

## 1) Create a new deck repo

Create an empty GitHub repo (example: `my-family-lettercards-deck`) and clone it locally.

```bash
git clone git@github.com:<you>/my-family-lettercards-deck.git
cd my-family-lettercards-deck
```

## 2) Copy the starter deck from this repo

From inside your deck repo, copy the starter deck files from a local checkout of `lettercards`:

```bash
cp /path/to/lettercards/starter-deck/deck.csv ./deck.csv
cp -R /path/to/lettercards/starter-deck/images ./images
```

You now have a fully working starter deck that can generate cards immediately.

## 3) Install the generator (recommended for this branch)

Keep generator code versioned separately from your deck content:

```bash
git clone git@github.com:<you-or-org>/lettercards.git
python3 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -e /path/to/lettercards
```

If you prefer the packaged release instead of local source:

```bash
pip install lettercards
```

## 4) Generate using your deck repo files

Run generation and point to your deck files:

```bash
lettercards generate --csv ./deck.csv --output ./letterkaarten.pdf
lettercards deck check --csv ./deck.csv
```

If your shell cannot find the `lettercards` command, run through Python directly:

```bash
python -m lettercards generate --csv ./deck.csv --output ./letterkaarten.pdf
python -m lettercards deck check --csv ./deck.csv
```

## 5) Customize safely

- Add your own words in `deck.csv`.
- Place personal photos in your deck repo `images/` folder and reference them by filename.
- Commit changes to your deck repo without changing upstream `lettercards` code.

### Quick personal-card smoke test

After copying starter files, add one personal card and verify:

```bash
cp ./images/appel.png ./images/oma.png
echo "o,oma,oma.png,,yes,active,,nl" >> ./deck.csv
lettercards deck check --csv ./deck.csv
lettercards generate --csv ./deck.csv --no-placeholders --output ./letterkaarten.pdf
```

## Updating from upstream

When new `lettercards` versions are released, upgrade in your deck repo environment:

```bash
pip install -U lettercards
```

If the starter deck format changes, copy only the pieces you want from the latest `starter-deck/` and review with `lettercards deck check`.

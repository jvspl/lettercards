# lettercards — engine

Generic deck→PDF renderer for toddler letter-learning cards. This repo is
**public and generic**: no family data, ever — no names in code, fixtures,
issues, or commit messages. The private family decks live in a separate repo.

## Rules

- **Line budget: ≤ 1,000 lines of Python including tests**
  (`wc -l lettercards/*.py tests/*.py`). Question the feature before the budget.
- **PRs only for changes that could break rendering.** Docs and starter-deck
  content go straight to `main`.
- **No deck-management CLI.** Adding words or changing statuses is editing
  `deck.csv` directly.
- Tests: `pip install -e ".[dev]" && python -m pytest -q`. Keep them fast, and
  reproduce anything with starter-deck words only.
- Docs budget: README, this file, and `lettercards/starter/images/SOURCES.md`.
  No ADRs, no extra process docs.

## Card images

The house style ("Zebra–Nijntje–Ghibli"), master generation prompt, acceptance
criteria, and the API generation recipe live in
`lettercards/starter/images/SOURCES.md`. This repo's cloud environment has
`OPENAI_API_KEY` set and `api.openai.com` allowed — generate images here, not
in the family environment (it stays network-tight). Intake raw generations with
`lettercards photo <raw> images/<word>.png --pictogram`.

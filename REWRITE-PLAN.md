# Lettercards v2 — Rewrite Plan

**Status:** Agreed with Jeroen, 2026-07-03. This document supersedes the v1 `docs/architecture.md` and is the founding document of the v2 setup.

**Progress (2026-07-04):** Phases 0–2 done — repos split, engine v0 shipped (render/check/photo), print-from-phone proven, Kleurblok design with letter-family specimen rows and language pills implemented. Phase 2's only remainder is taking the new personal photos. Phase 3 (Laura's deck, Spanish words) awaits Laura's starting point and a session with Pilar. Phase 4: v1 repo archived without issue migration — still-relevant ideas were carried into the design (bilingual, letter variation) or into engine issue #1.

## Why restart

The v1 verdict, honestly:

- **Process ate the product.** 118 merged PRs produced ~2,800 lines of Python whose core job is "CSV in, A4 PDF out". Ten personas, a security protocol, ADRs, custom hooks, hook tests, and phased migration plans consumed most sessions. The governance was built for a team; there is one parent and one assistant.
- **The v1 architecture was right but never executed.** The three-layer design (generic engine / private deck / Claude as interface) is still correct. Incremental migration on a codebase this small was the mistake — Phase 2 (content separation) never landed, and personal family names shipped in a **public** repo.
- **Requirements changed.** Printing from the phone was a v1 non-goal. It is now a v2 requirement — and it turns out to need zero infrastructure.

Decision: clean cut. Keep the pictogram images and the lessons. Delete the code, the process apparatus, and the repo history that contains personal data.

## Target setup: two repos

| Repo | Visibility | Contents |
|------|-----------|----------|
| `jvspl/lettercards` (fresh) | Public | The engine: deck → PDF renderer, generic starter images, fonts. Nothing personal, ever — not even names in test fixtures. |
| `jvspl/lettercards-family` (new) | Private | Everything about our family: per-child decks, personal photos, progress journals, print-ready output conventions. |

The current public repo is renamed to `jvspl/lettercards-v1` and **made private immediately** (its history and issues contain family names), then archived once v2 is running. Renaming frees the `lettercards` name for the fresh engine repo.

### Engine repo layout

```
lettercards/
├── lettercards/
│   ├── deck.py        # load + validate deck.csv, resolve images
│   ├── layout.py      # card design: layout, typography, colors
│   ├── render.py      # PDF assembly (A4, cut lines)
│   └── cli.py         # lettercards render / check
├── starter/
│   ├── deck.csv       # generic Dutch starter deck
│   └── images/        # the 34 generic pictograms from v1
├── fonts/
├── tests/
├── pyproject.toml
└── README.md
```

**Line budget: ≤ 1,000 lines of Python including tests.** If a feature threatens the budget, the feature is questioned first, the budget second. CLI surface is two commands:

```bash
lettercards render <deck-dir> [--letters a,b,c] [--cards zebra,opa] [-o out.pdf]
lettercards check  <deck-dir>     # validate CSV, missing images, duplicates
```

Deck management (adding words, changing status, recording progress) is **not** CLI work — Claude edits the data files directly. This was the one v1 insight that fully holds.

### Family repo layout

```
lettercards-family/
├── CLAUDE.md              # content-assistant instructions (≤ 40 lines)
├── setup.sh               # pip install git+https://github.com/jvspl/lettercards
├── decks/
│   ├── lena/
│   │   ├── deck.csv
│   │   └── journal.md     # progress + session log (see below)
│   └── laura/
│       ├── deck.csv
│       └── journal.md
└── images/                # personal photos + custom pictograms, shared across decks
```

**Deck format** (`deck.csv`), one per child:

```csv
letter,word,image,language,status,notes
a,appel,appel.png,nl,active,
o,opa,opa.png,nl,active,personal photo
c,casa,casa.png,es,active,
k,kasteel,,nl,idea,needs image
```

- `status`: `idea` (no image yet — phone ideation lands here), `active`, `retired`.
- `image` resolves against the family repo's `images/` first, then the engine's `starter/images/`. Children share images but not word lists.
- `language`: `nl` / `es`. Bilingual is first-class from day one; how language shows on the card (accent color, marker, nothing) is a Phase 2 design decision made with Pilar.

**Progress tracking** (`journal.md`), one per child — replacing v1's `deck-state.json` schema, which was elaborately designed and never accumulated a single real session in the repo. Markdown, because Claude reads and writes it natively, it never needs migrations, and a human can read it in the GitHub app:

```markdown
# Lena — journal

## Current status
Recognizes: A, O. Learning: D, E. Not yet started: rest.
Last session: 2026-07-01.

## Log
### 2026-07-01 — review session (~10 min)
Pointed at appel immediately. Confused zebra with paard again — consider retiring.
```

Claude maintains the "Current status" block; the log is append-only. No physical-card inventory tracking in v2 — the parent can see the table and just says "reprint zebra". Revisit only if it's actually missed.

## The four workflows (all phone-capable)

1. **Ideate** — on the phone: "words with K for Laura?" → Claude adds rows with status `idea` to her `deck.csv`, commits.
2. **Design a card** — pictogram generation or personal-photo processing, conversationally; image lands in `images/`, status → `active`. Photo pipeline details are Phase 2 scope.
3. **Print** — on the phone: "reprint zebra and the new K cards for Lena" → a Claude Code cloud session on the family repo runs `lettercards render`, **sends the PDF to the phone**, parent prints via AirPrint. This is the flagship flow; Phase 1 is not done until it has produced a physically printed card started from a phone.
4. **Review & progress** — on the couch: "she nailed appel, mixed up zebra again" → Claude appends to `journal.md`, updates card statuses, commits.

All four are conversation + data files. No app, no server, no GitHub Action needed for v1 of v2.

## Process rules (guardrails against a v1 repeat)

- **CLAUDE.md ≤ 40 lines per repo.** No persona tables. Three standing questions replace them: *Will Lena/Laura respond to it? Could it leak family data? Is it the simplest thing?*
- **No ADRs, no custom hooks, no skills** until a concrete recurring pain justifies one — and then exactly one.
- **Family repo: commit straight to `main`.** It's data. Git history is the undo button.
- **Engine repo: PRs only for changes that could break rendering**; docs and starter-deck tweaks go straight to `main`. No draft-PR ceremony, no mandated re-review loops.
- **Every phase ends with something printable.** A phase that only produces documents (this one excepted) is a smell.
- **Docs budget:** README per repo, this plan until superseded, nothing else.

## Privacy rules

1. `jvspl/lettercards-v1` goes private **on day one of Phase 0** — its public history contains family names.
2. Personal photos and family names live only in `lettercards-family`. The engine repo — code, fixtures, starter deck, issues, commit messages — stays name-free.
3. Cloud sessions that touch the family repo don't need broad network access; keep that environment's network policy tight.

## Phases

**Phase 0 — Cut over (one session + a few clicks from Jeroen)**
Rename old repo to `lettercards-v1`, make it private. Create fresh public `lettercards` and private `lettercards-family`. Copy the 34 generic pictograms + fonts into the engine's `starter/`; seed `decks/lena/` from the v1 word list (personal rows included — it's private now); scaffold `decks/laura/`.
*Jeroen:* approve repo names, upload personal photos from `~/.lettercards/personal/` on the laptop, salvage any local `deck-state.json` worth keeping into `journal.md`.
*Done when:* both repos exist, old repo is private, no personal data remains public.

**Phase 1 — Engine v0 + print-from-phone (1–2 sessions)**
Rewrite the renderer fresh (port the v1 card design as-is for now), `render` + `check`, minimal tests. Set up the cloud environment on the family repo with `setup.sh` installing the engine.
*Done when:* Jeroen, from his phone, asks for a PDF, receives it, and prints a card that Lena holds.

**Phase 2 — Card redesign (1–2 sessions, iterative)**
He chose to keep images but redesign the layout. Claude produces 2–3 layout variants as preview images, sent to the phone for review with Pilar; pick one; implement in `layout.py`. Decide the bilingual visual treatment here. Define the photo-processing flow for new personal cards.
*Done when:* a redesigned batch is printed and in use.

**Phase 3 — Laura's deck + progress rhythm (ongoing, small sessions)**
Fill Laura's deck (age-appropriate — see open questions), Spanish words with Pilar, and start using journals for real. Tune CLAUDE.md based on actual phone sessions.
*Done when:* both kids have live decks and two weeks of journal entries exist.

**Phase 4 — Retirement**
Archive `lettercards-v1`. Migrate the handful of still-relevant open issues (of 24) to the new repos as plain issues; close the rest without ceremony.

## Open questions

1. **Laura's age and starting point?** Determines whether her v1 deck is letters at all, or first just picture-word cards.
2. **Spanish pedagogy:** mixed-language play sessions or separate? Decide with Pilar during Phase 3, from practice not theory.
3. **Pictogram generation:** v1 used ChatGPT manually. Keep manual-with-guidance, or wire image generation into the workflow? Defer to Phase 2.

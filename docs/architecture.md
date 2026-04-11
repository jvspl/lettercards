# Lettercards Architecture Design

## Status

Proposed — March 2026

## Context

Lettercards is a card generator for teaching toddlers to associate letter sounds with words. It produces printable A4 PDFs with picture cards and letter cards. Built for Lena (almost 2), using words she knows, in Dutch.

The project started as a single Python script and has grown into several scripts, a personal photo workflow, an AI image generation pipeline, and a growing backlog of features (bilingual support, double-sided cards, card grouping mechanics). The codebase is maintained through Claude Code, which is also used for content authoring — adding words, processing photos, reviewing cards.

This document defines the target architecture that separates concerns, supports multiple users, and enables conversational deck management from any device.

## Problem

Three tensions are driving this redesign.

**Dev work and content work are tangled.** Claude Code sessions mix code changes (security hooks, bug fixes) with content operations (adding words, processing photos). These have different audiences, different rhythms, and different risk profiles. A content session shouldn't require git knowledge or Python environment awareness.

**Users need to know which script to run.** There are currently four scripts (`generate.py`, `pictogram_workflow.py`, `process_photo.py`, `draw_placeholders.py`), each with its own CLI interface. There's no unified entry point and no awareness of system state — what's ready to print, what's missing, what needs attention.

**The project is personal but the engine is reusable.** The code works for any parent teaching any toddler letter-sound associations. But the word list, images, and feedback are specific to one child. Today these live together in the repo, making it hard for someone else to use the tool for their own kid.

## Constraints

**Privacy is non-negotiable.** Personal family photos live outside the repo at `~/.lettercards/personal/`. No architectural change may weaken this boundary. The security persona in CLAUDE.md governs all decisions touching personal data.

**No over-engineering.** This is a side project for one family, with aspirations to be useful to others. The architecture should be the simplest thing that supports the target state. Build what's needed now, document what's intended for later.

**Mobile access is primarily for planning.** The real workflow is "think of words on the bus, batch-print at home." Mobile must support ideation, review, and deck management. PDF generation on mobile is not a requirement but could be a nice-to-have if the architecture allows it without significant complexity.

## Non-Goals

**Not a mobile app.** There is no custom UI, no app store presence. The conversational interface runs on existing Claude surfaces (Desktop, mobile, web).

**Not a classroom tool.** Lettercards is designed for parent-child use at home, not multi-student classroom management.

**Not a general flashcard system.** The system is specifically for letter-sound associations, not arbitrary flashcard content.

**Not real-time collaboration.** One parent manages the deck. There is no multi-user editing or conflict resolution.

## Runtime Flows

Four flows describe how the system is used day-to-day. Each flow shows which layers are involved and where it typically happens. The architecture layers are described in detail in the next section.

**Flow 1: Add a word suggestion** *(mobile, on the bus)*

The parent thinks of a word and tells Claude. Claude checks if the letter is covered, proposes the word, and adds it to `deck.csv` with status `pending`. No CLI involved — this is pure deck protocol CRUD through the conversational interface. The word doesn't become a printable card until it has an image (Flow 2).

Layers: 3 (conversation) → 2 (deck data via GitHub)

**Flow 2: Design a card** *(laptop, at home)*

A word in `deck.csv` has status `pending` — it needs an image before it becomes a printable card. Two sub-flows: Claude generates a pictogram (AI image generation pipeline), or Claude guides the parent through taking and processing a personal photo. Either way, the result is an image file in the deck's `images/` or `personal/` directory, and the card status moves from `pending` to `testing`. Could this work on mobile in the future? Photo guidance could; pictogram generation depends on the same server-side question as Flow 3.

Layers: 3 (conversation) → 1 (CLI for photo processing / pictogram generation) → 2 (deck data update)

**Flow 3: Generate and print cards** *(laptop, at home)*

The parent asks Claude what's ready to print. Claude compares active cards in `deck.csv` against the `printed_cards` inventory in `deck-state.json`, suggests a batch, and executes the CLI to generate the PDF. The parent prints, laminates, and confirms — Claude updates `printed_cards` and logs a print session. Could PDF generation work on mobile in the future? Possibly, if the engine can run server-side or as a lightweight service. The architecture doesn't prevent this, but it's not a near-term goal.

Layers: 3 (conversation) → 1 (CLI execution) → 2 (deck data update)

**Flow 4: Review session** *(couch, after playing with cards)*

The parent and child play with the cards. Afterward, the parent tells Claude how it went — which cards worked, which confused the child, any spontaneous letter recognition moments. Claude records a review session in `deck-state.json`, updates card statuses if needed (e.g., retire wolf, promote hond to active), and logs observations in the learning progress section. The pedagogue persona may suggest which letters to introduce next based on the progress data.

Layers: 3 (conversation) → 2 (deck data update)

## Target Architecture

The system is organized in three layers: the engine, the user deck, and the conversational interface.

```
┌─────────────────────────────────────────────────┐
│         Layer 3: Conversational Interface        │
│                                                  │
│   Claude Desktop / Claude Mobile / Claude Web    │
│   Reads deck data, manages workflows, tracks     │
│   feedback. No custom UI — just project          │
│   knowledge + structured deck data.              │
├─────────────────────────────────────────────────┤
│         Layer 2: User Deck                       │
│                                                  │
│   Per-user data: deck.csv, deck state, notes,    │
│   personal photos, custom images.                │
│   Storage: local (~/.lettercards/) or private    │
│   GitHub repo for cross-device access.           │
├─────────────────────────────────────────────────┤
│         Layer 1: Engine                          │
│                                                  │
│   Public repo: PDF generator, photo processor,   │
│   pictogram workflow. Ships with starter deck.   │
│   CLI is the base interface for execution.       │
└─────────────────────────────────────────────────┘
```

**Two base interfaces.** The system has two distinct interfaces with different purposes:

1. **CLI (`lettercards`)** — for compute-heavy execution: PDF generation, photo processing, pictogram creation, deck validation. These operations need a Python environment and local file access.

2. **Deck protocol (`deck.csv` + `deck-state.json`)** — for deck management: adding words, updating statuses, recording sessions, tracking progress. These are simple CRUD operations on structured data files. The conversational interface reads and writes these files directly — no CLI wrapper needed.

This split reflects a key insight: deck management is data manipulation, not computation. Wrapping every data operation in a CLI command would add complexity without value. Claude can read a CSV and add a row more naturally than invoking `lettercards add <word>`.

### Layer 1: Engine

The engine is the public repository (`jvspl/lettercards`). It contains reusable code and a starter deck. Anyone can clone it and generate cards.

**Module structure** (target, from current monolith):

```
lettercards/
├── lettercards/            # Python package
│   ├── __init__.py
│   ├── generator.py        # PDF layout and rendering (from generate.py)
│   ├── cards.py            # Card model, CSV parsing, deck operations
│   ├── photos.py           # Photo processing (from process_photo.py)
│   ├── pictograms.py       # Image generation workflow (from pictogram_workflow.py)
│   └── cli.py              # Unified CLI entry point (`lettercards` command)
├── starter/                # Starter deck (complete, ready to print)
│   ├── deck.csv            # Example word list (Dutch)
│   └── images/             # ChatGPT-generated pictograms
├── fonts/                  # Bundled fonts
├── tests/                  # Unit + integration tests
├── docs/
│   ├── adr/                # Architecture Decision Records
│   └── architecture.md     # This document
├── requirements.txt
└── README.md
```

**The CLI (`lettercards`) handles execution tasks:**

```bash
lettercards generate              # Generate PDF from user deck
lettercards generate --letters a,d,o
lettercards status                # Show deck state: what's ready, what's missing
lettercards photo process <name>  # Process a personal photo
lettercards deck init             # Initialize user deck from starter
lettercards deck check            # Validate deck integrity
```

**Starter deck.** The starter deck ships complete with images for every word — a new user can generate and print cards immediately after `lettercards deck init`. The generated pictograms and current Dutch word list serve as both working examples and a ready-to-print set for Dutch-speaking families. The deck protocol is designed so that additional curated decks could be shared in the future.

**Legacy script removal.** The existing standalone scripts (`generate.py`, `pictogram_workflow.py`, `process_photo.py`, `draw_placeholders.py`) will be removed once the `lettercards` CLI is verified as a complete replacement. Clean cut, no wrapper phase.

**First-run experience.** The architecture requires a clear first-run setup: install the package, run `lettercards deck init`, optionally connect a private GitHub repo. The conversational interface can guide new users through this process step by step.

### Layer 2: User Deck

Each user's deck lives outside the engine repo. It contains their personalized word list, card metadata, images, and session history.

**Default location:** `~/.lettercards/`

The top-level directory holds a configuration file and one or more named decks. Each deck is self-contained — it can be a local directory or a clone of a private GitHub repo.

```
~/.lettercards/
├── config.json             # Global config: active deck, deck registry
├── lena/                   # Lena's deck (local or git repo)
│   ├── deck.csv
│   ├── deck-state.json
│   ├── images/
│   ├── personal/
│   └── staging/
└── laura/                  # Laura's deck (could be a separate git repo)
    ├── deck.csv
    ├── deck-state.json
    ├── images/
    ├── personal/
    └── staging/
```

The `config.json` registers available decks and tracks which is active:

```json
{
  "active_deck": "lena",
  "decks": {
    "lena": {
      "path": "~/.lettercards/lena",
      "remote": "git@github.com:jvspl/lettercards-lena.git"
    },
    "laura": {
      "path": "~/.lettercards/laura",
      "remote": null
    }
  }
}
```

A deck with a `remote` is a git-backed deck — the engine can pull/push changes. A deck without a remote is local-only. This means you can have Lena's deck synced to GitHub (so Claude on mobile can access it) while Laura's deck is local-only.

**Deck CSV format (`deck.csv`).** This is the human-readable and human-editable file — the word list with status tracking and feedback:

```csv
letter,word,image,font,personal,status,notes,language
a,appel,appel.png,,no,active,,nl
w,wolf,wolf.png,,no,retired,"she says 'hond' instead",nl
o,oma,oma.png,,yes,active,,nl
h,hond,hond.png,,no,testing,"replacement for wolf",nl
k,kasteel,,,no,pending,"needs image",nl
```

Status values: `active` (in current print set), `testing` (try next print), `retired` (no longer used), `pending` (needs image or review). A word with status `pending` is not yet a printable card — it needs an image first.

**Deck state file (`deck-state.json`).** This file is machine-managed — users don't need to edit it directly. It's the operational memory of the deck, tracking session history, the physical card inventory, learning progress, and planning state. This is what allows the conversational interface to reason about the deck's state over time.

The file tracks:

**Physical card inventory (`printed_cards`).** This array tracks exactly which cards are currently in the physical, printed deck. It bridges the digital deck (all cards in `deck.csv`) and the real world (the cards on the table). Cards are added when printed, removed when lost, broken, or retired. Duplicates are supported — if you print a card twice, it appears twice. This is what Claude reads when answering "what should I print next?" — it compares active cards in the CSV against this inventory to find the gap.

**Sessions.** Three types of sessions are recorded:

- **Print sessions** — what was generated and when. Helps Claude suggest "you haven't printed the new K cards yet" or "last batch was two weeks ago."
- **Generation sessions** — when new cards or images were created. Tracks what's new and untested.
- **Review sessions** — feedback from playing with the cards. The most valuable data in the system. Includes free-text observations and an optional `duration_minutes` field. Review sessions close the loop between creating cards and learning what works.

**Learning progress.** Per-letter status and timestamped observations — see the Learning Progress section below.

```json
{
  "deck_protocol": "1.0",
  "next_batch": ["h", "k", "n"],
  "printed_cards": [
    {"word": "appel", "printed_date": "2026-03-20"},
    {"word": "deur", "printed_date": "2026-03-20"},
    {"word": "eend", "printed_date": "2026-03-20"},
    {"word": "oma", "printed_date": "2026-03-20"}
  ],
  "sessions": [
    {
      "date": "2026-03-18",
      "type": "generation",
      "summary": "Added words: appel, aap, auto for letter A",
      "cards_added": ["appel", "aap", "auto"],
      "cards_modified": []
    },
    {
      "date": "2026-03-20",
      "type": "print",
      "letters": ["a", "d", "e", "o"],
      "card_count": 12,
      "notes": "Printed on 160gsm, laminated"
    },
    {
      "date": "2026-03-22",
      "type": "review",
      "duration_minutes": 15,
      "letters_played": ["a", "d", "o"],
      "observations": [
        {
          "card": "appel",
          "reaction": "positive",
          "notes": "Points and says 'appel!' immediately"
        },
        {
          "card": "wolf",
          "reaction": "confused",
          "notes": "Says 'hond' instead — image doesn't distinguish well enough"
        },
        {
          "card": "oma",
          "reaction": "positive",
          "notes": "Very excited, recognized immediately"
        }
      ]
    }
  ],
  "progress": {
    "letters": {
      "a": {
        "status": "recognized",
        "first_introduced": "2026-03-20",
        "observations": [
          {"date": "2026-03-22", "note": "Points at A on cereal box"},
          {"date": "2026-03-25", "note": "Almost always recognizes A now"}
        ]
      },
      "d": {
        "status": "learning",
        "first_introduced": "2026-03-20",
        "observations": [
          {"date": "2026-03-22", "note": "Knows 'deur' but doesn't connect to letter yet"}
        ]
      }
    },
    "summary_snapshots": [
      {
        "date": "2026-03-25",
        "total_letters_introduced": 6,
        "recognized": ["a", "o"],
        "learning": ["d", "e"],
        "not_yet": ["w", "z"],
        "notes": "Good progress on vowels, consonants need more time"
      }
    ]
  }
}
```

**Data validation.** The engine validates deck integrity on startup — checking that the deck protocol version is compatible, required CSV columns exist, and referenced image files are present. The `lettercards deck check` command runs a more thorough validation on demand. Git is recommended for recovery from data issues; formal schema definitions for `deck.csv` and `deck-state.json` are future work.

**Storage options.** The engine reads from a deck directory — it doesn't care where that directory lives. Two storage paths are supported:

1. **Local files.** `~/.lettercards/` on the user's machine. Simple, private, works immediately. Suitable for getting started or for users who only work from one machine.

2. **Private GitHub repo (strongly recommended).** The user deck directory is a private GitHub repo. This is the recommended path because it enables the full conversational workflow: Claude can access the deck from any surface (Desktop, mobile, web) via GitHub integration. Deck changes are committed through Claude. This enables the "think on the bus, print at home" workflow — Claude reads the deck on mobile, proposes changes conversationally, and commits them. The laptop pulls and generates PDFs. Version history comes for free. The conversational interface handles all git operations transparently — the parent only needs a GitHub account, not git knowledge. Alternative sync mechanisms (Dropbox, iCloud) are potential future work but don't provide the same conversational access pattern.

### Layer 3: Conversational Interface

The conversational interface is not a feature to build — it is a protocol to design for. The engine and deck format are structured so that any Claude surface can act as an effective deck manager.

The protocol is also runtime-agnostic: any agentic environment (Claude surfaces, Codex cloud/web, or human-operated tooling) can participate if it can (a) read/write deck files and (b) interact with GitHub through built-in integrations, CLI tooling, or operator-assisted manual handoff.

**The interface is defined by two artifacts:**

**1. Content-mode project knowledge.** A CLAUDE.md (or Claude.ai Project knowledge file) that tells Claude how to behave as a deck assistant. It covers how to read and modify `deck.csv` and `deck-state.json`, what questions to ask during a review session, how to suggest new words, how to plan a print batch, and how to record feedback and update card status.

**2. Structured deck data.** The CSV and deck-state.json formats described above. `deck.csv` is designed to be both human-editable (you can open it in any editor) and Claude-readable. `deck-state.json` is machine-managed — Claude reads and writes it, users don't need to touch it.

**Personas and skills.** The architecture supports personas (defined in CLAUDE.md) and skills (defined in `.claude/agents/`). Some personas apply to Layer 1 development work (e.g., engineer, security researcher), while others apply to Layer 3 conversations (e.g., pedagogue, parent-facing personas). The specifics of which personas exist and how they're orchestrated are documented in CLAUDE.md and governed by ADR-001. Skills can encode specialized capabilities like security review or pedagogical analysis. Letter introduction order, for example, is a Layer 3 concern — the pedagogue persona suggests which letters to introduce next based on the child's progress data, rather than following a hardcoded sequence.

**Conversational workflows the protocol enables:**

- "What should I print next?" — Claude compares active cards in `deck.csv` against the `printed_cards` inventory to find the gap, then suggests a batch.
- "Lena liked appel but wolf confused her" — Claude updates card status, suggests a replacement word, records the session.
- "Add some words for the letter K" — Claude proposes age-appropriate Dutch words, adds them with status `pending`.
- "How's the deck looking?" — Claude summarizes coverage by letter, highlights gaps, flags cards that haven't been tested.
- "How is Lena's progress?" — Claude reads the progress section, summarizes which letters she recognizes, which are in progress, and generates a progress overview.

## Learning Progress Tracking

The `progress` section in `deck-state.json` tracks letter recognition development over time. Each letter has a status and a timestamped list of observations. This data is the raw material for pedagogical reporting — whether conversational summaries, generated charts, or exports for sharing with professionals.

**Letter status** reflects the current assessment: `not_introduced` → `introduced` → `learning` → `recognized` → `mastered`. Status can move backward — if a child regresses, the status is updated to reflect where they are now. The observation log preserves the full trajectory, so patterns like "she knew D last month but seems to have forgotten it" are visible in the data without needing explicit backward-transition rules.

**Observations** are free-text and timestamped. They capture everything from structured review sessions to spontaneous moments ("pointed at A on a cereal box"). Observations are kept simple for now — additional structured fields (reaction types, confidence levels) can be added in the future if analysis requires it.

**Summary snapshots** are periodic overall assessments. They can be used for progress reports and visualizations — for example, a chart showing how many letters have moved from "introduced" to "recognized" over weeks.

**What we track and why.** From a pedagogical standpoint, letter-sound association learning in toddlers involves several observable dimensions: letter recognition, sound-word association, generalization beyond the cards, session frequency, card effectiveness, and vocabulary growth. All of these can be derived from the session log and progress data described above.

**What we don't yet have.** The specific reporting format (charts, summaries, exportable reports) is intentionally left open. This will be designed once enough real session data accumulates to know what's most useful.

## Architecture Decisions

### Two base interfaces: CLI and deck protocol

Deck management is CRUD on structured data files — it doesn't need CLI commands. The CLI handles compute-heavy execution (PDF generation, photo processing, validation). The conversational interface reads and writes deck data directly. This avoids duplicating workflow logic in CLI wrappers that would add complexity without value.

### CLI wizard vs. conversational (Claude-as-interface)

**Decision: Conversational, with CLI as the execution layer.**

A CLI wizard would require building and maintaining interactive prompts, state management, and user flows — all things Claude already does well. The CLI stays as a non-interactive tool that the conversational layer (or a human) invokes.

### Content separation now vs. later

**Decision: Design for separation now, implement incrementally.**

The module structure and deck format described here are the target. Migration can happen gradually — the current `generate.py` doesn't need to be rewritten all at once. The starter deck concept can be introduced by simply reorganizing existing files. The extended CSV format is backward-compatible (new columns can have defaults).

### Private repo vs. local-only deck storage

**Decision: Both supported. Private GitHub repo is strongly recommended.**

The local path works for getting started. But the private repo path is the recommended default because it unlocks the full value of the conversational interface — Claude can access the deck from any device, and deck history is version-controlled. The engine is agnostic: it reads from a deck directory and doesn't care whether it's git-backed. Each deck in `~/.lettercards/` can independently be local or remote.

### Monolith vs. package

**Decision: Split into a Python package with clear modules.**

`generate.py` currently handles CSV parsing, font registration, card layout, color management, and PDF rendering. As bilingual support, double-sided cards, and card grouping land, this will become unwieldy. Splitting into `cards.py`, `generator.py`, `photos.py`, and `pictograms.py` creates natural boundaries for these features without over-engineering.

### Starter deck licensing

All images in the starter deck must have clear licensing that allows free redistribution. The current ChatGPT/DALL-E generated pictograms satisfy this requirement — per OpenAI's terms, generated images are owned by the user who created them and can be freely distributed. Any future image sources must meet the same standard. This should be documented in the repo's LICENSE file.

### Testing strategy

Testing surfaces are defined in ADR-002 and updated to reflect the new architecture. Key additions: module-level unit tests for the `lettercards` package, validation tests for deck integrity checking, and migration tests that verify round-trip compatibility between deck protocol versions.

## Migration Path

This architecture does not require a big-bang rewrite. It can be implemented in phases:

**Phase 1: Deck format and CLI unification.** Extend `cards.csv` to `deck.csv` with status/notes columns (backward-compatible). Add `deck-state.json`. Create a `lettercards` CLI entry point that wraps existing scripts. This is useful immediately and doesn't break anything.

**Phase 2: Content separation.** Move images and example CSV into a `starter/` directory. Add `lettercards deck init` to bootstrap a user deck. Existing users can keep their current setup — the engine falls back to in-repo content if no user deck exists.

**Phase 3: Module split.** Refactor `generate.py` into the `lettercards/` package. This is internal — the CLI interface doesn't change. Do this when a feature (bilingual, double-sided) makes the monolith painful.

**Phase 4: Conversational protocol.** Write the content-mode project knowledge document. Set up a Claude.ai Project (or Desktop project) pointing at the deck data. Test the "bus workflow" — ideation and review on mobile, execution on laptop. Remove legacy scripts once the CLI is verified as a complete replacement.

## Versioning

Both the engine and the deck protocol carry explicit version numbers. Breaking changes without migration paths are not acceptable.

**Engine version.** Standard semver (e.g., `1.0.0`). Tracks the `lettercards` Python package and CLI. Major version bumps may require deck protocol migration.

**Deck protocol version.** Tracked in `deck-state.json` via the `deck_protocol` field (e.g., `"1.0"`). This version defines the expected CSV columns, deck-state.json schema, and directory structure. Rules:

- Minor version bumps (1.0 → 1.1) must be backward-compatible. The engine must be able to read older deck formats without modification.
- Major version bumps (1.x → 2.0) may introduce breaking changes but must ship with a tested migration script (`lettercards deck migrate`). The engine should detect an outdated deck version and offer to run the migration.
- Every release that touches the deck format must include migration tests that verify round-trip compatibility with the previous version.

The engine validates the deck protocol version on startup and refuses to operate on an incompatible deck with a clear error message explaining how to migrate.

## Related Issues

- #29 — Unified entry point with guided workflows
- #30 — Separate core program from content
- #60 — Bilingual Dutch/Spanish word support
- #61 — Double-sided laminated card format
- #62 — Card grouping mechanic
- #26 — Run Claude Code in container for safety
- #24 — Improving code without laptop

## Open Questions

1. **Bilingual workflow.** The architecture supports bilingual decks through the `language` column in the CSV and the conversational protocol. However, the specifics of how bilingual review sessions work (mixed-language cards in one session? separate sessions per language?) need to be tested and iterated on during implementation.

2. **Progress reporting format.** The data model for learning progress is defined, but the visualization and reporting layer is not. This needs design work once real session data accumulates — see the Learning Progress Tracking section above.

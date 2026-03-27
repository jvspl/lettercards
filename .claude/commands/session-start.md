# /session-start — Orient at the start of a work session

Get a quick picture of where things stand and what to work on next.

## Steps

Run these in sequence to build a complete picture:

1. Check git state:
   ```bash
   git status
   git branch
   git log --oneline -5
   ```

2. Fetch open PRs and issues in bulk:
   ```bash
   gh pr list --state open --json number,title,labels,isDraft
   gh issue list --state open --json number,title,labels --limit 30
   ```

## What to report

**In-flight work** — list open PRs with their status (draft, review requested, etc.). Note any that need attention (no activity in 3+ days, failing checks).

**Current branch** — if not on master, note which branch and what issue it relates to.

**Backlog snapshot** — top 3–5 issues by priority:
- Any `priority:high` issues not yet in a PR
- Phase 1 issues (#100 deck.csv, #101 deck-state.json, #102 CLI) if not done
- Any `ready-to-close` issues that need Jeroen's sign-off

**Suggested next steps** — 2–3 concrete options for what to work on this session, based on:
- What's in flight (finish before starting new work)
- Architecture phase ordering (Phase 1 before Phase 2, etc.)
- Any issues Jeroen mentioned at the start of the session

## Tone

Keep it brief — this is orientation, not a full backlog review. For deeper grooming, use `/backlog`.

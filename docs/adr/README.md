# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for the lettercards project.

An ADR captures a single significant architectural or process decision: what was decided, why,
what alternatives were rejected, and what the consequences are. It is a log, not a living document.

## What belongs here

An ADR is warranted when a decision:
- Is hard to reverse (or costly to reverse later)
- Has meaningful tradeoffs between options
- Affects how future work should be done
- Would be confusing to a future contributor without context

Not everything needs an ADR. "Use reportlab for PDF generation" does not need one if there
was no real alternative considered. "Use subagents vs agent teams for persona orchestration"
does, because both were viable and the choice shapes future work.

## How to read an ADR

Each ADR has:
- **Status** — the current state of the decision (see lifecycle below)
- **Context** — what problem or pressure forced this decision
- **Decision** — what was decided, stated plainly
- **Consequences** — what this makes easier, harder, or impossible; positive and negative
- **Alternatives considered** — what else was evaluated and why it was rejected

The context and consequences sections matter most. The decision itself is usually one sentence.

## Status lifecycle

```
Proposed → Accepted → Deprecated
                    ↘ Superseded by ADR-XXX
```

- **Proposed**: under discussion, not yet in effect
- **Accepted**: the decision is in effect
- **Deprecated**: the decision is no longer relevant (e.g. the feature it governed was removed)
- **Superseded by ADR-XXX**: a newer ADR replaces this one; see that ADR for the current decision

## How to create a new ADR

1. Copy `template.md` to `NNN-short-title.md` (e.g. `002-font-loading-strategy.md`)
2. Number sequentially — never reuse or reorder numbers
3. Fill in the frontmatter and sections
4. Set status to `Proposed`
5. Open a PR; status becomes `Accepted` on merge

## How to supersede an ADR

When a decision changes:

1. Write a new ADR explaining the new decision and why the old one no longer holds
2. In the new ADR, note "Supersedes ADR-XXX" in the context
3. In the old ADR, change status to `Superseded by ADR-YYY` and add a one-line note at the top

Do not edit the body of the old ADR. The old reasoning should remain readable as history.

## Rules

- **One decision per ADR** — don't bundle unrelated choices
- **Write it when you make the decision** — context fades quickly
- **ADRs are immutable once accepted** — supersede, don't edit
- **Never delete** — superseded ADRs are historical record, not clutter
- **Be honest about consequences** — list negatives too; an ADR with only upsides is a sales pitch

## Index

| ADR | Title | Status |
|-----|-------|--------|
| [001](001-persona-orchestration.md) | Persona orchestration via Claude Code subagents | Accepted |
| [002](002-testing-strategy.md) | Three-tier testing strategy (pytest + hook pipe-tests + manual + CI) | Proposed |

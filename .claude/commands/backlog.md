---
description: Groom the GitHub issue backlog — find what's done but not closed, what's blocked, what needs refinement, and what to work on next. Use this when the user asks what to work on, says "what should we tackle", "I have two hours what's most valuable", "let's figure out what's next", wants to clean up after a batch of work, or needs to prioritise. Accepts an optional focus area: /backlog security, /backlog phase-1.
---

# Backlog Grooming

A healthy backlog has one property: you can look at it and immediately know what to do next. Your job is to get it there.

## Understand the project direction first

Before touching the issue list, understand where the project is heading. Look for architecture, roadmap, or planning documents in `docs/`, and check `CLAUDE.md` for phase structure and priorities. This is your priority lens — an issue that *unblocks* Phase 2 work is more important than one that *is* Phase 2 work. Skip this and your recommendations will be blind.

## Fetch the data

Everything in one pass — never loop over individual issues:

```bash
gh issue list --state open --json number,title,body,labels,comments --limit 100
gh issue list --state closed --json number,title,labels,closedAt --limit 20
gh pr list --state open --json number,title,body,labels,comments,isDraft
```

## Focus filter

If `$ARGUMENTS` is set (e.g. `/backlog security` or `/backlog phase-1`), filter the entire analysis through that lens — issues, gaps, recommendations, everything. Omit sections that have no relevant content in the focused view.

## What to look for

**Done but still open.** Cross-reference recent closed PRs against open issues. If work shipped that resolves an issue, flag it for closure — post a comment explaining what shipped and wait for the project lead's sign-off. Never close issues yourself.

**Blocked — but distinguish the type, because they need different responses:**
- *Needs a decision from the project lead* — frame the specific question in a comment and wait. The blocker is a choice only the project lead can make.
- *Needs design discussion* — note what needs to be resolved and what the options are. This isn't a quick answer; it's a conversation.
- *Externally blocked* — waiting on something outside the project. Note what it is and whether there's a path forward without it.

**Stale.** Issues untouched for months that no longer reflect the project's direction. These should be explicitly surfaced — sometimes the right call is to close them outright rather than carry dead weight indefinitely.

**Scope creep in flight.** Open PRs that have grown beyond their linked issue. Post a comment identifying the out-of-scope changes and suggest they move to a new issue. Bloated PRs are a review and merge risk.

**Gaps.** Based on the architecture/roadmap, are there phases, features, or deliverables with no issue? Name the gap — a backlog that looks complete but isn't is worse than one that honestly shows what's missing.

## Priority framework

When ranking what to work on next:

1. **Security issues** — jump the queue regardless of anything else
2. **Blocking work** — issues other issues depend on
3. **Explicitly prioritised** — `priority:high` label; reflects a conscious human call that overrides algorithmic ordering
4. **Quick wins** — small scope, high signal, resolves something real (`quick-win` label or evident from the body)
5. **Phase order** — earlier phase before later phase; within a phase, dependencies before dependents

## Refine issues before recommending them

A ready issue has a clear problem statement, acceptance criteria that define done, and no unanswered questions that would block implementation. Before putting an issue in the recommended list, check it passes this bar.

**If you can improve it yourself** (filling in missing acceptance criteria, making implicit scope explicit based on available context): post a comment using this exact template, then wait for confirmation before editing the issue body:

```
💡 **Suggested refinement** — please confirm or adjust before I update the issue.

[proposed revised description]

— 🤖 Claude
```

**If it needs a decision from the project lead** (design tradeoffs, scope choices, architecture calls): post a comment framing the specific question. Don't make those decisions yourself.

After grooming, update labels to reflect current state — remove `needs-input` once a question is answered, add `quick-win` if scope turns out to be small, update `discussion` to `needs-input` once the design question is clear enough to become a decision. Labels are only useful if they stay accurate.

## Session-fit signal

For each item in the recommended list, add a rough signal based on scope:
- **One session** — clear scope, completable in a focused sitting
- **Multi-session** — larger work; consider whether it should be split before starting

This isn't a time estimate. It's a judgment call that helps the project lead decide what to start when.

## Output

Only include sections that have content — an empty section is noise. Lead with state, end with recommendations and gaps.

**State:** one sentence — open issues, in-flight PRs, current project phase.

Then only what applies:
- **Ready to close** — each with a one-line reason; post a comment on each before listing here
- **Blocked** — each with its type and the specific question or blocker
- **Stale** — issues that should be closed or updated, with a brief reason
- **Scope creep** — PRs with out-of-scope changes; post a comment identifying them
- **Recommended next** — 2–3 items in priority order, each with: why it's next, one-session or multi-session signal, confirmation it's ready to pick up now
- **Gaps** — work that should exist but doesn't, referenced against the architecture/roadmap

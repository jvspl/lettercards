---
description: Orient at the start of a work session — check what's in flight, where things stand, and what to focus on. Use when starting a new session, resuming after a break, or when context needs refreshing. For deeper backlog grooming, use /backlog instead.
---

# Session Start

Get oriented fast. The goal is to know — within 60 seconds — what's in flight and what to do next.

## Check the local and remote state

```bash
git status
git log --oneline -5
gh pr list --state open --json number,title,labels,isDraft
gh issue list --state open --json number,title,labels --limit 30
```

## What to surface

**What's already in motion.** If there are open PRs, those are the highest priority — finish before starting. If you're on a non-default branch, that work is in progress and needs to land first. Don't start new work while old work is unmerged.

**What needs attention right now.** Open PRs with no recent activity, failing checks, or review comments that haven't been addressed. Name them specifically.

**What to do next.** Pick 2–3 concrete options from the backlog. Prefer:
- Work that unblocks other work (foundational > dependent)
- Work that matches the project's current phase (don't skip ahead)
- Work that can realistically finish in a session

## Output

Keep it short. This is orientation, not a full report. Three sections:

1. **In flight** (PRs + current branch): what's already started
2. **Needs attention**: anything stalled or requiring action
3. **Suggested next**: 2–3 options with a one-line reason each

If everything is clean and there's nothing in flight, just say so and go straight to the suggestions.

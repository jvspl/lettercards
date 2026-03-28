---
description: Answer "where was I and what do I do next?" — triage git state, open branches, and in-flight PRs. Use when the user says "where was I", "catch me up", "what should I work on", "getting started", or is resuming after a break. This skill handles triage decisions; the session-start hook handles passive awareness. Both serve different purposes and should both run.
---

# Session Start

The session-start hook already ran when this session opened — it told you what's happening on GitHub (open PRs, recent issue activity, external comment warnings). That's awareness. This skill's job is different: it turns awareness into a triage decision by adding git state and answering "what's the next concrete action?"

## Fetch what the hook doesn't have

```bash
git status
git branch -vv
gh pr list --state open --json number,title,labels,isDraft,updatedAt,comments
```

`git branch -vv` is the most information-dense git command for orientation — it shows every local branch, its upstream, and whether it's ahead or behind in one line. Always run it.

The `gh pr list` here fetches richer data than the hook (labels, isDraft, comments) — that's intentional.

## Triage in priority order

**1. Uncommitted changes** — surface these first, always. If `git status` shows modified or staged files, name them. Do they belong to the current branch's work, or are they from something else? This is the most urgent signal because it means there's work that exists nowhere except your local machine.

**2. Unpushed commits or open branches** — `git branch -vv` shows branches ahead of their upstream. An open branch with no PR is invisible to everyone else. Either it needs a PR or it should be abandoned. Name each one.

**3. Open PRs** — if there are open PRs, finishing them comes before starting anything new. For each PR, give one concrete next action and what it's about: "PR #108 (skills + CLAUDE.md refactor) has unaddressed review comments" tells you what to do; "PR #108 is open" doesn't.

## Three situations, three responses

**In-flight work exists** (any of the above):
State exactly what needs to happen for each item. One action per item. Stop there — don't pad with backlog suggestions when there's already work to finish.

**Clean state, nothing in flight:**
This is a prioritisation question, not an orientation one. Don't guess. Say the slate is clean and suggest running `/backlog` for a proper analysis.

**Mid-session check** (rich conversation context already exists):
Read the room — summarise where the session has got to and what remains, rather than re-running commands unnecessarily.

## Output

Short. No empty sections. Most urgent thing first.


---
description: Review a pull request — check scope, correctness, test coverage, documentation, and safety before merging. Use when asked to review a PR, check if something is ready to merge, or apply a pre-merge review. Optionally pass a PR number: /pr-review 42
---

# PR Review

The goal of a review is to answer one question: **is merging this PR safe and does it do what it claims?**

A good review has a clear verdict. Don't leave the author guessing.

## Fetch the PR

```bash
gh pr view $ARGUMENTS --comments   # or list open PRs if no number given
gh pr diff $ARGUMENTS
```

Read the linked issue if there is one — you need to know what the PR was supposed to do to judge whether it did it.

## Four things to check

**1. Scope.** Does the PR do what the linked issue asked, and only that? Extra changes — even good ones — belong in separate PRs. They make reviews harder, obscure intent, and create merge risk. If the PR has scope creep, name it specifically.

**2. Verifiability.** Can someone else reproduce the expected outcome from what's written in the PR description? A "How to Verify" section with runnable steps is the bar. If the change is visual, before/after evidence belongs here too.

**3. Safety.** Ask: could this PR expose private data, weaken security boundaries, or break something that's currently working?
- Changes to settings files, hooks, or permissions need extra scrutiny — apply the security checklist in CLAUDE.md
- Changes involving personal data paths (photos, private files) should never move that data into version control
- Test the blast radius: what breaks if this is wrong?

**4. Completeness.** Does the code that changed have tests for the new logic? Is the documentation updated to match? Is the commit message accurate?

## Verdict

Choose one and state it clearly:

- **Approve** — safe to merge as-is
- **Request changes** — specific things must change before merging (list them)
- **Needs discussion** — something is ambiguous or out of scope that the author should clarify

If requesting changes, post a comment on the PR naming each required change. Sign with `— 🤖 Claude`.

Don't approve if you have doubts you haven't surfaced. It's better to request changes than to let something questionable slip through quietly.

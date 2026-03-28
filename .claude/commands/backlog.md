---
description: Groom the GitHub issue backlog. Use this when the user asks what to work on next, wants to review or clean up the backlog, asks about project state, or needs help prioritizing. Also useful after a batch of work to close out completed issues.
---

# Backlog Grooming

A healthy backlog has one property: you can look at it and immediately know what to do next. Your job is to get it there.

## Gather the data

Fetch everything in one pass — never loop over individual issues:

```bash
gh issue list --state open --json number,title,body,labels,comments --limit 100
gh issue list --state closed --json number,title,labels,closedAt --limit 20
gh pr list --state open --json number,title,body,labels,comments
```

Read `docs/architecture.md` to understand the project's intended direction and phases. This is the lens through which you judge priority — an issue that blocks Phase 2 work matters more than one that is Phase 2 work.

## What to look for

**Done but still open.** Recent merged PRs often resolve issues that are still listed as open. Cross-reference the PR list against open issues — if the work shipped, the issue should close. Post a comment explaining what shipped and flag it for the owner's sign-off. Never close issues yourself.

**Blocked or stale.** Issues marked `needs-input` or `discussion` are not actionable without a decision. Surface them explicitly: what is the open question? Who needs to answer it? Sometimes the right action is to close them rather than let them accumulate.

**Missing work.** Read the architecture doc and ask: is there work that clearly needs to happen that has no issue? If so, say so — it's better to name the gap than to pretend the backlog is complete.

**Scope creep in flight.** Open PRs that have grown beyond their linked issue slow everything down. Flag them.

## Refine issues before recommending them

Before suggesting an issue as "next up", check whether it's actually ready to pick up. A ready issue has: a clear problem statement, acceptance criteria that tell you when it's done, and no unanswered questions that would block implementation. If an issue is missing any of these, refine it first:

- Post a comment on the issue with the improved body (sign with `— 🤖 Claude`)
- For vague or ambiguous issues, post a comment asking the project lead the specific question that needs answering before work can start
- For issues that need a decision from the project lead (design tradeoffs, scope questions, prioritisation calls), post a comment framing the question clearly — don't make those decisions yourself

The goal: every issue in the "recommended next" list should be ready to pick up immediately, with no open questions.

## Suggest the next 2–3 things to work on

A good recommendation has three properties:
1. It has a clear definition of done (you know when it's finished)
2. It unblocks other work (prefer dependencies over dependents)
3. It matches the current project phase (don't skip ahead)

Explain *why* each item is the right next thing, not just that it's high priority.

## Output structure

1. **State in one sentence**: open issues, in-flight PRs, current phase
2. **Ready to close**: each with a one-line reason
3. **Blocked / needs decision**: each with the specific open question (post a comment on the issue)
4. **Refined this session**: issues you improved or asked a question on
5. **Recommended next**: 2–3 items in order, with reasoning — these should be ready to pick up now
6. **Gaps**: work that should exist but doesn't

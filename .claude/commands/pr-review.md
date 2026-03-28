---
description: Review a pull request before merging — check code correctness, edge cases, test coverage, scope, safety, and verifiability. Use when asked to review a PR, check if something is ready to merge, "can we ship this", "is this good to merge", "pre-merge check", or any request to evaluate a PR. Optionally pass a PR number: /pr-review 42
---

# PR Review

The purpose of a review is to give the project lead enough information to merge with confidence. Lead with the verdict — don't bury it at the end.

Almost all code in this project is AI-generated. That means it will look plausible and well-structured. Apply specific skepticism to whether the implementation is *actually correct*, not just whether it looks correct. AI-generated code has a characteristic failure mode: coherent output that subtly doesn't do what was intended.

## Gather context

If `$ARGUMENTS` is a PR number, use it. Otherwise list open PRs and ask — or auto-select if only one is open.

```bash
gh pr view $ARGUMENTS --json number,title,body,labels,isDraft,comments,files
gh pr diff $ARGUMENTS
gh pr checks $ARGUMENTS
```

Read the linked issue if there is one — the issue defines what was supposed to change; the PR should be judged against that, not just against itself.

## Pre-flight

Check these before reading a single line of diff. Any failure here changes what you do next.

**Draft?** Don't review unless explicitly asked. Draft means not ready.

**Too large?** If the diff touches more than ~15 files or spans clearly unrelated concerns, flag it and stop. A PR too large to review coherently should be split, not half-reviewed. Name the distinct concerns and suggest how to divide them.

**CI failing?** If `gh pr checks` shows failures, say so and stop. No point reviewing code that already fails — the author needs to fix CI first.

## Understand the intent

Before looking at the code, establish what was supposed to happen:
1. What does the linked issue say should change?
2. What does the PR description say it does?

A mismatch between these is itself a finding — either the description is wrong or the scope drifted during implementation.

## Code review

Read the diff, then read the changed files for context. The diff shows *what* changed; the file shows *why it matters*. For each meaningful change:

**Correctness.** Does the implementation actually do what it claims? Walk through the logic — don't assume correctness because the code looks plausible. Pay close attention to: conditional branches, loop boundaries, return values, state mutations, and anything that touches data the user cares about.

**Edge cases.** What inputs, states, or call sequences does this code not handle? Empty inputs, missing files, unexpected types, large data. Not every edge case needs handling — but unhandled ones should be conscious choices, not oversights.

**Simplicity.** Is there a meaningfully simpler way to achieve the same outcome? Not a style preference — a real reduction in complexity that makes the code easier to understand and less likely to break.

**Consistency.** Does this match the patterns and conventions of the surrounding code? Inconsistency creates maintenance drag.

## Test review

Don't just check whether tests exist — check whether they verify the right things.

- Which behaviors in the changed code are covered?
- Which changed behaviors have *no* test? Name them specifically.
- Do the tests exercise the actual changed code paths, or something adjacent that happens to pass?
- If a test failed, would it clearly tell you what broke?

A passing test suite that doesn't cover the changed logic is a false sense of safety.

## Process checks

- **Scope** — does the PR do what the linked issue asked, and only that? Extra changes, even good ones, belong in a separate PR. Name any out-of-scope items.
- **Commit history** — are there "wip", "fix", "oops" commits landing on master? Not always a blocker, but worth noting.
- **Documentation** — if behavior changed, is documentation updated to match?
- **Verifiability** — can the project lead reproduce the expected outcome from the PR description? A concrete "How to Verify" section is the bar. Visual changes require before/after evidence.

## Security

These apply to every diff — not just PRs that look security-related:

- **Injection** — user-controlled input passed to shell commands (`subprocess`, `os.system`), SQL queries, template renderers, or `eval`/`exec`? Even indirect paths count: input → stored → later executed.
- **Path traversal** — file paths built from user input? Validate and normalize. `../` sequences can escape intended directories.
- **Hardcoded secrets** — new string literals that look like API keys, tokens, or passwords; new config files; environment variable handling.
- **Input validation** — at system entry points (user input, file contents, external API responses), is external data checked before use?
- **Information leakage** — do error messages, logs, or API responses expose internal paths, stack traces, or data the caller shouldn't see?
- **New dependencies** — each new package is a trust decision. Is it widely used, actively maintained, and actually necessary?
- **Blast radius** — if this change is wrong, what breaks? Loud failures (exceptions) are better than silent wrong output.

When the diff touches settings, hooks, permissions, or personal data paths, also check:

- **No personal data in version control** — photos or private files from `~/.lettercards/` must never appear in a commit
- **No `bypassPermissions`** — if introduced anywhere, flag immediately and block
- **Permissions as narrow as possible** — a new permission should do exactly what's needed, nothing broader

## Label every finding

Make it clear what's blocking and what isn't:

- 🔴 **Must fix** — blocker; won't approve until resolved
- 🟡 **Should fix** — worth addressing, but won't block merge
- 💡 **Nit** — optional, mentioned for future reference

## Verdict

State this at the top, before the findings:

- ✅ **Approve** — safe to merge as-is
- ✅ **Approve with comments** — merge-ready, but with observations the author should see
- 🔄 **Request changes** — one or more must-fix blockers; list them and post a comment on the PR signed `— 🤖 Claude`
- ❓ **Needs discussion** — scope or design question needs resolution before review can complete
- 📦 **Too large** — name the distinct concerns; suggest how to split

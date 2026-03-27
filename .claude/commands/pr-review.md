# /pr-review — Review a pull request before merging

Apply the full PR review checklist. Pass an optional PR number: `/pr-review 107`

## Steps

1. Identify the PR to review:
   - If `$ARGUMENTS` is a number, review that PR
   - Otherwise, list open PRs and ask which to review (or review all if only one is open)

2. Fetch the PR with comments:
   ```bash
   gh pr view $PR_NUMBER --comments
   ```

3. Read the changed files:
   ```bash
   gh pr diff $PR_NUMBER
   ```

## Checklist (Tester persona)

Work through each item and report pass / fail / not-applicable:

- [ ] **How to Verify** — does the PR have a concrete "How to Verify" section with runnable steps?
- [ ] **Visual changes** — if card layout, colors, or fonts changed: are before/after screenshots included?
- [ ] **Safe screenshots** — were personal card letters excluded? Should use `--safe-letters-only` or `--letters d,e,w`
- [ ] **Scope** — does the PR do what the linked issue asked, and nothing more?
- [ ] **Commit message** — accurate, references the issue number, doesn't use `--amend` on published commits?
- [ ] **Tests** — does the PR include or update tests for new logic? Run `venv/bin/pytest tests/` mentally against the diff.
- [ ] **CLAUDE.md / docs** — if behavior changed, is documentation updated?

## Security lens

- Does the change touch `.claude/settings.json`, `.claude/hooks/`, or permission-related code?
  - If yes: apply the security checklist from CLAUDE.md (necessity, scope, bypassPermissions check, data exposure)
- Does the change affect personal photo handling or `~/.lettercards/` paths?
- Does the change commit or expose any personal images?

## Designer lens (visual changes only)

- Does the card layout still fit 9 per A4?
- Are colors consistent with the `LETTER_COLORS` palette?
- Is the first letter visually distinct from the rest of the word?

## Verdict

End with one of:
- **Approve** — all checklist items pass
- **Request changes** — list specific items that need fixing
- **Needs discussion** — something is unclear or out of scope

If requesting changes: post a comment on the PR explaining what needs to change (sign with `— 🤖 Claude`).

# /backlog — Groom the issue backlog

Review the current state of the GitHub backlog and suggest what to work on next.

## Steps

1. Fetch all open issues with full details in one call:
   ```bash
   gh issue list --state open --json number,title,body,labels,comments --limit 100
   ```

2. Fetch recent closed issues (last 2 weeks) to catch anything that should be marked done:
   ```bash
   gh issue list --state closed --json number,title,labels,closedAt --limit 20
   ```

3. Fetch open PRs:
   ```bash
   gh pr list --state open --json number,title,body,labels,comments
   ```

## What to report

**Ready to close** — issues with `ready-to-close` label, or whose linked work has shipped. Post a comment explaining why they can be closed, then flag them to Jeroen for approval. Never use `gh issue close` directly.

**Stale or blocked** — issues with `needs-input` label that haven't had activity. Flag them and ask if they're still relevant.

**Missing issues** — based on the architecture in `docs/architecture.md`, identify work that should be on the backlog but isn't. Reference the four phases (Phase 1a/1b/1c → Phase 2 → Phase 3 → Phase 4).

**Priority suggestion** — based on the architecture phases and existing labels, suggest the 2–3 highest-value issues to work on next. Consider:
- Phase 1 (deck.csv + deck-state.json + CLI) is the foundation — it unblocks everything else
- `priority:high` label overrides phase ordering
- Security issues take precedence over features

**State summary** — end with a one-paragraph overview: how many issues are open, how many PRs are in flight, what phase the project is currently in.

## Conventions

- Post a comment on issues you're flagging for closure (sign with `— 🤖 Claude`)
- Never close issues yourself — flag them to Jeroen
- Reference the architecture phases from `docs/architecture.md` when suggesting priorities

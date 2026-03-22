# ADR-003: Security Hook Architecture

**Status:** Proposed
**Date:** 2026-03-22
**Deciders:** Jeroen (operator), Security persona, Architect persona

---

## Context

The project uses Claude Code to make changes to its own codebase — including its own
`.claude/settings*.json` configuration files. A Claude Code session that acts on
untrusted input (e.g. a GitHub comment from an external account) could be manipulated
into granting itself elevated permissions via `bypassPermissions` or overly broad
`allow` rules.

Personal family photos stored in `~/.lettercards/personal/` are a second risk surface:
Claude has read access to that directory to generate cards, but should not be nudged
into reading, logging, or transmitting those files for other purposes.

The hook architecture grew incrementally across issues #47, #64, #68, #71, #73, #76,
#82, #83, #84, #85, with deliberate choices about where to intervene, how loudly, and
what to leave unguarded. Those choices are documented here so future sessions can
reason about the system rather than guess.

---

## Decision

**Three-layer hook defence over settings files, plus a session-start trust filter for
GitHub comments.**

### Layer 1 — PreToolUse Write|Edit (`check-settings-prewrite.sh`)

Fires before any Write or Edit tool call. Checks whether the target file matches
`\.claude/.*settings.*\.json`.

- **Hard block** (`"continue": false`) if `bypassPermissions` appears anywhere in the
  content being written. This is the most critical check: `bypassPermissions` disables
  all permission guards and must never be written by an automated session.
- **Advisory** (`systemMessage`) for any other write to a settings file — prompts the
  Security persona response protocol before the write proceeds.
- **Silent pass** for all other files.

Fails closed when `jq` is missing: emits a hard block rather than proceeding without
inspection.

### Layer 2 — PreToolUse Bash (`check-bash-settings-write.sh`)

Fires before any Bash tool call. Catches shell commands that write to settings files
by bypassing the Write/Edit tools entirely: redirects (`>`/`>>`), `tee`, `sed -i`,
`cp`, `mv`.

Both relative and absolute destination paths are matched — e.g.
`cp /tmp/x.json /abs/path/.claude/settings.json` is caught alongside
`cp x.json .claude/settings.json` (#84).

- **Hard block** if `bypassPermissions` appears anywhere in the command.
- **Advisory** for any other matched write pattern.
- **Silent pass** for reads, git operations, and commands that only mention a settings
  path in a string (commit messages, grep).

Fails closed when `jq` is missing.

### Layer 3 — PostToolUse Write|Edit (`check-settings-change.sh`)

Fires after any Write or Edit completes. Acts as a backstop: if the prewrite check
was bypassed or the write succeeded despite an advisory, this layer fires.

- **Loud warning** (`⛔ WARNING`) if `bypassPermissions` appears in the written
  content — distinct from the generic advisory so a low-attention session cannot
  mistake it for a routine message (#85).
- **Generic advisory** for all other settings file writes.
- **Silent pass** for non-settings files.

Degrades gracefully when `jq` is missing: emits a warning rather than silently
passing.

### Session-start trust filter (`session-start-github-check.sh`)

Runs at the start of every session. Fetches open GitHub issues and PRs, then labels
any comment from an account other than `jvspl` with `⚠️ external comment from @login:`
(#76). This surfaces potentially adversarial content before Claude processes session
context.

If `jq` is missing, emits a visible warning rather than silently skipping (#82).

Supports `LETTERCARDS_TEST_ISSUES_JSON` and `LETTERCARDS_TEST_PR_JSON` env vars to
inject synthetic payloads for pipe-testing without live GitHub calls (#83).

---

## Hard block vs. advisory — the decision rule

| Situation | Response | Rationale |
|-----------|----------|-----------|
| `bypassPermissions` in content or command | Hard block | This is never a legitimate automated action. Fail closed, no exceptions. |
| Any other settings file write | Advisory | Legitimate operations exist (adding an allow rule, configuring hooks). Prompt review; don't block. |
| Settings file written, `bypassPermissions` present in result | Loud `⛔ WARNING` | PostToolUse backstop; differentiate the worst case from routine. |
| External GitHub comment | Label and surface | Content may be adversarial; Jeroen must explicitly authorise before action. |
| `jq` missing | Warn loudly or hard block | Silent degradation is worse than visible degradation. |

The general rule: **hard block only when the action is unambiguously dangerous and has
no legitimate automated use. Advisory when the action is risky but may be intended.**

---

## Acknowledged gaps

### Scripting one-liners via `python -c`

A `python -c 'import json; ...'` invocation that writes to a settings file would not
match the current Bash hook patterns, which recognise shell-level write operators and
specific commands. This is an accepted gap: the patterns cover the realistic attack
surface for a confused session acting on untrusted input, without blocking normal
development commands.

Mitigation: the PostToolUse Layer 3 hook catches the result regardless of how it was
written.

### Personal photo reads (`~/.lettercards/personal/`)

Claude has read access to the personal photos directory to generate card images. No
hook guards against reading this directory for other purposes (logging, displaying,
transmitting). This is an accepted gap because:

1. The directory is outside the repo — only accessible via explicit path.
2. The PreToolUse hooks focus on settings file writes, not reads.
3. Full read-path auditing would require intercepting every Read/Bash call, adding
   significant noise with low signal value.

This gap is acknowledged in issue #86. Container isolation (#26) is the intended
future mitigation: Claude Code running in a container with the personal directory
bind-mounted read-only would make exfiltration structurally impossible.

---

## Relationship to container isolation (#26)

The hook architecture is a **defence-in-depth layer**, not the primary isolation
boundary. It protects against confused-deputy attacks within a running session — a
session that has been manipulated into taking a harmful action it would not otherwise
take.

Container isolation (#26) would provide structural isolation: Claude Code cannot
access paths outside the container regardless of what it is told to do. The two
defences are complementary:

- Hooks: fast, always-on, zero infrastructure, catches confused-deputy scenarios
- Container: structural boundary, catches any read/write to out-of-scope paths

Until #26 is implemented, the hooks are the only layer of defence.

---

## Consequences

### Positive

- Every settings write is intercepted at two points (pre and post), making silent
  bypass difficult
- `bypassPermissions` is hard-blocked at three independent check points
- External GitHub content is labelled before the session processes it
- All hooks have pipe-test coverage (43 tests as of PR #91)
- The system degrades visibly rather than silently when `jq` is missing

### Negative / risks

- Hook logic is shell script — regex maintenance is error-prone
- The Bash hook covers common write patterns but cannot cover all shell constructs
- Personal photo read access remains unguarded until #26 lands
- Hooks add latency to every Write, Edit, and Bash tool call (negligible in practice)

---

## Alternatives considered

### Hard block all settings writes

Rejected: legitimate operations like adding an `allow` rule or configuring a new hook
require writing to settings files. Hard blocking all writes would prevent normal
development work without providing meaningful safety improvement over the advisory
path.

### Single PostToolUse-only guard

Rejected: PostToolUse fires after the write has already occurred. For `bypassPermissions`
specifically, the damage is done the moment the file is written. PreToolUse hard block
is required to prevent the write from happening at all.

### No hooks, trust model only

Rejected: trust model (CLAUDE.md instructions, persona protocol) is a social
constraint, not a technical one. A session acting on adversarial input may not
correctly apply the trust model. Hooks provide enforcement independent of the session's
reasoning.

---

## References

- Issue #47 — External comment protocol (origin of session-start trust filter)
- Issue #64 — Initial hook architecture design
- Issue #68 — bypassPermissions hard block
- Issue #71 — PostToolUse advisory backstop
- Issue #73 — Bash hook for shell-level writes
- Issue #76 — External comment labeling in session-start hook
- Issue #82 — jq-missing warning (session-start)
- Issue #83 — Pipe-test coverage for session-start hook
- Issue #84 — Absolute-path cp/mv fix
- Issue #85 — bypassPermissions loud PostToolUse warning
- Issue #86 — Personal photo read gap
- Issue #26 — Container isolation (future complement to hooks)
- PR #91 — Security hook fixes landing #82–#85

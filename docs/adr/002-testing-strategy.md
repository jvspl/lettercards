# ADR-002: Three-Tier Testing Strategy

**Status:** Proposed
**Date:** 2026-03-21
**Deciders:** Jeroen (operator), Architect persona

---

## Context

The lettercards codebase started as a small personal script with no automated tests.
Two forces pushed toward adding tests:

1. **Security hooks** were added to `.claude/hooks/` to protect personal photos and
   prevent accidental settings file exposure. These run as shell scripts invoked by
   Claude Code on every tool call. Getting the hook logic wrong silently is a real
   risk — wrong regex lets dangerous operations through; overly broad patterns block
   legitimate work.

2. **Growing core logic** in `generate.py` and `process_photo.py` — CSV parsing,
   personal-dir lookup, safe-letters filtering, square-crop geometry — was being
   modified regularly across PRs. Regressions were caught during PDF review, not at
   code time.

The question was: what kind of automated testing is appropriate for a personal toddler
card project maintained primarily through Claude Code sessions?

---

## Decision

**Use a three-tier testing approach with CI enforcement on PRs:**

1. **Pytest unit tests** (`tests/test_generate.py`, `tests/test_process_photo.py`) —
   test pure logic: CSV parsing, personal-dir resolution, safe-letters filtering,
   image path lookup, crop geometry. Run with `venv/bin/pytest tests/`.

2. **Shell pipe-tests** (`tests/test_hooks.sh`) — test security hook behaviour by
   piping synthetic JSON payloads through the hook scripts and asserting on stdout.
   Run with `bash tests/test_hooks.sh`.

3. **Manual visual review** — card layout, spacing, colors, and font variety are
   verified by generating the PDF and opening it. This tier is never automated.

**GitHub Actions CI** (`.github/workflows/tests.yml`) runs tiers 1 and 2 automatically
on every push and PR to master. Ubuntu runner, Python 3.11, `jq` installed for the
hook tests.

---

## Rationale

### Why pytest for logic tests?

Pytest is the standard Python testing tool, readable, and low-boilerplate. The
alternative (unittest) offers no advantage. The functions being tested (`load_cards`,
`get_safe_letters`, `process_image`, etc.) are pure logic with no external dependencies
— they are the ideal pytest target.

### Why shell scripts for hook tests?

Claude Code hooks are shell scripts that receive JSON on stdin and emit JSON to stdout.
The most direct way to test them is to pipe representative JSON payloads through them
in a shell — this matches exactly how Claude Code invokes them. Testing via pytest
subprocess calls would add a Python indirection layer for no benefit, and would test
the test harness as much as the hooks. Shell scripts also serve as documentation: each
test case is a concrete example of what the hook accepts or rejects.

### Why is visual review kept manual?

The output is a PDF rendered by reportlab + Pillow. Automated visual regression would
require either a rendered PDF-to-image pipeline or committed reference screenshots that
go stale with every intended visual change. For a project where visual changes are
intentional and frequent, this creates more friction than it prevents. Manual review
takes under a minute and catches real issues.

### Why GitHub Actions?

Single-operator project means "run tests before PR" is a convention that can be
forgotten. Adding a CI gate converts the convention into enforcement without requiring
any local developer setup change. The test suite runs in under 5 seconds total, so CI
adds minimal latency. `jq` is available on ubuntu-latest runners and the hooks are
portable bash, so no platform-specific concerns arise.

---

## Consequences

### Positive

- **Security hooks are verifiable**: hook behaviour is confirmed before merge without
  triggering live Claude Code sessions
- **Logic regressions caught early**: CSV and crop bugs surface at PR time, not when
  Jeroen opens the PDF
- **CI enforces the convention**: the "run tests before PR" rule is automated, not just
  documented
- **Tests as documentation**: the shell pipe-tests are concrete examples of the hook
  contract; the pytest files document expected function signatures

### Negative / risks

- **Manual visual tier is subjective**: spacing and color regressions can be missed
- **Shell tests are fragile to hook renames**: if a hook file moves, the shell test
  breaks silently unless the path is updated
- **No cross-platform coverage**: tests run on macOS locally and ubuntu-latest in CI;
  Pillow rendering differences are not tested
- **jq is a hard CI dependency**: if `jq` is unavailable in a CI runner, the hook
  tests cannot run (mitigated by the `apt-get install jq` step in the workflow)

### What this means for PRs

- Any PR touching `generate.py`, `process_photo.py`, or `.claude/hooks/` must pass
  the CI check before merge
- Visual changes require a before/after PDF screenshot, generated with `--safe-letters-only`
- New test files follow the tier structure: pytest for Python logic, shell for hook
  behaviour; do not test PDF visual output in code

---

## Alternatives considered

### Option A: pytest for everything (including hooks via subprocess)

Use `subprocess.run` in pytest to invoke hook scripts. Rejected: adds a Python wrapper
around shell behaviour with no clarity benefit. The shell pipe-test approach is more
direct.

### Option B: No automated tests

Acceptable for a tiny personal project but rejected once the security hooks made
regressions genuinely costly (a silent hook regression could allow settings file
overwrites without Jeroen noticing).

### Option C: Visual regression testing (percy, pixelmatch)

Generate reference PDF images and diff automatically. Rejected: visual changes are
frequent and intentional; reference images would need updating constantly, creating
friction rather than safety.

---

## References

- CLAUDE.md §"Automated tests" — operational documentation for running tests
- CLAUDE.md §"PR review checklist" (Tester persona) — where test evidence is required
- `tests/test_generate.py`, `tests/test_process_photo.py`, `tests/test_hooks.sh`
- `.github/workflows/tests.yml` — the CI workflow
- ADR-001 — persona orchestration context (Claude Code subagents are the primary
  contributor, so CI enforcement matters more than in a human-only workflow)

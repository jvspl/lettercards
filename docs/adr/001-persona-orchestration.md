# ADR-001: Persona Orchestration via Claude Code Subagents

**Status:** Accepted
**Date:** 2026-03-19
**Deciders:** Jeroen (operator), Architect persona

---

## Context

The project uses a set of named personas (Engineer, Designer, Pedagogue, Security, Product Owner, etc.) to represent different concerns and perspectives. Currently these personas are consulted ad-hoc during conversations — they have no persistent memory, no standing investigations, and no way to operate independently.

The goal is to let personas work autonomously: picking up issues from the GitHub backlog, making changes to the codebase, opening PRs, reviewing each other's work, and handing off across sessions — without Jeroen having to drive every step.

Two mechanisms in Claude Code can enable this:

1. **Subagents** (`claude/agents/`) — specialized agents that run within a single orchestrator session, each in their own context window, reporting results back to the orchestrator. Stable feature.
2. **Agent Teams** — fully independent Claude Code sessions that share a task list and can message each other directly. Experimental feature (requires `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS=1`), higher token cost, known limitations around session resumption and task coordination.

---

## Decision

**Use Claude Code subagents (Option A) as the first implementation.**

Each persona is defined as a subagent in `.claude/agents/`. An orchestrator session (the main Claude Code session) reads the GitHub backlog, identifies the right persona for each issue, and delegates via the `Agent` tool. Personas return results to the orchestrator, which handles handoffs.

Agent Teams (Option B) are deferred. They are the natural evolution once subagents prove insufficient — specifically when personas need to coordinate directly with each other rather than through the orchestrator. That transition has its own issue (#future).

---

## Architecture

### Persona subagent files

Each persona lives in `.claude/agents/<persona-name>.md`, checked into version control so all sessions share the same definitions.

```
.claude/
  agents/
    engineer.md
    designer.md
    pedagogue.md
    security.md
    product-owner.md
    architect.md
```

Each file uses YAML frontmatter + a system prompt:

```markdown
---
name: engineer
description: >
  Software engineering specialist. Use when implementing code changes,
  fixing bugs, refactoring, or any task that requires editing files.
  Invoked proactively when a GitHub issue is labeled persona:engineer.
tools: Read, Edit, Write, Glob, Grep, Bash
model: sonnet
memory: project
isolation: worktree
---

You are the Engineer persona for the lettercards project...
```

### Tool access per persona

Personas get the minimum tools needed for their role:

| Persona | Tools | Model | Memory | Isolation |
|---------|-------|-------|--------|-----------|
| Engineer | Read, Edit, Write, Glob, Grep, Bash, WebSearch | sonnet | project | worktree |
| Designer | Read, Edit, Write, Glob, Grep, Bash | sonnet | project | worktree |
| Pedagogue | Read, Glob, Grep, Bash (gh) | haiku | project | none |
| Security | Read, Glob, Grep, Bash (gh, git) | sonnet | project | none |
| Product Owner | Bash (gh only), Read | haiku | project | none |
| Architect | Read, Glob, Grep, Bash (gh) | sonnet | project | none |

**Why `isolation: worktree` for Engineer and Designer?** The `isolation: worktree` frontmatter field runs the subagent in a temporary git worktree — an isolated copy of the repo. This prevents branch conflicts when multiple agents run in parallel, and the worktree is cleaned up automatically if no changes are made.

**Why `memory: project`?** Stores agent memory in `.claude/agent-memory/<name>/`, which can be checked into version control. This lets personas accumulate project-specific knowledge across sessions (style patterns found, security findings, recurring issues).

**Why Haiku for read-only personas?** Pedagogue, Product Owner, and Architect primarily read and report — they don't need Sonnet's reasoning depth for most tasks. Using Haiku reduces cost.

### GitHub as the task queue

Issues are the coordination layer. The orchestrator polls `gh issue list` and routes by label:

| Label | Persona invoked |
|-------|----------------|
| `persona:engineer` | Engineer |
| `persona:designer` | Designer |
| `persona:pedagogue` | Pedagogue |
| `persona:security` | Security |
| `persona:product-owner` | Product Owner |
| `persona:architect` | Architect |
| `needs:review` | Architect (cross-cutting review) |

#### Transport abstraction for different runtimes

The orchestration model depends on GitHub data/actions, but not on one specific transport. Runtime preference order:

1. **Built-in integration (MCP/API/UI bridge)** when available.
2. **`gh` CLI** in desktop/local environments.
3. **Operator-assisted/manual fallback** when direct integration is unavailable.

This preserves the same persona routing model while making execution portable across Claude Desktop, Codex Cloud, and human-operated workflows.

Handoffs use issue comments and PR labels. When the Engineer opens a PR, it adds `needs:designer-review` — the orchestrator picks this up next session and invokes the Designer subagent.

### Orchestrator responsibilities

The main Claude Code session acts as orchestrator. It:

1. Reads the backlog (`gh issue list --label persona:*`)
2. Selects the appropriate persona subagent
3. Provides context: the issue body, relevant files, any handoff notes
4. Invokes the subagent via the `Agent` tool
5. Receives the result and updates GitHub (comment, label change, PR link)
6. Loops to the next issue or stops

The orchestrator does not do the work itself — it routes and synthesises.

### ORCHESTRATOR.md — persistent repo memory

The orchestrator session maintains a file called `ORCHESTRATOR.md` in the repo root. This is a living document the orchestrator actively reads and updates, distinct from the auto-managed `memory: project` files. It serves two purposes:

1. **Survives context compaction** — when a long session compacts, Claude preserves what's in ORCHESTRATOR.md. Without this, the repo map and accumulated decisions can be silently lost.
2. **Human-readable source of truth** — Jeroen can read it to understand what the orchestrator knows, correct it, or prime a fresh session.

Contents of ORCHESTRATOR.md at minimum:
- Architecture map (modules, entry points, dependencies)
- Conventions and patterns discovered
- Decisions made (links to ADRs and issues)
- Known fragile areas
- Current state (what's in flight, what was recently changed)

The orchestrator updates ORCHESTRATOR.md after every subagent completes and before any context compaction checkpoint.

### File ownership protocol

When the orchestrator spawns a subagent, the prompt must explicitly state:
- **Goal**: what to achieve
- **Files it owns**: the only files it may edit
- **Files it must not touch**: explicitly named off-limits files
- **Conventions to follow**: from ORCHESTRATOR.md
- **How to verify**: what to run and what a passing result looks like

This is stricter than `isolation: worktree` alone — worktree prevents branch conflicts, but file ownership prevents a subagent from touching unrelated parts of the codebase within its worktree.

### Verify-before-return protocol

Subagents must verify their own work before returning to the orchestrator. For this project that means running `python generate.py --letters <affected>` and confirming the output looks correct. The subagent reports: what it changed, what it verified, and any concerns. The orchestrator then decides whether to accept, reject, or spawn a follow-up.

### Key constraint: subagents cannot spawn subagents

Claude Code subagents cannot invoke other subagents. The orchestrator must always be the main session. This means:
- Persona-to-persona handoffs go through the orchestrator, not directly
- The orchestrator must stay active for the duration of a multi-persona workflow
- Long workflows are broken into discrete issues so each can be picked up independently

---

## Consequences

### Positive

- **Stable foundation**: subagents are a production-grade feature, not experimental
- **Version-controlled personas**: `.claude/agents/` files are in the repo, reviewable, improvable
- **Persistent knowledge**: `memory: project` lets personas accumulate project expertise
- **Git safety**: `isolation: worktree` prevents agents from accidentally breaking the main branch
- **Cost-conscious**: Haiku for lightweight personas, role-appropriate tool access
- **Incremental**: start with one persona, add others one by one

### Negative / risks

- **Orchestrator bottleneck**: all cross-persona communication goes through the main session; no direct peer-to-peer coordination
- **Token cost scales**: each subagent invocation uses its own context window; running all 6 personas in one session is expensive
- **Background subagents can't ask questions**: if a subagent needs clarification it fails silently — requires well-scoped issues and pre-approved permissions
- **No session resumption for in-process agents**: interrupted workflows lose subagent context

### Mitigation

- Keep issues small and well-scoped (Product Owner responsibility)
- Pre-approve common tool permissions in `settings.json` before running the orchestrator
- Use `maxTurns` in subagent definitions to prevent runaway agents
- Reassess Agent Teams (Option B) if orchestrator bottleneck becomes a real problem

---

## Alternatives considered

### Option B: Agent Teams (deferred)

The experimental `CLAUDE_CODE_EXPERIMENTAL_AGENT_TEAMS` feature would give each persona a fully independent session with a shared task list and direct peer-to-peer messaging. This removes the orchestrator bottleneck entirely.

Deferred because:
- Experimental, with known limitations (no session resumption, task status lag, no nested teams)
- Significantly higher token cost
- Known issues around shutdown and cleanup
- Subagents are sufficient for the handoff patterns this project needs

Revisit when: a persona genuinely needs to receive mid-task feedback from another persona without going through the orchestrator.

### Option C: External orchestrator script

A Python script using the Anthropic SDK spawning `claude` CLI subprocesses. More powerful but requires maintaining custom infrastructure. Not justified when Claude Code's built-in subagent system covers the use case.

---

## References

- [Claude Code: Create custom subagents](https://code.claude.com/docs/en/sub-agents)
- [Claude Code: Orchestrate agent teams](https://code.claude.com/docs/en/agent-teams)
- [Anthropic: Building effective agents](https://www.anthropic.com/research/building-effective-agents)
- [Matt Shumer: 10x Your Coding Agent Productivity](https://x.com/mattshumer_/status/2035058834117419036) — source of ORCHESTRATOR.md pattern, file ownership protocol, and verify-before-return convention
- GitHub issue #43: Define persona operating model
- GitHub issue #45: Epic — persona orchestration via Claude Code subagents

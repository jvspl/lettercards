# Letterkaarten

A card generator for teaching a toddler to associate letter sounds with words — in Dutch.

Each word produces two printable cards:
- **Picture card**: image + word (first letter highlighted)
- **Letter card**: the letter itself

Output is a printable A4 PDF with 9 cards per page.

## Quick Start

```bash
# Setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .

# Generate cards
lettercards generate
```

This creates `letterkaarten.pdf` ready for printing.

Legacy scripts still work during the transition:

```bash
python generate.py
python process_photo.py --list
python pictogram_workflow.py status
```

## CLI

```bash
lettercards generate
lettercards generate --letters a,d,o
lettercards status
lettercards photo process oma
lettercards pictogram prompt appel auto deur
lettercards pictogram split appel auto deur --grid 3x1
lettercards deck check
```

## Documentation

See [CLAUDE.md](CLAUDE.md) for full documentation:
- How to add words and images
- Personal photo workflow
- Font and color configuration
- Architecture details

## Developer setup

After cloning, the baseline requirement is a Python virtual environment (already covered in Quick Start).

GitHub tooling is environment-dependent:
- **Desktop/local workflows (human devs, Claude Code Desktop):** `gh` is recommended.
- **Web/cloud agent workflows (Codex Cloud or similar):** built-in integrations may replace `gh`.

### GitHub access modes (tool-agnostic)

Use this order of preference:

1. **Built-in platform integration** (MCP/server tools) when available.
2. **`gh` CLI** for local/desktop workflows.
3. **Repository-local fallback** (no GitHub API) for analysis/docs work when remote access is unavailable.

This keeps the repo usable whether work is done by Codex, Claude Code, or human developers, and whether the runtime is desktop or web/cloud.

### Agent compatibility notes

- In some web/cloud runtimes, creating the **actual GitHub PR** is a manual UI step (e.g., clicking "Create PR"), even when the agent has prepared commits and PR text.
- In desktop/local runtimes with `gh` configured, PR creation can be fully CLI-driven (`gh pr create`).
- When in doubt, treat PR draft text generation and PR publication as two separate steps.

### GitHub CLI — fine-grained PAT (desktop/local mode)

If you are using the `gh` CLI, use a **fine-grained personal access token** scoped to this repository only. A classic OAuth token grants full admin access (merge bypassing branch protection, delete repo, manage webhooks) — do not use one.

**Create the token:**

1. Go to GitHub → Settings → Developer settings → Personal access tokens → Fine-grained tokens
2. Click **Generate new token**
3. Set **Resource owner** to your account and **Repository access** to this repo only (`lettercards`)
4. Grant these permissions — nothing else:

| Permission | Access |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Issues | Read and write |
| Actions | Read-only |
| Metadata | Read-only (required, auto-selected) |

5. Generate the token and copy it.

**Set up the token in two steps.**

1. Create the gh config directory for Claude (one-time, per machine):

```bash
mkdir -p ~/.config/gh-claude
```

2. Create `.claude/settings.local.json` in the repo root (gitignored — each developer has their own):

```json
{
  "env": {
    "GH_TOKEN": "github_pat_YOUR_TOKEN_HERE"
  }
}
```

`GH_TOKEN` is read by `gh` directly and takes precedence over any stored credential, so no `gh auth login` is needed. The shared `.claude/settings.json` already sets `GH_CONFIG_DIR=~/.config/gh-claude` so `gh` reads its config from a sandbox-accessible path rather than from `~/.config/gh/`.

**Verify:**

```bash
gh pr list
```

Should return open PRs without errors. Your personal `gh` config is unaffected — `GH_TOKEN` and `GH_CONFIG_DIR` only apply inside Claude Code sessions in this repo.

### Sandbox

Claude Code runs sandboxed by default (configured in `.claude/settings.json`). The sandbox uses macOS Seatbelt to enforce:

- **Filesystem isolation**: Claude can only read/write the project directory. Reads from `~/` are blocked — this prevents accidental access to personal photos, SSH keys, credentials, etc.
- **Network isolation**: Outbound connections are restricted to `github.com`, `api.github.com`, and `api.anthropic.com`. Attempts to reach other hosts prompt for confirmation.
- **Weaker network isolation** (`enableWeakerNetworkIsolation: true`): allows the macOS system TLS trust service, which is needed by Go binaries like `gh` for certificate verification. This does not open additional network hosts — only allows the local trust daemon call.

**Developer impact:**

| Scenario | Works? | Notes |
|---|---|---|
| `venv/bin/pytest tests/` | Yes | All files in project dir |
| `bash tests/test_hooks.sh` | Yes | All files in project dir |
| `python generate.py --safe-letters-only` | Yes | No personal photos needed |
| `python generate.py` with personal letters | Only if run directly | Claude cannot read `~/` — run this yourself |
| `git` commands | Yes | Runs via normal permission flow |
| `gh` commands | Yes, with setup above | Needs `GH_TOKEN` + `GH_CONFIG_DIR` (both set by settings files) |

**What is not sandboxed**: Claude's `Read`, `Edit`, and `Write` file tools use the Claude Code permissions system directly (not the OS sandbox). These are governed by the `permissions.allow/deny` rules in `.claude/settings.json`.

The `bypassPermissions` mode is permanently disabled (`disableBypassPermissionsMode: "disable"`), so there is no way to run Claude without permission checks in this project.

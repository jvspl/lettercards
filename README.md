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

# Generate cards
python generate.py
```

This creates `letterkaarten.pdf` ready for printing.

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

**Configure a separate gh config dir** so Claude's token doesn't overwrite your personal one.

Create `.claude/settings.local.json` in the repo root (this file is gitignored — each developer has their own):

```json
{
  "env": {
    "GH_CONFIG_DIR": "/Users/yourname/.config/gh-claude"
  }
}
```

**Authenticate into that config dir:**

```bash
echo "YOUR_TOKEN" | GH_CONFIG_DIR=~/.config/gh-claude gh auth login --with-token
```

**Verify:**

```bash
GH_CONFIG_DIR=~/.config/gh-claude gh auth status
GH_CONFIG_DIR=~/.config/gh-claude gh pr list
```

`gh auth status` should show the token is scoped to this repo. `gh pr list` should work. `gh pr merge --admin` should now fail with a 403. Your regular `gh` CLI is unaffected.

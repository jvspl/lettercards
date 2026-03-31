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

After cloning, you need two things beyond the Quick Start above: a Python virtual environment (already covered) and a GitHub CLI token scoped to this repo only.

### GitHub CLI — fine-grained PAT

The `gh` CLI must use a **fine-grained personal access token** scoped to this repository only. A classic OAuth token grants full admin access (merge bypassing branch protection, delete repo, manage webhooks) — do not use one.

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

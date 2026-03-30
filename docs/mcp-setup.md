# MCP Photo Wizard — Setup Guide

This lets you select and process personal photos for letter cards entirely inside
Claude Desktop. See real card previews, pick the best one, and it gets saved to your
personal library — no command line needed.

## Requirements

- Claude Desktop installed and signed in
- Python 3.10+ (macOS: `brew install python@3.13` if needed)
- The lettercards repo cloned locally

## One-time setup

### 1. Create the MCP virtual environment

From the repo root:

```bash
python3.13 -m venv venv-mcp
venv-mcp/bin/pip install "mcp[cli]" pillow
```

### 2. Register the server with Claude Desktop

Edit `~/Library/Application Support/Claude/claude_desktop_config.json`
(create it if it doesn't exist):

```json
{
  "mcpServers": {
    "lettercards": {
      "command": "/absolute/path/to/repo/venv-mcp/bin/python",
      "args": ["/absolute/path/to/repo/mcp_server.py"]
    }
  }
}
```

Replace `/absolute/path/to/repo` with the actual path to your clone.
To find it: `pwd` from the repo root.

### 3. Restart Claude Desktop

Quit and reopen Claude Desktop. You should see a hammer icon (🔨) in the
chat input area — that means MCP tools are active.

## Using the wizard

### Option A — Staging folder (recommended for batches)

1. Copy your candidate photos to `~/.lettercards/staging/`
2. Open Claude Desktop (or a Cowork session)
3. Say something like: *"Help me pick a photo for Tata"*
4. Claude calls `list_staging_photos`, previews all photos, and if there are 4 or more
   shows a side-by-side comparison of the top 3
5. Confirm your choice — Claude saves it to `~/.lettercards/personal/`
6. Back in the terminal: `python generate.py --letters t` to generate the PDF

### Option B — Drag photos into the chat

1. Open Claude Desktop
2. Drag photos directly into the chat input
3. Say something like: *"Help me pick a photo for Tata"*
4. Claude sees the inline images and generates card previews using them directly
5. Confirm and save as above

> **Note:** Card previews appear inside the "Used lettercards integration" section —
> click that header to expand it and see the cards.

## Troubleshooting

**Hammer icon not showing:** Claude Desktop didn't pick up the config.
Check the JSON is valid (no trailing commas) and restart Claude Desktop.

**"Server failed to start":** Check the paths in the config are absolute and correct.
Test manually: `venv-mcp/bin/python mcp_server.py` should start without errors.

**Card preview looks wrong:** The crop takes the top square of portrait photos. If the
face is cut off, try a photo where the face is in the upper portion of the frame.

# MCP Photo Wizard — Setup Guide

This lets you select and process personal photos for letter cards inside any
MCP-capable AI client. A native file picker opens so you can choose photos from
anywhere on your computer, the AI evaluates the best candidates, and you see them
rendered as actual lettercards before saving — no command line needed for the
selection step.

## Requirements

- An MCP-capable AI client (Claude Desktop, ChatGPT Desktop, or any client that
  supports the MCP protocol)
- Python 3.10+
- The lettercards repo cloned locally

## One-time setup

### 1. Create the MCP virtual environment

From the repo root:

```bash
python3 -m venv venv-mcp
venv-mcp/bin/pip install "mcp[cli]" pillow
```

On Windows:
```
python -m venv venv-mcp
venv-mcp\Scripts\pip install "mcp[cli]" pillow
```

### 2. Register the server with your AI client

The config location depends on your client and OS:

**Claude Desktop — macOS:**
`~/Library/Application Support/Claude/claude_desktop_config.json`

**Claude Desktop — Windows:**
`%APPDATA%\Claude\claude_desktop_config.json`

**Claude Desktop — Linux:**
`~/.config/Claude/claude_desktop_config.json`

In all cases, add:

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

On Windows use the full path with backslashes and `venv-mcp\Scripts\python.exe`.

Replace `/absolute/path/to/repo` with the actual path to your clone
(`pwd` from the repo root gives you this).

### 3. Restart the AI client

Quit and reopen the client. You should see a tools/hammer icon in the chat
input area — that means MCP tools are active.

## Using the wizard

### Standard flow

1. Open your AI client
2. Say something like: *"Help me pick a photo for Tata"*
3. The AI calls `pick_photos("Tata")` — **a native file picker dialog opens**
4. Select your candidate photos (any folder, any number)
5. The AI evaluates them:
   - 1–3 photos: renders them directly as lettercards side-by-side
   - 4+ photos: shows a numbered thumbnail grid first, picks the best 2–3,
     then renders those as lettercards
6. Expand the tool output section in your AI client to see the rendered cards
7. Tell the AI which one you want: *"use number 2"*
8. The AI saves it to `~/.lettercards/personal/` and tells you the generate command

### Headless / no display fallback

If the file picker dialog cannot open (e.g. a remote session without a display),
tell the AI where the photos are:

*"Help me pick a photo for Tata — the photos are in ~/Downloads/family"*

The AI will call `pick_photos("Tata", directory="~/Downloads/family")` to list
photos from that directory instead.

### Staging folder fallback

If you prefer copying photos to a fixed location first, put them in
`~/.lettercards/staging/` and ask the AI to use `list_staging_photos` instead
of the picker.

## Troubleshooting

**Tools icon not showing:** The client didn't pick up the config.
Check the JSON is valid (no trailing commas) and restart the client.

**"Server failed to start":** The paths in the config are wrong or the venv is
missing. Test manually: `venv-mcp/bin/python mcp_server.py` should exit cleanly
(no output means success; it waits for stdin).

**File picker doesn't appear / appears behind other windows:** On macOS, the
dialog may appear behind the AI client window. Check the taskbar/dock.
On Linux, `tkinter` requires a display — install `python3-tk` if missing
(`sudo apt install python3-tk` on Debian/Ubuntu).

**Card preview looks wrong:** The crop takes the top square of portrait photos.
If the face is cut off, try a photo where the face is in the upper portion of
the frame, or choose a different candidate from the comparison grid.

**Wrong font / plain text on cards:** The server looks for fonts in the repo's
`fonts/` directory first, then common system locations. To guarantee a specific
font, drop a `.ttf` file into `fonts/` — it will be picked up automatically.

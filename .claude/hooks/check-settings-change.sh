#!/bin/bash
# Hook: PostToolUse on Write|Edit
# Fires when a Claude settings file is modified.
# Outputs a systemMessage prompting Security persona review.

# Skip if jq not installed
command -v jq >/dev/null 2>&1 || exit 0

# Extract the modified file path from stdin
f=$(jq -r '.tool_input.file_path // empty')

# Only trigger on .claude/*settings*.json files
echo "$f" | grep -qE '\.claude/.*settings.*\.json' || exit 0

printf '{"systemMessage":"⚠️ Security review required: a settings file was modified. Apply the Security persona before continuing — check for overly broad permissions, bypassPermissions usage, or commands that could expose personal data or grant excessive access."}'

#!/bin/bash
# Hook: PreToolUse on Write|Edit
# Runs BEFORE a settings file is written.
# - Blocks if bypassPermissions is detected (hard stop)
# - Warns and requires Security review for all other settings changes

command -v jq >/dev/null 2>&1 || exit 0

# Read stdin once into a variable
input=$(cat)

# Only act on .claude/*settings*.json files
f=$(echo "$input" | jq -r '.tool_input.file_path // empty')
echo "$f" | grep -qE '\.claude/.*settings.*\.json' || exit 0

# Extract content being written (Write uses .content, Edit uses .new_string)
content=$(echo "$input" | jq -r '.tool_input.content // .tool_input.new_string // empty')

# Hard block: bypassPermissions is never allowed
if echo "$content" | grep -q 'bypassPermissions'; then
  printf '{"continue": false, "stopReason": "⛔ Blocked: bypassPermissions detected. This grants unlimited tool access with no safety checks. Apply Security persona review — justify explicitly or remove."}'
  exit 0
fi

# Advisory: all other settings changes require Security persona review
printf '{"systemMessage":"⚠️ Security review required: about to modify a settings file. Before proceeding, apply the Security persona response protocol documented in CLAUDE.md."}'

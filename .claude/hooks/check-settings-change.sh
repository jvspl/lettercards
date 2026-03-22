#!/bin/bash
# Hook: PostToolUse on Write|Edit
# Fires when a Claude settings file is modified.
# Outputs a systemMessage prompting Security persona review.
#
# NOTE: Claude Code runs hooks from the project root, so the relative
# path in settings.json (bash .claude/hooks/...) is intentional and safe.

# Warn loudly if jq is not installed — do not silently pass
if ! command -v jq >/dev/null 2>&1; then
  printf '{"systemMessage":"⚠️ jq is not installed — settings file protection is disabled. Install jq (brew install jq) to enable security checks."}'
  exit 0
fi

# Read stdin once into a variable
input=$(cat)

# Extract the modified file path
f=$(echo "$input" | jq -r '.tool_input.file_path // empty')

# Only trigger on .claude/*settings*.json files
echo "$f" | grep -qE '\.claude/.*settings.*\.json' || exit 0

# Louder warning if bypassPermissions was written (#85)
content=$(echo "$input" | jq -r '.tool_input.content // .tool_input.new_string // empty' 2>/dev/null)
if echo "$content" | grep -qi 'bypasspermissions'; then
  printf '{"systemMessage":"⛔ WARNING: bypassPermissions was just written to a settings file. This grants unlimited tool access with no safety checks. Review immediately — revert if this was not intentional."}'
  exit 0
fi

printf '{"systemMessage":"⚠️ Security review required: a settings file was modified. Apply the Security persona before continuing — check for overly broad permissions, bypassPermissions usage, or commands that could expose personal data or grant excessive access."}'

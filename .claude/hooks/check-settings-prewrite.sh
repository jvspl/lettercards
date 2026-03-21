#!/bin/bash
# Hook: PreToolUse on Write|Edit
# Runs BEFORE a settings file is written.
# - Blocks if bypassPermissions is detected (hard stop)
# - Warns and requires Security review for all other settings changes
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

# Only act on .claude/*settings*.json files
f=$(echo "$input" | jq -r '.tool_input.file_path // empty')
echo "$f" | grep -qE '\.claude/.*settings.*\.json' || exit 0

# Extract content being written (Write uses .content, Edit uses .new_string)
content=$(echo "$input" | jq -r '.tool_input.content // .tool_input.new_string // empty')

# Hard block: bypassPermissions is never allowed.
# Use jq to parse the JSON structurally — handles unicode escapes that fool grep.
if echo "$content" | jq -e '.. | strings | contains("bypassPermissions")' 2>/dev/null | grep -q 'true'; then
  printf '{"continue": false, "stopReason": "⛔ Blocked: bypassPermissions detected. This grants unlimited tool access with no safety checks. Apply Security persona review — justify explicitly or remove."}'
  exit 0
fi

# Advisory: all other settings changes require Security persona review
printf '{"systemMessage":"⚠️ Security review required: about to modify a settings file. Before proceeding, apply the Security persona response protocol documented in CLAUDE.md."}'

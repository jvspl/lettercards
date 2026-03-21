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

printf '{"systemMessage":"⚠️ Security review required: a settings file was modified. Apply the Security persona before continuing — check for overly broad permissions, bypassPermissions usage, or commands that could expose personal data or grant excessive access."}'

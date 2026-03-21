#!/bin/bash
# Hook: PreToolUse on Bash
# Catches shell commands that write to .claude/ settings files,
# bypassing the Write/Edit hook guards.
#
# Only matches when the settings path appears as an actual write target:
#   echo ... > .claude/settings.local.json
#   cat ... >> .claude/settings.json
#   tee .claude/settings.local.json
#   sed -i ... .claude/settings.local.json
#
# Does NOT match commands that merely mention a settings path in a string
# (e.g. git commit messages, grep searches, cat reads).

# Warn loudly if jq is not installed
if ! command -v jq >/dev/null 2>&1; then
  printf '{"systemMessage":"⚠️ jq is not installed — Bash settings protection is disabled. Install jq (brew install jq) to enable security checks."}'
  exit 0
fi

input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only match when a settings file is the TARGET of a write operation.
# Require the path to follow a redirect (> or >>) or be an argument to tee/sed -i.
if ! echo "$cmd" | grep -qE '(>>?\s*["\x27]?\.claude/[^"'"'"' ]*settings[^"'"'"' ]*\.json|tee\s+["\x27]?\.claude/[^"'"'"' ]*settings[^"'"'"' ]*\.json|sed\s+-i\s+.*\.claude/.*settings.*\.json)'; then
  exit 0
fi

# Hard block if bypassPermissions appears in the command
if echo "$cmd" | grep -q 'bypassPermissions'; then
  printf '{"continue": false, "stopReason": "⛔ Blocked: Bash command would write bypassPermissions to a settings file. This grants unlimited tool access with no safety checks."}'
  exit 0
fi

# Advisory for any other write to a settings file via Bash
printf '{"systemMessage":"⚠️ Security review required: Bash command targets a settings file. Apply the Security persona response protocol before proceeding."}'

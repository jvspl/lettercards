#!/bin/bash
# Hook: PreToolUse on Bash
# Catches shell commands that write to .claude/ settings files,
# bypassing the Write/Edit hook guards.
#
# Matched write patterns:
#   echo ... > .claude/settings.local.json     (redirect)
#   cat ... >> .claude/settings.json           (append redirect)
#   tee .claude/settings.local.json            (tee)
#   sed -i ... .claude/settings.local.json     (in-place edit)
#   cp src.json .claude/settings.local.json    (copy to target)
#   mv /tmp/x.json .claude/settings.json       (move to target)
#
# Does NOT match commands that merely mention a settings path in a string
# (e.g. git commit messages, grep searches, cat reads).

# Warn loudly if jq is not installed
if ! command -v jq >/dev/null 2>&1; then
  printf '{"continue": false, "stopReason": "⛔ jq is required for security hooks but is not installed. Run: brew install jq"}'
  exit 0
fi

input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')

# Only match when a settings file is the TARGET of a write operation.
# Patterns: redirect (>/>>), tee, sed -i, cp/mv with settings as destination.
if ! echo "$cmd" | grep -qE '(>>?\s*["\x27]?\.claude/[^"'"'"' ]*settings[^"'"'"' ]*\.json|tee\s+["\x27]?\.claude/[^"'"'"' ]*settings[^"'"'"' ]*\.json|sed\s+-i\s+.*\.claude/.*settings.*\.json|(cp|mv)\b.*\s+["\x27]?\.claude/[^"'"'"' ]*settings[^"'"'"' ]*\.json)'; then
  exit 0
fi

# Hard block if bypassPermissions appears in the command (case-insensitive)
if echo "$cmd" | grep -qi 'bypasspermissions'; then
  printf '{"continue": false, "stopReason": "⛔ Blocked: Bash command would write bypassPermissions to a settings file. This grants unlimited tool access with no safety checks."}'
  exit 0
fi

# Advisory for any other write to a settings file via Bash
printf '{"systemMessage":"⚠️ Security review required: Bash command targets a settings file. Apply the Security persona response protocol before proceeding."}'

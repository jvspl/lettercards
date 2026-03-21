#!/bin/bash
# Hook: PreToolUse on Bash
# Catches shell commands that write to .claude/ settings files,
# bypassing the Write/Edit hook guards.
#
# Bash commands are free-form, so this uses pattern matching rather than
# structural parsing. It catches common write patterns:
#   echo ... > .claude/settings.local.json
#   cat ... > .claude/settings.json
#   sed -i ... .claude/settings.local.json
#   tee .claude/settings.local.json
#
# This is a best-effort guard, not a hard guarantee. The Write/Edit hooks
# are the primary structural protection.

# Warn loudly if jq is not installed
if ! command -v jq >/dev/null 2>&1; then
  printf '{"systemMessage":"⚠️ jq is not installed — Bash settings protection is disabled. Install jq (brew install jq) to enable security checks."}'
  exit 0
fi

input=$(cat)
cmd=$(echo "$input" | jq -r '.tool_input.command // empty')

# Check if the command targets a .claude/*settings*.json file
if ! echo "$cmd" | grep -qE '\.claude/.*settings.*\.json'; then
  exit 0
fi

# Check if it looks like a write operation (not a read)
if echo "$cmd" | grep -qE '(>|>>|tee|sed\s+-i|awk\s+.*>|cat\s+.*>|printf\s+.*>|echo\s+.*>)'; then
  # Hard block if bypassPermissions appears in the command
  if echo "$cmd" | grep -q 'bypassPermissions'; then
    printf '{"continue": false, "stopReason": "⛔ Blocked: Bash command would write bypassPermissions to a settings file. This grants unlimited tool access with no safety checks."}'
    exit 0
  fi
  # Advisory for any other write to a settings file via Bash
  printf '{"systemMessage":"⚠️ Security review required: Bash command targets a settings file. Apply the Security persona response protocol before proceeding."}'
  exit 0
fi

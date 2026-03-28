#!/bin/bash
# Hook: PostToolUse Bash
# Triggers a PR review at the right moment:
#   - gh pr create (no --draft): fires immediately
#   - gh pr create --draft:      silent — PR isn't ready yet
#   - gh pr ready:               fires — author has signalled done

command -v jq >/dev/null 2>&1 || exit 0

payload=$(cat)
cmd=$(echo "$payload" | jq -r '.tool_input.command // empty')
output=$(echo "$payload" | jq -r '.tool_response.output // empty')
exit_code=$(echo "$payload" | jq -r '.tool_response.exit_code // 1')

[ "$exit_code" = "0" ] || exit 0

pr_number=""

if echo "$cmd" | grep -q 'gh pr create'; then
  # Skip draft PRs — review will fire when gh pr ready is called
  echo "$cmd" | grep -q -- '--draft' && exit 0
  # Extract PR number from the URL gh pr create prints
  pr_number=$(echo "$output" | grep -oE '/pull/[0-9]+' | grep -oE '[0-9]+' | head -1)

elif echo "$cmd" | grep -q 'gh pr ready'; then
  # Try the PR number from the command first (gh pr ready 108)
  pr_number=$(echo "$cmd" | grep -oE '\b[0-9]+\b' | head -1)
  # Fall back to the URL in the output if no number in command
  if [ -z "$pr_number" ]; then
    pr_number=$(echo "$output" | grep -oE '/pull/[0-9]+' | grep -oE '[0-9]+' | head -1)
  fi
fi

[ -n "$pr_number" ] || exit 0

msg="PR #${pr_number} is ready for review. Run a full review following the /pr-review checklist and post the complete findings as a comment on PR #${pr_number} using gh pr comment, signed — 🤖 Claude."

printf '{"systemMessage":"%s"}' "$(echo "$msg" | sed 's/"/\\"/g')"

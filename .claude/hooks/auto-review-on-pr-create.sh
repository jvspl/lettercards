#!/bin/bash
# Hook: PostToolUse Bash
# Triggers a PR review at the right moment:
#   - gh pr create (no --draft): fires immediately
#   - gh pr create --draft:      silent — PR isn't ready yet
#   - gh pr ready:               fires — author has signalled done
#
# Safety invariant: pr_number is always digits-only before it reaches the
# systemMessage. Do not add output/cmd content to the message directly —
# that would open a prompt injection path via GitHub API responses.

command -v jq >/dev/null 2>&1 || exit 0

payload=$(cat)
cmd=$(echo "$payload" | jq -r '.tool_input.command // empty')
output=$(echo "$payload" | jq -r '.tool_response.output // empty')
exit_code=$(echo "$payload" | jq -r '.tool_response.exit_code // 1')

[ "$exit_code" = "0" ] || exit 0

pr_number=""

if echo "$cmd" | grep -q 'gh pr create'; then
  # Skip draft PRs — match --draft as a standalone token, not inside quoted strings
  echo "$cmd" | tr ' ' '\n' | grep -qx -- '--draft' && exit 0
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

# Use jq to construct JSON safely — handles quotes, newlines, and special chars
msg="PR #${pr_number} is ready for review. Run a full review following the /pr-review checklist and post the complete findings as a comment on PR #${pr_number} using gh pr comment, signed — 🤖 Claude."
jq -n --arg msg "$msg" '{"systemMessage":$msg}'

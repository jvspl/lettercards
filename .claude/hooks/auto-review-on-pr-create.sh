#!/bin/bash
# Hook: PostToolUse Bash
# When gh pr create succeeds, instruct Claude to run a full PR review
# and post the findings as a comment on the PR.

command -v jq >/dev/null 2>&1 || exit 0

payload=$(cat)

# Only act on gh pr create commands
cmd=$(echo "$payload" | jq -r '.tool_input.command // empty')
echo "$cmd" | grep -q 'gh pr create' || exit 0

# Only act if the command succeeded
exit_code=$(echo "$payload" | jq -r '.tool_response.exit_code // 1')
[ "$exit_code" = "0" ] || exit 0

# Extract PR number from URL in output
# gh pr create prints: https://github.com/owner/repo/pull/123
output=$(echo "$payload" | jq -r '.tool_response.output // empty')
pr_number=$(echo "$output" | grep -oE '/pull/[0-9]+' | grep -oE '[0-9]+' | head -1)

[ -n "$pr_number" ] || exit 0

msg="PR #${pr_number} was just created. Run a full review following the /pr-review checklist and post the complete findings as a comment on PR #${pr_number} using gh pr comment, signed — 🤖 Claude."

printf '{"systemMessage":"%s"}' "$(echo "$msg" | sed 's/"/\\"/g')"

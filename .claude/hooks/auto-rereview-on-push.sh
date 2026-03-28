#!/bin/bash
# Hook: PostToolUse Bash
# When git push succeeds on a branch with an open PR that has a 🔄 review,
# remind Claude to consider running a re-review.
#
# LETTERCARDS_TEST_PUSH_PR_JSON: inject mock PR data in tests instead of
# calling gh, consistent with the pattern used in other hooks (#83).

command -v jq >/dev/null 2>&1 || exit 0
command -v gh >/dev/null 2>&1 || exit 0

payload=$(cat)
cmd=$(echo "$payload" | jq -r '.tool_input.command // empty')
output=$(echo "$payload" | jq -r '.tool_response.output // empty')
exit_code=$(echo "$payload" | jq -r '.tool_response.exit_code // 1')

[ "$exit_code" = "0" ] || exit 0

# Only act on git push commands
echo "$cmd" | grep -q 'git push' || exit 0

# Extract the remote branch name from push output
# Successful push prints: "  abc1234..def5678  branch -> branch"
branch=$(echo "$output" | grep -oE '[a-zA-Z0-9_/.-]+ -> [a-zA-Z0-9_/.-]+' | awk -F' -> ' '{print $2}' | head -1)
[ -n "$branch" ] || exit 0

# Never trigger for master/main
echo "$branch" | grep -qE '^(master|main)$' && exit 0

# Look up open PR for this branch
if [ -n "$LETTERCARDS_TEST_PUSH_PR_JSON" ]; then
  pr_json="$LETTERCARDS_TEST_PUSH_PR_JSON"
else
  pr_json=$(gh pr list --head "$branch" --state open --json number,comments --limit 1 2>/dev/null)
fi

pr_number=$(echo "$pr_json" | jq -r '.[0].number // empty')
[ -n "$pr_number" ] || exit 0

# Only fire when the existing Claude review has 🔄 (unresolved findings)
has_open_findings=$(echo "$pr_json" | jq '[.[0].comments[] | select(.author.login == "jvspl" and (.body | contains("🤖 Claude")) and (.body | contains("🔄")))] | length' 2>/dev/null)
[ "$has_open_findings" -gt 0 ] || exit 0

msg="Fixes were just pushed to PR #${pr_number}, which has an outstanding 🔄 review. Run a re-review (/pr-review ${pr_number}) if the findings are addressed, or ask Jeroen first."
jq -n --arg msg "$msg" '{"systemMessage":$msg}'

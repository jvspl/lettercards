#!/bin/bash
# Hook: SessionStart
# Checks for recent GitHub activity (updated issues and PRs) and surfaces
# anything updated in the last 7 days as a session context message.

command -v gh >/dev/null 2>&1 || exit 0

# Warn loudly if jq is missing rather than silently skipping (#82)
if ! command -v jq >/dev/null 2>&1; then
  printf '{"systemMessage":"⚠️ jq is not installed — session-start security checks disabled. External GitHub comments will NOT be flagged as untrusted. Install jq to restore this guard: brew install jq"}'
  exit 0
fi

# Fetch open PRs
# LETTERCARDS_TEST_PR_JSON: inject pre-formed JSON in tests instead of calling gh (#83)
if [ -n "$LETTERCARDS_TEST_PR_JSON" ]; then
  prs="$LETTERCARDS_TEST_PR_JSON"
else
  prs=$(gh pr list --state open --json number,title,isDraft,updatedAt 2>/dev/null)
fi

# Fetch open issues updated in last 7 days (limit 20 for speed)
# LETTERCARDS_TEST_ISSUES_JSON: inject pre-formed JSON in tests instead of calling gh (#83)
if [ -n "$LETTERCARDS_TEST_ISSUES_JSON" ]; then
  issues="$LETTERCARDS_TEST_ISSUES_JSON"
else
  issues=$(gh issue list --state open --json number,title,updatedAt,comments --limit 20 2>/dev/null)
fi

# Build summary of open PRs
pr_summary=$(echo "$prs" | jq -r '.[] | "  PR #\(.number)\(if (.isDraft // false) then " [DRAFT]" else "" end): \(.title)"' 2>/dev/null)

# Build summary of issues with comments, flagging non-jvspl authors
issues_with_comments=$(echo "$issues" | jq -r '
  .[] | select(.comments | length > 0) |
  "  #\(.number): \(.title)",
  (.comments[] |
    if .author.login == "jvspl"
    then "    💬 @\(.author.login): \(.body | split("\n")[0] | .[0:100])"
    else "    ⚠️ external comment from @\(.author.login): \(.body | split("\n")[0] | .[0:100])"
    end
  )
' 2>/dev/null)

msg="📋 Session start — GitHub status:"

if [ -n "$pr_summary" ]; then
  msg="$msg\n\nOpen PRs:\n$pr_summary"
else
  msg="$msg\n\nNo open PRs."
fi

if [ -n "$issues_with_comments" ]; then
  msg="$msg\n\nIssues with comments (may have new activity):\n$issues_with_comments"
fi

printf '{"systemMessage":"%s"}' "$(echo -e "$msg" | sed 's/"/\\"/g')"

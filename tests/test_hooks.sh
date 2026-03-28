#!/bin/bash
# tests/test_hooks.sh
# Pipe-tests for the three Claude Code security hooks.
# Run from the project root: bash tests/test_hooks.sh
#
# Tests feed crafted JSON payloads to each hook via stdin and assert
# on stdout content. No Claude Code required — pure bash + jq.

HOOKS_DIR=".claude/hooks"
PASS=0
FAIL=0

pass() { echo "  PASS: $1"; PASS=$((PASS + 1)); }
fail() { echo "  FAIL: $1"; FAIL=$((FAIL + 1)); }

assert_contains() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -q "$needle"; then
    pass "$label"
  else
    fail "$label"
    echo "    expected to find : $needle"
    echo "    stdout was       : $haystack"
  fi
}

assert_not_contains() {
  local label="$1" needle="$2" haystack="$3"
  if echo "$haystack" | grep -q "$needle"; then
    fail "$label"
    echo "    did not expect   : $needle"
    echo "    stdout was       : $haystack"
  else
    pass "$label"
  fi
}

assert_silent() {
  local label="$1" haystack="$2"
  if [ -z "$haystack" ]; then
    pass "$label"
  else
    fail "$label"
    echo "    expected empty stdout, got: $haystack"
  fi
}

write_payload() {
  jq -n --arg fp "$1" --arg c "$2" '{"tool_input":{"file_path":$fp,"content":$c}}'
}

edit_payload() {
  jq -n --arg fp "$1" --arg s "$2" '{"tool_input":{"file_path":$fp,"new_string":$s}}'
}

bash_payload() {
  jq -n --arg c "$1" '{"tool_input":{"command":$c}}'
}

# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== check-settings-prewrite.sh (PreToolUse Write|Edit) ==="
H1="$HOOKS_DIR/check-settings-prewrite.sh"

out=$(write_payload ".claude/settings.local.json" '{"permissions":{"defaultMode":"bypassPermissions"}}' | bash "$H1")
assert_contains     "Hard block: bypassPermissions as string value in Write content" '"continue": false' "$out"

out=$(edit_payload ".claude/settings.local.json" '"bypassPermissions": true' | bash "$H1")
assert_contains     "Hard block: bypassPermissions in Edit new_string" '"continue": false' "$out"

out=$(write_payload ".claude/settings.local.json" '{"permissions":{"allow":["Bash(git:*)"]}}' | bash "$H1")
assert_contains     "Advisory: safe Write to settings file" 'systemMessage' "$out"
assert_not_contains "Advisory must not hard-block" '"continue": false' "$out"

out=$(write_payload "generate.py" 'print("hello")' | bash "$H1")
assert_silent       "Silent: Write to non-settings file" "$out"

out=$(write_payload ".claude/pr-body.md" 'some text' | bash "$H1")
assert_silent       "Silent: Write to .claude/ non-settings file" "$out"

out=$(jq -n '{"tool_input":{}}' | bash "$H1")
assert_silent       "Silent: payload with no file_path" "$out"

# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== check-settings-change.sh (PostToolUse Write|Edit) ==="
H2="$HOOKS_DIR/check-settings-change.sh"

out=$(write_payload ".claude/settings.local.json" '{}' | bash "$H2")
assert_contains     "Advisory: Write to settings.local.json" 'systemMessage' "$out"
assert_not_contains "Advisory must not show hard-block marker" '"continue": false' "$out"

out=$(write_payload ".claude/settings.json" '{}' | bash "$H2")
assert_contains     "Advisory: Write to settings.json" 'systemMessage' "$out"

out=$(write_payload ".claude/settings.local.json" '{"permissions":{"defaultMode":"bypassPermissions"}}' | bash "$H2")
assert_contains     "Loud warning: bypassPermissions written to settings file" 'bypassPermissions was just written' "$out"

out=$(edit_payload ".claude/settings.local.json" '"bypassPermissions": true' | bash "$H2")
assert_contains     "Loud warning: bypassPermissions in Edit new_string" 'bypassPermissions was just written' "$out"

out=$(write_payload "generate.py" 'code' | bash "$H2")
assert_silent       "Silent: Write to non-settings file" "$out"

out=$(write_payload ".claude/pr-body.md" 'text' | bash "$H2")
assert_silent       "Silent: Write to .claude/ non-settings file" "$out"

out=$(jq -n '{"tool_input":{}}' | bash "$H2")
assert_silent       "Silent: payload with no file_path" "$out"

# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== check-bash-settings-write.sh (PreToolUse Bash) ==="
H3="$HOOKS_DIR/check-bash-settings-write.sh"

out=$(bash_payload 'echo {"bypassPermissions":[]} > .claude/settings.local.json' | bash "$H3")
assert_contains     "Hard block: redirect with bypassPermissions" '"continue": false' "$out"

out=$(bash_payload 'echo {"BypassPermissions":[]} > .claude/settings.local.json' | bash "$H3")
assert_contains     "Hard block: BypassPermissions (capital B, case-insensitive)" '"continue": false' "$out"

out=$(bash_payload 'echo {} > .claude/settings.local.json' | bash "$H3")
assert_contains     "Advisory: redirect to settings.local.json" 'systemMessage' "$out"
assert_not_contains "Advisory must not hard-block" '"continue": false' "$out"

out=$(bash_payload 'echo {} >> .claude/settings.json' | bash "$H3")
assert_contains     "Advisory: append redirect to settings.json" 'systemMessage' "$out"

out=$(bash_payload 'tee .claude/settings.local.json < /dev/null' | bash "$H3")
assert_contains     "Advisory: tee to settings.local.json" 'systemMessage' "$out"

out=$(bash_payload "sed -i 's/x/y/' .claude/settings.local.json" | bash "$H3")
assert_contains     "Advisory: sed -i on settings.local.json" 'systemMessage' "$out"

out=$(bash_payload 'cp /tmp/x.json .claude/settings.local.json' | bash "$H3")
assert_contains     "Advisory: cp to relative settings.local.json" 'systemMessage' "$out"

out=$(bash_payload 'mv /tmp/x.json .claude/settings.json' | bash "$H3")
assert_contains     "Advisory: mv to relative settings.json" 'systemMessage' "$out"

out=$(bash_payload 'cp /tmp/x.json /Users/jeroen/lettercards/.claude/settings.local.json' | bash "$H3")
assert_contains     "Advisory: cp to absolute-path settings.local.json (#84)" 'systemMessage' "$out"

out=$(bash_payload 'mv /tmp/x.json /abs/path/.claude/settings.json' | bash "$H3")
assert_contains     "Advisory: mv to absolute-path settings.json (#84)" 'systemMessage' "$out"

out=$(bash_payload 'cat .claude/settings.json' | bash "$H3")
assert_silent       "Silent: cat (read only)" "$out"

out=$(bash_payload 'grep bypassPermissions .claude/settings.json' | bash "$H3")
assert_silent       "Silent: grep (read only)" "$out"

out=$(bash_payload 'git add .claude/settings.json' | bash "$H3")
assert_silent       "Silent: git add (not a write)" "$out"

out=$(bash_payload "git commit -m 'mention bypassPermissions in message'" | bash "$H3")
assert_silent       "Silent: bypassPermissions only in commit message" "$out"

out=$(bash_payload 'echo bypassPermissions > /tmp/other.json' | bash "$H3")
assert_silent       "Silent: bypassPermissions written to non-settings target" "$out"

out=$(jq -n '{"tool_input":{}}' | bash "$H3")
assert_silent       "Silent: payload with no command field" "$out"

# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== session-start-github-check.sh (SessionStart) ==="
H4="$HOOKS_DIR/session-start-github-check.sh"

OWNER_ISSUES=$(jq -n '[{
  "number": 1, "title": "Test issue",
  "comments": [{"author": {"login": "jvspl"}, "body": "Owner comment here"}]
}]')

EXTERNAL_ISSUES=$(jq -n '[{
  "number": 2, "title": "Another issue",
  "comments": [{"author": {"login": "badactor"}, "body": "External comment here"}]
}]')

MIXED_ISSUES=$(jq -n '[{
  "number": 3, "title": "Mixed issue",
  "comments": [
    {"author": {"login": "jvspl"}, "body": "Trusted comment"},
    {"author": {"login": "attacker"}, "body": "Untrusted comment"}
  ]
}]')

out=$(LETTERCARDS_TEST_ISSUES_JSON="$OWNER_ISSUES" LETTERCARDS_TEST_PR_JSON='[]' bash "$H4")
assert_contains     "Session-start: owner comment shown without warning" '💬 @jvspl' "$out"
assert_not_contains "Session-start: owner comment not flagged as external" '⚠️ external comment' "$out"

out=$(LETTERCARDS_TEST_ISSUES_JSON="$EXTERNAL_ISSUES" LETTERCARDS_TEST_PR_JSON='[]' bash "$H4")
assert_contains     "Session-start: external comment flagged with warning" '⚠️ external comment from @badactor' "$out"
assert_not_contains "Session-start: external comment not shown as owner" '💬 @badactor' "$out"

out=$(LETTERCARDS_TEST_ISSUES_JSON="$MIXED_ISSUES" LETTERCARDS_TEST_PR_JSON='[]' bash "$H4")
assert_contains     "Session-start: trusted comment shown in mixed issue" '💬 @jvspl' "$out"
assert_contains     "Session-start: untrusted comment flagged in mixed issue" '⚠️ external comment from @attacker' "$out"

out=$(LETTERCARDS_TEST_ISSUES_JSON='[]' LETTERCARDS_TEST_PR_JSON='[]' bash "$H4")
assert_contains     "Session-start: no-comment state produces header" 'Session start' "$out"
assert_not_contains "Session-start: no spurious warnings on empty issues" '⚠️ external comment' "$out"

DRAFT_PR=$(jq -n '[{"number": 10, "title": "Work in progress", "isDraft": true, "updatedAt": "2026-01-01T00:00:00Z"}]')
out=$(LETTERCARDS_TEST_ISSUES_JSON='[]' LETTERCARDS_TEST_PR_JSON="$DRAFT_PR" bash "$H4")
assert_contains     "Session-start: draft PR shows [DRAFT] label" 'PR #10 \[DRAFT\]' "$out"

NONDRAFT_PR=$(jq -n '[{"number": 11, "title": "Ready PR", "isDraft": false, "updatedAt": "2026-01-01T00:00:00Z"}]')
out=$(LETTERCARDS_TEST_ISSUES_JSON='[]' LETTERCARDS_TEST_PR_JSON="$NONDRAFT_PR" bash "$H4")
assert_contains     "Session-start: non-draft PR has no [DRAFT] label" 'PR #11:' "$out"
assert_not_contains "Session-start: non-draft PR has no [DRAFT] label" '\[DRAFT\]' "$out"

# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== auto-review-on-pr-create.sh (PostToolUse Bash) ==="
H5="$HOOKS_DIR/auto-review-on-pr-create.sh"

pr_payload() {
  jq -n --arg cmd "$1" --arg out "$2" --argjson ec "${3:-0}" \
    '{"tool_input":{"command":$cmd},"tool_response":{"output":$out,"exit_code":$ec}}'
}

out=$(pr_payload "gh pr create --title 'Test' --body-file .tmp/body.md" \
  "https://github.com/jvspl/lettercards/pull/42" 0 | bash "$H5")
assert_contains     "PR create (no draft): fires review" 'PR #42' "$out"

out=$(pr_payload "gh pr create --draft --title 'Test' --body-file .tmp/body.md" \
  "https://github.com/jvspl/lettercards/pull/42" 0 | bash "$H5")
assert_silent       "PR create --draft: silent" "$out"

out=$(pr_payload "gh pr ready 99" \
  "✓ Pull request #99 is marked as ready for review" 0 | bash "$H5")
assert_contains     "gh pr ready with number: fires review" 'PR #99' "$out"

out=$(pr_payload "gh pr ready" \
  "https://github.com/jvspl/lettercards/pull/55 marked ready" 0 | bash "$H5")
assert_contains     "gh pr ready without number: falls back to URL" 'PR #55' "$out"

out=$(pr_payload "gh pr create --title 'Test'" \
  "https://github.com/jvspl/lettercards/pull/42" 1 | bash "$H5")
assert_silent       "PR create failed (exit_code=1): silent" "$out"

out=$(pr_payload "gh issue list" "some output" 0 | bash "$H5")
assert_silent       "Non-PR command: silent" "$out"

out=$(pr_payload "gh pr create --title 'Test'" "error: authentication required" 0 | bash "$H5")
assert_silent       "PR create: no URL in output: silent" "$out"

# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== jq-missing: fail-closed behaviour ==="

out=$(write_payload ".claude/settings.local.json" '{}' | env PATH=/nonexistent /bin/bash "$H1")
assert_contains "H1 (prewrite): hard-blocks when jq is missing" '"continue": false' "$out"

out=$(bash_payload 'echo {} > .claude/settings.local.json' | env PATH=/nonexistent /bin/bash "$H3")
assert_contains "H3 (bash-write): hard-blocks when jq is missing" '"continue": false' "$out"

# H4 jq-missing: hook checks gh first, so we need a mock gh in PATH but no jq
MOCK_BIN=$(mktemp -d)
printf '#!/bin/bash\nexit 0\n' > "$MOCK_BIN/gh"
chmod +x "$MOCK_BIN/gh"
out=$(LETTERCARDS_TEST_ISSUES_JSON='[]' LETTERCARDS_TEST_PR_JSON='[]' env PATH="$MOCK_BIN" /bin/bash "$H4")
rm -rf "$MOCK_BIN"
assert_contains "H4 (session-start): warns when jq is missing (#82)" '⚠️ jq is not installed' "$out"

# ────────────────────────────────────────────────────────────────────────────
echo ""
echo "=== Results ==="
echo "  Passed : $PASS"
echo "  Failed : $FAIL"
echo ""

if [ "$FAIL" -eq 0 ]; then
  echo "All hook tests passed."
  exit 0
else
  echo "$FAIL test(s) failed."
  exit 1
fi

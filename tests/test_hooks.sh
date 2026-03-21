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

out=$(write_payload ".claude/settings.json" '{}' | bash "$H2")
assert_contains     "Advisory: Write to settings.json" 'systemMessage' "$out"

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
assert_contains     "Advisory: cp to settings.local.json" 'systemMessage' "$out"

out=$(bash_payload 'mv /tmp/x.json .claude/settings.json' | bash "$H3")
assert_contains     "Advisory: mv to settings.json" 'systemMessage' "$out"

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
echo "=== jq-missing: fail-closed behaviour ==="
# session-start-github-check.sh is excluded: it calls gh live and cannot be pipe-tested.

out=$(write_payload ".claude/settings.local.json" '{}' | env PATH=/nonexistent /bin/bash "$H1")
assert_contains "H1 (prewrite): hard-blocks when jq is missing" '"continue": false' "$out"

out=$(bash_payload 'echo {} > .claude/settings.local.json' | env PATH=/nonexistent /bin/bash "$H3")
assert_contains "H3 (bash-write): hard-blocks when jq is missing" '"continue": false' "$out"

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

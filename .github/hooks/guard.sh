#!/bin/bash
# Runs before every tool call of a Copilot cloud agent session (.github/hooks/guard.json).
# A deny stops the call before it runs; the reason goes back to the agent.
input="$(cat)"
tool="$(jq -r '.toolName' <<<"$input")"
args="$(jq -r '.toolArgs' <<<"$input")"

deny() {
  jq -cn --arg r "$1" '{permissionDecision: "deny", permissionDecisionReason: $r}'
  exit 0
}

# Security: no destructive commands.
if [ "$tool" = "bash" ] && grep -Eq 'rm -[a-z]*(rf|fr)|git push (-f|--force)|git reset --hard' <<<"$args"; then
  deny "Blocked by guard.sh (security, $tool): destructive command. A person runs it, not the agent."
fi

# Compliance: only Mei (SRE) changes the production configuration and this guard.
case "$tool" in
  edit|create|apply_patch|str_replace_editor) writes=yes ;;
  bash) grep -Eq 'sed -i|>|tee |mv |cp |rm ' <<<"$args" && writes=yes ;;
esac
if [ "$writes" = yes ] && grep -Eq 'config/|\.github/hooks/' <<<"$args"; then
  deny "Blocked by guard.sh (compliance, $tool): config/ and .github/hooks/ change only through Mei (SRE) and a reviewed pull request."
fi
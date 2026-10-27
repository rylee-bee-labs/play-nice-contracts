#!/usr/bin/env bash
# check-generated.sh — every generated file in the repo is current.
#
# Never edits anything: a stale file is reported with the one command that
# regenerates it, and the script exits 1. Used by ./tools/check.sh and CI.
# New generated files add one check here.
set -euo pipefail

cd "$(dirname "$0")/.."
CT="python3 tools/contractctl/contractctl.py"
PN="python3 tools/playnice/playnice.py"
tmp=$(mktemp -d)
trap 'cp "$tmp/lock.orig" contracts.lock.json 2>/dev/null || true; rm -rf "$tmp"' EXIT
stale=0

report() { # report <file> <ok:0|1> <command> [why]
  if [ "$2" = 0 ]; then
    echo "current   $1"
  else
    echo "STALE     $1${4:+ ($4)}"
    echo "          regenerate: $3"
    stale=1
  fi
}

# contracts.lock.json: regenerated twice, byte-compared, then restored.
cp contracts.lock.json "$tmp/lock.orig"
if ! { $CT lock >/dev/null 2>&1 && cp contracts.lock.json "$tmp/lock.1" && $CT lock >/dev/null 2>&1; }; then
  # lock refuses an invalid library; validate names what to fix first
  report contracts.lock.json 1 "$CT validate (fix what it lists), then $CT lock" "library does not validate"
elif ! cmp -s "$tmp/lock.1" contracts.lock.json; then
  report contracts.lock.json 1 "fix contractctl: two regenerations differ" "not deterministic"
else
  rc=0; cmp -s "$tmp/lock.orig" "$tmp/lock.1" || rc=1
  report contracts.lock.json $rc "$CT lock"
fi
cp "$tmp/lock.orig" contracts.lock.json

# CONTRACT_INDEX.md version and status columns.
rc=0; $CT index >/dev/null 2>&1 || rc=1
report "CONTRACT_INDEX.md (version/status columns)" $rc "$CT index --write"

# contracts/<pack>/README.md: the pack cards.
rc=0; $CT cards >/dev/null 2>&1 || rc=1
report "pack cards (contracts/<pack>/README.md)" $rc "$CT cards --write"

# playnice-badge.svg: what `playnice check .` draws today.
$PN check . --badge "$tmp/badge.svg" >/dev/null 2>&1 || true
rc=0; cmp -s "$tmp/badge.svg" playnice-badge.svg || rc=1
report playnice-badge.svg $rc "$PN check . --badge playnice-badge.svg"

# AGENTS.md Play-Nice block (between the play-nice:start/end markers).
$PN check . --json 2>/dev/null > "$tmp/check.json" || true
rc=0
python3 - "$tmp/check.json" <<'PY' || rc=1
import json, sys
checks = json.load(open(sys.argv[1])).get("checks", [])
state = next((c["state"] for c in checks if c["id"] == "agents-file"), "unknown")
sys.exit(0 if state == "healthy" else 1)
PY
report "AGENTS.md (play-nice block)" $rc "$PN start . --no-workflow"

if [ "$stale" = 1 ]; then
  echo "FAIL: generated files are stale; run the commands above and commit the result"
  exit 1
fi
echo "generated files: all current"

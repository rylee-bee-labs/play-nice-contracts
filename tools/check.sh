#!/usr/bin/env bash
# check.sh — the full deterministic gate, one command (mirrors CI's library job).
#
# Usage: ./tools/check.sh          (from a library checkout)
# Exit 0 = everything green. Any failure prints what failed and why.
set -euo pipefail

cd "$(dirname "$0")/.."
CT="python3 tools/contractctl/contractctl.py"

echo "==> validate library + lockfile"
$CT validate

echo "==> lock determinism (regenerate twice, byte-compare)"
tmp1=$(mktemp); tmp2=$(mktemp)
trap 'rm -f "$tmp1" "$tmp2"' EXIT
cp contracts.lock.json "$tmp1"
$CT lock >/dev/null
cp contracts.lock.json "$tmp2"
$CT lock >/dev/null
cmp -s "$tmp1" contracts.lock.json || {
  echo "FAIL: committed lock differs from regeneration — run: $CT lock and commit"; exit 1; }
cmp -s "$tmp2" contracts.lock.json || {
  echo "FAIL: lock regeneration is not deterministic (two runs differ)"; exit 1; }
echo "lock regeneration byte-identical"

echo "==> test suite"
# pytest-xdist is optional: with it the suite runs on every core (about
# 3x faster); without it the same tests run one at a time.
if python3 -c "import pytest, yaml" 2>/dev/null; then
  if python3 -c "import xdist" 2>/dev/null; then
    python3 -m pytest tests/ -q -n auto
  else
    python3 -m pytest tests/ -q
  fi
else
  echo "(pytest/pyyaml not in this interpreter; using uv)"
  uv run --python 3.12 --with pytest,pyyaml,pytest-xdist python3 -m pytest tests/ -q -n auto
fi

echo "==> secret / private-material scan (library surfaces)"
python3 tools/contractctl/contractctl.py scan

echo "==> Play-Nice self-check (what the README badge shows)"
python3 tools/playnice/playnice.py check .

echo "==> commit identity guard (last 20 commits vs allowed classes)"
# Mirrors CI's guard: a commit whose committer is exactly the GitHub
# wrapper (noreply@github.com) is skipped wholesale — its author email was
# checked when the PR event ran, and wrapper authors come from account
# settings, not local git config.
BAD=$(git log -20 --format='%ae %ce' | awk \
      '$2=="noreply@github.com"{next} {print $1; print $2}' | sort -u \
      | grep -Ev '@users\.noreply\.github\.com$|@[A-Za-z0-9.-]*[.]invalid$' || true)
if [ -n "$BAD" ]; then
  echo "FAIL: disallowed identity emails in recent history:"; echo "$BAD"; exit 1
fi
echo "identity guard: all recent emails noreply/.invalid"

echo ""
echo "CHECK: PASS"

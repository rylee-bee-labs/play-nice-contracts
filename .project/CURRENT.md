# CURRENT — play-nice-contracts

> **Live state** (last commit, CI on main, open PRs, recent merges, missions): `lab enter` at session start, or `now-block --print .` from this repo. This file keeps only what a command cannot tell you.

Notes below are hand-written: decisions in flight, why something is paused, what to read first.

## Direction

The plan is [docs/decisions/2026-10-26-play-nice-neat.md](../docs/decisions/2026-10-26-play-nice-neat.md):
2.1.0 tidy and self-running, 2.2.0 pack cards + site + uv install, 3.0.0 one
command. Check its status line before starting milestone work.

## Start here (cold session)

- Read `AGENTS.md`, then `docs/MAINTAINING.md` → "Start here" (proof line,
  change flow, the recipe for changing a contract).
- Branch, pull request, Rylee approves. Never push `main`.

## Verify

- `./tools/check.sh` must print `CHECK: PASS`; it runs what CI runs.
- Cloud sessions get pytest, pytest-xdist and pyyaml from the SessionStart
  hook (`.claude/hooks/session-start.sh`); elsewhere, `pip install` them.

## Generated files

Never edit these by hand: `contracts.lock.json`, the version and status
columns of `CONTRACT_INDEX.md`, the `play-nice` block in `AGENTS.md`,
`playnice-badge.svg`, and anything between `docsgen` markers. The table in
`docs/MAINTAINING.md` → "Generated files" names the command for each.

## Open decisions

Rylee decides; delete a line when it is settled. Settled on 2026-10-26 and
merged: #87 to #91 (enforcement, bump, scanner hash, setup hook, contract
wording and triggers, one default set, status words, shared helpers).

- **Release tags:** tag `v2.0.0` at the #38 merge, then cut 2.1.0 (part of
  the 2.1.0 milestone). Ask Rylee before any tag is pushed.
- **Plan questions** in docs/decisions/2026-10-26-play-nice-neat.md: GitHub
  Pages, how a uv/pipx install finds the contracts, when to cut 3.0.0,
  milestone issues.
- **Small follow-ups seen in review, not yet asked:** `human`/`service` role
  sets could include the four everyone basics; `playnice work` still prints
  its own status words; `playnice check` reads only `.contracts/adoption.yaml`
  (not `.project/contracts/`); `index --write` could also repair Title and
  Purpose cells.

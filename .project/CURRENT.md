# CURRENT — play-nice-contracts

> **Live state** (last commit, CI on main, open PRs, recent merges, missions): `lab enter` at session start, or `now-block --print .` from this repo. This file keeps only what a command cannot tell you.

Notes below are hand-written: decisions in flight, why something is paused, what to read first.

## Start here (cold session)

- Read `AGENTS.md`, then `docs/MAINTAINING.md` → "Start here" (proof line,
  change flow, the recipe for changing a contract).
- Branch, pull request, Rylee approves. Never push `main`.

## Verify

- `./tools/check.sh` must print `CHECK: PASS`; it runs what CI runs.
- In a fresh cloud container, first: `pip install pytest pytest-xdist pyyaml`
  (no SessionStart hook does this yet; see Open decisions).

## Generated files

Never edit these by hand: `contracts.lock.json`, the version and status
columns of `CONTRACT_INDEX.md`, the `play-nice` block in `AGENTS.md`,
`playnice-badge.svg`, and anything between `docsgen` markers. The table in
`docs/MAINTAINING.md` → "Generated files" names the command for each.

## Open decisions

From the 2026-10-26 review (PR `claude/effortless-maintenance`). Rylee decides;
delete a line when it is settled.

- **Tag a release.** There are no git tags, so the generated CHANGELOG
  block and RELEASE_NOTES.md call everything "unreleased 0.1.0" while
  `VERSION` is 2.0.0. Tagging `v2.0.0` (or the next version) fixes both.
- **Scanner pattern list.** `SCAN_PATTERNS` in contractctl spells out a
  private domain in this public repo. Option: match a hash of the domain
  instead of the text. A security-boundary change, so not done unasked.
- **SessionStart hook** for cloud sessions (installs the test tools so
  `./tools/check.sh` runs at once). Writing `.claude/settings.json` needs
  Rylee's go-ahead.
- **contract-proof wording** (PATCH): rule 5 and the machine notes say the
  badge always links to a check run and that `playnice check` writes the
  badge, and point at docs/PLAYNICE.md for the legacy gate. None of these
  is quite true (see docs/MAINTAINING.md).
- **Trigger gaps** (PATCH each): `playnice rules "build a website"` misses
  accessibility and plain-language; "docs" misses plain-language.
- **One default contract set.** With no manifest the agent default set
  includes contract-proof; `init-adoption`'s set does not.
- **`playnice check` status words** (`worked`, `needs_fix`, `skipped`)
  are not the shared status words (floor rule 8).
- **Duplicate helpers** between playnice and contractctl (YAML parsing,
  floor/receipt reading, remote URL) have started to drift.

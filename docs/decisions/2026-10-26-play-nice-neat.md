# Decision: Play-Nice, neat — smaller, one front door, lovely, runs itself

Date: 2026-10-26. **Status: Approved** (PR #92, merged 2026-10-26). The
owner chose every direction below in an interactive review on this date.
Each milestone still lands as its own reviewed PRs.

## In short

Play-Nice is built for the owner's own repos and agents first, and kept clean
enough that anyone could adopt it. "Neat" means four things at once: **smaller**
(less to read and keep up), **one front door** (one command, one page),
**lovely** (a polished, accessible site generated from the contracts), and
**runs itself** (releases, generated files and health checks are automatic; the
owner only reviews). No contract rule changes to get there.

## Starting point (2026-10-26)

- Two tools: `playnice` (front door) and `contractctl` (24 commands, four of
  them the retired attest/commit gate).
- 41 contracts in 7 packs; only the floor reads as one page. The rest are
  reached one file at a time through the index or `playnice rules`.
- History and research (`docs/background/`, `harness/`, `profiles/`) sit
  beside the product, plus 21 one-line "Moved to" pointer files promised for
  removal in 2.1.0.
- No release tags: the generated changelog calls everything "unreleased 0.1.0"
  while `VERSION` is 2.0.0.
- Install is clone + symlink.
- In flight: PRs #88–#91 (scanner hash, setup hook, contract wording and
  triggers, contractctl hardening, playnice status words and dedupe).

## What we are building

### 2.1.0 — Tidy and self-running

1. **Faster tests:** one shared `tests/conftest.py`, one light repo copy
   per test.
2. **Trim history in place:**
   - delete the 21 pointer files;
   - move `harness/` under `docs/background/`, which keeps one short
     index of everything there;
   - move `profiles/` to `examples/profiles/` (it stays MIT). *Amended
     2026-10-26: the owner chose this split so the move changes no file's
     license; the first text moved both under `docs/background/`.*
3. **Release automation:**
   - merging a `VERSION` bump tags `vX.Y.Z`;
   - it publishes a GitHub release from the `[Unreleased]` changelog
     section, which then resets.
4. **Generated files checked in CI:** lock, index columns, AGENTS block
   and badge (later also pack cards and site). CI fails with the one
   command that regenerates the stale file.
5. **Weekly health check:**
   - a scheduled run of the full gate plus a link check;
   - it opens one issue only when something breaks, and stays quiet
     when everything is fine.
6. **Release:**
   - tag `v2.0.0` at the #38 merge;
   - cut 2.1.0 from everything since.
   - The owner says yes before any tag is pushed.

### 2.2.0 — One front door, lovely

1. **Pack cards:**
   - for each pack, a generated one-page card like the floor: every
     contract's "In short" and its MUST rules, linking to the full text;
   - generated from the contracts, so the cards cannot drift.
2. **Site:**
   - a stdlib-only generator builds a GitHub Pages site from `contracts/`;
   - the home page is the floor plus a three-line start;
   - one page per pack (the card), with JSON beside every page;
   - a verify page: paste a proof line, get CURRENT / OUT OF DATE;
   - the site's own `/.well-known/play-nice.json`, so it passes
     `playnice check <url>`;
   - dark theme, reduced motion, keyboard-first, Buzzby's voice where it
     helps;
   - it dogfoods `friendly-site` and `one-truth-two-views`.
3. **Install with uv or pipx:**
   - `uv tool install git+https://github.com/rylee-bee-labs/play-nice-contracts`
     gives a `playnice` command;
   - runtime stays stdlib-only, and `pyproject.toml` gains a build table.

### 3.0.0 — One command

1. **`playnice` carries everything:** the everyday commands at the top,
   and the maintainer commands under `playnice library …` (validate, bump,
   lock, index, diff, scan, …).
2. **`contractctl` becomes a thin alias** so pinned adopters keep working.
3. **The legacy attest/commit gate is removed.** Projects that need it stay
   on 2.x. This is the only breaking change, and the reason for the major
   version.

## Not doing (chosen against, 2026-10-26)

- **A GitHub Action for adopters:** not chosen. `playnice start` keeps
  writing a small workflow.
- **Consolidating contracts into fewer, larger ones:** pack cards give the
  one-page view without a governance change.
- **Moving history to a separate repository:** trimmed in place instead.

## Open questions for the owner

- **Turning on GitHub Pages** is a repository setting. The owner flips it,
  or approves it being flipped, when the site PR is ready. It is free for
  a public repository. *2026-10-27: the site PR is up; the workflow
  publishes once Settings → Pages → Source is "GitHub Actions".*
- **How the uv/pipx install finds the contracts:** ship them inside the
  tool, or fetch them into `~/.cache/play-nice` as `playnice` already does
  for adopters? Recommendation: fetch, so a tool install never pins stale
  rules. Decide in the 2.2.0 PR.
- **When to cut 3.0.0:** recommendation is after 2.2.0 has run on the
  owner's repos for a while.
- **Roadmap issues:** whether to open one GitHub issue per milestone so the
  generated `ROADMAP.md` shows this plan (it is built from open issues).

## How we will know it worked

- A cold session goes from clone to a green `./tools/check.sh` with no
  manual install, and from a task to a valid proof line with
  `playnice rules` + `playnice verify` only.
- Top level shows the product (contracts, tools, docs, schema, tests) and
  little else.
- Nothing generated is ever edited by hand: CI says so when it is.
- A release is one merged PR, with no hand-made tag.
- The site passes `playnice check <url>` and the floor's accessibility
  rules.

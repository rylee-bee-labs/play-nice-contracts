# Maintaining the Play-Nice library

> **Status:** Current · for people and agents changing this library, not for
> people using it. Using Play-Nice in your project? Start at
> [the floor](../contracts/everyone/FLOOR.md).

## Start here

1. **Start with the proof line.** Run `playnice rules "<task>"` to list the
   contracts that apply, read them and the floor, then write
   `Play-Nice floor <version> · receipt <word> · read <ids>` at the top of
   your handoff and check it with `playnice verify "<line>"`
   ([contract-proof](../contracts/work/CONTRACT_PROOF.md)). The old
   attest/commit gate is retired for new work; see [Legacy](#legacy-the-attestcommit-gate).
2. **Branch, pull request, Rylee approves.** Never push to `main`.
3. **Done means `./tools/check.sh` prints `CHECK: PASS`.** It runs what CI
   runs. Cloud sessions install the test tools through the SessionStart hook;
   elsewhere, first: `pip install pytest pytest-xdist pyyaml`.
4. **Changing a contract?** Follow the recipe below.

### Changing a contract

Edit the text first, then let `contractctl bump` do the bookkeeping.

| Change | Steps |
|---|---|
| **A. Wording fix**: PATCH, same meaning | edit → `contractctl bump <id> --patch` → `./tools/check.sh` |
| **B. New or changed rule**: MINOR; MAJOR if it breaks existing users | edit → `contractctl bump <id> --minor --note "what changed"` (or `--major`) → `./tools/check.sh` |
| **C. New contract** | see below |
| **D. Floor change** | see below |

`contractctl bump <id> --patch|--minor|--major [--note "what changed"]`
sets the new version in the contract's front matter. For `--minor` and
`--major` it also picks a new receipt word the library has never used, and
requires `--note`, which it adds as a bullet under `## [Unreleased]` in
`CHANGELOG.md` (for `--patch` the note is optional). It then refreshes the
version column in `CONTRACT_INDEX.md` and regenerates `contracts.lock.json`.

**C. New contract.** Copy an existing contract in the same pack as a
template and save it as `contracts/<pack>/<ID_UPPER>.md`.

- Front matter: `contract_id`, `title`, `version: 1.0.0`,
  `status: canonical`, `layer` (the pack folder name), `applies`,
  `triggers`, `rationale`.
- One receipt line: `<!-- contract-receipt: word-word-word -->` (three
  lowercase words, not used by any other contract).
- Sections: In short · Applies when · Rules · Examples · Why · You're done
  when · Machine notes.
- `contractctl index --write` adds its row to its pack's table in
  `CONTRACT_INDEX.md` (title, version, status, and the rationale as the
  Purpose).
- `contractctl lock`, commit, `./tools/check.sh`.

**D. Floor change.** Edit `contracts/everyone/FLOOR.md` →
`contractctl bump floor --minor --note "what changed"` →
`playnice start . --no-workflow` (rewrites this repo's AGENTS.md block and
badge; `--no-workflow` because the library has its own CI) →
`./tools/check.sh` (`tests/test_doc_facts.py` names every proof-line
example and version still on the old floor; the example in
`contracts/work/CONTRACT_PROOF.md` is contract text, so it needs its own
`bump contract-proof --patch`). Every
floor version change makes all adopters' proof lines and badges read
"behind". That is by design: it is how they learn to re-read.

**Removing or renaming a contract:** add the old id to `aliases.json` and to
the "Old names" table in `CONTRACT_INDEX.md`, so old proof lines and links
keep working.

**How changes are checked.** `contractctl validate --base <rev>` compares
contracts with a base revision: by default the merge-base of `HEAD` and
`origin/main` (or `HEAD` when there is no `origin/main`); CI passes the pull
request's base commit. `PLAY_NICE_BASE` does the same as `--base`. It
fails when a contract's content changed without a version bump, when a
MINOR or MAJOR bump kept its receipt word, or when a MINOR or MAJOR bump has
no new `[Unreleased]` changelog bullet naming the contract. It also checks
each contract's pack folder and sections, that its index row matches its
front matter and sits in its pack's table, and that `aliases.json` matches
the index's "Old names" table. Errors from
`validate`, `lock` and `index` end with a `next:` line naming the command
that fixes them.

## Generated files

Never edit these by hand; run the command instead.

| File | Written by |
|---|---|
| `contracts.lock.json` | `contractctl lock` (also `bump`) |
| `CONTRACT_INDEX.md` missing rows, and the version and status columns | `contractctl index --write` (also `bump`, for the columns) |
| AGENTS.md, between `<!-- play-nice:start -->` and `<!-- play-nice:end -->` | `playnice start .` |
| `playnice-badge.svg` | `playnice check . --badge playnice-badge.svg` |
| `docsgen` blocks in README, CHANGELOG, ROADMAP, RELEASE_NOTES | `lab docs gen` (outside this repo) |

Hand-written changelog entries go under the hand-written `## [Unreleased]`
heading, below the generated block, never under the generated
`## Unreleased`.

## Outside this repo

These live in Rylee's wider workspace and are not installed in cloud
sessions.

- **`lab docs gen`** writes the `docsgen` blocks from merged PRs, releases
  and issues.
- **`lab enter`** and **`now-block --print .`** print live state (last
  commit, CI on main, open PRs) at session start; `.project/CURRENT.md`
  points to them.
- **ci-harness**: `.github/workflows/secret-scan.yml` calls the estate's
  reusable secret scan (gitleaks) from `rylee-bee-labs/ci-harness`, pinned
  to a commit SHA. Dependabot proposes updates to the pin.
- **pin-sync** (`tools/pin-sync/`): a script plus a systemd user timer for
  Rylee's machine. When `main` moves, it opens a pin-update PR in each
  adopting repo. See [its README](../tools/pin-sync/README.md).

## Rules for agents working here

**What this repo is:** the canonical contract library: the normative text
(`contracts/`), its JSON Schemas (`schema/`), and the stdlib-only tools
that check and lock them (`tools/contractctl`, `tools/playnice`). Other
repos pin revisions of it, so changes here ripple outward. Reference
contract text from other repos; never copy it. It is not its own
governance body: contract changes are proposals that Rylee reviews.

- **Standard library only.** Tools import nothing beyond Python 3.10+'s
  standard library (CI tests 3.10 to 3.12). `pyproject.toml` only declares
  test extras. Adding a runtime dependency is a decision for Rylee.
- **Contract text is the product.** State your intent and show the diff
  before rewriting normative language, and follow [the recipe](#changing-a-contract).
- **Changelog.** Every landed change gets a bullet under `## [Unreleased]`
  in `CHANGELOG.md`, docs and licensing changes too. Bump `VERSION` only for
  a library release.
- **This repo is public.** No real tokens, hostnames, private IPs, family
  details or personal medical history, anywhere. `contractctl scan` and the
  secret-scan workflow check for them. Keep `profiles/examples/` shaped as
  preferences, not personal records.
- **Commit emails are checked.** Only `*+*@users.noreply.github.com` or
  `*@*.invalid` author and committer emails may enter history; the CI
  identity guard fails on anything else. GitHub's own merge commits
  (committer `noreply@github.com`) are exempt.
- **Merging.** Merge only after Rylee's explicit approval in the task. Her
  token cannot approve its own PR, so an admin merge *with that approval*
  is the sanctioned path; say so in the PR. Never use admin bypass she did
  not grant for that change, and never to push `main` directly.
- **Evidence over memory.** Check counts, versions, receipts and history
  against this checkout and live CI. Prefer writing no count over one that
  can rot.
- **Project Worlds** characters and world content have a different license
  and home and must never appear here. No scanner checks for this.

## Licensing map

Contract text and docs: **CC BY-SA 4.0**. Tools, schemas, lockfile and
tests: **MIT**. Name and identity: `TRADEMARKS.md` (the bee acknowledgement
is optional credit, never endorsement). `tests/test_license_map.py` checks it.

## What governs what

| Path | What it is | Change kind |
|---|---|---|
| `contracts/` | the normative text, this library's product | recipe above |
| `schema/` | machine shapes for contracts and manifests | governance change |
| `CONTRACT_INDEX.md`, `aliases.json` | routing and old names; does not govern | with contracts |
| `tools/` | `contractctl`, `playnice` ([PLAYNICE.md](PLAYNICE.md)), `pin-sync` | code; tests accompany it |
| `tests/` | hermetic suite | with every change |
| `docs/` | non-normative guides and decision records | prose; never above `contracts/` |
| `docs/background/` | the Opus, principles, roles, research; old paths keep one-line pointers | prose; never above `contracts/` |
| `harness/` | **experimental** research: hypotheses with evidence, not rules | evidence only |
| `profiles/`, `examples/` | preference layer and real adoption manifests | keep schema-valid |
| `LICENSE`, `contracts/LICENSE.md`, `docs/LICENSE.md`, `SECURITY.md`, `TRADEMARKS.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS` | licensing, threat model, identity, review | Rylee reviews |

## Running the tools and tests

`contractctl` and `playnice` are files, not installed commands. Run
`./tools/contractctl/contractctl` (or `python3 tools/contractctl/contractctl.py`);
the same goes for `./tools/playnice/playnice`. There is no installer by
design. `contractctl --help` lists its commands in groups: everyday,
adopters, and the legacy gate.

```bash
./tools/check.sh                      # everything CI runs
python3 -m pytest tests/ -q -n auto   # tests only; -n auto (pytest-xdist) is optional
# the same, without touching the system Python:
uv run --python 3.12 --with pytest,pyyaml,pytest-xdist python3 -m pytest tests/ -q -n auto
```

## Versioning

`VERSION` describes the contract content; a Git revision pins the exact
commit a project adopted. `contracts.lock.json` records each contract's id,
version, path, SHA-256, receipt and status; CI regenerates it twice and
fails if either differs from the committed file. Every version number:
the README's [version table](../README.md#version-numbers).

## CI and branch protection

`.github/workflows/ci.yml` runs on every push and PR. The `library` job runs
once per Python version (3.10 to 3.12): commit identity guard, workflow
YAML check, `contractctl validate`, lock determinism, the full suite,
`contractctl scan`, and `playnice check .`. A gate job, also named
**`library`**, passes only when every run passed; branch protection
requires that name. `.github/workflows/secret-scan.yml` runs gitleaks
through ci-harness.

`main` protection requires a PR, one approving review (stale reviews
dismissed), the `library` check and an up-to-date branch, and forbids
force pushes and deletion. Check it live before relying on it:
`gh api repos/rylee-bee-labs/play-nice-contracts/branches/main/protection`.

## This repo adopts itself

`.contracts/adoption.yaml` has `source.self: true`. A commit cannot pin its
own SHA, so the pin is checked by ancestry instead:

- `playnice check .` passes when the pin is a commit in this checkout's
  history, and fails when it is not (for example a branch commit that a
  squash merge threw away).
- `contractctl freshness` reads CURRENT when the pin is in remote `main`'s
  history and this checkout contains remote `main`. BEHIND means pull;
  DIVERGED means merge `main`, or re-pin to a commit on `main`.
- `source.self` is honored only in the library's own manifest; other
  adopters keep the strict pin check.

The pin never needs bumping after a merge; re-pin only to a commit already
on `main`. A test keeps the committed `playnice-badge.svg` equal to
`playnice check .`, so the README badge says what the check says.

## The orchestrator (`playnice work`)

`playnice work` runs a unit of agent work end to end for orchestrators:
freshness, carryover, the legacy gate (below), a work permit, the agent,
then verify and handoff. It treats the commands in AGENTS.md's `## Verify`
section as the definition of done. Exit codes: `0` ok · `1` empty task or
unexpected internal error · `2` fail closed, or a command-line usage error
(argparse) · `3` agent failed · `4` needs help. Full reference:
[PLAYNICE.md](PLAYNICE.md).

## Legacy: the attest/commit gate

Retired for new work by [contract-proof](../contracts/work/CONTRACT_PROOF.md)
rule 10. It stays documented for projects that pinned it before v2, and
because `playnice work` still runs it internally. `contractctl resolve` is
still current: it answers which rules apply to a task.

```text
REMOTE FRESHNESS → RESOLVE → READ → VERIFY version, hash, receipt →
IMPACT → ATTEST (CONTRACT GATE: PASS) → COMMIT (CONTRACT COMMITMENT: ACTIVE) → WORK
```

```bash
contractctl freshness   # CURRENT expected
contractctl resolve --manifest .contracts/adoption.yaml --task "<task>"
# read each resolved contract's file, then:
contractctl attest --manifest .contracts/adoption.yaml --task "<task>" --impact <id>="<sentence>" ...
contractctl commit --manifest .contracts/adoption.yaml --task "<task>" --impact <id>="<sentence>" ...
```

Commitment files land in `.contracts/sessions/` (gitignored; never commit
them). Neither the gate nor the commitment is permission; authority comes
from the task.

**Remote freshness.** A manifest can set
`freshness: {policy: require-current, ref: main, update: review|automatic}`
(the default policy is `pinned`). `contractctl` then queries the remote with
`git ls-remote` before resolving; a local checkout or "I checked GitHub" is
not evidence.

- `UNKNOWN` or `UNREACHABLE` → commitment INACTIVE (fail closed). `BEHIND`
  or `DIVERGED` → STALE: update, then resolve, read, attest and commit again.
- `contractctl sync` refreshes the pin per `update`: `review` blocks until
  someone reviews; `automatic` refreshes it but still forces a fresh cycle.
- With `update: automatic`, freshness reads CURRENT when the pin and the
  checkout are both ancestors of the remote and `contracts/` and `schema/`
  are byte-identical across all three. Commitments record this as
  `freshness.equivalence`.
- `contractctl diff --from <pin> --to <rev>` shows what changed between two
  revisions, including receipt rotations.

# Maintaining the Play-Nice library

> **Status:** Current · for people changing this library, not for people using it.
> Using Play-Nice in your project? Start at [the floor](../contracts/everyone/FLOOR.md).

The legacy `contractctl` attest/commit gate below still works for projects
that pinned it; v2 replaces it with the one-line proof in
[contract-proof](../contracts/work/CONTRACT_PROOF.md).

## The contract gate (session prefix)

Substantial work starts with the complete preflight:

```text
REMOTE FRESHNESS (require-current only)
        (contractctl freshness — verify the authoritative remote revision)
                ↓
RESOLVE APPLICABLE CONTRACTS → READ CANONICAL SOURCES →
VERIFY VERSION + HASH + RECEIPT → TASK-IMPACT ACKNOWLEDGEMENT →
CHECK FOR CONFLICTS → CONTRACT ATTESTATION →
OPERATIONAL COMMITMENT → CONTRACT COMMITMENT: ACTIVE →
MUTATING WORK MAY BEGIN
```

The three stages mean: receipt = "I obtained the lesson"; attestation = "I know this lesson applies here"; commitment = "I will use this lesson while I work." For substantial mutating work, BOTH `CONTRACT GATE: PASS` and `CONTRACT COMMITMENT: ACTIVE` are required before implementation. The commitment is an operating state, not ceremony: tooling uses it as an execution gate, stale bundles invalidate it, scope changes force re-resolution, and workers inherit the parent's bundle (they may strengthen, never weaken, the applicable constraints). Full prefix: `examples/session-handoff.md`. Neither gate nor commitment is ever authorization — authority comes from the task and the Authorization contract.

## Remote freshness (require-current)

A project can opt into **current contracts** in its adoption manifest:

```yaml
schema: play-nice/adoption-v1
source:
  repository: rylee-bee-labs/play-nice-contracts
  revision: <reviewed SHA>
freshness:
  policy: require-current   # pinned (legacy default) | require-current
  ref: main                 # authoritative branch
  update: review            # review (block, ask for review) | automatic (refresh pin, still re-commit)
```

Under `require-current`, `contractctl` deterministically checks the authoritative remote (`git ls-remote`) BEFORE the resolve/read/attest stages:

```text
REMOTE FRESHNESS → RESOLVE → READ → VERIFY → ATTEST → COMMIT → MUTATE
```

- a local checkout, the adoption pin, a previous session, or "I checked GitHub" is **not** proof of remote freshness — the remote is actually queried;
- `UNKNOWN`/`UNREACHABLE` → `CONTRACT COMMITMENT: INACTIVE` (fail closed); `BEHIND`/`DIVERGED` → `STALE`, requiring fetch/update → resolve → read → attest → commit again;
- a changed authoritative revision invalidates existing commitments (re-resolve, re-attest, re-commit);
- `contractctl sync` refreshes the pin per the update policy — **checking for the newest revision is not the same as silently adopting it**; `update: review` blocks mutation pending explicit review, and even `automatic` still forces a fresh resolve/read/attest/commit cycle;
- **equivalence rule** (`update: automatic` only): when both the adopted pin and the local checkout are provable ancestors of the remote and `contracts/` + `schema/` are byte-identical across all three, freshness reads CURRENT despite post-merge docs/tooling commits ahead of the pin. Any difference in the normative surfaces, or unverifiable history, stays BEHIND — fail closed. This ends the post-merge pin treadmill without weakening review; commitment artifacts record `freshness.equivalence` so equivalence-CURRENT is distinguishable from exact-match CURRENT. `contractctl diff --from <pin> --to <rev>` answers "what actually changed between my pin and current?" including receipt rotations and always-set impact.

## The playnice orchestrator (`playnice work`)

`playnice` is the global agent-work entry point: take a task, fetch/refresh remote Play Nice contracts, reconcile carryover, pass the contract gate, issue a work permit, launch the agent, then verify and write a durable handoff — one command, no prompts required:

```bash
python3 tools/playnice/playnice.py work --repo ~/code/your-repo "implement the feature"
playnice status --repo ~/code/your-repo       # what state is this repo in?
playnice reconcile --repo ~/code/your-repo    # clean up merged work, refresh pins
```

- **Fail closed on UNKNOWN.** No adoption manifest, no freshness evidence, no permit → no work, no mutation. Freshness and carryover use the exact vocabularies `CURRENT/BEHIND/DIVERGED/UNREACHABLE/UNKNOWN` and `DONE/MERGED/CLOSED/STILL_ACTIVE/DEFERRED/WAITING_FOR_HELP/UNKNOWN/BLOCKED`.
- **Two-layer commitment.** The orchestrator computes a deterministic task-impact permit floor; the executing agent does its own worker attestation via `contractctl` and inherits the parent's constraints (worker packet: `INHERITED_CONTRACT_BUNDLE`, `PLAY_NICE_SOURCE_REVISION`, `PARENT_CONTRACT_COMMITMENT`).
- **Automation is explicit opt-in.** Automation runs only with both a global config grant (`~/.config/play-nice/global.yaml`, or `PLAY_NICE_CONFIG`/`--config`) and an ACTIVE permit; `reconcile` revalidates liveness with `contractctl session-status` before any mutation.
- **Deterministic, no live network.** Tests run against local bare remotes and a fake `gh` (`PLAY_NICE_GH`); nothing in the pipeline requires the network.
- Exit codes: `0` ok · `1` usage/internal · `2` fail-closed · `3` agent failed · `4` needs help (human attention, safely deferred).

Full reference: [`docs/PLAYNICE.md`](PLAYNICE.md) · config schema: [`schema/global-playnice.schema.json`](../schema/global-playnice.schema.json) · examples: [`examples/global-playnice.yaml`](../examples/global-playnice.yaml).

## Versioning

Per-contract semver: PATCH = clarification, MINOR = compatible new rule, MAJOR = incompatible change. Library semver (VERSION) is distinct from the adopted Git revision: the version describes contract content, the revision pins the exact adopted commit. `contracts.lock.json` pins id, version, path, SHA-256, receipt, and status; lock drift is detected deterministically and attestations fail closed on it. A commitment's bundle identity represents the **resolved contract set** for its task — different scopes, different bundles — and stale bundles invalidate commitments. Bundle receipts (e.g. `cedar-lantern-47`) are identifiers, never credentials or authorization.

## Tests

```bash
python3 -m pytest tests/ -q    # what CI runs, after pip install pytest pyyaml
```

One-command local equivalent without polluting the system Python:

```bash
uv run --python 3.12 --with pytest,pyyaml python3 -m pytest tests/ -q
```

The full suite covers: library invariants, resolution, attestation/commitment machinery, receipt-rotation enforcement, ask-for-help + question schema, the project-context/participant-pack framework, participation-and-contribution (right-sized participation, honest refusal), mutual-contribution (the agreement loop, authority separation), and collaborative-good-faith (critique toward repair, safe uncertainty, foreman disagreement integration, no moderation machinery).

## Privacy / repository state

This repository is **public**. It is published sanitize-first: no credentials, private endpoints, personal topology, or private medical history — enforced by a canary test that runs locally and in CI. Sensory-safe/low-vision/attention requirements stand as engineering requirements with no personal context attached; the profile under `profiles/examples/` is a presentation-preferences example, not a personal record. Keep the repo publishable by construction, not by later scrub.

## CI / branch protection

CI (`.github/workflows/ci.yml`) runs on every push and PR. The `library` job runs once per Python version (3.10–3.12): commit identity guard, workflow-YAML self-validation, `contractctl validate`, byte-identical lock determinism, the full test suite, and the secret/private-material scan. A separate gate job, also named **`library`**, passes only when every matrix run passed; that single name is what branch protection requires.

`main` branch protection is **configured** (verified live):

- require pull request before merging; ≥1 approving review; stale reviews dismissed
- require status check **`library`** (the actual job name) and branches up to date
- force pushes disallowed; deletions disallowed

Admin reality: the owner's token bypasses protection (GitHub also
forbids self-approval on a single-maintainer repo), so one approved
agent-side admin *merge* is the sanctioned close when the owner has
explicitly approved merging in-task — as happened for PR #17. Bypass
is never used silently, and never for a direct push.

Contract text changes: lockfile regeneration ships in the same commit (`contractctl lock`) — CI's determinism check fails otherwise. Meaningful contract changes (MINOR/MAJOR) must rotate the hidden receipt — `contractctl validate` enforces this from Git history.

## Rules for agents changing this library

(Moved from the root AGENTS.md, which is now a short signpost.)


> **Using Play-Nice in your own project? This file is not for you.** Read
> [the floor](../contracts/everyone/FLOOR.md) and the pack for what you're
> building ([index](../CONTRACT_INDEX.md)). This file is for agents and people
> who edit this library itself.

**What this repo is:** the canonical Play-Nice contract library — the
normative contract text (`contracts/`), its JSON Schemas (`schema/`),
and the stdlib-only reference tooling that resolves, validates, locks,
attests, and commits them (`tools/contractctl`, `tools/playnice`).
Consumer repos pin revisions of this library in adoption manifests, so
changes here ripple outward. This repo is the source of truth; never
copy contract text into other repos, reference it instead.

**What this repo is not:** a service, a framework, or the home of any
consumer project's local rules. It is not its own governance body —
contract changes are proposals reviewed by Rylee, not self-appointed.
Project Worlds characters and world content have a different license
and a different home: they must never appear in this public repository.
(Prose rule — no scanner checks for it; machines can't yet recognize a
character. Don't be the one who proves it wrong.)

## Licensing map (test-enforced: `tests/test_license_map.py`)

- contracts + docs text: **CC BY-SA 4.0** (attribution required;
  derivatives of the text stay open; your code unaffected)
- tooling, schemas, lockfile, tests: **MIT**
- name and identity: `TRADEMARKS.md` (descriptive; 🐝 acknowledgement
  is optional credit, never endorsement)

## How to run `contractctl`

`contractctl` is **a file, not an installed command**. Everywhere in
this repo's docs, `contractctl` means either the executable shim or the
Python file directly (identical behavior — the shim execs the file):

```bash
./tools/contractctl/contractctl             # from a library checkout
python3 "$PLAY_NICE_LIBRARY/tools/contractctl/contractctl.py"  # as a consumer
```

Consumers typically `alias` it once. There is no installer by design
(stdlib-only). The same applies to `./tools/playnice/playnice`.
One-command local verify (mirrors CI): `./tools/check.sh`.

## What governs what

| Surface | Nature | Change kind |
|---|---|---|
| `contracts/` | the normative text — this library's product | governance change |
| `schema/` | machine shapes for contracts and manifests | governance change |
| `contracts.lock.json` | generated; never hand-edited | regenerate via `lock` |
| `CONTRACT_INDEX.md` | registry: routes, does not govern | maintain with contracts |
| `tools/contractctl/`, `tools/playnice/` | reference CLI + orchestrator (`docs/PLAYNICE.md`) | code change |
| `tests/` | hermetic suite (CI job name is `library`) | must accompany changes |
| `docs/` | non-normative: principles, quick reference, research | prose; never above `contracts/` |
| `harness/` | **EXPERIMENTAL** research — candidate laws are hypotheses with evidence, NOT rules | evidence changes only |
| `profiles/`, `examples/` | preference layer + real adoption manifests | keep schema-valid |
| `VERSION`, `CHANGELOG.md` | library semver, distinct from git revision pins | bump per release rules |
| `LICENSE`, `contracts/LICENSE.md`, `docs/LICENSE.md`, `SECURITY.md`, `TRADEMARKS.md`, `CONTRIBUTING.md`, `.github/CODEOWNERS` | licensing, threat model, identity, review intent | Rylee-review required |

## The contract gate is dogfooded here

This repo adopts its own library via `.contracts/adoption.yaml`, marked
`source.self: true`. A commit cannot pin its own SHA, so a pin that had
to equal HEAD would be stale again after every merge. Self-adoption is
checked by ancestry instead:

- `playnice check .` passes when the pin is a commit in this checkout's
  history. It fails when the pin is not a commit here (for example a
  branch commit that a squash merge threw away) or is off this history.
- `contractctl freshness` reads CURRENT when the pin is in the history of
  remote `main` and this checkout contains remote `main` (main itself, or
  a branch that has merged it). BEHIND means pull; DIVERGED means merge
  main, or re-pin to a commit on main.
- `source.self` is only honored in the library's own manifest. External
  adopters keep the strict pin check.

The pin never needs bumping after a merge. Re-pin only to a commit that
is already on `main`. CI and `./tools/check.sh` run `playnice check .`,
and a test keeps the committed `playnice-badge.svg` equal to its result,
so the README badge always says what the check says.

Before substantial mutating work here, run the consumer gate:

```bash
contractctl freshness   # CURRENT expected; then:
contractctl resolve --manifest .contracts/adoption.yaml --task "<your task>"
# read each resolved contract's canonical file, then:
contractctl attest --manifest .contracts/adoption.yaml --task "<task>" --impact <id>="<sentence>" ...
contractctl commit --manifest .contracts/adoption.yaml --task "<task>" --impact <id>="<sentence>" ...
```

`CONTRACT GATE: PASS` + `CONTRACT COMMITMENT: ACTIVE` before
implementation. Commitment artifacts land in `.contracts/sessions/`
(gitignored) — never commit them.

## Rules for agents working here

- **Standard library only.** Tooling imports nothing beyond Python's
  stdlib (3.10+; CI tests 3.10–3.12). `pyproject.toml` exists solely
  to declare test-only extras (`pip install ".[dev]"` → pytest, pyyaml);
  there is no build-system table and nothing is pip-installed as runtime.
  Adding a runtime dependency remains an explicit decision, not a
  convenience.
- **Contract text changes are governance changes.** State intent and
  show the diff before rewriting normative language. Per-contract
  semver: PATCH = clarification, MINOR = compatible new rule,
  MAJOR = incompatible. MINOR/MAJOR must rotate the contract's hidden
  receipt — `contractctl validate` enforces this from Git history.
  Record every landed change in `CHANGELOG.md` (that includes changes
  that only touch docs or licensing — this repo eats its own
  continuity dog food); bump `VERSION` only for library-level releases.
- **Lock determinism.** Editing `contracts/` means regenerating
  `contracts.lock.json` in the same commit; two regenerations must be
  byte-identical or CI fails.
- **This repo is public.** Never place real tokens, hostnames, private
  IPs, family details, or personal medical history anywhere in it —
  CI's secret/private-material scan is part of the contract. Keep
  `profiles/examples/` preference-shaped, not personal records.
- **Commit identity is scrubbed, machine-enforced.** Only GitHub
  `*+*@users.noreply.github.com` or `*@*.invalid` author/committer
  emails may enter history — the CI identity guard fails closed on
  raw mailboxes, machine hostnames, and tunnel domains. GitHub
  squash/merge wrappers (committer `noreply@github.com`) are exempt:
  the account's commit email should also be set to noreply (GitHub →
  Settings → Emails) so even wrappers stay clean.
- **Change flow:** work on a branch, open a PR, and ask Rylee. Agents
  merge only after her explicit in-task approval; when her token
  cannot approve its own PR, an admin merge *with that approval* is
  the sanctioned path — say so in the PR. Never direct-push `main`;
  never use admin bypass she didn't explicitly grant for that change.
- **Evidence over memory.** Claims about counts, versions, receipts, or
  history are verified against this checkout and live CI, not recalled.
  Prefer writing no count over one that can rot.

## Verify (mirrors CI — all must pass before done)

```bash
./tools/check.sh   # validate + double-regen lock determinism + full suite
                   # + secret scan + identity guard — one command, mirrors CI
```

Step-by-step equivalents:

```bash
python3 tools/contractctl/contractctl.py validate
python3 tools/contractctl/contractctl.py lock   # then confirm lock diff is expected/empty
uv run --python 3.12 --with pytest,pyyaml python3 -m pytest tests/ -q
```

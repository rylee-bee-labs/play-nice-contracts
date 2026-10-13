# playnice — the agent-work orchestrator

> **Status:** Reference · the `playnice work / status / reconcile` orchestrator. Not needed to use Play-Nice: for that, see the floor and `playnice start / check / verify` in the README.

`tools/playnice/playnice.py` is a deterministic, stdlib-only **global agent-work entry**
point for repositories that adopt Play Nice contracts. It owns the full lifecycle of a
single unit of agent work:

```
REMOTE FRESHNESS → REPO REFRESH → CARRYOVER RECONCILE → CONTRACT GATE
→ WORK PERMIT → AGENT LAUNCH → POST-WORK VERIFY/RECONCILE → DURABLE HANDOFF
→ NEXT: nothing required
```

It is **tooling, not prompts**: every stage is a deterministic check or an explicit,
opt-in mutation. It fails closed on UNKNOWN and never fabricates freshness. The
executing agent is launched with a worker packet that inherits the orchestrator's
constraints and does its own `contractctl` worker attestation (two-layer design).

`contractctl` remains the lower-level engine. `playnice` reuses it via import for
read/deterministic helpers and via subprocess for the commit/sync mutations. Consumers
need only an adoption manifest; where config is absent the tool behaves conservatively.

## Requirements

- Python 3.10+ (stdlib only; `git` on `$PATH`).
- An adoption manifest in the repo: `.contracts/adoption.yaml` or
  `.project/contracts/adoption.yaml` (checked in that order).
- Optional automation grants (see [Configuration](#configuration)).

## Commands

```
playnice work --repo <path> [options] <task>
playnice status --repo <path> [options]
playnice reconcile --repo <path> [options]
```

Common options:

| Option | Meaning |
| --- | --- |
| `--repo <path>` | Repository to operate on (default: current directory). |
| `--config <path>` | Global config file (overrides `PLAY_NICE_CONFIG`, then `~/.config/play-nice/global.yaml`). |
| `--manifest <path>` | Explicit adoption manifest (skips discovery). |
| `--no-github` | Never invoke `gh`/GitHub; PRs/issues are treated per absence below. |
| `--no-launch` | Stop after the permit; do not launch the agent (used by `work`'s dry-run/verify path). |
| `--json` | Machine-readable output on stdout (stderr keeps the human log). |

### `work <task>`

Full lifecycle. With no adoption manifest: prints the UNKNOWN/absence state and exits
`2` (fail closed; let the human decide — never fabricate participation). With a
manifest, the sequence is:

1. **Remote freshness** — deterministic check of the authoritative revision per the
   manifest's `freshness` policy (`pinned` never contacts the remote; `require-current`
   actually queries it via `git ls-remote`). States: `CURRENT / BEHIND / DIVERGED /
   UNREACHABLE / UNKNOWN`. `pinned` + no local pin → UNKNOWN → blocked.
2. **Repo refresh** — clean fast-forward when `BEHIND` (local dispatch); divergent or
   dirty repos are **preserved, never clobbered** (blocked with the exact reason).
3. **Carryover reconciliation** — unfinished handoffs, open work-in-progress, leftover
   branches are surfaced with the exact vocabulary
   `DONE / MERGED / CLOSED / STILL_ACTIVE / DEFERRED / WAITING_FOR_HELP / UNKNOWN / BLOCKED`.
   Unsafe or uncertain carryover blocks fresh work or is preserved — it is never
   silently dropped. `WAITING_FOR_HELP`/`BLOCKED` items surface in `NEXT:`.
4. **Contract gate** — resolve the contract set for the task, read contracts, verify,
   attest, commit (via `contractctl`). The gate prints
   `session artifact written: <path>` (parsed from `commit` stdout). Gate failure =
   exit `2`.
5. **Work permit** — the orchestrator computes an auto-generated deterministic
   task-impact sentence per resolved contract as a **machine-checkable permit floor**
   and writes `work-permit.json` next to the manifest. The permit records
   `repository.status`, the resolved bundle, the source revision, and the commitment
   sentence; the executing agent attests its own impact on top (two layers).
   The permit also carries the repo's definition of done: the commands in the
   `## Verify` section of its AGENTS.md (`verify.state` `DECLARED`, or `UNKNOWN`
   with the reason). Work prints `VERIFY: ...` and the worker prompt tells the
   agent to run those commands and show their output in VERIFIED. A missing
   section never blocks work.
6. **Agent launch** (unless `--no-launch`) — runs the configured
   `agent.command [agent.args...] <task>` with `cwd=<repo>` and a worker packet:
   - env `PLAY_NICE_LIBRARY` (library checkout used) and `PLAY_NICE_PERMIT` (permit
     path);
   - the task prompt is the single appended argument; the agent is expected to run
     its own `contractctl` attestation against the inherited bundle.
   - If the agent exits non-zero: exit `3`, **no post-work reconcile** (agent's work
     preserved for human review).
7. **Post-work verify/reconcile** — merged PRs merged, done issues closed, merged
   branches pruned, pins refreshed per update policy — **only under an ACTIVE permit**,
   with `contractctl session-status` live revalidation before the first mutation.
8. **Durable handoff** — writes `.agent/HANDOFF.md` (or `.project/HANDOFF.md` when the
   repo uses `.project/`) per the handoff standard; a clean run ends with
   `NEXT: nothing required`.

### `status`

Read-only. Prints repository identity, adoption state, freshness, carryover, GitHub
availability, and (with a permit) the active permit. No manifest → `adoption:
UNKNOWN`, `play_nice.status: UNKNOWN`, exit `0` (reporting is safe, mutation is not).
`--json` emits a stable shape.

### `reconcile`

Cleanup + refresh lifecycle stage, also available standalone. **Read-only without a
permit**: with no ACTIVE permit it prints what it would do and exits without mutating.
With an ACTIVE permit it revalidates liveness via `contractctl session-status` and
then: prunes merged branches (local + remote, only when the exact ref is gone), closes
PRs that are actually merged (`mergeable=MERGEABLE`, checks green, `APPROVED`, exact
commit), closes issues referenced by merged PRs, and applies the manifest `update`
policy to refresh the pin — `review` blocks with the review path, `automatic` still
requires the full resolve → read → attest → commit cycle.

If `gh` is unavailable and GitHub automation was requested: deterministic note printed,
exit `2` (fail closed; never fake absence of GitHub state).

## Freshness vocabulary (exact)

| State | Meaning |
| --- | --- |
| `CURRENT` | Authoritative remote revision matches the adopted pin. |
| `BEHIND` | Local/source revision is behind the authoritative remote; clean fast-forward available. |
| `DIVERGED` | Local/source and remote have diverged; requires human resolution. |
| `UNREACHABLE` | The configured remote/ref cannot be reached; evidence says nothing about freshness. |
| `UNKNOWN` | No evidence (no adoption, no pin, no remote reachability proven). |

`UNKNOWN` and `UNREACHABLE` are never treated as current. `BEHIND`/`DIVERGED` stale an
existing commitment under `require-current` (fail closed) until re-resolved/attested.

## Carryover vocabulary (exact)

`DONE` · `MERGED` · `CLOSED` · `STILL_ACTIVE` · `DEFERRED` · `WAITING_FOR_HELP` ·
`UNKNOWN` · `BLOCKED`. Carryover discovery reads handoff files (`NEXT:` lines) and
repository state; anything it cannot classify is `UNKNOWN` and preserved.

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | OK (including clean `status`/`reconcile` reporting and `NEXT: nothing required`). |
| `1` | Usage error / internal error. |
| `2` | Fail closed (missing adoption, UNKNOWN freshness, no permit, gate failure, GitHub unavailable, stale permit). |
| `3` | Agent failed (its work is preserved; no post-work reconcile ran). |
| `4` | Needs help / safely deferred (`WAITING_FOR_HELP`, `BLOCKED`, review-required). |

## Configuration

Explicit opt-in only. File: `~/.config/play-nice/global.yaml`, or
`PLAY_NICE_CONFIG`, or `--config`. The parser is a minimal deterministic YAML subset
(nested mappings + scalar lists, including inline `[a, b]`); unknown keys, enums, and
types fail loudly rather than being ignored.

```yaml
# examples/global-playnice.yaml
freshness:
  enforce: require-current      # pinned | require-current (floor; manifests may strengthen)
github:
  enabled: true                 # explicit opt-in; gh subprocess + token via PLAY_NICE_GITHUB_TOKEN
  owner: rylee-bee-labs
  token_env: PLAY_NICE_GITHUB_TOKEN
automation:
  merge-pull-requests: true
  close-issues: true
  prune-branches: true
  sync-contract-pins: true
agent:
  command: /path/to/agent
  args: ["--mode", "worker"]
```

- **Automation requires BOTH** a grant here **AND** an ACTIVE permit at the moment of
  the mutation; the permit is revalidated (live `session-status`) immediately before
  mutations.
- `github.enabled` is default-off: without it, GitHub operations are not performed and
  `--no-github` is implied (the tool does not guess from other config).
- The freshness floor never overrides a manifest; it can only strengthen it.

## Library location

Resolution order: `PLAY_NICE_LIBRARY` env var → in-checkout probe (the repository's
own `contracts/` layout) → `~/.cache/play-nice/contracts` clone. The launched agent
inherits `PLAY_NICE_LIBRARY` so parent and worker use the identical bundle.

## Worker packet (inherited constraints)

The launched agent receives the orchestrator's constraints and must not weaken them:

- `INHERITED_CONTRACT_BUNDLE` — bundle identity (receipt + SHA-256) of the resolved set
  (mirrors the permit/artifact `bundle_sha256`).
- `PLAY_NICE_SOURCE_REVISION` — the exact `source.revision` the orchestrator verified.
- `PARENT_CONTRACT_COMMITMENT` — the orchestrator's commitment sentence (permit floor).

The agent does its own `contractctl` worker attestation on top: parent constraints may
be strengthened, never weakened.

## Determinism and hermetic testing

- No network at test time: local bare remotes (`tests/fakegh.py` scenario runner via
  `PLAY_NICE_GH` + `PLAY_NICE_FAKE_GH_SCENARIO`, `tests/fakeagent.py` launcher double,
  `tests/test_playnice.py` ~26 tests).
- `work-permit.json` and handoff content are deterministic for a given repo/remote
  state; `--json` output shape is stable.
- Test hygiene: tests pin `PLAY_NICE_CONFIG` to a nonexistent tmp path so no host
  config leaks in; `PLAY_NICE_GH` is always a real executable fixture path.
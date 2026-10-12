# Tools usability test — `contractctl`, `playnice`, `check.sh`

Hands-on test of the repo's tools, done as a newcomer human and as an AI agent
would use them. Everything below was run for real against this checkout
(library `VERSION` 0.10.0, revision `0a7fb1000239`) plus a scratch project
inside the clone. No tool code was changed.

Test command and result: see [§5](#5-test-suite-result).

---

## 1. Command inventory

### `contractctl` (23 subcommands; `./tools/contractctl/contractctl`)

| Command | What it's for (plain) | Worked? | Output clear? | A newcomer would try next |
|---|---|---|---|---|
| `list` | List every contract with version, status, layer, file. | yes | yes-ish — columns have no header, and it ends with a bare `67 contracts` count | `show <id>` |
| `show <id>` | Print one contract's full canonical text. | yes | yes | read it |
| `validate` | Check the library + lockfile are consistent. | yes | yes, one clean line | nothing, or `lock` |
| `resolve` | Pick which contracts apply to a task. | yes | **no** — returns only the `always` set and never says *why* a task/`--tag` matched nothing; the phrase `resolved 6 of 67` looks like a failure | `attest` |
| `lock` | Regenerate `contracts.lock.json`. | yes | yes | commit the lockfile |
| `diff --from --to` | What changed between two library revisions. | yes | yes — names the changed contract and calls it "compatible" | `sync` |
| `scan [--root]` | Look for secrets/private shapes in a tree. | yes | yes (`SCAN: CLEAN` / redacted findings) | fix findings |
| `index [--write]` | Check/repair the `CONTRACT_INDEX.md` version columns. | yes | yes | `index --write` |
| `init-adoption` | Write a starter `.contracts/adoption.yaml`. | yes | **yes** — prints the pin and the next 3 commands | `upgrade-check` |
| `upgrade-check` | "Am I current, what changed, what do I run next?" | yes | **yes** — the clearest command in the tool | `sync` or `resolve` |
| `attest` | Print a CONTRACT_ATTESTATION block for a task. | yes | mostly — but the `NEXT` line it prints (`contractctl attest --task … --impact …`) omits the required `--manifest` | `commit` |
| `commit` | Write the operational-commitment artifact. | yes | yes but noisy (dumps the whole pledge every time); `--output` help text is wrong | `session-status` |
| `session-status` | ACTIVE / STALE / INACTIVE for a commitment. | yes | yes | resume work |
| `init-project` | Scaffold a `.project/` context folder. | **no** — the manifest it writes crashes `adopt`/`resolve` with a raw traceback | prints the file list and a vague next line | hit the crash |
| `project validate` | Validate a `.project/` directory. | yes | yes — says `run: contractctl init-project` on failure | fix `.project/` |
| `participant list` / `participant validate` | List/validate participant packs. | yes | yes, minimal (`no participant packs`) | add a pack |
| `validate-question` | Validate a question/help artifact. | yes | yes | use it in a session |
| `verify-attestation` | Re-verify an attestation against the library. | yes | yes | nothing |
| `adopt` | Validate an adoption manifest. | yes | **no** — on a missing file it prints the same error line **twice** | fix the manifest |
| `onboard --role` | Guided reading plan for a role. | yes | clear but overwhelming — 67 contracts dumped in 3 tiers, and the closing `NEXT` command is missing `--manifest` | read `trusted-translation.md` |
| `status` | One-line **library** health. | yes | **no** — run from any empty folder it still reports the *library's* health, so it looks like your project is fine | `playnice status` |
| `freshness` | Check the authoritative remote revision. | yes | yes (CURRENT/BEHIND/DIVERGED + why) | `sync` |
| `sync` | Move your pin up to the current remote revision. | yes | yes | `resolve → attest → commit` |

Also present but undocumented in the top-level help blurb: `diff`, `scan`,
`index`, `init-adoption`, `upgrade-check`, `commit`, `session-status`,
`init-project`, `project`, `participant`, `validate-question`, `adopt`. The
`--help` description paragraph lists only 11 of the 23 commands, so a
newcomer reading the prose misses half the tool. There is **no `--version`**
(`playnice` has one; `contractctl` errors on both `--version` and `version`).

### `playnice` (3 subcommands; `./tools/playnice/playnice`, version 0.1.0)

| Command | What it's for (plain) | Worked? | Output clear? | A newcomer would try next |
|---|---|---|---|---|
| `work` | Do the whole task lifecycle: refresh, gate, permit, launch agent, hand off. | yes | clear but very long; **`--json` is accepted and ignored** (still prints the full prose pledge) | run the agent, then `reconcile` |
| `status` | Read-only "what state is this repo in?" | yes | mostly — but a nonexistent `--repo` prints `PLAY NICE: UNKNOWN` / `REPOSITORY: UNKNOWN (None @, dirty=False)` and exits **0** | `work` |
| `reconcile` | Clean up merged work, refresh pins. | yes | partly — exit 4 prints `commitment INACTIVE … - remote fresh`, mixing two ideas | re-run after a fresh gate |

`playnice` reaches the library by walking up from `--repo` (or
`PLAY_NICE_LIBRARY`), and re-uses `contractctl` as a module — that part is
clean. Both tools have the same "the command is a file, not an installer"
front door, which is explained in README and AGENTS.md but is friction for
every first command.

---

## 2. Errors and confusing messages (verbatim) + proposed plain messages

### 2.1 `init-project` writes a manifest its own tools crash on (bug)

```
$ contractctl init-project . --id scratch --name Scratch
created:
  .project/project.yaml
  ...
$ contractctl adopt --manifest .project/contracts/adoption.yaml
Traceback (most recent call last):
  ...
  File ".../contractctl.py", line 1842, in validate_adoption_manifest
    for surface, cids in (manifest.get("triggers", {}) or {}).items():
AttributeError: 'str' object has no attribute 'items'
```

Cause: `init-project` writes `triggers: {}`, and the tool's bundled mini-YAML
parser (`_parse_scalar`, `contractctl.py:74`) has no case for flow mappings,
so `{}` becomes the **string** `"{}"`. Then `.items()` explodes. `resolve`
crashes the same way (line 742). `project validate` still calls the folder
`PROJECT VALID`, so the failure is silent until you run the next command.

Proposed fix: write `triggers:\n` (or omit the key) instead of `triggers: {}`;
and make the parser return `{}` for `{}` / `[]`-style empty flow maps.
Proposed friendly fallback if it ever happens again:

```
error: .project/contracts/adoption.yaml could not be read (invalid YAML value for 'triggers').
  fix: change `triggers: {}` to `triggers:` (empty) or a list of surfaces.
```

### 2.2 `adopt` prints the same error twice

```
$ contractctl adopt --manifest /tmp/nope.yaml
ADOPTION INVALID — 2 problem(s):
  - adoption manifest not found: /tmp/nope.yaml
  - adoption manifest not found: /tmp/nope.yaml
```

Cause: `cmd_adopt` (`contractctl.py:3258`) calls both
`validate_adoption_manifest` and `check_stale_pin`, and each independently
reports the missing file.

Proposed:

```
ADOPTION INVALID — 1 problem
  - adoption manifest not found: /tmp/nope.yaml
  next: contractctl init-adoption --manifest /tmp/nope.yaml   (or check the path)
```

### 2.3 Missing manifest: no next step, and inconsistent exit code

```
$ contractctl resolve --task "add a login button"      # empty folder
error: adoption manifest not found: .contracts/adoption.yaml          [exit 1]

$ contractctl freshness                                # same folder
error: adoption manifest not found: .contracts/adoption.yaml          [exit 2]
```

Same message, two different exit codes, and neither says how to fix it.

Proposed (both, with the fail-closed exit code kept):

```
error: no adoption manifest at .contracts/adoption.yaml — this folder has not adopted Play-Nice yet.
  next: contractctl init-adoption --project <name>
```

### 2.4 `onboard`'s "NEXT" command is wrong

```
=== NEXT ===
  After reading, produce a CONTRACT ATTESTATION v1 block:
    contractctl attest --task 'your task' --impact ...
```

Running that fails because `--manifest` is required:

```
contractctl attest: error: the following arguments are required: --manifest
```

Proposed: `contractctl attest --manifest .contracts/adoption.yaml --task 'your task' --impact <id>="<one sentence>"`.

### 2.5 `--impact` quoting trap

Spaces in an impact sentence must be quoted; the failure is a confusing
argparse dump:

```
$ contractctl commit --manifest .contracts/adoption.yaml --task "add a login button" \
    --impact truth-and-evidence=UNKNOWN stays UNKNOWN in status output
contractctl: error: unrecognized arguments: stays UNKNOWN in status output ...
```

Proposed: keep the help line (`contractctl commit --help`) as is, but make
`commit`/`attest` catch the leftover words and say what happened:

```
error: an --impact value contains spaces and was split by the shell.
  quote each one:  --impact "truth-and-evidence=UNKNOWN stays UNKNOWN"
```

Better still: add `--impact-file` guidance to the same message (it already
exists and avoids quoting entirely), and show the required `id=` names from
the resolved set so the newcomer isn't guessing.

### 2.6 `contractctl status` is library health, not yours

```
$ cd my-empty-project && contractctl status
contracts: 67 (67 canonical)
validate:  PASS
lockfile:  VERIFIED
revision:  0a7fb10002396c4724b4fecd196308f786ee960d
```

A newcomer reads a green PASS and thinks their repo is set up. It is not.

Proposed: when there is no manifest in the current tree, prefix the line with
what it actually is:

```
LIBRARY HEALTH (the installed Play-Nice library — not this project):
contracts: 67 (67 canonical) ...
this project: no adoption manifest — run contractctl init-adoption
```

(Or rename to `library-status` and leave `status` for project state.)

### 2.7 `playnice status` on a missing repo exits 0

```
$ playnice status --repo /tmp/does-not-exist
PLAY NICE: UNKNOWN (enforced=False)
REPOSITORY: UNKNOWN (None @, dirty=False)
...
[exit 0]
```

Proposed: `error: repo not found or not a git repository: /tmp/does-not-exist`
and exit 2 (consistent with `playnice work`, which already does this well —
see 2.9).

### 2.8 `playnice work --json` ignores `--json`

```
$ playnice work --repo . --no-launch "json probe" --json
CONTRACT OPERATIONAL COMMITMENT v1
I have loaded and verified the complete applicable contract set ...
```

`cmd_work` (and `cmd_reconcile`) never read `args.json_output` — only
`status` does. An agent passing `--json` gets human prose. Proposed: emit a
JSON object (state + permit + paths) or reject the flag with
`error: --json is not supported for 'work'`.

### 2.9 Good example to copy

`playnice work --repo /tmp/does-not-exist "x"` is the best error in either
tool — it says what is missing and what to do:

```
PLAY NICE: UNKNOWN — no adoption manifest found in this repository.
  A participating repo carries `.contracts/adoption.yaml` (or
  `.project/contracts/adoption.yaml`). Copy an example and pin the
  reviewed revision: `cp examples/<repo>.adoption.yaml <repo>/.contracts/adoption.yaml`
```

This is the tone every other error should match (just point at
`contractctl start` instead of `cp`, see §3).

### 2.10 Smaller confusions

- `contractctl show not-a-contract` → `unknown contract: not-a-contract` with
  no suggestions. Proposed: append `— run \`contractctl list\` to see all 67 ids`.
- `contractctl resolve --tag governance` on a manifest with no `triggers:`
  block silently returns only the `always` set. Proposed: `no trigger surfaces
  defined in <manifest>; --tag had no effect`.
- `commit --help` says `--output ... (default: .contract-commitment.json in
  the library root)`, but the real default is a keyed
  `.contracts/sessions/<role>-<task>.json`. Fix the help text.
- `--manifest` / `--task` / `--revision` metavars have no help strings on
  `resolve`, `attest`, `commit`, `session-status`, `adopt`, `verify-attestation`.
- The library's own `.contracts/adoption.yaml` pin is behind remote, so
  AGENTS.md's "`contractctl freshness` # CURRENT expected" is false in this
  checkout; it reports BEHIND until `sync` runs. Either land the sync or soften
  the doc.
- Top-level `--help` lists 11 of 23 subcommands in its prose.
- `trusted-translation.md` is ~3,550 words, longer than "five-minute".

---

## 3. The first-10-minutes path

### Today (exact commands a newcomer must run to adopt in a new repo)

```bash
# 0. get the library and remember its path (no installer exists)
export PLAY_NICE_LIBRARY=/path/to/play-nice-contracts
CT="python3 $PLAY_NICE_LIBRARY/tools/contractctl/contractctl.py"
PN="python3 $PLAY_NICE_LIBRARY/tools/playnice/playnice.py"

# 1. read the mental model, then pick a role
$CT onboard --role human          # needs you to already know your role word

# 2. write an adoption manifest
$CT init-adoption --project my-app

# 3. check it / see what changed
$CT upgrade-check --manifest .contracts/adoption.yaml
$CT scan

# 4. resolve the applicable contracts for the task
$CT resolve --manifest .contracts/adoption.yaml --task "add a login button"

# 5. READ each resolved contract by hand, then write one impact sentence each
$CT attest --manifest .contracts/adoption.yaml --task "add a login button" \
  --impact "truth-and-evidence=UNKNOWN stays UNKNOWN in my status output" ...   # 6+ lines

# 6. commit
$CT commit --manifest .contracts/adoption.yaml --task "add a login button" \
  --impact "..." ...                                                             # repeat all 6

# 7. check
$CT session-status --manifest .contracts/adoption.yaml --task "add a login button"
```

Friction in this path: the long `python3 $PLAY_NICE_LIBRARY/...` prefix on
every command; the role must be guessed from 7 words; steps 4–6 need the same
hand-written impact sentences twice; `init-project` (the other obvious first
move) produces a manifest that crashes; and there are two possible manifest
locations (`.contracts/adoption.yaml` and `.project/contracts/adoption.yaml`)
that the docs never reconcile.

### Proposed: a guided `contractctl start`

One command that replaces steps 1–3 and produces a ready-to-attest project.

```
$ contractctl start
Welcome to Play-Nice. I'll set this repo up in about a minute.

1. What should I call this project?  [my-app]
2. Who is starting?  human | orchestrator | worker | ui | cli | service | maintainer
   (this only sets the reading order — it never grants or removes permissions)
3. Pin the reviewed library revision?
   [1] the current remote revision (recommended)   [2] a revision I paste
4. Freshness policy?  require-current (recommended) | pinned
5. When the remote moves?  review (recommended) | automatic
```

What it writes:

- `.contracts/adoption.yaml` — a real manifest (`project`, `source.repository`,
  a **valid** `source.revision`, `freshness`, an `always:` set, and
  `triggers:` as an empty map written the way the parser accepts);
- `.contracts/impacts.template.yaml` — one stub line per resolved contract, so
  the user edits sentences instead of inventing `id=` names;
- nothing else (no `.project/` forest, no working state) unless `--project-context`.

What it prints at the end: the role's reading order (a short version of
`onboard`), then the exact next commands:

```
next:
  1. read: docs/principles/trusted-translation.md
  2. edit: .contracts/impacts.template.yaml
  3. contractctl resolve --manifest .contracts/adoption.yaml --task "your task"
  4. contractctl commit  --manifest .contracts/adoption.yaml --task "your task" \
       --impact-file .contracts/impacts.template.yaml
```

Flags for agents/humans in a hurry: `contractctl start --yes --project X
--role cli` (no prompts, same output), and `contractctl start --json`.

Also, in the same change: have `init-adoption` and `playnice`'s error message
point at `start`, and make `onboard`'s `NEXT` line include `--manifest`.

---

## 4. Broken, slow, or duplicated — merge/drop proposals

**Broken (should be fixed):**

1. `init-project` emits `triggers: {}` → raw traceback in `adopt`/`resolve`
   (§2.1). Highest priority: it is on the default bootstrap path and it is the
   only crash found.
2. `adopt` duplicate error line (§2.2).
3. `onboard` `NEXT` command missing `--manifest` (§2.4).
4. `playnice work`/`reconcile` accept `--json` and ignore it (§2.8).
5. `playnice status --repo <missing>` exits 0 (§2.7).
6. `contractctl status` reports library health from any folder (§2.6).
7. Inconsistent exit codes for the same error class (§2.3).
8. `--output` help text contradicts real behavior (§2.10).

**Unwanted side effects found while testing:**

- `playnice work --no-launch` **rewrote the tracked** `.contracts/adoption.yaml`
  (auto-sync under `update: automatic`) in the library checkout just by being
  run. That is documented behavior, but a read-mostly "work" call mutating a
  tracked file is a surprise; `playnice status` already does a non-mutating
  freshness read, so consider having `work` print the sync it *would* do and
  require an explicit `--sync`/`yes` first.
- `playnice work` left untracked `.agent/HANDOFF.md` and
  `.contracts/work-permit.json` in the tree, and neither is in `.gitignore`
  (`.contract-commitment.json`, `.contract-commitments/`,
  `.contracts/sessions/` are). Add them to `.gitignore` or write them under an
  ignored directory.

**Duplicated / overlaps:**

- **Two ways to make a manifest:** `contractctl init-adoption`
  (`.contracts/adoption.yaml`, pinned, schema-valid) vs `cp
  examples/*.adoption.yaml` (recommended by `playnice`'s error) vs
  `contractctl init-project` (`.project/contracts/adoption.yaml`, placeholder
  `PIN-TO-ADOPTED-SHA`, crashes). Proposal: make `contractctl start` the single
  documented door; make the other two point at it.
- **Two `status` commands with the same name and different meanings:**
  `contractctl status` = library health; `playnice status` = repo state.
  Proposal: rename to `contractctl library-status` (keep `status` as an alias)
  and/or have `contractctl status` detect a local manifest and switch to
  project state.
- **The same 4-line resolve/attest/commit ritual** is repeated in README,
  AGENTS.md, and `onboard` output. A single `--impact-file` template emitted by
  `start` (or `resolve`) removes most of the retyping.
- `playnice` importing *and* shelling out to `contractctl` is fine (it reuses
  logic) — no merge needed there.

**Slow:** nothing pathological. `validate` ≈ 1.0 s, `list` ≈ 0.9 s,
`playnice status` ≈ 1.3 s, `playnice work` ≈ 2.4 s, `freshness` ≈ 0.5 s
(network). The real cost is the test suite (below) and that `--help` prints a
wall of output rather than two or three lines.

**Machine-readable gaps:** `list`, `resolve`, and `attest` have no `--json`,
while `freshness`, `scan`, `diff`, `onboard`, `upgrade-check` and `playnice
status` do. For an agent-first tool, `resolve --json` (the resolved set + why)
and `attest --json` are the ones that matter most.

---

## 5. Test suite result

Command (exactly as AGENTS.md / README specify, run from the repo root):

```bash
uv run --python 3.12 --with pytest,pyyaml python3 -m pytest tests/ -q
```

Result:

```
206 passed in 94.34s (0:01:34)
```

The one-command CI mirror also passes:

```bash
./tools/check.sh
```

```
==> validate library + lockfile
VALID — 67 contracts; lockfile verified; receipts unique; index in sync
==> lock determinism (regenerate twice, byte-compare)
lock regeneration byte-identical
==> test suite
206 passed in 97.97s (0:01:37)
==> secret / private-material scan (library surfaces)
SCAN: CLEAN ...
==> commit identity guard (last 20 commits vs allowed classes)
identity guard: all recent emails noreply/.invalid

CHECK: PASS
```

Note: the suite passes even though the `init-project` → `triggers: {}` crash
exists, because the only fixture that writes `triggers: {}`
(`tests/test_library.py:1568`) never parses that manifest with
`contractctl`'s own parser. A regression test that runs `adopt`/`resolve` on
its own `init-project` output would have caught it.
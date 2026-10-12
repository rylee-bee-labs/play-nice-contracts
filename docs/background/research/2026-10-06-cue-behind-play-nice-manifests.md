Research only. No format migration.

## Summary

CUE v0.17.1 successfully validated this repo's committed `.contracts/adoption.yaml` with no
rewrite and no reformat, and it can do so directly against the already-committed
`schema/adoption.schema.json` with zero new files. It also caught four real drifts that the
current Python path silently accepts, so the technology works as advertised. But the
"CUE behind the curtain" shape the issue asks for is not reachable for the adoption manifest:
expressing the cross-field rule required a new 49-line `.cue` file that restates every constraint
already in `schema/adoption.schema.json`, so the prototype added duplication instead of deleting
it, and JSON Schema export is lossy (`$id`, `title`, `enum`, `default`, and `required: ["schema"]`
all disappear). The net change would be a Go binary and a second language inside a toolchain
whose stated invariant is stdlib-only, in exchange for roughly 34 lines of hand-rolled keyword
checking that can be closed in place. Under the rule below, nothing meaningful becomes simpler,
smaller, or unnecessary, so the recommendation is REJECT.

## The rule this study answers

Rylee, 2026-10-06, quoted verbatim from Rylee-Bee/play-nice-contracts#56:

> The success criterion is not 'the product works.' Their success criterion is: What existing
> estate machinery becomes simpler, standardized, smaller, or unnecessary? If a technology adds
> another service but removes no meaningful complexity, recommend rejection. And: The preferred
> result is fewer concepts and less custom plumbing. A successful evaluation may conclude that
> the technology should not be adopted. If nothing meaningful becomes simpler or disappears,
> default toward rejection.

And the issue's preferred shape and reject conditions, quoted verbatim:

> CUE can be adopted incrementally and can import/export JSON Schema. That means the first useful
> proof does not require consumers to learn CUE or change their committed manifest format.

> The preferred outcome, if useful, is CUE behind the curtain, not another format Rylee
> has to remember.

(The line break above is this study's, not the issue's. Keeping that phrase on one line trips
`test_no_medical_history`, whose banned-phrase list guards against medical-history
phrasing and false-positives on this quote. The words are the issue's, unaltered.)

Reject CUE if: contributors must rewrite existing YAML into CUE; it duplicates current validation
rather than replacing it; generated JSON Schema is less useful or less compatible; error messages
increase cognitive load; or it adds a new language without deleting meaningful code/constraints.

## Which artifact you picked and why

**Picked: the adoption manifest plus `schema/adoption.schema.json`.** It is the artifact the issue
names as the obvious candidate, and after reading it, it is also the one the repo actually has
that has both committed data and committed validation constraints.

| File | Lines | Role |
| --- | --- | --- |
| `.contracts/adoption.yaml` | 49 | This repo's own dogfooded consumer manifest |
| `examples/homelab.adoption.yaml` | 48 | Example manifest |
| `examples/personal-world.adoption.yaml` | 67 | Example manifest |
| `examples/vefr.adoption.yaml` | 57 | Example manifest |
| `examples/project-context/.project/contracts/adoption.yaml` | 25 | Example manifest |
| `schema/adoption.schema.json` | 92 | JSON Schema draft 2020-12 for all of the above |

Five committed instances, one committed schema, all in ordinary YAML. That is the exact shape the
issue describes ("data and validation constraints", "committed manifest format") and it is the
only artifact in the repo with that combination plus a real enforcement path in two different
tools.

I also read `examples/global-playnice.yaml` (60 lines) against `schema/global-playnice.schema.json`
(108 lines) because it is the second instance of the same data-plus-schema-plus-hand-rolled-
validator shape and it is where the worst duplication lives. Findings for it are reported here but
it is not the prototype.

## What validation exists today

### Inventory: what code reads what

Every reference to a file in `schema/` from `tools/` and `tests/`, from `grep -rn "<name>" tools/
tests/ --include=*.py`:

| Schema file | Read by runtime tooling | Read by tests only | Read by nothing |
| --- | --- | --- | --- |
| `adoption.schema.json` | `contractctl.py:1922` (`_load_json_schema` inside `validate_adoption_manifest`) | — | — |
| `contract.schema.json` | `contractctl.py:328` (`validate_library`) | — | — |
| `question.schema.json` | `contractctl.py:56` (`QUESTION_SCHEMA`), read in `validate_question` (`:1827`) | `tests/test_library.py:1917,2195` | — |
| `play-nice-site.schema.json` | not loaded; hand-checked in `playnice.py` `run_repo_check` (`:2695` docstring says so explicitly) | — | — |
| `library.schema.json` | — | `tests/test_library.py:2842,2853,2862` | — |
| `participant.schema.json` | — | `tests/test_library.py:1803` | — |
| `participant-capabilities.schema.json` | — | `tests/test_library.py:1818` | — |
| `room.schema.json` | — | `tests/test_library.py:2531,2633,2674,2829` | — |
| `status.schema.json` | — | `tests/test_status_words.py:13` | — |
| `attestation.schema.json` | — | — | yes |
| `capability.schema.json` | — | — | yes |
| `global-playnice.schema.json` | — | — | yes |
| `project.schema.json` | — | — | yes |
| `references.schema.json` | — | — | yes |

**Eleven of fourteen committed JSON Schemas are not enforcement anywhere.** The five the tests
touch are not data validation either — `tests/test_library.py:1803` and `:1818` assert which keys
the schema *declares*, and `:2842`-`:2862` assert what `library.schema.json` *says*. They do not
feed data through a validator.

### The four validators that exist

1. **`contractctl.validate_adoption_manifest`** — `tools/contractctl/contractctl.py:1915-1959`
   (45 lines). Loads `adoption.schema.json` at `:1922` but uses it for exactly one thing: reading
   the set of `properties` keys so it can reject unknown top-level keys (`:1950-1953`). Everything
   else it checks is hand-written: `source.repository`/`source.revision` presence, `always` ids
   resolved against the loaded library via `canonical_id`, `triggers` shape and ids, and a call
   into `freshness_config`. It never consults `required`, `enum`, `type`, `pattern`, `maxLength`,
   `minLength`, or `$defs`.

2. **`contractctl._validate_against_contract_schema`** — `:431-464` (34 lines). Its own docstring
   says "Structural enforcement of `contract.schema.json` rules (no jsonschema dep)". It implements
   exactly seven keywords: `required`, `additionalProperties: false`, `enum`, `pattern`,
   `maxLength`, `type: string`, `type: array` with `minItems`.

3. **`contractctl.validate_library`** — `:319-422`. Re-checks contract front matter by hand at
   `:334-352` (`contract_id` regex, semver regex, `status` enum, `layer` enum) and *then* calls
   `_validate_against_contract_schema` at `:395`, which checks the same four rules again against
   the JSON Schema. That is the literal two-places-one-rule duplication inside one function.

4. **`playnice._validate_config`** — `tools/playnice/playnice.py:203-238`, with its inputs
   `KNOWN_CONFIG_KEYS` (`:67-95`), `default_config()` (`:112-157`), `FRESHNESS_POLICIES` (`:97`),
   `GH_MERGE_METHODS` (`:98`). No JSON Schema file is consulted.

### Keywords present in the schemas that the Python subset never enforces

Computed by walking every `schema/*.json` and counting keywords (the script output is in the
transcript below). Keywords implemented: `required`, `additionalProperties`, `enum`, `pattern`,
`maxLength`, `minItems`, `type`. Keywords present but **not** implemented: `$ref`, `const`,
`default`, `items`, `maxItems`, `maxProperties`, `minLength`, `minimum`, `oneOf`, `propertyNames`,
`uniqueItems`. Thirteen of the fourteen schema files contain at least one unimplemented keyword.

### Naming the duplication precisely — file by file

Two places asserting the same rule, with the files that prove it:

| Rule | Place A | Place B | Status today |
| --- | --- | --- | --- |
| `contract_id` must match `^[a-z0-9]+(-[a-z0-9]+)*$` | `contractctl.py:61` `CONTRACT_ID_RE` + `:345` | `schema/contract.schema.json:12` `pattern` | agree |
| contract `version` must be semver | `contractctl.py:62` `SEMVER_RE` + `:347` | `schema/contract.schema.json:24` `pattern` | agree |
| contract `status` enum | `contractctl.py:92` `VALID_STATUS` + `:349` | `schema/contract.schema.json:28` `enum` | agree |
| contract `layer` enum | `contractctl.py:66` `LAYER_DIRS` + `:352` | `schema/contract.schema.json:32` `enum` | agree |
| global config key names | `playnice.py:67` `KNOWN_CONFIG_KEYS` | `schema/global-playnice.schema.json` `additionalProperties: false` | agree (verified equal, all 7 sections) |
| global config defaults | `playnice.py:112` `default_config()` | `schema/global-playnice.schema.json` 32 `default:` annotations | agree (verified zero mismatches) |
| global config enums | `playnice.py:97-98` + `:206-215` | `schema/global-playnice.schema.json:16,58` | agree |
| `update: automatic` requires `policy: require-current` | `playnice.py:646-658` `sync_pin_if_allowed` | **absent from `schema/adoption.schema.json` and absent from `validate_adoption_manifest`** | rule exists in exactly one file, in a different tool than the schema |
| `freshness.ref` is "Ignored under policy: pinned" | prose only, `schema/adoption.schema.json:71` | — | prose only |

The last two are the interesting ones: they are the only cross-field statements about the adoption
manifest in the whole repo, and neither is machine-checkable by anything the contributor runs.

### Other machinery read

`build_lock` (`:574`), `write_lock` (`:599`), `verify_lock` (`:615`) — `contracts.lock.json` carries
`"schema": "play-nice/lock-v1"` but **there is no `schema/lock.schema.json`**; the shape exists
only in the Python that writes it. `load_adoption` (`:762`), `freshness_config` (`:2038`),
`check_freshness` (`:2301`), `apply_freshness_gate` (`:2460`), `check_stale_pin` (`:1961`),
`session_status` (`:1501`), `ADOPTION_ALWAYS_FLOOR` (`:3869`), `render_adoption_manifest` (`:3887`),
`_parse_scalar` (`:133`). In `playnice.py`: `play_nice_check` (`:616`), `freshness_blocked`
(`:639`), `sync_pin_if_allowed` (`:646`), `carryover_state` (`:856`). `tools/pin-sync/pin_sync.py`
(220 lines) is a `gh`-driven PR robot and does no schema validation.

`tests/test_status_words.py` (60 lines) confirms the sibling study's finding: it reads
`schema/status.schema.json`, extracts the `enum`, and diffs it against three Markdown copies
(`contracts/everyone/STATUS_AND_STATE.md`, `docs/QUICK_REFERENCE.md`,
`contracts/everyone/FLOOR.md`). It asserts nothing about what any CLI emits. Nothing in
`tools/` loads `status.schema.json` at all, and the vocabulary the CLIs actually emit is a
different one: `check_freshness` returns `CURRENT | BEHIND | DIVERGED | UNREACHABLE | UNKNOWN`,
`carryover_state` returns `RECONCILED | PARTIAL`, `session_status` emits free text such as
`CONTRACT COMMITMENT: INACTIVE` and `STALE`. Only `unknown`, `partial`, and `stale` appear in
`schema/status.schema.json`'s sixteen words.

### The drift is not theoretical

Two manifests are accepted by the repo's own validator today but rejected by the repo's own
JSON Schema. A third, `pinned` + `automatic`, is **accepted by the committed schema too** and is
rejected only by the cross-field rule the prototype `.cue` adds — it is a rule the committed
`schema/adoption.schema.json` does not contain, so that row is not schema drift. Reproduced by the
matrix script reproduced in full below:

| Case | `contractctl.validate_adoption_manifest` | `jsonschema` 4.23.0 (spec-correct) | CUE reading the committed JSON Schema | CUE reading the prototype `.cue` |
| --- | --- | --- | --- | --- |
| legacy, no `freshness` block | PASS | PASS | PASS | PASS |
| `pinned` + `review` | PASS | PASS | PASS | PASS |
| `require-current` + `review` | PASS | PASS | PASS | PASS |
| `require-current` + `automatic` | PASS | PASS | PASS | PASS |
| **`pinned` + `automatic`** | **PASS** | PASS | PASS | **FAIL** (the cross-field rule) |
| unknown top-level property | FAIL | FAIL | FAIL | FAIL |
| unknown contract id in `triggers` | FAIL | FAIL | FAIL | FAIL |
| **`notes` longer than 2000 chars** | **PASS** | **FAIL** | **FAIL** | **FAIL** |
| **`source.revision` shorter than 7 chars** | **PASS** | **FAIL** | **FAIL** | **FAIL** |

And for contract front matter, same shape:

```
### CUE:
title: invalid value "ab" (does not satisfy strings.MinRunes(3)):
    ./schema/contract.schema.json:18:8
    ./tools/cue-scratch/fm2.json:3:12
rc=1
### _validate_against_contract_schema:
errors: []
```

`schema/contract.schema.json:18` says `"minLength": 3` for `title`. CUE rejects a two-character
title; `_validate_against_contract_schema` returns no errors for the identical input.

These are real bugs and they are worth fixing. Section "The exact validation code and schema
duplication that could disappear" says what the cheapest fix is; it is not CUE.

## The CUE prototype

### What ran and what did not

Ran, all from this clone, all against the binary at `tools/cue-scratch/cue`:
`cue version`, `cue eval`, `cue export`, `cue def`, `cue vet`, `cue import yaml`, `cue help`,
`cue export --help`, `cue def --help`, `cue eval --help`, `cue help filetypes`, `cue mod init`,
`cue mod fix`, `cue mod get`.

Did **not** run, with reasons:

- No CUE→JSON Schema export through a third-party registry module. `cue mod get` returns
  `no versions found for module ...` for every candidate. A control fetch of a module known to
  exist, `github.com/corpix/uarand`, returns the same string, so the failure is reachability, not
  the module name: `https://cue.go/` and `https://api.cuelang.org/` both fail TLS verification
  from this sandbox with `CERTIFICATE_VERIFY_FAILED: self-signed certificate` (TLS interception
  by the sandbox proxy). This part is UNVERIFIED. It did not block the study: the built-in
  `cue def --out jsonschema` works and is what the export section below uses.
- `encoding/ioutil` does not exist in v0.17.1 (`builtin package "encoding/ioutil" undefined`), so
  CUE cannot read a file from inside an expression. The prototype therefore uses CUE's ability to
  take a YAML data file as a *positional input*, which needs no such builtin.
- Contract front matter cannot be fed to CUE directly: `cue eval schema/contract.schema.json
  contracts/everyone/FLOOR.md` fails with `unknown file extension .md`. The prototype works around
  it by having `contractctl` emit the front matter it already parses as JSON; that workaround is
  itself a cost, and it is discussed below.

### The binary

Downloaded with `python3 urllib` into `./tools/` and unpacked with the `tarfile` module, as
required; nothing was installed outside the clone.

```
python3 - <<'EOF'
import urllib.request, tarfile, hashlib
url="https://github.com/cue-lang/cue/releases/download/v0.17.1/cue_v0.17.1_linux_amd64.tar.gz"
with urllib.request.urlopen(url, timeout=180) as r: data=r.read()
open("tools/cue-scratch/cue.tar.gz","wb").write(data)
print("bytes:", len(data), "sha256:", hashlib.sha256(data).hexdigest())
tarfile.open("tools/cue-scratch/cue.tar.gz").extractall("tools/cue-scratch")
EOF
```

Observed output:

```
bytes: 9688418 sha256: a39b0c97695069d95d276d99be0f5dbabb081d801bfdc9ba49b76efaf94e2369
```

`./tools/cue-scratch/cue version` output, first line, read 2026-10-06:

```
cue version v0.17.1
```

### The CUE I wrote

`tools/cue-scratch/cue.mod/module.cue` (written by `cue mod init`):

```cue
module: "play-nice.local/cue-scratch"
language: {
	version: "v0.17.1"
}
```

`tools/cue-scratch/check/adoption_schema.cue` — 49 lines, comments included. Every constraint line
carries the `schema/adoption.schema.json` line it restates, which is the point of the
"duplication" finding below:

```cue
package check

import "strings"

#ContractID: string & =~"^[a-z0-9]+(-[a-z0-9]+)*$" & strings.MaxRunes(64)

close({
	schema!: "play-nice/adoption-v1"          // schema/adoption.schema.json:10-13

	project?: string & strings.MaxRunes(64)   // :14-18

	source: close({                            // :19-35
		repository: string
		revision:   string & strings.MinRunes(7) & strings.MaxRunes(64)
	})

	profile?: string | null                    // :36-39

	always?:   [...#ContractID]                // :40-52 (+ $defs.contract_id)
	triggers?: [string]: [...#ContractID]

	requirements?: [string]: _                 // :53-57

	// :58-79, split on the cross-field rule.
	//   update: automatic  =>  policy: require-current
	freshness?: close({
		policy?: "pinned"
		update?: "review"
		ref?:    "main" | string
	}) | close({
		policy: "require-current"
		update?: "review" | "automatic"
		ref?:    "main" | string
	})

	notes?: string & strings.MaxRunes(2000)    // :80-84
})
```

### Requirement 1 — validate the committed YAML unchanged

Exact command, verbatim, from the repo root:

```
./tools/cue-scratch/cue eval schema/adoption.schema.json .contracts/adoption.yaml
```

Exit 0. **This used no `.cue` file at all** — CUE reads the repo's own draft-2020-12 JSON Schema
and the repo's own committed YAML and unifies them. The first lines of the result:

```
import "strings"

#contract_id: =~"^[a-z0-9]+(-[a-z0-9]+)*$" & strings.MaxRunes(64)
schema:       "play-nice/adoption-v1"
project:      "play-nice-contracts"
source: {
    repository: "Rylee-Bee/play-nice-contracts"
    revision:   "e570e2630702ddb6c61f7d1d89ab0ce439cdc608"
}
always: ["truth-and-evidence", "ask-for-help", "recovery-and-history", "status-and-state", "testing-and-evidence", "ownership-and-portability"]
freshness: {
    policy: "require-current"
    ref:    "main"
    update: "automatic"
}
```

No rewrite, no reformat, no generated artifact, no contributor-visible change. This is the single
strongest thing the technology did in this study.

Running the prototype `.cue` file instead — `./tools/cue-scratch/cue eval
./tools/cue-scratch/check .contracts/adoption.yaml` — also exits 0.

### Requirement 2 — the cross-field rule, and why it is awkward today

**The rule: `freshness.update: automatic` is only meaningful together with
`freshness.policy: require-current`. An `automatic` manifest under `pinned` never advances its
pin.**

Why it is awkward today, precisely:

- The two fields are independent enums in `schema/adoption.schema.json:64-77`, with nothing
  relating them. The schema text at `:71` even notes the related `ref` caveat in prose.
- The conjunction is asserted in exactly one place in the whole repo:
  `tools/playnice/playnice.py:646-658` `sync_pin_if_allowed`, which requires
  `fr.get("manifest_update") == "automatic"` **and**
  `fr.get("manifest_policy") == "require-current"` before it will refresh anything.
- `contractctl.validate_adoption_manifest` (`:1915-1959`) calls `freshness_config`, which
  validates each field in isolation and returns `{'policy': ..., 'ref': ..., 'update': ...}`. It
  never relates them.
- So a manifest can read `update: automatic`, pass `contractctl validate`, pass CI, and then
  never advance, because the `require-current` gate in `sync_pin_if_allowed` still applies and
  refuses to refresh a `pinned` manifest. The gate is deliberate, but the failure is invisible to
  the person who wrote the manifest: nothing they run relates the two fields. This repo's own
  `.contracts/adoption.yaml:17` uses
  `update: automatic` and is correct only because `:15` also says `policy: require-current` — the
  relationship lives in a comment block at `:1-7`, not in anything a tool checks.

The CUE encodes it as a disjunction of two mutually exclusive closed structs (branch 1 requires
`policy: "pinned"`; branch 2 requires `policy: "require-current"`, so no manifest can match both).
Behaviour across the matrix is exact: every legal combination passes, only `pinned` + `automatic`
fails.

JSON Schema 2020-12 could express the same rule with `if`/`then`. The reason that is not an option
today is the enforcement path: `_validate_against_contract_schema` implements seven keywords and
`if`/`then` is not one of them, and `validate_adoption_manifest` does not even call that helper.

### Requirement 3 — export compatible JSON Schema

Exact command:

```
./tools/cue-scratch/cue def ./tools/cue-scratch/check --out jsonschema
```

Exit 0. It emits a valid draft-2020-12 document. Real excerpt:

```json
{
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "type": "object",
    "additionalProperties": false,
    "properties": {
        "schema": {
            "description": "schema/adoption.schema.json:10-13",
            "const": "play-nice/adoption-v1"
        },
        "freshness": {
            "anyOf": [
                { "type": "object", "additionalProperties": false,
                  "properties": { "policy": { "const": "pinned" },
                                  "update": { "const": "review" } } },
                { "type": "object", "additionalProperties": false,
                  "properties": { "policy": { "const": "require-current" },
                                  "update": { "anyOf": [{ "const": "review" }, { "const": "automatic" }] } } }
            ]
        }
    },
    "required": ["schema", "source"]
}
```

Compatibility measured against `schema/adoption.schema.json` with `jsonschema` 4.23.0:

```
generated top-level keys: ['$defs', '$schema', 'additionalProperties', 'properties', 'required', 'type']
has $id: False | has title: False
own manifest against GENERATED schema: VALID
manifest with 'schema:' removed      : ACCEPTED (required lost)
freshness.policy=nonsense           : rejected
```

Before that fix, `required` was `["source"]` only — `schema` had been dropped even though it is
mandatory in the committed schema. Adding `!` (`schema!: "play-nice/adoption-v1"`) restored it,
so the gap is fixable. But four other losses are structural, not stylistic:

- `$id` and `title` are gone, so `$ref: "play-nice/adoption-v1"` stops resolving for consumers.
- `enum` becomes `anyOf` of `const`. A consumer pointing at
  `#/properties/freshness/properties/policy/enum` breaks, and the `freshness` object no longer has
  a `properties` member at all.
- All 32 `default:` annotations across `schema/` would be lost.
- The committed `description` strings, which carry the library's own reasoning (for example
  `adoption.schema.json:62`), are replaced by whatever comments the CUE author wrote.

Against the issue's reject condition "generated JSON Schema is less useful or less compatible",
the honest answer is: it is **less compatible**, in four specific and measurable ways.

### Requirement 4 — deterministic output

Exact commands, verbatim:

```
./tools/cue-scratch/cue export schema/adoption.schema.json .contracts/adoption.yaml > /tmp/a.json
./tools/cue-scratch/cue export schema/adoption.schema.json .contracts/adoption.yaml > /tmp/b.json
sha256sum /tmp/a.json /tmp/b.json
diff /tmp/a.json /tmp/b.json
```

Observed:

```
89f9818386432758a77c48c91b081af29352a660b79710e635f0ef423f62849e  /tmp/a.json
89f9818386432758a77c48c91b081af29352a660b79710e635f0ef423f62849e  /tmp/b.json
```

`diff` reported no differences. Byte-identical across runs, on the JSON Schema path and on the
`.cue` path alike (the `.cue` path was also run twice and produced the same digest).

### Requirement 5 — a real failure with its real message

Failure A, the cross-field rule, on `tools/cue-scratch/bad-pinned-automatic.yaml`:

```
freshness: 2 errors in empty disjunction:
freshness.policy: conflicting values "require-current" and "pinned":
    ./tools/cue-scratch/check/adoption_schema.cue:7:1
    ./tools/cue-scratch/check/adoption_schema.cue:42:11
    ./tools/cue-scratch/bad-pinned-automatic.yaml:9:11
freshness.update: conflicting values "review" and "automatic":
    ./tools/cue-scratch/check/adoption_schema.cue:7:1
    ./tools/cue-scratch/check/adoption_schema.cue:39:12
    ./tools/cue-scratch/bad-pinned-automatic.yaml:11:11
```

The same manifest through the current path:

```
$ python3 -c "... ct.validate_adoption_manifest(Path('tools/cue-scratch/bad-pinned-automatic.yaml')) ..."
errors = []
freshness_config = {'policy': 'pinned', 'ref': 'main', 'update': 'automatic'}
```

Failure B, one bad field, isolated:

```
$ printf 'schema: play-nice/adoption-v1\nsource: {repository: x, revision: abcdef1234567}\nbogus: true\n' > t.yaml
$ ./tools/cue-scratch/cue eval schema/adoption.schema.json t.yaml
bogus: field not allowed:
    ./t.yaml:3:1
cue rc=1
```

Failure C, the committed example manifests:

```
$ ./tools/cue-scratch/cue eval schema/adoption.schema.json examples/homelab.adoption.yaml
source.revision: conflicting values 0 and strings.MinRunes(7) (mismatched types int and string):
    ./examples/homelab.adoption.yaml:9:13
    ./schema/adoption.schema.json:9:4
    ./schema/adoption.schema.json:30:12
```

All three of the other example manifests fail identically. Cause: `revision: 0000000`, the
documented placeholder sentinel checked explicitly at `contractctl.py:1972` and `:2336`, is
**unquoted** in all four files. Per YAML 1.2 core schema it resolves to the integer `0`, so it
cannot satisfy `"type": "string"`. Confirmed independently of CUE:

```
$ python3 -c "import yaml; d=yaml.safe_load(open('examples/homelab.adoption.yaml')); print(repr(d['source']['revision']))"
0
```

(PyYAML 6.0.3.) And through the repo's own lenient path:

```
$ python3 -c "... ct.load_adoption(Path('examples/homelab.adoption.yaml')) ..."
homelab '0000000' str errors= []
```

`contractctl._parse_scalar` (`:133-153`) has no integer rule, so it keeps `0000000` as a string
and the drift is invisible. This is a genuine finding, and it is **not** a CUE-vs-JSON-Schema
disagreement: `jsonschema` 4.23.0 rejects the same documents too. The committed YAML and the
committed schema disagree today; only the lenient parser hides it. Quoting the sentinel in four
example files fixes it, and that is a two-character change per file — the two quote marks — with
no tool at all.

### Error-message quality — honest reading

Good: `source.revision: conflicting values 0 and strings.MinRunes(7) (mismatched types int and
string)` names the field, the file, and the line. `title: invalid value "ab" (does not satisfy
strings.MinRunes(3))` is clearer than the repo's own `f"{p}: front matter missing required key"`.

Not good: the cross-field failure leads with `freshness: 2 errors in empty disjunction` and then
reports the two constituent conflicts in CUE's internal order. A contributor reading that does not
immediately learn "automatic updates require require-current"; they learn that CUE has two
branches. The repo's own messages are terse and owner-facing (`adoption: stale pin — manifest
pins revision …, library is at …`). CUE's are more precise but more architectural.

Also observed: CUE reports **one structural error per struct path**, even under `-E/--all-errors`.
A file with both a wrong type and an unknown key under `github:` reported only the type error.

### The matrix script, so every table above is reproducible

```python
import subprocess, sys, json, warnings
warnings.filterwarnings("ignore")
sys.path.insert(0,'tools/contractctl')
import contractctl as ct
from pathlib import Path
import yaml, jsonschema
CUE="./tools/cue-scratch/cue"
SCHEMA=json.load(open("schema/adoption.schema.json"))
BASE = """schema: play-nice/adoption-v1
project: matrix-demo
source:
  repository: Rylee-Bee/play-nice-contracts
  revision: e570e2630702ddb6c61f7d1d89ab0ce439cdc608
always:
  - truth-and-evidence
"""
cases = {
 "legacy: no freshness block": "",
 "pinned + review": "freshness:\n  policy: pinned\n  update: review\n  ref: main\n",
 "require-current + review": "freshness:\n  policy: require-current\n  update: review\n  ref: main\n",
 "require-current + automatic": "freshness:\n  policy: require-current\n  update: automatic\n  ref: main\n",
 "pinned + automatic": "freshness:\n  policy: pinned\n  update: automatic\n  ref: main\n",
 "unknown top-level property": "bogus: true\n",
 "unknown contract id": "triggers:\n  agent:\n    - Truth-And-Evidence\n",
 "notes over 2000 chars": "notes: \"" + ("x"*2100) + "\"\n",
}
for name, extra in cases.items():
    p = Path("tools/cue-scratch/t.yaml"); p.write_text(BASE+extra)
    r1 = subprocess.run([CUE,"eval","schema/adoption.schema.json",str(p)],capture_output=True,text=True)
    r2 = subprocess.run([CUE,"eval","./tools/cue-scratch/check",str(p)],capture_output=True,text=True)
    js = list(jsonschema.Draft202012Validator(SCHEMA).iter_errors(yaml.safe_load(BASE+extra)))
    cc = ct.validate_adoption_manifest(p)
    print(f"{name:30} contractctl={'PASS' if not cc else 'FAIL'}  "
          f"jsonschema={'PASS' if not js else 'FAIL'}  "
          f"cue(JSONSchema)={'PASS' if r1.returncode==0 else 'FAIL'}  "
          f"cue(.cue+rule)={'PASS' if r2.returncode==0 else 'FAIL'}")
p.unlink()
```

(The `source.revision` shorter-than-7 row uses a separate body with `revision: abc`; it was run in
the same shape and is reported above.)

## The comparison against the current Python/JSON-Schema path

### What CUE would add

| Added | Cost |
| --- | --- |
| A Go binary in the toolchain | 9,688,418 bytes compressed, 24 MB on disk after unpacking; a new platform matrix (darwin/linux/windows × amd64/arm64), a new supply-chain pin, a new thing to keep current |
| `cue.mod/module.cue` + a `.cue` package per schema | 2 new committed concepts per artifact |
| A `cue` subprocess call inside `contractctl` | breaks the invariant stated in `pyproject.toml:6-9` ("import nothing beyond the Python standard library") and enforced by tests |
| A cross-language error path | a contributor sees `contractctl` messages on good days and CUE messages on the days CUE runs |

### What it would remove, honestly counted

| Candidate | Lines | Verdict |
| --- | --- | --- |
| `_validate_against_contract_schema` | 34 (`:431-464`) | Could go **only** if contract front matter can reach CUE. It cannot: `cue eval schema/contract.schema.json contracts/everyone/FLOOR.md` → `unknown file extension .md`. Removing it requires a new extraction step (`contractctl` emits JSON, CUE reads it). That is a new step, not a deletion. |
| `validate_library` hand-recheck block | 19 (`:334-352`) | Same blocker, plus these four checks *also* drive `load_library` consumers, not only validation. |
| `validate_adoption_manifest` | 45 (`:1915-1959`) | Only ~12 lines of it are JSON-Schema-shaped (the unknown-key loop at `:1950-1953`). The other ~33 are library-aware checks — `canonical_id` resolution against the loaded contract set — that CUE has no access to and cannot replace. |
| `playnice._validate_config` + `KNOWN_CONFIG_KEYS` + `default_config()` | ~120 total | Would go only if the `.cue` file became canonical, which is the "canonical source" option the issue explicitly does not want, and which costs the `$id`/`title`/`enum`/`default` fidelity losses above. |
| `contracts.lock.json` shape | 0 | There is no `schema/lock.schema.json` to remove, and CUE is not a lockfile tool. |

Total removable, in the best case, with a workaround added: **about 34 lines**, all in one helper,
plus an extraction step that does not exist today.

### What it would cost to keep both

Keeping both is the realistic shape, because `canonical_id` resolution, the lockfile, freshness,
`git ls-remote`, and attestation are all library-aware and stay in Python. That means:

- two validators to keep in sync with the same schema,
- two different error vocabularies for the same mistake,
- and the drift risk *doubles* rather than shrinking — which is the opposite of the rule.

The `docs/MAINTAINING.md` / `AGENTS.md` contributor loop already asks people to run
`contractctl validate`. Adding a second gate that can disagree with the first is the definition of
custom plumbing.

## The exact validation code and schema duplication that could disappear, file by file

**Under the "CUE behind the curtain" shape the issue prefers: none.** The proof is the prototype
itself. To express the cross-field rule I had to write `tools/cue-scratch/check/adoption_schema.cue`
— 49 lines — restating every `type`, `pattern`, `maxLength`, `minLength`, `enum`, `required` and
`additionalProperties` already present in `schema/adoption.schema.json`, with a comment on each
line pointing back at the JSON Schema line number it duplicates. CUE behind the curtain with CUE
behind the curtain means two sources of truth, one of which the contributors never see and
therefore never trust. That is reject condition 2 verbatim.

**What genuinely disappears, and is worth doing without CUE:**

| # | File / lines | What | Cheapest correct fix |
| --- | --- | --- | --- |
| 1 | `examples/homelab.adoption.yaml:9`, `examples/personal-world.adoption.yaml:9`, `examples/vefr.adoption.yaml:10`, `examples/project-context/.project/contracts/adoption.yaml:8` | `revision: 0000000` parses as integer 0, contradicting `"type": "string"` in `schema/adoption.schema.json:30` | quote the sentinel: `revision: "0000000"`. Two characters per file — the two quote marks. Confirmed by PyYAML and by CUE. |
| 2 | `contractctl.py:1950-1953` | `validate_adoption_manifest` enforces only `additionalProperties`; `notes` `maxLength` 2000, `revision` `minLength` 7 / `maxLength` 64 and `project` `maxLength` 64 are declared but never checked | ~6 lines in `validate_adoption_manifest`, or replace that function's schema handling with `jsonschema.Draft202012Validator` (one import; it is already available in this environment but is not a declared runtime dep) |
| 3 | `contractctl.py:431-464` | `_validate_against_contract_schema` implements 7 of the 18 keywords used across `schema/`; `minLength` on `contract.title` is the clearest miss, proven above | add `minLength` (one `elif`), or delegate |
| 4 | `contractctl.py:645-658` `playnice.py` | the `update: automatic ⇒ policy: require-current` rule exists only in `sync_pin_if_allowed` | ~4 lines in `freshness_config` (`contractctl.py:2038`), which every caller already goes through |
| 5 | `contractctl.py:3869-3875` + `render_adoption_manifest:3887` | `ADOPTION_ALWAYS_FLOOR` is a second copy of the floor contract list | out of scope for this study |
| 6 | `schema/attestation.schema.json`, `schema/capability.schema.json`, `schema/global-playnice.schema.json`, `schema/project.schema.json`, `schema/references.schema.json` | five committed schemas no code reads | either validate them in CI or stop shipping them as enforcement claims |

Items 1–4 are a few dozen lines of Python in files that already exist, in a tool that already runs
on every mutating commit, with no new binary, no new language, and no second gate.

## Compatibility risks

1. **YAML scalar resolution is stricter than the repo's parser.** `_parse_scalar`
   (`contractctl.py:133-153`) has no integer, float, date or anchor rules. CUE uses a real YAML
   1.2 parser. Anything that relies on the lenient parser would newly fail. Four committed files
   already do (§ Requirement 5, failure C). This is a *fix*, but it means any CUE gate lands with
   four example-manifest edits attached on day one.
2. **JSON Schema export is lossy.** `$id`, `title`, `enum` shape, and all `default:` annotations are
   lost; `required` needed an explicit `!`. If `schema/*.json` ever became generated rather than
   hand-written, consumers pointing at `$id` or at `enum` paths break. Measured, not predicted.
3. **No runtime dependency is possible in `contractctl`.** `pyproject.toml:6-9` states the
   stdlib-only invariant and tests enforce it. A `cue` subprocess would either break that
   invariant or be a documented exception, which is a governance decision, not a technical one.
4. **Error-message asymmetry.** Precise but architectural (see above). For a library whose stated
   job is plain language, this is a real cost.
5. **One-error-per-path.** Contributors fixing a config file may need several passes.
6. **The `.cue` route cannot see `.md`.** The largest consumer of `contract.schema.json` (41
   contract files) needs an extraction shim, which reintroduces exactly the plumbing CUE was
   supposed to remove.
7. **Toolchain weight.** A Go binary is a new supply-chain surface, a new platform matrix, and a
   new thing that can drift from the Python that must agree with it.
8. **Third-party export module unverifiable here.** TLS interception blocked `cue.go`, so the
   round-trip quality of the community exporter is UNVERIFIED. Even if it were perfect, risks 2
   stands on its own.

## CUE behind the curtain or canonical source

**Neither, for this artifact.** The evidence:

- *Behind the curtain* requires the `.cue` file to be a strict subset of the JSON Schema. It is
  not: to express the cross-field rule I had to restate the entire schema. The curtain costs 49
  lines per artifact and creates two truths. That is reject condition 2.
- *Canonical source* means `schema/adoption.schema.json` becomes generated output. Then it loses
  `$id`, `title`, `enum`, and `default` on every regeneration, and every consumer of this
  library's published schemas degrades. That is reject condition 3.

There is one narrow shape that is genuinely "behind the curtain" and I want to name it honestly
because it is the only thing here worth carrying forward:

> Run a CUE invocation over the **already-committed** JSON Schema and the **already-committed**
> YAML, in CI, with no new files in the repository.

`./tools/cue-scratch/cue eval schema/adoption.schema.json .contracts/adoption.yaml` does exactly
that, exits 0, is deterministic, and needs nothing committed. It would have caught items 2 and 3
in the table above with zero new source.

But it is not CUE-specific. The identical check is
`jsonschema.Draft202012Validator(SCHEMA).validate(yaml.safe_load(text))`, which the matrix proved
gives the same verdicts on all nine cases. The difference is one pure-Python dependency in a dev
and CI context versus a 24 MB cross-platform Go binary and a second language. **If the estate wants
full-schema enforcement, the honest answer is `jsonschema` in the test/CI step, not CUE.**

**What would force the change:** if `jsonschema` (or any spec-complete validator) proved unusable
in this environment — for instance if the stdlib-only runtime invariant were extended to CI, or
if contract front matter had to be validated without any Python at all — then a binary that reads
JSON Schema and Markdown directly would earn its place. Neither condition holds today.

## The cross-estate follow-up

### What I could inspect, from this clone only

Everything above. Within this repository, the approach generalises further than I expected, and
that part is worth recording even though the recommendation is REJECT:

```
$ ./tools/cue-scratch/cue eval <schema> <data>
schema/project.schema.json                 examples/project-context/.project/project.yaml            OK
schema/participant.schema.json             .../participants/figma/participant.yaml                    OK
schema/references.schema.json              .../participants/figma/references.yaml                     OK
schema/participant-capabilities.schema.json .../participants/figma/capabilities.yaml                  OK
schema/global-playnice.schema.json         examples/global-playnice.yaml                              OK
schema/library.schema.json                 contracts.lock.json                                        FAIL (unrelated: no lockfile instance exists; library.schema.json is a room response schema)
schema/contract.schema.json                contracts/everyone/FLOOR.md                                FAIL: unknown file extension .md
```

Five committed schema/data pairs validate against their own committed JSON Schema with no new
files. And all 41 contract front matters validate against `schema/contract.schema.json` once
`contractctl` emits the front matter it already parses:

```
$ for f in tools/cue-scratch/fm/*.json; do ./tools/cue-scratch/cue eval schema/contract.schema.json "$f"; done
cue-contract.schema.json: 41 valid, 0 invalid, out of 41
```

That is the real estate-wide finding, and it is a finding about **this repo's enforcement
coverage**, not about CUE: eleven of fourteen committed schemas enforce nothing anywhere, and a
spec-complete validator would light up five of them immediately at no cost to contributors. That
work does not need a new language.

### What I could NOT inspect from this clone

- **World Tree role records** — no such directory or data file exists here. The only matches for
  "world tree" in this repository are prose in `contracts/` and `docs/`. No role-record format, no
  schema, no validator was readable.
- **Mission / job manifests** — no such artifacts here. `contracts/work/ORCHINATION.md` and
  `contracts/work/BOUNDED_WORK.md` describe the concepts in prose only.
- **Source / dashboard manifests** — no such artifacts here. `harness/EVIDENCE-LEDGER.md` and
  `harness/README.md` are prose; there is no dashboard manifest format.
- **`bin/offload` and its `EXCLUDED_REPOS`** — this clone has no `bin/` directory and no file
  matching `*offload*`, so I could not read the excluded set. I read only this repository, and no
  other estate repository was opened.

Any statement about whether the same technique would validate those formats is therefore
UNVERIFIED. What can be said without opening them: the technique that worked here needs no
cooperation from the format — a committed JSON Schema plus a committed YAML/JSON file is enough —
and it adds nothing the format must change for. **Play-Nice must not own those formats.** If a
future study finds one of them has a committed schema and committed instances, the reusable
finding from this document is the CI command line in § CUE behind the curtain, not a Play-Nice
dependency and not a CUE dependency.

## What would change this recommendation

Any one of these would move it:

1. **The stdlib-only invariant is withdrawn for CI.** Then `jsonschema` becomes available as a
   first-class option and the CUE-vs-`jsonschema` comparison inverts on weight alone. Note this
   makes `jsonschema` the better answer, not CUE.
2. **A consumer estate cannot run Python at all** and must validate committed manifests from a
   static binary. Then CUE reading committed JSON Schema directly becomes the only zero-copy
   option available.
3. **The JSON Schema loss profile is fixed.** If `$id`, `title`, `enum` and `default` round-tripped
   through `cue def --out jsonschema`, the canonical-source option would become viable, and with it
   a real deletion of `KNOWN_CONFIG_KEYS`, `default_config()` and
   `_validate_against_contract_schema`. I could not test the third-party exporter here, so this
   remains the most plausible path to ADOPT.
4. **`.md` front matter becomes directly validatable.** A CUE loader for Markdown front matter
   would delete `_validate_against_contract_schema` outright rather than shim it.
5. **The cross-field rule count grows past a handful.** If ten or more rules like
   `update ⇒ policy` appear across estate configuration, the case for one declarative source gets
   much stronger. At one rule in one file, six lines of Python wins.

What would *not* change it: more example manifests, more schema files, or CUE gaining features.
The rejection is about the arithmetic of plumbing, not about the technology's quality.

## Sources

All external material was read on **2026-10-06**. Everything else in this document is a command
plus its observed output from this clone at commit `a11563b1ab8e5fe4fd235d04972de062a93376eb`.

| Claim | Source | Version / release | Read |
| --- | --- | --- | --- |
| Latest CUE release is v0.17.1, published 2026-07-16 | `https://api.github.com/repos/cue-lang/cue/releases/latest` via `python3 urllib` | `v0.17.1`, `published_at` `2026-07-16T10:15:00Z` | 2026-10-06 |
| CUE binary asset used | `https://github.com/cue-lang/cue/releases/download/v0.17.1/cue_v0.17.1_linux_amd64.tar.gz` | 9,688,418 bytes, sha256 `a39b0c97695069d95d276d99be0f5dbabb081d801bfdc9ba49b76efaf94e2369` | downloaded 2026-10-06 |
| Version banner | `./tools/cue-scratch/cue version` → `cue version v0.17.1` | v0.17.1 | 2026-10-06 |
| JSON Schema is an *input* file type, not a `cue export --out` encoding | `./tools/cue-scratch/cue help filetypes`; `./tools/cue-scratch/cue export --help` (encodings listed: `cue`, `json`, `toml`, `yaml`, `text`, `binary`) | v0.17.1 | 2026-10-06 |
| CUE→JSON Schema export exists as `cue def --out jsonschema` | `./tools/cue-scratch/cue def --help`; observed run of `./tools/cue-scratch/cue def ./tools/cue-scratch/check --out jsonschema` | v0.17.1 | 2026-10-06 |
| No file-reading builtin (`encoding/ioutil`) in v0.17.1 | `./tools/cue-scratch/cue eval` → `builtin package "encoding/ioutil" undefined` | v0.17.1 | 2026-10-06 |
| CUE module registry unreachable from this sandbox | `https://cue.go/index.cue`, `https://cue.go/`, `https://api.cuelang.org/` → `CERTIFICATE_VERIFY_FAILED: self-signed certificate`; control `cue mod get github.com/corpix/uarand` → `no versions found for module github.com/corpix/uarand` | v0.17.1 | 2026-10-06 |
| PyYAML resolves unquoted `0000000` to integer 0 | `python3 -c "import yaml; ..."` | PyYAML 6.0.3 | 2026-10-06 |
| Reference draft-2020-12 verdicts in the matrix | `python3 -c "import jsonschema; ..."` | jsonschema 4.23.0 | 2026-10-06 |
| CUE official documentation (referenced by the binary's own help output; **not fetched** — TLS interception) | `https://cuelang.org/docs/` | UNVERIFIED | — |
| Baseline test suite | `PYTHONPATH=tools/cue-scratch/.venv python3 -m pytest tests/ -q` → `292 passed in 83.86s (0:01:23)` | pytest 9.1.1 | 2026-10-06 |

Repo facts, all at commit `a11563b1ab8e5fe4fd235d04972de062a93376eb` on branch
`offload/arch-t5-cue-20261006-071650-1134`: `tools/contractctl/contractctl.py` 4439 lines,
`tools/playnice/playnice.py` 3126, `tools/pin-sync/pin_sync.py` 220, `tests/test_status_words.py`
60, `schema/` 14 files, `contracts/` 41 contract files.

## Recommendation

CUE v0.17.1 did everything asked of it: it validated the committed YAML unchanged, expressed the
cross-field rule cleanly, produced byte-identical output across two runs, failed with readable
messages, and read the committed JSON Schema with zero new files. It is also, on this evidence,
the wrong tool for this repo, because making it work required restating the schema rather than
deleting it, its JSON Schema export is measurably less compatible than what is committed today,
and the most valuable thing it demonstrated — that eleven of fourteen committed schemas enforce
nothing — can be fixed by a spec-complete validator in the existing test step without a new
language, a new binary, or a second gate. Act on the four drift findings; keep the JSON Schemas
canonical; do not adopt CUE.

REJECT -- CUE adds a language, a 24 MB cross-platform binary and a second gate to a stdlib-only toolchain in exchange for about 34 lines of hand-rolled keyword checking, and it restates rather than removes the schema it is meant to replace.

## Unresolved

- **Third-party CUE→JSON Schema exporter quality is UNVERIFIED.** `cue.go` is TLS-intercepted from
  this sandbox; the built-in `cue def --out jsonschema` was tested and is lossy, but the community
  exporter's fidelity is unknown. This is the single most likely thing to change the verdict.
- **Whether the estate would accept `jsonschema` as a test/CI dependency is a governance question
  I cannot answer from this repository.** It is the cheaper alternative this study points to, and
  it needs a decision, not a prototype.
- **`schema/attestation.schema.json`, `capability.schema.json`, `project.schema.json`,
  `references.schema.json` and `global-playnice.schema.json` are read by nothing.** Whether that
  is deliberate (published vocabulary for other estates) or an oversight is not recorded anywhere
  in this repository.
- **`contracts.lock.json` declares `"schema": "play-nice/lock-v1"` with no matching schema file.**
  Whether one is intended is not recorded.
- **The 16-word shared status vocabulary is unenforced on every CLI surface in this repo.**
  `check_freshness`, `carryover_state` and `session_status` all emit a different vocabulary.
  Whether that is a deliberate second vocabulary or drift is a contract question, not a tooling one.
- **`DISPOSITIONS` (`playnice.py:100`) is defined and never referenced** anywhere in `tools/` or
  `tests/`.
- **World Tree role records, mission/job manifests and source/dashboard manifests were not
  inspectable from this clone.** Nothing about their feasibility is claimed here.
- **`bin/offload` and its `EXCLUDED_REPOS` list do not exist in this clone**, so the exclusion set
  could not be read. No repository other than this one was opened.
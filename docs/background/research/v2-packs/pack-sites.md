# Pack review: sites

Reviewed 2026-09-26 for the Play-Nice v2 merge plan, step 3
(docs/decisions/2026-09-26-play-nice-v2.md). The Sites pack is **new**:
the contracts map found no contract for websites being friendly to agents
(section 1, "no contract for websites being friendly to agents"), so nothing
was merged in and no source files were deleted.

## Old id -> new id

| old id | new id | note |
|---|---|---|
| (none — new contract) | friendly-site (1.0.0) | `contracts/sites/FRIENDLY_SITE.md` |

Closest existing contracts, deliberately **not** touched or merged: `web-ui`
(page behaviour for a person), `accessibility-floor` (People pack depth),
`machine-readable-output` and `human-and-machine-parity` (tool output, not
site publishing). The new contract links to the floor (rules 13, 14) instead
of restating them.

## Rules dropped or changed in meaning

None — there are no source contracts to drop from. Every rule in
`friendly-site` comes from the owner-approved plan, step 3 brief: semantic
HTML and labels, no-script content, promised machine views stay truthful,
`/llms.txt` (SHOULD, per the plan's "recommended"), the well-known file with
version/packs/contact/expires, the A2A card link, robots.txt and rate limits,
no hidden agent-directed prompt text, no dark patterns, stable URLs,
accessibility by pointer.

## Stale references found

- `schema/contract.schema.json` `layer` enum and `contractctl.py` `LAYER_DIRS`
  (line 49) have no `sites` value, so `contractctl validate` currently ignores
  `contracts/sites/` entirely — it reports "VALID — 68 contracts" and never
  reads the new file. Integration must add `sites` to both, then re-lock and
  re-index. Expected; the orchestrator owns tool and schema edits.
- `CONTRACT_INDEX.md` and `contracts.lock.json` have no row for
  friendly-site; both need regeneration at integration.
- `playnice check` (named in "You're done when") does not exist yet —
  `tools/playnice/playnice.py` currently has only `work`, `status`,
  `reconcile`. It arrives with plan step 4. The contract text names the
  command the plan promises.
- Receipt `sparrow-thistle-cove` is new: checked against every existing
  `contract-receipt` comment and against the receipt words used in
  `tests/test_library.py` / `tests/test_playnice.py`; no collision.

## Checks run on the new files

- Headings present in order: In short, Applies when, Rules (12), Examples,
  Why, You're done when, Machine notes.
- `grep -c "contract-receipt" contracts/sites/FRIENDLY_SITE.md` = 1.
- Body 653 words (target ≤800).
- `schema/play-nice-site.schema.json` parses as JSON (draft 2020-12).

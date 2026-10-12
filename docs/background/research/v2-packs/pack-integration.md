# Pack review: integration (Play-Nice v2, step 3)

Rewritten 2026-09-26 on branch `pack/integration`. Eight contracts in
`contracts/interoperability/` became four in `contracts/integration/`, at
version 2.0.0 with new receipts. `FAILURE_AND_DEGRADATION.md` is **not** part
of this pack and was left in place.

## Old id → new id

| old id (deleted file) | new id (new file) |
|---|---|
| capability-first (CAPABILITY_FIRST.md) | capabilities-not-vendors (CAPABILITIES_NOT_VENDORS.md) |
| provider-neutrality (PROVIDER_NEUTRALITY.md) | capabilities-not-vendors |
| friendly-api-client (FRIENDLY_API_CLIENT.md) | calling-other-services (CALLING_OTHER_SERVICES.md) |
| external-mutations (EXTERNAL_MUTATIONS.md) | calling-other-services |
| idempotency (IDEMPOTENCY.md) | calling-other-services |
| polling-webhooks-and-caching (POLLING_WEBHOOKS_AND_CACHING.md) | events-and-caching (EVENTS_AND_CACHING.md) |
| versioning-and-compatibility (VERSIONING_AND_COMPATIBILITY.md) | versions-and-discovery (VERSIONS_AND_DISCOVERY.md) |
| discovery-and-negotiation (DISCOVERY_AND_NEGOTIATION.md) | versions-and-discovery |

Receipts: `sundial-alder-ferry`, `kiln-larch-copper`, `thistle-tidemark-roost`,
`signpost-alabaster-crag` (all checked unused in this repo).

## Rules dropped or changed in meaning

**capabilities-not-vendors**
- capability-first 1 (shape/anti-shape diagrams) → rule 2 in prose; diagrams are tool-doc material, the rule survives.
- capability-first 6 (`native`/`enrichment`/`replacement` mode vocabulary) → kept only as "optional providers, rare required" (rules 7–8); the closed three-word enum was dropped as invented jargon.
- capability-first 8's cite of `schema/capability.schema.json` → dropped; the meaning ("vendor fields namespaced, never canonical") is kept as rule 4.
- provider-neutrality 6 (neutral UI wording) → folded into rule 3; plain UI wording is the floor, rule 12's job.
- capability-first 3 (models/tools/humans as providers) → rule 11 in plain words; its cross-packs ("Participation and Contribution; Model Routing") no longer exist post-merge.

**calling-other-services**
- The observe→…→record mutation pipeline appeared word-for-word in two sources (friendly-api-client 8, external-mutations 1) → one rule.
- external-mutations 5 and 7 (human approval, step-up confirmation) → rule 8 in plain words, linked to floor rule 6; "step-up" and "blast radius" jargon replaced. Approval mechanics per se belong to the Access pack's identity-and-access.
- external-mutations 6's "approved boundaries" kept as rule 9 (visible, editable, revocable, journaled); external-mutations 8 kept in rule 9 ("never widens its own authority").
- idempotency 5 (content-hash dedup for appends) → dropped as a standalone rule; covered by rule 10's ensure-semantics; the detail is implementation, not contract.
- friendly-api-client 5 (long list of honored headers) → rule 3; webhook/ETag specifics point to events-and-caching instead of repeating.

**events-and-caching**
- All eight source rules kept. New rule 5 states `stale` explicitly (source rule 3 implied it); new rule 10 promotes the "retry-storm" anti-pattern to a rule. Source rule 3's "(see Truth and Evidence)" now cites floor rule 1.

**versions-and-discovery**
- versioning 8 (semver meanings "across the library") → generalized to any published interface in Machine notes; same semantics, broader addressee.
- versioning 3's "consumers reject what they cannot understand" → merged into rule 5 (fail clearly), one place instead of two.
- discovery 5 ("minimal system is legitimate") → rule 12, meaning unchanged.
- discovery 8 ("Asking is part of negotiation, see Ask for Help") → rule 8; the ask-ladder cross-pack cite was replaced by the floor's rules 2–3, which already cover ask-don't-assume.
- versioning's `contracts.lock.json` mention → generic "pins (exact version + hash)".

## Stale references found

- `DISCOVERY_AND_NEGOTIATION.md:28`: "Negotation" typo inside a normative rule (known in the map) — fixed by the merge.
- `CAPABILITY_FIRST.md:39` cited contracts (`Participation and Contribution`, `Model Routing`) that v2 merges into `contribution` — no longer valid pointers.
- `CAPABILITY_FIRST.md:44` and machine notes cite `schema/capability.schema.json`; the schema still exists but is no longer referenced from a contract — decide during schema integration.
- `POLLING_WEBHOOKS_AND_CACHING.md` ranked `stale` against healthy/unknown, leaning on explicit-state/failure-and-degradation — now expressed via floor rule 8 only.
- Outside this pack, these still reference the deleted ids and need orchestrator integration (alias rows / re-pointing): `CONTRACT_INDEX.md`, `contracts.lock.json`, `CHANGELOG.md`, `.contracts/adoption.yaml`, `examples/*.adoption.yaml`, `examples/session-handoff.md`, `contracts/interfaces/API.md`, `CLI.md`, `ROOM.md`, `contracts/agents/CONTRACT_ATTESTATION.md`, `contracts/core/ASK_FOR_HELP.md`, `contracts/human/INTERRUPTION_AND_RESUMPTION.md`, `schema/room.schema.json`, `docs/PLAY-NICE-OPUS.md`, `docs/principles/trusted-translation.md`, `docs/roles/trusted-steward.md`, `tests/test_library.py`, `tools/contractctl/contractctl.py`.
- `FAILURE_AND_DEGRADATION.md` remains the only file in `contracts/interoperability/`; it belongs to the state-and-status merge in another pack. Flag so the directory isn't mistaken for fully migrated.

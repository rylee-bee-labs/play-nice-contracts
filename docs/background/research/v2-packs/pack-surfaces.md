# Pack review: surfaces

Rewrite per [the v2 plan](../../../decisions/2026-09-26-play-nice-v2.md),
step 3. Nine source contracts merged into seven; one new contract added.
All new files in `contracts/surfaces/`, version 2.0.0 (1.0.0 for the new
one). Nothing committed; deletions are staged `git rm` only.

## Old id -> new id

| old id (file) | new id (file) |
|---|---|
| copy-and-language (experience/COPY_AND_LANGUAGE.md) | plain-language (surfaces/PLAIN_LANGUAGE.md) |
| human-and-machine-parity (interfaces/HUMAN_AND_MACHINE_PARITY.md) | one-truth-two-views (surfaces/ONE_TRUTH_TWO_VIEWS.md) |
| machine-readable-output (interfaces/MACHINE_READABLE_OUTPUT.md) | one-truth-two-views (surfaces/ONE_TRUTH_TWO_VIEWS.md) |
| api (interfaces/API.md) | api (surfaces/API.md) |
| cli (interfaces/CLI.md) | cli (surfaces/CLI.md) |
| web-ui (interfaces/WEB_UI.md) | web-ui (surfaces/WEB_UI.md) |
| room (interfaces/ROOM.md) | room (surfaces/ROOM.md) |
| design-source-and-fidelity (experience/DESIGN_SOURCE_AND_FIDELITY.md) | design-fidelity (surfaces/DESIGN_FIDELITY.md) |
| visual-fidelity-and-composition (experience/VISUAL_FIDELITY_AND_COMPOSITION.md) | design-fidelity (surfaces/DESIGN_FIDELITY.md) |
| — (new) | setup-checks-itself (surfaces/SETUP_CHECKS_ITSELF.md) |

## Rules dropped or changed in meaning

### copy-and-language -> plain-language
- Old rule 2 (errors: what failed, why, what still works, next action)
  compressed to "what happened, then the next step"; the longer failure
  list now lives once, in cli rule 5. One copy, not three.
- Old rule 10 (a documentation-only brevity pass) merged into the general
  shortening rule 5; doc continuity belongs to the WORK pack's
  documentation contract.
- Old rationale's "Words are interface" kept as a plain sentence, not a
  motto (no metaphors in rules, per the floor).

### human-and-machine-parity + machine-readable-output -> one-truth-two-views
- Parity rule 8 (questions carry a `play-nice/question-v1` machine form)
  dropped: the gate-era artifact mechanics were retired by the v2 plan.
- Parity rule 6 ("no undocumented side doors") folded into rules 2 and 12
  (test parity; record deliberate gaps) — same duty, one statement.
- Cross-refs to "Versioning and Compatibility", "Secrets", "Data
  Classification", "Failure and Degradation" removed: those contracts are
  merged or renamed in other packs, so the rules now stand on their own
  or point to the floor.

### api
- **Meaning change (per plan):** errors must now be RFC 9457 problem
  details (`application/problem+json`); old rule kept stable identifiers
  and status codes but no required error body shape. Identifiers ride
  inside the problem object.
- Rationale's "Personal World envelope" history sentence dropped: product
  history, not a rule.
- Refs to "Discovery and Negotiation" / "Idempotency" / "Versioning and
  Compatibility" (Integration-pack material now) made self-contained.

### cli
- "Full six-question error" fixed: the old text cited a six-question
  list that existed nowhere (research §3.5). Rule 5 now names the five
  parts directly — no counted folklore to rot.
- Machine notes ("one CLI framework per project") dropped: implementation
  advice, not a contract.

### web-ui
- All ten rules kept, compressed. Pointer-heavy rules (Explicit State,
  Failure and Degradation, Complexity on Demand, Themes) now name the
  floor status words or the People pack instead of dead ids.
- Machine implications (typed clients, axe-in-CI, fabricated-data tests)
  dropped to tool docs; their duty survives as rules 1 and 10.

### room
- **Fix (per plan):** descriptor status enum was
  `healthy, degraded, unhealthy, unknown`; `unhealthy` is not in
  `schema/status.schema.json`. Now `healthy, degraded, unavailable,
  unknown`, all shared words.
- **Moved (per plan):** old rule 15 ("Worlds MUST support independently
  built … rooms") left the rules; it is now a Machine-notes line
  pointing to the Worlds product spec.
- The five full JSON samples moved to a compact Machine-notes shape
  (schemas stay normative via `schema/room.schema.json`).
- UI tier display names ("NEEDS YOU", "A SMALL UPDATE" …) dropped:
  front-door styling, not interface truth.
- Machine-implications block (idempotency store keys, circuit breaker,
  token checks) folded into rules 8/11/12 or dropped as mechanics.

### design-source-and-fidelity + visual-fidelity-and-composition -> design-fidelity
- Twenty-plus rules from both files merged to thirteen; every duty
  appears at least once.
- The Personal World UAT provenance story dropped; its lesson is the Why
  paragraph (stories off rules, per the design philosophy).
- The "task resolves this contract → VISUAL IMPACT attestation block"
  rule dropped: the eight-step gate and attestation ritual are retired in
  v2; compare-before-code survives as rule 8 and its record as a done-check.
- `design/CURRENT.md` fixed example softened to "one 'what is
  current' pointer" (a convention, not one filename).

### setup-checks-itself (new)
- No sources; content per the v2 plan and the pack brief.

## Stale references found

1. `schema/room.schema.json:16` still lists `unhealthy` in the descriptor
   status enum, contradicting the fixed contract. Not edited here (schema
   is orchestrator-owned): update the enum to `unavailable` and its
   description at integration.
2. `CONTRACT_INDEX.md`, `contracts.lock.json`, `README.md`,
   `docs/QUICK_REFERENCE.md`, `docs/PLAYNICE.md` and several
   still-live contracts (e.g. agents, interoperability, security files)
   link or point-name the nine deleted ids/paths. Expected until
   integration; aliases per the plan will cover the ids.
3. Deleted `interfaces/CLI.md:25` cited the "full six-question error"
   (see cli above) — one of the three places the six-vs-seven conflict
   lived; the other two (failure-and-degradation, observability) sit in
   other packs and still need the same fix there.
4. Deleted `interfaces/ROOM.md:171` was the product-specific rule inside
   a universal contract (research §3.10) — moved, as planned.
5. Deleted `interfaces/HUMAN_AND_MACHINE_PARITY.md:40` referenced
   `play-nice/question-v1` (Ask for Help mechanics) with no live home in
   the v2 shape — dropped here; if Ask-for-Help's rewrite wants question
   parity, it should restate it there.
6. `examples/` and `docs/QUICK_REFERENCE.md` quote the old envelope
   example `{ok, status, changed, warnings, actions, data}` from
   interfaces/API.md; with RFC 9457 errors adopted, those samples will
   need regeneration at integration.

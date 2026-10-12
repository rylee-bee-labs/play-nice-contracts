# Pack review: everyone (Play-Nice v2, step 3)

Branch of work: this pack rewrote 15 source contracts into 7, and moved the
floor into the pack. All merges are version 2.0.0 with fresh receipts; the
floor keeps 1.0.0 and changed only `layer: core -> everyone` (text
untouched). Each file uses the v2 shape from docs/DESIGN_PHILOSOPHY.md.

## Old id -> new id

| old id (file) | new id (file) | kind |
|---|---|---|
| floor (contracts/core/FLOOR.md) | floor (contracts/everyone/FLOOR.md) | moved; text unchanged |
| truth-and-evidence (core) | truth-and-evidence (everyone) | rewritten + merged |
| assume-unknown (core) | truth-and-evidence | merged in; id retired |
| explicit-state (core) | status-and-state | merged; id retired |
| failure-and-degradation (interoperability) | status-and-state | merged; id retired |
| ask-for-help (core) | ask-for-help (everyone) | rewritten (slim) |
| play-nice-together (core) | working-together | merged; id retired |
| collaborative-good-faith (core) | working-together | merged; id retired |
| mutual-contribution (core) | working-together | merged; id retired |
| participation-and-contribution (core) | working-together | merged; id retired |
| recovery-and-reversibility (core) | recovery-and-history | merged; id retired |
| provenance-and-audit (core) | recovery-and-history | merged; id retired |
| migrations (engineering) | recovery-and-history | merged; id retired |
| portability-and-ownership (core) | ownership-and-portability | merged; id retired |
| stable-truth-replaceable-machinery (core) | ownership-and-portability | merged; id retired |
| project-context-and-participant-packs (core) | project-context | rewritten + renamed; id retired |

Old ids stay alias rows for CONTRACT_INDEX.md (orchestrator integrates).

## Correctness fixes from the plan (applied here)

- **Six-vs-seven error questions.** failure-and-degradation rule 4 lists
  seven questions but its own acceptance check (and cli.md:25,
  observability.md:24) said "six". status-and-state keeps the seven-item
  list (rule 8) and its "You're done when" cites "all of rule 8" instead of
  a count, so nothing can rot.
- **ask-for-help count drift.** Rule 9 listed seven question parts but the
  old acceptance check enumerated six (dropping "who is best able to
  answer"). Fixed: rule 5 carries all seven; done-when names the rule.
- **Broken internal pointer.**
  PROJECT_CONTEXT_AND_PARTICIPANT_PACKS.md:53 said "see rule 28 of the
  framework" in a 21-rule contract; the directory-comment reference is gone.

## Rules dropped or changed in meaning (with why)

### truth-and-evidence (truth-and-evidence + assume-unknown)

- "Never present inferred state as observed; label distinctly" (truth r6) —
  folded into the rule-1 classification; one statement, not two.
- truth machine bullets ("APIs must not return cached data marked fresh",
  observed_at/source fields) — moved once into status-and-state rule 3; the
  fields belong to the shared status shape.
- assume-unknown r5's design procedure (compare the full canonical design
  family, frontend bones, retention of components) — generalized to
  "inherited design is a hypothesis"; the design-specific half belongs to
  the Surfaces pack.
- assume-unknown machine line "put assume-unknown in adoption manifests'
  always lists" — dropped: the attestation/gate ritual is retired in v2
  (decision §5) and resolver mechanics are tool docs.
- "Receipts, attestations, commitments and green gates do not certify
  comprehension" (assume-unknown r6) — kept as "a gate proves only what its
  checks cover", stripped of gate vocabulary.
- Rationale case-study links (Workshop v3, named ecosystem projects) —
  stories belong on why pages; the research file stays.

### status-and-state (explicit-state + failure-and-degradation)

- The 15-word shared list is kept exactly as in schema/status.schema.json.
- "State word is the signal; color/icon/position reinforcement"
  (explicit-state r5) — not restated as its own rule; floor rule 14 carries
  it, linked from Applies-when territory.
- "implemented ≠ verified; running ≠ correct" moved out of the word-list
  distinctions into truth-and-evidence rule 4 (where they were also
  stated), so each pair is listed once.
- failure-and-degradation r7 "Level 2 detail" (a progressive-disclosure
  term) — wording dropped, requirement kept.
- Circuit-breaker/timeout budget machine line — dropped; implementation
  guidance for the Surfaces/Integration packs.
- "Errors support recovery, not blame" kept (it was good-faith-adjacent);
  its enforcement details live in working-together.

### ask-for-help (rewritten from ask-for-help only)

- Decision-ladder diagram (KNOW → … → preserve UNKNOWN) — compressed into
  rules 1–2; all five rungs survive as text.
- Scope-negotiation vocabulary (ACCEPT / MODIFY / DECLINE /
  OFFER_ALTERNATIVE / NEEDS_CONTEXT / NEEDS_HELP) and the
  WAITING_FOR_HELP loop cross-reference — negotiation now belongs to
  working-together rule 3; this contract keeps only the help-request side
  (needs-help, waiting-for-help).
- "Asking must feel safe / never ridicule" — moved to working-together
  (rules 5, 10); it is conduct, not question mechanics.
- JSON walkthrough (question-v1 sample, human rendering) — moved to
  Machine notes, one short block, per the brief.
- "Foreman" — renamed "coordinator" (glossary: replace).
- Contract-gate integration bullet (task-impact acknowledgement) —
  dropped; the gate is retired in v2.

### working-together (play-nice-together + collaborative-good-faith + mutual-contribution + participation-and-contribution)

- play-nice-together r2/r3 (no first-class/second-class surfaces; the
  long "expose…" list) — covered by floor rule 13 and the Surfaces pack;
  not restated.
- play-nice-together r8/r9/r13 — pointer rules to ask-for-help,
  project-context and truth-and-evidence; replaced by actual cross-links.
- good-faith's "not nice at all costs" preamble and the
  CLEAR+HONEST+RESPECTFUL+USEFUL formula — framing, not rules; the
  behavior survives in rules 9–13.
- good-faith r10 "yes, and" scripting and r4's worked density critique —
  etiquette examples per the contracts map; dropped.
- good-faith machine guard "Do NOT build sentiment scoring / civility
  points / moderation infrastructure" — dropped from the rules; v2
  contracts state behavior, and tool scope is in tool docs (decision §5:
  lighter proof, no enforcement ritual).
- good-faith r16 attribution example (visual concept: Figma; …) —
  generalized into rule 12.
- mutual-contribution's NEED→OFFER→…→VERIFY loop diagram — prose rule 3.
- mutual-contribution's closed word list (OFFERED/ACCEPTED/…/PARTIAL) —
  rendered in plain words (rules 3/5); no new tooling vocabulary is
  asserted in this pack. If the tooling keeps these states, the index/
  schema can preserve them separately.
- participation's ladder and pipeline diagrams — one prose rule 7.
- participation r21 "No token burn for status: when a contribution is
  complete, STOP" — dropped; floor rule 9 ("stopping is success") already
  covers it, and BOUNDED_WORK (Agents-and-work pack) owns the budget side.
  Flagging it because it is the only truly *removed* idea, not a restated
  one.
- r21's agreement-vs-authorization distinction was stated three times
  (mutual r21, authorization, floor 5) — kept once (rule 15).

### recovery-and-history (recovery-and-reversibility + provenance-and-audit + migrations)

- provenance r5 "provenance must stay reachable, not loud (a drawer, an
  endpoint)" — dropped from rules; it is presentation behavior owned by
  the People pack (quiet-when-healthy merge).
- migrations machine bullets (feature-flag expiry, dual-run tooling,
  evidence-grade references) — dropped as tooling mechanics; the six-part
  definition and deletion gate survive as rules 9–11.
- recovery "undo/revert/restore semantics exist on stateful surfaces" —
  folded into rule 6 (reachable undo path).
- "PROVE STALE → CLEAN" kept verbatim in spirit as rule 5.

### ownership-and-portability (portability-and-ownership + stable-truth-replaceable-machinery)

- Anti-pattern items (generated code edited by hand under a generator,
  canonical schema as vendor-product shape) — dropped; each is already a
  contrapositive of rules 1/3/4.
- Product-shaped names (world.json, world-export.json) — generalized away
  from the owner's product per the map's "move product out of universal
  contracts".

### project-context (project-context-and-participant-packs)

- "PLAY-NICE PARTICIPANT ACCEPTANCE v1" ritual text with contract_bundle
  hash and COMMITMENT header — dropped; the attestation ritual is retired
  in v2 (decision §5). The durable part (participants offer capabilities
  and the project keeps them) survives in rules 5–6.
- contractctl command mechanics (init-project, project validate) —
  dropped; tool docs.
- Session bootstrap procedure (rule 16) — shortened to rule 10.
- The observed-capability YAML (strengths/limitations/good_task_shapes…) —
  kept as prose (rule 7); sample blocks live in examples/.
- Broken "see rule 28" pointer — removed (see fixes above).

## Stale references found (for the orchestrator, not fixed here)

- `.contracts/adoption.yaml` and all four `examples/*.adoption.yaml` still
  list retired ids: assume-unknown, explicit-state, failure-and-degradation,
  recovery-and-reversibility, provenance-and-audit, truth-and-evidence,
  ask-for-help, stable-truth-replaceable-machinery, portability-and-ownership,
  play-nice-together, collaborative-good-faith, mutual-contribution,
  participation-and-contribution, project-context-and-participant-packs.
  `examples/project-context/.project/contracts/adoption.yaml` likewise.
- `README.md:13` links `contracts/core/FLOOR.md` — now
  `contracts/everyone/FLOOR.md`.
- Surviving contracts that name or link the deleted ones: interfaces/CLI.md
  and engineering/OBSERVABILITY.md ("six questions" — see fix above);
  interfaces/{API,ROOM,WEB_UI,HUMAN_AND_MACHINE_PARITY,MACHINE_READABLE_OUTPUT}.md;
  interoperability/{CAPABILITY_FIRST,EXTERNAL_MUTATIONS,IDEMPOTENCY,POLLING_WEBHOOKS_AND_CACHING,DISCOVERY_AND_NEGOTIATION}.md;
  agents/{HANDOFF,CONTRACT_ATTESTATION,MODEL_ROUTING,ORCHESTRATION,WORKER_CONTRACT}.md;
  engineering/{DEPENDENCY_DISCIPLINE,DETERMINISTIC_FIRST,TESTING_AND_VERIFICATION}.md;
  experience/{COPY_AND_LANGUAGE,WHAT_WHY_NEXT}.md;
  human/{HUMAN_RELIABILITY,INTERRUPTION_AND_RESUMPTION}.md;
  security/AUTHENTICATION.md.
- docs/principles/trusted-translation.md links `../contracts/core/…`
  (broken depth even before this pack; also references ASK_FOR_HELP,
  ASSUME_UNKNOWN). docs/QUICK_REFERENCE.md, examples/session-handoff.md,
  CHANGELOG.md and CONTRACT_INDEX.md cite old ids and paths.
- Tooling/schema gaps that make `contractctl validate` fail until
  integration (expected): `LAYER_DIRS` in tools/contractctl/contractctl.py
  and the `layer` enum in schema/contract.schema.json do not yet know
  "everyone"; contracts.lock.json and CONTRACT_INDEX.md drift;
  tests/test_library.py hard-codes the 68-contract count and several
  deleted file paths.

## Shape check for this pack's files

- v2 headings in order (In short ≤3 lines, Applies when, Rules ≤15,
  Examples 1–3, Why, You're done when, optional Machine notes); one receipt
  comment each; body ≤800 words; front matter keys exactly: contract_id,
  title, version, status, layer, applies, triggers, rationale; triggers are
  task words (none use always-applicable — only the floor does, per plan).

# Pack review: work (Agents and work)

Play-Nice v2 step 3, pack `work`. 15 source contracts → 9 new contracts
in `contracts/work/`, all version 2.0.0, all in the v2 shape modeled on
`contracts/core/FLOOR.md`. Old files deleted via `git rm`. Nothing in
CONTRACT_INDEX.md, contracts.lock.json, tests, tools, README, CHANGELOG,
or schema/ touched — that's the orchestrator's integration pass.

## Old → new

| old id (file) | new id | what happened |
|---|---|---|
| agent-behavior (agents/AGENT_BEHAVIOR.md) | agent-behavior | rewritten + merged with model-routing |
| model-routing (agents/MODEL_ROUTING.md) | agent-behavior | compressed to routing rules 8–13 |
| orchestration (agents/ORCHESTRATION.md) | orchestration | rewritten + merged with worker-contract; "foreman" renamed "coordinator" |
| worker-contract (agents/WORKER_CONTRACT.md) | orchestration | packet fields became orchestration rules 5–6, loop became rule 9 |
| review-and-integration (agents/REVIEW_AND_INTEGRATION.md) | bounded-work | merge rules became bounded-work 6–13 |
| bounded-work (engineering/BOUNDED_WORK.md) | bounded-work | rewritten; field list slimmed (full packet now lives in orchestration rule 6) |
| handoff (agents/HANDOFF.md) | handoff-and-continuity | merged with documentation-and-continuity |
| documentation-and-continuity (engineering/DOCUMENTATION_AND_CONTINUITY.md) | handoff-and-continuity | rules 6–12 |
| testing-and-verification (engineering/TESTING_AND_VERIFICATION.md) | testing-and-evidence | rewritten |
| deterministic-first (engineering/DETERMINISTIC_FIRST.md) | testing-and-evidence | merged as rules 1–3, 13 |
| search-before-inventing (engineering/SEARCH_BEFORE_INVENTING.md) | search-before-building | rewritten + merged with dependency-discipline |
| dependency-discipline (engineering/DEPENDENCY_DISCIPLINE.md) | search-before-building | rules 4–8, 11 |
| git-and-worktrees (engineering/GIT_AND_WORKTREES.md) | git-and-worktrees | rewritten |
| observability (engineering/OBSERVABILITY.md) | observability | rewritten |
| contract-attestation (agents/CONTRACT_ATTESTATION.md) | contract-proof | rewritten to the v2 proof model (plan §5); rules now sequential 1–10 (old file ran 1–17, then 21–27, then 18–20) |

## Rules dropped or changed in meaning

agent-behavior (kept from AGENT_BEHAVIOR 1–11; merged from MODEL_ROUTING):
- Old AB 1–3: rules 1, 2, 5–7 keep the substance; AB 3's "access ≠
  authority" dropped — floor rule 5 says it.
- Old AB 12–13 (authority language, truth-before-tone): collapsed into
  one rule 7 pointing at copy-and-language — they duplicated that
  contract near-verbatim (contracts map: agent-behavior row).
- Old AB MACHINE IMPLICATIONS ("consume contracts via the gate") — the
  gate is retired (contract-proof); dropped.
- MR 1 (task→model matching): kept as rule 8, stripped of its
  ~200-word restatement of participation-and-contribution rules.
- MR "small/local by sufficiency, largest/cheapest never justifies":
  kept as rule 9 (the no-model-hierarchy idea, one line; the full
  version belongs to the Everyone pack's contribution contract).
- MR 2 (routing is configuration): kept as rule 13 (coordinator's copy
  is orchestration rule 14). MR 3 (reject is normal): moved to
  orchestration rule 11. MR 4–7 kept as 10–12 + testing-and-evidence 12.

orchestration (ORCHESTRATION + WORKER_CONTRACT):
- Old rule 7: the ~240-word negotiation paragraph duplicating
  mutual-contribution: compressed to rule 7 pointing at contribution.
  Refusal-word lists (`ACCEPT/MODIFY/DECLINE/...`) dropped — tool
  vocabulary, lives in the question schema.
- Old rule 5's grab-bag of coordinator duties: kept as rule 4; model
  selection split into rule 14.
- Old "foreman" name: renamed "coordinator" (glossary: replace).
  "Worker contract" term: renamed "work packet" (glossary: packet
  only; avoids clash with normative contract).
- Old rule 8 (assign bounded tasks + ownership + serial integration):
  ownership/serial integration moved to bounded-work (its merge
  partner); packet fields kept here as rule 6.
- WORKER_CONTRACT 13–15 (may-not-do): covered by rules 2/9 here +
  bounded-work 4 + the floor; not restated.
- Old rationale's "Fable-derived framework": project-history term
  dropped (research friction item 7).

bounded-work (BOUNDED_WORK + REVIEW_AND_INTEGRATION):
- BW 1's 14-line field list: trimmed to the bounds (rule 1); the full
  delegation packet is orchestration rule 6 — no second list to rot.
- R&I 1–8: kept as rules 6–13. "Worker-green ≠ integration-green",
  stated in 5 contracts, now has one home (rule 8).
- BW 6's pointer to progress-and-closure ("done beats additionally
  awesome"): phrase kept as plain text (that contract merges into the
  People pack's attention-and-quiet; the phrase itself is self-owned
  now).

handoff-and-continuity (HANDOFF + DOCUMENTATION_AND_CONTINUITY):
- HANDOFF 1's ten-section shape: cut to the seven research-canonical
  headings (CURRENT/CHANGED/VERIFIED/CONTRACTS/UNKNOWN/DEFERRED/NEXT);
  ACCESSIBILITY/INTEROPERABILITY/SECURITY lines fold into VERIFIED —
  they were per-task checklists, not stable sections. Meaning edit for
  simplicity, owner-approved.
- HANDOFF 7 (debug bundle): kept as rule 5, without the "VEFR" origin
  story.
- HANDOFF machine note "nouns doctor-style verification command":
  broken reference (research §5 item 13 — exists nowhere); replaced
  with "the exact commands in VERIFIED are there so the receiver can
  re-run them" (rule 3).
- DOC 1 ("docs serve four audiences"): folded into Why; no separate
  rule.
- DOC 9 brevity pass: kept (rule 10) — this contract is its home; the
  Surfaces pack's copy-and-language should point here at integration
  (the map flagged them as duplicates).

testing-and-evidence (TESTING_AND_VERIFICATION + DETERMINISTIC_FIRST):
- All nine grades kept verbatim; they're the library's vocabulary.
- TV 4–8: kept. T&V 6 (worker-green) became a pointer to bounded-work.
- DF 1–2 (owners/jobs lists): compressed into rule 1 prose; the two
  lists were reference material, not obligations.
- DF 3–5 kept as rule 3; DF 6 folded into rule 13 (provenance) +
  bounded storage; DF 7 (smallest mechanism) moved to
  search-before-building rule 9 (duplication there anyway).
- "VEFR's rule" attribution dropped from Why (project-history term).

search-before-building (SEARCH_BEFORE_INVENTING + DEPENDENCY_DISCIPLINE):
- SBI 1–7: kept as rules 1–3, 9, 12 + rule 10 (retire complexity) +
  examples; the "seam map" machine note dropped (tooling advice, not a
  rule; "seam" jargon replaced with plain words).
- DD 1–8: kept as rules 4–8, 11. DD rationale's "Personal World P1
  removed 14 packages" product history dropped from Why (kept the
  lesson).
- DD 5's refs to Capability First: replaced with an internal pointer
  (testing-and-evidence rule 2).

git-and-worktrees: kept 1–8 as rules 1–9 (rule 2 split). "PROVE STALE →
CLEAN" kept as plain prose (glossary: keep, define). Anti-patterns kept
as one example. Machine-note tooling ideas (safe-commit tool) dropped —
tool docs.

observability: kept 1–8 as rules 1–9 (quiet-when-healthy split into 7).
Rule 3's "(see Failure and Degradation's six questions)" — the
six-vs-seven mismatch (research §5 item 4) — removed; the questions
themselves are now rule 2's own words. "Level 2/3" depth-ladder
jargon (People pack) replaced with "available on request".

contract-proof (contract-attestation → rewritten per plan §5):
- Removed from the contract (legacy lives in docs/PLAYNICE.md, one
  pointer rule kept as rule 10): the eight-step gate order (old rules
  1–2), bundle receipts (old 5), attestation artifact format (old 6–7),
  the full operational-commitment text (old 9–12), worker inheritance /
  propagation tree (old 13–16), re-commitment mechanics (old 18–20),
  the entire remote-freshness block (old 21–27: CURRENT/BEHIND/
  DIVERGED/UNREACHABLE/UNKNOWN vocabulary, `git ls-remote` determinism,
  byte-identical equivalence affordance). These are tool mechanics,
  and the plan retires the gate: proof is now one receipt line +
  `playnice verify` + badge + well-known file.
- Kept in v2 form: receipt uniqueness/version-binding (new rules 1–3),
  "receipt ≠ authorization" (new rule 4, echoing old rule 20), honest
  conflict blocking (new rule 9), no-fabrication of proof (new rule 8).
- Rule numbering fixed: sequential 1–10 (old file's 1–17 → 21–27 →
  18–20 scramble was research agent-item 2).

## Stale references found (not fixed here — other packs' files / orchestrator)

Fixed inside my own source files before merging:

- agents/HANDOFF.md:55 cited `nouns doctor` — a command that exists in
  no tool (map §5 item 13). Replaced: VERIFIED carries exact commands
  the receiver can re-run.
- engineering/OBSERVABILITY.md:24 cited "Failure and Degradation's six
  questions" — that rule lists seven (map §5 item 4). The number is
  gone; the questions are observability rule 2's own text now.
- agents/CONTRACT_ATTESTATION.md rule numbering ran 1–17 → 21–27 →
  18–20 (map §3 agent item 2). contract-proof numbers rules 1–10
  sequentially.
- agents/ORCHESTRATION.md:56 "Fable-derived framework" and
  engineering/DETERMINISTIC_FIRST.md / DEPENDENCY_DISCIPLINE / HANDOFF
  rationales naming "VEFR" / "Personal World P1": project-history
  terms dropped from normative text (map friction item 7).

Still citing removed/renamed ids in OTHER packs (repoint at
integration):

- "Worker Contract" → orchestration: core COLLABORATIVE_GOOD_FAITH:54,
  core MUTUAL_CONTRIBUTION:148, core PARTICIPATION_AND_CONTRIBUTION:75.
- "Model Routing" → agent-behavior routing rules (or contribution):
  core COLLABORATIVE_GOOD_FAITH:67, core MUTUAL_CONTRIBUTION:81, core
  PARTICIPATION_AND_CONTRIBUTION:40, :123 (also a fragile "rule 5–6"
  number), interoperability CAPABILITY_FIRST:39.
- "Review and Integration" → bounded-work: core
  COLLABORATIVE_GOOD_FAITH:101, :130, core MUTUAL_CONTRIBUTION:110.
- "Testing and Verification" → testing-and-evidence: core
  MUTUAL_CONTRIBUTION:110, :149, engineering MIGRATIONS:32.
- "Documentation and Continuity" → handoff-and-continuity: core
  COLLABORATIVE_GOOD_FAITH:68; "Handoff" → same:
  human INTERRUPTION_AND_RESUMPTION:27, core COLLABORATIVE_GOOD_FAITH:130,
  core PARTICIPATION_AND_CONTRIBUTION:78 (also stale "Agent Behavior
  rule 9" — number changed; now rule 6).
- Not broken, path-only moves: "Agent Behavior"
  (security AUTHORIZATION:29, LEAST_PRIVILEGE:28), "Orchestration"
  (core ASK_FOR_HELP:60, COLLABORATIVE_GOOD_FAITH:101), "Bounded Work"
  (core ASK_FOR_HELP:127, PARTICIPATION_AND_CONTRIBUTION:75),
  "Observability" (interfaces API:47, core PLAY_NICE_TOGETHER:72) —
  ids unchanged; CONTRACT_INDEX rows just need new paths.
- experience/VISUAL_FIDELITY_AND_COMPOSITION.md:131 "Visual contract
  attestation" is a local heading about gate-sounding design checks,
  not a cross-reference — but the word "attestation" now means
  something else; worth a rename at integration.

Non-contract files naming removed ids that the orchestrator owns:
`.contracts/adoption.yaml`, `profiles/baseline.yaml`,
`profiles/examples/rylee.yaml`, `examples/*.adoption.yaml`,
`examples/session-handoff.md`, `schema/global-playnice.schema.json`,
`CONTRACT_INDEX.md`, `docs/QUICK_REFERENCE.md`, and tests
(test_library.py pins contract count 68, orchestration 1.4.0 with rule
numbers 1–13, and model-routing text; test_freshness/test_playnice
exercise the retired gate mechanics).

Plan-vs-brief note: the contracts map §2 routed model-routing into core
`contribution` and merged bounded+worker+review into one
`bounded-and-delegated-work`; this pack followed the owner-approved
brief's split instead (model-routing → agent-behavior;
review-and-integration → bounded-work; worker-contract →
orchestration). Alias rows in CONTRACT_INDEX should reflect the
brief's mapping.

## Receipt words (new, verified unique)

kestrel-sparrow-thistle, quarry-loom-cypress, garnet-spindle-marigold,
pasture-walnut-copper, hearth-anvil-tamarack, cobble-zephyr-pine,
umber-reed-slate, kettle-vane-daisy, aspen-nimbus-reef.

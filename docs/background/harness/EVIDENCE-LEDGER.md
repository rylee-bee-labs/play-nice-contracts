# Play-Nice Harness Evidence Ledger

**Status: EXPERIMENTAL**

This ledger turns observations into testable harness hypotheses. Do not promote attractive wording without evidence.

## Confidence vocabulary

- **SEED** — plausible hypothesis; evidence collection has begun.
- **SUPPORTED** — repeated evidence, but transfer/counterexample work remains.
- **STRONG** — repeated cross-domain/cross-participant evidence with counterexample testing.
- **REJECTED** — evidence does not support a universal law; retain the lesson and reason.
- **ADAPTER** — useful behavior, but evidence suggests it is role/model/domain specific.

## Candidate ledger — after Claude/Fable-era mining pass 1

| ID | Candidate | Evidence after pass 1 | Counterexample question | Transfer target | Confidence |
|---|---|---|---|---|---|
| H01 | Observe before claiming | Stale local homelab checkout contradicted fresh upstream/live VM; stale project pointers and remote configuration produced wrong-looking state; browser runtime contradicted green token/tests | When is cached/pinned state intentionally sufficient? | Claude/Fable-era engineering → Hermod → VEFR | **SUPPORTED** |
| H02 | Know who owns truth | Backend/server preference truth corrected optimistic UI; local Git vs GitHub enrichment separated; one canonical current-state pointer replaced competing narratives; participant packs explicitly remain enrichment | Can explicit delegated authority safely move truth temporarily? | Engineering + world simulation | **SUPPORTED** |
| H03 | Separate epistemic kinds | Project state vs observation freshness explicitly separated; configured vs status separated; proposal vs approval vs action separated; participant observations vs canonical truth separated | What is the minimum useful distinction set? | Engineering ↔ characters/worlds | **SUPPORTED** |
| H04 | UNKNOWN is valid | Missing timestamps changed from fabricated “just now” to unknown; unknown frame approval preserved; GitHub count failures return unknown rather than zero | When should safe discovery replace UNKNOWN immediately? | All roles | **SUPPORTED** |
| H05 | Ask for help at competence/authority boundary | Epoch contains repeated owner-decision boundaries and deliberate deferrals; stronger direct evidence currently comes from Play-Nice/Granite rather than Claude/Fable | Can excessive escalation destroy usefulness? Where is the threshold? | Small + frontier models | SEED |
| H06 | Constrain authority, not creativity | Bounded foundation spec enabled substantial implementation while preserving owner gates; product rename pass classified rather than blindly replacing; creative UI work survived within explicit design/authority boundaries | Which constraints improve useful freedom vs merely reduce options? | Coding + design + character generation | SEED |
| H07 | Define success externally | Green token/tests missed invisible focus and OS-motion bugs; published image initially exercised legacy UI instead of accepted React UI; human browser/UAT gates exposed both | Which low-risk tasks can be safely self-graded? | Engineering + structured generation | **SUPPORTED** |
| H08 | Verify consequential results deterministically | Browser probes, getComputedStyle, exact SHA/CI verification, ETag round trips, restart tests, Git graph checks and live VM checks repeatedly corrected plausible assumptions | What counts as consequential, and when is deterministic verification unavailable? | All operational roles | **SUPPORTED** |
| H09 | Re-observe before consequential action | Concurrent push caught before push; local checkout 1007 commits behind; live observations changed during task; re-fetch after preference writes restores server truth | How fresh is fresh enough by task class? | Orchestration + operations | **SUPPORTED** |
| H10 | Preserve evidence | Figma drift postmortem, CURRENT/DECISIONS/handoffs, historical docs retained after supersession, known defects carried into next-agent handoff | What is the minimum evidence that avoids burdensome logging? | Experiments + operations | **SUPPORTED** |

## Mining scope and attribution note

“Claude/Fable epoch” is used here as the project era/dataset, not as a claim that one model authored every artifact. The durable history includes bcode/Claude work, Fable-class planning/review, GLM orchestration, owner UAT/corrections, deterministic tooling, and later integration passes. For harness research this is useful: it lets us study the whole **instruction → implementation → verification → correction → durable outcome** chain without pretending every observation isolates one model variable.

## Pass-1 observations

### OBS-2026-001 — Green structural checks did not prove lived correctness

- Source / participant: Claude-era T14 UI convergence + owner/browser verification.
- Task / domain: accessibility and frontend composition.
- What happened: token generation/checks and existing tests were green while the shipped focus-ring token was invalid CSS; browsers silently dropped the outline. The React preference path also allowed a stored `subtle` motion preference to override the OS reduced-motion signal.
- Result: live browser inspection found both defects; tests were then rewritten to test the real semantic/runtime property instead of the representation that happened to exist.
- Candidate(s): H07, H08.
- Supports: external success criteria; deterministic verification at the layer where the claim matters.
- Counterfactual: a harness rule saying “verify the user-visible/runtime consequence, not only the intermediate artifact” would have forced a browser check before completion.
- Transfer note: likely universal in form, though the verification mechanism is domain-specific.
- Evidence: `personal-world@dc5c2cb61d8774bc4a6f3a18448a7c90a09660c0`.

### OBS-2026-002 — Token fidelity did not imply composition fidelity

- Source / participant: Claude-era Figma handoff postmortem.
- Task / domain: design-to-code translation.
- What happened: design tokens survived byte-for-byte, but screen composition drifted toward generic card-heavy patterns. Written prose existed, yet nothing mechanically or procedurally required comparison against the visual reference.
- Result: direct browser-vs-reference comparison exposed the drift; the postmortem recommends inline references, wrong-vs-right examples, and visual gates.
- Candidate(s): H07, H08, H10; complicates H06.
- Supports: success must be measured against the actual target dimension; preserved postmortems are reusable harness evidence.
- Complicates: “constrain authority, not creativity” needs care — unconstrained implementation defaults can overpower intended composition even when the model is acting reasonably.
- Counterfactual: require the participant to name the authoritative visual reference and record differences before implementation/review.
- Evidence: `personal-world@1ecd1b06f217597ffd6f6d174ffff41e79900476`.

### OBS-2026-003 — Multiple plausible current-state narratives created ambiguity

- Source / participant: trunk-unification / identity pass.
- Task / domain: project orientation and continuity.
- What happened: `.project/CURRENT.md`, `.agent/STATE.md`, and `STATUS.md` had become competing/stale narratives. Historical material remained useful, but it was unsafe as current truth.
- Result: `.project/CURRENT.md` became the single current-state pointer; older records were retained and explicitly marked historical rather than deleted or silently treated as current.
- Candidate(s): H01, H02, H03, H10.
- Supports: orient to a named authority; preserve history without letting it impersonate current state.
- Counterexample: historical/pinned state can be authoritative for “what was adopted then,” so “newest wins” is explicitly NOT the rule.
- Evidence: `personal-world@69394f0e9719b64e3685a1d6512475a93ee88ddb`.

### OBS-2026-004 — Fresh upstream/live evidence overturned local evidence

- Source / participant: 2026-09-12 orchestration freshness evidence.
- Task / domain: cross-repository integration.
- What happened: a local homelab checkout was 1007 commits behind and implied the Lab CLI did not exist. Fresh GitHub state and live VM observation showed that it did. A concurrent push also landed during active work and was caught before pushing.
- Result: work re-anchored to fresh evidence; unrelated local repo state was not silently fast-forwarded.
- Candidate(s): H01, H02, H09.
- Supports: observation has scope and age; re-observe before consequential action; discovering fresher truth does not grant mutation authority over the stale witness.
- Counterexample: the Play-Nice adoption pin intentionally remained behind library HEAD; freshness of a repo and correctness of a pinned adoption are different questions.
- Evidence: `personal-world@47c316f8605cdec5f267fafccbe8571ca4aa8fc4`.

### OBS-2026-005 — State and freshness are orthogonal

- Source / participant: Project-state trust pass.
- Task / domain: sensor/UI/assistant truth translation.
- What happened: a prior implementation could fabricate “Observed just now” when no timestamp existed. The correction made `publish_state` and observation age separate dimensions: stale diverged remains a stale observation of diverged; missing/invalid age remains unknown.
- Result: UI and assistant context carry dated provenance without rewriting observed state.
- Candidate(s): H03, H04, H09.
- Supports: epistemic distinctions should survive translation layers instead of collapsing into one status word.
- Counterfactual: an explicit harness vocabulary for observation/value/freshness/unknown would make this distinction harder to lose.
- Evidence: `personal-world@42389d0fa37c7f0af362ca866923ccffd34a0324`.

### OBS-2026-006 — Optimistic presentation became a small lie

- Source / participant: owner’s first real Settings use and subsequent fix.
- Task / domain: preference mutation/UI state.
- What happened: the UI showed attempted preference values without re-reading what the server actually stored; failed companion writes could leave an unsaved choice visible. A dead theme-pack selector also exposed options the server vocabulary could not act on.
- Result: every write attempt now re-fetches server truth; failed optimistic state is reverted; dead controls were removed rather than cosmetically retained.
- Candidate(s): H02, H03, H09.
- Supports: presentation should translate authoritative state, not become a competing state owner.
- Counterexample: optimistic UI can still be useful if explicitly provisional and guaranteed to reconcile.
- Evidence: `personal-world@ec29e8571b32d8bb3c13478ff736a65236f17f7e`.

### OBS-2026-007 — The accepted UI was not the UI being exercised

- Source / participant: T15 cutover / owner acceptance walk.
- Task / domain: deployment and product verification.
- What happened: the image still defaulted to the legacy server-rendered UI, so an acceptance walk could exercise a retired surface rather than the React build whose tests and design work were being discussed.
- Result: legacy UI and the mode switch were deleted; missing React dist now produces an honest 503 rather than silently falling back.
- Candidate(s): H02, H07, H08.
- Supports: verify the deployed path, not merely the artifact believed to be deployed; fallback machinery can conceal failure and invalidate acceptance evidence.
- Counterfactual: completion proof should name the exact executable path/build being exercised.
- Evidence: `personal-world@20697feee85cb0c46bade2317131840485f1ee25`.

### OBS-2026-008 — UAT created requirements tests could not invent

- Source / participant: owner UAT round 1.
- Task / domain: browser trust and test-environment discipline.
- What happened: owner use established two product truths not captured by generic correctness tests: stale browser assets were a trust failure, and persistent state during pre-beta UAT made it hard to know whether observed behavior came from the current walk.
- Result: immutable caching was replaced with explicit revalidation; every ordinary UAT walk starts from a proven clean slate until the owner promotes the environment.
- Candidate(s): H07, H08, H10.
- Supports: human acceptance can define success dimensions that automated checks cannot infer; once learned, those dimensions should become durable/testable constraints.
- Evidence: `personal-world@bbd1b5f0527b9c4facaf129595e3315c0010913e`, `personal-world@13fdb6752c35e2917793b7c1099ba89fd510a1f0`.

### OBS-2026-009 — Restart crossed a truth boundary tests had not exercised

- Source / participant: P2 auth groundwork after UAT.
- Task / domain: authentication persistence.
- What happened: setup wrote a human-created token into live process state and a file, but boot ignored the file. Restart restored the compose token and could lock the owner out.
- Result: boot-time reconciliation established which source owns the human-facing credential, and restart tests now verify the lifecycle boundary.
- Candidate(s): H02, H07, H08.
- Supports: authority/truth ownership must be explicit across lifecycle transitions; tests should cross the boundary where state can change ownership or disappear.
- Evidence: `personal-world@90fcabb27add0cfd83d3ca0ff2f98a2eab9bd824`.

### OBS-2026-010 — Proposal, approval, action, and result must not collapse

- Source / participant: first propose→approve→act workflow + assistant journal correction workflow.
- Task / domain: agent participation and mutation authority.
- What happened: the product deliberately models suggestion as non-action. Repository refresh explains what/why/tool/risk/expected result and remains “not happened” until explicit approval. Assistant journal corrections are drafts; malformed/stale proposals degrade to text and no mutation occurs before owner approval.
- Result: useful agent contribution is preserved without granting implicit action authority.
- Candidate(s): H02, H03, H06.
- Supports: constrain authority, not contribution; preserve explicit phase/state distinctions.
- Counterexample: low-risk autonomous actions may be intentionally delegated, so the universal rule should be “authority must be explicit,” not “humans must approve every action.”
- Evidence: `personal-world@f0f64e6c389f0ed22219316bc30d839db2e9cfce`, `personal-world@04c9c76c928b91dcadb1294b8aded6dc941d0c57`.

### OBS-2026-011 — Bounded specs enabled cheaper/replaceable workers

- Source / participant: Fable-class P1 foundation planning followed by implementation tasks.
- Task / domain: model routing and implementation harnessing.
- What happened: the foundation spec named ownership boundaries, settled decisions, explicit gates, task sizes, acceptance criteria, exclusions, and where human/browser review was required. It explicitly expected cheaper implementation models to work from the bounded spec.
- Result: implementation could proceed in smaller tasks without reopening product decisions on every pass.
- Candidate(s): H06, H07, H10.
- Supports: a harness can increase freedom inside a task by making authority, invariants, and finish conditions explicit outside the worker.
- Complicates: large specs can themselves become stale; H01/H09 still apply.
- Evidence: `personal-world@17adc0d86da47181968bc0a4df066d9989a44579`.

### OBS-2026-012 — Durable handoff preserved defects, not just accomplishments

- Source / participant: UAT round-1 orchestration handoff.
- Task / domain: interruption/resumption.
- What happened: the handoff recorded exact landed commits, deployment state, verification counts, owner decisions, known diagnosed-but-unfixed defects, and ordered next actions. The setup-token restart defect was explicitly carried forward rather than hidden by the passed UAT round.
- Result: the next participant had a resumable state that separated “passed this round” from “everything is finished.”
- Candidate(s): H03, H07, H10.
- Supports: evidence preservation should include unresolved defects and scope of the claim, not only success summaries.
- Evidence: `personal-world@63b0825d357d7dab23f01ac59ba85b8e6fa9cc3f`.

## Pass-1 synthesis

The strongest pattern is not “write a better prompt.” It is **keep the participant correctly oriented to truth and to the meaning of its evidence**.

The epoch repeatedly failed when a valid fact was silently promoted into a stronger claim:

- generated tokens match → therefore the UI is accessible;
- tests pass → therefore the deployed experience is correct;
- local checkout exists → therefore it is current;
- UI shows a value → therefore the server stored it;
- an observation has a state → therefore it is current;
- a proposal is useful → therefore it is authorized;
- UAT passed this round → therefore no known defects remain.

The corresponding successful behavior is to preserve the **type, source, scope, age, authority, and verification level** of information as it moves through the system.

This suggests a possible future consolidation: H01/H02/H03/H04/H09 may be different operational faces of one deeper principle — tentatively, **preserve the semantics of evidence**. Do not merge them yet. The Granite/VEFR corpus is an excellent counter-test: if world truth, character belief, observation age, uncertainty, and authority show the same pattern, consolidation becomes much more defensible.

H07/H08 also appear tightly related but should remain separate for now: one says **who/what defines success**, the other says **how claims are proven**.

H06 remains intentionally SEED. The epoch supports bounded autonomy, but we need counterexamples from creative/world tasks before calling “constrain authority, not creativity” universal.

H05 remains SEED from this mining pass. The epoch shows deliberate deferral at owner boundaries, but Granite/Hermod gives cleaner direct evidence that asking for help can itself be successful participant behavior.

## Observation record template

```markdown
### OBS-YYYY-NNN — short name

- Source / participant:
- Task / domain:
- Harness / model / version:
- Canonical context or revision:
- What happened:
- Expected behavior:
- Result:
- Candidate(s) affected: Hxx
- Supports / contradicts / complicates:
- Deterministic evidence:
- Human/UAT evidence:
- Counterfactual: what harness change might have changed the outcome?
- Model-specific or likely transferable?
- Notes / links:
```

## Promotion record template

```markdown
### Hxx promotion review

- Proposed wording:
- Failure/capability addressed:
- Supporting observations:
- Contradicting observations:
- Models/participants tested:
- Domains tested:
- Counterexample tests:
- Why kernel instead of adapter:
- Interaction with canonical contracts:
- Testable behavioral consequence:
- Decision: PROMOTE / KEEP EXPERIMENTAL / ADAPTER / REJECT
- Decision evidence / owner review:
```

## Research discipline

A failed hypothesis is useful. Preserve rejected candidates and why they failed so later contributors do not rediscover the same attractive but unsupported rule.

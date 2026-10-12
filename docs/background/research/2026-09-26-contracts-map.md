# Contracts Map — a plain-words review of the Play-Nice contract library

Reviewed 2026-09-26 on branch `offload/pn-contracts-map-20260926-121608-5465` (library v0.10.0, 67 contracts).
This is a read-only review. It changes no contract, no document, no tool. The owner's stated goal:
make the library simpler and friendlier for humans and agents, with permission to change meaning,
merge, rename, add, and remove.

What was read: README.md, AGENTS.md, CONTRACT_INDEX.md, docs/QUICK_REFERENCE.md, docs/principles/*
(trusted-translation.md, world-with-manners.md), all 68 files under contracts/ (67 contracts +
LICENSE.md), schema/ (12 JSON schemas), profiles/ (2 YAML + 4 model profiles), tools/contractctl,
tools/check.sh, tests/, examples/session-handoff.md, docs/PLAYNICE.md, CHANGELOG.md, harness/.

Word counts in the table are words in the Markdown body only (front matter and the receipt comment
excluded). Library total at the time of this review: **47,456 body words, 671 numbered rules**.

Verdict words used below: **keep** (leave mostly alone), **keep (slim)** (shorten, cut duplicated
rules), **merge into X** (becomes part of another contract, file removed), **rename**,
**remove** (the text leaves the contract library; the idea moves to tool docs or a project spec).
Nothing in the library is without value — the problem is repetition and shape, not content.

## 1. Every contract

| id | group | words | one-line plain summary | who it's for | overlaps with | verdict | why |
|---|---|---|---|---|---|---|---|
| play-nice-together | core | 1011 | What Play-Nice is: the ground rules for humans, agents, and services working together, and how a contract binds you (only after you load and accept it). | everyone | ask-for-help, participation-and-contribution, human-and-machine-parity | keep (slim) | It is the one front door; rules 7–13 restate other contracts and should cross-reference instead. |
| truth-and-evidence | core | 507 | Say only what you can back up; `UNKNOWN` is a valid answer; evidence beats reports; never make things up. | everyone who states a fact | assume-unknown, observability, room | keep | Foundation every other contract cites; already tight. |
| assume-unknown | core | 1063 | Sort claims into seen / reasoned / believed / unknown; before a risky action, name your biggest unproven belief and run the cheapest test that could prove it wrong. | humans and agents before consequential actions | truth-and-evidence | merge into truth-and-evidence | Same subject split into two files; the disconfirmation procedure is just rules 5–8 of the truth contract. |
| explicit-state | core | 452 | Report state using one shared 15-word status list; never guess a state from silence. | anything that shows a status | failure-and-degradation, room | merge into `state-and-status` (with failure-and-degradation) | The 15-word list is typed out in prose in two files (explicit-state.md:22, failure-and-degradation.md:22) while the schema is the real source. |
| stable-truth-replaceable-machinery | core | 472 | Facts must outlive the tools that store them; anything derived from them must be rebuildable. | owners, architects | play-nice-together | keep | One clear idea with no other home. |
| provenance-and-audit | core | 448 | Record who did what, when, and why; label generated content; automation must be attributable. | everyone; auditors | observability, external-mutations | keep | Short, unique, heavily cited by others. |
| recovery-and-reversibility | core | 434 | Risky changes need a preview and an undo; prove state is stale before cleaning it. | anyone making changes | migrations, git-and-worktrees | keep + merge migrations | Preview/undo is universal; migrations restates it in database clothing. |
| portability-and-ownership | core | 455 | The owner can export everything; exports replace secrets with placeholders; data stays the owner's. | owners; anything storing user data | secrets, stable-truth | keep | Unique and load-bearing against lock-in. |
| ask-for-help | core | 1808 | When to act, when to look it up, when to ask; a question is stored resumable state with options and a recommendation, not a chat line. | agents and coordinators | mutual-contribution, discovery-and-negotiation, authorization | keep (slim) | The ladder and the stop states matter; the JSON artifacts and schema walkthrough should move to tool docs. |
| collaborative-good-faith | core | 2612 | Cooperate in good faith: criticism must point at a repair, no blame language, trust earned by evidence not position. | humans and agent conduct | agent-behavior, copy-and-language, orchestration | keep (slim) | Longest contract in the library; roughly half is etiquette that belongs in examples, and rule 23 duplicates orchestration rule 7. |
| mutual-contribution | core | 2481 | How participants offer and take work: NEED → OFFER → ACCEPT/MODIFY/DECLINE; being able to do something is not being allowed to. | participants negotiating work | participation-and-contribution, ask-for-help, authorization | merge into `contribution` | Deliberately overlaps two other files; a three-way merge cuts ~4,500 words to ~1,500. |
| participation-and-contribution | core | 2013 | Any participant may contribute at the level its role and evidence allow; no ranking by model size, price, or origin. | owners routing work | mutual-contribution, model-routing | merge into `contribution` | "No model castes" is three rules, restated again in QUICK_REFERENCE.md:111–115. |
| project-context-and-participant-packs | core | 1494 | The standard `.project/` file layout and the contents of a participant pack (identity, capabilities, limits, evidence). | adopting projects; pack authors | documentation-and-continuity | keep (slim) | Real structure spec, but mixes rules with reference material; internal pointer at line 53 ("see rule 28") is broken — it has 21 rules. |
| human-reliability | human | 737 | Design for tired, interrupted, forgettable humans: reminders, resumable state, and "no action needed" counts as success. | designers; agents talking to humans | interruption-and-resumption, attention-and-focus | keep + absorb interruption-and-resumption | Its truth-report format and the interruption checklist are two halves of one idea. |
| accessibility-floor | human | 618 | The minimum anyone can use: keyboard, visible focus, 44px targets, no color-only meaning, 200% zoom, honor reduced-motion. | UI builders | low-vision-and-reflow, migraine-and-sensory-safety, motion-and-feedback | keep + absorb low-vision-and-reflow | The zoom/reflow rule exists almost verbatim in both files (accessibility-floor.md:29 vs low-vision-and-reflow.md). |
| migraine-and-sensory-safety | human | 479 | Default to still; no strobing or flashing; loud sensory effects are opt-in only. | UI/motion builders | motion-and-feedback, accessibility-floor | merge into `motion-and-sensory-safety` | Its reduced-motion rule is stated for the third time (migraine.md:27, accessibility-floor.md:30, motion-and-feedback.md:42). |
| low-vision-and-reflow | human | 525 | Layouts survive 200% zoom, text scaling, and forced-colors; reflow is a release gate. | UI builders | accessibility-floor | merge into accessibility-floor | Adds almost nothing the floor doesn't already require. |
| attention-and-focus | human | 554 | Control when complexity enters attention; after an interruption the state must be findable without archaeology. | UI builders; agents | interruption-and-resumption, complexity-on-demand, quiet-when-healthy | merge into `attention-and-quiet` | Rule 7 (attention-and-focus.md:28) rewrites interruption-and-resumption.md:22's checklist almost word for word. |
| interruption-and-resumption | human | 434 | After a pause or restart, current state, completed work, open questions, and next action must be reconstructable. | everyone | human-reliability, handoff, attention-and-focus | merge into human-reliability | One contract per idea; this is human-reliability's second paragraph given its own file. |
| what-why-next | experience | 412 | Every surface answers three things: what happened, why, and what's next. | UI writers | attention-and-focus, room | merge into `attention-and-quiet` | Seven rules that the room descriptor and attention contract already require. |
| progressive-disclosure | experience | 477 | Show the summary first; detail is one action away. | UI builders | complexity-on-demand, guide-me | merge into `depth-on-demand` | complexity-on-demand.md:18 already calls this contract "the presentation mechanism" for it. |
| quiet-when-healthy | experience | 426 | A healthy system says nothing; silence is the default output. | systems; agents | attention-and-focus, what-why-next | merge into `attention-and-quiet` | The same attention idea from the output side. |
| progress-and-closure | experience | 465 | Work in progress shows progress; finished work looks finished and stops. | builders | bounded-work, cli | merge into `attention-and-quiet` | "Done beats additionally awesome" restates bounded-work rule 6. |
| guide-me | experience | 502 | First use or confusion gets a path, not a wall of options. | onboarding builders | complexity-on-demand, copy-and-language | merge into `depth-on-demand` | The depth ladder minus its rungs. |
| themes-and-personalization | experience | 486 | Themes can't break the accessibility floor; personalization layers stack in a fixed order. | themers; UI owners | accessibility-floor | keep (slim) + fix its layer stack | Rule 1 (themes-and-personalization.md:22–33) presents a different five-layer authority stack from README.md:20–28. One of the two is wrong. |
| motion-and-feedback | experience | 420 | Motion must mean something, stay calm by default, and be opt-out. | UI builders | migraine-and-sensory-safety, accessibility-floor | merge with migraine | Two files, one subject. |
| design-source-and-fidelity | experience | 544 | The approved design source and semantic tokens are truth; implementations must match or say so. | design + UI builders | visual-fidelity-and-composition | merge into `design-truth` | Two fidelity contracts split one rule set. |
| visual-fidelity-and-composition | experience | 1453 | Fidelity levels D0–D4, preserve the approved composition, listed anti-patterns, a gate for AI-generated design work. | UI/design builders; AI design operators | design-source, accessibility-floor | merge into `design-truth` | 25 rules restate design-source plus a long anti-pattern list; only the D-levels carry new information. |
| copy-and-language | experience | 775 | Plain human wording in UI text; truth before tone. | writers | agent-behavior, documentation-and-continuity | keep | Unique and useful — but rules 10–11 (copy-and-language.md:31–32) duplicate documentation-and-continuity.md:30 and agent-behavior.md:34 near-verbatim. |
| api | interfaces | 520 | Stable, versioned, honest machine interfaces: real errors, dry runs, idempotent writes. | API designers | cli, web-ui, idempotency, versioning-and-compatibility | merge into `surfaces` | Three interface files share most of their rules. |
| cli | interfaces | 489 | Quiet success, loud failure; human text plus machine flags; meaningful exit codes. | tool builders | api, failure-and-degradation | merge into `surfaces` | Same rules again; also cites the "full six-question error" (cli.md:25) that doesn't number six anywhere. |
| web-ui | interfaces | 573 | Web surfaces show every state (loading, empty, error), keyboard first, honest defaults. | web builders | api, accessibility-floor | merge into `surfaces` | Most rules are pointers to the accessibility and state contracts. |
| human-and-machine-parity | interfaces | 558 | Humans and machines get the same capabilities, each in the form that suits them; neither view is second-class. | interface designers | machine-readable-output, api | merge into `one-truth-two-views` | Rule 6 repeats play-nice-together rule 2. |
| machine-readable-output | interfaces | 461 | Structured output (`--json` and friends) must be stable, documented, and versioned; same facts as the human view. | tool builders | human-and-machine-parity, cli | merge into `one-truth-two-views` | It is the other half of parity. |
| room | interfaces | 1746 | The ROOM surface: five fixed endpoints (descriptor, cards, needs-you, actions, idempotent POST) so one front door can host many small independent backends. | room implementers; card producers | explicit-state, authorization, what-why-next | keep, rename to `room-spec`; fix status words | Newest and machine-checked, but its status enum (`unhealthy`, room.md:52) is not in the shared vocabulary, and rule 15 (room.md:171) is a product-specific "Worlds MUST…" inside a universal contract. |
| capability-first | interoperability | 647 | Find out what a system can actually do (capability endpoints), don't guess from its vendor name. | integrators | provider-neutrality, discovery-and-negotiation | merge into `capabilities-not-vendors` | Its rule 9 restates provider-neutrality rule 4. |
| provider-neutrality | interoperability | 450 | No vendor lock-in: adapters at the edges, provider swaps must not rewrite the core. | architects | capability-first, portability-and-ownership | merge into `capabilities-not-vendors` | Same rules twice; its optional-default rule also lands in least-privilege rule 3. |
| friendly-api-client | interoperability | 538 | Behave politely toward other systems: respect limits, back off, discover before assuming, mutate safely. | anyone calling an API | external-mutations, polling-webhooks-and-caching, idempotency | merge into `integrating-with-other-systems` | Its mutation pipeline (friendly-api-client.md:39) is external-mutations.md:24 word for word. |
| external-mutations | interoperability | 499 | Changing other systems needs a preview, a verification after, recorded provenance, and a revert path. | integrators; agents | friendly-api-client, recovery-and-reversibility, authorization | merge into `integrating-with-other-systems` | Rule 8 ≈ least-privilege rule 7 ≈ authorization rule 8. |
| polling-webhooks-and-caching | interoperability | 429 | Learn about changes without spamming: webhooks over polling, cache with expiry, avoid stampedes. | integrators | friendly-api-client, room | merge into `integrating-with-other-systems` | One topic already split four ways; belongs with the client contract. |
| idempotency | interoperability | 447 | Retried writes must not duplicate: idempotency keys, safe retries everywhere. | API designers and clients | external-mutations, api | merge into `integrating-with-other-systems` | Seven rules, all referenced from the other three files anyway. |
| discovery-and-negotiation | interoperability | 478 | A system announces what it is and what it can do, and honest negotiation settles shared terms. | integrators | capability-first, versioning-and-compatibility, ask-for-help | merge into `negotiating` (with versioning) | Rule 8 restates ask-for-help rule 17; line 28 spells "Negotation" inside a normative rule. |
| versioning-and-compatibility | interoperability | 455 | Explicit versions, honest deprecation windows, never break silently. | interface owners | discovery-and-negotiation, api, room | merge into `negotiating` | Half is restated inside the room spec. |
| failure-and-degradation | interoperability | 528 | Name failures precisely, say what still works, contain optional failures; partial beats a false all-clear. | systems; agents | explicit-state, truth-and-evidence, observability | merge into `state-and-status` | It is the reporting half of explicit-state; its rule 4 (failure-and-degradation.md:25–33) lists seven questions while its own acceptance check says "six questions" (line 76). |
| authorization | security | 451 | Capability is not authority; authority must be explicit; ambiguous authority means no; risky actions step up for human sign-off. | everyone acting | least-privilege, authentication, room (rule 9) | merge into `identity-and-access` (authn+authz+least-privilege) | Three files each restate "fail closed" and each other's boundaries. |
| authentication | security | 471 | Prove who you are with current evidence; no shared accounts; re-check over time. | system builders | authorization, secrets | merge into `identity-and-access` | Its rule 8 repeats the secrets contract. |
| least-privilege | security | 463 | Grant the smallest rights the task needs; expire and audit grants. | owners; integrators | authorization, external-mutations | merge into `identity-and-access` | Rule 7 duplicates authorization rule 8. |
| secrets | security | 555 | Secrets live in secret stores, never in code, exports, or logs; exports carry placeholders. | anyone shipping code | data-classification, portability-and-ownership | merge into `data-and-secrets` | Rule 2 and data-classification's handling rules are the same rule. |
| data-classification | security | 450 | Label data by sensitivity, handle at the label, never downgrade silently. | data owners | secrets, authorization | merge into `data-and-secrets` | Rule 2 ≈ authorization rule 6. |
| public-private-boundaries | security | 512 | Keep private material off public surfaces; canary markers prove whether it leaked. | publishers; agents | secrets, provenance-and-audit, room | keep | Its canary / `pn-safety` mechanism has no other home and works. |
| deterministic-first | engineering | 455 | Deterministic logic before heuristics before model guesses; model output gets verified. | builders; agents | testing-and-verification, truth-and-evidence | keep | Short, unique, in the always-load list. |
| bounded-work | engineering | 480 | Every task has one goal, limits, and named stop conditions; stopping at a stop condition is success. | coordinators; agents | worker-contract, review-and-integration, progress-and-closure | merge into `bounded-and-delegated-work` | Its field list (bounded-work.md:23–38) is the worker packet minus three fields. |
| worker-contract | agents | 546 | The format of a work packet for a delegate: goal, owned paths, budget, acceptance checks, inherited limits. | orchestrators | bounded-work, orchestration, review-and-integration | merge into `bounded-and-delegated-work` | "Worker-green is not integration-green" is stated in five contracts (worker.md:62, bounded-work.md:44, orchestration.md:35, review.md:23, testing.md:38). |
| review-and-integration | agents | 516 | Parallel work integrates serially; the combined result is re-tested at the integration commit. | reviewers; orchestrators | orchestration, testing-and-verification | merge into `bounded-and-delegated-work` | Restates orchestration plus the same worker-green line. |
| testing-and-verification | engineering | 482 | Nine evidence grades, from SOURCE INSPECTED to HUMAN ACCEPTED; never silently upgrade a grade; state the exact command. | builders; agents | observability, documentation-and-continuity | keep | Referenced by the quick reference and the handoff format; the grades are the library's most useful machine vocabulary. |
| dependency-discipline | engineering | 452 | Add dependencies only for real gaps; vet, pin, and license-note each one. | maintainers | search-before-inventing, portability-and-ownership | merge into search-before-inventing | Same "search, justify, keep small" idea from the supply side. |
| search-before-inventing | engineering | 463 | Before a new abstraction or tool, look for an existing pattern, contract, or proven library. | builders; agents | dependency-discipline, stable-truth | keep (absorbs dependency-discipline) | In the always-load list; a natural home for the dependency rules. |
| documentation-and-continuity | engineering | 669 | Docs live with the code, update in the same change, get a brevity pass, and say what is stale. | everyone who writes | copy-and-language, handoff, git-and-worktrees | keep (absorbs handoff) | Its brevity pass (documentation-and-continuity.md:30) duplicates copy-and-language.md:31; the handoff format is just its final section. |
| handoff | agents | 547 | End a session with a resumable report: CURRENT, CHANGED, VERIFIED, CONTRACTS, UNKNOWN, DEFERRED, NEXT. | agents; humans resuming | human-reliability, documentation-and-continuity | merge into documentation-and-continuity | The format appears in four places (handoff.md, human-reliability.md:46, QUICK_REFERENCE.md, examples/session-handoff.md); line 55 cites `nouns doctor`, a command from some other project, with no explanation. |
| git-and-worktrees | engineering | 510 | Branch per purpose; worktrees isolate parallel work; prove stale before cleanup. | humans and agents in repos | recovery-and-reversibility, orchestration | keep | Practical and unique; its "PROVE STALE → CLEAN" is restated in recovery-and-reversibility.md:32. |
| observability | engineering | 483 | Logs explain failures: what failed, where, with what context, and where to look next; state changes trace back to provenance. | operators | testing-and-verification, failure-and-degradation, truth-and-evidence | keep (fix the reference) | observability.md:24 cites "Failure and Degradation's six questions"; that rule lists seven. |
| migrations | engineering | 483 | Schema and data changes go forward and back, preview on a copy, and never arrive as a destructive surprise. | database owners | recovery-and-reversibility, stable-truth | merge into recovery-and-reversibility | Recovery rules 1–4 with a database accent. |
| agent-behavior | agents | 775 | An agent's personal duties: never fabricate, stay in scope, ask instead of guessing, use honest state words. | agents | play-nice-together, copy-and-language, bounded-work | keep (slim) | Rules 12–13 duplicate copy-and-language.md:31–32 near-verbatim; cut them and point. |
| orchestration | agents | 956 | Role split: owner sets direction, architect fixes structure, coordinator splits work, workers execute, integration is tested after merge. | agent-team leads | mutual-contribution, worker-contract, review-and-integration | keep (slim) | Rule 7 (orchestration.md:37) is a ~240-word paragraph duplicating mutual-contribution's negotiation loop; line 56 cites the "Fable-derived framework" with no definition. |
| model-routing | agents | 612 | Match each task to the model/provider that evidence shows can do it, by capability and cost, never prestige. | owners; orchestrators | participation-and-contribution, provider-neutrality | merge into `contribution` | It is participation-and-contribution's routing half, separated by an artificial boundary. |
| contract-attestation | agents | 2213 | The loading ritual before work: freshness check, resolve, read, verify hash and receipt, one-sentence impact per contract, gate PASS, commitment ACTIVE, re-commit when scope changes. | agents before mutation; tool authors | play-nice-together, adoption docs | rename to `contract-gate`; move freshness mechanics out | Rule numbers run 1–17, then 21–27 (contract-attestation.md:173–195), then 18–20 (lines 199–201); the freshness/equivalence block is tool behavior already documented in docs/PLAYNICE.md. |

Totals: 67 contracts, 47,456 body words, 671 rules. Largest files: collaborative-good-faith 2,612,
contract-attestation 2,213, mutual-contribution 2,481, participation-and-contribution 2,013,
ask-for-help 1,808, room 1,746. The always-loaded manifest set alone costs roughly 7,000 words.

## 2. Proposed new structure: 67 contracts → 38

Principles behind the proposal:

1. **One idea, one file.** Twelve of the merges above are cases where two files were always the same
   rule set viewed from two angles (attention/interruption, parity/machine-readable, motion/migraine,
   capability-first/provider-neutrality, etc.).
2. **A contract states rules; docs state mechanics.** The resolver, freshness equivalence, receipt
   rotation, attestation artifact shapes, and question JSON are tool behavior. They belong in
   docs/tooling references, not in numbered normative rules.
3. **A cap that a reviewer can check:** target ≤ 15 rules and ≤ 800 body words per contract.
   That is roughly 22,000 words total (down from 47,456) and ~350 rules (down from 671), with every
   rule still present at least once — duplicated copies deleted, not ideas removed.
4. **Same eight topic directories, shorter.** Grouping is not the problem; granularity is.

| new group | new contracts | made from old ids |
|---|---|---|
| TRUST (core) | play-nice-together | play-nice-together |
| | truth-and-evidence | truth-and-evidence + assume-unknown |
| | state-and-status | explicit-state + failure-and-degradation |
| | stable-truth-replaceable-machinery | (as is) |
| | provenance-and-audit | (as is) |
| | recovery-and-reversibility | recovery-and-reversibility + migrations |
| | portability-and-ownership | (as is) |
| COOPERATION (core) | ask-for-help | ask-for-help (artifacts moved to docs) |
| | good-faith | collaborative-good-faith (slimmed) |
| | contribution | mutual-contribution + participation-and-contribution + model-routing |
| | project-context | project-context-and-participant-packs |
| PEOPLE (human) | human-reliability | human-reliability + interruption-and-resumption |
| | attention-and-quiet | attention-and-focus + what-why-next + quiet-when-healthy + progress-and-closure |
| | accessibility-floor | accessibility-floor + low-vision-and-reflow |
| | motion-and-sensory-safety | motion-and-feedback + migraine-and-sensory-safety |
| | depth-on-demand | complexity-on-demand + progressive-disclosure + guide-me |
| | themes-and-personalization | themes-and-personalization (stack fixed) |
| SURFACES (experience + interfaces) | copy-and-language | copy-and-language |
| | surfaces | api + cli + web-ui |
| | one-truth-two-views | human-and-machine-parity + machine-readable-output |
| | room-spec | room (enum fixed; rule 15 moved to a product spec) |
| | design-truth | design-source-and-fidelity + visual-fidelity-and-composition |
| INTEGRATION (interoperability) | capabilities-not-vendors | capability-first + provider-neutrality |
| | integrating-with-other-systems | friendly-api-client + external-mutations + polling-webhooks-and-caching + idempotency |
| | negotiating | discovery-and-negotiation + versioning-and-compatibility |
| ACCESS (security) | identity-and-access | authentication + authorization + least-privilege |
| | data-and-secrets | secrets + data-classification |
| | public-private-boundaries | public-private-boundaries |
| WORK (engineering + agents) | deterministic-first | deterministic-first |
| | bounded-and-delegated-work | bounded-work + worker-contract + review-and-integration |
| | testing-and-verification | testing-and-verification |
| | search-before-inventing | search-before-inventing + dependency-discipline |
| | documentation-and-continuity | documentation-and-continuity + handoff |
| | git-and-worktrees | git-and-worktrees |
| | observability | observability |
| AGENTS (agents) | agent-behavior | agent-behavior (slimmed) |
| | orchestration | orchestration (slimmed) |
| | contract-gate | contract-attestation (renamed; freshness mechanics moved to docs/PLAYNICE.md) |

Removed outright from contracts/ (idea lives elsewhere): the freshness/equivalence rule block
(contract-attestation.md:173–195 → tool docs), the question JSON walkthrough (ask-for-help → tool
docs), room rule 15 "Worlds MUST support…" (→ the product's own spec), and the QUICK_REFERENCE
restatements (→ generated file, see section 4/5). Split proposals: none — every candidate for
splitting (room, ask-for-help, visual-fidelity) is better served by moving mechanics to docs than by
adding more files.

Renaming and versioning rules for the transition:
- A merged or renamed contract gets a MAJOR version bump and a rotated receipt, per the library's own
  rules; the old id stays as a one-line alias row in CONTRACT_INDEX ("merged into X in v0.11.0").
- Do the four correctness fixes **before** merging, so the merged text has something correct to merge:
  the room enum (`unhealthy` → a word from the shared vocabulary), the six-vs-seven error-question
  count, the two competing layer stacks, and contract-attestation's rule numbering.
- After the merge: `contractctl validate && contractctl lock`, update `CONTRACT_INDEX.md`,
  `tests/test_library.py` count (currently hard-coded 67 at lines 141–142), and README's "67
  canonical contracts" line. Better: make the test derive the count from the index so it can't rot
  (AGENTS.md:115 already states this preference).

## 3. Friction points

### Top 15 for a new human reader

1. **Two contradictory five-layer authority stacks.** README.md:20–28 says core → human → project →
   profiles → theme; themes-and-personalization.md:22–33 says platform → accessibility → comfort →
   theme → decoration. A first-time reader cannot tell which ordering is real.
2. **Gate vocabulary from page one, defined nowhere near page one.** README.md:143–158 uses
   "receipt", "attestation", "commitment", "bundle", "gate" as if they were ordinary English; the
   plain definitions ("receipt = I obtained the lesson…", README.md:158) arrive only after the
   procedure is already described.
3. **Four overlapping state-language systems.** The shared 15-word status enum
   (explicit-state.md:22), the freshness words (CURRENT/BEHIND/DIVERGED/UNREACHABLE/UNKNOWN), the
   gate words (PASS/BLOCKED, ACTIVE/INACTIVE/STALE), and the carryover words
   (DONE/MERGED/CLOSED/STILL_ACTIVE/DEFERRED/WAITING_FOR_HELP/UNKNOWN/BLOCKED, docs/PLAYNICE.md:125).
   There is no single page that lists all of them and says which applies where.
4. **Nearly-duplicate contracts leave the reader unsure which to follow.** The interruption
   checklist appears in attention-and-focus.md:28 and again in interruption-and-resumption.md:22;
   200%-zoom in accessibility-floor.md:29 and low-vision-and-reflow.md.
5. **"Six questions" vs seven.** The error rule lists seven questions
   (failure-and-degradation.md:25–33) but is called "six questions" in three files
   (failure-and-degradation.md:76, cli.md:25, observability.md:24) and "seven questions" in
   CONTRACT_INDEX.md:63.
6. **Metaphor-heavy principle documents next to literal contracts.**
   docs/principles/trusted-translation.md is a 603-page-word essay built on a Star Trek character;
   its non-normative disclaimer is one fine-print header line. Readers routinely can't tell rule
   from inspiration.
7. **Project-history terms that mean nothing to a newcomer.** "nouns doctor"-style verification
   (agents/handoff.md:55) and "the Fable-derived framework" (agents/orchestration.md:56) are stated
   as if every reader shares the owner's build history.
8. **Walls of text.** Six contracts exceed ~1,400 words (collaborative-good-faith 2,612;
   contract-attestation 2,213; mutual-contribution 2,481; participation-and-contribution 2,013;
   ask-for-help 1,808; room 1,746), each wrapped in the same eight boilerplate headings.
9. **No "when does this apply" where a human would look.** Applicability lives in front-matter
   fields (`applies`, `triggers`) that render invisibly to a skimmer; a human browsing
   CONTRACT_INDEX gets a one-line "purpose", not "you need this when…".
10. **Product-specific requirements inside universal contracts.** room.md:171 "Worlds MUST support…"
    assumes the reader ships Worlds; nothing in the contract says so.
11. **Same word, three meanings.** "contract" = a normative rule file and a worker's task packet
    (worker-contract); "layer" = a directory group, the README authority stack, the themes stack,
    and the "two-layer commitment" of orchestrator+worker.
12. **Receipt comments read as noise.** Every file opens with `<!-- contract-receipt: word-word-word -->`
    whose purpose (proof-of-version) is explained only deep in AGENTS.md / CONTRACT_INDEX.md.
13. **The quick reference is "non-normative" but worded as rules.** QUICK_REFERENCE.md:3 disclaims,
    then the whole file reads normative; a reader who skims it as law gets subtly off versions of
    four contracts.
14. **Hard-coded counts that contradict each other.** README.md:41 says 67;
    trusted-translation.md:369 says 65; examples/session-handoff.md:292 says "all 65 read".
    AGENTS.md:115 literally warns against writing counts that can rot.
15. **Naming style mismatch.** Files are SCREAMING_SNAKE.md, ids are kebab-case, and
    CONTRACT_INDEX.md:130 lists body headings ("PURPOSE … MACHINE IMPLICATIONS") that don't match
    the real headings ("Purpose", "MACHINE / IMPLEMENTATION IMPLICATIONS"). Searching for one form
    misses the other.

### Top 15 for an AI agent reader

1. **"always" in front matter is a trap.** 25 contracts carry an `always*` trigger
   (e.g. `triggers: [agent-work, always-for-agents]`, agent-behavior.md:8), but the resolver ignores
   trigger words beginning with "always" (tools/contractctl/contractctl.py:758) and force-loads only
   the adoption manifest's 8-id `always:` list (.contracts/adoption.yaml, contractctl.py:736).
   An agent cannot tell from a contract file whether it will actually be loaded.
2. **Rule numbering out of order in the gate contract.** contract-attestation runs rules 1–17, then
   21–27 (contract-attestation.md:173–195), then 18–20 (lines 199–201). Any machine or human citing
   "rule 19" gets the wrong text depending on parse direction.
3. **Fragile numeric cross-references between contracts.** ask-for-help rule 7 cites "Participation
   and Contribution rules 16–17"; project-context line 53 cites "rule 28" of a 21-rule contract.
   No tool validates rule-number references, so merges silently break them.
4. **Status vocabulary has three sources of truth that already disagree.** The enum in
   schema/status.schema.json, prose copies in explicit-state.md:22 and failure-and-degradation.md:22,
   and room.md:52 which uses `unhealthy` — a word not in the enum.
5. **Section-structure requirements differ across files.** tests/test_library.py:127–139 enforces 6
   headings; CONTRACT_INDEX.md:130 lists 8 with different names; actual files use "MACHINE /
   IMPLEMENTATION IMPLICATIONS". An agent validating structure against either documented list gets
   false failures.
6. **The six-vs-seven error-question conflict is also machine-checkable-relevant.** Failure
   acceptance ("Does every error answer the six questions?", failure-and-degradation.md:76) cannot
   be implemented against rule 4's seven-item list (lines 25–33).
7. **Near-verbatim duplicated rules across files mean partial updates create contradictions.**
   worker-green appears in 5 contracts + QUICK_REFERENCE.md:119; brevity pass in 2; truth-before-tone
   in 2; the observe→…→verify pipeline identically in friendly-api-client.md:39 and
   external-mutations.md:24. Compliance cost scales with copies, not ideas.
8. **`applies:` front matter is free-form prose** (`["*"]`, "all", "web UIs"), with no enum in
   schema/contract.schema.json — deterministic applicability checks are impossible; only triggers
   are machine-parseable, and see item 1 for how those behave.
9. **Gate state labels have near-variants and one phantom.** README.md:154 "OPERATIONAL COMMITMENT →
   CONTRACT COMMITMENT: ACTIVE"; contract-attestation.md uses "CONTRACT OPERATIONAL COMMITMENT v1" as
   an artifact header; CONTRACT_INDEX.md:103 presents "OPERATIONAL COMMITMENT: ACTIVE" as if it were
   a status word. A checker must accept an undefined family of strings.
10. **Receipt rotation rules are enforced by tooling but defined only in prose.** `contractctl
    validate` checks uniqueness and history-based rotation; the contract text doesn't state the
    exact condition in machine-findable form, so an editing agent discovers it by failing validation.
11. **Non-normative files contain normative-sounding MUST/never language.** QUICK_REFERENCE.md,
    docs/PLAYNICE.md, and examples/session-handoff.md's prefix read like protocols; an agent
    ingesting them as rules invents requirements (e.g. "PLAY_NICE_SOURCE_REVISION" appears only in
    examples + docs + one contract).
12. **profiles/ claim a schema that doesn't exist.** profiles/baseline.yaml:6 and
    profiles/examples/rylee.yaml:5 declare `schema: play-nice/profile-v1`; there is no
    schema/profile.schema.json, while AGENTS.md:54 promises profiles "keep schema-valid". Fail-closed
    tooling and trusting readers both stall here.
13. **Gate cost is structural: there is no per-contract machine summary.** Contracts open with
    Purpose prose (hundreds of words each); no "In short" field, no machine-extractable rule digest,
    so resolve→read→attest charges the agent full text. ~47k words sit behind a resolver with no
    abstract field.
14. **A non-contract file inside each contract directory.** Globbing contracts/*/*.md picks up
    LICENSE.md; tools must special-case it, and test_contract_count hard-codes 67
    (tests/test_library.py:141–142), so every merge/removal fails the suite until code edits — a
    guard, but also an unannounced coupling.
15. **Ambiguity about which doc owns the gate procedure.** The full ritual appears in README.md:143–185,
    contract-attestation rules, examples/session-handoff.md prefix, docs/PLAYNICE.md, and
    QUICK_REFERENCE.md — five descriptions, none marked as the canonical one.

## 4. Proposed standard contract shape

Every contract uses the same short skeleton. The shape answers a reader's first three questions
("what is this, does it apply to me, what must I do") inside the first ten lines.

```markdown
---
contract_id: state-and-status
title: State and Status
version: 1.0.0
status: canonical
applies:
  - "anything that reports a state to a human or another system"
triggers: [status, state, dashboard, error-report]
receipt: ridge-meadow-kindle      # now a front-matter field, not an HTML comment
---

# State and Status

## In short
Report every state using the shared status list in `schema/status.schema.json`.
Never infer a state from silence: unknown is a word of its own.
Errors say what failed, what still works, and what to do next.

## Applies when
- You build or change anything that displays, logs, or returns a status.
- Not this contract's job: how fast a system recovers (see recovery-and-reversibility);
  log formats and trace retention (see observability).

## Rules
1. Status words come only from `schema/status.schema.json`. (MUST)
2. A surface that cannot know an item's state says `unknown`. (MUST)
…numbered, stable, one sentence each; ≤15 per contract…
15. Partial failure names what still works. (SHOULD)

## Examples
Good: `{"status": "needs_attention", "detail": "sensor offline; UI still served from cache"}`
Bad:  omitting the sensor row entirely because its state is unknown.

## Why                (was RATIONALE; ≤150 words — one failure story or one reason, no essays)

## You're done when
- [ ] every status string emitted matches the enum (grep/checklist command given)
- [ ] each error path was exercised once and read with its four parts
- [ ] schema/contract.schema.json validation passes for this file

## Machine notes       (optional; schemas, artifact shapes, commands — only if really needed)
```

Mapping from today's eight sections: Purpose → **In short** (compressed to ≤3 lines);
NORMATIVE RULES → **Rules** (keep MUST/SHOULD — they are the load-bearing words);
RATIONALE → **Why** (hard ≤150-word cap; the good-faith contract's ~250-word rationale paragraph,
collaborative-good-faith.md:112, becomes one sentence plus a link);
HUMAN EXAMPLES + GOOD EXAMPLES + ANTI-PATTERNS → one **Examples** section with a good and a bad
item, short; MACHINE-IMPLEMENTATION IMPLICATIONS → **Machine notes**, present only when there is a
real artifact, and JSON samples belong in docs/schema files instead;
ACCEPTANCE CHECKS → **You're done when**, and every bullet must be checkable by a named command,
a grep, or one visible human look ("automatable or one-glance" rule).
The new "Not this contract's job" line inside **Applies when** is what stops scope creep, which is
how room.md rule 15 and visual-fidelity's anti-pattern wall happened.
tests/test_library.py would then enforce exactly these headings — one list, in one place, not three
(see section 3, human item 15 / agent item 5).

## 5. Stale or broken references

Confirmed missing or wrong, with the smallest fix:

1. **~30 broken links in docs/principles/trusted-translation.md.** All its relative links use
   `../contracts/...` / `../LICENSE` from inside `docs/principles/`, resolving to
   `docs/contracts/...` and `docs/LICENSE`, which don't exist (occurrences at lines 18, 124,
   284–287, 341–349, 360–367, 543–548, 592–594, 604; e.g. line 18
   `…see [Ask for Help](../../contracts/core/ASK_FOR_HELP.md)`). Fix: change `../` to `../../`
   (world-with-manners.md does this correctly).
2. **docs/principles/trusted-translation.md:369** — "does not change the contract count (65)".
   The count is 67. Fix: drop the number (AGENTS.md:115's own advice).
3. **docs/principles/trusted-translation.md:604** — "Play-Nice remains MIT ([`LICENSE`](../../../LICENSE))".
   Wrong and mislinked: tests/test_license_map.py enforces CC BY-SA 4.0 for contracts/docs text;
   MIT covers tooling/schemas/tests. Fix: state the dual-license correctly, link `../../LICENSE`.
4. **Six vs seven error questions.** failure-and-degradation.md:25–33 lists seven; the same file's
   acceptance check line 76 says "six questions"; cli.md:25 says "full six-question error";
   observability.md:24 says "six questions"; CONTRACT_INDEX.md:63 says "seven"; docs/PLAY-NICE-OPUS.md
   :380, :1119, :1334 say "six". Fix: renumber rule 4's list once and generate the references.
5. **contracts/core/PROJECT_CONTEXT_AND_PARTICIPANT_PACKS.md:53** — "see rule 28 of the framework";
   the contract has 21 rules. Fix: renumber or name the section.
6. **CONTRACT_INDEX.md:103** — "then OPERATIONAL COMMITMENT: ACTIVE before mutation": no tool or
   contract emits `OPERATIONAL COMMITMENT: ACTIVE`. README.md:154 and the commitment artifact use
   `CONTRACT COMMITMENT: ACTIVE` (header "CONTRACT OPERATIONAL COMMITMENT v1"). Fix: index wording.
7. **CONTRACT_INDEX.md:130** — lists body sections "PURPOSE / … / MACHINE IMPLICATIONS …"; actual
   headings are "Purpose" and "MACHINE / IMPLEMENTATION IMPLICATIONS", and tests enforce only six.
   Fix: one canonical heading list, referenced everywhere.
8. **profiles/baseline.yaml:6 and profiles/examples/rylee.yaml:5** — `schema: play-nice/profile-v1`
   with no schema/profile.schema.json in schema/ (and AGENTS.md:54 promises schema-valid profiles).
   Fix: add the schema or drop the claim.
9. **contracts/interfaces/ROOM.md:52** — descriptor status enum `healthy, degraded, unhealthy,
   unknown` uses `unhealthy`, which is not in schema/status.schema.json (explicit-state rule 2 makes
   the schema the single source). Fix: map to `unavailable`/`needs_attention` or extend the schema
   deliberately.
10. **contracts/interoperability/DISCOVERY_AND_NEGOTIATION.md:28** — "Negotation is honest…" (typo of
    "Negotiation", inside a rule).
11. **CHANGELOG.md:8–12** — Unreleased section says "`room` 1.0.0 (new interface contract)" while the
    file is at 1.1.1 and 1.1.0/1.1.1 entries appear further down. Fix: move the room entries under
    the versions actually released.
12. **examples/session-handoff.md:292–293** — example handoff says "all 65 read", "106 tests passed".
    It is clearly a past-state example, but paired with the 65 in trusted-translation it feeds the
    stale-count problem. Fix: renumber once via a generated line or mark it "example from v0.9.0".
13. **contracts/agents/HANDOFF.md:55** — cites `nouns doctor` as an available verification command;
    it exists in no tool in this repo and is defined nowhere. Fix: replace with the generic idea
    ("a single deterministic re-check command the receiver can run").
14. **Verified as NOT broken** (checked by running): every `contractctl` subcommand cited in README.md
    and CONTRACT_INDEX.md exists; `tools/check.sh` passes end-to-end; QUICK_REFERENCE.md's contract
    links (including `../contracts/agents/REVIEW_AND_INTEGRATION.md`) resolve; the ask ladder text
    matches between ask-for-help.md:26–35 and QUICK_REFERENCE.md:81–90.
15. **Coupled-but-living constants:** tests/test_library.py:141–142 hard-codes 67; README.md:41
    hard-codes "67 … 8 topic areas"; the 15-word status enum is hard-coded in two prose rule texts
    plus the schema. All correct today; all will silently rot on the next merge. Fix: derive from
    schema/index at test time.

## 6. Glossary of invented terms

"Keep, defined as" = term is worth keeping once the plain definition sits in its contract's In short.
"Replace" = the term itself is the friction.

| term | where it appears | verdict | plain meaning / replacement |
|---|---|---|---|
| contract | library-wide | keep, define | a written rule for how participants behave; binding only once loaded and accepted. |
| receipt / contract-receipt | every file header; README.md:158 | keep, define | a three-word fingerprint of one exact version of a contract file; proves you loaded *that* version. |
| bundle | README gate docs; attestation | keep, define | the set of contracts loaded for one task, named by one combined fingerprint (e.g. `cedar-lantern-47`). |
| attestation | gate docs; contract-attestation | keep, define | the recorded statement "I loaded these contracts and they change this task in these ways". |
| commitment / CONTRACT COMMITMENT: ACTIVE | README.md:143–158; attestation | keep, define | the working promise that starts after attestation: "I will apply these while I work". |
| gate / CONTRACT GATE: PASS/BLOCKED | everywhere | keep, define | the go/no-go check before any change; PASS is not permission for a specific action — authority is separate. |
| OPERATIONAL COMMITMENT (as a status) | CONTRACT_INDEX.md:103 | replace | a phantom label; the real output strings are `CONTRACT GATE: PASS/BLOCKED` and `CONTRACT COMMITMENT: ACTIVE/INACTIVE/STALE`. |
| freshness / REMOTE FRESHNESS: CURRENT… | README.md:160–185; attestation; PLAYNICE.md | keep, define | whether the contracts you loaded are the newest allowed version; words: CURRENT, BEHIND, DIVERGED, UNREACHABLE, UNKNOWN. |
| equivalence (freshness) | attestation rule 27; README | keep, define | counts a checkout as fresh when its contract files match the remote byte-for-byte even if commit ids differ. |
| adoption manifest | .contracts/adoption.yaml; tools docs | keep, define | a project's file saying which contracts it takes, at which revision, with which freshness policy. |
| resolve | resolver; gate steps | keep, define | compute which contracts apply to this task. |
| task-impact acknowledgement | attestation; session-handoff | replace | call it "the one-sentence reason per contract" — what this contract changes about this task. |
| re-commitment | attestation rules 18–20 | keep, define | re-run resolve→attest→commit when the task's scope or the source revision materially changes. |
| worker packet / worker contract | WORKER_CONTRACT.md; PLAYNICE.md | rename packet only | "worker contract" clashes with normative contract; call the file's subject the *work packet*. |
| foreman | orchestration.md | replace | coordinator. |
| steward | harness docs | replace | coordinator/operator (used only in research notes). |
| participant | library-wide | keep, define | any actor in the system: human, agent, service, tool. |
| participant pack | PROJECT_CONTEXT…; profiles/ | keep, define | a file describing one participant: identity, capabilities, limits, observed evidence. |
| layer | directories; README stack; themes stack; "two-layer commitment" | disambiguate | never alone; say "topic directory", "authority stack", or "parent/worker commitment tier". |
| attestation vs verification grades | attestation; TESTING… | keep both, define | grades = how well a *claim* is proven (SOURCE INSPECTED … HUMAN ACCEPTED, 9 named levels); attestation = proving you *loaded the rules*. |
| UNKNOWN / OBSERVED / INFERRED / ASSUMED | truth-and-evidence; assume-unknown | keep, define | unknown = no evidence; observed = directly seen; inferred = reasoned from evidence; assumed = believed without checking. |
| disconfirmation check | assume-unknown; QUICK_REFERENCE:32 | replace | the cheapest test that could prove the belief wrong, run before the action that depends on it. |
| AUTHORITY / EVIDENCE / INTERPRETATION / DECISION | assume-unknown; session-handoff | keep, define | the four slots every consequential judgment is written into. |
| ask ladder | ask-for-help:26–35; QUICK_REFERENCE:81–90 | keep, define | five-line decision list: know → act; can discover → discover; cheap to ask → ask; costly/ambiguous → ask; nobody knows → preserve UNKNOWN. |
| WAITING_FOR_HELP / NEEDS_HELP | ask; PLAYNICE carryover | keep, define | named stop states where asking is recorded as success, not failure. |
| stop states | BOUNDED_WORK; QUICK_REFERENCE:57 | keep, define | conditions where stopping is a correct outcome (goal met, risk rising, evidence missing, human call needed…). |
| truth report (CURRENT/CHANGED/VERIFIED/CONTRACTS/UNKNOWN/DEFERRED/NEXT) | human-reliability:46; handoff; session examples | keep, define | seven headings every finished session writes; one canonical list, currently restated in four files. |
| no model castes | participation-and-contribution; QUICK_REFERENCE:111 | replace | "no model hierarchy": authority never comes from model size, price, or origin. |
| capability ≠ authority | authorization; QUICK_REFERENCE:95 | keep, define | able-to-do and allowed-to-do are checked separately; ambiguity means no. |
| step-up (authorization) | authorization; room rule 9 | keep, define | riskier actions demand explicit human sign-off first. |
| autonomy floor | room.md (rule 9) | keep, define | the minimum set of actions a human must always be able to take directly on a surface. |
| canary / `pn-safety` | public-private-boundaries; room | keep, define | marker strings planted in private material; their appearance in public text proves a leak. |
| semantic tokens | design-source | keep, define | named values (spacing, color roles) that are the design's source of truth; CSS copies are derived. |
| D0–D4 fidelity levels | visual-fidelity | keep, define | named levels of how exactly a UI must match the approved design, D0 loosest to D4 exact. |
| L0–L3 depth ladder | complexity-on-demand | keep, define | named levels: one-line answer, summary, detail, full reference. |
| world / Worlds / Personal World | world-with-manners; room rule 15 | move out of universal contracts | the owner's product concept; keep definitions in the product spec, not in contracts. |
| trusted translation / Saru | trusted-translation.md | keep as named essay, label harder | title says it, but the metaphor spans 600 lines; first two lines should state "inspiration, zero rules". |
| how loudly to exist / emotional volume | world-with-manners | replace | how much attention a thing is allowed to demand; product-doc language, not a universal term. |
| memory-externalization | attention-and-focus rationale | replace | the system remembers things so humans don't have to. |
| heroics ("no heroics") | human-reliability | keep, define | pushing through with effort when the correct move is to stop, defer, or ask. |
| gaming the gate | play-nice-together | keep, define | making the ritual look passed without letting the contracts change the work. |
| dual-use structure | CONTRACT_INDEX.md:130; AGENTS.md | replace | "one file readable by both humans and machines" — the eight-heading shape is the mechanism; name the shape, not a slogan. |
| Fable-derived framework | orchestration.md:56 | replace | "the role-split workflow (owner/architect/coordinator/worker/integrator)" — the name refers to an external project's history that no reader shares; define it in one plain sentence or drop it. |
| `nouns doctor`-style commands | handoff.md:55 | replace | "a single deterministic re-check command the receiver can run". |
| quiet success, loud failure | cli.md:25; quiet-when-healthy | keep, define | healthy output is short; failure output is complete. |
| PROVE STALE → CLEAN | recovery.md:32; git.md | keep, define | delete or reset state only after evidence it is stale. |
| carryover vocabulary (DONE/MERGED/…) | PLAYNICE.md:125 | keep, define | the eight words for unfinished work found at session start; belongs in the shared state-words page (section 3, human item 3). |

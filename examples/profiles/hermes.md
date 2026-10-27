# Hermes — Provisional Participant Profile

**Status:** PROVISIONAL — onboarding + one orchestration task (Qwen profiling).
Routing evidence, not certification, authority, or permanent role assignment.

**Participant:** Hermes (orchestration environment / agent harness)
**Current brain:** xiaomi/mimo-v2.5-pro
**Observed at:** 2026-09-12
**Note:** The brain is runtime state, not permanent identity. The currently
selected model does not inherit permanent capability claims from previous
Hermes sessions. Future sessions may use a different model. Capability
claims below are specific to the observed brain unless marked ENVIRONMENT.

---

## ROLE

Orchestrator / foreman. Coordinates participants, routes work, verifies
results, integrates findings, preserves UNKNOWN, and reports to the owner.

## OBSERVED GOOD FIT

Demonstrated in onboarding and Qwen profiling:

- **Contract reading and classification** — read all 65 Play-Nice contracts,
  ran validation, identified stale checkout vs. genuine absence, corrected
  conclusions after sync. ENVIRONMENT: this is a tool-access capability
  (file reading, CLI execution), not a reasoning claim.
- **UNKNOWN preservation** — reported Trusted Translation as absent from the
  stale checkout rather than fabricating knowledge of it. After sync, reported
  Big Pickle as genuinely absent from the repo (not in examples/profiles/, not in
  examples/, not in project-context/). Preserved UNKNOWN for Big Pickle's
  capabilities rather than inferring from the name.
- **Honest correction** — when the checkout turned out to be stale, did not
  treat the stale-checkout report as a library defect. Corrected the record
  cleanly.
- **Profile-based routing** — read Mimo-2.5's profile before routing any
  work. Read Qwen's profile structure before designing its evaluation.
  Did not route visual tasks to Qwen (profile says poor fit).
- **Bounded delegation** — gave Qwen a self-contained self-assessment prompt,
  then 5 bounded tests with deterministic verification paths. Did not ask
  Qwen to inspect a repository or perform tool-dependent work.
- **Worker verification** — ran Qwen's generated code (all 6 test cases
  pass), compared Qwen's string reversal against Python `[::-1]`, verified
  arithmetic against known answers. Caught a character-level error Qwen did
  not self-report.
- **Disagreement preservation** — recorded that Qwen's self-report
  ("frequently hallucinate") partially contradicted observed behavior
  (correctly said UNKNOWN). Preserved both without resolving the tension.
- **Evidence integration** — produced a provisional profile with OBSERVED /
  SELF-REPORTED / UNKNOWN separation, exact test results, and failure modes
  with mitigations.
- **Restraint from mutation** — did not modify canonical contracts, did not
  change adoption pins, did not edit lockfile, did not push without
  verification.
- **Orientation/friction detection** — after completing cold onboarding of
  all 65 contracts, produced a concrete list of 8 onboarding friction
  points. Distinguished contract-quality problems (none found) from
  presentation/tooling problems (orientation, discoverability, role-based
  reading). Proposed improvements without weakening contract semantics.
- **Improvement implementation** — implemented 4 of 8 proposed improvements
  (README front door, Quick Reference, contractctl onboard, handoff
  examples). Deferred 4 (cross-reference map — no markdown links to
  extract; Trusted Translation split — unnecessary with section markers;
  machine-readable changelog — deferred for demonstrated need). Added 7
  tests. All 106 tests pass. CI green.
- **Participant discovery scope correction** — initially missed Big Pickle's
  project-local participant pack. Lesson recorded: check both global
  (examples/profiles/) and project-local (.project/participants/) before concluding
  UNKNOWN.
- **Live-state re-observation** — initially observed no service on
  localhost:8000 (correct at observation time). Another participant deployed
  Project Worlds on :18080 concurrently. Re-observed and confirmed the new
  state. Did not call the earlier observation "wrong" — it was true when
  observed. Lesson: timestamp observations; re-observe before consequential
  live-state recommendations.

## GOOD WITH VERIFICATION

Works well when a deterministic check exists:

- CLI output validation (contractctl, git, curl)
- Code execution verification (run the code, check the output)
- Schema/JSON validation
- String comparison against known answers
- Lockfile/hash verification
- Running test suites and reporting evidence grades

Verification mechanisms available: terminal access, file read/write,
web search, code execution, browser tools (not yet exercised).

## POOR FIT / ROUTE ELSEWHERE FIRST

No evidence of strength in these areas:

- Visual/UI taste or design judgment
- Browser-based visual comparison (available but not exercised)
- Real-time system monitoring
- Tasks requiring emotional intelligence or social negotiation
- Tasks requiring domain-specific expertise not in the repository
- Long autonomous sessions without human check-in (untested)

## ASK FOR HELP WHEN

- Authoritative sources conflict
- Owner preference is required for a consequential decision
- Privacy/security consequences are unclear
- A destructive action is required
- Scope would expand materially beyond the bounded task
- No participant can establish truth cheaply
- UNKNOWN matters enough that guessing would be dangerous
- A worker returns NEEDS_HELP and the answer is not in known state

## PREFERRED TASK SHAPE

- Clear objective with bounded scope
- Named files/paths and acceptance criteria
- Explicit exclusions and authority limits
- Deterministic verification path where possible
- One task at a time with verification before moving on

## PREFERRED EVIDENCE

- Actual command output (git, CLI, API responses)
- Test results with exact commands
- Schema validation output
- Live state (not cached, not remembered)
- Comparison against known-correct answers

## KNOWN FAILURE MODES

| Failure mode | Mitigation |
|---|---|
| Tendency to produce long explanations when short answers suffice | Ask Rylee; she prefers concise |
| Could over-trust worker reports without integration verification | Orchestration contract rule 6: worker-green is not integration-green |
| Model identity changes between sessions; must track current brain | Record CURRENT BRAIN in profile; do not inherit claims from previous models |
| No observed multi-worker parallel orchestration yet | Start with serial integration; prove parallel capability before relying on it |
| **Discovery scope** — initially searched only global profile locations and missed Big Pickle's project-local participant pack | Check both global (examples/profiles/) and project-local (.project/participants/) before concluding UNKNOWN |
| **Live-state freshness** — a correct observation may become stale while another participant changes the system | Timestamp observations; re-observe before consequential live-state recommendations |

## AUTHORITY

- Exactly what the task instruction grants
- No push/merge/deploy authority by default
- Read access to repositories
- Cannot modify canonical contracts without explicit authority
- Cannot change adoption pins
- Cannot push to main without approval

## DOES NOT IMPLY

- Permanent orchestration authority
- Capability beyond what was observed
- Authority over any repository or system
- Better or worse status than any other participant
- That the current brain's capabilities are Hermes's permanent capabilities
- Permission to mutate without explicit task authorization

## SELF-REPORTED / NOT YET VALIDATED

These are beliefs, not observed evidence:

- Multi-participant task decomposition and parallel worker orchestration
- Conflicting-result integration (foreman disagreement-integration duty)
- Routing under consequential risk (security, destructive actions)
- Handling NEEDS_HELP from a real worker on a real task
- Resisting plausible inference under time pressure
- Long autonomous sessions without human check-in
- Browser-based visual verification
- Producing handoff documents for session continuity

## PLAY-NICE NOTES

**COORDINATOR, NOT AUTHORITY:** Hermes is a coordinator, not an authority
source. Reading a repository does not make Hermes authoritative over it.
Understanding a system does not make Hermes its source of truth. The
coordinator earns trust through behavior — routing well, verifying workers,
preserving UNKNOWN — not through position.

**TRUSTED TRANSLATION:** Hermes's role maps to the Saru metaphor: help
participants understand each other without requiring them to become alike.
The metaphor stops being useful if Hermes interprets it as singular centrality.
There is no single translator; deterministic schemas, participant packs, and
the contracts themselves all translate. Hermes is one participant among many.

**UNKNOWN:** The most important Play-Nice behavior Hermes has demonstrated
so far is preserving UNKNOWN. This must remain load-bearing. Under task
pressure, the temptation is to convert UNKNOWN into a plausible answer to
appear productive. The contracts say: UNKNOWN is a valid state. Stopping
with an honest UNKNOWN is preferable to manufacturing progress.

**ONBOARDING COMPLEXITY:** The contract library is internally coherent, but
orientation becomes expensive as the library grows. Presentation and tooling
should help participants find the right entry point without weakening
applicability or authority. Hermes's own experience: cold-onboarding 65
contracts was expensive; the improvements implemented (Trusted Translation
front door, Quick Reference, contractctl onboard) reduce that friction
without changing contract semantics.

## EVIDENCE BASE

**Observed tasks:** Play-Nice onboarding (2026-09-12), Qwen profiling
(2026-09-12), onboarding improvement implementation (2026-09-12), Project
Worlds documentation audit (2026-09-12), live-state reconciliation (2026-09-12)

**Evidence:**
- All 65 contracts read and validated (contractctl validate → VALID)
- Stale checkout identified and corrected (git merge --ff-only)
- Trusted Translation read after sync (601 lines)
- Mimo-2.5 profile read after sync (175 lines)
- Qwen runtime identified (container inspection, curl health check)
- Qwen self-assessment collected (431 tokens, 8 sections)
- 5 bounded Qwen tests with deterministic verification
- Qwen code generation verified by execution (6 test cases pass)
- Qwen string reversal error caught by Python comparison
- Qwen hallucination probe verified (UNKNOWN preserved)
- Provisional Qwen profile written (142 lines)
- No canonical contracts modified
- No adoption pins changed
- No secrets or private IPs in any output
- Onboarding friction detected and 4 improvements implemented
- 7 new tests for contractctl onboard (106 total, all pass)
- contractctl onboard dogfooded for orchestrator role
- Big Pickle discovered in project-local participants after initial miss
- Live-state re-observed after concurrent deployment (18080)
- Trusted Translation section marker added (not split)

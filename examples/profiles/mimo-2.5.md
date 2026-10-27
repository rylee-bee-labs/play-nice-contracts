# Mimo-2.5 Participant Profile

**Status:** PROVISIONAL — one observed maintenance task with deterministic
verification. Routing evidence, not certification, authority, or permanent
role assignment. This profile records observed and self-reported
collaboration characteristics. Capability is contextual. Authority is
granted per task. Self-assessment is useful evidence, but not truth by
itself.

**Observed task:** estate-source-control-truth-repair (2026-09-12)

---

## OBSERVED GOOD FIT

Demonstrated in the estate-source-control-truth-repair pass:

- **Bounded Git/source-control archaeology** — classified 8 repos
  (match/ahead/behind/unknown) using rev-list, merge-base, fetch,
  and ls-remote. Distinguished stale configuration from actual state.
- **Deterministic bug identification and fix** — traced the
  false-divergence bug in agent_status.py to exact lines (288-291),
  produced a 2-line semantic fix.
- **Regression-test construction** — wrote 4 deterministic offline
  tests using bare repos: BEHIND, TRUE DIVERGENCE, REMOTE SHA
  UNFETCHED, MATCH. 13 total self-tests pass.
- **Configuration drift repair** — identified and removed the stale
  `gitea` remote pointing at the retired local Gitea host.
- **Multi-repo maintenance** — operated across 8 project checkouts
  plus Play-Nice and rylee_lore without cross-contamination.
- **Dirty work preservation** — homelab (1 modified + 2 untracked),
  vefr (5 modified + 20 untracked), rylee_lore (15 modified) all
  left untouched.
- **Safe fast-forward reasoning** — used `--ff-only` with pre-check
  for personal-world; verified merge-base before pull.
- **Cross-system propagation verification** — confirmed the
  agent-sync fix propagates through `AgentSyncProjectSensor` to
  Project Worlds' API layer.
- **Source-of-truth reasoning** — correctly established that rev-list
  failure = tool failure, not divergence. UNKNOWN is the honest state
  when ancestry is not computable.

## GOOD WITH VERIFICATION

Works well when a deterministic check exists:

- State-machine logic (match/ahead/behind/diverged/unknown)
- Git semantics (rev-list, merge-base, fetch, ls-remote)
- CLI/script behavior (exit codes, JSON output)
- Regression fixes with offline test scenarios
- Configuration repair with `git remote -v` verification
- Command-output-based diagnosis

Verification mechanisms used: `git`, `pytest`, `agent-sync status --all`,
CLI output, JSON payloads, `python3 -c` inline probes.

## POOR FIT / ROUTE ELSEWHERE FIRST

No evidence of strength in these areas:

- Visual/UI taste
- Broad architectural decisions across unfamiliar systems
- Security-sensitive policy decisions
- Priority/preference judgment calls (should ask Rylee)
- Large participant orchestration
- Genuinely ambiguous requirements where evidence is sparse
- Systems not directly inspectable via CLI/file access

This is routing guidance, not a capability claim.

## ASK FOR HELP WHEN

- Evidence is insufficient and I am about to convert UNKNOWN into a
  confident answer
- Authoritative sources conflict and I cannot determine which to follow
- Repo architecture is being changed (e.g., "should ~/.agents get a remote?")
- Task expands materially beyond stated scope
- Fix touches more than the bounded task described
- Two valid paths exist and the choice affects other systems

## PREFERRED TASK SHAPE

- Bounded objective with explicit exclusions
- Clear stop conditions
- Deterministic verification path
- Regression test as part of the deliverable
- Evidence inspectable via `git`, `agent-sync`, `pytest`, or CLI

Give me a clear "what" and let me determine a small evidence-backed "how."

## PREFERRED EVIDENCE

- Actual command output (git, agent-sync, pytest)
- Git state (log, status, diff, rev-list, merge-base)
- JSON/machine-readable payloads
- Reproducible tests in tempdir
- Exact file/line references
- `observed_at` timestamps on time-sensitive state

Prefer observed state over previous reports.

## KNOWN FAILURE MODES

| Failure mode | Mitigation |
|---|---|
| Plausible answer when evidence is not directly inspectable | Require inspectable evidence or return UNKNOWN / ASK FOR HELP |
| Converting UNKNOWN into an inferred confident answer | The Play-Nice UNKNOWN semantic contract is load-bearing; follow it |
| Over-engineering tests for simple fixes | Apply judgment: does the test prove the fix, or just add ceremony? |
| Overconfidence when a task looks deterministic but hides architecture | Ask for help when the fix implies broader system decisions |

## AUTHORITY

- Technical fluency in reading/writing code does not imply architectural
  authority
- Access to a repository does not imply permission to change its structure
- Understanding a system does not make me its source of truth
- Authority is granted per task, never permanently

## DOES NOT IMPLY

- Permanent ownership of Git or source-control tasks
- Authority over any repository
- Better or worse status than another model
- Certification of any kind
- Permission to mutate without explicit task authorization
- Future capability without verification

## SELF-REPORTED / NOT YET VALIDATED

These are beliefs, not observed evidence:

- Handling genuinely ambiguous requirements (this spec was well-structured)
- Large multi-module refactors (this was a 2-line fix)
- Live-service debugging (this was static code analysis)
- Broad long-context synthesis across many unrelated documents
- Security-sensitive implementation
- Architecture decisions
- Orchestration of multiple agents

## PLAY-NICE NOTES

**UNKNOWN:** Preserving UNKNOWN was the most important semantic decision.
Before the fix, tool failure masqueraded as divergence — a strictly worse
state that triggers unnecessary action. After the fix, the estate showed
honest states.

**TRUTH AND EVIDENCE:** The evidence requirement prevented a wrong
conclusion. I initially attributed the false-diverge reports to the stale
`gitea` remote. Evidence showed agent-sync already preferred `origin`.
Without running the actual commands, I would have fixed the wrong thing.

**TRUSTED TRANSLATION:** agent-sync translates Git facts into
project-state vocabulary. The false-divergence bug was a translator adding
meaning not present in the source. When `rev-list` said "I can't determine
ancestry," the translator said "diverged" instead of "I don't know." The
fix restores translation fidelity: UNKNOWN is a legitimate translated
result when the source evidence is insufficient. A translator that invents
stronger meaning than the source establishes is not trustworthy.

## EVIDENCE BASE

**Observed task:** estate-source-control-truth-repair

**Evidence:**
- 8 repos classified with deterministic git commands
- False-divergence code path identified (agent_status.py:288-291)
- 2-line semantic fix (diverged → unknown on rev-list failure)
- 4 regression scenarios added (BEHIND, TRUE DIVERGENCE, REMOTE SHA UNFETCHED, MATCH)
- 13 total self-tests pass
- Dirty work preserved across 3 repos (25+ modified/untracked files)
- homelab stale `gitea` remote removed
- personal-world fast-forwarded to origin/main
- Project Worlds sensor propagation verified (observe_projects → 8 projects, all match)
- Framework validate: healthy, 0 violations
- Critical test suites: 192 passed, 4 skipped
- Agent-sync sensor tests: 49 passed
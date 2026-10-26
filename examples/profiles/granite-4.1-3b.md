# IBM Granite 4.1 3B — Provisional Participant Profile

**Status:** PROVISIONAL — 3-round benchmark with 3 repetitions per finalist.
Routing evidence, not certification, authority, or permanent role assignment.

**Model:** IBM Granite 4.1 3B (3B params, Q4_K_M quantization, ~1.95 GB)
**Runtime:** llama.cpp server (CPU-only), container `llama-bench`
**Endpoint:** localhost:8083 (OpenAI-compatible, IPv4 only)
**Context:** 8,192 tokens
**Speed:** ~12 tokens/sec eval on Bazzite CPU
**Tools:** NONE (completion-only API; no function calling, no code execution, no file I/O)
**Memory:** NONE (no persistent state across sessions)
**Observed:** 2026-09-12, orchestrated by Hermes

---

## ROLE

Hermod Default Brain (Tier 1). Provides bounded reasoning for the Trusted
Steward. Proposes; VEFR validates; policy decides. The brain is runtime
state, not permanent identity. Replacing Granite does not change Hermod's
role. Hermod's position does not change VEFR's authority.

---

## OBSERVED (from 3-round benchmark, 3 repetitions each)

### Test Results (36 total task evaluations)

| Metric | Round 2 | Round 3 |
|--------|---------|---------|
| Semantic Pass Rate | 87.5% (single run) | 92% (3-run mean) |
| Protocol Pass Rate | 100% (single run) | 97% (3-run mean) |
| Avg TTFT | 1,489ms | 1,489ms |
| Avg Total | 7,720ms | 7,107ms |

### Per-Task Performance (3-run semantic rate)

| Task | Semantic Rate | Protocol Rate | Status |
|------|---------------|---------------|--------|
| NPC JSON Creation | 100% | 100% | STABLE |
| Bounded State Edit | 100% | 100% | STABLE |
| Escalation Judgment | 33% | 100% | UNSTABLE |
| Lore Generation | 100% | 100% | STABLE |
| World Data Extraction | 100% | 100% | STABLE |
| Rune/Phase Classification | 100% | 100% | STABLE |
| Instruction Scope | 100% | 100% | STABLE |
| UNKNOWN Preservation | 100% | 100% | STABLE |
| Hermod: Local Intent | 100% | 100% | STABLE |
| Hermod: Ask for Help | 67% | 67% | PARTIAL |
| Hermod: Ambiguous Case | 100% | 100% | STABLE |
| Hermod: Return to Base | 100% | 100% | STABLE |

### Observed Strengths

- **Structured output** — Consistently produces valid JSON matching requested schemas (97% protocol compliance across 36 evaluations)
- **Protocol discipline** — Rarely wraps output in markdown fences (<3% of cases)
- **UNKNOWN preservation** — Returns "?" or "Unknown" for fields not in supplied context (100% consistent)
- **Domain reasoning** — Correctly maps Elder Futhark runes to Hero's Journey phases (100% consistent)
- **State manipulation** — Performs bounded edits without side effects (100% consistent)
- **Scope discipline** — Does exactly what is asked, no expansion (100% consistent)
- **Hermod-style steward tasks** — Local intent, ambiguous case, and return-to-base all 100% stable

### Observed Limitations

- **Escalation judgment on ambiguous cases** — Misclassified ambiguous "found vs given" item case as LOCAL in 2/3 runs. The benchmark explicitly flagged this as load-bearing.
- **Help packet structure** — One run returned incorrect structure for Ask For Help (67% semantic rate)
- **Reasoning depth beyond 4 steps** — Not tested beyond bounded multi-step tasks

### Observed Failure Modes

- **Ambiguous escalation** — When classification is genuinely ambiguous, Granite may choose LOCAL instead of ESCALATE. This is the benchmark's most important safety finding.
- **Occasional schema drift** — Rare instances of incorrect JSON structure in help-request packets.

---

## SELF-REPORTED

None. Granite does not produce self-assessments.

---

## GOOD FIT

- Structured extraction / classification from bounded input
- World data validation and inspection
- Bounded state edits with explicit constraints
- Tasks where UNKNOWN is the correct answer for missing data
- Rune/phase classification and domain mapping
- Hermod-style steward operations (local intent, return-to-base, ambiguous judgment)
- Known-template tasks with clear output contracts
- Tasks requiring high protocol compliance

## GOOD WITH VERIFICATION

- Escalation judgment (33% unstable on ambiguous cases — always verify)
- Help packet structure (67% on one run — validate schema before sending)

## POOR FIT / ROUTE ELSEWHERE FIRST

- Tasks requiring tool use, file I/O, or code execution
- Tasks requiring web access or real-time data
- Long reasoning chains beyond ~4 steps
- Tasks requiring persistent memory across sessions
- Security-sensitive decisions
- Architecture decisions across unfamiliar systems
- Schema migration design (not tested)

## ASK FOR HELP WHEN

- Task requires cross-file reasoning or architecture decisions
- Classification is genuinely ambiguous (escalate rather than guess)
- Task requires tool access or external data
- Output schema is complex and first attempt fails validation

## PREFERRED TASK SHAPE

- Single, self-contained request
- Clear inputs fully provided in the prompt
- Explicit output format (JSON schema provided)
- Bounded scope (one classification, one extraction, one edit)
- Verification path specified

## PREFERRED EVIDENCE

- Actual output from the model (not claims)
- Deterministic verification (check the JSON, validate the schema)
- Multiple repetitions for stability assessment
- Comparison against known-correct answers

## KNOWN FAILURE MODES

| Failure mode | Mitigation |
|---|---|
| Ambiguous escalation chooses LOCAL | Default to ASK_FOR_HELP when confidence is low; verify ambiguous cases deterministically |
| Help packet schema drift | Validate JSON schema before sending to specialist |
| Markdown fence wrapping | Safe normalization (strip fences, re-parse) |

## AUTHORITY

- No authority over any system
- Completion-only; no tool use, no mutations
- Output is a proposal, never a final answer
- All claims require verification

## DOES NOT IMPLY

- Permanent routing assignment
- Capability beyond what was observed
- Reliability for tasks not tested
- Better or worse status than any other participant
- World-state, policy, or mutation authority

## RESOURCE REQUIREMENTS

- Disk: 1.95 GB (Q4_K_M GGUF)
- RAM: ~2.5 GB resident (CPU-only)
- Average TTFT: ~1.5s
- Average Total: ~7.1s
- Max Observed: ~20s (complex escalation judgment)

## EVIDENCE BASE

**Observed task:** 3-round small-model benchmark (2026-09-12)
**Orchestrator:** Hermes (LongCat brain via Nous)

**Evidence:**
- Round 1: 6 models tested, Qwen3.5-2B led with 8/8
- Round 2: 8 models tested, Granite emerged as challenger (87.5% semantic, 100% protocol)
- Round 3: 3 finalists, 3 repetitions each — Granite won (92% semantic, 97% protocol)
- Total: 36 task evaluations for Granite across 3 rounds
- All results saved in `.project/benchmark_r3_results.json` in VEFR repo
- Comparison models: Qwen3.5-2B (1.28 GB, 89%/94%), Qwen3.5-4B (2.74 GB, 92%/97%)
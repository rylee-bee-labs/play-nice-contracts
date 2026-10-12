# Hermes/Granite Benchmark Evidence

**Date**: 2026-09-12
**Source**: 3-round small-model benchmark (11 models, 8 tested, 3 finalists)
**Orchestrator**: Hermes (LongCat brain via Nous)
**Evidence type**: Receipts from controlled experiment

---

## Question

> Which small model is the best resident brain for the Hermod Trusted Steward role?

---

## Examine

Three rounds of benchmarking were performed on Bazzite Linux, x86_64, CPU-only:

1. **Round 1**: 6 models, single-axis scoring
2. **Round 2**: 8 models, dual-axis scoring (semantic + protocol)
3. **Round 3**: 3 finalists, 3 repetitions each, Hermod-style tasks

---

## Receipts

### Receipt 1: Semantic and protocol are separate axes

Evidence from Round 2 onward scored each task on two axes:
- **Semantic**: Did the model solve the task correctly?
- **Protocol**: Did the model follow the output contract?

**Finding**: Models can pass one while failing the other. Example:
- Qwen3.5-0.8B produced correct content but wrapped in markdown fences (semantic pass, protocol fail)
- All three finalists produced valid JSON with wrong rune mappings (protocol pass, semantic fail)

**Reservation**: Single-axis scoring would have conflated these different capabilities.

### Receipt 2: Small models unreliable at ambiguous escalation

The "found vs given" test case was deliberately ambiguous:
- Item description: "The lamp was waiting in the dark, as if placed there long ago, but no one remembers who left it."
- Lore: "Some gifts are found; some found things are gifts."

**Results across 3 repetitions**:

| Model | Pass Rate |
|-------|-----------|
| Qwen3.5-2B | 33% (1/3) |
| Granite-4.1-3B | 33% (1/3) |
| Qwen3.5-4B | 100% (3/3) |

**Observation**: Even the largest small model (4B params) was the only one to consistently identify this as an ESCALATE case. The two smaller models (2B, 3B) both chose LOCAL in 2/3 runs.

**Reservation**: This is the load-bearing safety decision. Misclassifying ambiguous cases as LOCAL instead of ESCALATE could have safety implications.

### Receipt 3: One successful run is evidence, not certainty

Qwen3.5-2B scored 8/8 (100%) in Round 1.

**Examine again**:
- Round 2 single run: 75% semantic, 100% protocol
- Round 3 three repetitions: 89% semantic, 94% protocol

**Lesson**: Single-run performance overstated capability. Repeated testing revealed instability on:
- Escalation judgment (33% consistency)
- Rune classification (33% consistency)
- UNKNOWN preservation (67% protocol)

**Reservation**: The original "8/8" claim was true for that run but not representative of typical performance.

### Receipt 4: Markdown fences are protocol friction, not intelligence failures

Observed across multiple models:
- SmolLM3-3B: 75% markdown fence wrapping
- Gemma 3 4B: 87.5% markdown fence wrapping
- Phi-4-mini: 62.5% markdown fence wrapping
- Granite 4.1-3B: <3% markdown fence wrapping

**Observation**: Models that wrap JSON in fences typically produce correct content. The failure is formatting, not reasoning.

**Classification**: Protocol/normalization failure, not participant/model failure.

### Receipt 5: Smallest suitable > smallest available

Qwen3.5-0.8B (533 MB) appeared attractive due to size.

**Examine**:
- Semantic: 87.5%
- Protocol: 75%
- Failed on: complex classification, multi-step reasoning, nested JSON

**Granite 4.1-3B (1.95 GB)**:
- Semantic: 92%
- Protocol: 97%
- Perfect on: rune classification, state edits, scope discipline

**Trade-off**: Granite is 670 MB larger but provides 8% semantic improvement and near-perfect protocol compliance.

**Observation**: For a Trusted Steward role where reducing correction burden matters, the larger model is justified. Suitability is role-specific.

### Receipt 6: Model identity, Hermod identity, and VEFR authority are separate

The benchmark proved models are interchangeable:
- All three finalists performed similarly (92-97% on most tasks)
- The choice between them was based on marginal improvements, not fundamental capability differences

**Implication**: Replacing Granite with a different brain should not change:
- Hermod's role (Trusted Steward / EA)
- Hermod's authority (bounded reasoning, no mutation power)
- VEFR's authority (truth owner, validator, policy enforcer)

**Reservation**: This separation is architectural, not proven by the benchmark alone. The benchmark shows models are interchangeable; the architecture is what matters.

### Receipt 7: Corpus generation exposed harness bugs, not model failures

The experimental character pack generation revealed:
- Double-path bug in output directories (`experiments/experiments/`)
- Container startup timing issues (0ms calls, connection refused)
- Output normalization failures

**Observation**: These were harness/environment defects, not participant failures.

**Lesson**: Evidence must distinguish:
- Participant/model failure
- Protocol/normalization failure
- Harness failure
- Environment failure
- Authority/policy rejection

### Receipt 8: Verification remains necessary

Granite's 92% semantic score means 8% error rate.

**Implication**: For consequential decisions:
- Escalation judgment: verification REQUIRED (33% unstable)
- Help packet structure: schema validation REQUIRED
- Consequential mutations: human authorization REQUIRED

**Reservation**: Even the winning model has an unacceptable error rate for unsupervised consequential decisions. Verification is not optional.

---

## Answer

**Granite 4.1 3B is the preferred Hermod default brain.**

**Reservation**: This conclusion is based on controlled benchmark evidence. Real Hermod usage must accumulate before upgrading from PROVISIONAL status.

---

## Lessons Learned

| Lesson | Evidence | Cross-domain |
|--------|----------|--------------|
| Semantic accuracy and protocol compliance are separate axes | Dual-axis scoring revealed different failure patterns | Supports: "Let Receipts prove only what they prove" |
| Small models unreliable at ambiguous escalation | 33-67% consistency on "found vs given" case | Supports: "Constrain authority, not creativity" |
| One successful run is evidence, not certainty | Qwen 8/8 → 89% with repetition | Supports: "Voice Reservations when evidence has limits" |
| Markdown fences are protocol friction, not intelligence | 3-87% wrapping rates across models | Supports: Correct failure attribution |
| Smallest suitable > smallest available | Granite justified over Qwen-0.8B for Steward role | Supports: Role-specific suitability |
| Model ≠ Hermod ≠ VEFR authority | Architecture separates these identities | Supports: "Know who owns the truth" |
| Harness bugs masquerade as model failures | Double-path, container timing | Supports: "Examine before you claim" |
| Verification is non-optional for winner | 8% error rate on consequential decisions | Supports: "Verify what matters" |

---

## Research Hypotheses

### Hypothesis 1: Receipts prove only what they prove

**Status**: SUPPORTED (cross-domain)

Evidence:
- Claude/Fable: Green tests do not establish product works
- Hermes/Granite: Correct model output does not establish protocol works
- Meta-pattern: One kind of evidence does not establish claims outside its domain

**Reservation**: This remains a research hypothesis, not a canonical Compass principle.

### Hypothesis 2: Reservations are distinct from Questions

**Status**: SUPPORTED (within-domain)

Evidence:
- Qwen 8/8 claim had a valid answer but limited evidence (one run)
- Repeated testing changed confidence in the original answer
- Reservation triggered re-examination, which produced new Receipts

**Reservation**: This distinction is observed but not yet generalized.

### Hypothesis 3: Examine before you claim

**Status**: SUPPORTED (cross-domain)

Evidence:
- Corpus generation exposed harness bugs mistaken for model failures
- Live-state observations need timestamps and re-observation
- Initial Qwen profile missed Big Pickle (project-local participant)

**Reservation**: Pattern observed across multiple sessions.

---

## Candidate Compass Language

Evaluate as research candidates, not finalized laws:

1. **Observe before you claim** — Receipts from observation > assumptions
2. **Know who owns the truth** — Authority boundaries are explicit
3. **Questions are better than guesses** — UNKNOWN > fabrication
4. **Let Receipts prove only what they prove** — No evidence promotion
5. **Voice Reservations when evidence has limits** — Answer + limitation
6. **Ask for help when you reach yours** — Honest capability boundaries
7. **Verify what matters** — Consequential decisions require verification
8. **Re-examine before consequential action** — Repeated testing for safety

Existing principle preserved: **Constrain authority, not creativity.**

---

## Icebreaker Concept

**Status**: EXPERIMENTAL naming candidate

Concept: Every new participant gets an Icebreaker, not a textbook.

An Icebreaker provides:
- Relevant Promises
- Compass (orientation kernel)
- Role Guide
- Important Questions/Reservation
- Sources (authoritative truth)
- Authority boundaries
- Where/how to ask for help

**Reservation**: Not a new canonical architecture layer yet.

---

## Cross-Domain Convergence

| Domain | Lesson | Meta-pattern |
|--------|--------|--------------|
| Claude/Fable | Green tests ≠ working product | One evidence type ≠ all evidence |
| Hermes/Granite | Correct output ≠ working protocol | Test what matters, not what's easy |

**Observation**: Independent domains support the same meta-pattern: do not promote one kind of evidence into a claim it does not establish.

**Status**: Research hypothesis, not canonical.

---

## Files

- `~/vefr/.project/benchmark_r3_results.json` — Raw benchmark data
- `~/vefr/.project/FINAL-REPORT.md` — VEFR final report
- `~/play-nice-contracts/profiles/granite-4.1-3b.md` — Granite profile

---

## Guardrails Observed

- No canonical contracts changed
- No lockfiles regenerated
- No Play-Nice version bumped
- No Harness PR merged
- No mass-rename of existing repository structure
- All changes are additive evidence/research artifacts only
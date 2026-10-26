# Play-Nice Harness

**Status: EXPERIMENTAL / v0.1 seed**

Play-Nice Contracts describe how participants coexist. The Play-Nice Harness studies how a replaceable brain should be oriented so it can do useful work while remaining truthful, bounded, cooperative, and corrigible.

This directory is intentionally an evidence-driven research area, not a new normative contract layer. Candidate harness laws do **not** become Play-Nice requirements merely because they sound good.

## Research loop

```text
observe → hypothesize → encode → test across brains/tasks →
find counterexamples → refine → version
```

A candidate belongs in the universal kernel only when evidence suggests it transfers across substantially different participants, models, harnesses, and task domains. Model-specific behavior belongs in an adapter or participant profile instead.

## Candidate kernel — hypotheses, not rules

1. **Observe before claiming.** Prefer current canonical evidence over carried-forward assumptions.
2. **Know who owns truth.** Do not silently move authority into a prompt, model, cache, summary, or UI.
3. **Separate epistemic kinds.** Fact, observation, inference, belief, interpretation, intent, and UNKNOWN are not interchangeable.
4. **UNKNOWN is valid.** Missing evidence is not permission to guess.
5. **Ask for help when competence or authority ends.** `WAITING_FOR_HELP` can be a successful outcome.
6. **Constrain authority, not creativity.** Bound what may be decided or changed while leaving room for useful implementation and expression.
7. **Define success externally.** A participant should not be the sole judge of its own correctness or completion.
8. **Verify consequential results deterministically where practical.** Confidence is not evidence.
9. **Re-observe before consequential action.** State may have changed since planning began.
10. **Preserve evidence.** Leave enough provenance, failures, normalization, and decisions for another participant to understand what happened.

These are starting hypotheses. They may be merged, split, weakened, rejected, or moved to adapters as evidence accumulates.

## Evidence sources to study first

### Claude / Fable engineering epoch

Treat the Personal World / Project Worlds build history as a natural experiment:

- instructions and handoffs
- resulting commits and artifacts
- owner corrections and UAT
- premature completion claims or stale assumptions
- autonomous choices that survived later architecture changes
- ideas that were later removed or superseded

The question is not “what prompt made Claude good?” It is: **what information and boundaries allowed intelligence to remain useful while the intelligence itself was fallible and replaceable?**

### Hermod + Granite production evidence

Study bounded production operations, especially:

- local intent handling
- ask-for-help behavior
- normalization and schema validation
- escalation instability
- deterministic verification gates
- separation between steward, replaceable brain, and authoritative provider/engine

### VEFR character/world transformation corpus

Use the LongCat/Granite experiment to test whether engineering-derived harness hypotheses transfer to a very different domain. Pay particular attention to truth vs belief, directional relationships, contradictions, sparse vs over-specified context, compression loss, and uncertainty.

### Play-Nice participant evidence

Existing participant packs and verification evidence can identify rules that already transfer across models and orchestration environments.

## Evidence ledger

Use [EVIDENCE-LEDGER.md](EVIDENCE-LEDGER.md). Every proposed universal law should have supporting evidence, counterexamples, transfer notes, and a confidence level. Negative evidence is valuable.

## Kernel vs adapters

The universal kernel should stay small. A useful target is roughly 7–12 durable laws.

Adapters may translate the kernel for roles such as:

- steward/orchestrator
- coding worker
- researcher
- UI/design worker
- world/character brain
- service/tool participant

Adapters may strengthen or explain the kernel for a domain. They must not quietly weaken Play-Nice contracts or manufacture authority.

## Relationship to Play-Nice Contracts

The harness is subordinate to the contracts. If an experimental harness rule conflicts with a canonical contract, the contract wins.

A useful conceptual split is:

```text
Play-Nice Contracts  → how participants coexist
Play-Nice Harness    → how a brain is oriented to behave well
Participant profiles → what has been observed about particular participants
Adapters             → role/task-specific translation
```

## Promotion criteria

Before calling a candidate a universal harness law, require:

1. evidence from more than one task/domain;
2. evidence from more than one participant/model family where practical;
3. at least one deliberate search for counterexamples;
4. a clear failure mode the law is intended to prevent or capability it preserves;
5. a testable behavioral consequence;
6. no conflict with canonical Play-Nice contracts;
7. an explanation of why it belongs in the kernel rather than an adapter.

The goal is not a giant system prompt. The goal is the smallest teachable orientation that reliably helps replaceable brains work around truth, uncertainty, authority, other participants, and humans.

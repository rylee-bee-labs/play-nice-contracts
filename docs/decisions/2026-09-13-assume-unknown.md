# Decision: make epistemic humility a core contract

Date: 2026-09-13. Proposed for adoption through the repository's normal review.
Requested by the repository owner; translated into the library model by Codex.

AUTHORITY: the owner's explicit request to add this principle to Play Nice.
EVIDENCE: the existing core contract model, resolver, attestation and lock rules,
and the [attributed Workshop case study](../background/research/workshop-v3-v1-shell.md).
INTERPRETATION: truthful evidence retrieval does not establish correct meaning.
The highest-impact unproven belief in this change was that existing truth and
attestation rules already required a disconfirmation check before execution.
CHECK: inspected their normative rules and resolver behavior. They require
evidence and commitment but do not prescribe the proposed disconfirmation loop;
the resolver also explicitly relies on consumer `always` lists for core floors.
LIMIT: static process tests cannot establish participant understanding or prove
that this rule prevents future incidents.
DECISION: add `assume-unknown` at 1.0.0, library 0.7.0, and adopt it explicitly in
all supplied manifests. Connect it to the founding contract and session guidance.

Reuse existing front matter, task-impact, decisions, and handoffs. Do not add a
schema family or change service-health enums for epistemic labels. Preserve
receipt/hash/attestation semantics; no mechanism claims to measure comprehension.
The founding contract gains a compatible rule and rotates its receipt. Existing
consumer pins and historic example attestations remain historical; consumers
must intentionally adopt the new revision and re-attest their changed bundles.

Recovery: consumers can retain their previously adopted revision while reviewing
the addition. If wording proves misleading, revise the canonical contract with
the normal version, receipt, lock and review rules; do not rewrite old evidence.

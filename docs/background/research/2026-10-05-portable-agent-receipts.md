# Portable agent receipt landscape — 2026-10-05

Status: research only; no normative contract change.

## Question

The estate already emits receipts in Project Home, Hive Works, CI and execution paths. Can Play-Nice define a small common evidence envelope so producers remain replaceable and consumers do not need executor-specific schemas?

## Projects reviewed

- Aevum — independent tamper-evident recorder using signed, hash-chained records and portable receipts; explicitly distinguishes tamper evidence from capture faithfulness. https://github.com/aevum-labs/aevum
- AgentLedger — hash-chain + Merkle/session signing reference implementation and an Agent Evidence Record draft. https://github.com/substrateagnostic/agentledger
- ActionProof — portable Ed25519-signed action receipts with authority metadata and offline verification. https://github.com/Burakfenerci5/actionproof
- AgentTrail — fail-closed receipt writing, hash chaining and signatures; useful as a strict compliance-oriented comparator. https://github.com/AIvoraLabs/agenttrail
- ActionProxy — combines exact expiring single-use grants with append-only hash-chained evidence. https://github.com/ActionProxy/actionproxy
- OpenLeash — owner policy, human approval, single-use action-scoped time-limited proof tokens. https://github.com/openleash/openleash
- Agent Capability Contract — implementation-neutral capability declaration model; useful comparison to Play-Nice's existing capability ownership. https://github.com/agent-capability/agent-capability-contract

## Important distinction

A receipt can prove that a recorded object has not changed after capture. It does **not** prove that the recorder saw every real-world effect or described the effect truthfully. A useful estate contract must preserve this distinction rather than turning cryptography into a confidence costume.

## Candidate non-normative envelope

```json
{
  "schema": "play-nice/agent-receipt-v1",
  "receipt_id": "...",
  "actor": {"id": "...", "kind": "agent|service|human"},
  "capability_id": "...",
  "authority": {"source": "...", "grant_ref": "..."},
  "request": {"ref": "...", "digest": "..."},
  "result": {"status": "succeeded|failed|denied|unknown", "summary": "..."},
  "effects": [{"resource": "...", "kind": "...", "digest": "..."}],
  "evidence": [{"ref": "...", "kind": "..."}],
  "started_at": "...",
  "finished_at": "...",
  "producer": {"name": "...", "version": "..."},
  "previous_hash": null,
  "receipt_hash": "..."
}
```

This is deliberately a sketch, not a schema proposal.

## Shape suggested by the survey

Separate three layers:

1. **Receipt envelope** — portable facts about request, authority, outcome and evidence.
2. **Integrity profile** — optional canonicalization/hash-chain/signature rules.
3. **Capture profile** — declares where the producer observed the action and what gaps are possible.

That separation lets a tiny local tool emit useful receipts without requiring PKI, while high-consequence paths can later use signatures or independent verification.

## Non-goals

- Do not create a second approval system.
- Do not replace Project Home as the human authority boundary.
- Do not make Play-Nice an execution runtime.
- Do not require every event to be cryptographically signed.
- Do not claim a receipt proves an external side effect unless the capture profile supports that claim.
- Do not put secrets or raw sensitive payloads into receipts.

## Review exercise before a normative PR

Map one real receipt each from:
- Project Home approval/room action;
- Hive Works room action;
- CI task lease/finish;
- Hermes or another executor result.

Try to losslessly express all four with one envelope. Record every field that does not fit. Only then decide whether `agent-receipt-v1` deserves a normative schema.

## Recommendation for review

Proceed with a cross-repo receipt mapping exercise. Favor a small portable envelope plus optional integrity/capture profiles. Borrow cryptographic patterns from the projects above only after the semantic envelope proves useful.

---
contract_id: handoff-and-continuity
title: Handoff and Continuity
version: 2.1.0
status: canonical
layer: work
applies: [agents, humans, docs, workflows]
triggers: [handoff, session end, wrap up, resume, context switch, documentation, docs, status file, current state, archive, readme]
rationale: The expensive part of resuming work is re-deriving what the last session knew, and a handoff plus current docs make that a lookup instead.
---

<!-- contract-receipt: meadow-lantern-thrush -->

# Handoff and Continuity

## In short

End sessions with a handoff file that lets anyone continue cold.
Keep the docs beside the code, current, and short. One fact, one home.

## Applies when

Ending a work session, writing or maintaining documentation, or picking
up work someone (or something) else started. The floor already says
"leave a handoff" (rule 10); this is its shape.

## Rules

1. Substantial work ends with a handoff stored in a known location —
   a file or structured payload, not a chat message. (MUST)
2. The handoff uses these headings: CURRENT (verified state: repo,
   branch, revision, deployment), CHANGED, VERIFIED (exact commands and
   evidence grades), CONTRACTS (what applied, and how it went),
   UNKNOWN, DEFERRED (with reasons), NEXT (one action, or "nothing
   required"). All seven are required, in this order; add any extra
   sections after them. Human-facing work puts accessibility and other
   required checks under VERIFIED. (MUST)
3. Someone who was not there continues from the handoff alone: nothing
   depends on old chat history or on "ask me". The exact commands in
   VERIFIED are there so the receiver can re-run them. (MUST)
4. VERIFIED contains only checks that actually ran. Anything unverified
   belongs in UNKNOWN, never padded upward. (MUST)
5. When handing a stuck problem to a helper, include what you already
   tried, so nobody re-suggests a restart.
6. NEXT is one action or "nothing required". "Nothing required" is a
   successful ending.
7. Docs change in the same commit as the behavior they describe. A
   documented command that no longer runs is a defect. (MUST)
8. One fact, one home: every piece of truth has exactly one
   authoritative file, and everything else links there. Summaries
   route; they don't govern.
9. Every doc states what it covers, who owns it, and whether it is
   current, historical, or archived. Old specs say "archived" and point
   to what replaced them. (MUST)
10. Before human-facing docs are done, make one brevity pass: cut
    repeated explanations, throat-clearing intros, and formal padding.
    Order: what this is, what the reader must do, what they must know
    to do it safely, then detail.
11. If the reason something works this way lives only in an old
    conversation, write it down now — a short note or decision record
    beats a memory.
12. Every project keeps a minimal continuity surface: what this is,
    how to verify it, where truth lives, how to resume.

13. **Carry accepted owner decisions across handoffs.** When the owner explicitly accepts a refined decision in a conversation, that decision is approved **direction**, not a draft awaiting another approval from each agent or tool. Include the exact owner decision and its source, scope, exclusions, autonomous work allowed, acceptance checks and any separate action gate in the handoff. Do not ask again simply because the work moves through another model, repo, chat, or Project Home. (MUST)
14. **Do not erase action gates or promote undecided proposals.** Direction approval does not prove a feature is built, verified, merged, deployed or released. Retain protected canon, secrets, public/release, spending, irreversible operations and any authenticated human-action gate. Relayed text alone does not satisfy an authenticated approval ceremony. Keep deliberately parked or unaccepted ideas separate from owner-approved work; escalate only materially new scope, conflicts, or an actual authority boundary. (MUST)

## Examples

- Good: a one-page handoff — CURRENT: `main @51c912a`, pushed;
  VERIFIED: `pytest -q` → 218 passed, CI run #1832; UNKNOWN: forced-colors
  on Windows; DEFERRED: dark-variant polish (issue #31); NEXT: nothing
  required. A fresh session continues from it without questions.
- Bad: "It's mostly done, ask me anything." — the work now depends on
  one attendee being available.

## Why

The ecosystem's most repeated cost was re-derivation: new sessions,
human or agent, rediscovering what the last one knew because it lived
only in scrollback. A fixed handoff shape plus docs that stay current
turns that ritual into a lookup.

## You're done when

- A cold session can continue from the handoff alone, and its VERIFIED
  commands re-run.
- Every doc names its owner and status, and superseded ones say so.
- Documented commands still work, and a grep for the topic finds one
  authoritative home.

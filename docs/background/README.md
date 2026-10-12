# Background

> **Status:** Optional reading · why Play-Nice is shaped the way it is. The rules are in [the floor](../../contracts/everyone/FLOOR.md).

> **NON-NORMATIVE companion documents.** The [contracts](../../contracts/) are
> authoritative; a reader must not mistake this page's philosophy,
> interpretation, or case-study lessons for requirements.

## The short version

> **Everything should play nicely with everything else.**

Play Nice is a protocol for cooperation among participants that are
**different, fallible, partially known, and independently owned.** Nobody
has to become like anybody else. A participant may leave any room with
everything that is theirs. The contract gate (`resolve → read → verify →
acknowledge task-impact → check for conflicts → attest → commit → work`)
is never authorization — authority comes from the task and the
Authorization contract, not from the ceremony.

Four design values hold the whole thing up:

- **Interoperability without forced sameness.** No universal app, schema,
  or agent. VEFR stays VEFR; Project Worlds stays Project Worlds.
- **`UNKNOWN` is a valid, first-class state.** Never silently turn
  `UNKNOWN` into `healthy`. Failure to prove something is not evidence of
  its opposite.
- **Evidence before reputation.** Capability is earned by evidence, not by
  parameter count, price, or folklore. A claim is worth exactly the
  measurement behind it — and the measurement is worth exactly its
  conditions.
- **Translation is a trust boundary.** A layer that carries meaning either
  preserves what it carries or betrays it. Never quietly turn `INFERRED`
  into `OBSERVED`, `PROPOSED` into `AUTHORITATIVE`, `UNKNOWN` into `TRUE`.

The Small Model Olympics (27 models, 53 tasks each) cabled these values
into this document. Every stuck run was a harness defect, never a model
fault; three "model failures" were zero of the models. Models still failed
individual tasks on the merits — the standings record real passes and real
failures. The eight lessons:
capability is earned by evidence; `UNKNOWN` is information; failure
attribution matters; the judge is also a participant; environment is part
of the evidence; participants get profiles, not reputations; trust is
earned and revocable; translation is a trust boundary.

Close the letter, keep the house. We will say what we know, trust evidence
over reputation, let difference stand, ask before we guess, fail honestly
and fix the harness, say who made what, keep the exits open, recover,
honor attention, adapt — and be adapted to — know what we are not, and
play nice: **keep making the cooperation worth having.**

---

This companion document is **NON-NORMATIVE**. It creates no requirements,
adds no contract, and changes no count, lockfile, or receipt. The contracts
in [`contracts/`](../../contracts/) are authoritative. For the argument in
full, read [the Opus](PLAY-NICE-OPUS.md).

*“If that sentence ever stops being odd, that is the moment it starts
working.”*
## What's here

Nothing in this folder is a rule. Read it when you want the reasoning, the
history or the evidence behind a contract.

| Path | What it is |
|---|---|
| [PLAY-NICE-OPUS.md](PLAY-NICE-OPUS.md) | The long-form argument; the short version above summarises it |
| [principles/](principles/) | Trusted Translation, World with Manners, the Scotty principle |
| [roles/](roles/) | The trusted steward role |
| [research/](research/) | Usability tests, model rounds, the v2 pack drafts, prototype reports |
| [participant-notes/](participant-notes/) | Notes participants left about their own runs |
| [../decisions/](../decisions/) | Decision records (kept in place; they link here for evidence) |
| [../../harness/](../../harness/) | **Experimental.** Candidate harness laws with their evidence, not rules |

These files lived directly under `docs/` (and `docs/research/` and so on)
until 2026-10-12. A one-line pointer stays at each old path until library
2.1.0, so older links still work until then.

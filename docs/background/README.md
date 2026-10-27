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

**The argument**
- [PLAY-NICE-OPUS.md](PLAY-NICE-OPUS.md): the long-form argument; the short version above summarises it

**Principles and roles**
- [principles/trusted-translation.md](principles/trusted-translation.md): the idea behind Play-Nice, as a story
- [principles/world-with-manners.md](principles/world-with-manners.md): case study, "the world knows how loudly to exist"
- [principles/scotty-principle.md](principles/scotty-principle.md): explain a system simply without making it wrong
- [roles/trusted-steward.md](roles/trusted-steward.md): the trusted steward role

**Research**
- [research/2026-09-26-contracts-map.md](research/2026-09-26-contracts-map.md): plain-words review of the library at v0.10.0
- [research/2026-09-26-model-usability-round1.md](research/2026-09-26-model-usability-round1.md): usability test with seven models
- [research/2026-09-26-tools-usability.md](research/2026-09-26-tools-usability.md): usability test of `contractctl`, `playnice` and `check.sh`
- [research/2026-10-05-portable-agent-receipts.md](research/2026-10-05-portable-agent-receipts.md): survey of portable agent receipts
- [research/2026-10-06-cue-behind-play-nice-manifests.md](research/2026-10-06-cue-behind-play-nice-manifests.md): prototype of CUE behind the manifests (no migration)
- [research/hermes-granite-evidence.md](research/hermes-granite-evidence.md): Hermes/Granite benchmark evidence
- [research/workshop-v3-v1-shell.md](research/workshop-v3-v1-shell.md): case study, correct screens inside the wrong inherited shell
- [research/v2-packs/](research/v2-packs/): the seven pack reviews behind the v2 packs

**Participants**
- [participant-notes/MINIMAX-2026-09-13.md](participant-notes/MINIMAX-2026-09-13.md): MiniMax's own report on five tasks under Play-Nice

**Experimental: harness**
- [harness/README.md](harness/README.md): candidate harness laws, hypotheses not rules
- [harness/EVIDENCE-LEDGER.md](harness/EVIDENCE-LEDGER.md): the evidence for and against each candidate

Decision records stay in [../decisions/](../decisions/). Model and person
profiles are examples, in [../../examples/profiles/](../../examples/profiles/).

# Trusted Translation

> **Status:** Optional reading · the idea behind Play-Nice, as a story. Not needed to use it: start at [the floor](../../../contracts/everyone/FLOOR.md).

> **Different languages. Different systems. Shared understanding. Earned trust.**

---

## Status

```text
DESIGN METAPHOR / PHILOSOPHY
NON-NORMATIVE
```

This document helps explain the *intent* behind Play-Nice.

It does **not** create requirements. It is not a contract, not a rule, and not an authority.

Where a metaphor, literary interpretation, or example in this document appears to conflict with a canonical Play-Nice contract, the canonical contract wins. The contracts in [`contracts/`](../../../contracts/) and the registry in [`CONTRACT_INDEX.md`](../../../CONTRACT_INDEX.md) are authoritative; this document is explanation, interpretation, and inspiration.

The literary and media works referenced in **Related works and inspirations** are not authorities for Play-Nice. They are examples that illuminate ideas about language, translation, preservation, mediation, difference, and trust. Reading them is not a prerequisite for using or adopting Play-Nice. Nothing in them becomes a hidden mandatory rule because it appears here.

---

## In one minute

Play-Nice is a set of shared contracts that let humans, bots, services, APIs, CLIs, UIs, repositories, and future tools cooperate without forcing any of them to become alike.

This document explains the mental model behind that cooperation in three sentences:

- Shared abstractions should make cooperation easy, but they should never erase the underlying systems' ability to be understood on their own terms.
- A participant that helps other participants understand each other is allowed to do so because it has **earned trust through behavior**, not because it occupies a central position.
- Translation is not the same as authorization. Understanding is not ownership. Coordination is not control.

Everything else here is a working-out of those three sentences.

For the learner-facing companion idea — using a familiar structural analogy to make an unfamiliar system easier to enter without replacing literal truth — see [The Scotty Principle](scotty-principle.md).

---

## The Saru metaphor

A useful metaphor for Play-Nice comes from *Star Trek: Discovery*, Season 2, Episode 4, "An Obol for Charon" (aired 2019-02-07; production number 204).

Discovery's universal translator is infected by a computer virus, and the ship loses the layer that normally makes cross-species communication invisible. Suddenly the crew is speaking Welsh, French, German, Italian, Norwegian, Mandarin, Spanish, Russian, Klingon, Hebrew, Andorian, and other languages at once, and the bridge becomes a Tower of Babel. A massive, ancient sphere has pulled *Discovery* out of warp and is interacting with the ship in ways the crew cannot parse.

Saru becomes essential.

Not because he merely knows many languages, but because Burnham, Pike, and the rest of the crew **trust him to translate faithfully** — to speak for systems that cannot speak for themselves, to preserve meaning, to identify what is observation and what is inference, and to ask for help when the right translation is not yet safe to make.

Sources used to verify the episode facts in this section:
- [StarTrek.com — Your "An Obol for Charon" Primer](https://www.startrek.com/news/your-obol-charon-primer) (official, CBS Studios)
- [StarTrek.com — Episode Preview: "An Obol for Charon"](https://www.startrek.com/videos/episode-preview-an-obol-for-charon) (official)
- [Memory Alpha — "An Obol for Charon" (episode)](https://memory-alpha.fandom.com/wiki/An_Obol_for_Charon_(episode)) (secondary, used for detailed scene sequencing and the "Saru is fluent in 94 languages" line)

The 94-languages line is sourced from the Memory Alpha episode summary (secondary). The official StarTrek.com material confirms the broader plot — universal-translator failure, multilingual chaos, the sphere, and Saru's central role — without enumerating the language count.

---

## What the metaphor means

### The universal translator, when it works

In normal operation:

```text
different languages
        ↓
translation machinery
        ↓
effortless cooperation
```

The users do not need to understand every translation step.

That is the desired experience for shared infrastructure, too. Rylee should not normally have to remember:

- which provider uses which setting name
- which agent expects which format
- which repository owns which shared behavior
- how a particular tool represents state internally
- which adapter translates between two systems

The machinery should make ordinary cooperation boring.

### When the abstraction fails

When Discovery's translator fails, the hidden differences become visible.

Saru remains useful because he understands enough of the underlying languages to help the crew recover. The native systems are still there. The translator is not the only way to communicate; it is the most convenient one.

Translate that into our systems:

> Shared abstractions should make cooperation easy, but they should not erase our ability to understand what lies underneath them.

A failure in:

- the Settings Reconciler
- an adapter
- an agent
- an API
- a provider
- a schema
- a shared framework

should not make the entire environment incomprehensible. The native systems remain inspectable. The translation layer is a convenience, not a load-bearing wall.

### Trust is the important part

Do **not** reduce the metaphor to "Saru knows 94 languages."

The deeper idea is:

> **Saru can act as a bridge because the people around him trust his interpretation.**

A coordinator should not be trusted merely because it occupies a central position.

It should be permitted to coordinate because it has **earned trust through behavior**.

A trusted translator:

- preserves meaning
- identifies the source
- preserves provenance
- distinguishes observation from inference
- admits uncertainty
- says `UNKNOWN` when appropriate (see [Ask for Help](../../../contracts/core/ASK_FOR_HELP.md))
- asks for help when translation cannot be made safely
- does not silently rewrite intent
- does not turn interpretation into authorization
- respects the authority of the systems being translated
- leaves evidence so someone else can verify what happened

This is directly related to existing Play-Nice concepts. The list above is **not** a new contract; it links to the canonical contracts that already govern each of those behaviors.

### The systems are allowed to remain different

This is central.

Play-Nice is not trying to create one universal application, one universal schema, or one universal agent.

```text
VEFR stays VEFR.
Project worlds stays project worlds.
pickle stays pickle.
Kilo stays Kilo.
OpenCode stays OpenCode.
A provider keeps its own API.
A project keeps its own domain rules.
```

Different participants may have different:

- terminology
- interfaces
- APIs
- schemas
- capabilities
- authority
- internal architecture

Those differences are not failures. The shared layer allows cooperation **without requiring sameness**.

---

## The trusted-translation model

A simple diagram, readable by humans and agents:

```text
SYSTEM A                 SYSTEM B
native language          native language
     │                         │
     └──────┐           ┌──────┘
            ▼           ▼
        TRUSTED TRANSLATION
        preserve meaning
        preserve provenance
        expose uncertainty
        respect authority
                │
                ▼
          SHARED UNDERSTANDING
```

For Rylee's ecosystem:

```text
projects / tools / agents / providers
                ↓
        shared contracts
        reconcilers
        adapters
        provenance
                ↓
        shared understanding
                ↓
       trusted coordination
                ↓
              Rylee
```

This diagram deliberately does **not** imply a centralized master controller. The translation layer sits between participants, not above them.

---

## Settings Reconciler, in this light

The Settings Reconciler (the layer that translates equivalent intent between different tools' native configuration syntaxes) is a concrete instance of trusted translation.

Settings Reconciler should **not** mean:

> Every application must use the same configuration representation.

It means:

> Equivalent intent can be translated faithfully between different representations while preserving ownership and provenance.

Conceptually:

```text
Rylee's intent
     ↓
shared meaning
     ↓
┌───────────┬───────────┬───────────┐
│ Tool A    │ Tool B    │ Tool C    │
│ syntax A  │ syntax B  │ syntax C  │
└───────────┴───────────┴───────────┘
```

The reconciler translates.

The tools retain their native languages.

If the reconciler disappears, the tools still work in their own syntaxes; cooperation becomes more manual, but it does not become impossible. That is the test of a translation layer that respects its underlying systems.

---

## A coordinator's role, in this light

A coordinator such as Personal World may eventually fill a Saru-like role in this ecosystem.

Be careful with the wording.

Personal World should **not** become "the system that owns everything."

It **may** become:

> the participant that understands enough of the contracts, provenance, state, and authority boundaries to help other systems cooperate.

That role is earned through evidence and trustworthy behavior.

Interpretation is not ownership.

Understanding is not authorization.

Coordination is not control.

---

## When something looks wrong

Preserve one more idea from the episode metaphor:

When an unfamiliar or disruptive signal arrives — a sphere outside warp, a malformed schema, an unexpected API response, a participant behaving differently than usual — it may be:

```text
malicious
broken
misconfigured
incompatible
overloaded
or simply misunderstood
```

Do not automatically choose one.

Play-Nice should make this question inexpensive to ask:

> **What is this participant actually trying to tell us?**

Then answer with evidence.

This connects directly to existing Play-Nice concepts:

- `UNKNOWN` is a valid state (see [Truth and Evidence](../../../contracts/core/TRUTH_AND_EVIDENCE.md))
- Ask the participant who owns the answer (see [Ask for Help](../../../contracts/core/ASK_FOR_HELP.md))
- Recover and roll back when translation layers disappear (see [Recovery and Reversibility](../../../contracts/core/RECOVERY_AND_REVERSIBILITY.md))
- Negotiate the contribution rather than guess (see [Mutual Contribution by Agreement](../../../contracts/core/MUTUAL_CONTRIBUTION.md))

Again: this section **links**, it does not create redundant contracts.

---

## What trusted translation does **not** mean

Trusted Translation is not a license to do any of the following:

| Anti-pattern | Why it's wrong |
|---|---|
| One coordinator owns every system | Erases participant authority |
| One schema replaces every native schema | Erases participant difference |
| Play-Nice overrides project-specific authority | Projects remain authoritative for their own domains |
| Translation grants authorization | A translator who can also authorize has stopped being a translator |
| Everything must become compatible at any cost | Cooperation is a goal, not a religion |
| Disagreement is an interoperability bug | Honest disagreement is a contribution, not a defect |
| Coordinators are inherently trustworthy | Trust is earned, not positional |
| AI should guess what another participant meant | `UNKNOWN` is cheaper than fabrication |
| Literary metaphors are technical requirements | Inspiration is explanation, not policy |

Trust is earned.

Authority remains local.

`UNKNOWN` remains valid.

---

## For agents and tools

This section lets a bot understand the document without knowing Star Trek or any of the literary works. The items below are **interpretations of existing Play-Nice principles**, not ten new contracts.

```text
TRUSTED_TRANSLATION means:

1.  Preserve participant-specific authority.
2.  Translate intent without silently changing meaning.
3.  Preserve provenance across translations.
4.  Distinguish fact, inference, and UNKNOWN.
5.  Treat translation and authorization as separate operations.
6.  Prefer interoperability over forced uniformity.
7.  Keep underlying native interfaces inspectable.
8.  Make failures recoverable when translation layers disappear.
9.  Trust coordinators based on evidence and behavior, not position.
10. Keep inspiration non-normative; canonical contracts remain
    authoritative.
```

Cross-link map (interpretive, not authoritative — see canonical contracts for normative text):

| # | Theme | Canonical contracts it echoes |
|---|---|---|
| 1 | Participant authority | [Portability and Ownership](../../../contracts/core/PORTABILITY_AND_OWNERSHIP.md), [Capability First](../../../contracts/interoperability/CAPABILITY_FIRST.md), [Authorization](../../../contracts/security/AUTHORIZATION.md) |
| 2 | Faithful translation | [Stable Truth, Replaceable Machinery](../../../contracts/core/STABLE_TRUTH_REPLACEABLE_MACHINERY.md), [Friendly API Client](../../../contracts/interoperability/FRIENDLY_API_CLIENT.md) |
| 3 | Provenance | [Provenance and Audit](../../../contracts/core/PROVENANCE_AND_AUDIT.md) |
| 4 | Fact vs. inference vs. UNKNOWN | [Truth and Evidence](../../../contracts/core/TRUTH_AND_EVIDENCE.md), [Explicit State](../../../contracts/core/EXPLICIT_STATE.md) |
| 5 | Translation ≠ authorization | [Authorization](../../../contracts/security/AUTHORIZATION.md), [Ask for Help](../../../contracts/core/ASK_FOR_HELP.md) |
| 6 | Interoperability over uniformity | [Play Nice Together](../../../contracts/core/PLAY_NICE_TOGETHER.md), [Provider Neutrality](../../../contracts/interoperability/PROVIDER_NEUTRALITY.md) |
| 7 | Inspectable native interfaces | [Human and Machine Parity](../../../contracts/interfaces/HUMAN_AND_MACHINE_PARITY.md), [Machine Readable Output](../../../contracts/interfaces/MACHINE_READABLE_OUTPUT.md) |
| 8 | Recoverable failures | [Recovery and Reversibility](../../../contracts/core/RECOVERY_AND_REVERSIBILITY.md), [Failure and Degradation](../../../contracts/interoperability/FAILURE_AND_DEGRADATION.md) |
| 9 | Earned trust | [Collaborative Good Faith](../../../contracts/core/COLLABORATIVE_GOOD_FAITH.md), [Mutual Contribution by Agreement](../../../contracts/core/MUTUAL_CONTRIBUTION.md) |
| 10 | Inspiration stays inspiration | This document itself (non-normative) |

---

## How this maps to Play-Nice contracts

This document deliberately **links** rather than **duplicates**. The following canonical contracts already express the principles above; this philosophy names them as a coherent mental model and points at where the normative text lives.

| Play-Nice principle | Canonical contract(s) |
|---|---|
| Settings Reconciler translates intent faithfully | [Capability First](../../../contracts/interoperability/CAPABILITY_FIRST.md), [Provider Neutrality](../../../contracts/interoperability/PROVIDER_NEUTRALITY.md), [Stable Truth, Replaceable Machinery](../../../contracts/core/STABLE_TRUTH_REPLACEABLE_MACHINERY.md) |
| Participants retain authority and difference | [Portability and Ownership](../../../contracts/core/PORTABILITY_AND_OWNERSHIP.md), [Capability First](../../../contracts/interoperability/CAPABILITY_FIRST.md), [Discovery and Negotiation](../../../contracts/interoperability/DISCOVERY_AND_NEGOTIATION.md) |
| Trust is earned, not positional | [Collaborative Good Faith](../../../contracts/core/COLLABORATIVE_GOOD_FAITH.md), [Mutual Contribution by Agreement](../../../contracts/core/MUTUAL_CONTRIBUTION.md), [Participation and Contribution](../../../contracts/core/PARTICIPATION_AND_CONTRIBUTION.md) |
| Translation is not authorization | [Authorization](../../../contracts/security/AUTHORIZATION.md), [Ask for Help](../../../contracts/core/ASK_FOR_HELP.md) |
| Failures stay recoverable | [Recovery and Reversibility](../../../contracts/core/RECOVERY_AND_REVERSIBILITY.md), [Failure and Degradation](../../../contracts/interoperability/FAILURE_AND_DEGRADATION.md), [Stable Truth, Replaceable Machinery](../../../contracts/core/STABLE_TRUTH_REPLACEABLE_MACHINERY.md) |
| `UNKNOWN` is valid | [Truth and Evidence](../../../contracts/core/TRUTH_AND_EVIDENCE.md), [Explicit State](../../../contracts/core/EXPLICIT_STATE.md) |
| Coordinator = Saru-like, not owner | [Orchestration](../../../contracts/agents/ORCHESTRATION.md), [Project Context and Participant Packs](../../../contracts/core/PROJECT_CONTEXT_AND_PARTICIPANT_PACKS.md) |
| Future Rylee should not have to remember | [Documentation and Continuity](../../../contracts/engineering/DOCUMENTATION_AND_CONTINUITY.md), [Provenance and Audit](../../../contracts/core/PROVENANCE_AND_AUDIT.md), [Handoff](../../../contracts/agents/HANDOFF.md) |

No duplicate contracts are introduced by this document. Adding `docs/principles/trusted-translation.md` does not change the contract count (65), the lockfile, or any contract receipt.

---

## Related works and inspirations

These works are not authorities for Play-Nice and do not define its contracts. They are examples that illuminate related ideas about language, translation, preservation, mediation, difference, and trust.

For every entry:

```text
SOURCE FACT:
What the publisher / creator / official source actually establishes.

PLAY-NICE INTERPRETATION:
What this suggests as a useful lens for the philosophy above.

LIMIT OF THE ANALOGY:
Where the analogy stops being useful or stops being safe to push.
```

### 1 — *Star Trek: Discovery* — "An Obol for Charon"

```text
TITLE:           "An Obol for Charon"
CREATOR / WORK:  Star Trek: Discovery (Season 2, Episode 4; production number 204)
MEDIUM:          Television (science fiction)
OFFICIAL LINK:   https://www.startrek.com/news/your-obol-charon-primer
                 https://www.startrek.com/videos/episode-preview-an-obol-for-charon
                 (CBS Studios / StarTrek.com — primary)
SECONDARY:       https://memory-alpha.fandom.com/wiki/An_Obol_for_Charon_(episode)
                 (Memory Alpha — used only for detailed scene sequencing
                 and the "Saru is fluent in 94 languages" detail)
RELEVANT THEME:  Trusted translation; graceful degradation of a shared
                 abstraction; understanding before assuming hostility;
                 coordination earned by demonstrated trust.
HOW IT RELATES:  The opening metaphor of this document. Saru becomes
                 essential when the translation layer fails, not because
                 he merely knows many languages, but because the crew
                 trusts his interpretation.
LIMIT:           A 45-minute narrative episode is not an engineering
                 principle. The metaphor is useful for naming a mental
                 model; it is not a recipe for system design.
```

### 2 — Ursula K. Le Guin — *The Left Hand of Darkness*

```text
TITLE:           The Left Hand of Darkness
CREATOR / WORK:  Ursula K. Le Guin (1969)
MEDIUM:          Novel (science fiction)
OFFICIAL LINK:   https://www.penguinrandomhouse.com/books/538943/the-left-hand-of-darkness-by-ursula-k-le-guin/
                 (Penguin Random House — primary)
                 https://www.ursulakleguin.com/left-hand-darkness
                 (Author's official site — supplements)
RELEVANT THEME:  Understanding across profound cultural difference
                 without requiring the other culture to become like
                 your own.
HOW IT RELATES:  Interoperability requires humility about one's own
                 conceptual model. A local schema or culture is not
                 automatically the universal schema. Genly Ai is an
                 emissary entering a society whose assumptions differ
                 substantially from his own.
LIMIT:          This is a complex literary work about much more than
                 interoperability. It is not an engineering parable.
                 Reducing it to one would lose the rest of it.
```

### 3 — Ted Chiang — "Story of Your Life"

```text
TITLE:           "Story of Your Life" (short story)
CREATOR / WORK:  Ted Chiang (collected in Stories of Your Life and Others,
                 2002)
MEDIUM:          Short story (science fiction)
OFFICIAL LINK:   https://www.penguinrandomhouse.com/books/538163/stories-of-your-life-and-others-by-ted-chiang/
                 (Penguin Random House — primary)
RELEVANT THEME:  Learning another language may require learning another
                 way of representing reality, rather than merely
                 substituting vocabulary.
HOW IT RELATES:  Translation is about meaning, not field-name
                 substitution. Two systems may encode equivalent intent
                 using genuinely different conceptual models.
LIMIT:          Do not present the story as proposing an engineering
                 theory. The connection is interpretive, not authorial.
```

#### Optional film reference — *Arrival* (2016)

```text
TITLE:           Arrival (2016)
CREATOR / WORK:  Directed by Denis Villeneuve; screenplay by Eric Heisserer;
                 based on Ted Chiang's "Story of Your Life"
MEDIUM:          Film (science fiction)
OFFICIAL LINK:   https://www.paramountmovies.com/movies/arrival/
                 (Paramount Pictures — primary)
NOTE:            The film is an adaptation of the short story, not the
                 other way around. The literary source is "Story of
                 Your Life" (above). The film and the story are not
                 the same work; if you reference one, name which.
```

### 4 — China Miéville — *Embassytown*

```text
TITLE:           Embassytown
CREATOR / WORK:  China Miéville (2011)
MEDIUM:          Novel (science fiction)
OFFICIAL LINK:   https://www.penguinrandomhouse.com/books/206876/embassytown-by-china-mieville/
                 (Del Rey / Penguin Random House — primary)
RELEVANT THEME:  The Ariekei have a language with unusual requirements;
                 only specialized human ambassadors can speak it;
                 changes to that linguistic interface destabilize
                 relations.
HOW IT RELATES:  A translation layer can become critical infrastructure.
                 If interoperability depends on a specialized bridge,
                 its assumptions, failure modes, replacement path, and
                 authority boundaries all matter. An interface that
                 appears to be "just translation" may encode much
                 deeper semantics.
LIMIT:          Do not present the novel as advocating Play-Nice
                 architecture. It is a literary work about language,
                 identity, and trust.
```

### 5 — Samuel R. Delany — *Babel-17*

```text
TITLE:           Babel-17 (collected with Empire Star)
CREATOR / WORK:  Samuel R. Delany (1966; revised 1969; Vintage edition 2002)
MEDIUM:          Novel (science fiction)
OFFICIAL LINK:   https://www.penguinrandomhouse.com/books/38902/babel-17empire-star-by-samuel-r-delany/
                 (Vintage / Penguin Random House — primary)
RELEVANT THEME:  Language itself has profound consequences for
                 perception, reasoning, and behavior.
HOW IT RELATES:  A translator is powerful enough to distort intent.
                 Shared adapters and reconcilers should not silently
                 redefine the meaning they transport. Provenance and
                 inspection matter.
LIMIT:          Avoid claiming strong versions of linguistic
                 determinism as factual engineering principles. The
                 literary work is inspiration, not evidence for that
                 scientific claim.
```

### 6 — Walter M. Miller Jr. — *A Canticle for Leibowitz*

```text
TITLE:           A Canticle for Leibowitz
CREATOR / WORK:  Walter M. Miller Jr. (1959)
MEDIUM:          Novel (post-apocalyptic / science fiction)
OFFICIAL LINK:   https://www.penguinrandomhouse.com/books/114888/a-canticle-for-leibowitz-by-walter-m-miller-jr/
                 (Spectra / Penguin Random House — primary)
RELEVANT THEME:  Knowledge and artifacts are preserved across
                 generations even when the people preserving them do
                 not fully understand their original meaning.
HOW IT RELATES:  Future Rylee should not have to remember. Useful
                 state, decisions, provenance, artifacts, and history
                 must survive the participant who currently
                 understands them. This illuminates durable handoffs,
                 provenance, decision records, explicit current state,
                 and recoverability without transcript archaeology.
LIMIT:          The novel is broad and religious / philosophical. The
                 Play-Nice connection concerns preservation and
                 continuity specifically, not the novel's other
                 themes.
```

---

## Thematic map

| Work | Useful lens | Primary Play-Nice echo |
|---|---|---|
| *Star Trek: Discovery* — "An Obol for Charon" | Trusted translation; graceful failure of a shared abstraction | [Play Nice Together](../../../contracts/core/PLAY_NICE_TOGETHER.md), [Capability First](../../../contracts/interoperability/CAPABILITY_FIRST.md) |
| *The Left Hand of Darkness* (Le Guin) | Understanding without requiring sameness | [Capability First](../../../contracts/interoperability/CAPABILITY_FIRST.md), [Provider Neutrality](../../../contracts/interoperability/PROVIDER_NEUTRALITY.md) |
| "Story of Your Life" (Chiang) | Translation of meaning and conceptual models | [Stable Truth, Replaceable Machinery](../../../contracts/core/STABLE_TRUTH_REPLACEABLE_MACHINERY.md), [Friendly API Client](../../../contracts/interoperability/FRIENDLY_API_CLIENT.md) |
| *Embassytown* (Miéville) | Translation layers as critical infrastructure | [Recovery and Reversibility](../../../contracts/core/RECOVERY_AND_REVERSIBILITY.md), [External Mutations](../../../contracts/interoperability/EXTERNAL_MUTATIONS.md) |
| *Babel-17* (Delany) | Translation can alter or distort meaning | [Provenance and Audit](../../../contracts/core/PROVENANCE_AND_AUDIT.md), [Truth and Evidence](../../../contracts/core/TRUTH_AND_EVIDENCE.md) |
| *A Canticle for Leibowitz* (Miller) | Knowledge must survive the current knower | [Documentation and Continuity](../../../contracts/engineering/DOCUMENTATION_AND_CONTINUITY.md), [Handoff](../../../contracts/agents/HANDOFF.md) |

None of the authors or creators above endorse Play-Nice. Their works appear here because they illuminate ideas that the Play-Nice contracts already capture in normative form.

---

## Core principles (one page)

> **CORE MODEL ENDS HERE · RELATED WORKS / OPTIONAL READING BELOW**

> **Different languages. Different systems. Shared understanding. Earned trust.**

> **Translation should preserve meaning, not erase difference.**

> **A participant is not trusted because it sits in the middle. It is allowed to sit in the middle because it has earned trust.**

> **Understanding is not ownership. Interpretation is not authorization. Coordination is not control.**

> **Everything should play nicely with everything else — not because everything is the same, but because they understand how to work together.**

> **Future Rylee should not have to remember what the previous translator knew. The meaning, provenance, and path to recovery should survive them.**

---

## Sources and further reading

### Primary, official

- [StarTrek.com — Your "An Obol for Charon" Primer](https://www.startrek.com/news/your-obol-charon-primer) (CBS Studios / Paramount; primary)
- [StarTrek.com — Episode Preview: "An Obol for Charon"](https://www.startrek.com/videos/episode-preview-an-obol-for-charon) (CBS Studios / Paramount; primary)
- [Penguin Random House — *The Left Hand of Darkness*](https://www.penguinrandomhouse.com/books/538943/the-left-hand-of-darkness-by-ursula-k-le-guin/) (publisher; primary)
- [Ursula K. Le Guin — official site, *The Left Hand of Darkness* page](https://www.ursulakleguin.com/left-hand-darkness) (creator; supplements publisher)
- [Penguin Random House — *Stories of Your Life and Others*](https://www.penguinrandomhouse.com/books/538163/stories-of-your-life-and-others-by-ted-chiang/) (publisher; primary)
- [Penguin Random House / Del Rey — *Embassytown*](https://www.penguinrandomhouse.com/books/206876/embassytown-by-china-mieville/) (publisher; primary)
- [Penguin Random House / Vintage — *Babel-17 / Empire Star*](https://www.penguinrandomhouse.com/books/38902/babel-17empire-star-by-samuel-r-delany/) (publisher; primary)
- [Penguin Random House / Spectra — *A Canticle for Leibowitz*](https://www.penguinrandomhouse.com/books/114888/a-canticle-for-leibowitz-by-walter-m-miller-jr/) (publisher; primary)
- [Paramount Pictures — *Arrival*](https://www.paramountmovies.com/movies/arrival/) (studio; primary, for the film adaptation only)

### Secondary

- [Memory Alpha — "An Obol for Charon" (episode)](https://memory-alpha.fandom.com/wiki/An_Obol_for_Charon_(episode)) — used only for the scene-sequencing details and the "Saru is fluent in 94 languages" line, neither of which is in the official StarTrek.com primer.

### Play-Nice (canonical)

- [`CONTRACT_INDEX.md`](../../../CONTRACT_INDEX.md) — the registry of every canonical contract.
- [`contracts/`](../../../contracts/) — the contracts themselves, in their layer directories.
- [`README.md`](../../../README.md) — orientation, layering, and how to adopt the library.

---

## Attribution and copyright

- Every external work is named with its creator / author, work title, medium, and an official publisher / studio / creator link when one exists.
- Brief paraphrase is used throughout; quotations, where unavoidable, are short and attributed. No long copyrighted excerpts are reproduced.
- Every `HOW IT RELATES` entry is labeled as Play-Nice interpretation, not as the source's claim or intent.
- Memory Alpha is used only for facts absent from the official StarTrek.com material (specifically: detailed scene sequencing and the "94 languages" line); its role as a secondary source is acknowledged above.
- Adding this document does not change Play-Nice's license. Play-Nice remains MIT ([`LICENSE`](../../../LICENSE)). The external works referenced above remain the property of their respective creators and publishers; no rights are claimed over them by this repository.
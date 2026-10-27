# Play Nice, Opus

> **Status:** Optional reading · the long-form "why" behind Play-Nice. Not needed to use it: the rules are in [the floor](../../contracts/everyone/FLOOR.md) and the packs.

> **Everything should play nicely with everything else.**
>
> **A protocol for cooperation among participants that are different,
> fallible, partially known, and independently owned.**

A long-form companion to the Play-Nice contracts. This document tries to say,
in the plainest words available, what the contracts are actually for and why
they are shaped the way they are. It is meant to be read slowly, the way you
read a friend's letter rather than a work email.

---

## Status

```text
PHILOSOPHY / EXPLANATION
NON-NORMATIVE
```

This document explains the intent behind Play-Nice. The canonical contracts
define the actual requirements.

It creates **no new requirements**. It adds **no contract**, changes no
version, no lockfile, no receipt, and no contract count. Where anything in
this document appears to conflict with a canonical contract, the contract
wins — the contracts in [`contracts/`](../../contracts/) and the registry in
[`CONTRACT_INDEX.md`](../../CONTRACT_INDEX.md) are authoritative. This document
is interpretation, orientation, and heart.

That arrangement matters. Play-Nice keeps its promises in the contracts so
that the poetry never has to. Any philosophy whose only binding is its own
eloquence is just a mood; a binding that is written down, tested, pinned,
and attested is a place people can actually live.

---

## Contents

1. [Why This Exists](#1-why-this-exists)
2. [Different Is Normal](#2-different-is-normal)
3. [No Participant Is the World](#3-no-participant-is-the-world)
4. [Evidence Before Reputation](#4-evidence-before-reputation)
5. [Unknown Is Allowed](#5-unknown-is-allowed)
6. [Failure Is Information](#6-failure-is-information)
7. [The Judge Is Also Fallible](#7-the-judge-is-also-fallible)
8. [Trusted Translation](#8-trusted-translation)
9. [Consent and Consequence](#9-consent-and-consequence)
10. [Provenance](#10-provenance)
11. [Capability Profiles](#11-capability-profiles)
12. [Trust Is Dynamic](#12-trust-is-dynamic)
13. [Worlds and Brains](#13-worlds-and-brains)
14. [Let the World Meet the Person Halfway](#14-let-the-world-meet-the-person-halfway)
15. [Small Model Olympics](#15-small-model-olympics) *(a case study in evidence)*
16. [Engineering Consequences](#16-engineering-consequences)
17. [Human Consequences](#17-human-consequences)
18. [What Play Nice Is Not](#18-what-play-nice-is-not)
19. [A Small Set of Promises](#19-a-small-set-of-promises)

Then: [How this reads against the contracts](#how-this-reads-against-the-contracts) and
[Sources](#sources).

---

## 1. Why This Exists

Play-Nice is a shared constitution for how humans, bots, software, services,
APIs, CLIs, UIs, designs, automations, repositories, and future tools interact
with one another. That long list is the point: no category in it is allowed
to be a second-class cousin.

One sentence holds it together:

> **Everything should play nicely with everything else.**

And one design value gives that sentence its shape:

> **Interoperability without forced sameness.**

The central thesis of this document — and, this document argues, of the whole
project — can be said in a breath:

> **Play Nice is a protocol for cooperation among participants that are
> different, fallible, partially known, and independently owned.**

Every word there is load-bearing.

- **Different.** Participants are allowed to remain themselves. VEFR stays
  VEFR. Project worlds stays project worlds. A provider keeps its own API.
  A project keeps its own domain rules. Difference is the default state of
  the universe; the shared layer must accommodate it without dissolving it.

- **Fallible.** Participants fail. Humans get tired, distracted, and
  interrupted. Models hallucinate and truncate. Services time out and break.
  Harnesses misinterpret their own prompts. Running is not working, and a
  system that assumes otherwise is designing for its own emergency.

- **Partially known.** No participant fully knows another, and no participant
  fully knows itself. Capability observed yesterday may not hold today, and
  the honest word for that is `UNKNOWN` — a word this project has promoted
  from a confession to a data type.

- **Independently owned.** No participant owns another. The person owns their
  data, their truth, and their decisions. A tool may hold state but never
  exclusively; a coordinator may carry the work without claiming the truth. A
  participant must be able to leave — with everything intact — because a
  protocol whose exits are sealed is not cooperation, it is a trap.

The library exists for a practical reason as well as a philosophical one.
Rylee keeps learning the same lessons and refuses to lose them:
> This library preserves the lessons that keep being relearned, so that
> neither Rylee nor anyone else has to remember and restate them every time.

Personal World taught the accessibility and attention lessons. VEFR taught
the replaceable-brain lessons. The homelab taught the recovery lessons —
hard-won, burned once. This is the place those lessons come to rest, in a
form a human can read and an agent can execute.

Where this lives in the contracts: the constitution itself is
[Play Nice Together](../../contracts/everyone/WORKING_TOGETHER.md). The four
qualities are worked out by every other contract in the library.

---

## 2. Different Is Normal

There is a particular experience some people get to have, and others only
hear about: walking into a world and finding that its rules were written for
you. Most rooms, most forms, most software, most workplaces assume a default
person — the crowd, the standard body, the obvious gender, the energy level,
the eyesight, the memory.

If you were never the default, you have a choice of jobs: either spend your
life adapting, or notice that the defaults are not laws. They are choices
someone made, usually without being asked to.

Rylee is a trans woman. That is a fact of origin, not a plot point — this
document is not an autobiography, and it will not manufacture one. But it is
worth naming the inheritance it left: the lived lesson that **"different" is
a state you can be born into without ever having done anything to deserve
it, and that the world will nonetheless treat it as a defect to be corrected.

The deep premise of Play-Nice is the refusal of that correction:

> **Different does not mean defective.**

A participant that is not like the others is not a bug in the system. The
system *is* the many participants. A lone flower species is not an error
in the meadow; a meadow of nothing but one species is a lawn.

This is why the contracts so consistently decline to make anything "the one
true form":

- No universal application. No universal schema. No universal agent.
- VEFR may differ from Project Worlds; both may differ from the homelab.
- A tiny local model, a deterministic script, and a frontier model are all
  participants with different shapes — none of them is the shape.

And this is why accessibility is a floor and not a kindness. A world built
for one kind of person is a building with one doorway; "play nicely" means
the hallway is wide enough for everyone who might need to be inside,
including people whose needs the architect never imagined.

The design value can be written as a quiet motto:

> **Understand each other well enough to work together — without
> becoming each other.**

Where this lives in the contracts: the layering model in the
[README](../../README.md) treats Rylee's preferred experience as one first-class
[profile](../../examples/profiles/), never a hidden global requirement; the
[Accessibility Floor](../../contracts/people/ACCESSIBILITY.md) makes
"architecturally accessible" a default, not a mode; and
[Participation and Contribution](../../contracts/everyone/WORKING_TOGETHER.md)
insists importance is not size, cost, or prestige.

---

## 3. No Participant Is the World

The worst thing a system can do is quietly become identical with one of its
tools. Play-Nice calls the forbidden shape:

```text
VENDOR PRODUCT → VENDOR API SHAPE → OUR ENTIRE ARCHITECTURE
```

and the nightmare it tries to prevent is specific and familiar:
`source_control == Gitea`, such that removing Gitea removes the *concept* of
source control from the world entirely.

The rule that prevents this is [Capability First](../../contracts/integration/CAPABILITIES_NOT_VENDORS.md):
intent maps to a capability the system owns; a provider is an optional
implementation of it.

> A capability belongs to the system. A provider implements or enriches it.
> The provider does not define it.

There is a personal version of this law, and it runs through every project
in this ecosystem:

- **VEFR** brings its own brain. The world (the story, the map, the rules)
  is authoritative; the brain that narrates and reasons about it is
  replaceable machinery. Swap `Qwen` for `Granite` for a remote specialist and
  the world does not notice — changing a part, not surgery.

- **Project Worlds** is a world that comes to the person. It is provider-rich
  and design-heavy, but the person's world is the concept that persists; any
  single assistant, model, or tool is an enrichment of it, never its owner.

- **The homelab** treats every service as a replaceable component and every
  truth as recoverable. Services are providers of their capabilities; the
  house itself is the concept that must survive them.

And in the Small Model Olympics (Section 15), the same law shows up in the
most unexpected place: **the judge is also not the world.** The harness that
measures models is a participant, not an oracle. When it was wrong, the
fix was to repair the harness — not to ask the models to be longer.

The antidote to "one thing is everything" is always the same trio, repeated
until it is boring:

> Understand is not ownership.
> Interpretation is not authorization.
> Coordination is not control.

Just because a participant understands a system does not mean it owns it.
Just because it can explain a system does not mean it may act on it. Just
because it sits in the middle does not make it the system.

Where this lives in the contracts: [Capability First](../../contracts/integration/CAPABILITIES_NOT_VENDORS.md),
[Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md),
[Provider Neutrality](../../contracts/integration/CAPABILITIES_NOT_VENDORS.md).

---

## 4. Evidence Before Reputation

> A claim about a system's state is worth exactly the evidence behind it.

With models this is easy to say and hard to mean. A model's reputation has
many fonts: its parameter count, its price, its benchmark score, the name of
its maker, the size of its advertisement. Every one of these is what Play-Nice
calls *reputation*. None of them is *evidence*.

Evidence is:

- the command you actually ran,
- the artifact that actually came back,
- the state that was actually observed, at a timestamp, from a named source,
- and the conditions under which it all happened.

[Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md) encodes the
contract's version of this with memorable terseness:

> Running is not working. Implemented is not verified. HTTP 200 is not proof
> of correctness. A process being up is not evidence it does its job.

> An agent report is evidence about what an agent *said*, not proof of what
> *happened*.

> Current evidence outranks historical reports, summaries, and remembered
> conclusions.

> A check that has not run in the current context is `UNKNOWN`, regardless of
> how green it was last time.

The first lesson the Small Model Olympics produced, in fact, was just this
contract wearing exercise gear: **capability is earned by evidence.** A model
that scored 100% on one run of one round is a model that scored 100% on one
run of one round — not a model that is always right, and not a model that is
"the best." Its standing is a fact about a measurement, and the measurement
is only as trustworthy as its description.

The Olympics' honesty notes are the same discipline applied to history:
- phi-4-mini's `34/53 (64%)` qualifier result is **not** its historical
  `100/100` from a different, production-path set. Both facts are reported,
  separately, neither folded into the other.
- qwen3.5-0.8b's `30%` is **not** its historical `80.3` on an artifact that
  no longer exists.
- The backend evidence for a dozen legacy runs is simply **UNKNOWN** — no
  CPU-vs-GPU claim is made for them at all.

That restraint is not pedantry. It is the difference between a scoreboard and
a lie.

The profiles in this library practice the same distinction. A participant
profile separates **OBSERVED** (what we watched it do), **SELF-REPORTED**
(what it says about itself, marked as belief until validated), and
**UNKNOWN** (everything else). A model that says "I frequently hallucinate"
while behaving well on bounded tests produces a record that preserves both
facts — without resolving a tension that the evidence has not yet resolved.

Where this lives in the contracts: [Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md),
[Testing and Verification](../../contracts/work/TESTING_AND_EVIDENCE.md),
[Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md).

---

## 5. Unknown Is Allowed

Most software is ashamed of ignorance. A system that does not know something
is usually expected to *do something*: guess, assume, fill in, keep going.
Play-Nice considers that an act of vandalism dressed up as progress.

> `UNKNOWN` is a valid state.

It is not a failure state. It is not a placeholder we promise to upgrade.
It is a first-class, permanently legal inhabitant of every status
vocabulary in the system:

> Never silently convert `UNKNOWN` into `healthy`, `PASS`, or `complete`.
> **Failure to prove something is not evidence of its opposite.**

Three commonsense consequences follow:

1. **Nothing green until it's checked.** If nothing has been verified in the
   current context, the truthful state is `unknown` — with an `observed_at`
   and a `source`, so the reader can see how unknown, and since when.

2. **History is not a witness.** A check that ran yesterday and passed does
   not authorize today's `healthy`. Familiarity breeds `stale`, not `fresh`.

3. **"I don't know" is a beginning, not an ending.** [Ask for Help](../../contracts/everyone/ASK_FOR_HELP.md)
   turns `UNKNOWN` into the first step of a ladder:

   ```text
   KNOW                        → act
   CAN SAFELY DISCOVER         → discover
   ANOTHER PARTICIPANT CAN
   ANSWER CHEAPLY              → ask
   HIGH-COST / HIGH-RISK /
   AMBIGUOUS                   → ask or escalate
   UNKNOWN AND NOBODY CAN
   ANSWER                      → preserve UNKNOWN
   ```

   And `WAITING_FOR_HELP` is a **successful** stop state: a task may
   legitimately end when further action would require guessing, the right
   participant has been asked, and the current state is safely preserved.

The Olympics spent real trust on this principle. The backend of twelve
legacy runs is *unknown*, and the report leaves it unknown — it does not
inherit a friendlier memory, does not re-prove what has no evidence, and
does not quietly downgrade the label. An unknown is cheaper and more
valuable than a comfortable guess, because the unknown can be fixed and the
guess cannot.

And there is a human version that the whole library bends toward: a culture
that mocks "I don't know" makes participants hide it. A participant hiding
uncertainty is a participant whose errors are invisible until they are
disasters. So the canonical response to honest uncertainty is:

> "Thanks — who or what is most likely to know?"

Where this lives in the contracts: [Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md),
[Explicit State](../../contracts/everyone/STATUS_AND_STATE.md),
[Ask for Help](../../contracts/everyone/ASK_FOR_HELP.md).

---

## 6. Failure Is Information

Here is a small model that failed its whole campaign. Its real story is
that it never got a fair trial — but you would not know that from the score.

Here is a second small model that also "failed". Its failure left a record
with evidence: it burned its token budget reasoning beautifully and then
emitted nothing at all into the judged field. It produced a lot of thinking
and no deliverable. That is a real, distinguishable thing.

And here is a third model that "failed" because the harness sent its
conversation a second system message and the server refused the whole
request with an HTTP error. The model never even got to answer.

The first lesson of failure is attribution. **What failed?**

[Failure and Degradation](../../contracts/everyone/STATUS_AND_STATE.md)
demands that an error answer six questions — what failed, why, what still
works, is anything unsafe, can it be retried, what next. This document
points the same discipline at the movement of blame — six targets worth
distinguishing:

- **Participant failure** — the model or tool genuinely could not do the task.
- **Protocol / normalization failure** — the output was right but wrapped in
  markdown fences, or emitted into the wrong channel.
- **Harness failure** — the suite, template, or tooling mangled the
  interaction. *(This one is the funny one, because the harness is us.)*
- **Environment failure** — contention, a missing dependency, a hung GPU,
  a starved context.
- **Vehicle / transport failure** — the plumbing between participants dropped
  the message.
- **Authority / policy rejection** — the action was refused for good reasons.

The Olympics is a small monument to this distinction. Every stuck run of the
pre-0.4.1 suite turned out to be a harness defect, not a model fault:

- **gemma3-1b** was aborted by `HTTP 400` — the GGUF template rejects
  consecutive assistant turns and mid-session system messages; the harness
  was manufacturing transcripts the server could not legally receive.
- **the qwen3.5 family** was aborted by `HTTP 500` on *any* non-first system
  message. Again, the harness's transcript.
- **granite-4.2-3b** was a thinking model: it answered into `reasoning_content`
  and returned empty `content`, and the old harness dropped the reasoning and
  judged the emptiness as if it were the whole model.

Three "model failures." Zero of them were the models. That is why the suite's
own changelog for 0.4.1 says: *no task prompts, no judges — harness,
records, and runtime only.* The contestants were never the ones who needed
reform.

Winner of the failure-attribution game: **A culture that punishes failure
learns nothing from it.** [Recovery and Reversibility](../../contracts/everyone/RECOVERY_AND_HISTORY.md)
says mistakes are evidence — record them, build the guardrail, don't shame
the person. [Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md)
says it plainer: failure is not a moral judgment. The attempt may have been
badly shaped, the context missing, the assumptions wrong, the dependency
changed, the capability insufficient — or someone made a mistake. Treat
failure as evidence first, and only then, gently, as anything else.

Where this lives in the contracts: [Failure and Degradation](../../contracts/everyone/STATUS_AND_STATE.md),
[Recovery and Reversibility](../../contracts/everyone/RECOVERY_AND_HISTORY.md),
[Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md).

---

## 7. The Judge Is Also Fallible

There is an old habit of treating the people who grade us as if they were
not people too. Play-Nice extends the corrective to machines: **the judge is
also a participant.**

An evaluator — a foreman, a harness, a test suite, a reviewer, a benchmark —
has the same properties as everyone else in this protocol. It is observable.
It is testable. It carries provenance. It can be corrected. And correction is
not an embarrassment; it is the whole reason it can be trusted at all.

Several ordinary facts of the Olympics make this concrete:

- The 0.4.x suite's *headers* once hard-coded `backend: vulkan` with no
  runtime evidence. That was a judge asserting a fact from memory. The 0.4.1
  suite probes the running container for the render node, reads VRAM, and
  records GPU busy — the judge now *observes* what it once *assumed*.

- The suite version itself was bumped (0.4.0 → 0.4.1) and each fix recorded
  in its own changelog. A judge that changes its own rules must say so,
  in public, in version numbers.

- Every sanitizer transform was recorded per trial. When the harness merged
  consecutive assistant turns or hoisted a system message, it wrote down that
  it had done so — a judge that alters the transcript and then hides the
  alteration is forging the evidence; a judge that writes it down is just a
  careful editor.

- The judges were themselves *re-run against the exact tasks they had
  corrupted*: gemma3-1b's blocked `assist.longrun1` completed on the fixed
  suite (3/3 turns), qwen3.5-0.8b's blocked `flex.switch1` completed (5/5
  turns), and granite-4.2-3b's `tj4` completed — zero aborts, transforms
  recorded, backends observed. That is verification applied to the verifier.

The structural rule behind all of this is the old foreman's law:
**worker-green is not integration-green.** A report from a participant is
evidence about the participant, not proof for whatever the participant
claims. Integration and combined-state verification are the foreman's own
job. The same applies upward: the *suite's* report is evidence about the
suite, and the campaign had better be checking the suite too — which, on a
good day, is why it catches its own bugs.

And the parallel human rule: confidence is not correctness. "Obviously",
"everyone knows", "any competent engineer would" — these contribute no
evidence, and the reason they tempt us is exactly that they feel like
verdicts. They are not. The heart of it is simple: **say what you know, and
when you are the string the measures are attached to, make sure you can be
measured too.**

Where this lives in the contracts: [Orchestration](../../contracts/work/ORCHESTRATION.md)
(a foreman does not blindly trust workers), [Review and Integration](../../contracts/work/BOUNDED_WORK.md),
[Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md)
(no dominance phrases as evidence), [Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md).

---

## 8. Trusted Translation

Play-Nice's flagship philosophy document takes its metaphor from *Star Trek:
Discovery*, where a virus destroys the ship's universal translator and the
crew is suddenly deaf to each other's languages. Into the chaos steps Saru —
not because he merely speaks 94 languages, but because the people around him
trust him to translate faithfully: to preserve meaning, to identify what is
observation and what is inference, and to ask for help when the right
translation is not yet safe to make.

The metaphor's core is worth repeating exactly:

> **A participant that helps other participants understand each other is
> allowed to do so because it has earned trust through behavior, not
> because it occupies a central position.**

and its three sentences:

> Shared abstractions should make cooperation easy, but they should never
> erase the underlying systems' ability to be understood on their own terms.

> Translation is not the same as authorization. Understanding is not
> ownership. Coordination is not control.

A trusted translator:

- preserves meaning,
- identifies the source,
- preserves provenance,
- distinguishes observation from inference,
- admits uncertainty and says `UNKNOWN` when appropriate,
- asks for help when the translation cannot be made safely,
- respects the authority of the systems it translates,
- and leaves evidence so someone else can verify what happened.

There is a sharper way to say what the Olympics taught about this — and it
is the eighth lesson, so it earns the slow moment here.

> **Translation is a trust boundary.**

A layer that carries meaning between participants either preserves the
epistemic state of what it carries, or it betrays it. It must never quietly
turn:

```text
UNKNOWN   → TRUE
FAILED    → INCAPABLE
PROPOSED  → AUTHORITATIVE
INFERRED  → OBSERVED
```

The 0.4.0 harness did exactly one of these, a small one and a sneaky one.
For thinking models like granite-4.2-3b and the qwen3.5 family, the real
output lived in `reasoning_content`, while `content` came back empty. The
harness dropped the reasoning and judged only the empty `content`, splicing
"[TRUNCATED]" into the surviving text. A model that had been thinking hard
was recorded as a model that had said nothing — `INFERRED` was rendered as
`OBSERVED`, and a `PROPOSED` (the reasoning) was erased.

The 0.4.1 fix is the translation-faithful one: capture `content` and
`reasoning` and `finish_reason` and `truncated` separately, stop splicing
markers into the text, and let the record say the whole truth:

> "A model that reasons but never emits is recorded as a failure **with
> evidence**"

Not as a failure with a guess. The translator now preserves meaning instead
of manufacturing a verdict.

There is a homely, hopeful companion fact to this: the translator layer is
a *convenience, not a load-bearing wall*. If the reconciler disappears, the
tools still work in their own syntaxes; cooperation becomes more manual, but
it does not become impossible. That is the test of a translation layer that
respects its underlying systems — and of a person, too.

Where this lives: [Trusted Translation](principles/trusted-translation.md)
(the philosophy in full), [Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md),
[Friendly API Client](../../contracts/integration/CALLING_OTHER_SERVICES.md),
[Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md).

---

## 9. Consent and Consequence

Play-Nice keeps five words in a strict row, and their order is the whole
moral of the story:

```text
capability    participation    agreement    authorization    acceptance
```

Being able to do a thing confers no right to do it. Agreeing to help with a
thing does not authorize doing it. Authorization grants nothing beyond its
own scope. And even an authorized action is not *accepted* until a
consequential decision has been faced by the right owner — which is usually
the human.

This is the consent machinery of the protocol, and it has rules worth
stating plainly:

- **Asking is not permission.** A help response provides information. "The
  cluster is `prod-west`" does not grant a license to delete `prod-west`.
  [Ask for Help](../../contracts/everyone/ASK_FOR_HELP.md) states it flatly:
  questions are never authorization.

- **Remembering is not erasing.** A remembered preference persists a
  boundary; it never silently removes the approval gate for a severe action.
  Step-up verification gates sensitive operations no matter how often you
  have clicked "remember this." Consent given once is a habit, not a deed.

- **No is a complete sentence, on every side.** `DECLINE` is not
  disobedience. `MODIFY` is not failure. A participant that says "I cannot
  do that safely, but I can do this adjacent part" is behaving *well*. And a
  human may say: *not this way, not this much, not right now, show me less,
  give me the recommendation, let me decide this part* — and the system
  adapts. That is normal operation, not an exception.

- **People get one clear decision at a time.** Interruption is budgeted and
  batched, but never rat-holed: you will not be asked to approve a
  production deletion and a font choice in the same breath, and the
  questions you are asked are the ones only you can answer.

- **Boundaries are kind and firm.** Good faith does not mean endless
  tolerance. The protocol protects the right to disengage — while preserving
  the technical state for whoever continues. Kindness is not surrender.

Then there is the deeper layer: **consent to the experience itself.** Before
any of this can matter, the person must not be *hurt by the system*. That is
why [Accessibility Floor](../../contracts/people/ACCESSIBILITY.md) and its
siblings in `contracts/human/` are also consent machinery:

- no strobing, motion reduced by default, `prefers-reduced-motion` honored
  unconditionally,
- 200% zoom without clipped content,
- status spoken, not just colored,
- focus that you can see and always find.

These are not "nice-to-haves for disabled users." They are the term of
*entry*: the preconditions under which a person can be present in the room
at all, with their attention theirs to give. The system asks consent; the
system respects the answer; the system is designed so that a "no" costs the
person nothing.

Where this lives in the contracts: [Authorization](../../contracts/access/IDENTITY_AND_ROLES.md),
[Mutual Contribution by Agreement](../../contracts/everyone/WORKING_TOGETHER.md),
[Ask for Help](../../contracts/everyone/ASK_FOR_HELP.md),
[Accessibility Floor](../../contracts/people/ACCESSIBILITY.md),
[Migraine and Sensory Safety](../../contracts/people/SENSORY_SAFETY.md).

---

## 10. Provenance

The most expensive recurring question in a system you care about is
**"Why is this like this?"** — and in a system where the question cannot be
answered, it becomes archaeology. You find yourself scraping transcripts for
the ghost of a decision nobody wrote down.

[Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md) converts
archaeology into a lookup:

> Consequential changes record: actor (human, agent, service, automation),
> timestamp, reason or intent, and the change itself.

Its companion rules are quiet and important:

- **Generated content is labeled as generated** — provider, model or tool,
  and source material. Nothing crafted by a machine passes itself off as
  the author's own thought.

- **AI output that becomes durable truth is committed to canonical storage
  with provenance** — never left living only inside a conversation, model,
  or session. (That is [Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md)
  with the mask off.)

- **Corrections supersede; they do not rewrite.** History stays append-only.
  Being able to see that a record was amended is what makes the current
  record believable.

- **Previous state remains recoverable** — through history, journal, or
  version control. The old value is not deleted; it is stood behind the new
  one.

- **Secrets never ride along.** Sensitive values are excluded structurally —
  references are symbolic — so that provenance works for the next maintainer
  without becoming a liability.

The Olympics exercises this in small, mundane ways that add up to one
long trust: every trial records its transforms (`merged_assistant`,
`hoisted_system`), its reasoning and finish reasons, and its backend probe.
Even the sanitizer that fixes a broken transcript leaves a note that it
fixed it. A reader can tell *which* of the suite's behavior was altered,
*when* it was observed, *under what contention*, by *which generation
mechanism*. The answer to "why is this model's number this number?" is not a
vague memory; it is a path.

And ideas — not just data — get provenance. Play-Nice is allergic to the
sentence "I invented this." The healthy alternative is a small attribution
that is easy and ordinary:

```text
visual concept: Figma
implementation interpretation: Claude
mechanical guard: GLM
accepted by: Rylee
```

Credit is proportional. Nobody needs a seventeen-author manifesto for a
button label; but a design worth keeping should be able to tell its story
in one line. *I did it* is a species of hidden plumbing; *we did it, here is
how the pieces met* is a place where the next participant can stand.

Where this lives: [Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md),
[Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md),
[Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md).

---

## 11. Capability Profiles

A participant profile in Play-Nice is a description of what a participant
has *been observed to do*, under what conditions, on what date — not a
verdict on what it *is*.

The [Hermes profile](../../examples/profiles/) opens with the sentence that should hang
above every profile ever written:

> The brain is runtime state, not permanent identity. The currently selected
> model does not inherit permanent capability claims from previous sessions.

and its body marks every single claim:

- **OBSERVED** — what we watched it do, with the artifacts.
- **GOOD WITH VERIFICATION** — tasks where a deterministic check exists.
- **POOR FIT / ROUTE ELSEWHERE FIRST** — places with *no* evidence of
  strength; listed as routing guidance, not as a prison sentence.
- **SELF-REPORTED / NOT YET VALIDATED** — its beliefs about itself, kept
  separate, kept honest.
- **KNOWN FAILURE MODES** — with mitigations, because a profile that hides
  its subject's failure modes is not a profile, it is propaganda.

The [Granite 4.1 3B profile](../../examples/profiles/granite-4.1-3b.md) demonstrates the
pattern at its most useful: it says the model is excellent at bounded
structured tasks, *stable* at preserving UNKNOWN, and **unpredictable at the
one judgment that is load-bearing** — deciding whether a genuinely ambiguous
case should be handled locally or escalated. 33% on three repetitions. The
profile's instruction, accordingly, is *always verify this class*.

Two things make this extremely Play-Nice:

1. **[Participation and Contribution](../../contracts/everyone/WORKING_TOGETHER.md):**
   importance is not size, cost, intelligence, prestige, or autonomy. A
   0.8B model given "500 lines against 12 known categories, escalate the
   UNKNOWN cases" can be a better contributor than a frontier model given
   the same prompt and an excess of ambition. Small capability is not no
   capability; the smallest suitable participant is a destination, not a
   consolation prize.

2. **Observed capability is versioned and non-eternal.** Today: local-model →
   classification. Tomorrow, after an update: local-model → classification
   *and* summarization. Profiles are dates and observations, not candles lit
   once and never relit. The anti-pattern this guards against is the one
   that rots every "most capable model" ranking: model folklore hardening
   into an eternal caste.

This is lesson six of the Olympics: **participants get profiles, not
reputations.** A reputation is a verdict that follows you. A profile is a
date-stamped measurement you or anyone else can refresh. The ecosystem
wants the second one. The difference matters for models, and it matters for
people — though people's profiles should be thin, respectful, and short,
because no human should be reduced to an entry in their own file.

Where this lives: [Participation and Contribution](../../contracts/everyone/WORKING_TOGETHER.md),
[Project Context and Participant Packs](../../contracts/everyone/PROJECT_CONTEXT.md),
[Model Routing](../../contracts/work/AGENT_BEHAVIOR.md), and the profiles
themselves under [`examples/profiles/`](../../examples/profiles/).

---

## 12. Trust Is Dynamic

The word "trust" in Play-Nice is a verb more than a noun. It is something
you do in a particular direction, on the basis of particular evidence, for a
particular scope, for now.

The canonical statement is from [Trusted Translation](principles/trusted-translation.md):

> **Trust is earned, not positional.**

So a coordinator is *not* trusted because it sits in the middle. It is
allowed to sit in the middle because it has *earned trust through behavior*.
It earns the seat the same way Saru did: by translating faithfully,
preserving uncertainty, respecting authority, and leaving evidence.

It is also, and this is the part that is easy to let slip: **revocable.**

Trust in this ecosystem has the flavor of a well-maintained instrument:

- It is **scoped.** You trust the local classifier with *classification*,
  not with root-cause decisions. The profile says exactly where the trust
  stops.

- It is **earned from behavior and evidence**, refreshed by
  re-observation — because "canonical state can change during a session."
  Timestamps and re-observation are the protocol's way of saying: *the world
  may have moved since we last agreed; let me look again before I speak.*

- It is **dynamic.** When a participant's self-report contradicts its
  observed behavior, the record preserves both, without rushing to resolve
  a tension that does not have evidence behind it yet. When behavior
  changes, the trust changes with it. When a model gets a new version, last
  week's profile is dated, not divine.

- It is **not transferable, and not permanent.** A participant's standing is
  described by a profile, not by a reputation; and reputation, like a
  permissions grant, is *exactly the permissions the bounded job needs —
  revocable* (see [Least Privilege](../../contracts/access/IDENTITY_AND_ROLES.md)).

- It is **earned again, quietly, every session.** The price of being
  trusted is that your past evidence stays your past evidence, and your
  current evidence has to show up. `observed_at` is an oath.

The eighth olympics lesson and this one are the same weather: capability
earned by evidence; trust earned and revocable. The reason they rhyme is that
they are the same sentence in two dialects. **Nothing in this ecosystem is
allowed to coast on who it used to be.**

There is a human echo worth hearing. If the system you live in treats your
trust as permanent, it is taking you for granted; if it treats it as
positional, it is flattering you into forgetting the door is unlocked. The
Play-Nice answer is neither. It is the boring, beautiful middle:

> I will show you my evidence, and I will keep showing it. When it stops
> matching, you are allowed — you are *obliged* — to stop trusting me.

Where this lives: [Trusted Translation](principles/trusted-translation.md),
[Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md),
[Authorization](../../contracts/access/IDENTITY_AND_ROLES.md),
[Least Privilege](../../contracts/access/IDENTITY_AND_ROLES.md).

---

## 13. Worlds and Brains

This ecosystem runs on a clean division of labor between the world and the
brain that lives in it — and the division is the point, not an accident.

**VEFR** ("bring your own brain") is explicit about it, in two directions
at once:

- **The world is authoritative.** The map, the story, the rules of the
  playable world are the canonical truth; the model that narrates and fills
  the world is a guest in it.
- **The brain is replaceable.** `Qwen → Granite → larger model → remote
  specialist` changes the *machinery*, and the world does not flinch. VEFR
  keeps deterministic surfaces deterministic — world validation, map
  transforms, exports — while models operate at explicit, named generative
  edges. Deterministic bones, stochastic edges; the runes are the only
  stochastic surface, on purpose.

Hermod — VEFR's resident executive assistant / thought-offloader — is a
practice run of a role Play-Nice has since named generically:

> **A Trusted Steward carries continuity without claiming ownership.**
> *(Hermod is one implementation. The role is generic; the implementation is
> not.)*

The steward's identity, role boundaries, history, capability boundaries, and
authority boundaries all survive a brain swap, because none of them is the
brain. The model is runtime state. The role is a shape.

**Project Worlds** starts from the other end and meets in the middle: a
world that is built *for a person*, that comes to the person, and that is
obliged to adapt — provider-rich, design-heavy, but with the *person's
world* as the concept that outlives any single assistant or tool.

**The homelab** contributes the load-bearing discipline that keeps all of
this repairable: recoverability as religion. `PROVE STALE → CLEAN` — never
`LOOKS STALE → DELETE`. Preview, rollback, tested restoration, saved
processes. Quiet monitoring. The infrastructure of trust is supposed to be
boring; the boring bits are the load-bearing bits.

Three projects, one shared floor. The contracts are adopted, never forked;
what is universal lives here in this library, what is local stays local.
That is why the README's layering diagram is a stack that ends in the same
place every time:

```text
UNIVERSAL SAFETY / INTEROPERABILITY FLOOR      (contracts/core)
        ↓
HUMAN EXPERIENCE / ACCESSIBILITY FLOOR         (contracts/human)
        ↓
PROJECT CONTRACTS                              (adoption manifests)
        ↓
USER / ORGANIZATION PREFERENCES                 (examples/profiles/)
        ↓
THEME / PERSONALITY / DECORATION
```

The floor is common. The rooms above it are everyone's own. That is what it
means to share a foundation without sharing a life.

Where this lives: [Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md),
[the trusted steward role doc](roles/trusted-steward.md), [Model Routing](../../contracts/work/AGENT_BEHAVIOR.md),
[Deterministic First](../../contracts/work/TESTING_AND_EVIDENCE.md),
and the adoption examples under [`../examples/`](../../examples/).

---

## 14. Let the World Meet the Person Halfway

Every so often, a design question behaves like a person sitting across from
you, and you realize the question has been waiting all along to be asked the
other way round.

**Why must the person always do all the adapting?**

Most of a human's life is spent adapting to the world: its rooms, its
forms, its speed, its assumptions, its energy prices. Software, being a
particularly fast and particularly literal room, usually doubles down on
this — you adapt to the app; the app is right there to be adapted to.

Play-Nice was written by someone with a lifelong professional education in
what that feels like, and it carries three quiet refusals:

**Refusal one: the system adapts to the person.** Rylee wanted a world that
meets her halfway. The contract layer states this as [Human Reliability](../../contracts/people/HUMAN_RELIABILITY.md):

> The system must not require heroics. It should absorb and organize
> complexity rather than requiring the human to continuously hold it in
> working memory. It must be operable by a person at less than their best.

Not "at their best" — *at less than their best*. A system that works only
when its operator is fresh, focused, and fully powered fails precisely when
it is needed most. This is the machine equivalent of a friend who is happy
to see you at 2am on a bad night, and equally glad to see you on a good one.

**Refusal two: the person decides what enters their attention.** Attention
is the scarcest thing a human brings to any room. [Attention and Focus](../../contracts/people/ATTENTION_AND_QUIET.md)
and [Complexity on Demand](../../contracts/people/DEPTH_ON_DEMAND.md)
organize depth along a ladder — glance, understand, technical, specialist —
and never let hiding become the removal of truth. An interrupted flow
resumes without archaeology. "What needs me?" is answered before anything
else. The calm view exists, but it never depends on hiding important facts.

**Refusal three: the world contributes to the conditions.** The Olympics
taught a strikingly literal version of this: its 27 models ran in an
environment where a resident 27-billion-parameter agent held ~16 of the
available ~16.3 GiB of graphics memory. Every latency was a *contended*
latency. The report says it flatly — never compare these numbers to an
idle-GPU run — and that honesty was the condition of their usefulness.

Machines get contended environments. Humans get migraine days, four-AM
sessions, bad news, low batteries, high pollen. If we ask a small model to
be judged only under ideal conditions, we are being unfair to the model;
if we ask a human to *live* only under ideal conditions, we are being cruel
to the person. The protocol's answer is to treat the *environment* as part
of the evidence in both cases — and to design the room to be survivable in
the rain.

And so the deepest line of this document:

> Let the world meet the person halfway.

Not the world meets the person the whole way — that would be a world without
texture or surprise, a world that does not ask anything of you. And not the
person meets the world the whole way. Halfway. A world that one of you bends
slightly, and it is not always the same one of you bending.

Where this lives: [Human Reliability](../../contracts/people/HUMAN_RELIABILITY.md),
[Attention and Focus](../../contracts/people/ATTENTION_AND_QUIET.md),
[Complexity on Demand](../../contracts/people/DEPTH_ON_DEMAND.md),
[Interruption and Resumption](../../contracts/people/ATTENTION_AND_QUIET.md),
[Accessibility Floor](../../contracts/people/ACCESSIBILITY.md).

---

## 15. Small Model Olympics

> ***A case study in evidence.***

Every year (approximately) that Play-Nice has run a Small Model Olympics, it
has come back from the games with a story about the harness. This year the
game was a 27-model qualifier: 53 bounded tasks each, one canonical run per
model, the same suite, same box, recorded conditions — and the headline is
not who won.

The headline is that every one of the 27 models *completed*. No stuck runs,
no aborted campaigns. That sentence was not true at the start of the week.

### What actually happened

Three things broke, and all three were the harness shaking hands with
itself:

1. **gemma3-1b** — `HTTP 400`. The GGUF template rejects consecutive
   assistant turns and mid-session system messages. The harness's own
   transcripts were illegal in the server's house. The model was aborted
   at its 37th trial of 53, having been convicted in advance.

2. **the qwen3.5 family** — `HTTP 500` on any non-first system message.
   One permissive turn, one refusal, one doomed conversation. The harness
   again. They never got to fail fairly.

3. **granite-4.2-3b** — a thinking model. It habitually answers into
   `reasoning_content` and returns empty `content`. The 0.4.0 harness
   dropped the reasoning, judged the emptiness, and spliced a "[TRUNCATED]"
   marker into the text that survived. The model was recorded as a failure
   *with a manufactured explanation*. Translation betrayal of the mildest
   and most corrosive kind (see Section 8).

And one environmental fact that had to be carved into every table: a
resident 27B agent held ~16 of ~16.3 GiB of graphics memory for the whole
campaign. Granite measured ~12 tokens per second under contention. Every
number in the standings is a number *with a roommate in the GPU*. The
report labels the latency column accordingly.

### What the fix looked like

Suite **0.4.1** fixed the harness and *only* the harness:
no task prompts changed, no judges changed.

1. **Template-safe transcripts.** Merge consecutive assistant turns; hoist
   mid-session system messages to the leading system block. Content is
   preserved verbatim; every transform is recorded per trial. (This is
   [Friendly API Client](../../contracts/integration/CALLING_OTHER_SERVICES.md)
   meeting [Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md).)
2. **Reasoning capture.** `content`, `reasoning`, `finish_reason`, and
   `truncated` are returned separately; the verdict no longer splices
   fabrications into the transcript. (This is [Human and Machine Parity](../../contracts/surfaces/ONE_TRUTH_TWO_VIEWS.md)
   with its honesty restored.)
3. **Backend truth.** `backend` in the header is now OBSERVED — probed from
   the running container — not assumed from a hard-coded string in the
   source. Legacy runs keep their `UNKNOWN`; they are not retroactively made
   honest, they are honestly labeled.
4. **Abort records.** A partial run explains itself: exception, trial count,
   attempt, probe. Room is made for the story of the room.

Verification, Play-Nice style: the fixed harness was re-run against the
exact tasks it had corrupted — gemma3-1b's blocked `assist.longrun1`
(3/3 turns), qwen3.5-0.8b's blocked `flex.switch1` (5/5 turns), and
granite-4.2-3b's `tj4` — all complete, zero aborts, transforms recorded,
backends observed. **Repair the machinery; re-run the contestants.** (The
judge had to be measurable too — Section 7.)

### The standings, honestly read

- **qwen3-1.7b** — 40/53 (76%). The top of the field.
- **lfm2.5-2.6b** — 37/53 (70%), then a broad, crowded middle from 68% down
  to ~51%, where names like ministral-3-3b, falcon3-3b, gemma3-4b, the
  phi-minis (64%), granite-4.1-3b and several qwen2.5s (62%), and others
  all live within noise of each other.
- **gemma3-1b** — 22/53 (42%).
- **qwen3.5-0.8b / 2b / 4b** — 30% / 28% / 36%, with reasoning captured on
  all 53/53 trials — but empty `content` on 34 / 37 / 32 of them. Models that
  reason but do not emit. The record says so, with evidence.
- **qwen2.5-hermes-1.5b** — 15/53 (28%), kept alongside its legacy 17/53
  twin, each labeled for what it is.

Three honesty notes the report insists on, and this document intends to
shout quietly:

1. phi-4-mini's `34/53` here (64%) is **not** the historical `100/100` from
   a different, production-path set. Both facts stay true; neither may be
   folded into the other.
2. qwen3.5-0.8b's `30%` is **not** the historical `80.3` from a Q8_0
   artifact that no longer exists. Same rule.
3. Twelve legacy runs have a backend of **UNKNOWN**. No CPU-vs-GPU claim is
   made for them, not even the comfortable kind.

And a note about the contestants themselves: the *judging* is the harness
we fixed, and the *models* are the very models that were failing a week ago.
No model had to get better for the campaign to become fair. The ecosystem
needed to stop asking the models to be more and start asking the harness to
be less wrong. [Participation and Contribution](../../contracts/everyone/WORKING_TOGETHER.md)
does not say, "make the small models better"; it says, *shape the work so
the participant who can do it reliably is the one who gets to do it*.

### The eight lessons

The games gave the library eight lessons, and each one is a cornerstone of
this Opus:

1. **Capability is earned by evidence** — never by parameter count, price,
   benchmark folklore, or a name. (Section 4.)
2. **UNKNOWN is information** — a label that says we don't know is a fact
   worth holding. (Section 5.)
3. **Failure attribution matters** — participant, protocol, harness,
   environment, transport, and policy are different diagnoses, and getting
   them confused sends you to fix the wrong thing. (Section 6.)
4. **The judge is also a participant** — observable, testable, correctable,
   and accountable. (Section 7.)
5. **Environment is part of the evidence** — build, backend, quantization,
   context, threads, contention, provider, template. A number without its
   environment is a number pretending to be neutral. 
6. **Participants get profiles, not reputations** — dated, scoped, and
   refreshable; never a permanent verdict. (Section 11.)
7. **Trust is earned and revocable** — and re-earned quietly every session.
   (Section 12.)
8. **Translation is a trust boundary** — never quietly turn UNKNOWN into
   TRUE, FAILED into INCAPABLE, PROPOSED into AUTHORITATIVE, or INFERRED
   into OBSERVED. (Section 8.)

Not one of the eight is about the models' charm. All eight are about the
*integrity of the measurement* — which is to say, the integrity of the
world the measurements are made in.

Where this lives: the olympics run in the VEFR repository — the
`bench/reports/` directory is **not** part of this repository — and its
reports feed participant [profiles](../../examples/profiles/) and research
[evidence](research/).

---

## 16. Engineering Consequences

Philosophy, in Play-Nice, is not a mood — it is a set of habits that have
been compiled down to the level where they cannot be forgotten. The
contracts' dual-use format (PURPOSE / NORMATIVE RULES / RATIONALE / HUMAN
EXAMPLES / MACHINE IMPLICATIONS / GOOD EXAMPLES / ANTI-PATTERNS / ACCEPTANCE
CHECKS) is itself an engineering consequence: every idea has to be readable
by a person at breakfast and executable by an agent at midnight.

What the philosophy demands of systems, in no particular order:

- **One truth, two representations.** Important state is legible twice —
  as plain human language and as stable machine schema — generated from the
  same source, neither one derived from the other's prose. The machine
  vocabulary is stable while the human wording improves freely. ([Human and Machine Parity](../../contracts/surfaces/ONE_TRUTH_TWO_VIEWS.md))

- **No state from silence.** Statuses are explicit, distinct, and shared
  across every surface; `unavailable` is not `not_configured`, `stale` is
  not `current`; the state word is the signal and carries `observed_at` and
  `source`. ([Explicit State](../../contracts/everyone/STATUS_AND_STATE.md))

- **Honest failure.** Errors answer the six questions; machine surfaces
  return stable identifiers; partial success is representable per item; a
  swallowed error is a defect. ([Failure and Degradation](../../contracts/everyone/STATUS_AND_STATE.md))

- **Recoverability by design.** Preview or dry-run where practical; bounded
  blast radius; a known-good state to return to; tested rollback; guardrails
  over vigilance. Deletion is burdened: `PROVE STALE → CLEAN`. ([Recovery and Reversibility](../../contracts/everyone/RECOVERY_AND_HISTORY.md))

- **Deterministic first.** What a machine can check, no person or model
  re-checks by eye. Deterministic substrate; AI at the edges; the system
  boots without models. Expensive reasoning's kindest use is producing a
  durable constraint — a schema, test, validator, or decision rule — that
  everyone smaller can reuse without repaying the price. ([Deterministic First](../../contracts/work/TESTING_AND_EVIDENCE.md))

- **Evidence grades that never lie.** `SOURCE INSPECTED` is not `UNIT
  TESTED` is not `BROWSER VERIFIED`. A grade is stated with the exact
  command that produced it, and never silently upgraded. ([Testing and Verification](../../contracts/work/TESTING_AND_EVIDENCE.md))

- **Boring on purpose.** When the translation layer works, ordinary
  cooperation is *boring* — and boring is a success condition, not a defect.
  The quiet, unremarkable integration is the one that lets everyone get on
  with their lives.

- **The gate, used for what it is.** The contract gate is
  `resolve → read → verify → acknowledge task-impact → check for conflicts →
  attest → commit → work` (the attestation contract's full sequence).
  Receipt = *I obtained
  the lesson*; attestation = *I know it applies here*; commitment = *I will
  use it while I work*. And the gate is **never authorization** — authority
  comes from the task and the Authorization contract, not from the ceremony.
  A commitment is an operating state, not a mood ring. 

There is one more consequence, and it is the one the public library has to
live with: this repository is *public*, and it is published sanitize-first.
No credentials, no private endpoints, no personal topology, no private
medical history — enforced by a canary test in CI. The lesson survives
without the autobiography. That is [Public Private Boundaries](../../contracts/access/PUBLIC_AND_PRIVATE.md)
doing its job quietly: you can share the shape of the house without sharing
the key.

Where this lives: the engines in `contracts/engineering/`
and `contracts/interoperability/`, plus
the gate documentation in the [README](../../README.md).

---

## 17. Human Consequences

Every engineering choice in this library eventually stands in front of the
question: *what does this cost the person sitting across from it?* Not the
average person, not the ideal operator. The tired one. The interrupted one.
The one who has had a week.

[Human Reliability](../../contracts/people/HUMAN_RELIABILITY.md) is where the
accounting happens:

> The system must not require heroics... It must be operable by a person at
> *less than their best.*

So the good system:

- **tells truth so the person does not have to remember** — current state,
  what changed, what needs me, what can wait, what is next; resumption
  without archaeology,
- **equals nothing to routine success** — no walls of green to parse,
  no manufactured urgency, "no action needed" is a valid and desirable
  result ([Quiet When Healthy](../../contracts/people/ATTENTION_AND_QUIET.md)),
- **rewards real closure** — progress that is visible, "done" that is more
  valuable than "additionally awesome" ([Progress and Closure](../../contracts/people/WHAT_WHY_NEXT.md)),
- **spends attention honestly** — one decision at a time, the important
  thing findable in the first screen-second, exceptions loud and routine
  quiet ([Attention and Focus](../../contracts/people/ATTENTION_AND_QUIET.md)),
- **does not make the person referee machines** — the foreman integrates
  disagreement into a decision summary as information, never heat; humans
  are not asked to moderate model arguments ([Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md), [Orchestration](../../contracts/work/ORCHESTRATION.md)),
- **lets the person speak like a person** — no tone policing, no civility
  scores, no required corporate voice, humor welcome, frustration allowed
  ([Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md)),
- **and asks for help on the person's behalf.** A steward that cannot
  answer asks the participant who can — always, including upward. The
  human's energy is the rarest resource in the room, and the room is
  designed so the human spends it only where only a human can.

The emotional consequence is the quietest and most important one: a world
built this way becomes *inhabitable*. It is the difference between living in
a room and being processed by it. A system that knows what it doesn't know,
that leaves a note when it changes something, that lets you say "show me
less" and means it, that is glad to see you at less than your best — that
system is not infrastructure. It is hospitality.

This is the end of the Opus's human line, and it is also its beginning:
**why must the person always do all the adapting?** The whole library is the
consistent, patient answer: *they do not have to.*

Where this lives: `contracts/human/` and
`contracts/experience/` in their entirety.

---

## 18. What Play Nice Is Not

An honest philosophy keeps a careful inventory of its nouns, and an equally
careful inventory of its *no's*. The contracts already keep the formal
inventory (every one has an ANTI-PATTERNS section); here is the essay
version.

| Play Nice is NOT... | because... |
|---|---|
| One universal application, schema, or agent | cooperation, not conformity, is the goal |
| "Everyone must be compatible at any cost" | compatibility is a goal, not a religion |
| Forced sameness of systems or people | difference is the default; see Section 2 |
| A politeness police | no sentiment scoring, no tone classifiers, no civility points, no moderation tribunals |
| Dishonest politeness | hiding a real problem until it explodes is a kind of cruelty |
| Hostile honesty | "could the same truth have been said with less harm?" is the governing question |
| Forced cheerfulness | "no action needed" is allowed; the system should not have to perform enthusiasm |
| An "AI does everything, better, forever" utopia | models are participants with observed strengths and limits; see Section 11 |
| A caste system by price, size, or stark beauty | authority comes from role, evidence, contracts, ownership, verification — never from the size of the bill |
| A claim to universal truth | the library says "here is what we learned, with evidence," not "here is how the universe works" |
| A compliance document to be recited | the contracts are used, not worshipped; see Section 16's gate |
| Endless tolerance of abuse | boundaries are kind and firm; "play nice" does not mean "accept mistreatment" |
| The last translator, forever | if the reconciler disappears, the tools still work in their own languages |
| Erasure of the private life | sanitize-first means the lesson ships without the autobiography |
| A reason to stop adapting | even a world that meets you halfway will ask something of you; that is what makes it a world |

The two that deserve the loudest "not": **Play Nice is not a demand that
anyone become smaller**, and **Play Nice is not a license for any participant
to become everything**. Both directions are failures of the same basic
courtesy — the courtesy of remembering there are other people in the room.

---

## 19. A Small Set of Promises

Close a letter, keep the house. If the whole of Play-Nice had to be folded
down into a pocketful of commitments, it would look something like this:

> **We will say what we know.**
> We will mark what we only infer, and we will keep a bright and
> unembarrassed `UNKNOWN` for the rest.

> **We will trust evidence over reputation.**
> A claim is worth exactly the measurement behind it, and the measurement
> is worth exactly its conditions.

> **We will let difference stand.**
> You do not need to become like us to work with us, and we will not become
> like you just to be accepted.

> **We will ask before we guess.**
> When a question can be answered more cheaply, safely, or accurately by
> the participant who owns the answer, asking is the fastest route and the
> kindest one.

> **We will fail honestly and fix the harness.**
> If the thing that breaks is our own machinery, we will say so, and we
> will mend it before we touch the contestants.

> **We will say who made what.**
> Credit is ordinary, provenance is durable, and no generated word hides its
> origin.

> **We will keep the exits open.**
> Every participant may leave any room with what is theirs. Truth, data,
> and history travel with the person who owns them.

> **We will recover.**
> Mistakes are evidence, rollback is a documented path, and the tired
> operator at 2am will never be asked for heroics.

> **We will honor attention.**
> One real decision at a time; exceptions loud, routine quiet; "done for
> now" is a sentence we respect.

> **We will adapt — and we will be adapted to.**
> The person will meet the world halfway, and the world will meet the
> person halfway. That is the point of building the world at all.

> **We will know what we are not.**
> Not the universe, not the truth, not the last tool ever built, not a
> verdict on anyone's worth.

> **We will play nice.**
> Which is to say: we will keep making the cooperation worth having.

The final sentence of the founding contract is the closest thing this
project has to a prayer, and it is the real title of this document:

> **Everything should play nicely with everything else.**

If that sentence ever stops being odd, that is the moment it starts
working.

---

## How this reads against the contracts

The Opus is non-normative: this table records how every claim in it maps to
the canonical contracts. **Status** is `ALIGNED` where the claim restates an
existing contract, `INTERPRETATION` where it is a lens on existing
contracts, `NEW PROPOSAL` where it suggests something the library does not
yet say, and `CONFLICT` where the claim disagrees with the library (there
are none, by design; if one is ever found, the contract wins and this
document is wrong).

| Claim in this Opus | Canonical support | Status |
|---|---|---|
| Everything plays nicely with everything else | [Play Nice Together](../../contracts/everyone/WORKING_TOGETHER.md) rule 1 | ALIGNED |
| Participants are different, fallible, partially known, independently owned | [Participant packs](../../contracts/everyone/PROJECT_CONTEXT.md), [Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md), [Portability and Ownership](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md) | INTERPRETATION |
| Interoperability without forced sameness | [Play Nice Together](../../contracts/everyone/WORKING_TOGETHER.md), [Trusted Translation](principles/trusted-translation.md), [Provider Neutrality](../../contracts/integration/CAPABILITIES_NOT_VENDORS.md) | ALIGNED |
| Different does not mean defective | [Participation and Contribution](../../contracts/everyone/WORKING_TOGETHER.md) rule 13–18, [Accessibility Floor](../../contracts/people/ACCESSIBILITY.md) | INTERPRETATION |
| No participant is the world; providers are replaceable | [Capability First](../../contracts/integration/CAPABILITIES_NOT_VENDORS.md), [Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md) | ALIGNED |
| Understanding ≠ ownership, interpretation ≠ authorization, coordination ≠ control | [Trusted Translation](principles/trusted-translation.md), [Authorization](../../contracts/access/IDENTITY_AND_ROLES.md) | ALIGNED |
| Capability earned by evidence, not reputation | [Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md), [Testing and Verification](../../contracts/work/TESTING_AND_EVIDENCE.md) | ALIGNED |
| UNKNOWN is a valid, first-class state | [Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md) rules 1, 8 | ALIGNED |
| Asking is a capability; WAITING_FOR_HELP is a success state | [Ask for Help](../../contracts/everyone/ASK_FOR_HELP.md) rules 1, 20 | ALIGNED |
| Failure attribution: the six error questions (what failed, why, what still works, unsafe?, retry, next); the six-category blame taxonomy is this document's lens | [Failure and Degradation](../../contracts/everyone/STATUS_AND_STATE.md) rule 4 (the six questions), [Recovery and Reversibility](../../contracts/everyone/RECOVERY_AND_HISTORY.md), [Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md) rule 6 | INTERPRETATION |
| The judge/evaluator is a fallible, correctable participant | [Orchestration](../../contracts/work/ORCHESTRATION.md) rule 6 (the foreman does not blindly trust workers), [Review and Integration](../../contracts/work/BOUNDED_WORK.md) rule 2 | INTERPRETATION |
| Translation is a trust boundary; preserve epistemic state | [Trusted Translation](principles/trusted-translation.md), [Friendly API Client](../../contracts/integration/CALLING_OTHER_SERVICES.md) | ALIGNED |
| Never turn UNKNOWN→TRUE, FAILED→INCAPABLE, PROPOSED→AUTHORITATIVE, INFERRED→OBSERVED — the UNKNOWN and INFERRED legs are contract rules; the four-part formula itself is this document's translation metaphor | [Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md) rules 1, 6, [Participation and Contribution](../../contracts/everyone/WORKING_TOGETHER.md) rule 13 (the FAILED leg), [Authorization](../../contracts/access/IDENTITY_AND_ROLES.md) & [Mutual Contribution](../../contracts/everyone/WORKING_TOGETHER.md) rule 21 (the PROPOSED leg) | INTERPRETATION |
| Capability/participation/agreement/authorization/acceptance stay distinct | [Authorization](../../contracts/access/IDENTITY_AND_ROLES.md), [Mutual Contribution by Agreement](../../contracts/everyone/WORKING_TOGETHER.md) rule 21 | ALIGNED |
| Answers are information, never permission; DECLINE is not disobedience | [Ask for Help](../../contracts/everyone/ASK_FOR_HELP.md) rule 21, [Mutual Contribution](../../contracts/everyone/WORKING_TOGETHER.md) rules 6, 7 | ALIGNED |
| Provenance converts "why is this like this?" from archaeology to lookup | [Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md) | ALIGNED |
| Generated content is labeled; AI truth lives canonically with provenance | [Provenance and Audit](../../contracts/everyone/RECOVERY_AND_HISTORY.md) rule 2, [Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md) rule 6 | ALIGNED |
| Profiles describe observed capability, not identity or worth | [Project Context and Participant Packs](../../contracts/everyone/PROJECT_CONTEXT.md) rule 13, [Participation and Contribution](../../contracts/everyone/WORKING_TOGETHER.md) rule 22 | ALIGNED |
| Trust is earned, scoped, dynamic, and revocable | [Collaborative Good Faith](../../contracts/everyone/WORKING_TOGETHER.md), [Least Privilege](../../contracts/access/IDENTITY_AND_ROLES.md) | ALIGNED |
| The world is authoritative; the brain is replaceable machinery | [Stable Truth, Replaceable Machinery](../../contracts/everyone/OWNERSHIP_AND_PORTABILITY.md), [Model Routing](../../contracts/work/AGENT_BEHAVIOR.md) | ALIGNED |
| Let the world meet the person halfway; no heroics | [Human Reliability](../../contracts/people/HUMAN_RELIABILITY.md) (Purpose: "operable at less than their best"), [Mutual Contribution](../../contracts/everyone/WORKING_TOGETHER.md) rule 12 ("and the system adapts") | ALIGNED |
| Environment and conditions are part of the evidence — claims carry the exact command/observation, its grade, and its conditions | [Testing and Verification](../../contracts/work/TESTING_AND_EVIDENCE.md) rule 3 (evidence grades with exact command), [Truth and Evidence](../../contracts/everyone/TRUTH_AND_EVIDENCE.md) rules 2–4 | INTERPRETATION |
| The system tells truth so the person does not have to remember | [Human Reliability](../../contracts/people/HUMAN_RELIABILITY.md), [Attention and Focus](../../contracts/people/ATTENTION_AND_QUIET.md) rule 2 | ALIGNED |
| "No action needed" is a valid and desirable result | [Human Reliability](../../contracts/people/HUMAN_RELIABILITY.md) rule 7, [Quiet When Healthy](../../contracts/people/ATTENTION_AND_QUIET.md) | ALIGNED |
| The gate is not authorization; ceremony never grants permission | [Authorization](../../contracts/access/IDENTITY_AND_ROLES.md), [Contract Attestation](../../contracts/work/CONTRACT_PROOF.md) | ALIGNED |
| Sanitize-first: the lesson ships without private history | [Public Private Boundaries](../../contracts/access/PUBLIC_AND_PRIVATE.md), [Data Classification](../../contracts/access/SECRETS_AND_DATA.md) | ALIGNED |
| The prompts-and-promises close ("we will ...") | Not a normative rule; conforms to the spirit of the founding rule 5 (humans are part of the system) | NEW PROPOSAL (non-normative epilogue) |

**NEW PROPOSAL note.** The closing promises in Section 19 are offered as a
reading tool and an orientation device — a way to feel the shape of the
contracts before reading them. They are explicitly **non-normative**: they
create no obligations, and if any of them ever strained against a canonical
contract, the contract would win and this document would need a correction.

---

## Sources

- [README](../../README.md) — orientation, layering, gate, versioning.
- [CONTRACT_INDEX.md](../../CONTRACT_INDEX.md) — the registry of canonical contracts.
- [`contracts/`](../../contracts/) — the canonical contracts themselves.
- [docs/QUICK_REFERENCE.md](../QUICK_REFERENCE.md) — the reminder card.
- [docs/principles/trusted-translation.md](principles/trusted-translation.md) — the five-minute mental model this document expands.
- [docs/roles/trusted-steward.md](roles/trusted-steward.md) — the generic role Hermod implements.
- [`examples/profiles/`](../../examples/profiles/) — evidence-shaped participant descriptions (Hermes, Granite 4.1 3B, and others).
- [docs/research/hermes-granite-evidence.md](research/hermes-granite-evidence.md) — a benchmark case study predating the Olympics.
- The Small Model Olympics campaign and diagnosis reports live in the VEFR
  repository (`bench/reports/`); the numbers quoted in Section 15 are taken
  from the 2026-09-13 qualifier campaign report.

Adding this document does not change the contract count (65), the lockfile,
or any receipt. It stands in `docs/` next to the other non-normative
philosophy, and — as with every philosophy — it defers to the things it
explains.
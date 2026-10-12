# The Scotty Principle

> **Status:** Optional reading · the learner-facing idea behind Play-Nice. Not needed to use it: start at [the floor](../../../contracts/everyone/FLOOR.md).

> **Understand the system deeply enough to explain it simply without making it wrong.**

---

## Status

```text
DESIGN PRINCIPLE / PHILOSOPHY
NON-NORMATIVE
```

This document explains a teaching and explanation pattern. It does not create
requirements by itself. Canonical requirements live in
[`contracts/`](../../../contracts/) and the registry in
[`CONTRACT_INDEX.md`](../../../CONTRACT_INDEX.md).

The name is a mnemonic inspired by Montgomery "Scotty" Scott, the engineer from
*Star Trek*. No knowledge of Star Trek is required, and the character is not an
authority for Play-Nice.

## In one minute

An unfamiliar system is easier to learn when the learner has something familiar
to think with.

A useful explanation therefore has a path like this:

```text
familiar structure
      ↓
plain explanation
      ↓
real term
      ↓
actual mechanism
      ↓
full technical depth
```

The familiar structure may be an analogy. The analogy is scaffolding, not
truth. It should preserve the relationships that matter, make the new idea
easier to predict, and stop before it starts teaching the wrong system.

The literal system must remain reachable.

## Translation and analogy do different jobs

Translation answers:

> What does this mean in words I already know?

Analogy answers:

> What familiar thing has the same useful shape?

That difference matters. A translation can make a sentence readable while the
relationships remain hard to hold in mind. A good structural analogy gives the
learner a small model they can reason with.

For example, a work queue can begin as "a line at a counter." That familiar
model explains waiting and taking turns. It stops being enough when concurrency,
retries, priorities, or reordering matter. At that point the explanation should
say so and teach the real mechanism.

The test is not whether the analogy is charming. The test is whether it helps a
person understand or predict the system more accurately.

## The five-year-old test

"Explain it to a five-year-old" is not a demand for baby talk or a fixed reading
level. It is a test for prerequisite load.

Ask:

- Can someone understand what this thing does without first learning our
  internal vocabulary?
- Can they tell what it belongs to or connects to?
- Can they understand an important boundary or thing it must not do?
- Can they keep learning from there without having to unlearn the analogy?

A child-simple entry and an expert-honest destination can coexist.

## A small pattern

When an analogy helps, three pieces are enough:

```text
LITERAL
What the thing actually is or does.

ANALOGY
The familiar structure that makes the relationship easier to understand.

BREAKS AT
The point where the analogy stops being reliable.
```

This is a writing pattern, not a schema. Do not add analogy fields to APIs,
database records, or every document merely because this principle exists.

## What makes a good analogy

A useful analogy:

- preserves the relationship that matters;
- makes at least one correct prediction easier;
- keeps the real term visible or easy to reach;
- has a clear stopping point;
- does not invent authority, safety, certainty, ownership, or capability;
- can disappear without changing the underlying system.

A bad analogy:

- is memorable but structurally wrong;
- becomes the only explanation;
- hides an exception that changes a safety or authority decision;
- creates a new ontology the implementation now has to obey;
- forces every product into the same story or visual theme.

If no honest analogy fits, use a concrete plain explanation instead.

## The learner ladder

The Scotty Principle works with
[Plain Language](../../../contracts/surfaces/PLAIN_LANGUAGE.md) and
[Depth on Demand](../../../contracts/people/DEPTH_ON_DEMAND.md):

```text
"Something familiar"
        ↓
"What it means here"
        ↓
"What we actually call it"
        ↓
"How it really works"
        ↓
logs / protocols / policies / internals
```

The first rung lowers the cost of entry. The later rungs prevent simplification
from becoming concealment.

A newcomer should be able to enter the explanation. An expert should be able to
keep walking until they reach bedrock.

## Relationship to Trusted Translation

[Trusted Translation](trusted-translation.md) asks participants to preserve
meaning, provenance, uncertainty, and authority while translating between
different systems.

The Scotty Principle asks one additional learner-facing question:

> Can the explanation give someone a familiar structure to think with without
> changing what the system actually means?

Trusted Translation protects meaning across systems. The Scotty Principle helps
a learner acquire that meaning.

Neither grants authority. Neither replaces canonical contracts.

## For agents and tools

```text
SCOTTY_PRINCIPLE means:

1. Start from human meaning, not internal vocabulary.
2. For an unfamiliar important concept, look for a familiar structural analog.
3. Use the analog only when it preserves the relationships that matter.
4. Keep the literal term and mechanism reachable.
5. State or reveal the analogy's consequential limits before they mislead.
6. Prefer no analogy to a wrong analogy.
7. Never let an analogy create machine semantics, authority, or hidden truth.
8. Let beginners enter and experts continue to full depth.
```

## Core line

> **Understand the system deeply enough to explain it simply without making it wrong.**

And the practical test:

> **A beginner can enter. An expert can keep walking to bedrock.**

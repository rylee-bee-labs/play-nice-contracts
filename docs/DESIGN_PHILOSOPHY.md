# How Play-Nice looks and sounds

> **Status:** Current · non-normative guidance for writing contracts, docs,
> tool messages and badges. Where it conflicts with a contract, the contract
> wins.

## In short

Plain, warm and short. The rule first, the reason second. Same shape every
time. Readable by anyone, on anything.

## Voice

- **Plain.** Say what a thing does, in the words a person would use.
  No invented terms. If a term of art is needed, define it once, where it
  first appears.
- **Warm.** Friendly, never cute at the reader's expense. Kind about
  mistakes: say what happened and what to do next.
- **Short.** Sentences under 25 words; paragraphs of three sentences or
  fewer. Cut anything that doesn't change what the reader does.
- **Rule first.** Lead with what to do; follow with why, briefly. Stories,
  metaphors and history belong on "why" pages, never inside a rule.
- **Specific.** Numbers, names, commands and dates beat adjectives.

## Shape of a contract

Every contract uses the same headings, in this order, so readers always know
where to look:

1. **In short**: three lines at most.
2. **Applies when**: who and what it's for, and when it doesn't apply.
3. **Rules**: numbered. MUST and SHOULD keep their usual meaning. At most
   about 15.
4. **Examples**: one good, one bad, if they help.
5. **Why**: one short paragraph.
6. **You're done when**: checks a person or a tool can actually run.
7. **Machine notes** (optional): schemas, file shapes, commands.

Aim for 800 words or fewer. Tool mechanics live in tool docs, not in rules.

## Tool messages

Every message says what happened and the next step, in that order:

```text
error: no Play-Nice setup in this folder yet.
  next: playnice start
```

Machine-readable output (`--json`) carries the same facts as the words.

## The bee badge

- One mark: the **honeycomb bee** (`assets/badge/`). A bee in a hexagon
  cell, for "part of the hive".
- Three states, always written out, never colour alone:
  - **plays nice · v1.2**: honey gold, dark text.
  - **behind · v1.3 is out**: amber, dark text.
  - **fix needed**: soft red, white text.
- Every colour pair meets WCAG AA contrast for its text.
- The badge links to the CI check that produced it when the repo has that
  workflow, and to the library otherwise. A copied picture is just a
  picture; the link is the proof.

## Accessible by default

- Everything reads well as plain text and with a screen reader.
- Images have text alternatives; badges carry their state in the image's
  title and alt text.
- Works on a small phone screen; tables scroll sideways inside themselves,
  never the page.

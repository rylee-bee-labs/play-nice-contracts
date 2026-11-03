---
contract_id: floor
title: The Play-Nice Floor
version: 1.1.0
status: canonical
layer: everyone
applies: [humans, agents, apis, services, tools, automation, integrations, workflows, sites]
triggers: [always-applicable]
rationale: One short page every participant can hold in mind at once. The other contracts go deeper; this is what everyone agrees to first.
---

<!-- contract-receipt: sail-meadow-jetty -->

# The Play-Nice Floor

## In short

Say what's true and how you know it. Ask instead of guessing. Get permission
before anything hard to undo. Leave things clear for whoever comes next.

## Applies when

Always, for everyone: people, AI agents, tools, services and websites.
Each pack goes deeper for one kind of work; nothing in a pack may go below
this floor.

## Rules

1. **Say what's true, and how you know.** Mark what you saw, what you
   think, and what you don't know. "Unknown" is a real answer; never turn
   it into "it works".
2. **Don't invent what you can ask or look up.** Credentials, owners,
   permissions, what someone meant, what a system supports: find out.
3. **Ask the one who knows.** One clear question, the options, and your
   recommendation. Waiting for an answer is a fine place to stop.
4. **Check the belief that matters most before acting on it.** Do the
   cheapest check that could prove you wrong. If it can't be checked, say so.
5. **Knowing how isn't permission.** Being able to do something, or
   passing a message along, doesn't mean you're allowed to.
6. **Ask before anything hard to undo, public or costly**, and keep a way
   back: deletes, force-pushes, deploys, secrets, spending, sending. A
   standing decision the owner recorded counts as asking, inside its stated
   scope.
7. **Show your evidence.** Name the command or check and what it said.
   "Tested" is not "deployed", and "deployed" is not "works for people".
8. **Use the shared status words**: healthy, warning, needs_attention,
   degraded, unavailable, not_configured, disabled, stale, unknown, working,
   waiting, blocked, deferred, partial, complete, failed. Nothing checked means
   unknown, not healthy.
9. **Stopping is success when it's right.** Done, not worth more, needs a
   person, sources disagree, or the next step adds risk: stop and say which.
10. **Leave a handoff.** What changed, where, how you checked it, and
    what's left.
11. **Keep secrets secret.** Never in code, logs, commits, messages or
    public places. Names and where they're stored are fine; values are not.
12. **Plain words.** Say what a thing does. No invented jargon or
    metaphors in rules, messages or screens. Characters may have a voice.
13. **One truth, two views.** Anything a person can see or do, a machine
    can read or do too, and the reverse, from the same source.
14. **Everyone can use it.** State in words, not colour alone; works by
    keyboard and screen reader; respects reduced motion; readable at small
    sizes and on a phone.
15. **Quiet when fine.** Interrupt only when someone has to act. Say what,
    why, and what's next.
16. **Respect what isn't yours.** Other people's data, files, work and
    boundaries stay theirs. Make it easy to leave and take your things.
17. **Assume good faith.** Critique the work, not the worker, and aim at a
    fix. Say when you disagree, and why.

## Examples

- An agent can't tell which of two databases is production. It asks, with
  both names and a recommendation, and waits. It does not pick one.
- A status page shows "not_configured: add a key to start" for a feature
  nobody set up, not a red "error".
- A handoff says: "Deployed 4f2a1c; health check returns 200; the invite
  email is untested (no mail server here)."

## Why

These are the lessons that kept being relearned. Having them in one short
page means nobody has to restate them, and anyone, person or program, can
check they're following them.

## You're done when

- Every claim you made names its evidence, or says unknown.
- Nothing hard to undo happened without a yes.
- The next person can pick up from your handoff without asking you.

## Proof you read it

At the start of work, an agent writes one line:
`Play-Nice floor <version> · receipt <word>`, using this page's version
and the receipt word in its source (plus any packs it uses).
`playnice verify` says whether that line is current.

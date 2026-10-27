# AGENTS.md

**Using Play-Nice in a project (including a copy under `vendor/`)?**
Read [the floor](contracts/everyone/FLOOR.md), then the pack for what you're
building ([index](CONTRACT_INDEX.md)). Start your handoff with the proof line
from [contract-proof](contracts/work/CONTRACT_PROOF.md). Nothing else here
is needed.

**Changing this library itself?** Read
[docs/MAINTAINING.md](docs/MAINTAINING.md) first: tests, CI, versioning, and
the rules for agents working on this repository.

## The packs

The floor is for everyone. Each pack goes deeper for one kind of work; nothing
in a pack may go below the floor. Each pack folder opens on its card: every
contract in short, with the headlines of its MUST rules and a link to the
full text.

| Pack | For |
|---|---|
| [Everyone](contracts/everyone/) | truth and unknowns, status words, asking for help, working together, recovery, ownership |
| [Agents and work](contracts/work/) | AI agents and anyone doing a task: bounded work, handoffs, testing, git, proof |
| [People](contracts/people/) | anything a person uses: attention, accessibility, sensory safety, depth, themes |
| [Surfaces](contracts/surfaces/) | APIs, CLIs, web UIs, rooms: plain words, one truth for people and machines, setups that check themselves |
| [Sites](contracts/sites/) | websites that people and agents can both use |
| [Integration](contracts/integration/) | connecting to other services |
| [Access](contracts/access/) | identity and roles, secrets and data, public and private |

## Version numbers

The library, the floor, each contract and the `playnice` tool have their own
version; the [README table](README.md#version-numbers) lists them. Proof lines
name the floor's. `playnice --version` prints the tool, library and floor.

## The proof line

Agents put one line at the top of their handoff —
`Play-Nice floor <version> · receipt <word> · read <contract ids>` — and check
it with `playnice verify`, which prints `CURRENT` (exit 0), `OUT OF DATE`
(exit 1) or `INVALID` (exit 2). The receipt word is in the floor's source.
`playnice rules "<task>"` lists the contract ids that apply.

A Play Nice receipt records the contract floor and applicable rules an agent
declares it has consulted. Verification checks the receipt's validity and
currency; it does not independently prove comprehension or compliance.

## The bee badge

`playnice check` writes a badge — **plays nice**, **behind** (a newer version is
out), or **fix needed**. When `playnice start` can write the CI workflow, the
README badge links to that check's runs; otherwise it links to the library.
A copied picture proves nothing. Run `check --badge playnice-badge.svg`
yourself to write the file and commit it.

`playnice check` also takes a website: `playnice.py check https://example.org`
reads its `/.well-known/play-nice.json` (see
[friendly-site](contracts/sites/FRIENDLY_SITE.md)).

## Changing the library

Read [docs/MAINTAINING.md](docs/MAINTAINING.md#start-here) first: the proof
line, the change flow (pull request, Rylee approves) and the recipe for
changing a contract. Old contract names still work: see the "Old names" table
in the [index](CONTRACT_INDEX.md) and `aliases.json`.

Character and world content from Project Worlds lives in other repositories
under their own terms. Nothing here licenses it, and it must never be moved
into this repository. License map: [maintaining](docs/MAINTAINING.md#licensing-map).
How the badge and the docs look and sound: [design
philosophy](docs/DESIGN_PHILOSOPHY.md).

## Verify

Work here is done when this passes (it runs what CI runs):

```bash
./tools/check.sh
```

## The floor

<!-- play-nice:start -->
<!-- written by `playnice start` — refresh with the same command, not by hand -->
This project follows Play-Nice (floor 1.0.0).

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
   back: deletes, force-pushes, deploys, secrets, spending, sending.
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

Packs that apply to this repo:
- Everyone — https://github.com/rylee-bee-labs/play-nice-contracts/tree/main/contracts/everyone
- Agents and work — https://github.com/rylee-bee-labs/play-nice-contracts/tree/main/contracts/work
- Surfaces — https://github.com/rylee-bee-labs/play-nice-contracts/tree/main/contracts/surfaces
- Integration — https://github.com/rylee-bee-labs/play-nice-contracts/tree/main/contracts/integration
- Access — https://github.com/rylee-bee-labs/play-nice-contracts/tree/main/contracts/access

Start each handoff with: Play-Nice floor 1.0.0 · receipt honey-cell-lantern
<!-- play-nice:end -->

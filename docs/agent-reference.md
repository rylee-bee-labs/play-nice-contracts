# Play-Nice agent reference

Depth moved out of `AGENTS.md` (what this is, how to verify, what not to touch, how to ask Rylee). Nothing
here overrides it, and nothing here changes a contract: the contracts under `contracts/` are the rules.

## The packs

The floor is for everyone. Each pack goes deeper for one kind of work; nothing
in a pack may go below the floor. Each pack folder opens on its card: every
contract in short, with the headlines of its MUST rules and a link to the
full text.

| Pack | For |
|---|---|
| [Everyone](../contracts/everyone/) | truth and unknowns, status words, asking for help, working together, recovery, ownership |
| [Agents and work](../contracts/work/) | AI agents and anyone doing a task: bounded work, handoffs, testing, git, proof |
| [People](../contracts/people/) | anything a person uses: attention, accessibility, sensory safety, depth, themes |
| [Surfaces](../contracts/surfaces/) | APIs, CLIs, web UIs, rooms: plain words, one truth for people and machines, setups that check themselves |
| [Sites](../contracts/sites/) | websites that people and agents can both use |
| [Integration](../contracts/integration/) | connecting to other services |
| [Access](../contracts/access/) | identity and roles, secrets and data, public and private |

## Version numbers

The library, the floor, each contract and the `playnice` tool have their own
version; the [README table](../README.md#version-numbers) lists them. Proof lines
name the floor's. `playnice --version` prints the tool, library and floor.

## The proof line

Agents put one line at the top of their handoff —
`Play-Nice floor <version> · receipt <word> · read <contract ids>` — and check
it with `playnice verify`, which prints `CURRENT` (exit 0), `OUT OF DATE`
(exit 1) or `INVALID` (exit 2). The receipt word is in the floor's source.
`playnice rules "<task>"` lists the contract ids that apply.

## The bee badge

`playnice check` writes a badge — **plays nice**, **behind** (a newer version is
out), or **fix needed**. When `playnice start` can write the CI workflow, the
README badge links to that check's runs; otherwise it links to the library.
A copied picture proves nothing. Run `check --badge playnice-badge.svg`
yourself to write the file and commit it.

`playnice check` also takes a website: `playnice.py check https://example.org`
reads its `/.well-known/play-nice.json` (see
[friendly-site](../contracts/sites/FRIENDLY_SITE.md)).

## Changing the library (detail)

Read [MAINTAINING.md](MAINTAINING.md#start-here) first: the proof
line, the change flow (pull request, Rylee approves) and the recipe for
changing a contract. Old contract names still work: see the "Old names" table
in the [index](../CONTRACT_INDEX.md) and `aliases.json`.

Character and world content from Project Worlds lives in other repositories
under their own terms. Nothing here licenses it, and it must never be moved
into this repository. License map: [maintaining](MAINTAINING.md#licensing-map).
How the badge and the docs look and sound: [design
philosophy](DESIGN_PHILOSOPHY.md).

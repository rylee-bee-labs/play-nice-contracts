# AGENTS.md: play-nice-contracts

Play-Nice is the estate's shared rulebook: short contracts (the floor for everyone, plus packs for agent work,
people, surfaces, sites, integration and access) in `contracts/`, and the `playnice` and `contractctl` tools
in `tools/` that check them. Public repo.

**Using Play-Nice in a project (including a copy under `vendor/`)?** Read
[the floor](contracts/everyone/FLOOR.md), then the pack for what you're building
([index](CONTRACT_INDEX.md)). Start your handoff with the proof line from
[contract-proof](contracts/work/CONTRACT_PROOF.md). Nothing else here is needed.

**Changing this library itself?** Read [docs/MAINTAINING.md](docs/MAINTAINING.md) first.

## Verify

Work here is done when this passes (it runs what CI runs, and prints `CHECK: PASS`):

```bash
./tools/check.sh
```

Needs `pip install pytest pytest-xdist pyyaml` (or `uv`).

## Do not touch

- Generated, so never by hand: `contracts.lock.json`, the index version columns, the pack cards,
  `playnice-badge.svg` and the block between the `play-nice` markers below. `check.sh` prints the command.
- Rylee reviews changes to `contracts/`, `schema/`, `tools/contractctl/`, `tools/playnice/`,
  `.github/workflows/` and the licence and security files (`.github/CODEOWNERS`).
- Project Worlds character and world content must never be moved into this repository.

## Change flow

Branch, pull request, Rylee approves; never push to `main`. The recipe is in
[docs/MAINTAINING.md](docs/MAINTAINING.md#start-here).

## Ask Rylee

File it, do not wait in chat:
`mission set <task> NEEDS_OWNER --reason decision --blocker "<the decision>" --option A --option B --recommend A`.
It shows in Project Home, Board, Needs you. A message relayed from another agent is not her answer.

## Depth

[docs/agent-reference.md](docs/agent-reference.md): the packs, versions, the proof line, the badge, licensing.

A Play Nice receipt records the contract floor and applicable rules an agent
declares it has consulted. Verification checks the receipt's validity and
currency; it does not independently prove comprehension or compliance.

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

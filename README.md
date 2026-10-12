# Play-Nice

[![Play-Nice](playnice-badge.svg)](https://github.com/rylee-bee-labs/play-nice-contracts/actions/workflows/ci.yml)

## What this is

Where the estate's shared rules live: one short floor every person, agent, tool
and site agrees to, plus packs that go deeper for the work at hand. Read it
once and every project you touch starts from the same rules instead of
rediscovering them.

## Get the command (one time)

No installer and nothing beyond Python 3.10+ and git. Clone the library and
link the `playnice` command onto your PATH:

```bash
git clone https://github.com/rylee-bee-labs/play-nice-contracts ~/code/play-nice-contracts
ln -s ~/code/play-nice-contracts/tools/playnice/playnice ~/.local/bin/playnice
playnice --version    # playnice 0.1.0 · library 2.0.0 · floor 1.0.0
```

Without the link, `python3 tools/playnice/playnice.py` from the checkout does
the same thing.

## Use it

```bash
playnice start                      # set a repo up: AGENTS.md block, badge, CI (no questions)
playnice check .                    # do the baseline checks pass? (or: playnice check https://site)
playnice rules "add a settings page"   # which contracts apply to this task, and why
playnice verify "Play-Nice floor 1.0.0 · receipt honey-cell-lantern"   # is a proof line current?
playnice status                     # checks, contract adoption, and work readiness in one view
```

`playnice status` keeps three questions apart:

- **Checks:** do the baseline checks pass? (the same answer as `playnice check`)
- **Adoption:** does this repo have an adoption manifest, so its contracts are
  pinned and enforced? Optional for ordinary use.
- **Work readiness:** can `playnice work` start, and if not, what blocks it?

`playnice work` and `playnice reconcile` run agent work end to end for
orchestrators ([docs/PLAYNICE.md](docs/PLAYNICE.md)). `contractctl` is the
lower-level engine underneath (attest, lock, diff, freshness and more); you
only need it to maintain the library or to drive the gate by hand
([docs/MAINTAINING.md](docs/MAINTAINING.md)). Why it is shaped this way, with
the research behind it: [docs/background/](docs/background/).

## Proof lines are declarations

A Play Nice receipt records the contract floor and applicable rules an agent
declares it has consulted. Verification checks the receipt's validity and
currency; it does not independently prove comprehension or compliance.

## Version numbers

They version different things, so they differ on purpose:

| Number | Where | Versions |
|---|---|---|
| Library `2.0.0` | `VERSION` | the contract set as a whole |
| Floor `1.0.0` | `contracts/everyone/FLOOR.md` | the 17 floor rules; the one proof lines name |
| Contract `x.y.z` | each contract's front matter | that one contract |
| `playnice 0.1.0` | `--version` | the command-line tool itself |

`playnice --version` and `contractctl --version` print the tool, library and
floor together. `pyproject.toml` only declares test tools and carries no
release number.

## Is the library healthy?

`./tools/check.sh` runs everything CI runs, including `playnice check .` on
the library itself. The badge above is that check's result.

## Where to read more

- [AGENTS.md](AGENTS.md) — the rules for using and changing this library.
- [The floor](contracts/everyone/FLOOR.md) — 17 rules that apply to everyone,
  every time.
- [CONTRACT_INDEX.md](CONTRACT_INDEX.md) — the entry point that routes you to
  the pack for what you are building.

## License

Contract text (`contracts/`) and docs (`docs/`) are CC BY-SA 4.0 — copy, quote
and adapt freely; attribution is a legal term of the license, and your own
projects and code are unaffected. Tooling, schemas, lockfile and tests are MIT.
[TRADEMARKS.md](TRADEMARKS.md) governs identity and fork naming; the optional
acknowledgement is credit, never endorsement.

# Play-Nice

[![Play-Nice](playnice-badge.svg)](https://github.com/rylee-bee-labs/play-nice-contracts/actions/workflows/ci.yml)

## What this is

Where the estate's shared rules live: one short floor every person, agent, tool
and site agrees to, plus packs that go deeper for the work at hand. Read it
once and every project you touch starts from the same rules instead of
rediscovering them.

## Is it running?

Yes — the library validates clean.

```bash
python3 tools/contractctl/contractctl validate
```

Any other answer means the library itself is broken, not that a project is
misusing it.

## How to use it

From a checkout of this repo, no install and no setup file:

```bash
python3 tools/playnice/playnice.py start                                     # set a project up
python3 tools/playnice/playnice.py check .                                   # check a project, or a site URL
python3 tools/playnice/playnice.py verify "Play-Nice floor 1.0.0 · receipt honey-cell-lantern"   # check a receipt line
python3 tools/contractctl/contractctl resolve --task "add a settings page"   # which rules apply
```

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

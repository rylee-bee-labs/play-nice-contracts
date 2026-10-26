# Contributing to Play-Nice Contracts

One maintainer of record (Rylee Hulgan). Agents, bots, and future
co-maintainers come through the same door. The full guide is
[docs/MAINTAINING.md](docs/MAINTAINING.md); these are the essentials.

1. **Start with the proof line**, not the old gate:
   [Start here](docs/MAINTAINING.md#start-here).
2. **Branch and open a pull request.** Never push to `main`; Rylee
   approves or merges ([merging](docs/MAINTAINING.md#rules-for-agents-working-here)).
3. **Changing a contract?** Follow [the recipe](docs/MAINTAINING.md#changing-a-contract):
   edit, then `contractctl bump`.
4. **Keep the rules for this repo:** stdlib-only tools, a changelog entry
   for every change, nothing private in a public repo, and the license map
   ([rules](docs/MAINTAINING.md#rules-for-agents-working-here),
   [licensing](docs/MAINTAINING.md#licensing-map)).
5. **Green or it didn't happen.** `./tools/check.sh` passes locally and
   the CI check `library` passes on the PR.

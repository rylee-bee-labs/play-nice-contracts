# The Play-Nice bee

> **Status:** Current · the badge and sticker, with the lines to copy.

A bee in a honeycomb cell: this project is part of the hive. The badge is
drawn by `playnice check` from the project's own check. A copied picture
proves nothing on its own: trust the check run, not the image.

## The badge, in its three states

| State | Badge | When |
|---|---|---|
| Plays nice | ![Play-Nice: plays nice · v2.0](badge-current.svg) | the project follows the current version and every check passed |
| Behind | ![Play-Nice: behind · v2.1 is out](badge-behind.svg) | a newer floor is out; run `playnice start` to refresh the AGENTS.md block |
| Fix needed | ![Play-Nice: fix needed](badge-fix.svg) | a check failed; the check's log says what to fix |

The state is always written on the badge, never shown by colour alone, and
every colour pair meets WCAG AA contrast (7.2, 5.5 and 5.2 to 1).

## Show it

`playnice start` adds this line under your README's title and writes
`playnice-badge.svg`. Where the badge links depends on what start could set
up:

- **Your repo has `.github/` and a GitHub origin:** start writes
  `.github/workflows/playnice.yml`, which re-runs the check on every push,
  and the badge links to that workflow's runs.
- **Otherwise:** the badge links to the Play-Nice library, because there is
  no check run to link to. Run `playnice check --badge playnice-badge.svg`
  yourself to redraw it.

```markdown
[![Play-Nice](playnice-badge.svg)](https://github.com/OWNER/REPO/actions/workflows/playnice.yml)
```

## The sticker

<img src="sticker-hive.svg" width="160" alt="Play-Nice: joined the hive">

For a README, a site footer, or a laptop. It says you joined; it isn't a
check result, so pair it with the badge if you want proof.

```markdown
<img src="https://raw.githubusercontent.com/rylee-bee-labs/play-nice-contracts/main/assets/badge/sticker-hive.svg" width="120" alt="Play-Nice: joined the hive">
```

## Floor stickers

Four of the floor's rules as stickers, for when a project wants to say what
it cares about.

| | | | |
|---|---|---|---|
| <img src="sticker-asks.svg" width="120" alt="Play-Nice: asks instead of guessing"> | <img src="sticker-unknown.svg" width="120" alt="Play-Nice: unknown is a real answer"> | <img src="sticker-quiet.svg" width="120" alt="Play-Nice: quiet when fine"> | <img src="sticker-agents.svg" width="120" alt="Play-Nice: plays nice with agents"> |
| asks instead of guessing (floor 2-3) | unknown is a real answer (floor 1) | quiet when fine (floor 15) | plays nice with agents |

## The bee on its own

<img src="bee.svg" width="64" alt="The Play-Nice bee">

Use it next to the name "Play-Nice". Rules for the name and the bee:
[TRADEMARKS.md](../../TRADEMARKS.md).

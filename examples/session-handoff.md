# Example handoff (v2)

> **Status:** Current · an example of the handoff shape from
> [handoff-and-continuity](../contracts/work/HANDOFF_AND_CONTINUITY.md).

```text
Play-Nice floor 1.1.0 · receipt <word from the floor> · read api, web-ui, accessibility, plain-language

CURRENT
  repo garden-notes, branch feat/settings, revision 4f2a1c0; not deployed.

CHANGED
  app/server.py: GET/PUT /api/settings (garden name), errors as problem details.
  app/static/index.html: settings form with a label, loading/empty/error states.

VERIFIED
  python3 tests_smoke.py -> "smoke ok" (unit tested).
  Keyboard: tab reaches the field and Save; not screen-reader tested (unknown).

CONTRACTS
  web-ui rule 3 (states), plain-language rule 2 (errors say the next step),
  accessibility rule 6 (labels). All followed.

UNKNOWN
  Browser zoom at 200%: not checked here (no browser).

DEFERRED
  /api/status still says healthy without checking: out of this task's scope.

NEXT
  Review and merge feat/settings.
```

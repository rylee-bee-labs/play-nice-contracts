---
contract_id: web-ui
title: Web UI
version: 2.0.1
status: canonical
layer: surfaces
applies: [ui, web]
triggers: [web page, website, frontend, ui, screen, form, dashboard, browser, page, button, menu, modal, dialog]
rationale: The web UI is one view of the same truth the API and CLI show: honest about state, usable by everyone, and never the only way in.
---

<!-- contract-receipt: gorse-poplar-harvest -->

# Web UI

## In short

Render real state, never invent it. Every section shows its own honest
loading, empty, and error state. Anything you can do on screen, you can
do without the screen.

## Applies when

You build or change a web interface. Not this contract's job: accessibility
detail and depth on demand (People pack), design truth (design-fidelity),
wording specifics (plain-language).

## Rules

1. The UI is a view, not the source of truth: every displayed value comes
   from a real response field or is labeled unknown or loading. Nothing
   on screen is fabricated. (MUST)
2. No UI-only truth: every concept operable on screen is understandable
   and operable without the UI (see one-truth-two-views, cli). The UI may
   be easier, never the only way. (MUST)
3. Show shared status words only, rendered as plain language, with honest
   empty states ("No journal entries yet") and explicit loading and error
   states per section. (MUST)
4. A failing section degrades alone; one broken widget never blanks the
   page. (MUST)
5. The accessibility floor applies in full: keyboard, visible focus,
   labels, zoom and reflow, reduced motion (People pack). (MUST)
6. Glanceable by default; detail one action away; the technical view is
   linked, not hidden. (SHOULD)
7. Theme, density, and motion come from stored user preferences, never
   invented per screen. (MUST)
8. Self-host what you can: no runtime requests to third parties for
   assets you could ship; a deployed UI works inside its own network.
   (MUST)
9. Follow the design contracts: semantic tokens, the approved
   composition, no hand-invented values (design-fidelity). (MUST)
10. Demo data never ships: no hardcoded content that pretends to be
    real. (MUST)

## Examples

- Good: the dashboard shows "not configured: add a key to start" for a
  feature nobody wired up, with a setup action.
- Good: the API says `not_configured`, the UI renders that word plus the
  action — it never invents `healthy` to look complete.
- Bad: one failed fetch blanks the whole app; a fabricated "Recent
  activity" fills an empty screen; an operation possible only by clicking
  through five screens.

## Why

Every system that treated the UI as the product and the API as plumbing
became fragile: UI rewrites became product rewrites, and screen-only
state drifted from real state.

## You're done when

- Every displayed value traces to a real response field or says unknown.
- The UI could be deleted and rebuilt from the API with no loss of
  operability.
- Sections fail independently, and every screen meets the accessibility
  floor.

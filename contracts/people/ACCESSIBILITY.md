---
contract_id: accessibility
title: Accessibility
version: 2.0.1
status: canonical
layer: people
applies: [ui, web, sites, product]
triggers: [ui, frontend, web page, page, form, screen, button, menu, modal, dialog, navigation, keyboard, screen reader, contrast, zoom, layout, accessibility, a11y]
rationale: The default product already works for people with different vision, motor control and assistive technology; preferences may add comfort but never lower the floor.
---

<!-- contract-receipt: slate-porch-kestrel -->

# Accessibility

## In short

The default product already works for different vision, movement and assistive
technology. Preferences may add comfort; nothing may drop below this floor
(see the floor, rule 14).

## Applies when

- You build or change any human-facing surface: web page, app screen, form,
  control, badge or site.
- Not this contract's job: how loud motion or sound is (see sensory-safety);
  when a surface may interrupt (see attention-and-quiet); theme mechanics
  (see themes-and-personalization).

## Rules

1. **Keyboard first-class.** Every function is reachable and operable with the
   keyboard alone; nothing traps focus; Escape closes overlays.
2. **Focus visible.** A clear focus indicator follows reading order and is
   never removed for looks.
3. **Targets at least 44×44 CSS px.** Icons may look smaller; hit areas may
   not. Preferences may grow targets, never shrink them below this.
4. **Meaning in words.** Never carry status or meaning by color, icon,
   position, glow or expression alone; every status has a text label.
5. **Real structure.** Heading levels in order, none skipped; landmarks
   (`header`, `nav`, `main`); a skip-to-content link as the first focusable
   element.
6. **Honest names.** Every meaningful control has a real accessible name and
   every input a real label; prefer native controls (`button`, `dialog`,
   `details`) over invented ones.
7. **Errors explain.** Error and validation messages name what failed, what
   still works, and what to do next.
8. **Zoom never blocked.** Browser zoom and text scaling are never disabled;
   at 200% zoom the layout reflows with no clipping, truncation or page-level
   horizontal scrolling. On web UIs this is a release gate checked in a real
   browser.
9. **Text wraps, not clips.** Keep line lengths readable; meaningful text wraps
   instead of being cut off, and anything truncated is reachable in full
   elsewhere.
10. **Scroll inside the table, not the page.** Dense tables may scroll
    sideways inside their own labeled region; the page itself never does.
11. **System modes welcomed.** Honor platform high-contrast and forced-colors
    modes: add borders and separation on top of system colors, never fight
    them; aim contrast at a comfortable band, not just the minimum.
12. **Destructive actions named.** Say the verb and the consequence ("Delete 3
    files"), never "OK" or "Yes"; confirmations start focus on the safe action.
13. **No fine-motor demands.** Nothing essential requires hover, drag,
    double-click or precise movement; every drag has a button or menu
    alternative.
14. **Dialogs behave.** Modal dialogs trap focus, make the background inert,
    close on Escape and return focus to the control that opened them.
15. **No "accessibility mode".** Preferences tune an already-accessible
    product; no combination of settings may lower this floor.

## Examples

- A screen reader says "Status: needs attention, certificate expires in 2
  days" — not "red dot".
- At 200% zoom on a narrow window, a settings form stacks into one column and
  everything still works.
- Not: focus outlines removed for a cleaner look; an `aria-label` that reads
  "button".

## Why

These are engineering requirements, stated without anyone's personal history,
and they cover real common conditions — limited vision, motor differences,
screen readers, fatigue — plus keyboard-heavy power users and automation. Built
into the default they serve everyone at once; bolted on later as a separate
"accessible mode", they quietly rot.

## You're done when

- A keyboard-only walkthrough of the main flows completes with no dead ends.
- Every status reads as text; nothing depends on color or position alone.
- Real browser at 200% zoom: no clipping, no page-level horizontal scroll.
- An automated scan (axe-class) reports zero serious/critical issues.
- No preference combination can lower the floor — structurally impossible,
  not promised.

## Machine notes

- Accessibility semantics (motion, contrast, text scale, target size) are
  core-owned state or schema; a theme consumes them and never owns them.
- Automated scans are proxies; the real-browser zoom/reflow check stays a
  release gate for web UIs.

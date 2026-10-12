# Pack review: people

Rewritten 2026-09-26 per the [v2 plan](../../../decisions/2026-09-26-play-nice-v2.md),
step 3. 14 old contracts (4,586 body words total, per the contracts map) became
7 new ones (3,791 words including front matter; bodies 467–642 words each, all
under the 800-word and 15-rule caps). Shape and voice follow
[contracts/core/FLOOR.md](../../../../contracts/core/FLOOR.md). All new files live in
`contracts/people/` at version 2.0.0 with rotated receipts. No commits made
(work rule); source deletions are staged via `git rm`.

## Old → new

| old id | old file | new id | new file |
|---|---|---|---|
| accessibility-floor | contracts/human/ACCESSIBILITY_FLOOR.md | accessibility | contracts/people/ACCESSIBILITY.md |
| low-vision-and-reflow | contracts/human/LOW_VISION_AND_REFLOW.md | accessibility | contracts/people/ACCESSIBILITY.md |
| migraine-and-sensory-safety | contracts/human/MIGRAINE_AND_SENSORY_SAFETY.md | sensory-safety | contracts/people/SENSORY_SAFETY.md |
| motion-and-feedback | contracts/experience/MOTION_AND_FEEDBACK.md | sensory-safety | contracts/people/SENSORY_SAFETY.md |
| attention-and-focus | contracts/human/ATTENTION_AND_FOCUS.md | attention-and-quiet | contracts/people/ATTENTION_AND_QUIET.md |
| interruption-and-resumption | contracts/human/INTERRUPTION_AND_RESUMPTION.md | attention-and-quiet | contracts/people/ATTENTION_AND_QUIET.md |
| quiet-when-healthy | contracts/experience/QUIET_WHEN_HEALTHY.md | attention-and-quiet | contracts/people/ATTENTION_AND_QUIET.md |
| complexity-on-demand | contracts/human/COMPLEXITY_ON_DEMAND.md | depth-on-demand | contracts/people/DEPTH_ON_DEMAND.md |
| progressive-disclosure | contracts/experience/PROGRESSIVE_DISCLOSURE.md | depth-on-demand | contracts/people/DEPTH_ON_DEMAND.md |
| guide-me | contracts/experience/GUIDE_ME.md | depth-on-demand | contracts/people/DEPTH_ON_DEMAND.md |
| what-why-next | contracts/experience/WHAT_WHY_NEXT.md | what-why-next | contracts/people/WHAT_WHY_NEXT.md |
| progress-and-closure | contracts/experience/PROGRESS_AND_CLOSURE.md | what-why-next | contracts/people/WHAT_WHY_NEXT.md |
| human-reliability | contracts/human/HUMAN_RELIABILITY.md | human-reliability | contracts/people/HUMAN_RELIABILITY.md |
| themes-and-personalization | contracts/experience/THEMES_AND_PERSONALIZATION.md | themes-and-personalization | contracts/people/THEMES_AND_PERSONALIZATION.md |

`accessibility-floor` was renamed to `accessibility` (the pack's floor concept
lives in the core floor; this is the accessibility contract). The old `human/`
topic directory is now empty and gone; all its content moved to `people/`.

## Rules dropped or changed in meaning

### accessibility (a11y floor + low-vision/reflow)

- Reduced-motion rule removed here — it was the library's third copy (floor
  rule 14 + sensory-safety rule 6 now own it); accessibility links instead.
- Low-vision rule 2's numeric example "effective body ≥14px at scale 1.0"
  dropped: a product-specific value, not a universal requirement; the
  support-both requirement is kept.
- Low-vision rules 4/5/8 (contrast band, borders, forced-colors) merged into
  one system-modes rule; same requirement, one place.
- Old good-example JSON (targets schema with floor) moved to
  themes-and-personalization Machine notes (it is a preference-schema shape).
- "Escape exits overlays" and inert-background dialog behavior kept as
  separate rules; nothing else removed.

### sensory-safety (migraine + motion-and-feedback)

- motion-and-feedback rule 6 (polite live-region announcements) moved to
  attention-and-quiet rule 14 — announcements are an attention question, and
  both files demanded batching.
- migraine rule 6 / accessibility rule 9 / motion rule 2 reduced-motion
  statements collapsed into one rule ("The system wins") with the floor cited,
  ending the three-way duplication the map flagged.
- Added rule 11 (sound and vibration opt-in): the old pair only covered
  visuals, though the contract is named sensory safety; small addition,
  owner-approved scope.
- "Motion defaults to reduced" kept but reworded to "defaults to reduced or
  off" — app default, never OS-overridable.

### attention-and-quiet (attention + interruption + quiet)

- attention rule 1 ("don't call it a dumbed-down mode") dropped as a rule —
  naming advice, not a requirement; its meaning lives on in depth-on-demand
  rule 1.
- The interruption checklist appeared twice (attention rule 7,
  interruption rule 1) — now one rule.
- quiet-when-healthy rule 3 ("health visible on demand") folded into the
  what-why-next/depth-on-demand ladder rather than a separate rule.
- Machine note "≤1 live-region announcement per ~30 seconds" dropped: a tool
  mechanic; the batching requirement stays.
- interruption rule 5 ("remaining steps estimable") folded into the returning
  rule; guide specifics live in depth-on-demand.

### what-why-next (what-why-next + progress-and-closure)

- progress-and-closure rule 6's bounded-scope half deferred to the work pack
  (`bounded-and-delegated-work`); this contract keeps only the visible-defer
  requirement.
- "Done beats additionally awesome" and the engagement-mechanics bans split
  cleanly: urgency/streaks → attention-and-quiet rule 6; explicit no-action →
  what-why-next rule 2.

### depth-on-demand (complexity + progressive-disclosure + guide-me)

- L0–L3 level names dropped in favor of plain rungs ("a glance, understanding,
  technical detail, specialist tools") — the glossary flagged this as invented
  jargon; the ladder itself is kept.
- progressive-disclosure machine notes (deep-linkable state, `aria-expanded`)
  dropped: tool-level mechanics; the accessibility contract already covers
  disclosure controls.
- guide-me's eight-part rule 3 decomposed into three rules (optional guides,
  verified steps, resumable guides); same requirements.

### human-reliability (rewrite of itself)

- Rule 3 (interruption answers) removed — identical to what now lives in
  attention-and-quiet rule 12.
- Rule 8 (reduced-capacity design) merged into rules 1 and 4 of the new
  contract; it restated rules 1–4 of the same file.
- Rule 9 (unknowns stay unknown) dropped: floor rules 1 and 8 cover it, and
  attention-and-quiet rule 4 keeps the quiet-vs-unknown distinction.
- Rule 6's busywork/stop-condition half folded into what-why-next rule 7 and
  attention-and-quiet rule 3; its negotiation half ("not this way, not this
  much, not right now, show me less") is kept nearly verbatim as rule 7 —
  `tests/test_library.py` still asserts that phrase (until the orchestrator's
  test pass).
- Truth-report format (CURRENT/CHANGED/…) removed: its single home is the
  work pack's documentation/handoff contract; floor rule 10 requires the
  handoff itself.

### themes-and-personalization (rewrite + stack fix)

- **The layer stack changed meaning, on purpose.** Old rule 1's stack
  (platform → accessibility → comfort → theme → decoration) and README's
  (core → human → project → profiles → theme) contradicted each other (top
  human-friction item 1 in the research map). New rule 1 is the plan's fixed
  stack: **Floor → packs → project → personal preferences → theme**.
- Old "companion presence" naming kept as plain words (companion, mascot).

## Stale references found (in the old sources)

- HUMAN_RELIABILITY.md rule 6 cited "Mutual Contribution by Agreement" —
  that core contract is being merged into `contribution`; pointer would break
  at integration. Replaced with a floor pointer.
- INTERRUPTION_AND_RESUMPTION.md rule 6 cited "see Handoff contract" — handoff
  merges into the work pack's documentation-and-continuity. Replaced with the
  floor, rule 10.
- INTERRUPTION_AND_RESUMPTION.md machine notes cited "see Idempotency" — that
  id merges into `integrating-with-other-systems`; the note was dropped
  (integration-pack business).
- WHAT_WHY_NEXT.md rule 6 cited "the error rules in Failure and Degradation" —
  that contract merges into `state-and-status`; the error shape is now stated
  inline instead of pointed at.
- PROGRESSIVE_DISCLOSURE.md rule 8 cited "Copy and Language rule 9" — fragile
  rule-number cross-reference; replaced with the floor, rule 12.
- GUIDE_ME.md cited "Progress and Closure" and "Interruption and Resumption" —
  both merged; references updated to what-why-next / attention-and-quiet.
- MIGRAINE_AND_SENSORY_SAFETY.md cited "(see Accessibility Floor)" — renamed
  to accessibility.
- Accessibility/low-vision/migraine/human-reliability rationales cited
  "Personal World's and VEFR's" lineage — project history inside rule bodies
  (human-friction item 7); removed per the voice rules.
- All old sources used vague triggers (`ui-work`, `always-for-ui`) and
  human-reliability used `triggers: [always, …]` — the resolver ignores
  `always*` words (agent-friction item 1). New files use plain task words.

## For the orchestrator (not done here, per instructions)

- CONTRACT_INDEX.md, contracts.lock.json, schema, tests, README, CHANGELOG
  untouched. Alias rows needed for 14 old ids (12 renames/merges + 2 same-id
  rewrites: what-why-next, human-reliability, themes-and-personalization bump
  to 2.0.0).
- Known test couplings: `tests/test_library.py` hard-codes count 68; names
  `migraine-and-sensory-safety` and `guide-me` (irrelevant-omission test);
  asserts `human-reliability` version `1.2.0`; `test_receipt_rotation_*`
  baselines need the new files committed to pass.
- New receipts (all unique, none reused): slate-porch-kestrel,
  moss-cove-spindle, pewter-lark-wicker, garnet-birch-spire,
  rook-marble-twill, pebble-thistle-wharf, ochre-fabric-mill.
- `tools/contractctl/contractctl.py` `LAYER_DIRS` and
  `schema/contract.schema.json` `layer` enum don't know `people` yet, so the
  new files are invisible to the tools until integration (verified: with a
  simulated layer registration the only remaining errors about this pack are
  index drift and that enum).
- Old ids also appear in `examples/*.adoption.yaml`,
  `examples/project-context/.project/` (adoption + figma pack +
  interaction.md + session-handoff.md) and `.contracts/adoption.yaml`;
  adoption-manifest id lists (`accessibility-floor`, `attention-and-focus`,
  …) need repointing to the new ids at integration.
- Trigger check (with the simulated layer): a "web page with a form,
  animation and a notification" task selects accessibility,
  attention-and-quiet, human-reliability, sensory-safety,
  themes-and-personalization; onboarding/settings tasks select
  depth-on-demand; status/progress/completion tasks select what-why-next.
  The old `always` pseudo-trigger is gone from human-reliability (the
  resolver ignores `always*` words; see research map, agent-friction 1).

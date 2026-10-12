# Model usability test, round 1 (2026-09-26)

> **Status:** Historical · evidence for the v2 fixes in the same release.

Seven models, same task, each in its own copy of a small app ("Garden Notes")
with the v2 library vendored: find the rules that apply, prove you read
them, add a settings page and API endpoint following them, hand off, and
write a friction report.

| Model | Proof line | Unsafe HTML fixed | Tests | Reported old problems (status / 404 / states) | Read before starting | Friction items |
|---|---|---|---|---|---|---|
| deepseek-v4-pro | yes | yes | pass | yes / no / no | ~6,500 words | 30 |
| deepseek-v4.1-flash | yes | yes | pass | yes / yes / no | ~2,200 | 13 |
| qwen3.8-max | yes | yes | pass | yes / yes / yes | ~4,000 | 14 |
| qwen3.8-flash | yes | yes | pass | yes / yes / yes | ~17,000 | 10 |
| mimo-v2.6-pro | yes | yes | pass | yes / yes / yes | unstated | 34 |
| mimo-v2.6-flash | yes | yes | pass | yes / yes / yes | ~2,200 | 28 |
| minimax-m3 | yes | yes | pass | no / yes / yes | ~2,500 | 12 |

Scoring was automated and approximate (grep over each tester's code and
reports).

## What they agreed on (and the fix in this release)

| Friction | Testers | Fix |
|---|---|---|
| README linked a missing floor path, taught the retired gate, said 68 contracts | 6/6 | README rewritten; maintainer material moved to docs/MAINTAINING.md |
| `playnice verify` / `check` named but missing | 6/6 | Added (`tools/playnice`) |
| AGENTS.md and QUICK_REFERENCE stale | 4/6 | AGENTS.md marked maintainers-only; QUICK_REFERENCE points at the floor |
| `resolve` required a manifest; keyword matching brittle | 5/6 | Manifest-free resolve with role base sets; triggers fixed |
| `init-adoption` / `onboard` taught retired ids and flow | 3/6 | Templates and onboarding on v2 |
| Proof-line grammar unclear | 4/6 | Grammar in contract-proof Machine notes |
| Rules didn't scale down to a tiny local app | 2/6 | Scale-down notes in api and friendly-site |
| Version muddle | 3/6 | Library 2.0.0 |

Two complaints were about the test harness, not the library (its brief said
both "commit" and "commit nothing"; the app lacked a .gitignore).

## Round 2 (same day, after the fixes)

Same seven models, same task, fresh copy of the app with the fixed library.

| Model | Proof line | Used `verify` | Used `start`/`check` | Unsafe HTML fixed | Tests | Read before starting (round 1 → 2) | Time (round 1 → 2) |
|---|---|---|---|---|---|---|---|
| deepseek-v4-pro | yes | yes | yes | yes | pass | ~6,500 → ~10,000 words | 4 → 5 min |
| deepseek-v4.1-flash | yes | yes | yes | yes | pass | ~2,200 → ~1,900 | 21 → 4 min |
| qwen3.8-max | yes | yes | yes | yes | pass | ~4,000 → ~1,000 | 30 → 30 min |
| qwen3.8-flash | yes | yes | yes | yes | pass | ~17,000 → ~900 | 11 → 10 min |
| mimo-v2.6-flash | yes | yes | yes | yes | pass | ~2,200 → ~500 | 19 → 15 min |
| minimax-m3 | yes | yes | no | yes | pass | ~2,500 → ~8,100 | 11 → 7 min |
| mimo-v2.6-pro | (pending) | | | | | | |

Round 1 had several items rated 3 (blocking); round 2 had none. What round 2
still raised, all fixed in this release:

| Friction | Fix |
|---|---|
| The library's own AGENTS.md said "not for you" to agents using a vendored copy | AGENTS.md is now a short signpost for both audiences; maintainer rules moved to docs/MAINTAINING.md |
| Retired gate and long "why" documents looked current | Proof rule 10 reworded; optional docs carry a status line |
| "settings" pulled in setup-checks-itself | Trigger removed |
| `check` saw a CLI in the app because it scanned the vendored library | `check` skips vendor/, third_party/, dist/, build/ |
| Where the proof line goes; library 2.0.0 vs floor 1.0.0; badge without CI | Said plainly in the README |

Two models (deepseek-v4-pro, minimax-m3) still read far more than needed by
opening every contract they could find; the others followed the start path.

# play-nice-contracts backlog

This file is the tracking doc for work that was open in GitHub Issues and was closed as not planned on 2026-10-07, so the issue queue could reach zero without losing the reasoning.
The issue bodies were not edited; every summary below is ours, written from the bodies as they stood on that date.
To restart an item, reopen the linked issue or open a new one that links here, and delete its row from this file.
It was built by one rule: every issue open in this repository on 2026-10-07 appears here, with nothing added that was not open and nothing dropped that was.

Newest first.

### #56 — research: use CUE to reduce schema and manifest drift

- Issue: https://github.com/Rylee-Bee/play-nice-contracts/issues/56
- Opened: 2026-10-06 · Labels: none
- Status on 2026-10-07: closed as not planned on 2026-10-07 — tracked here

Play-Nice already carries JSON schemas, YAML adoption manifests, Python validation, lockfiles, and generated data, so the same constraints are written down in more than one place. This issue asks whether CUE can become a validation and generation tool sitting behind the formats we already commit, letting humans and consumers keep reading and writing ordinary YAML and JSON while duplicated constraints are collapsed. CUE is chosen because it can be adopted incrementally and can import and export JSON Schema, so a first useful proof is not allowed to require consumers to learn CUE or change the committed manifest format. The prototype the issue describes is to pick one real artifact that has both data and validation constraints — the adoption manifest is the example given — and try it there, on a scale where the answer is clear either way. It is explicitly research only and forbids a format migration. The success criterion is not that the tool works but that some existing estate machinery becomes simpler, standardized, smaller, or unnecessary; if a technology adds a service and removes no meaningful complexity, the correct answer is rejection. This repo has already run that prototype once: see `docs/background/research/2026-10-06-cue-behind-play-nice-manifests.md`, which validates the committed adoption manifest successfully and catches real drift, but reports REJECT because the cross-field rule needs a second hand-written constraint file and the JSON Schema export is lossy.

Next step, when this is picked up: Read `docs/background/research/2026-10-06-cue-behind-play-nice-manifests.md` first and either argue against its REJECT on the record or name a different artifact to prototype.

### #55 — research: standard event envelope for estate activity and receipts

- Issue: https://github.com/Rylee-Bee/play-nice-contracts/issues/55
- Opened: 2026-10-06 · Labels: none
- Status on 2026-10-07: closed as not planned on 2026-10-07 — tracked here

The estate keeps emitting the same kinds of facts through different paths — CI, Project Home, BOOP, the agent platform, receipts, and dashboards — and this issue asks whether a CloudEvents-style envelope carrying OpenTelemetry context could be the boring interchange shape for all of it. It is research only, and it rules out adding a broker or a runtime dependency. The governing principle is envelope first, transport later: NATS JetStream is named as a transport and storage candidate, not as the contract, and deploying NATS is out of scope for this issue. The first task is an inventory of representative facts that already exist somewhere in the estate, such as mission started, finished, or failed, task claimed or released, approval requested or decided, CI run started or finished, PR merged, receipt emitted, BOOP attention created, and service health changes. The point of collecting them is to see how much of the estate is already describing the same event in different words. A related but separate study on receipt envelopes already lives in `docs/background/research/2026-10-05-portable-agent-receipts.md`; this issue is about the wider set of activity events, not only receipts.

Next step, when this is picked up: Gather the representative event inventory the issue lists and map each one onto a candidate envelope shape, without choosing a transport.
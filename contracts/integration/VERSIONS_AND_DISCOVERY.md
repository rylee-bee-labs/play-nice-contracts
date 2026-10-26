---
contract_id: versions-and-discovery
title: Versions and Discovery
version: 2.0.1
status: canonical
layer: integration
applies: [apis, schemas, integrations, tools]
triggers: [api version, schema change, breaking change, deprecation, compatibility, capability discovery, api change, version mismatch, deprecate]
rationale: Systems stop misreading each other when versions are declared and checked, and stop guessing when they can ask what a system supports.
---

<!-- contract-receipt: signpost-alabaster-crag -->

# Versions and Discovery

## In short

Declare your version; check theirs before using it. Breaking changes get a
new major number and a migration path. Ask what a system supports before
assuming — and say honestly what you support.

## Applies when

- You publish or consume an API, schema, file format, or tool interface that others depend on across releases.
- Not this contract's job: how hard to fail when things break (the floor and the state-and-status work cover status words); capability *design* (see capabilities-not-vendors).

## Rules

### Versions

1. Every published interface and stored payload declares its version explicitly (a `schema_version` field, a version header or path). Nothing is unversioned. (MUST)
2. Behavior never changes silently behind a version consumers already hold: a breaking change is a new MAJOR version with an explicit migration path. (MUST)
3. Compatible additions ship as MINOR, clarifications as PATCH. (SHOULD)
4. Readers validate the version stamp before interpreting the data. (MUST)
5. An unknown version fails clearly — "schema v9 not supported (this reader handles ≤ v7)" — never by guessing a shape or reinterpreting old data. (MUST)
6. Deprecation is announced, documented, and given a real migration window; removal is an explicit major event, not a surprise. (MUST)
7. Make compatibility testable where it matters: a conformance check over the version combinations you support. (SHOULD)

### Discovery

8. Ask before assuming: a client learns what a system supports before using it. A version or capability endpoint beats hard-coded per-server feature lists. (MUST)
9. Expose what you speak, where practical: supported versions, capability set, and which optional features are on, off, or not configured. (SHOULD)
10. Never advertise a capability you can't honor. An optional feature that exists but is switched off reports its real state (`disabled`, `not_configured`, `unavailable`). (MUST)
11. A missing optional capability is a normal outcome: the client skips it, falls back, or reports it. One absent feature never sinks the rest of the integration. (MUST)
12. A minimal system with a small capability set is as legitimate as a maximal one; it is not a broken big one. (MUST)
13. Report version mismatches at connection or negotiation time, in clear words — not at first use, as strange behavior. (MUST)
14. Cache discovery results if you like, but refresh them when versions change. (SHOULD)

## Examples

- Good: a CLI connects and says "this server speaks v2; I need v3" and stops, instead of half-working.
- Good: a server reports `webhooks: not_configured`; the client skips that feature and everything else works.
- Bad: renaming a JSON key in a minor release because "old readers will just ignore it".

## Why

Silent reinterpretation (new data read by an old reader as garbage) and silent breaking (a change discovered by a consumer's outage) are the two recurring integration disasters. Declared versions plus fail-closed readers catch both at the boundary, cheaply; asking what a system supports beats guessing at it.

## You're done when

- Every interface and stored payload you publish carries a version.
- Feeding a reader an unknown version produces a clear error, not wrong output.
- One absent optional feature degrades gracefully instead of failing the whole integration.
- Deprecations announce a migration path and window.

## Machine notes

Semver semantics apply: PATCH = clarification only, MINOR = compatible addition, MAJOR = changed or incompatible behavior. Keep machine-readable pins (exact version plus hash) so a consumer notices drift deterministically.

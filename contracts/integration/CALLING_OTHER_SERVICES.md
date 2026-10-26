---
contract_id: calling-other-services
title: Calling Other Services
version: 2.0.1
status: canonical
layer: integration
applies: [integrations, api clients, agents, automation]
triggers: [api call, third-party api, integration, external service, sync job, automation, retry, rate limit, write to another system, webhook]
rationale: Calling someone else's system well — learn first, respect limits, write small, verify, stay safe to repeat — is what keeps integrations running.
---

<!-- contract-receipt: kiln-larch-copper -->

# Calling Other Services

## In short

Before you call a service: read its docs. While you call: respect its
limits. When you change it: write small, verify with a fresh read, and make
"run it again" safe.

## Applies when

- You call, sync with, or change another team's system through its API — including agents and automation doing it for you.
- Not this contract's job: change notifications and caching (see events-and-caching), versions (see versions-and-discovery). Permission to act at all is the floor's (rules 5–6).

## Rules

1. Learn before acting: use the current documented API, official SDKs, and supported authentication; check documented versions and deprecation notes first. (MUST)
2. Don't scrape screens when an API exists, and avoid undocumented endpoints unless truly needed — then write down why. (MUST)
3. Respect the service: honor pagination, rate limits, `Retry-After`, timeouts, and connection limits; use bounded concurrency. (MUST)
4. Back off with jitter when retrying. Never strip protections (TLS verification, rate limits) to make a call "work". (MUST)
5. Not every failure retries: authentication errors, invalid data, refusals, and a human "no" are answers, not obstacles. Stop and report. (MUST)
6. For writes, go in order: read current state → name desired state → preview the diff → smallest useful change → verify with a fresh read from the source → record who did what. (MUST)
7. A success code is not proof the world changed; re-read the resource. "Delete and recreate" is a last resort with a stated reason, not an update method. (MUST)
8. Hard-to-undo, public, or costly external actions follow the floor, rule 6: ask first, and show the diff, how many things it touches, and whether it can be undone. (MUST)
9. Automation acts only inside the boundaries it was given — visible, editable, revocable — and journals its actions. An agent never widens its own authority. (MUST)
10. Make repeats safe: prefer ensure-a-result ("set to X") over do-an-action ("add X"); use the provider's idempotency keys or unique constraints where offered. (MUST)
11. Never assume an endpoint tolerates repeats: treat undocumented ones as unsafe to retry. (MUST)
12. Scheduled jobs treat every run as possibly a rerun: guard effects with "only if changed". Recovery replays check what already happened before acting (see recovery-and-reversibility). (MUST)
13. Record every external change: actor, intent, target, time, result (see provenance-and-audit). (MUST)

## Examples

- Good: a sync job reads one page at a time, waits out a `429 Retry-After: 120`, and resumes.
- Good: an agent proposes "add label `needs-review` to 3 pull requests, nothing else", is approved, applies once, re-reads each request, and records the change.
- Bad: retrying a `401` forever with the same dead token; POSTing one create three times "to be safe" and getting three rows.

## Why

Integrations written in a hurry produce the same incidents everywhere: rate-limit bans, duplicate writes, wiped state. Reading first, respecting limits, writing small, and verifying against the source is what survives a provider that is slow, flaky, or strict.

## You're done when

- Double-running the most destructive job changes nothing the second time.
- Every write was preceded by a read and followed by a fresh verification.
- Terminal failures end the retry loop, not extend it.
- Every external change traces to an actor, an intent, and a result.

## Machine notes

Centralize in the client: pagination, rate-limit and backoff policy, timeouts, terminal vs transient error classes (e.g. 401/403/409/422 never retried; 429/5xx retried with a bound), idempotency keys. Keep job records of what was applied, so reruns skip completed work.

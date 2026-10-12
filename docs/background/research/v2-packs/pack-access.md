# Pack review: access (Play-Nice v2, step 3)

Rewritten 2026-09-26 on branch `offload/pack-access-20260926-130130-0223`.
The six `contracts/security/*` files merge into three `contracts/access/*`
contracts. Nothing from the sources is silently lost; everything dropped or
changed is listed below.

## Old -> new

| old id | old file | new id | new file |
|---|---|---|---|
| authentication | contracts/security/AUTHENTICATION.md | identity-and-roles | contracts/access/IDENTITY_AND_ROLES.md |
| authorization | contracts/security/AUTHORIZATION.md | identity-and-roles | contracts/access/IDENTITY_AND_ROLES.md |
| least-privilege | contracts/security/LEAST_PRIVILEGE.md | identity-and-roles | contracts/access/IDENTITY_AND_ROLES.md |
| secrets | contracts/security/SECRETS.md | secrets-and-data | contracts/access/SECRETS_AND_DATA.md |
| data-classification | contracts/security/DATA_CLASSIFICATION.md | secrets-and-data | contracts/access/SECRETS_AND_DATA.md |
| public-private-boundaries | contracts/security/PUBLIC_PRIVATE_BOUNDARIES.md | public-and-private | contracts/access/PUBLIC_AND_PRIVATE.md |

All three are rewrites/merges, so all are version 2.0.0 with fresh receipts
(`anchor-fennel-postbox`, `quiet-cedar-satchel`, `meadow-lighthouse-fence`).
Old ids stay alias rows in CONTRACT_INDEX.md (orchestrator's job).

## New rules added (owner-approved brief)

- "Code asks `can this actor do X?` against named permissions, never names,
  groups or role strings; a role is only a bundle of permissions"
  (identity-and-roles rule 4). Meaning change: the old contracts assumed
  scoped grants but never forbade checking role strings.
- "The owner cannot be demoted or locked out by a group or role mapping"
  (rule 3). New; sharpens the old break-glass rule.
- "A helper works from a consented, expiring grant" (rule 11). New name for
  what least-privilege implied.
- "An agent acts with the lesser of its task's scopes and its person's
  permissions" (rule 12). Meaning change: least-privilege rule 7 said only
  "authority comes from task instructions"; now the person's own limits cap
  it.

## Rules dropped or changed, with why

| source rule | what happened | why |
|---|---|---|
| authentication 7 (three distinct auth failure messages; don't aid enumeration) | dropped | error/status wording belongs to the Surfaces pack (state-and-status), not access. |
| authentication 8 (secret handling at auth) | dropped as duplicate | lives once in secrets-and-data. |
| authentication machine notes (`authenticate/verify/step_up/whoami`, session stores) | dropped | tool mechanics move to tool docs per the v2 decision. |
| authorization 7 (journal sensitive authz decisions) | dropped | audit trail is provenance-and-audit (Everyone pack); one home per idea. |
| authorization machine note ("policy is code; cemented policies reject non-user mutations") | dropped | product-specific mechanism, not a universal rule. |
| least-privilege 2 (prefer short-lived per-service credentials) | strengthened | became "every grant has an expiry" (identity-and-roles rule 5); SHOULD -> MUST. |
| least-privilege 3 (`required` is a justified exception with `required_reason`) | dropped | config-schema hygiene, not an access rule; the shape survives in secrets-and-data machine notes. |
| least-privilege 5 + 1/2 (no silent widening; scoped grants) | merged | one grants rule (rule 5) — same content, half the words. |
| least-privilege rationale (PAT-in-URL incident, Personal World P0) | dropped | incident history is a story, not a rule; the general point is in Why. |
| secrets 7 + public-private 7 (exposure = compromise; rotate first; never re-send) | merged | one exposure rule (secrets-and-data rule 3); "coordinate history rewrites with the owner" dropped — the floor, rule 6 already requires asking before hard-to-undo acts. |
| secrets 8 (CI scan everywhere; redacted findings) | merged | one scan mechanism, required in secrets-and-data rule 4 and owned by public-and-private rule 6. |
| secrets 3 ("see Capability First") | kept as the one-interface rule, cross-reference dropped | that contract's id changes in the Interop pack; the idea stands alone (secrets-and-data rule 2). |
| data-classification 1 examples (`world`, `internal`) | dropped | product-specific class names; "a system may add classes, closed and documented" keeps the rule. |
| data-classification 2/6 (core assigns class; unknown fails safe) | kept | identity-and-roles rule 10 and secrets-and-data rules 6-7. |
| secrets anti-pattern ("ignore rule trusted to protect a tracked file") | moved | became public-and-private rule 5 — its natural home. |
| public-private 6 (recorded public/private decision) | kept (rule 1) | unchanged meaning. |
| public-private canary mechanism (`pn-safety: synthetic`, redacted findings) | kept verbatim in meaning | no other home for it; contractctl's participant validator depends on the marker string. |

## Stale or fragile references found

- contracts/security/AUTHENTICATION.md:28 cites "Failure and Degradation" —
  that contract merges into state-and-status in another pack; reference
  would go stale. Dropped.
- contracts/security/AUTHORIZATION.md:29 cites "External Mutations, Agent
  Behavior" — external-mutations merges into integrating-with-other-systems
  (Interop pack). Dropped from the merged text.
- contracts/security/SECRETS.md:24 cites "Capability First" — renames to
  capabilities-not-vendors (Interop pack). Dropped.
- contracts/security/LEAST_PRIVILEGE.md:28 cites "Agent Behavior". Dropped;
  the idea now lives in identity-and-roles rules 11-12.
- Old front matter used trigger pseudo-words `always` and `always-for-data`
  (AUTHORIZATION.md:8, SECRETS.md:8, DATA_CLASSIFICATION.md:8); the resolver
  ignores triggers beginning with "always" (tools/contractctl/contractctl.py
  ~line 758), so they never selected anything. Replaced with plain task words.
- Still referencing old ids, left untouched for the orchestrator:
  CONTRACT_INDEX.md, contracts.lock.json, examples/homelab.adoption.yaml,
  examples/personal-world.adoption.yaml, tests/test_library.py (hardcoded
  count and least-privilege trigger tests).
- schema/contract.schema.json: the `layer` enum allows `security`, not
  `access`, so `contractctl validate` fails on the new directory until the
  schema is updated at integration (expected per the brief).

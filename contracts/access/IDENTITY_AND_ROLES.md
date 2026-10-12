---
contract_id: identity-and-roles
title: Identity and Roles
version: 2.0.1
status: canonical
layer: access
applies: [services, apps, apis, agents, automation, infrastructure]
triggers: [login, log in, sign in, sign up, signup, auth, authenticate, authentication, authorization, oidc, saml, sso, mfa, 2fa, permission, role, access control, session, token, oauth, api key, agent access, admin, user management]
rationale: One contract for who someone is and what they may do — identity proved with current evidence, access decided with named permissions, every grant bounded, dated and revocable.
---

<!-- contract-receipt: anchor-fennel-postbox -->

# Identity and Roles

## In short

Prove who is acting with current evidence. Decide access by asking
"can this actor do X?" about named permissions, never names or role
strings. Grant only what the job needs, with an expiry and a revoke.

## Applies when

- You let someone in: a person, a browser, a CLI, an agent, a service.
- You write the part that decides what a caller may do: permissions,
  roles, tokens, sessions.
- Not this contract's job: keeping secret values out of files and data
  classes (secrets-and-data); what may appear in public places
  (public-and-private). Knowing how isn't permission — see the floor,
  rule 5.

## Rules

1. Identity comes from current evidence: a credential, session or
   token that is valid right now. Network position, hostname or being
   "internal" is never identity, and client-supplied identity headers
   are never believed unless they come from a trusted front door that
   proves itself (a shared secret or mutual TLS). (MUST)
2. Keep more than one way in, and treat each as first-class: browser
   sessions for people, tokens for CLIs, agents and services. The
   sign-in provider is swappable configuration, not architecture. (MUST)
3. The owner always has a tested local path in, and no group or role
   mapping can demote the owner or lock the owner out. (MUST)
4. Code asks "can this actor do X?" against named permissions. It
   never checks names, group membership, or role strings. A role is
   just a named bundle of permissions; editing a bundle changes
   permissions and nothing else. (MUST)
5. Every grant is explicit and bounded: named actor, named permission,
   named scope, expiry, revocable. Nothing is granted "just in case";
   admin credentials are never shared. Authority widens only by a
   recorded, explicit change. (MUST)
6. Ambiguous authority means no: deny, name the permission that was
   missing, say how to get it, and leave the refusal visible. (MUST)
7. Sessions are bounded and inspectable: you can see who you are and
   when the session ends; any session can be revoked; losing session
   storage costs nothing important. (MUST)
8. Risky actions step up: policy changes, reading stored secrets,
   destructive operations. They need fresh proof of authority, even on
   remembered devices. A remembered choice keeps a boundary; it never
   erases one. (MUST)
9. Running a system is not reading its contents: administrative
   ability never grants routine access to other people's private
   material. (MUST)
10. A request cannot promote itself: a role, level or class declared
    inside a payload, header or record is stored data, not authority.
    The system assigns them. (MUST)
11. A helper works from a consented, expiring grant: who allowed what,
    for which job, until when. No standing keys. (MUST)
12. An agent acts with the lesser of its task's scopes and the
    permissions of the person who dispatched it — never more. (MUST)
13. Keep environments apart: development credentials and grants never
    reach production. (MUST)
14. List who holds what; review and rotate. Test revocation before
    you need it. (SHOULD)

## Examples

- Good: a request is refused with `{"error": "forbidden",
  "needed_permission": "vault:read", "how": "grant the scope, or use
  the vault screen"}` — no secret and no inventory leaks.
- Bad: `if user.role == "admin": show_everyone_journals()` — it checks
  a role string and grants routine access to private data (rules 4
  and 9).
- A group sync drops the owner from every group. The owner still gets
  in through the local path and is still the owner; flag the sync for
  a person.

## Why

Long-lived, broad credentials turn a small mistake into an incident,
and one-provider lock-in turns a provider outage into a lockout.
Naming permissions in code keeps every access decision reviewable and
lets providers change without rewriting anything.

## You're done when

- Searching authorization code for role-string checks (`role ==`,
  `isAdmin`) finds none deciding access.
- The owner can sign in with the main provider unreachable, on a path
  tested this month.
- Every standing credential can answer: whose, for what job, expires
  when, how revoked.
- Agents and helpers have expiry dates, and no task or config says
  "do whatever is needed".

## Machine notes

- A permission check takes (actor, action, scope) and answers yes or
  no; a "no" names the missing permission.
- Grant record shape:
  `{"actor": "backup-sync", "permission": "repo:read", "scope": "repo-a",
  "granted": "2026-09-01", "expires": "2026-12-01", "revocable": true}`
- Step-up levels live on sessions and tokens and are checked per
  sensitive operation.

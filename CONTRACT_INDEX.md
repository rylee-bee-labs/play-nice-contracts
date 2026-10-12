# Contract index

The registry of Play-Nice contracts. It routes; the contracts themselves govern.

**Start with [the floor](contracts/everyone/FLOOR.md)**: one page everyone reads. Then open the pack for what you are building.

## Everyone

All participants: truth, status words, asking, working together, recovery, ownership.

| ID | Title | Ver | Status | Purpose |
|---|---|---|---|---|
| `floor` | The Play-Nice Floor | 1.0.0 | canonical | One short page every participant can hold in mind at once. The other contracts go deeper; this is what everyone agrees to first. |
| `ask-for-help` | Ask for Help | 2.0.0 | canonical | Asking the participant who owns an answer is safer, cheaper, and kinder than guessing, and a good question is resumable state. |
| `ownership-and-portability` | Ownership and Portability | 2.0.0 | canonical | Tools are temporary, so the owner's truth must outlive every one of them and stay movable on the owner's terms. |
| `project-context` | Project Context | 2.0.0 | canonical | A new session should orient from durable files, not rediscover the project and its participants from scratch every time. |
| `recovery-and-history` | Recovery and History | 2.0.0 | canonical | Mistakes and failures happen, so risky changes need a tested way back and every meaningful change needs a record of who, when, and why. |
| `status-and-state` | Status and State | 2.1.0 | canonical | One shared status vocabulary and honest errors let people and machines tell broken from not-set-up from not-checked without guessing. |
| `truth-and-evidence` | Truth and Evidence | 2.0.0 | canonical | Confident reports drift from reality, so every claim needs its evidence and every unchecked belief needs a cheap test before it can steer work. |
| `working-together` | Working Together | 2.0.0 | canonical | Cooperation lasts when work is offered and agreed rather than imposed, contributions are right-sized, and criticism points at a repair. |

## Agents and work

AI agents and anyone doing the work: bounded work, handoffs, testing, git, proof.

| ID | Title | Ver | Status | Purpose |
|---|---|---|---|---|
| `agent-behavior` | Agent Behavior | 2.0.0 | canonical | One page for how an agent behaves while it works, including how to pick which model does a job. |
| `bounded-work` | Bounded Work | 2.0.0 | canonical | A job with a defined finish can be finished; a job without one grows until someone pays to stop it. |
| `contract-proof` | Contract Proof | 2.0.1 | canonical | Being current with the rules needs one cheap, checkable statement per kind of participant, not a ceremony that proves reading instead of following. |
| `git-and-worktrees` | Git and Worktrees | 2.1.0 | canonical | Branches and worktrees record who owns which work in flight, so parallel work stays safe and nothing real is deleted on a guess. |
| `handoff-and-continuity` | Handoff and Continuity | 2.0.0 | canonical | The expensive part of resuming work is re-deriving what the last session knew, and a handoff plus current docs make that a lookup instead. |
| `observability` | Observability | 2.0.0 | canonical | Logs and status surfaces exist so the next person or agent can diagnose a failure without reverse engineering it or leaking secrets while doing so. |
| `orchestration` | Orchestration | 2.0.0 | canonical | Splitting work between people and agents only works when each role, each work packet, and each check is explicit. |
| `search-before-building` | Search Before Building | 2.0.0 | canonical | New things are easy to add and hard to remove, so an existing thing that already owns the job beats a new parallel one. |
| `testing-and-evidence` | Testing and Evidence | 2.0.0 | canonical | Every "it works" is a claim with a grade and a command behind it, and the ordinary path should need no model at all. |

## People

Anything a person uses: attention, accessibility, sensory safety, depth, themes.

| ID | Title | Ver | Status | Purpose |
|---|---|---|---|---|
| `accessibility` | Accessibility | 2.0.1 | canonical | The default product already works for people with different vision, motor control and assistive technology; preferences may add comfort but never lower the floor. |
| `attention-and-quiet` | Attention and Quiet | 2.0.0 | canonical | A person's attention is borrowed, not owned; healthy systems spend almost none of it, and pausing and coming back is designed for, not suffered. |
| `depth-on-demand` | Depth on Demand | 2.1.0 | canonical | Useful complexity is kept, not deleted; it is organized so a beginner has a clear path and an expert can drill all the way down. |
| `human-reliability` | Human Reliability | 2.0.0 | canonical | A system must stay safe and understandable when the person using it is tired, interrupted or new, not only at their best. |
| `sensory-safety` | Sensory Safety | 2.0.0 | canonical | Interfaces stay usable for people sensitive to light, motion and sound as plain engineering requirements; start still, keep motion meaningful, never demand it. |
| `themes-and-personalization` | Themes and Personalization | 2.0.0 | canonical | People make the product theirs without customization eroding accessibility, coherence or meaning. |
| `what-why-next` | What, Why, Next | 2.0.0 | canonical | Every important state and message answers the same three questions, and finished work is allowed to stay finished. |

## Surfaces

APIs, CLIs, web UIs, rooms: plain words, one truth for people and machines, setups that check themselves.

| ID | Title | Ver | Status | Purpose |
|---|---|---|---|---|
| `api` | API | 2.0.0 | canonical | The API is the seam every other surface builds on, so it must be versioned, documented, discoverable, and honest about errors. |
| `cli` | CLI | 2.0.0 | canonical | The command line is a first-class view of the system: usable by a tired human, scriptable by cron, inspectable by agents. |
| `design-fidelity` | Design Fidelity | 2.0.0 | canonical | The approved design is data in the repo, checked layer by layer, so what ships matches what was decided — with no design tool required. |
| `one-truth-two-views` | One Truth, Two Views | 2.0.0 | canonical | One fact stored once and shown twice: plain words for people, stable shapes for machines, both generated from the same source. |
| `plain-language` | Plain Language | 2.1.0 | canonical | Words are part of every surface, so they get the same care as the rest: honest, short, and actionable. |
| `room` | Room | 2.2.0 | canonical | Many small independent backends can share one front door only if each serves the same few endpoints with the same honest shapes. |
| `library` | Library | 1.2.0 | canonical | Many apps can teach people how they work only if their books share one shape that a beginner and an expert can both read, and one home can gather them without rewriting them. |
| `setup-checks-itself` | Setup Checks Itself | 1.0.0 | canonical | A setup that ends in "should work now" is a guess, so every setup offers a real check the person can run on the spot. |
| `web-ui` | Web UI | 2.0.1 | canonical | The web UI is one view of the same truth the API and CLI show: honest about state, usable by everyone, and never the only way in. |

## Sites

Websites that people and agents can both use.

| ID | Title | Ver | Status | Purpose |
|---|---|---|---|---|
| `friendly-site` | Friendly Site | 1.0.0 | canonical | Sites are read by agents as well as people, so a site needs its own rules for being honest and usable to both. |

## Integration

Connecting to other services: capabilities not vendors, calls, events, versions.

| ID | Title | Ver | Status | Purpose |
|---|---|---|---|---|
| `calling-other-services` | Calling Other Services | 2.0.0 | canonical | Calling someone else's system well — learn first, respect limits, write small, verify, stay safe to repeat — is what keeps integrations running. |
| `capabilities-not-vendors` | Capabilities, Not Vendors | 2.0.0 | canonical | Your system's meaning should not depend on any one outside product, so that product can be swapped or lost without losing the feature. |
| `events-and-caching` | Events and Caching | 2.0.0 | canonical | Learn about changes without spamming the source: get told when you can, poll politely when you can't, and keep cached data honest about its age. |
| `versions-and-discovery` | Versions and Discovery | 2.0.0 | canonical | Systems stop misreading each other when versions are declared and checked, and stop guessing when they can ask what a system supports. |

## Access

Identity and roles, secrets and data, public and private.

| ID | Title | Ver | Status | Purpose |
|---|---|---|---|---|
| `identity-and-roles` | Identity and Roles | 2.0.1 | canonical | One contract for who someone is and what they may do — identity proved with current evidence, access decided with named permissions, every grant bounded, dated and revocable. |
| `public-and-private` | Public and Private | 2.0.0 | canonical | A repository that is public now or later is held to the public standard today, and canary tests — not intentions — enforce that boundary. |
| `secrets-and-data` | Secrets and Data | 2.0.0 | canonical | Secret values live only in secret storage, every record carries a class that decides where it may appear, and both are enforced by structure and tests, not by memory. |

## Old names

Contract ids from library 0.10.0 and where their rules live now. Tools accept the old names.

| Old id | Now part of |
|---|---|
| accessibility-floor | `accessibility` |
| assume-unknown | `truth-and-evidence` |
| attention-and-focus | `attention-and-quiet` |
| authentication | `identity-and-roles` |
| authorization | `identity-and-roles` |
| capability-first | `capabilities-not-vendors` |
| collaborative-good-faith | `working-together` |
| complexity-on-demand | `depth-on-demand` |
| contract-attestation | `contract-proof` |
| copy-and-language | `plain-language` |
| data-classification | `secrets-and-data` |
| dependency-discipline | `search-before-building` |
| design-source-and-fidelity | `design-fidelity` |
| deterministic-first | `testing-and-evidence` |
| discovery-and-negotiation | `versions-and-discovery` |
| documentation-and-continuity | `handoff-and-continuity` |
| explicit-state | `status-and-state` |
| external-mutations | `calling-other-services` |
| failure-and-degradation | `status-and-state` |
| friendly-api-client | `calling-other-services` |
| guide-me | `depth-on-demand` |
| handoff | `handoff-and-continuity` |
| human-and-machine-parity | `one-truth-two-views` |
| idempotency | `calling-other-services` |
| interruption-and-resumption | `attention-and-quiet` |
| least-privilege | `identity-and-roles` |
| low-vision-and-reflow | `accessibility` |
| machine-readable-output | `one-truth-two-views` |
| migraine-and-sensory-safety | `sensory-safety` |
| migrations | `recovery-and-history` |
| model-routing | `agent-behavior` |
| motion-and-feedback | `sensory-safety` |
| mutual-contribution | `working-together` |
| participation-and-contribution | `working-together` |
| play-nice-together | `working-together` |
| polling-webhooks-and-caching | `events-and-caching` |
| portability-and-ownership | `ownership-and-portability` |
| progress-and-closure | `what-why-next` |
| progressive-disclosure | `depth-on-demand` |
| project-context-and-participant-packs | `project-context` |
| provenance-and-audit | `recovery-and-history` |
| provider-neutrality | `capabilities-not-vendors` |
| public-private-boundaries | `public-and-private` |
| quiet-when-healthy | `attention-and-quiet` |
| recovery-and-reversibility | `recovery-and-history` |
| review-and-integration | `bounded-work` |
| search-before-inventing | `search-before-building` |
| secrets | `secrets-and-data` |
| stable-truth-replaceable-machinery | `ownership-and-portability` |
| testing-and-verification | `testing-and-evidence` |
| versioning-and-compatibility | `versions-and-discovery` |
| visual-fidelity-and-composition | `design-fidelity` |
| worker-contract | `orchestration` |

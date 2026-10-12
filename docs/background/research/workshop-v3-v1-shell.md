# Workshop v3 inside a V1 shell

Status: non-normative, generalized reported case study. Recorded 2026-09-13
by Codex from the repository owner's explicit contribution request and the
referenced discussion, “Research Figma Implementation Workflow.”

## Reported incident

In Project Worlds, agents had the correct canonical Figma authority and
faithfully implemented screens, but carried an untested assumption that the
inherited V1 shell should survive. The reported result was Workshop v3 content
inside V1 architecture: locally correct implementation that missed the intended
structural redesign. The owner clarified that the design should inform the
frontend bones, with valid product behavior preserved independently.

## Evidence and limits

The owner supplied this account and requested its use as motivating provenance.
The discussion contains relayed implementation reports and assistant diagnoses;
those are attributed reports, not independent runtime verification. This library
change did not inspect the Worlds checkout, live application, or complete Figma
family. Exact visual fidelity, causal completeness, and a successful subsequent
repair remain UNVERIFIED here. No private conversation identifiers, design file
identifiers, screenshots, personal context, or private topology are published.

## Interpretation and reusable correction

The working interpretation is that preserving the inherited shell became an
implicit requirement. Accurate reference retrieval could not challenge that
premise because it was never made explicit. A pre-execution comparison of the
canonical family's structure and any preservation decision could have challenged
it; that is a counterfactual opportunity, not proof the incident would have been
prevented.

Classify the inherited shell as ASSUMED, distinguish authority from observation
and interpretation, and ask what evidence would make preservation wrong. Compare
the family before committing to shared architecture. Keep UNKNOWN if that check
does not resolve intent. Existing code demonstrates behavior; it does not grant
itself design authority.

The normative lesson lives in
[Assume UNKNOWN](../../../contracts/core/ASSUME_UNKNOWN.md). This case study grants
no authority to rewrite another project.

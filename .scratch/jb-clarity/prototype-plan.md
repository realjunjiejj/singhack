# JB Clarity UI prototype plan

**Status:** ready-for-agent

## Question

Which desktop information architecture lets Priscilla move from the Priority Queue to an evidence-backed, approved Meeting Brief in under 60 seconds?

This is a UI prototype. It evaluates structure, hierarchy, progressive disclosure, and the golden path. It does not validate production architecture, analytics correctness, persistence, or model integration.

## Shape

- Create one clearly marked throwaway prototype route because no application route currently exists.
- Render three structurally different variants selected by `?variant=A`, `?variant=B`, or `?variant=C`.
- Add a floating bottom-centre variant switcher with pointer and keyboard navigation.
- Use representative Hartono data from the supplied dataset; stub interaction state in memory.
- Provide one project command that starts the prototype.
- Surface relevant state after every interaction: selected case, evidence pane, stress assumption, Meeting Brief edit state, and approval state.

## Variants

### Variant A: Command centre

A persistent three-column desktop composition: Priority Queue on the left, active Client Case in the centre, and contextual evidence or Meeting Brief on the right. The primary affordance is moving through the case without leaving the workspace.

### Variant B: Morning brief

A narrative, ranked briefing feed that explains why each client matters. Opening Hartono transitions into a focused case workspace with a clear breadcrumb back to the Book. The primary affordance is rapid scanning and progressive deepening.

### Variant C: Relationship ledger

A dense client roster organised around financial Anticipatory Signals, Open Loops, and Governance Clocks. Selecting Hartono opens a dossier-style detail panel. The primary affordance is connecting financial risk with relationship memory.

The variants must disagree about structure and primary affordance, not merely color or typography.

## Required Hartono walkthrough

1. Begin on the Book and identify Hartono's Client Case and Priority Rationale.
2. Open the case and distinguish historical-resolved LTV status from present conditions.
3. Reveal the Evidence Chain for the breach and its resolution.
4. Adjust the bounded collateral stress assumption and observe recalculated state.
5. Prepare an editable Meeting Brief that includes the family constraint and property need.
6. Approve the draft and show the resulting Case Resolution.

## Evaluation

Evaluate each variant against:

- Time to identify whom to contact and why
- Clarity of Urgency versus Confidence
- Ability to understand compound financial and relationship signals
- Ease of reaching and leaving the Evidence Chain
- Visibility of uncertainty and historical-versus-current status
- Ease of preparing and approving the Meeting Brief
- Suitability for a calm, premium private-banking workbench
- Ability to explain the interface during a short live demo

Record the winning structure, elements borrowed from other variants, and the reason. Promote the validated decisions into the production implementation; preserve the full prototype as a primary source on a throwaway branch.

## Completion Criteria

- All three variants are reachable by URL and the floating switcher.
- The variants are structurally different.
- The Hartono walkthrough is operable in every variant without persistence or external services.
- A non-developer can compare variants using the evaluation criteria.
- The repository documents one command to start the prototype.
- The result records a winner and the decision it settles before production UI work begins.

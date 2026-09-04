# Agent instructions

## Agent skills

### Issue tracker

Work is specified in GitHub Issues for `realjunjiejj/singhack`. Read `docs/agents/issue-tracker.md` before creating, claiming, or completing a ticket.

### Triage labels

Use the repository's canonical agent-readiness labels. Read `docs/agents/triage-labels.md` before changing a ticket status.

### Domain docs

This is a single-context repository. Before changing JB Clarity behavior or vocabulary, read `CONTEXT.md` and every relevant decision in `docs/adr/`; see `docs/agents/domain.md`.

## JB Clarity work

- **Current phase:** prototype implementation. The separate UI-comparison prototype was deliberately skipped; the specification selects the Command Centre information architecture directly.
- Before implementation, read the assigned brief: `BUILDER-1-INTELLIGENCE-ENGINE.md` or `BUILDER-2-RM-WORKBENCH.md`.
- `.scratch/jb-clarity/spec.md` is the finalized local behavioral source of truth.
- The shared integration boundary already exists at `contracts/workbench.schema.json`. `artifacts/workbench.fixture.json` is Builder 2's temporary input; Builder 1 replaces it with the generated `artifacts/workbench.json` without changing the presentation contract.
- Read `.scratch/jb-clarity/infrastructure-state-prototype.html` from branch `prototype/infrastructure-state` when changing schema versioning, artifact adoption, Meeting Brief approval, or Case Resolution behavior. It records the state invariants agreed before implementation and is intentionally kept off `main`.
- If the specification is published as a GitHub issue, the published issue becomes authoritative.
- For dataset interpretation, read `singhacks-jb-wealth-intelligence/README.md` and `singhacks-jb-wealth-intelligence/docs/DATA_DICTIONARY.md`. Treat `event_log.csv` as the Controlled Event Source for 2026 events.
- Preserve the separation between deterministic analytics, Evidence Packets, presentation, and optional language generation.
- Use the glossary's canonical terms in code, tests, UI copy, and documentation.
- Implement only the assigned vertical slice. Treat unrelated working-tree changes as user-owned.

## Completion

A ticket is complete only when its acceptance criteria pass, relevant tests have been run, and the ticket records verification evidence and any remaining uncertainty.

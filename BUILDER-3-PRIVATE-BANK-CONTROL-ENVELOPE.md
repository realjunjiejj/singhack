# Builder 3 — Private-Bank Control Envelope

## Assignment

Build a bank-sandbox vertical slice around AAActual Intelligence that proves one Client Case can move through authenticated access, client-level authorization, data minimisation, bounded language preparation, audit, and explicit Relationship Manager (RM) approval.

Preserve the existing product core:

```text
governed source data
  → deterministic analytics and Safety Overrides
  → versioned Evidence Packets
  → optional bounded language
  → RM review and approval
  → existing advisory channels
```

This is a control envelope around the existing Workbench contract. It is not a replacement engine, a generic agent platform, or a claim of regulatory approval.

## Read before editing

Read these files completely, in this order:

1. `AGENTS.md`
2. `CONTEXT.md`
3. `.scratch/jb-clarity/spec.md`
4. every decision under `docs/adr/`
5. `contracts/workbench.schema.json`
6. `docs/research/private-banking-open-source.md`
7. `docs/research/open-source-leverage.md`
8. `BUILDER-1-INTELLIGENCE-ENGINE.md`
9. `BUILDER-2-RM-WORKBENCH.md`

Follow `docs/agents/issue-tracker.md` before claiming or completing implementation tickets. If a published GitHub issue differs from this brief, the published issue is authoritative.

## Required outcome

A reviewer must be able to run a local bank-sandbox profile and observe all of the following:

1. Priscilla authenticates through an OIDC-compatible identity boundary.
2. The server—not the browser—checks whether she may access the requested client, Client Case, Evidence Packet, and Guided Action.
3. A cross-client or unassigned-client request is denied by default and recorded.
4. Only the minimum authorised Evidence Packet fields cross into an optional language boundary.
5. Sensitive content is excluded from telemetry and redacted before any model egress.
6. Every view, Guided Action, generation request, edit, approval, dismissal, denial, and export produces a correlated application audit event.
7. Operational lineage connects source version, engine/config version, Workbench artifact, Evidence Packet, and generated draft.
8. The RM must explicitly approve the current Meeting Brief revision; no route sends a client message or executes a transaction.
9. The existing offline demonstration continues to work without the control-plane services.

Completion means the behavior is implemented and tested. Architecture diagrams or Docker containers alone do not satisfy the assignment.

## Fixed component choices for the first slice

Use the smallest stack that proves the control boundaries:

- **OIDC boundary:** integrate through standard issuer, audience, JWKS, subject, group, and expiry claims. Provide a local Keycloak profile only if it reduces test/setup friction. Production must remain compatible with the bank's existing identity provider.
- **Fine-grained authorization:** use OpenFGA for RM → client → portfolio → Client Case → Evidence Packet relationships and specialist delegation. Do not add OPA in this slice.
- **Audit persistence:** use PostgreSQL application audit events. Enable pgAudit in the sandbox profile for database-level activity. Treat independently controlled WORM/retention storage as a documented production integration, not as implemented by PostgreSQL.
- **Privacy guard:** use Presidio behind a narrow redaction interface for optional model-bound text. Combine it with explicit field allowlists. Presidio is defence in depth and must not be described as complete sensitive-data detection.
- **Observability:** use OpenTelemetry with allowlisted attributes and pseudonymous correlation identifiers. Client names, account identifiers, holdings, tax data, RM notes, Evidence Packets, prompts, and generated text must never enter spans, metrics, baggage, or logs.
- **Lineage:** emit OpenLineage-compatible events for ingestion and Evidence Packet publication. The product Evidence Chain remains the user-facing financial provenance contract.
- **Secrets and keys:** integrate through an interface compatible with the bank's KMS/HSM/secrets platform. Keep local secrets out of Git. OpenBao may be documented or supplied as an optional sandbox profile, but it must not become a second production root of trust by default.

Defer Kafka, Apache Camel, Temporal, MLflow, and Evidently. Add one only through a separate ticket with a demonstrated throughput, connector, durable-workflow, or model-governance requirement.

## Ownership and boundaries

Builder 3 owns:

- the bank-sandbox control-plane service;
- identity-claim validation and request context;
- OpenFGA models, tuples, migration/setup, and authorization tests;
- privacy projection and redaction at the optional model boundary;
- application audit schema, persistence, and correlation;
- payload-safe OpenTelemetry configuration;
- OpenLineage emission and tests;
- local sandbox orchestration and runbook;
- the optional web API adapter required to exercise the slice.

Builder 3 does not own:

- financial formulas, ranking, Safety Overrides, Evidence Packet semantics, or source interpretation;
- browser-side inference or calculation;
- automatic conflict resolution;
- trade, order, email, message, calendar, or CRM execution;
- production identity, HSM, SIEM, WORM storage, network segmentation, or regulatory approval.

Use canonical terms from `CONTEXT.md`. Keep Urgency separate from Confidence. Preserve the versioned Workbench boundary and all existing state invariants.

## Target request path

```text
Next.js Workbench
  → authenticated same-origin API request
  → OIDC token validation
  → OpenFGA authorization check
  → purpose/action allowlist
  → Workbench adapter and Evidence Packet projection
  → optional Presidio redaction
  → bounded language adapter or cached output
  → schema/citation/figure validation
  → RM review and explicit approval

Cross-cutting
  → application audit event
  → payload-safe OpenTelemetry signal
  → OpenLineage run/dataset event where applicable
```

Every denial and failure must fail closed, return a stable error shape, and create an audit event without leaking restricted values.

## Domain authorization model

Represent at least these relations in OpenFGA:

```text
team can include RM or specialist
RM can manage assigned client
client owns portfolio
client has Client Case
Client Case contains Evidence Packet
specialist can review explicitly delegated Client Case
```

Enforce actions separately:

- `view_case`
- `view_evidence`
- `prepare_conversation`
- `edit_brief`
- `approve_brief`
- `delegate_specialist`
- `dismiss_case`
- `export_client_ready`

The server derives object identifiers from validated records. It must not authorize solely from a client, case, or packet identifier supplied by the browser.

## Application audit event

Define one versioned event schema containing at least:

- event ID and schema version;
- UTC timestamp and trusted actor subject;
- actor role/group snapshot;
- action and outcome (`allowed`, `denied`, `failed`);
- client, case, packet, and brief identifiers where authorised;
- purpose and policy decision/reference;
- source snapshot, artifact, rules/config, prompt/template, and model versions when applicable;
- previous and resulting brief revision for edits or approvals;
- correlation/trace ID;
- reason for dismissal, deferral, denial, or failure where required;
- before/after content hashes for mutable RM state, without duplicating restricted content.

Audit events are append-only through the application API. Normal application roles cannot update or delete them. Database audit and external retention are separate layers.

## Data-classification and minimisation rules

Classify and test these transitions:

| Data class | Example | Permitted boundary |
|---|---|---|
| Restricted source | holdings, RM notes, tax position, identifiers | governed ingestion and authorised deterministic engine only |
| Derived restricted | Client Case, Evidence Packet | authorised server and RM Workbench |
| Model-minimised | allowlisted packet claims with necessary identifiers tokenised/redacted | optional bounded language adapter only |
| Generated draft | validated explanation or Meeting Brief | authorised RM review only |
| Approved content | current RM-approved revision | existing advisory channel integration boundary; no send in this slice |
| Audit metadata | actor/action/version/hash/correlation | audit and compliance stores; no copied client narrative |
| Operational telemetry | latency, status, service, pseudonymous correlation | approved observability pipeline; no business payload |

An optional model call must be blocked when projection, redaction, authorization, or output validation fails. Cached validated output remains available where the existing contract supplies it.

## Build sequence

### 1. Contract and threat model

Write the API, authorization, audit-event, telemetry-attribute, and data-classification contracts before implementation. Add a concise threat model covering broken object-level authorization, privilege escalation, prompt injection, data exfiltration, telemetry leakage, replay, stale evidence, cross-environment access, and administrator misuse.

**Complete when:** every later test can name the contract or threat it verifies.

### 2. Identity and authorization seam

Validate OIDC tokens server-side and create the OpenFGA model and local tuples. Implement deny-by-default middleware/dependencies around one read path and one Guided Action path.

**Complete when:** assigned access succeeds; wrong-client, wrong-case, expired-token, missing-token, malformed-token, and unauthorised-action requests fail closed in integration tests.

### 3. Controlled Workbench API

Expose the minimum API needed for the vertical slice. Load data only through the existing Workbench adapter/contract and return authorised projections. Preserve offline artifact mode as a separate documented profile.

**Complete when:** the web UI can complete Queue → Client Case → Evidence Chain → Meeting Brief through the sandbox API without moving financial logic into the service or browser.

### 4. Privacy and bounded-language gate

Create an explicit model-input projection, apply field allowlists, run Presidio/custom recognisers, and send only one Evidence Packet with a fixed task type to a mock language adapter. Validate the structured output, citations, and immutable figures before returning it.

**Complete when:** tests prove restricted fields and adversarial note content cannot cross the model or telemetry boundary, while a valid projected packet produces or retrieves a validated draft.

### 5. Audit, telemetry, and lineage

Persist versioned application events, enable pgAudit for the sandbox database, emit allowlisted OpenTelemetry signals, and emit OpenLineage events for artifact/Evidence Packet publication.

**Complete when:** a single correlation ID reconstructs the authorised request and approval path without storing client content in telemetry or lineage metadata.

### 6. RM approval integration

Exercise existing Meeting Brief revision and approval invariants through the server path. Editing an approved brief must invalidate approval and `conversation-prepared`; approval must bind to the current evidence/artifact version.

**Complete when:** browser and API tests cover prepare → edit → approve → resolve and approve → evidence/version change → invalidated approval.

### 7. Sandbox operations and evidence

Provide reproducible local orchestration, health checks, migrations, seed identities/relationships using synthetic IDs, backup/restore notes, dependency versions, SBOM generation, and a runbook. Update the Target Architecture UI only for controls demonstrated by passing tests; keep all others visibly marked as target controls.

**Complete when:** a clean checkout can run the sandbox profile and verification suite from documented commands, and the evidence is recorded in the implementation issue.

## Required security tests

- horizontal access: RM A cannot view RM B's client, case, packet, brief, or audit content;
- vertical access: RM cannot perform administrator, retention, entitlement, or deployment operations;
- object mismatch: a valid client ID combined with another client's case/packet is denied;
- delegation: specialist access is limited to the delegated case and permitted action;
- token validation: issuer, audience, signature, expiry, not-before, subject, and required claims;
- deny-by-default behavior when OpenFGA, identity, audit persistence, or required policy data is unavailable;
- model boundary: prompt injection in RM notes remains untrusted data and cannot change task, tools, citations, or output schema;
- privacy: restricted content never appears in telemetry, lineage, error messages, or unauthorised responses;
- replay/idempotency: approval and audit writes cannot be duplicated by retry;
- state integrity: approval is invalidated by brief or evidence-version change;
- supply chain: pinned dependencies, vulnerability scan, SBOM, and verified container/source provenance.

## Operational requirements

- Separate local, test, sandbox, and production configuration; no shared credentials or data stores.
- Encrypt transport between every service in the target design. Document where sandbox transport differs.
- Use structured errors and health/readiness probes that reveal no client data.
- Define retention categories and deletion/legal-hold integration points with compliance; do not invent retention periods.
- Record recovery-time and recovery-point targets as unresolved bank decisions unless supplied by stakeholders.
- Document capacity assumptions before adding Kafka, caching, or horizontal scaling.
- Keep the public/synthetic demo clearly separated from any bank-sandbox profile.

## Verification commands and evidence

Add repository-native commands for:

- unit and contract tests;
- API/integration tests;
- authorization-model tests;
- privacy/telemetry leakage tests;
- browser golden path;
- production build;
- dependency/license inventory, vulnerability scan, and SBOM generation;
- sandbox startup, health verification, and teardown.

Record the exact commands, results, relevant logs/screenshots, dependency versions, remaining uncertainty, and unimplemented target controls in the implementation issue before closing it.

## License and reuse rules

Prefer published packages, containers, protocols, and schemas over copied source. Pin exact versions and image digests. Review each repository's `LICENSE`, `NOTICE`, transitive dependencies, supported versions, security policy, release provenance, and vulnerability-response process.

If source code or substantial text is copied, record the repository, commit SHA, files, modifications, license, notices, and attribution in `THIRD_PARTY_NOTICES.md`. “Open source” is not equivalent to approved bank production use.

Use `docs/research/private-banking-open-source.md` as the candidate assessment and source index. Re-verify licenses and releases at implementation time.

## Definition of done

- The bank-sandbox vertical slice runs from a clean checkout.
- Identity is validated and object/action authorization is deny-by-default.
- Cross-client isolation and specialist delegation tests pass.
- One Client Case completes the controlled API path through current-revision RM approval.
- The optional language boundary is allowlisted, redacted, bounded, and output-validated.
- Application audit, pgAudit, OpenTelemetry, and OpenLineage evidence is inspectable and contains no prohibited payloads.
- Existing deterministic engine, Workbench contract, offline demo, Urgency/Confidence separation, Evidence Chain, and approval invariants still pass.
- The UI labels only verified sandbox controls as demonstrated and keeps the remaining controls marked as targets.
- Runbook, threat model, SBOM, licenses/notices, verification evidence, and remaining bank decisions are documented.
- No client communication, trade, transaction, or production-bank claim is introduced.

The slice succeeds when a security or compliance reviewer can trace who accessed which authorised client evidence, under which versioned policy and purpose, through which bounded generation step, to which RM-approved revision—without finding client content in telemetry or an automated path to action.

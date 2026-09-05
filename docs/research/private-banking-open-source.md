# Open-source building blocks for a private-bank operating model

**Research date:** 2026-09-05

**Scope:** Security, scalability, data protection, integration, explainability, and compliance around JB Clarity.
**Conclusion:** Reuse narrow infrastructure components and standards; do not copy a complete wealth-advice application.

## Executive recommendation

JB Clarity already has the right core boundary: deterministic analytics produce a versioned Workbench model and bounded Evidence Packets; optional language generation explains one packet at a time; the RM reviews every Advisory Action. Preserve that architecture. The production path is to put bank-grade controls around it:

1. Federate with the bank's existing identity provider; use **Keycloak** only when an approved self-hosted identity broker is actually needed.
2. Enforce client-, portfolio-, case-, purpose-, and action-level access with **OpenFGA or OPA**. Start with one policy system, selected against the bank's existing entitlement architecture.
3. Use the bank's KMS/HSM and secrets platform; evaluate **OpenBao** only if an approved self-hosted alternative is required.
4. Put **Microsoft Presidio**-style detection and redaction before any optional model call and telemetry export, as defence in depth rather than a privacy guarantee.
5. Instrument services with **OpenTelemetry**, with an explicit prohibition on client content in spans, logs, baggage, or metric labels.
6. Emit **OpenLineage** events from source ingestion through Evidence Packet creation. Trial **Marquez** only as a lineage backend, not as the Evidence Chain itself.
7. Record RM views, Guided Actions, generation requests, evidence versions, edits, approvals, dismissals, and exports in append-only audit events. **pgAudit** can cover PostgreSQL activity, but application-level audit events and approved WORM/immutable retention are still required.
8. Add **Temporal**, **Apache Camel**, or **Kafka** only when real integration and reliability requirements justify their operating cost. Add **MLflow/Evidently** only when optional language generation enters a governed pilot with a defined evaluation set.

No open-source repository makes a system compliant or bank-ready by itself. Bank architecture, cybersecurity, privacy, records-management, legal/compliance, model-risk, and operational-resilience owners must approve the control design, deployment boundary, retention schedule, and evidence needed for assurance. The current repository accurately states that these are target capabilities, not implemented production controls ([ADR 0009](../adr/0009-build-a-guided-desktop-workbench.md)).

## Recommended control envelope

```text
Bank systems / controlled files
  -> versioned integration adapters
  -> validation, reconciliation, and data-quality quarantine
  -> deterministic analytics and Safety Overrides
  -> versioned Evidence Packet
  -> entitlement + purpose + data-minimisation policy gate
  -> optional bounded language generation
  -> schema, citation, and figure-preservation validation
  -> RM review / edit / approve / dismiss
  -> client conversation or bank workflow

Cross-cutting: identity, encryption/secrets, audit, lineage, telemetry, retention
```

Open-source controls must not collapse the existing separation between deterministic analytics, Evidence Packets, presentation, and optional language generation ([ADR 0007](../adr/0007-separate-analytics-presentation-and-language-generation.md)). They also must not allow a model to rank the Book, execute a trade, contact a client, or silently resolve an Evidence Conflict ([ADR 0004](../adr/0004-use-deterministic-prioritisation-and-ai-explanation.md), [ADR 0005](../adr/0005-make-uncertainty-and-ai-grounding-visible.md)).

## Candidate assessment

| Component | What it can contribute | JB Clarity fit and boundary | License and maintenance signal | Decision |
|---|---|---|---|---|
| [Keycloak](https://github.com/keycloak/keycloak) | OIDC/SAML identity brokering and LDAP/Active Directory user federation ([official guide](https://www.keycloak.org/docs/latest/server_admin/)) | Authenticate the RM and specialists; pass stable identity and group claims to the authorization layer. It should not decide client-level entitlement by UI role alone. Prefer the bank's existing IAM platform when one exists. A production deployment needs an HA database/cluster, TLS, protected admin endpoints, monitoring, backups, and rapid patching ([production guide](https://www.keycloak.org/server/configuration-production)). | Apache-2.0; active 2026 release stream ([releases](https://github.com/keycloak/keycloak/releases), [license](https://github.com/keycloak/keycloak/blob/main/LICENSE.txt)). | **Conditional component; strong reference.** |
| [OpenFGA](https://github.com/openfga/openfga) | Relationship-based, fine-grained access checks over users and objects; HTTP/gRPC APIs and production storage options ([concepts](https://openfga.dev/docs/concepts), [repository](https://github.com/openfga/openfga)) | Natural fit for `RM -> client -> portfolio -> Client Case -> Evidence Packet`, team coverage, delegation, and specialist access. Model and test explicit relations; never treat a client ID supplied by the browser as authorization. Authentication defaults to none, TLS must be enabled, and OpenFGA's built-in server access-control feature is explicitly experimental ([configuration](https://openfga.dev/docs/getting-started/setup-openfga/configure-openfga), [access-control warning](https://openfga.dev/docs/getting-started/setup-openfga/access-control)). | Apache-2.0; v1.18.1 released in June 2026, with signed artifacts and SBOMs ([releases](https://github.com/openfga/openfga/releases), [release process](https://github.com/openfga/openfga/blob/main/RELEASES.md)). | **Shortlist for entitlements, behind hardened service access controls.** |
| [Open Policy Agent](https://github.com/open-policy-agent/opa) | General, context-aware policy decisions for APIs ([official API authorization guide](https://www.openpolicyagent.org/docs/http-api-authorization)) | Better fit than a relationship graph when decisions depend mainly on attributes such as role, jurisdiction, purpose, approval state, environment, or permitted Guided Action. Keep policy version and decision result in the audit event. OPA decision logs may contain the full policy input and result, so erase or mask client data before export ([decision-log guidance](https://www.openpolicyagent.org/docs/management-decision-logs)). | Apache-2.0; CNCF graduated project with active 2026 releases ([repository](https://github.com/open-policy-agent/opa), [releases](https://github.com/open-policy-agent/opa/releases)). | **Shortlist for policy gates.** Do not introduce both OPA and OpenFGA without separate proven needs. |
| [OpenBao](https://github.com/openbao/openbao) | Secrets, certificates, keys, signing/HMAC, and encryption-as-a-service; its transit engine does not retain submitted plaintext ([transit docs](https://openbao.org/docs/secrets/transit/)) | Can protect service credentials and support envelope encryption or signing of Evidence Packet hashes. In a bank, use the approved KMS/HSM/secrets service first; do not build a second root of trust casually. OpenBao itself warns that networked software is not a substitute for an offline root CA/HSM ([PKI considerations](https://openbao.org/docs/secrets/pki/considerations/)). | MPL-2.0; active 2026 releases ([repository](https://github.com/openbao/openbao), [releases](https://github.com/openbao/openbao/releases), [license](https://github.com/openbao/openbao/blob/main/LICENSE)). | **Conditional component; adopt the pattern now.** |
| [Presidio](https://github.com/data-privacy-stack/presidio) | Detects, masks, redacts, or anonymises PII using rules, checksums, NLP, and custom recognisers ([docs](https://microsoft.github.io/presidio/), [supported entities](https://microsoft.github.io/presidio/supported_entities/)) | Run before optional model calls, diagnostics export, or non-production fixture creation. Create and test recognisers for the bank's jurisdictions and identifiers. Preserve controlled reversible token mapping only inside an approved boundary if client names must be restored. | MIT; moved from Microsoft's GitHub organisation to Data Privacy Stack and released 2.2.364 in July 2026 ([releases](https://github.com/data-privacy-stack/presidio/releases), [license](https://github.com/data-privacy-stack/presidio/blob/main/LICENSE)). | **Adopt narrowly as defence in depth.** Its docs explicitly say it cannot guarantee detection of all sensitive data. |
| [OpenTelemetry Collector](https://github.com/open-telemetry/opentelemetry-collector) | Vendor-neutral collection, processing, and export of traces, metrics, and logs ([repository](https://github.com/open-telemetry/opentelemetry-collector)) | Trace ingestion, engine execution, policy decisions, generation latency, approval transitions, and failures using pseudonymous correlation IDs. Never export raw Evidence Packets, prompts, generated client text, names, account IDs, holdings, RM notes, or tax data. | Apache-2.0; v0.160.0 released 2 September 2026 with signed artifacts and SBOMs ([official releases](https://github.com/open-telemetry/opentelemetry-collector-releases/releases)). The project warns that telemetry may contain PII and requires secure collector configuration ([security guidance](https://opentelemetry.io/docs/security/)). | **Adopt for observability, with a telemetry data contract.** |
| [OpenLineage](https://github.com/OpenLineage/OpenLineage) and [Marquez](https://github.com/MarquezProject/marquez) | An open event standard for Job, Run, and Dataset lineage; facets can describe inputs, outputs, schemas, versions, quality, source code, and run state ([object model](https://openlineage.io/docs/spec/object-model/), [facets](https://openlineage.io/docs/spec/facets/)). Marquez stores and visualises this metadata. | Emit lineage for controlled source versions, ingestion runs, deterministic rule/config versions, Workbench artifacts, and Evidence Packet IDs. Keep client values out of metadata. The user-facing Evidence Chain remains JB Clarity's versioned domain contract; lineage is operational provenance underneath it. | OpenLineage and Marquez are Apache-2.0. OpenLineage 1.53.0 shipped September 2026 ([releases](https://github.com/OpenLineage/OpenLineage/releases)); Marquez describes itself as active but its last tagged release was 0.50.0 in October 2024 ([repository](https://github.com/MarquezProject/marquez), [releases](https://github.com/MarquezProject/marquez/releases)). | **Adopt the standard; evaluate the backend.** Do not make Marquez mandatory initially. |
| [Temporal](https://github.com/temporalio/temporal) | Durable execution that resumes workflows after process, network, or infrastructure failure ([official docs](https://docs.temporal.io/)) | Useful later for long-running specialist referrals, information requests, approvals, retries, reminders, and Case Resolution. Workflow histories persist payloads, so store authorised opaque references or use approved client-side payload encryption rather than raw Evidence Packets. Self-hosted authentication/authorization and transport security must be deliberately configured. It must not turn the RM approval state into automatic advice or execution. | MIT; v1.31.2 released July 2026 ([repository](https://github.com/temporalio/temporal), [releases](https://github.com/temporalio/temporal/releases), [license](https://github.com/temporalio/temporal/blob/main/LICENSE)). | **Pilot when workflows become asynchronous and durable.** Overkill for the current prototype. |
| [Apache Camel](https://github.com/apache/camel) | Enterprise integration patterns and 350+ connectors for APIs, databases, brokers, and cloud services ([repository](https://github.com/apache/camel)) | Put adapters upstream of the deterministic engine to isolate core-banking, CRM, KYC, document, market/reference, and event-source schemas from the Workbench contract. Each adapter must validate, classify, and quarantine incomplete or contradictory data rather than “cleaning” it silently. | Apache-2.0; long-running project with active 2026 releases ([license](https://github.com/apache/camel/blob/main/LICENSE.txt)). | **Useful integration layer if the bank is Java-oriented; otherwise copy the anti-corruption-layer pattern.** |
| [Apache Kafka](https://github.com/apache/kafka) | Distributed event streaming for high-throughput, replayable pipelines ([repository](https://github.com/apache/kafka)) | Appropriate only if the bank needs near-real-time signals, multiple consumers, ordered replay, and independently scalable ingestion. For nightly snapshots or a small Book, scheduled idempotent batch processing is simpler. Kafka does not provide business audit immutability or exactly-once end-to-end correctness by itself. | Apache-2.0; active Apache project ([license](https://github.com/apache/kafka/blob/trunk/LICENSE)). | **Conditional scale component, not a default dependency.** |
| [pgAudit](https://github.com/pgaudit/pgaudit) | Detailed PostgreSQL session and object audit logging through PostgreSQL's logging facility | Covers database reads/writes and privileged activity; pair it with application events that capture actor, action, client/case, evidence/config/model versions, policy result, before/after hashes, timestamp, correlation ID, and reason. Ship records to retention-controlled storage outside the application's admin boundary. | PostgreSQL License; active branches for PostgreSQL 14–18 and 2025/2026 repository activity ([repository](https://github.com/pgaudit/pgaudit), [license](https://github.com/pgaudit/pgaudit/blob/main/LICENSE)). | **Strong database audit component, not the whole audit trail.** |
| [MLflow](https://github.com/mlflow/mlflow) | Experiment tracking, model/prompt lifecycle, tracing, evaluation, and registry capabilities ([registry docs](https://github.com/mlflow/mlflow/blob/master/docs/docs/classic-ml/model-registry/index.mdx)) | Useful only for governed language-generation experiments: record approved model/prompt/template version, evaluation dataset version, metrics, and promotion decision. Do not send unredacted client prompts to its tracking store. It is unnecessary for deterministic Priority Rationale. | Apache-2.0; active 2026 release stream ([releases](https://github.com/mlflow/mlflow/releases), [license](https://github.com/mlflow/mlflow/blob/master/LICENSE.txt)). | **Defer until a model-governance pilot.** |
| [Evidently](https://github.com/evidentlyai/evidently) | Offline and live tests/monitoring for tabular and LLM systems, including custom metrics and exported reports | Potentially useful for regression tests over generated explanations: citation coverage, unsupported-claim rate, figure preservation, refusal behaviour, language fidelity, and human acceptance. These deterministic measures should be primary; “LLM judge” scores are supplemental evidence only. Its own comparison says the OSS UI lacks authentication, RBAC, alerts, scheduling, and a scalable backend ([official comparison](https://docs.evidentlyai.com/faq/oss_vs_cloud)); do not expose that UI as a bank control plane. | Apache-2.0; v0.7.21 released March 2026 ([repository](https://github.com/evidentlyai/evidently), [releases](https://github.com/evidentlyai/evidently/releases)). | **Optional headless evaluation library; not a compliance control.** |

## What should remain JB Clarity's own code

The repositories above do not understand the challenge's financial semantics. Keep these in the deterministic engine and its tests:

- aggregate every portfolio owned by the client before testing concentration, liquidity, mandate, tax, or objective mismatch;
- use `instruments.underlying_reference` for structured-product look-through rather than trusting the top-level asset-class label;
- preserve disagreements between RM notes and calculated evidence as visible Evidence Conflicts;
- distinguish private-market reporting lag from data corruption while exposing the valuation date and Confidence effect;
- quarantine and disclose real-world imperfections, assumptions, missing joins, duplicate records, stale values, and unsupported conclusions;
- version formulas, thresholds, configuration, source snapshots, Controlled Event Source entries, and Evidence Packets;
- preserve claim-level evidence references and figures through language generation and translation;
- require explicit RM review for every Advisory Action and Client-Ready View.

OpenLineage can record that these transformations ran; it cannot supply or validate their private-banking meaning. MLflow or Evidently can measure optional generated language; they must not replace deterministic calculations or the Evidence Chain.

## Audit design: use layers, not an “immutable database” claim

A credible audit trail needs at least three layers:

1. **Application events:** who viewed evidence, requested a Guided Action, changed a Conversation Plan, approved/dismissed a case, exported content, or invoked a specialist workflow—and which immutable evidence, rule, policy, prompt, and model versions were involved.
2. **Platform/database audit:** administrative access, entitlement changes, secret/key use, database reads/writes, deployments, and configuration changes.
3. **Retention and independent verification:** append-only ingestion, restricted deletion, legal-hold/retention policy, periodic signed checkpoints or hashes, and storage controlled separately from application administrators.

Do not claim that a normal append-only table is immutable. Conversely, do not add a specialist ledger merely for presentation value. [immudb](https://github.com/codenotary/immudb) offers cryptographic verification, but current versions use Business Source License 1.1 with use restrictions and a four-year delayed change to Apache-2.0 ([license](https://github.com/codenotary/immudb/blob/master/LICENSE)); it is source-available, not a clean open-source recommendation for incorporation. **Reject it unless bank legal/procurement explicitly approves the exact use and version.**

[Sigstore Rekor](https://github.com/sigstore/rekor) is Apache-2.0 and provides a tamper-resistant transparency log for software-supply-chain metadata, not confidential wealth-advice records. Rekor v1 is in maintenance mode while v2 is being developed, and a public transparency log must never receive client data ([repository status and purpose](https://github.com/sigstore/rekor)). Use Sigstore for signed build provenance if the bank adopts it; treat its Merkle-log design as a pattern, not the application audit store.

## Practical adoption sequence

### Prototype narrative now

- Show the control envelope and mark every unbuilt control as target architecture.
- Add a concise data-flow classification: raw/restricted source data, derived Evidence Packets, redacted model input, generated draft, approved client-ready content, audit metadata.
- Demonstrate stable IDs, evidence/config versions, claim citations, uncertainty, and explicit RM approval using synthetic data.
- Do not describe the public Vercel prototype as a bank deployment.

### Bank sandbox / pilot

- Integrate the bank identity provider and one entitlement/policy service; deny by default and test cross-client isolation.
- Use approved KMS/HSM/secrets, private networking, encryption in transit/at rest, environment separation, and automated key/credential rotation.
- Build one source adapter with reconciliation and quarantine; emit OpenLineage events.
- Establish the audit event schema, external retention sink, time synchronisation, access review, and incident investigation path.
- Redact and minimise one Evidence Packet before a model call; prove that raw client data and generated content do not enter telemetry.
- Run adversarial authorization, prompt-injection, data-exfiltration, replay, stale-data, conflict, and fail-closed tests.

### Scale only after evidence

- Introduce Temporal for durable human workflows, Camel for a growing adapter estate, or Kafka for proven event-streaming/replay needs.
- Add MLflow/Evidently when there is a representative, privacy-approved evaluation corpus and defined release thresholds.
- Complete dependency pinning, SBOM and artifact-signature verification, vulnerability response, HA/DR, backup/restore, capacity, recovery-time/recovery-point, penetration testing, supplier-risk, and exit plans for every component.

## Copying and licensing rule

Prefer supported packages, containers, APIs, and published standards over copying source files. If code is copied, pin the exact commit, review the license and `NOTICE`, record modifications, preserve required notices, scan dependencies, and create a third-party inventory. Apache-2.0, MIT, MPL-2.0, and the PostgreSQL License have different notice and distribution obligations; “open source” is not equivalent to “approved for bank production.” This report is technical research, not legal advice.

## Final answer to “is there a repository we can copy?”

There is no credible single repository to copy into a private bank. The strongest realistic combination is:

- bank IAM (Keycloak only if needed) + OpenFGA **or** OPA for least-privilege access;
- bank KMS/HSM/secrets (OpenBao only if approved) for keys and credentials;
- Presidio as a non-guaranteed privacy guardrail before model or telemetry egress;
- OpenTelemetry for payload-free operational observability;
- OpenLineage for source-to-Evidence-Packet provenance;
- application audit events + pgAudit + independently retained/WORM records;
- Temporal/Camel/Kafka only when workflow, integration, or throughput requirements demand them;
- MLflow/Evidently only for the optional language layer's governed evaluation.

This gives JB Clarity a believable production evolution while preserving its strongest proposition: deterministic financial reasoning, inspectable Evidence Chains, bounded generation, and the RM in control.

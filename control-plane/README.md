# Control envelope — AAActual Intelligence

The bank-sandbox control plane from `BUILDER-3-PRIVATE-BANK-CONTROL-ENVELOPE.md`.
It wraps the existing Workbench artifact with identity, object-level
authorization, data minimisation, audit and RM approval.

It owns **control** decisions only. It never ranks, scores, recalculates or
reinterprets a Client Case — that stays in `engine/`, and the boundary is
enforced by construction: this package reads the artifact and decides who may
see it.

## Commands

```bash
python -m pip install -e "control-plane[dev]"
```

```bash
python -m pytest control-plane/tests
```

87 tests. No containers, no network, no credentials.

## What is demonstrated, and what is not

This matters more than the feature list. Per Step 7 of the brief, only controls
proven by a passing test are described as demonstrated.

| Control | State | Evidence |
|---|---|---|
| OIDC token validation — issuer, audience, signature, `exp`, `nbf`, required claims, `alg` confusion, `alg: none` | **Demonstrated** | `test_identity.py`, 17 tests |
| Deny-by-default object authorization, horizontal isolation | **Demonstrated** | `test_authorization.py` |
| Object mismatch — valid client id paired with a foreign case or packet | **Demonstrated** | `test_authorization.py`, `test_gateway.py` |
| Specialist delegation, scoped per case, revocable | **Demonstrated** | `test_authorization.py` |
| Purpose allowlist per action | **Demonstrated** | `test_authorization.py` |
| Fail closed when authorization or audit is unavailable | **Demonstrated** | `test_gateway.py` |
| Model-input projection — allowlist, evidence items excluded | **Demonstrated** | `test_projection.py` |
| Generated-output validation — citations, figures, structure | **Demonstrated** | `test_projection.py`, `test_gateway.py` |
| Append-only, hash-chained audit incl. denials and failures | **Demonstrated** | `test_audit.py` |
| Correlation id reconstructs one request's path | **Demonstrated** | `test_gateway.py` |
| Approval bound to brief revision **and** artifact version | **Demonstrated** | `test_gateway.py` |
| Telemetry attribute allowlist, pseudonymous correlation | **Demonstrated** | `test_gateway.py` |
| No send / trade / order route exists | **Demonstrated** | `test_gateway.py` |
| Keycloak or another hosted identity provider | **Target** | `JwksKeyResolver` implements the JWKS path; no issuer is run here |
| OpenFGA server | **Target** | model authored in `contracts/authorization-model.fga`; evaluated locally by `authorization.py` |
| PostgreSQL + pgAudit | **Target** | audit persists to JSON lines in this slice |
| Presidio | **Target** | `Redactor` is the interface; the shipped recognisers are a small named pattern set, not complete detection |
| OpenTelemetry exporter, OpenLineage emission | **Target** | `TelemetrySink` enforces the attribute allowlist; nothing is exported |
| HTTP API and web integration | **Target** | the decision path is a library; no transport layer yet |
| WORM retention, SBOM, container provenance, environment separation | **Target** | see the threat model |

The hash chain detects tampering by an application-level actor. It is **not**
immutability — that needs WORM storage and independent retention, and the
threat model says so rather than implying this covers it.

## The path

```text
token → identity → authorization → purpose → projection → generation
      → output validation → RM review → explicit approval
```

Each step can only narrow. Every outcome — allowed, denied, failed — writes one
audit event before the caller hears anything, so an access log that only
records successes cannot happen.

## Design decisions worth knowing

**Denial and non-existence are the same answer.** `AuthorizationError` carries
one message for both. "Case X forbidden" versus "case X not found" is an
enumeration oracle; the precise reason goes to the audit record, not the caller.

**The server resolves identifiers.** A request naming a client you are assigned
to, paired with a case belonging to someone else, is refused. Browser-supplied
identifiers are a request, never proof. This is the brief's headline rule and
the highest-impact API risk.

**Projection is an allowlist.** A field added to the Workbench contract next
month is dropped by default. `items` is explicitly denied because evidence
items carry source record keys and RM note excerpts — the model gets
engine-authored claim statements and citation identifiers, and resolves nothing
itself.

**Delegation is recorded on the case, not the client**, so it cannot widen to
that client's other cases, and revoking it takes effect immediately.

**Approval binds to what was approved.** Editing the brief or regenerating the
artifact both invalidate it. An approval is a statement about specific content,
not a permanent flag.

## Contracts

| File | Purpose |
|---|---|
| `contracts/authorization-model.fga` | Relationship model, in OpenFGA DSL |
| `contracts/audit-event.schema.json` | Audit event, JSON Schema validated in tests |
| `contracts/data-classification.json` | Data classes, model-input allowlist, telemetry allowlist |
| `../docs/THREAT-MODEL.md` | Eleven threats, each naming its control and test, or marked unmitigated |

## Not implemented, and not claimed

No HTTP transport, no hosted identity provider, no OpenFGA server, no
PostgreSQL, no Presidio models, no OTel exporter, no OpenLineage, no sandbox
orchestration, no SBOM. Token replay inside the validity window is not
prevented. Cross-environment separation and administrator misuse are named in
the threat model as unmitigated.

This is the decision layer, tested. The managed infrastructure around it is the
next slice.

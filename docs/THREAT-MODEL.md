# Threat model — AAActual Intelligence control envelope

Scope: the path from an authenticated Relationship Manager request to an
RM-approved Meeting Brief revision. The deterministic engine and the Workbench
contract are trusted inputs to this model; how they are computed is covered by
the engine's own tests.

Every threat below names the control that addresses it and the test that
proves the control works. A threat with no test is listed as **unmitigated**
rather than described as handled.

## Trust boundaries

```text
browser  ──▶  ① token validation  ──▶  ② object authorization  ──▶  ③ purpose allowlist
                                                                        │
                                              ④ projection + redaction  ▼
                                                                   language adapter
                                                                        │
                                              ⑤ output validation       ▼
                                                                   RM review + approval

cross-cutting: ⑥ audit   ⑦ telemetry allowlist
```

The browser is untrusted. RM notes are untrusted **data**, never instructions.
The language adapter is untrusted output until validated.

## Threats

### T1 — Broken object-level authorization

An RM requests a Client Case, Evidence Packet or brief belonging to a client
they are not assigned. This is the highest-likelihood, highest-impact failure
in an API of this shape.

**Control.** The server resolves every object identifier against stored
records and checks the relationship graph before reading anything. A packet is
reachable only through its parent case. Browser-supplied identifiers are
treated as a request, never as proof.

**Tested by** `test_authorization.py::test_an_rm_cannot_reach_another_rms_client`,
`::test_a_packet_from_another_case_is_denied`,
`::test_a_valid_client_paired_with_a_foreign_case_is_denied`.

### T2 — Privilege escalation through delegation

A specialist delegated one Client Case reaches a second case, or performs an
action delegation never granted.

**Control.** Delegation is recorded on the case, not the client, so it cannot
widen to the client's other cases. Delegated subjects receive view and prepare
actions only; `edit_brief`, `approve_brief`, `delegate_specialist`,
`dismiss_case` and `export_client_ready` remain with the assigned RM.

**Tested by** `test_authorization.py::test_a_specialist_reaches_only_the_delegated_case`,
`::test_a_specialist_cannot_approve_or_export`.

### T3 — Forged, expired or replayed identity

A caller presents a token from another issuer, for another audience, past
expiry, before its not-before, unsigned, or signed with the wrong key.

**Control.** Signature verified against the issuer's JWKS by key id; issuer,
audience, `exp`, `nbf` and required claims all checked; `alg: none` and
symmetric algorithms rejected so a public key cannot be used as an HMAC secret.

**Tested by** `test_identity.py` — nine cases covering each rejection.

**Partially unmitigated.** Token replay within the validity window is not
prevented. Production needs short lifetimes plus DPoP or mTLS binding. Recorded
as a bank decision, not implemented here.

### T4 — Prompt injection through RM notes

A note contains text instructing the model to ignore its task, cite something
else, or emit restricted content. RM notes are client-influenced input.

**Control.** The model never receives note text. Projection is an allowlist:
packet metadata, claim statements and citation identifiers only. Evidence
items — which carry note excerpts and source record keys — are denied by
classification. Task type is fixed by the caller, never by content. Output is
validated for schema, citation membership and figure preservation before use.

**Tested by** `test_projection.py::test_evidence_items_never_reach_the_model`,
`::test_injected_instructions_in_a_claim_do_not_change_the_task`,
`test_gateway.py::test_output_citing_an_unknown_item_is_rejected`.

**Residual risk.** A claim *statement* is model-visible by design, and the
engine derives statements partly from note text. Statements are engine-authored
sentences rather than raw note content, which narrows but does not eliminate
the channel. Presidio is the intended defence in depth and is not installed
here.

### T5 — Data exfiltration through the language boundary

Restricted fields cross into a model request.

**Control.** Projection is deny-by-default: any field not named in
`data-classification.json` is dropped, including fields added to the Workbench
contract later. A projection failure blocks the call rather than degrading to
sending more.

**Tested by** `test_projection.py::test_an_unknown_field_added_later_is_dropped`,
`::test_projection_failure_blocks_the_call`.

### T6 — Telemetry and log leakage

Client names, holdings, note text, prompts or generated drafts reach spans,
metrics or logs.

**Control.** Telemetry attributes are allowlisted; anything else is rejected
before emission. Errors use stable codes and never echo the requested values.

**Tested by** `test_telemetry.py::test_only_allowlisted_attributes_are_emitted`,
`::test_client_content_is_rejected`, `test_gateway.py::test_denial_reveals_nothing_about_the_target`.

### T7 — Stale evidence approved as current

An RM approves a brief; the artifact is regenerated; the approval silently
continues to apply to superseded evidence.

**Control.** Approval binds to the artifact version and brief revision recorded
at approval time. A change to either invalidates the approval.

**Tested by** `test_gateway.py::test_approval_is_invalidated_by_an_artifact_change`,
`::test_approval_is_invalidated_by_a_later_edit`.

### T8 — Audit gaps and tampering

A denial leaves no trace, or a record is altered after the fact.

**Control.** Every decision writes one event, including `denied` and `failed`.
The store exposes append and read only; there is no update or delete path.
Records are hash-chained so a removal or edit breaks verification.

**Tested by** `test_audit.py::test_a_denial_is_recorded`,
`::test_the_log_has_no_mutation_path`, `::test_tampering_breaks_the_chain`.

**Unmitigated.** True immutability requires WORM storage and independent
retention. The hash chain detects tampering by an application-level actor; it
does not stop an administrator with database access. Documented as a production
integration.

### T9 — Fail-open when a dependency is unavailable

The authorization or audit backend is down and the request proceeds anyway.

**Control.** Both are required. If the relationship store cannot answer, or the
audit write fails, the request is denied. There is no degraded read path.

**Tested by** `test_gateway.py::test_an_unavailable_authorization_store_denies`,
`::test_a_failed_audit_write_denies_the_request`.

### T10 — Cross-environment access

Sandbox credentials or data reach production, or the reverse.

**Unmitigated in this slice.** Environment separation, distinct credentials and
distinct stores are operational requirements. No production profile exists.

### T11 — Administrator misuse

An operator with infrastructure access reads client data or alters audit
history.

**Unmitigated in this slice.** Requires privileged-access management, separation
of duties and independent audit retention. Named here so it is not mistaken for
covered.

## Out of scope

No route sends a client message, places an order, or executes a transaction.
The approved revision stops at the advisory channel boundary. That is a
property of the design, not a control that can be switched off, and it is
tested by `test_gateway.py::test_no_action_can_send_or_execute`.

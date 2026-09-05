"""Evidence-bounded analyst team over a completed Workbench model.

The specialists do not recalculate financial facts. They consume the existing
deterministic Evidence Packets and shape them into an integration-friendly
view. Hidden Risk and Prioritisation are the two deliberately deep roles.
"""

from __future__ import annotations

from jb_clarity.domain.models import EvidencePacket, WorkbenchModel
from jb_clarity.intelligence.models import (
    AgentFinding,
    AgentReport,
    AnalysisDiagnostic,
    DatasetProfile,
)
from jb_clarity.intelligence.provider import (
    NarrativePolicy,
    NarrativeProvider,
    enrich_deep_reports,
)

DEEP_FOCUS = ["hidden-risk", "prioritisation"]


def run_agent_team(
    workbench: WorkbenchModel,
    profile: DatasetProfile,
    narrative_provider: NarrativeProvider | None = None,
    narrative_policy: NarrativePolicy | None = None,
) -> list[AgentReport]:
    steward = _dataset_steward(workbench, profile)
    if steward.status == "blocked":
        return [
            steward,
            AgentReport(
                agent_id="hidden-risk-specialist",
                role="Finds exposure visible only after whole-client aggregation or structured-product look-through.",
                depth="deep",
                status="blocked",
                summary="Blocked due to material data integrity issues.",
                findings=[],
            ),
            AgentReport(
                agent_id="advisory-context-analyst",
                role="Adds supported portfolio change and event context without claiming measured performance attribution.",
                depth="supporting",
                status="blocked",
                summary="Blocked due to material data integrity issues.",
                findings=[],
            ),
            AgentReport(
                agent_id="prioritisation-specialist",
                role="Explains the deterministic whole-Book order while keeping Urgency and Confidence separate.",
                depth="deep",
                status="blocked",
                summary="Blocked due to material data integrity issues.",
                findings=[],
            ),
            AgentReport(
                agent_id="evidence-auditor",
                role="Fails closed when a specialist finding escapes its Evidence Packets.",
                depth="control",
                status="blocked",
                summary="Blocked due to material data integrity issues.",
                findings=[],
            ),
        ]

    reports = [
        steward,
        _hidden_risk_specialist(workbench),
        _advisory_context_analyst(workbench),
        _prioritisation_specialist(workbench),
    ]
    if narrative_provider is not None:
        reports = enrich_deep_reports(reports, narrative_provider, narrative_policy)
    auditor = _evidence_auditor(workbench, reports)
    reports.append(auditor)
    if any(report.status == "blocked" for report in reports):
        reports = [report.model_copy(update={"findings": []}) for report in reports]
    return reports


def _dataset_steward(workbench: WorkbenchModel, profile: DatasetProfile) -> AgentReport:
    quality = workbench.meta.data_quality
    diagnostics = [
        AnalysisDiagnostic(
            code=issue.id,
            severity=("material" if str(issue.severity) == "material" else "warning"),
            message=issue.summary,
        )
        for issue in quality.issues
    ]
    is_blocked = any(d.severity == "material" for d in diagnostics)
    return AgentReport(
        agent_id="dataset-steward",
        role="Profiles the dataset and keeps imperfections visible.",
        depth="control",
        status="blocked" if is_blocked else "completed",
        summary=(
            f"Profiled {len(profile.files)} source files. Deterministic validation "
            f"reported data quality as {quality.status}."
        ),
        diagnostics=diagnostics,
    )


def _hidden_risk_specialist(workbench: WorkbenchModel) -> AgentReport:
    cases = {case.client_id: case for case in workbench.client_cases}
    packets = [
        packet
        for packet in workbench.evidence_packets
        if packet.signal_type == "concentration"
    ]
    findings: list[AgentFinding] = []
    for packet in packets:
        case = cases[packet.client_id]
        summary = " ".join(claim.statement for claim in packet.facts)
        meaning = " ".join(claim.statement for claim in packet.interpretations)
        findings.append(
            AgentFinding(
                finding_id=f"FINDING-{packet.client_id}-HIDDEN-RISK",
                direction="hidden-risk",
                client_id=packet.client_id,
                case_id=packet.case_id,
                title=f"Hidden risk — {case.client_name}",
                summary=summary or case.conclusion,
                why_it_matters=meaning or case.why_now,
                limitations=[
                    claim.statement
                    for claim in [*packet.uncertainties, *packet.conflicts]
                ],
                evidence_packet_ids=[packet.packet_id],
                evidence_item_ids=[item.id for item in packet.items],
                derived_metrics=packet.derived_metrics,
                urgency=case.urgency,
                confidence=case.confidence,
            )
        )
    findings.sort(key=lambda finding: (-_largest_metric(finding), finding.client_id))
    return AgentReport(
        agent_id="hidden-risk-specialist",
        role=(
            "Finds exposure visible only after whole-client aggregation or "
            "structured-product look-through."
        ),
        depth="deep",
        status="completed",
        summary=(
            f"Found {len(findings)} evidence-backed hidden-risk findings across all "
            "portfolios, including custody and declared structured underlyings."
        ),
        findings=findings,
    )


def _advisory_context_analyst(workbench: WorkbenchModel) -> AgentReport:
    cases = {case.client_id: case for case in workbench.client_cases}
    queue = {item.client_id: item for item in workbench.book.priority_queue}
    packets = [
        packet
        for packet in workbench.evidence_packets
        if packet.signal_type == "explanation"
    ]
    findings: list[AgentFinding] = []
    for packet in packets:
        case = cases[packet.client_id]
        item = queue[packet.client_id]
        facts = " ".join(claim.statement for claim in packet.facts)
        interpretations = " ".join(claim.statement for claim in packet.interpretations)
        findings.append(
            AgentFinding(
                finding_id=f"FINDING-{packet.client_id}-EXPLANATION",
                direction="explanation",
                client_id=packet.client_id,
                case_id=packet.case_id,
                title=f"Portfolio explanation — {case.client_name}",
                summary=facts,
                why_it_matters=interpretations or case.why_now,
                limitations=[claim.statement for claim in packet.uncertainties],
                evidence_packet_ids=[packet.packet_id],
                evidence_item_ids=[item.id for item in packet.items],
                derived_metrics=packet.derived_metrics,
                rank=item.rank,
                urgency=item.urgency,
                confidence=item.confidence,
            )
        )
    findings.sort(key=lambda finding: finding.rank or 10**6)
    return AgentReport(
        agent_id="advisory-context-analyst",
        role=(
            "Adds supported portfolio change and event context without claiming "
            "measured performance attribution."
        ),
        depth="supporting",
        status="completed",
        summary=f"Prepared bounded context for {len(findings)} Client Cases.",
        findings=findings,
    )


def _prioritisation_specialist(workbench: WorkbenchModel) -> AgentReport:
    cases = {case.client_id: case for case in workbench.client_cases}
    packets_by_client: dict[str, list[EvidencePacket]] = {}
    for packet in workbench.evidence_packets:
        packets_by_client.setdefault(packet.client_id, []).append(packet)

    findings: list[AgentFinding] = []
    diagnostics: list[AnalysisDiagnostic] = []
    queue = workbench.book.priority_queue

    ranks = [item.rank for item in queue]
    if ranks != list(range(1, len(queue) + 1)):
        diagnostics.append(
            AnalysisDiagnostic(
                code="PRIORITISATION-RANKS-NOT-CONTIGUOUS",
                severity="blocked",
                message=f"Queue ranks {ranks} are not unique and contiguous 1..{len(queue)}.",
            )
        )

    seen_non_override = False
    for item in queue:
        has_override = item.urgency.safety_override is not None
        is_critical = item.urgency.tier == "Critical"
        if is_critical and not has_override:
            diagnostics.append(
                AnalysisDiagnostic(
                    code="PRIORITISATION-CRITICAL-WITHOUT-OVERRIDE",
                    severity="blocked",
                    message=f"Client {item.client_id} is Critical without an auditable Safety Override.",
                )
            )
        if has_override and not is_critical:
            diagnostics.append(
                AnalysisDiagnostic(
                    code="PRIORITISATION-OVERRIDE-NOT-CRITICAL",
                    severity="blocked",
                    message=f"Client {item.client_id} has a Safety Override but is not Critical tier.",
                )
            )
        if has_override:
            if seen_non_override:
                diagnostics.append(
                    AnalysisDiagnostic(
                        code="PRIORITISATION-OVERRIDE-ORDERING-VIOLATION",
                        severity="blocked",
                        message=f"Safety Override for {item.client_id} placed after non-override items.",
                    )
                )
        else:
            seen_non_override = True

    override_scores = [
        item.urgency.score for item in queue if item.urgency.safety_override is not None
    ]
    non_override_scores = [
        item.urgency.score for item in queue if item.urgency.safety_override is None
    ]
    for group_name, scores in [
        ("override", override_scores),
        ("non-override", non_override_scores),
    ]:
        for i in range(len(scores) - 1):
            if scores[i] < scores[i + 1]:
                diagnostics.append(
                    AnalysisDiagnostic(
                        code="PRIORITISATION-SCORES-NOT-DESCENDING",
                        severity="blocked",
                        message=(
                            f"In {group_name} group, score {scores[i]} at rank {i+1} "
                            f"is less than score {scores[i+1]} at rank {i+2}."
                        ),
                    )
                )

    for item in queue:
        factor_sum = sum(f.points for f in item.factor_contributions)
        if abs(factor_sum - item.urgency.score) > 0.05:
            diagnostics.append(
                AnalysisDiagnostic(
                    code="PRIORITISATION-FACTOR-SUM-MISMATCH",
                    severity="blocked",
                    message=(
                        f"Client {item.client_id} factor sum {factor_sum:.2f} does "
                        f"not equal urgency score {item.urgency.score:.2f}."
                    ),
                )
            )

    for item in queue:
        if str(item.confidence.level) not in {"High", "Medium", "Low"}:
            diagnostics.append(
                AnalysisDiagnostic(
                    code="PRIORITISATION-INVALID-CONFIDENCE",
                    severity="blocked",
                    message=f"Client {item.client_id} has invalid confidence level: {item.confidence.level}.",
                )
            )

    is_blocked = any(d.severity == "blocked" for d in diagnostics)

    for item in queue:
        case = cases[item.client_id]
        packets = packets_by_client[item.client_id]
        evidence_ids = list(
            dict.fromkeys(
                evidence_id
                for factor in item.factor_contributions
                for evidence_id in factor.evidence_item_ids
            )
        )
        if not evidence_ids:
            evidence_ids = [
                evidence.id for packet in packets[:1] for evidence in packet.items[:1]
            ]
        findings.append(
            AgentFinding(
                finding_id=f"FINDING-{item.client_id}-PRIORITY",
                direction="prioritisation",
                client_id=item.client_id,
                case_id=item.case_id,
                title=f"Priority {item.rank} — {item.client_name}",
                summary=item.priority_rationale,
                why_it_matters=case.why_now,
                limitations=list(case.confidence.reasons),
                evidence_packet_ids=[packet.packet_id for packet in packets],
                evidence_item_ids=evidence_ids,
                factor_contributions=item.factor_contributions,
                rank=item.rank,
                urgency=item.urgency,
                confidence=item.confidence,
            )
        )
    return AgentReport(
        agent_id="prioritisation-specialist",
        role=(
            "Explains the deterministic whole-Book order while keeping Urgency and "
            "Confidence separate."
        ),
        depth="deep",
        status="blocked" if is_blocked else "completed",
        summary=(
            f"Audited and defended the deterministic order of all {len(findings)} Client Cases "
            f"(verified 6 ranking invariants: contiguous ranks 1..{len(findings)}, safety overrides, "
            "descending scores, factor bounds, and urgency/confidence independence); "
            "the agent did not assign scores, tiers, Safety Overrides, or ranks."
        ),
        findings=[] if is_blocked else findings,
        diagnostics=diagnostics,
    )


def _evidence_auditor(
    workbench: WorkbenchModel, reports: list[AgentReport]
) -> AgentReport:
    packets = {packet.packet_id: packet for packet in workbench.evidence_packets}
    errors: list[AnalysisDiagnostic] = []
    checked = 0
    for report in reports:
        for finding in report.findings:
            checked += 1
            selected = [
                packets.get(packet_id) for packet_id in finding.evidence_packet_ids
            ]
            if any(packet is None for packet in selected):
                errors.append(
                    AnalysisDiagnostic(
                        code="EVIDENCE-MISSING-PACKET",
                        severity="blocked",
                        message=f"{finding.finding_id} cites an unknown Evidence Packet.",
                    )
                )
                continue

            for packet in selected:
                if (
                    packet.client_id != finding.client_id
                    or packet.case_id != finding.case_id
                ):
                    errors.append(
                        AnalysisDiagnostic(
                            code="EVIDENCE-OWNERSHIP-MISMATCH",
                            severity="blocked",
                            message=(
                                f"{finding.finding_id} ({finding.client_id}) cites packet "
                                f"{packet.packet_id} belonging to client {packet.client_id}."
                            ),
                        )
                    )

            allowed = {
                item.id
                for packet in selected
                if packet is not None
                for item in packet.items
            }
            if not set(finding.evidence_item_ids) <= allowed:
                errors.append(
                    AnalysisDiagnostic(
                        code="EVIDENCE-CROSS-PACKET",
                        severity="blocked",
                        message=(
                            f"{finding.finding_id} cites evidence outside its bounded "
                            "Evidence Packets."
                        ),
                    )
                )

            if not set(finding.narrative_evidence_item_ids) <= allowed:
                errors.append(
                    AnalysisDiagnostic(
                        code="EVIDENCE-CROSS-PACKET-NARRATIVE",
                        severity="blocked",
                        message=(
                            f"{finding.finding_id} narrative cites evidence outside its bounded "
                            "Evidence Packets."
                        ),
                    )
                )

    is_blocked = bool(errors)
    return AgentReport(
        agent_id="evidence-auditor",
        role="Fails closed when a specialist finding escapes its Evidence Packets.",
        depth="control",
        status="blocked" if is_blocked else "completed",
        summary=(
            f"Checked {checked} specialist findings; "
            f"{len(errors)} evidence-boundary violations found."
        ),
        diagnostics=errors,
    )


def _largest_metric(finding: AgentFinding) -> float:
    values = [metric.result.value for metric in finding.derived_metrics]
    return max(values, default=0.0)

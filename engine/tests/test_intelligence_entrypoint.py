"""Public intelligence entry point and specialist-team behavior."""

from __future__ import annotations

import json
import shutil
from datetime import date

import jsonschema
import pandas as pd

from jb_clarity import analyse_dataset
from jb_clarity.cli import main
from jb_clarity.intelligence.provider import NarrativeDraft


def _agent(result, agent_id: str):
    return next(agent for agent in result.agent_reports if agent.agent_id == agent_id)


def test_supported_dataset_runs_the_specialist_team(data_dir, model):
    result = analyse_dataset(data_dir, clock=lambda: model.meta.generated_at)

    assert result.status == "completed"
    assert result.adapter_id == "jb-wealth-challenge-v1"
    assert result.workbench is not None
    assert result.workbench.to_contract_dict() == model.to_contract_dict()
    assert result.deep_focus == ["hidden-risk", "prioritisation"]
    assert [agent.agent_id for agent in result.agent_reports] == [
        "dataset-steward",
        "hidden-risk-specialist",
        "advisory-context-analyst",
        "prioritisation-specialist",
        "evidence-auditor",
    ]


def test_embedded_workbench_keeps_its_frozen_contract(data_dir, model, schema):
    result = analyse_dataset(data_dir, clock=lambda: model.meta.generated_at)

    payload = result.to_contract_dict()
    jsonschema.Draft202012Validator(schema).validate(payload["workbench"])


def test_hidden_risk_agent_exposes_aggregate_and_look_through_evidence(data_dir, model):
    result = analyse_dataset(data_dir, clock=lambda: model.meta.generated_at)
    hidden_risk = _agent(result, "hidden-risk-specialist")
    hartono = next(f for f in hidden_risk.findings if f.client_id == "CL-0001")

    assert hidden_risk.depth == "deep"
    assert hartono.direction == "hidden-risk"
    assert "44.99%" in hartono.summary
    assert "every portfolio" in hartono.summary
    assert hartono.evidence_packet_ids == ["PACKET-CL-0001-CONCENTRATION"]
    assert any("UNDERLYING" in item_id for item_id in hartono.evidence_item_ids)
    assert any(
        "weights are not supplied" in item.lower() for item in hartono.limitations
    )


def test_prioritisation_agent_preserves_the_deterministic_queue(data_dir, model):
    result = analyse_dataset(data_dir, clock=lambda: model.meta.generated_at)
    prioritisation = _agent(result, "prioritisation-specialist")

    assert prioritisation.depth == "deep"
    assert len(prioritisation.findings) == model.book.client_count
    assert [finding.client_id for finding in prioritisation.findings] == [
        item.client_id for item in model.book.priority_queue
    ]
    assert [finding.rank for finding in prioritisation.findings] == list(
        range(1, model.book.client_count + 1)
    )
    assert all(finding.urgency is not None for finding in prioritisation.findings)
    assert all(finding.confidence is not None for finding in prioritisation.findings)


def test_unknown_dataset_returns_a_mapping_report_instead_of_guessing(tmp_path):
    (tmp_path / "positions.csv").write_text(
        "account,security,value\nA-1,ABC,100\n", encoding="utf-8"
    )

    result = analyse_dataset(tmp_path)

    assert result.status == "needs-mapping"
    assert result.workbench is None
    assert result.dataset_profile.files[0].name == "positions.csv"
    assert "account" in result.dataset_profile.files[0].columns
    assert any(
        diagnostic.code == "DATASET-NO-ADAPTER" for diagnostic in result.diagnostics
    )
    assert "clients.csv" in result.diagnostics[0].message


def test_as_of_date_before_latest_snapshot_is_blocked_instead_of_leaking_future_data(
    data_dir,
):
    result = analyse_dataset(data_dir, date(2026, 6, 30))

    assert result.status == "blocked"
    assert result.workbench is None
    assert any(
        diagnostic.code == "DATASET-AS-OF-AFTER-CUTOFF"
        for diagnostic in result.diagnostics
    )


def test_known_bundle_with_an_invalid_schema_returns_a_blocking_diagnostic(
    data_dir, tmp_path
):
    target = tmp_path / "data"
    shutil.copytree(data_dir, target)
    holdings = target / "holdings.csv"
    content = holdings.read_text(encoding="utf-8")
    holdings.write_text(
        content.replace("snapshot_date", "wrong_date", 1), encoding="utf-8"
    )

    result = analyse_dataset(target)

    assert result.status == "blocked"
    assert result.workbench is None
    assert any(
        diagnostic.code == "DATASET-SCHEMA-INVALID" for diagnostic in result.diagnostics
    )


def test_material_data_integrity_issue_blocks_outward_insights(data_dir, tmp_path):
    target = tmp_path / "data"
    shutil.copytree(data_dir, target)
    clients = pd.read_csv(target / "clients.csv")
    clients.loc[clients.client_id == "CL-0008", "total_aum_usd"] = 5_000_000.0
    clients.to_csv(target / "clients.csv", index=False)

    result = analyse_dataset(target)

    assert result.status == "blocked"
    assert result.workbench is None
    assert all(not report.findings for report in result.agent_reports)
    assert any(
        diagnostic.code == "DQ-TOTALS-DISAGREE" for diagnostic in result.diagnostics
    )


def test_every_finding_is_bounded_to_existing_evidence(data_dir, model):
    result = analyse_dataset(data_dir, clock=lambda: model.meta.generated_at)
    assert result.workbench is not None

    packets = {packet.packet_id: packet for packet in result.workbench.evidence_packets}
    for report in result.agent_reports:
        for finding in report.findings:
            allowed_items = {
                item.id
                for packet_id in finding.evidence_packet_ids
                for item in packets[packet_id].items
            }
            assert set(finding.evidence_item_ids) <= allowed_items


def test_cli_writes_one_ui_ready_intelligence_run(data_dir, tmp_path):
    output = tmp_path / "intelligence.json"

    exit_code = main(
        [
            "analyse",
            "--data",
            str(data_dir),
            "--as-of",
            "2026-08-26",
            "--generated-at",
            "2026-09-05T00:00:00+00:00",
            "--output",
            str(output),
        ]
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert exit_code == 0
    assert payload["status"] == "completed"
    assert payload["deepFocus"] == ["hidden-risk", "prioritisation"]
    assert payload["workbench"]["book"]["clientCount"] == 20
    assert payload["agentReports"][1]["agentId"] == "hidden-risk-specialist"


class _SafeNarrativeProvider:
    def generate(self, request):
        return NarrativeDraft(
            summary=request.canonical_summary,
            why_it_matters=request.canonical_why_it_matters,
            evidence_item_ids=request.allowed_evidence_item_ids[:1],
        )


class _UnsafeNarrativeProvider:
    def generate(self, request):
        return NarrativeDraft(
            summary="Invented exposure of 999%.",
            why_it_matters="Act immediately.",
            evidence_item_ids=["EV-ANOTHER-CLIENT"],
        )


def test_optional_model_provider_can_only_enrich_bounded_deep_findings(data_dir, model):
    result = analyse_dataset(
        data_dir,
        clock=lambda: model.meta.generated_at,
        narrative_provider=_SafeNarrativeProvider(),
        narrative_policy=lambda request: request,
    )

    hidden = _agent(result, "hidden-risk-specialist")
    priority = _agent(result, "prioritisation-specialist")
    context = _agent(result, "advisory-context-analyst")
    assert all(
        finding.narrative_source == "model-validated" for finding in hidden.findings
    )
    assert all(
        finding.narrative_source == "model-validated" for finding in priority.findings
    )
    assert all(
        finding.narrative_source == "deterministic" for finding in context.findings
    )
    assert [finding.rank for finding in priority.findings] == [
        item.rank for item in model.book.priority_queue
    ]


def test_unsafe_model_output_is_rejected_without_losing_deterministic_insights(
    data_dir, model
):
    result = analyse_dataset(
        data_dir,
        clock=lambda: model.meta.generated_at,
        narrative_provider=_UnsafeNarrativeProvider(),
        narrative_policy=lambda request: request,
    )

    hidden = _agent(result, "hidden-risk-specialist")
    assert all(
        finding.narrative_source == "deterministic" for finding in hidden.findings
    )
    assert all("999%" not in finding.summary for finding in hidden.findings)
    assert any(
        diagnostic.code == "MODEL-OUTPUT-REJECTED" for diagnostic in hidden.diagnostics
    )
    assert result.status == "completed"


def test_model_provider_requires_an_explicit_egress_policy(data_dir):
    try:
        analyse_dataset(data_dir, narrative_provider=_SafeNarrativeProvider())
    except ValueError as error:
        assert "egress policy" in str(error).lower()
    else:  # pragma: no cover - assertion gives the useful failure
        raise AssertionError("provider ran without an explicit egress policy")

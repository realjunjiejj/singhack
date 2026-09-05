"""One deep interface from a dataset directory to evidence-backed insights."""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Callable

import pandas as pd

from jb_clarity.build import DEFAULT_AS_OF, build_workbench
from jb_clarity.config import CONFIG_DIR, SCORING_CONFIG_FILE
from jb_clarity.intelligence.intake import profile_dataset, select_adapter
from jb_clarity.intelligence.models import (
    AnalysisDiagnostic,
    DatasetProfile,
    IntelligenceRun,
)
from jb_clarity.intelligence.provider import NarrativePolicy, NarrativeProvider
from jb_clarity.intelligence.team import DEEP_FOCUS, run_agent_team


def analyse_dataset(
    data_source: Path | str,
    as_of_date: date = DEFAULT_AS_OF,
    *,
    clock: Callable[[], datetime] | None = None,
    narrative_provider: NarrativeProvider | None = None,
    narrative_policy: NarrativePolicy | None = None,
) -> IntelligenceRun:
    """Profile, adapt, analyse, and return one UI-ready Intelligence Run.

    The first adapter accepts the published challenge bundle. Other source
    shapes intentionally return ``needs-mapping`` until an explicit adapter is
    added; financial semantics are never inferred from column names by a model.
    """
    if narrative_provider is not None and narrative_policy is None:
        raise ValueError(
            "Using a model provider requires an explicit narrative egress policy."
        )

    profile = profile_dataset(data_source)
    adapter_id, missing = select_adapter(profile)
    now = (clock or (lambda: datetime.now(timezone.utc)))()

    scoring_path = CONFIG_DIR / SCORING_CONFIG_FILE
    scoring_hash = (
        hashlib.sha256(scoring_path.read_bytes()).hexdigest()[:16]
        if scoring_path.exists()
        else "none"
    )
    run_id = _run_id(
        profile,
        as_of_date,
        adapter_id=adapter_id,
        scoring_hash=scoring_hash,
        has_model=(narrative_provider is not None),
    )

    if adapter_id is None:
        missing_text = ", ".join(missing) if missing else "a supported directory"
        return IntelligenceRun(
            run_id=run_id,
            generated_at=now,
            status="needs-mapping",
            deep_focus=DEEP_FOCUS,
            dataset_profile=profile,
            diagnostics=[
                AnalysisDiagnostic(
                    code="DATASET-NO-ADAPTER",
                    severity="blocked",
                    message=(
                        "No approved dataset adapter matches this source. Map it to the "
                        f"canonical wealth roles; the current adapter requires: {missing_text}."
                    ),
                )
            ],
        )

    try:
        latest_snapshot = date.fromisoformat(
            str(
                pd.read_csv(
                    Path(data_source) / "holdings.csv", usecols=["snapshot_date"]
                )["snapshot_date"].max()
            )
        )
    except (KeyError, TypeError, ValueError):
        return IntelligenceRun(
            run_id=run_id,
            generated_at=now,
            status="blocked",
            adapter_id=adapter_id,
            deep_focus=DEEP_FOCUS,
            dataset_profile=profile,
            diagnostics=[
                AnalysisDiagnostic(
                    code="DATASET-SCHEMA-INVALID",
                    severity="blocked",
                    message=(
                        "The source filenames match the adapter, but the canonical "
                        "wealth schema does not. Review the profiled columns and add "
                        "or update an approved mapping adapter."
                    ),
                )
            ],
        )
    if latest_snapshot > as_of_date:
        return IntelligenceRun(
            run_id=run_id,
            generated_at=now,
            status="blocked",
            adapter_id=adapter_id,
            deep_focus=DEEP_FOCUS,
            dataset_profile=profile,
            diagnostics=[
                AnalysisDiagnostic(
                    code="DATASET-AS-OF-AFTER-CUTOFF",
                    severity="blocked",
                    message=(
                        f"The dataset contains a {latest_snapshot.isoformat()} snapshot "
                        f"after the requested as-of date {as_of_date.isoformat()}. The "
                        "current adapter will not expose future records; use a source "
                        "filtered to the requested cutoff or analyse at the latest date."
                    ),
                )
            ],
        )

    try:
        workbench = build_workbench(Path(data_source), as_of_date, clock=lambda: now)
    except (KeyError, TypeError, ValueError):
        return IntelligenceRun(
            run_id=run_id,
            generated_at=now,
            status="blocked",
            adapter_id=adapter_id,
            deep_focus=DEEP_FOCUS,
            dataset_profile=profile,
            diagnostics=[
                AnalysisDiagnostic(
                    code="DATASET-SCHEMA-INVALID",
                    severity="blocked",
                    message=(
                        "The approved adapter could not produce the canonical wealth "
                        "model. No partial insight was published; review its mapping "
                        "and deterministic validation evidence."
                    ),
                )
            ],
        )
    reports = run_agent_team(workbench, profile, narrative_provider, narrative_policy)
    blocked = any(report.status == "blocked" for report in reports)
    diagnostics: list[AnalysisDiagnostic] = []
    if blocked:
        for report in reports:
            for diag in report.diagnostics:
                if diag.severity in ("blocked", "material"):
                    diagnostics.append(diag)
        workbench = None
        reports = [report.model_copy(update={"findings": []}) for report in reports]

    return IntelligenceRun(
        run_id=run_id,
        generated_at=now,
        status="blocked" if blocked else "completed",
        adapter_id=adapter_id,
        deep_focus=DEEP_FOCUS,
        dataset_profile=profile,
        diagnostics=diagnostics,
        agent_reports=reports,
        workbench=workbench,
    )


def _run_id(
    profile: DatasetProfile,
    as_of_date: date,
    adapter_id: str | None = None,
    scoring_hash: str | None = None,
    team_version: str = "1.0.0",
    has_model: bool = False,
) -> str:
    from jb_clarity import SCHEMA_VERSION, __version__ as engine_version

    model_version = "prompt-v1" if has_model else "no-model"
    material = "|".join(
        [
            f"schema:{SCHEMA_VERSION}",
            f"engine:{engine_version}",
            f"adapter:{adapter_id or 'none'}",
            f"scoring:{scoring_hash or 'none'}",
            f"team:{team_version}",
            f"model:{model_version}",
            f"as_of:{as_of_date.isoformat()}",
            *[f"{file.name}:{file.sha256}" for file in profile.files],
        ]
    )
    return "RUN-" + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16].upper()

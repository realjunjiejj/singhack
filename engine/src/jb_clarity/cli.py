"""Command-line entry point.

    python -m jb_clarity.cli build \\
        --data singhacks-jb-wealth-intelligence/data \\
        --as-of 2026-08-26 \\
        --output artifacts/workbench.json
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timezone
from pathlib import Path

from jb_clarity.build import DEFAULT_AS_OF, SCHEMA_VERSION, build_workbench
from jb_clarity.intelligence.entrypoint import analyse_dataset

DEFAULT_SCHEMA = Path("contracts/workbench.schema.json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m jb_clarity.cli",
        description="Build Workbench or multi-agent intelligence artifacts.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    build = subparsers.add_parser("build", help="Generate the Workbench artifact.")
    build.add_argument(
        "--data",
        required=True,
        type=Path,
        help="Directory containing the supplied challenge files.",
    )
    build.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=DEFAULT_AS_OF,
        help="As-of date in ISO format. Defaults to 2026-08-26.",
    )
    build.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the generated artifact to.",
    )
    build.add_argument(
        "--schema",
        type=Path,
        default=DEFAULT_SCHEMA,
        help="JSON Schema to validate the artifact against before writing.",
    )
    build.add_argument(
        "--generated-at",
        type=datetime.fromisoformat,
        default=None,
        help="Fix the generation timestamp, for reproducible output.",
    )
    build.add_argument(
        "--skip-validation",
        action="store_true",
        help="Write the artifact without validating it against the schema.",
    )

    check = subparsers.add_parser(
        "validate-data",
        help="Check a dataset against the canonical source contract without "
        "writing an artifact.",
    )
    check.add_argument("--data", required=True, type=Path, help="Dataset directory.")
    check.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=None,
        help="As-of date. Defaults to the latest supplied snapshot.",
    )

    analyse = subparsers.add_parser(
        "analyse",
        help="Profile a dataset and run the evidence-bounded analyst team.",
    )
    analyse.add_argument(
        "--data",
        required=True,
        type=Path,
        help="Directory containing a supported or mappable dataset.",
    )
    analyse.add_argument(
        "--as-of",
        type=date.fromisoformat,
        default=DEFAULT_AS_OF,
        help="As-of date in ISO format. Defaults to 2026-08-26.",
    )
    analyse.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Path to write the Intelligence Run artifact to.",
    )
    analyse.add_argument(
        "--generated-at",
        type=datetime.fromisoformat,
        default=None,
        help="Fix the generation timestamp, for reproducible output.",
    )
    analyse.add_argument(
        "--live-ai",
        action="store_true",
        default=False,
        help="Enable live AI agent reasoning via Google Gemini.",
    )
    analyse.add_argument(
        "--gemini-model",
        default="gemini-3.8-flash",
        help="Google Gemini model to use. Defaults to gemini-3.8-flash.",
    )
    analyse.add_argument(
        "--api-key",
        default=None,
        help="API key for Gemini (defaults to GEMINI_API_KEY or GOOGLE_API_KEY env var).",
    )
    return parser


def _validate_data(args: argparse.Namespace) -> int:
    """Report whether a dataset can produce a Workbench artifact, and why not.

    Deliberately prints counts and capability names only. Relationship-manager
    notes and client record contents never appear in validation output.
    """
    from jb_clarity.ingestion import source_contract
    from jb_clarity.ingestion.loader import load_challenge_data
    from jb_clarity.ingestion.validation import validate

    print(f"Canonical source contract : v{source_contract.CONTRACT_VERSION}")
    print(f"Dataset directory         : {args.data}")

    try:
        data = load_challenge_data(args.data)
    except (FileNotFoundError, source_contract.SourceContractError) as error:
        print(f"\nBLOCKED: {error}", file=sys.stderr)
        return 1

    try:
        snapshots = data.snapshot_dates
    except source_contract.SourceContractError as error:
        print(f"\nBLOCKED: {error}", file=sys.stderr)
        return 1

    as_of = args.as_of or date.fromisoformat(snapshots[-1])
    rm_ids = sorted({str(value) for value in data.clients["rm_id"].dropna().unique()})

    print("\nResolved source files:")
    for contract in source_contract.TABLES.values():
        path = Path(args.data) / contract.default_filename
        marker = "present" if path.exists() else "MISSING"
        print(f"  {contract.canonical_name:<20} {contract.default_filename:<26} {marker}")

    print("\nBook:")
    print(f"  relationship manager    : {', '.join(rm_ids) or 'none recorded'}")
    print(f"  clients                 : {len(data.clients)}")
    print(f"  portfolios              : {len(data.portfolios)}")
    print(f"  holdings                : {len(data.holdings)}")
    print(f"  snapshots               : {len(snapshots)} ({snapshots[0]} to {snapshots[-1]})")
    print(f"  as-of date              : {as_of.isoformat()}")

    capabilities = {
        "credit and collateral stress test": not data.facilities.empty,
        "uncalled commitments": not data.commitments.empty,
        "planned obligations": not data.cash_needs.empty,
        "event-grounded explanation": not data.events.empty,
        "open loops from RM notes": bool(data.notes),
    }
    print("\nCapabilities:")
    for name, available in capabilities.items():
        print(f"  {'enabled ' if available else 'UNAVAILABLE'} {name}")

    report = validate(data)
    blocking = [i for i in report.issues if i.severity == "material"]
    warnings = [i for i in report.issues if i.severity != "material"]

    print(f"\nData quality: {report.status}")
    for issue in blocking:
        print(f"  BLOCKING  {issue.id}: {issue.summary}")
    for issue in warnings:
        print(f"  warning   {issue.id}: {issue.summary}")
    if not report.issues:
        print("  no issues found")

    if len(rm_ids) > 1:
        print(
            "\nBLOCKED: this dataset contains more than one relationship manager "
            f"({', '.join(rm_ids)}). Building a Book across several RMs is not "
            "supported; supply a dataset filtered to one RM.",
            file=sys.stderr,
        )
        return 1

    print("\nGeneration may proceed.")
    return 0


def _validate(payload: dict, schema_path: Path) -> None:
    import jsonschema

    with schema_path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    jsonschema.Draft202012Validator(schema).validate(payload)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command == "validate-data":
        return _validate_data(args)

    clock = None
    if args.generated_at is not None:
        stamped = args.generated_at
        if stamped.tzinfo is None:
            stamped = stamped.replace(tzinfo=timezone.utc)
        clock = lambda: stamped  # noqa: E731 - a fixed clock is the whole point

    if args.command == "analyse":
        narrative_provider = None
        narrative_policy = None
        if args.live_ai:
            from jb_clarity.intelligence.provider import (
                default_narrative_policy,
                get_gemini_provider,
            )

            narrative_provider = get_gemini_provider(
                api_key=args.api_key, model=args.gemini_model
            )
            narrative_policy = default_narrative_policy

        result = analyse_dataset(
            args.data,
            args.as_of,
            clock=clock,
            narrative_provider=narrative_provider,
            narrative_policy=narrative_policy,
        )
        payload = result.to_contract_dict()
        if payload.get("workbench") is not None:
            schema_path = Path("contracts/workbench.schema.json")
            if schema_path.exists():
                try:
                    _validate(payload["workbench"], schema_path)
                except Exception as exc:
                    print(
                        f"Validation error for embedded workbench: {exc}",
                        file=sys.stderr,
                    )
                    return 2

        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("w", encoding="utf-8") as handle:
            json.dump(payload, handle, indent=2, ensure_ascii=False)
            handle.write("\n")

        print(f"Wrote {args.output}")
        print(f"  run id         : {result.run_id}")
        print(f"  status         : {result.status}")
        print(f"  adapter        : {result.adapter_id or 'needs mapping'}")
        print(f"  specialist team: {len(result.agent_reports)} agents")
        return 0 if result.status in {"completed", "partial"} else 2

    if args.command != "build":  # pragma: no cover - argparse enforces this
        return 2

    model = build_workbench(args.data, args.as_of, clock=clock)
    payload = model.to_contract_dict()

    if not args.skip_validation:
        if not args.schema.exists():
            print(f"Schema not found at {args.schema}", file=sys.stderr)
            return 2
        _validate(payload, args.schema)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=False)
        handle.write("\n")

    queue = model.book.priority_queue
    print(f"Wrote {args.output}")
    print(f"  schema version : {SCHEMA_VERSION}")
    print(f"  artifact kind  : {model.meta.artifact_kind}")
    print(f"  as-of date     : {model.meta.as_of_date.isoformat()}")
    print(f"  clients ranked : {len(queue)}")
    print(f"  evidence packets: {len(model.evidence_packets)}")
    print(
        "  tiers          : "
        f"{model.book.summary.critical} Critical, "
        f"{model.book.summary.high} High, "
        f"{model.book.summary.watch} Watch"
    )
    print(f"  data quality   : {model.meta.data_quality.status}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

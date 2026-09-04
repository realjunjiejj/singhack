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

DEFAULT_SCHEMA = Path("contracts/workbench.schema.json")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="python -m jb_clarity.cli",
        description="Build the JB Clarity Workbench artifact from the challenge data.",
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
    return parser


def _validate(payload: dict, schema_path: Path) -> None:
    import jsonschema

    with schema_path.open(encoding="utf-8") as handle:
        schema = json.load(handle)
    jsonschema.Draft202012Validator(schema).validate(payload)


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if args.command != "build":  # pragma: no cover - argparse enforces this
        return 2

    clock = None
    if args.generated_at is not None:
        stamped = args.generated_at
        if stamped.tzinfo is None:
            stamped = stamped.replace(tzinfo=timezone.utc)
        clock = lambda: stamped  # noqa: E731 - a fixed clock is the whole point

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

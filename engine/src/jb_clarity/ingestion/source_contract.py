"""The canonical source-dataset contract.

One authoritative description of the tables the engine reads. The loader and
the validator both consume this, so a column list exists in exactly one place
and the challenge Data Dictionary stays documentation rather than becoming
executable prose.

A Book that uses these filenames, grains and column names loads without a
mapping layer. Mapping other column names onto this contract is a separate
adapter concern and is deliberately not implemented here.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Literal

CONTRACT_VERSION = "1.0.0"

ColumnType = Literal["string", "number", "integer", "date", "boolean"]


@dataclass(frozen=True)
class ForeignKey:
    """A column that must resolve to a primary key in another canonical table."""

    column: str
    references_table: str
    references_column: str


@dataclass(frozen=True)
class WideColumnFamily:
    """Columns whose names embed a snapshot date, e.g. `drawn_2026-08-26`.

    The dataset stores parts of its history across columns rather than rows.
    The family records the prefix so the loader can discover which snapshots a
    table actually carries instead of assuming a fixed grid.
    """

    prefix: str
    type: ColumnType = "number"
    required: bool = True

    def column_for(self, snapshot: str) -> str:
        return f"{self.prefix}{snapshot}"


@dataclass(frozen=True)
class TableContract:
    canonical_name: str
    default_filename: str
    grain: str
    required_columns: dict[str, ColumnType]
    primary_key: tuple[str, ...] = ()
    optional_columns: dict[str, ColumnType] = field(default_factory=dict)
    foreign_keys: tuple[ForeignKey, ...] = ()
    wide_column_families: tuple[WideColumnFamily, ...] = ()
    nullable_columns: frozenset[str] = frozenset()
    # A core table must exist for a Book to be constructed at all. A
    # capability-input table only powers particular detectors.
    core: bool = True

    @property
    def identifier_columns(self) -> tuple[str, ...]:
        return tuple(
            name
            for name, kind in {**self.required_columns, **self.optional_columns}.items()
            if kind == "string" and (name.endswith("_id") or name.endswith("_code"))
        )

    def dtype_map(self) -> dict[str, str]:
        """Parse-time dtypes.

        Identifier columns are read as strings so a stable record key is never
        reshaped by type inference — `0001` must not become `1`.
        """
        return {name: "string" for name in self.identifier_columns}

    def all_columns(self) -> dict[str, ColumnType]:
        return {**self.required_columns, **self.optional_columns}


CLIENTS = TableContract(
    canonical_name="clients",
    default_filename="clients.csv",
    grain="one row per client",
    primary_key=("client_id",),
    required_columns={
        "client_id": "string",
        "client_name": "string",
        "booking_centre": "string",
        "rm_id": "string",
        "rm_name": "string",
        "base_currency": "string",
        "risk_profile": "string",
        "risk_tolerance_score": "number",
        "liquidity_needs": "string",
        "objectives": "string",
        "total_aum_usd": "number",
    },
    optional_columns={
        "age": "number",
        "gender": "string",
        "nationality": "string",
        "country_of_residence": "string",
        "tax_domicile": "string",
        "rm_desk": "string",
        "wealth_band": "string",
        "life_stage": "string",
        "source_of_wealth": "string",
        "investment_horizon_years": "number",
        "client_since": "date",
        "kyc_review_due": "date",
        "pep_status": "string",
        "reporting_language": "string",
    },
    nullable_columns=frozenset({"age", "gender", "kyc_review_due"}),
)

PORTFOLIOS = TableContract(
    canonical_name="portfolios",
    default_filename="portfolios.csv",
    grain="one row per portfolio",
    primary_key=("portfolio_id",),
    required_columns={
        "portfolio_id": "string",
        "client_id": "string",
        "portfolio_name": "string",
        "mandate_code": "string",
        "service_model": "string",
        "base_currency": "string",
    },
    optional_columns={
        "mandate_name": "string",
        "inception_date": "date",
        "benchmark": "string",
        "aum_usd_current": "number",
    },
    foreign_keys=(
        ForeignKey("client_id", "clients", "client_id"),
        ForeignKey("mandate_code", "mandates", "mandate_code"),
    ),
    wide_column_families=(WideColumnFamily("aum_"),),
)

HOLDINGS = TableContract(
    canonical_name="holdings",
    default_filename="holdings.csv",
    grain="one row per position per snapshot date",
    primary_key=("snapshot_date", "portfolio_id", "instrument_id"),
    required_columns={
        "snapshot_date": "date",
        "portfolio_id": "string",
        "client_id": "string",
        "instrument_id": "string",
        "instrument_name": "string",
        "asset_class": "string",
        "instrument_ccy": "string",
        "quantity": "number",
        "price_local": "number",
        "market_value_local": "number",
        "portfolio_ccy": "string",
        "market_value_base": "number",
        "market_value_usd": "number",
        "liquidity_tier": "string",
    },
    optional_columns={
        "sub_asset_class": "string",
        "sector": "string",
        "region": "string",
        "weight_pct": "number",
        "avg_cost_local": "number",
        "cost_basis_base": "number",
        "unrealised_pnl_base": "number",
        "unrealised_pnl_pct": "number",
        "lending_value_base": "number",
        "advance_rate_pct": "number",
        "valuation_date": "date",
        "acquired_date": "date",
    },
    foreign_keys=(
        ForeignKey("portfolio_id", "portfolios", "portfolio_id"),
        ForeignKey("client_id", "clients", "client_id"),
        ForeignKey("instrument_id", "instruments", "instrument_id"),
    ),
)

INSTRUMENTS = TableContract(
    canonical_name="instruments",
    default_filename="instruments.csv",
    grain="one row per instrument",
    primary_key=("instrument_id",),
    required_columns={
        "instrument_id": "string",
        "instrument_name": "string",
        "asset_class": "string",
        "currency": "string",
        "liquidity_tier": "string",
    },
    optional_columns={
        "sub_asset_class": "string",
        "sector": "string",
        "region": "string",
        "underlying_reference": "string",
        "sustainability_excluded": "string",
        "concentration_limit_applies": "string",
    },
    nullable_columns=frozenset({"underlying_reference", "sector", "region"}),
    wide_column_families=(WideColumnFamily("price_", required=False),),
)

MANDATES = TableContract(
    canonical_name="mandates",
    default_filename="mandates.csv",
    grain="one row per mandate and asset class",
    primary_key=("mandate_code", "asset_class"),
    required_columns={
        "mandate_code": "string",
        "asset_class": "string",
        "min_pct": "number",
        "target_pct": "number",
        "max_pct": "number",
        "max_single_position_pct": "number",
    },
    optional_columns={"mandate_name": "string", "mandate_notes": "string"},
)

TRANSACTIONS = TableContract(
    canonical_name="transactions",
    default_filename="transactions.csv",
    grain="one row per transaction",
    primary_key=("transaction_id",),
    required_columns={
        "transaction_id": "string",
        "trade_date": "date",
        "portfolio_id": "string",
        "client_id": "string",
        "transaction_type": "string",
    },
    optional_columns={
        "settlement_date": "date",
        "instrument_id": "string",
        "instrument_name": "string",
        "quantity": "number",
        "price_local": "number",
        "currency": "string",
        "amount": "number",
        "narrative": "string",
    },
    nullable_columns=frozenset({"instrument_id", "quantity", "price_local", "amount"}),
    core=False,
)

CREDIT_FACILITIES = TableContract(
    canonical_name="credit_facilities",
    default_filename="credit_facilities.csv",
    grain="one row per credit facility",
    primary_key=("facility_id",),
    required_columns={
        "facility_id": "string",
        "client_id": "string",
        "collateral_portfolio_id": "string",
        "facility_type": "string",
        "facility_ccy": "string",
        "credit_limit": "number",
        "margin_call_ltv_pct": "number",
    },
    optional_columns={"interest_rate_pct": "number", "utilisation_pct_current": "number"},
    foreign_keys=(
        ForeignKey("client_id", "clients", "client_id"),
        ForeignKey("collateral_portfolio_id", "portfolios", "portfolio_id"),
    ),
    wide_column_families=(
        WideColumnFamily("drawn_"),
        WideColumnFamily("collateral_market_value_"),
        WideColumnFamily("lending_value_"),
        WideColumnFamily("ltv_pct_"),
        WideColumnFamily("headroom_", required=False),
    ),
    core=False,
)

COMMITMENTS = TableContract(
    canonical_name="commitments",
    default_filename="commitments.csv",
    grain="one row per outstanding commitment",
    primary_key=("commitment_id",),
    required_columns={
        "commitment_id": "string",
        "client_id": "string",
        "portfolio_id": "string",
        "fund_name": "string",
        "currency": "string",
        "committed": "number",
        "called_to_date": "number",
        "uncalled": "number",
    },
    optional_columns={"expected_call_window": "string"},
    foreign_keys=(ForeignKey("client_id", "clients", "client_id"),),
    core=False,
)

PLANNED_CASH_NEEDS = TableContract(
    canonical_name="planned_cash_needs",
    default_filename="planned_cash_needs.csv",
    grain="one row per planned obligation",
    primary_key=("need_id",),
    required_columns={
        "need_id": "string",
        "client_id": "string",
        "description": "string",
        "currency": "string",
        "amount": "number",
        "due_from": "date",
        "due_to": "date",
        "recurrence": "string",
        "certainty": "string",
    },
    foreign_keys=(ForeignKey("client_id", "clients", "client_id"),),
    core=False,
)

MARKET_CONTEXT = TableContract(
    canonical_name="market_context",
    default_filename="market_context.csv",
    grain="one row per market series per snapshot date",
    primary_key=("series_id", "snapshot_date"),
    required_columns={
        "series_id": "string",
        "snapshot_date": "date",
        "value": "number",
    },
    optional_columns={
        "series_name": "string",
        "category": "string",
        "unit": "string",
    },
)

EVENT_LOG = TableContract(
    canonical_name="event_log",
    default_filename="event_log.csv",
    grain="one row per recorded external event",
    required_columns={
        "event_date": "date",
        "event_type": "string",
        "description": "string",
        "primary_transmission": "string",
    },
    optional_columns={"region": "string", "severity": "string"},
    core=False,
)

RM_NOTES = TableContract(
    canonical_name="rm_notes",
    default_filename="rm_notes.json",
    grain="one record per relationship-manager note",
    primary_key=("note_id",),
    required_columns={
        "note_id": "string",
        "client_id": "string",
        "note_date": "date",
        "note": "string",
    },
    optional_columns={"rm_id": "string", "rm_name": "string", "channel": "string"},
    foreign_keys=(ForeignKey("client_id", "clients", "client_id"),),
    core=False,
)

TABLES: dict[str, TableContract] = {
    table.canonical_name: table
    for table in (
        CLIENTS,
        PORTFOLIOS,
        HOLDINGS,
        INSTRUMENTS,
        MANDATES,
        TRANSACTIONS,
        CREDIT_FACILITIES,
        COMMITMENTS,
        PLANNED_CASH_NEEDS,
        MARKET_CONTEXT,
        EVENT_LOG,
        RM_NOTES,
    )
}

CORE_TABLES = tuple(name for name, table in TABLES.items() if table.core)
CAPABILITY_TABLES = tuple(name for name, table in TABLES.items() if not table.core)

# Snapshot history must be comparable before any change can be explained.
MINIMUM_SNAPSHOTS = 2


class SourceContractError(ValueError):
    """A dataset does not satisfy the canonical source contract.

    Messages name the file, the record and the field, because an operator
    fixing a Book needs to find the row rather than be told the shape is wrong.
    """


def table(name: str) -> TableContract:
    try:
        return TABLES[name]
    except KeyError as error:
        raise SourceContractError(
            f"Unknown canonical table '{name}'. Known tables: "
            f"{', '.join(sorted(TABLES))}."
        ) from error


def discover_snapshots(snapshot_values: list[str], source: str) -> list[str]:
    """Validate and order the snapshot dates a Book actually supplies.

    Requires at least two distinct, well-formed, ordered dates. A single
    snapshot cannot support a change explanation, and the engine says so rather
    than comparing a date with itself.
    """
    unique = sorted({str(value) for value in snapshot_values})
    if not unique:
        raise SourceContractError(f"{source} contains no snapshot dates.")

    for value in unique:
        try:
            date.fromisoformat(value)
        except ValueError as error:
            raise SourceContractError(
                f"{source} has snapshot_date '{value}', which is not an ISO date "
                "(YYYY-MM-DD)."
            ) from error

    if len(unique) < MINIMUM_SNAPSHOTS:
        raise SourceContractError(
            f"{source} supplies {len(unique)} snapshot date "
            f"({unique[0]}). At least {MINIMUM_SNAPSHOTS} distinct dates are "
            "required to explain what changed."
        )
    return unique

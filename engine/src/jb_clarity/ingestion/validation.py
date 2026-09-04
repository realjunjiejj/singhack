"""Data-quality validation.

Every check records what it found and leaves the decision to a detector. The
engine never repairs a source, and never picks whichever total supports a
stronger story.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from jb_clarity.calculations.fx import FxTable
from jb_clarity.domain.enums import IssueSeverity
from jb_clarity.domain.models import DataQualityIssue, SourceReference
from jb_clarity.ingestion.loader import ChallengeData

# Relative difference above which two totals for the same thing are treated as
# a real disagreement rather than presentation rounding.
MATERIAL_TOTAL_DIFFERENCE_PCT = 0.5
# Difference below which an FX-converted total is treated as explaining a
# denomination gap exactly.
FX_EXPLAINED_TOLERANCE_PCT = 0.01


@dataclass(frozen=True)
class TotalsReconciliation:
    """Three independent statements of one client's wealth, compared."""

    client_id: str
    holdings_usd: float
    client_record_usd: float
    portfolio_record_usd: float
    portfolio_base_currency_total: float
    base_currencies: tuple[str, ...]
    max_difference_pct: float
    fx_explains_denomination_gap: bool

    @property
    def is_material(self) -> bool:
        return self.max_difference_pct > MATERIAL_TOTAL_DIFFERENCE_PCT


@dataclass
class ValidationReport:
    issues: list[DataQualityIssue] = field(default_factory=list)
    reconciliations: dict[str, TotalsReconciliation] = field(default_factory=dict)
    stale_valuations: list[dict] = field(default_factory=list)

    @property
    def status(self) -> str:
        if any(i.severity == IssueSeverity.MATERIAL for i in self.issues):
            return "attention"
        if self.issues:
            return "attention"
        return "clear"


def _orphan_issue(
    issue_id: str, summary: str, file: str, keys: list[str]
) -> DataQualityIssue:
    return DataQualityIssue(
        id=issue_id,
        severity=IssueSeverity.MATERIAL,
        summary=summary,
        source_references=[
            SourceReference(file=file, record_key=key) for key in sorted(keys)[:10]
        ],
    )


def validate(data: ChallengeData) -> ValidationReport:
    """Run every structural and arithmetic check over the loaded dataset."""
    report = ValidationReport()
    latest = data.latest_snapshot
    fx = FxTable.from_market(data.market, latest)

    _check_referential_integrity(data, report)
    _check_duplicates(data, report)
    _check_holding_arithmetic(data, report)
    _check_stale_valuations(data, report, latest)
    _reconcile_totals(data, report, fx, latest)

    report.issues.sort(key=lambda i: (i.severity != IssueSeverity.MATERIAL, i.id))
    return report


def _check_referential_integrity(data: ChallengeData, report: ValidationReport) -> None:
    checks = [
        (
            "DQ-REF-HOLDING-INSTRUMENT",
            set(data.holdings.instrument_id) - set(data.instruments.instrument_id),
            "holdings.csv rows reference an instrument that is not in instruments.csv.",
            "holdings.csv",
        ),
        (
            "DQ-REF-HOLDING-PORTFOLIO",
            set(data.holdings.portfolio_id) - set(data.portfolios.portfolio_id),
            "holdings.csv rows reference a portfolio that is not in portfolios.csv.",
            "holdings.csv",
        ),
        (
            "DQ-REF-PORTFOLIO-CLIENT",
            set(data.portfolios.client_id) - set(data.clients.client_id),
            "portfolios.csv rows reference a client that is not in clients.csv.",
            "portfolios.csv",
        ),
        (
            "DQ-REF-PORTFOLIO-MANDATE",
            set(data.portfolios.mandate_code) - set(data.mandates.mandate_code),
            "portfolios.csv references a mandate code that is not in mandates.csv.",
            "portfolios.csv",
        ),
        (
            "DQ-REF-FACILITY-PORTFOLIO",
            set(data.facilities.collateral_portfolio_id) - set(data.portfolios.portfolio_id),
            "credit_facilities.csv references a collateral portfolio that does not exist.",
            "credit_facilities.csv",
        ),
        (
            "DQ-REF-NOTE-CLIENT",
            {n.client_id for n in data.notes} - set(data.clients.client_id),
            "rm_notes.json references a client that is not in clients.csv.",
            "rm_notes.json",
        ),
    ]
    for issue_id, orphans, summary, file in checks:
        orphans = {o for o in orphans if o == o}  # drop NaN
        if orphans:
            report.issues.append(
                _orphan_issue(issue_id, summary, file, [str(o) for o in orphans])
            )


def _check_duplicates(data: ChallengeData, report: ValidationReport) -> None:
    key = ["snapshot_date", "portfolio_id", "instrument_id"]
    duplicated = data.holdings[data.holdings.duplicated(subset=key, keep=False)]
    if not duplicated.empty:
        report.issues.append(
            DataQualityIssue(
                id="DQ-DUP-HOLDINGS",
                severity=IssueSeverity.MATERIAL,
                summary=(
                    f"{len(duplicated)} holdings.csv rows repeat the same "
                    "snapshot, portfolio and instrument."
                ),
                source_references=[
                    SourceReference(
                        file="holdings.csv",
                        record_key=f"{r.portfolio_id}|{r.instrument_id}|{r.snapshot_date}",
                    )
                    for r in duplicated.head(10).itertuples()
                ],
            )
        )

    for frame, name, column in (
        (data.clients, "clients.csv", "client_id"),
        (data.portfolios, "portfolios.csv", "portfolio_id"),
        (data.instruments, "instruments.csv", "instrument_id"),
        (data.facilities, "credit_facilities.csv", "facility_id"),
    ):
        dupes = frame[frame.duplicated(subset=[column], keep=False)]
        if not dupes.empty:
            report.issues.append(
                DataQualityIssue(
                    id=f"DQ-DUP-{column.upper()}",
                    severity=IssueSeverity.MATERIAL,
                    summary=f"{name} contains duplicate {column} values.",
                    source_references=[
                        SourceReference(file=name, record_key=str(v))
                        for v in sorted(set(dupes[column].tolist()))[:10]
                    ],
                )
            )


def _check_holding_arithmetic(data: ChallengeData, report: ValidationReport) -> None:
    """`quantity x price_local` must reproduce `market_value_local`."""
    frame = data.holdings
    calculated = frame["quantity"] * frame["price_local"]
    difference = (calculated - frame["market_value_local"]).abs()
    scale = frame["market_value_local"].abs().clip(lower=1.0)
    offending = frame[(difference / scale) > 0.0001]
    if not offending.empty:
        report.issues.append(
            DataQualityIssue(
                id="DQ-ARITHMETIC-MARKET-VALUE",
                severity=IssueSeverity.MATERIAL,
                summary=(
                    f"{len(offending)} holdings rows where quantity x price_local "
                    "does not reproduce market_value_local."
                ),
                source_references=[
                    SourceReference(
                        file="holdings.csv",
                        record_key=f"{r.portfolio_id}|{r.instrument_id}|{r.snapshot_date}",
                        field="market_value_local",
                    )
                    for r in offending.head(10).itertuples()
                ],
            )
        )


def _check_stale_valuations(
    data: ChallengeData, report: ValidationReport, latest: str
) -> None:
    """A valuation older than its snapshot is normal for private markets, but
    it still limits what can be concluded from the number."""
    current = data.holdings_at(latest)
    stale = current[current.valuation_date != current.snapshot_date]
    for row in stale.itertuples():
        lag_days = (
            date.fromisoformat(str(row.snapshot_date))
            - date.fromisoformat(str(row.valuation_date))
        ).days
        report.stale_valuations.append(
            {
                "client_id": str(row.client_id),
                "portfolio_id": str(row.portfolio_id),
                "instrument_id": str(row.instrument_id),
                "instrument_name": str(row.instrument_name),
                "valuation_date": str(row.valuation_date),
                "snapshot_date": str(row.snapshot_date),
                "lag_days": lag_days,
                "liquidity_tier": str(row.liquidity_tier),
                "market_value_usd": float(row.market_value_usd),
            }
        )

    if report.stale_valuations:
        report.issues.append(
            DataQualityIssue(
                id="DQ-STALE-VALUATION",
                severity=IssueSeverity.WARNING,
                summary=(
                    f"{len(report.stale_valuations)} current holding(s) are carried at a "
                    "valuation date earlier than the snapshot date. Private markets "
                    "report on a lag, so this is expected, but any conclusion drawn "
                    "from the value is limited by its age."
                ),
                source_references=[
                    SourceReference(
                        file="holdings.csv",
                        record_key=f"{s['portfolio_id']}|{s['instrument_id']}|{s['snapshot_date']}",
                        field="valuation_date",
                    )
                    for s in report.stale_valuations[:10]
                ],
            )
        )


def _reconcile_totals(
    data: ChallengeData,
    report: ValidationReport,
    fx: FxTable,
    latest: str,
) -> None:
    """Compare the three independent statements of each client's total wealth.

    `clients.total_aum_usd` and `portfolios.aum_usd_current` are USD. The dated
    `portfolios.aum_<date>` columns are in each portfolio's own base currency.
    Comparing those two directly looks like a disagreement when it is only a
    denomination difference, so the FX explanation is tested explicitly.
    """
    holdings_now = data.holdings_at(latest)
    holdings_usd = holdings_now.groupby("client_id", dropna=False)["market_value_usd"].sum()

    for client_id in data.client_ids():
        client_record = float(data.client(client_id)["total_aum_usd"])
        portfolios = data.client_portfolios(client_id)
        portfolio_usd = float(portfolios["aum_usd_current"].sum())
        base_total = float(portfolios[f"aum_{latest}"].sum())
        currencies = tuple(sorted(set(portfolios["base_currency"].tolist())))
        held = float(holdings_usd.get(client_id, 0.0))

        values = [held, client_record, portfolio_usd]
        reference = max(abs(v) for v in values) or 1.0
        max_diff_pct = 100.0 * (max(values) - min(values)) / reference

        converted = 0.0
        convertible = True
        for _, row in portfolios.iterrows():
            conversion = fx.to_usd(float(row[f"aum_{latest}"]), str(row["base_currency"]))
            if conversion.amount != conversion.amount:  # NaN means no rate
                convertible = False
                break
            converted += conversion.amount

        fx_explains = False
        if convertible and portfolio_usd:
            gap_pct = abs(100.0 * (converted - portfolio_usd) / portfolio_usd)
            fx_explains = gap_pct <= FX_EXPLAINED_TOLERANCE_PCT

        report.reconciliations[client_id] = TotalsReconciliation(
            client_id=client_id,
            holdings_usd=held,
            client_record_usd=client_record,
            portfolio_record_usd=portfolio_usd,
            portfolio_base_currency_total=base_total,
            base_currencies=currencies,
            max_difference_pct=max_diff_pct,
            fx_explains_denomination_gap=fx_explains,
        )

    material = [r for r in report.reconciliations.values() if r.is_material]
    if material:
        report.issues.append(
            DataQualityIssue(
                id="DQ-TOTALS-DISAGREE",
                severity=IssueSeverity.MATERIAL,
                summary=(
                    f"{len(material)} client(s) where the holdings, client and portfolio "
                    "records state materially different totals in the same currency."
                ),
                source_references=[
                    SourceReference(file="clients.csv", record_key=r.client_id, field="total_aum_usd")
                    for r in material[:10]
                ],
            )
        )

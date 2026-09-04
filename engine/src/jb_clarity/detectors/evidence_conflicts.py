"""Material disagreements between sources.

Where two supplied sources say different things about the same quantity, both
are kept, the conclusion is narrowed and Confidence falls. Where an apparent
disagreement is fully explained — most often by currency denomination — that
explanation is stated rather than left as a scary-looking gap.
"""

from __future__ import annotations

import re

from jb_clarity.domain.enums import CaseStatus, SignalType
from jb_clarity.domain.models import Measure
from jb_clarity.evidence.claims import DetectedSignal, SignalBuilder

CLIENTS_FILE = "clients.csv"
PORTFOLIOS_FILE = "portfolios.csv"

_AMOUNT = re.compile(
    r"\b(USD|EUR|SGD|HKD|JPY|GBP|CHF)\s*([\d,]+(?:\.\d+)?)\s*(m|k|bn)?\b",
    re.IGNORECASE,
)
_MULTIPLIERS = {"k": 1_000.0, "m": 1_000_000.0, "bn": 1_000_000_000.0}
# Relative difference at which two statements of the same amount disagree.
AMOUNT_CONFLICT_PCT = 5.0
AMOUNT_UNRELATED_PCT = 100.0


def detect(context) -> list[DetectedSignal]:
    signals: list[DetectedSignal] = []
    totals = _totals_signal(context)
    if totals is not None:
        signals.append(totals)
    objective = _objective_amount_signal(context)
    if objective is not None:
        signals.append(objective)
    stale = _stale_valuation_signal(context)
    if stale is not None:
        signals.append(stale)
    schedule = _recurring_schedule_signal(context)
    if schedule is not None:
        signals.append(schedule)
    return signals


def _recurring_schedule_signal(context) -> DetectedSignal | None:
    """A recurring obligation whose full schedule exceeds the client's wealth.

    `amount` is per instalment and the window says how long instalments run. If
    multiplying the two produces more than the client owns, the record is
    ambiguous: `amount` may be the total rather than the instalment. The engine
    does not guess which reading is right.
    """
    if context.exposure.total_usd <= 0:
        return None

    for occurrence in context.occurrences:
        if not occurrence.is_confirmed:
            continue
        if "annual" not in occurrence.recurrence.lower():
            continue
        years = (occurrence.window_to - occurrence.window_from).days / 365.25
        instalments = max(int(round(years)) + 1, 1)
        if instalments < 2:
            continue
        converted = context.fx.to_usd(occurrence.amount, occurrence.currency)
        if converted.amount != converted.amount:
            continue
        schedule_usd = converted.amount * instalments
        if schedule_usd <= context.exposure.total_usd:
            continue

        builder = SignalBuilder(
            context.client_id,
            SignalType.DATA_CONFLICT,
            status=CaseStatus.ACTIVE,
            discriminator=f"SCHEDULE-{occurrence.need_id}",
        )
        need_item = builder.item(
            "need",
            f"Planned cash need {occurrence.need_id}",
            {
                "description": occurrence.description,
                "amount": occurrence.amount,
                "currency": occurrence.currency,
                "recurrence": occurrence.recurrence,
                "dueFrom": occurrence.window_from.isoformat(),
                "dueTo": occurrence.window_to.isoformat(),
            },
            file="planned_cash_needs.csv",
            record_key=occurrence.need_id,
            field_name="amount|recurrence|due_from|due_to",
        )
        wealth_item = builder.item(
            "wealth",
            "Total client wealth at the current snapshot",
            {"amount": context.exposure.total_usd, "currency": "USD"},
            file="holdings.csv",
            record_key=f"{context.client_id}|{context.snapshot}",
            field_name="market_value_usd",
        )
        builder.metric(
            f"schedule-{occurrence.need_id}",
            "Full recurring schedule against client wealth",
            "instalment amount x instalments over the stated window / client wealth x 100",
            {
                "instalmentAmount": occurrence.amount,
                "currency": occurrence.currency,
                "instalments": instalments,
                "scheduleUsd": schedule_usd,
                "clientWealthUsd": context.exposure.total_usd,
            },
            Measure(
                value=round(100.0 * schedule_usd / context.exposure.total_usd, 2),
                unit="percent",
            ),
            context.snapshot,
        )
        builder.conflict(
            f"schedule-{occurrence.need_id}",
            f"{occurrence.need_id} records {occurrence.currency} "
            f"{occurrence.amount:,.0f} with recurrence '{occurrence.recurrence}' running "
            f"from {occurrence.window_from.isoformat()} to "
            f"{occurrence.window_to.isoformat()}. Read as {instalments} instalments that "
            f"totals about USD {schedule_usd:,.0f}, which is more than this client's "
            f"entire wealth of USD {context.exposure.total_usd:,.0f}. Either the amount "
            "is the whole programme rather than one instalment, or the obligation is "
            "not fundable as recorded.",
            [need_item, wealth_item],
        )
        builder.interpretation(
            f"schedule-reading-{occurrence.need_id}",
            "The engine plans against a single instalment, which is the smaller and "
            "safer of the two readings, and flags the ambiguity rather than resolving "
            "it. The client's actual commitment needs confirming before any funding "
            "plan is built on it.",
            [need_item],
        )
        builder.deduct_confidence(
            "A recurring obligation's amount and schedule are ambiguous, and the two "
            "readings differ materially.",
            context.config["confidence"]["deductions"]["materialEvidenceConflict"],
        )
        return builder.finish(
            summary=(
                f"{occurrence.need_id} as recorded would total about USD "
                f"{schedule_usd:,.0f} over its window, more than this client's total "
                "wealth."
            ),
            time_horizon="over the stated window",
            severity_rank=68,
        )
    return None


def _totals_signal(context) -> DetectedSignal | None:
    reconciliation = context.reconciliation
    non_usd = [c for c in reconciliation.base_currencies if c != "USD"]
    if not reconciliation.is_material and not non_usd:
        return None

    builder = SignalBuilder(
        context.client_id,
        SignalType.DATA_CONFLICT,
        status=CaseStatus.ACTIVE if reconciliation.is_material else CaseStatus.NORMAL,
        discriminator="TOTALS",
    )

    client_item = builder.item(
        "client-total",
        "Client record total",
        {"amount": reconciliation.client_record_usd, "currency": "USD"},
        file=CLIENTS_FILE,
        record_key=context.client_id,
        field_name="total_aum_usd",
    )
    holdings_item = builder.item(
        "holdings-total",
        "Sum of holdings at the current snapshot",
        {"amount": reconciliation.holdings_usd, "currency": "USD"},
        file="holdings.csv",
        record_key=f"{context.client_id}|{context.snapshot}",
        field_name="market_value_usd",
    )
    portfolio_usd_item = builder.item(
        "portfolio-total-usd",
        "Portfolio record total, USD column",
        {"amount": reconciliation.portfolio_record_usd, "currency": "USD"},
        file=PORTFOLIOS_FILE,
        record_key=context.client_id,
        field_name="aum_usd_current",
    )
    portfolio_base_item = builder.item(
        "portfolio-total-base",
        "Portfolio record total, dated snapshot column",
        {
            "amount": reconciliation.portfolio_base_currency_total,
            "currency": "|".join(reconciliation.base_currencies),
        },
        file=PORTFOLIOS_FILE,
        record_key=context.client_id,
        field_name=f"aum_{context.snapshot}",
    )

    builder.metric(
        "totals-spread",
        "Largest disagreement between the three USD totals",
        "(max total - min total) / max total x 100",
        {
            "holdingsUsd": reconciliation.holdings_usd,
            "clientRecordUsd": reconciliation.client_record_usd,
            "portfolioRecordUsd": reconciliation.portfolio_record_usd,
        },
        Measure(value=round(reconciliation.max_difference_pct, 4), unit="percent"),
        context.snapshot,
    )

    if reconciliation.is_material:
        builder.conflict(
            "totals",
            f"The holdings, client and portfolio records state materially different "
            f"totals for this client: USD {reconciliation.holdings_usd:,.2f}, "
            f"USD {reconciliation.client_record_usd:,.2f} and "
            f"USD {reconciliation.portfolio_record_usd:,.2f}. The engine does not choose "
            "between them.",
            [holdings_item, client_item, portfolio_usd_item],
        )
        builder.deduct_confidence(
            "Sources disagree on this client's total wealth.",
            context.config["confidence"]["deductions"]["materialEvidenceConflict"],
        )
        summary = "Sources disagree on this client's total wealth."
        severity = 70
    else:
        currencies = ", ".join(non_usd)
        builder.fact(
            "totals-agree",
            f"The three supplied statements of this client's wealth agree to within "
            f"{reconciliation.max_difference_pct:.4f}%: holdings sum to "
            f"USD {reconciliation.holdings_usd:,.2f}, the client record states "
            f"USD {reconciliation.client_record_usd:,.2f} and the portfolio records state "
            f"USD {reconciliation.portfolio_record_usd:,.2f}.",
            [holdings_item, client_item, portfolio_usd_item],
        )
        builder.interpretation(
            "denomination",
            f"The dated portfolio column `aum_{context.snapshot}` reads "
            f"{reconciliation.portfolio_base_currency_total:,.2f}, which looks like a gap "
            f"against the USD totals. It is not one: that column is denominated in the "
            f"portfolio's base currency ({currencies}), and converting it at the "
            f"{context.snapshot} rate reproduces the USD total. Comparing the two columns "
            "directly would manufacture a disagreement that does not exist.",
            [portfolio_base_item, portfolio_usd_item],
        )
        builder.assumption(
            "fx-convention",
            "Conversion uses the market_context.csv pair in its quoted direction at the "
            "as-of date.",
            [portfolio_base_item],
        )
        summary = (
            "Totals reconcile across all three sources once base-currency columns are "
            "converted."
        )
        severity = 5

    return builder.finish(summary=summary, time_horizon="current", severity_rank=severity)


def _objective_amount_signal(context) -> DetectedSignal | None:
    """A number in the stated objectives that a planned obligation contradicts."""
    objectives = str(context.client["objectives"])
    stated = _extract_amounts(objectives)
    if not stated:
        return None

    needs = context.data.client_cash_needs(context.client_id)
    if needs.empty:
        return None

    for currency, amount in stated:
        candidates = needs[needs.currency == currency]
        if candidates.empty:
            continue
        row = min(
            (r for _, r in candidates.iterrows()),
            key=lambda r: abs(float(r["amount"]) - amount),
        )
        recorded = float(row["amount"])
        if recorded <= 0:
            continue
        difference_pct = 100.0 * abs(recorded - amount) / recorded
        if difference_pct < AMOUNT_CONFLICT_PCT or difference_pct > AMOUNT_UNRELATED_PCT:
            continue

        builder = SignalBuilder(
            context.client_id,
            SignalType.DATA_CONFLICT,
            status=CaseStatus.ACTIVE,
            discriminator="OBJECTIVE-AMOUNT",
        )
        objective_item = builder.item(
            "objective",
            "Stated objectives",
            objectives,
            file=CLIENTS_FILE,
            record_key=context.client_id,
            field_name="objectives",
        )
        need_item = builder.item(
            "planned-need",
            f"Planned cash need {row['need_id']}",
            {
                "description": str(row["description"]),
                "amount": recorded,
                "currency": currency,
                "recurrence": str(row["recurrence"]),
                "certainty": str(row["certainty"]),
            },
            file="planned_cash_needs.csv",
            record_key=str(row["need_id"]),
            field_name="amount",
        )
        builder.metric(
            "objective-gap",
            "Difference between the stated objective and the planned obligation",
            "abs(planned amount - stated amount) / planned amount x 100",
            {
                "statedAmount": amount,
                "plannedAmount": recorded,
                "currency": currency,
            },
            Measure(value=round(difference_pct, 4), unit="percent"),
            context.snapshot,
        )
        builder.conflict(
            "objective-amount",
            f"The client's recorded objectives describe {currency} {amount:,.0f}, while "
            f"{row['need_id']} records {currency} {recorded:,.0f} for "
            f"{str(row['description']).lower()} — {difference_pct:.1f}% higher. Both "
            "figures are supplied and the engine does not choose between them.",
            [objective_item, need_item],
        )
        builder.interpretation(
            "objective-amount",
            "Planning against the lower figure would understate what the portfolio is "
            "being asked to fund. Which number is current is a question for the RM to "
            "settle with the client.",
            [objective_item, need_item],
        )
        builder.deduct_confidence(
            "The stated objective and the planned obligation disagree on the amount.",
            context.config["confidence"]["deductions"]["materialEvidenceConflict"],
        )
        return builder.finish(
            summary=(
                f"The stated objective ({currency} {amount:,.0f}) and the recorded "
                f"obligation ({currency} {recorded:,.0f}) disagree."
            ),
            time_horizon="current",
            severity_rank=65,
        )
    return None


def _stale_valuation_signal(context) -> DetectedSignal | None:
    if not context.stale_valuations:
        return None

    builder = SignalBuilder(
        context.client_id,
        SignalType.DATA_CONFLICT,
        status=CaseStatus.NORMAL,
        discriminator="STALE-VALUATION",
    )
    item_ids = []
    total = 0.0
    max_lag = 0
    for stale in context.stale_valuations:
        total += stale["market_value_usd"]
        max_lag = max(max_lag, stale["lag_days"])
        item_ids.append(
            builder.item(
                f"stale-{stale['instrument_id']}",
                f"{stale['instrument_name']} valuation date",
                {
                    "valuationDate": stale["valuation_date"],
                    "snapshotDate": stale["snapshot_date"],
                    "lagDays": stale["lag_days"],
                    "marketValueUsd": stale["market_value_usd"],
                    "liquidityTier": stale["liquidity_tier"],
                },
                file="holdings.csv",
                record_key=(
                    f"{stale['portfolio_id']}|{stale['instrument_id']}|{stale['snapshot_date']}"
                ),
                field_name="valuation_date",
            )
        )

    builder.fact(
        "stale",
        f"USD {total:,.0f} of this client's holdings are carried at a valuation up to "
        f"{max_lag} days older than the snapshot date.",
        item_ids,
    )
    builder.interpretation(
        "stale",
        "Private markets report on a lag, so an older mark is normal rather than an "
        "error. It does mean the current value is an estimate, and any conclusion that "
        "depends on it is correspondingly less precise.",
        item_ids,
    )
    builder.deduct_confidence(
        "A holding relevant to this client's total is carried at a stale valuation.",
        context.config["confidence"]["deductions"]["staleValuationRelevantToConclusion"],
    )
    return builder.finish(
        summary=(
            f"USD {total:,.0f} is valued as at a date up to {max_lag} days before the "
            "snapshot."
        ),
        time_horizon="current",
        severity_rank=30,
    )


def _extract_amounts(text: str) -> list[tuple[str, float]]:
    amounts: list[tuple[str, float]] = []
    for currency, digits, suffix in _AMOUNT.findall(text):
        value = float(digits.replace(",", ""))
        if suffix:
            value *= _MULTIPLIERS[suffix.lower()]
        amounts.append((currency.upper(), value))
    return amounts

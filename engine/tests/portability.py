"""Helpers that rebuild the supplied Book under a different identity scheme.

Portability cannot be proved by reading code. It is proved by feeding the
engine a Book whose every identifier, relationship manager, booking centre and
reporting currency differs from the demonstration data, and checking that the
answers still come out — and still come from the new records.

The remapping is deliberately hostile to hidden assumptions: identifier shapes
change, not just their digits, so anything that pattern-matches `CL-0001` or
`SYN-EQ-0007` breaks loudly instead of quietly working.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd

# Canonical identifier columns, and the table each identifier is defined in.
# Every other appearance is a foreign key and must be rewritten with it.
ID_COLUMNS = (
    "client_id",
    "portfolio_id",
    "collateral_portfolio_id",
    "instrument_id",
    "facility_id",
    "commitment_id",
    "need_id",
    "transaction_id",
    "mandate_code",
    "rm_id",
)

CSV_FILES = (
    "clients.csv",
    "portfolios.csv",
    "holdings.csv",
    "instruments.csv",
    "mandates.csv",
    "transactions.csv",
    "credit_facilities.csv",
    "commitments.csv",
    "planned_cash_needs.csv",
    "market_context.csv",
    "event_log.csv",
)


@dataclass
class RemapPlan:
    """The identity substitutions applied to a copy of a Book."""

    clients: dict[str, str] = field(default_factory=dict)
    portfolios: dict[str, str] = field(default_factory=dict)
    instruments: dict[str, str] = field(default_factory=dict)
    facilities: dict[str, str] = field(default_factory=dict)
    commitments: dict[str, str] = field(default_factory=dict)
    needs: dict[str, str] = field(default_factory=dict)
    transactions: dict[str, str] = field(default_factory=dict)
    notes: dict[str, str] = field(default_factory=dict)
    mandates: dict[str, str] = field(default_factory=dict)
    client_names: dict[str, str] = field(default_factory=dict)
    booking_centres: dict[str, str] = field(default_factory=dict)
    rm_id: tuple[str, str] = ("", "")
    rm_name: tuple[str, str] = ("", "")
    recurrenced_currency: tuple[str, str, str] = ("", "", "")

    def all_id_substitutions(self) -> dict[str, str]:
        combined: dict[str, str] = {}
        for mapping in (
            self.clients,
            self.portfolios,
            self.instruments,
            self.facilities,
            self.commitments,
            self.needs,
            self.transactions,
            self.notes,
            self.mandates,
        ):
            combined.update(mapping)
        if self.rm_id[0]:
            combined[self.rm_id[0]] = self.rm_id[1]
        return combined


# Deliberately different shapes from the SingHacks scheme.
_PREFIXES = {
    "clients": "ZCLI",
    "portfolios": "ZACC",
    "instruments": "ZSEC",
    "facilities": "ZLOAN",
    "commitments": "ZPLEDGE",
    "needs": "ZOBLIG",
    "transactions": "ZMOVE",
    "notes": "ZMEMO",
    "mandates": "ZMDT",
}

_BOOKING_CENTRES = {"Singapore": "Zurich", "Hong Kong": "Geneva"}

_REPLACEMENT_NAMES = (
    "Adaeze Okonkwo", "Bjorn Halvorsen", "Camila Restrepo", "Dmitri Volkov",
    "Eleni Papadaki", "Farida Haddad", "Gustavo Pereira", "Hana Yildirim",
    "Ines Marchetti", "Jonas Lindgren", "Kwame Mensah", "Lucia Fernandez",
    "Mateo Silva", "Noor Rahmani", "Otto Brenner", "Petra Novak",
    "Quentin Dubois", "Rania Aziz", "Sten Karlsson", "Tomas Horak",
)


def _sequential(values: list[str], prefix: str) -> dict[str, str]:
    return {
        original: f"{prefix}-{index:04d}"
        for index, original in enumerate(sorted(values), start=1)
    }


def build_plan(source: Path, *, switch_currency_for: str | None = None) -> RemapPlan:
    """Derive a complete substitution plan from a canonical Book."""
    clients = pd.read_csv(source / "clients.csv")
    portfolios = pd.read_csv(source / "portfolios.csv")
    instruments = pd.read_csv(source / "instruments.csv")
    facilities = pd.read_csv(source / "credit_facilities.csv")
    commitments = pd.read_csv(source / "commitments.csv")
    needs = pd.read_csv(source / "planned_cash_needs.csv")
    transactions = pd.read_csv(source / "transactions.csv")
    mandates = pd.read_csv(source / "mandates.csv")
    with (source / "rm_notes.json").open(encoding="utf-8") as handle:
        notes = json.load(handle)

    plan = RemapPlan(
        clients=_sequential(clients.client_id.astype(str).tolist(), _PREFIXES["clients"]),
        portfolios=_sequential(
            portfolios.portfolio_id.astype(str).tolist(), _PREFIXES["portfolios"]
        ),
        instruments=_sequential(
            instruments.instrument_id.astype(str).tolist(), _PREFIXES["instruments"]
        ),
        facilities=_sequential(
            facilities.facility_id.astype(str).tolist(), _PREFIXES["facilities"]
        ),
        commitments=_sequential(
            commitments.commitment_id.astype(str).tolist(), _PREFIXES["commitments"]
        ),
        needs=_sequential(needs.need_id.astype(str).tolist(), _PREFIXES["needs"]),
        transactions=_sequential(
            transactions.transaction_id.astype(str).tolist(), _PREFIXES["transactions"]
        ),
        notes=_sequential([str(n["note_id"]) for n in notes], _PREFIXES["notes"]),
        mandates=_sequential(
            mandates.mandate_code.astype(str).unique().tolist(), _PREFIXES["mandates"]
        ),
        booking_centres=dict(_BOOKING_CENTRES),
        rm_id=(str(clients.rm_id.iloc[0]), "RM-ZH-900"),
        rm_name=(str(clients.rm_name.iloc[0]), "Adaeze Okonkwo"),
    )
    plan.client_names = {
        str(original): _REPLACEMENT_NAMES[index % len(_REPLACEMENT_NAMES)]
        for index, original in enumerate(sorted(clients.client_name.astype(str)))
    }
    if switch_currency_for:
        plan.recurrenced_currency = (switch_currency_for, "USD", "SGD")
    return plan


def _substitute_frame(frame: pd.DataFrame, plan: RemapPlan) -> pd.DataFrame:
    substitutions = plan.all_id_substitutions()
    frame = frame.copy()
    for column in frame.columns:
        if column in ID_COLUMNS:
            frame[column] = frame[column].map(
                lambda value: substitutions.get(str(value), value)
            )
    if "rm_name" in frame.columns:
        frame["rm_name"] = frame["rm_name"].replace({plan.rm_name[0]: plan.rm_name[1]})
    if "client_name" in frame.columns:
        frame["client_name"] = frame["client_name"].map(
            lambda value: plan.client_names.get(str(value), value)
        )
    if "booking_centre" in frame.columns:
        frame["booking_centre"] = frame["booking_centre"].map(
            lambda value: plan.booking_centres.get(str(value), value)
        )
    return frame


def _switch_currency(target: Path, plan: RemapPlan) -> None:
    """Move one client's portfolios to a different base currency.

    Base-currency values are recomputed at each snapshot's own supplied rate,
    so the Book stays internally consistent rather than merely relabelled.
    """
    client_id, from_ccy, to_ccy = plan.recurrenced_currency
    if not client_id:
        return
    mapped_client = plan.clients.get(client_id, client_id)

    market = pd.read_csv(target / "market_context.csv")
    pair = f"{from_ccy}{to_ccy}"
    rates = {
        str(row.snapshot_date): float(row.value)
        for row in market.itertuples()
        if str(row.series_id) == pair
    }
    if not rates:
        raise ValueError(f"No {pair} rate supplied; cannot switch currency safely.")

    portfolios = pd.read_csv(target / "portfolios.csv")
    rows = portfolios.client_id.astype(str) == mapped_client
    if not rows.any():
        raise ValueError(f"{mapped_client} has no portfolios to convert.")
    affected = set(portfolios.loc[rows, "portfolio_id"].astype(str))
    portfolios.loc[rows, "base_currency"] = to_ccy
    for snapshot, rate in rates.items():
        column = f"aum_{snapshot}"
        if column in portfolios.columns:
            portfolios.loc[rows, column] = portfolios.loc[rows, column] * rate
    portfolios.to_csv(target / "portfolios.csv", index=False)

    holdings = pd.read_csv(target / "holdings.csv")
    mask = holdings.portfolio_id.astype(str).isin(affected)
    holdings.loc[mask, "portfolio_ccy"] = to_ccy
    for snapshot, rate in rates.items():
        snap = mask & (holdings.snapshot_date.astype(str) == snapshot)
        holdings.loc[snap, "market_value_base"] = holdings.loc[snap, "market_value_base"] * rate
        holdings.loc[snap, "cost_basis_base"] = holdings.loc[snap, "cost_basis_base"] * rate
        holdings.loc[snap, "unrealised_pnl_base"] = (
            holdings.loc[snap, "unrealised_pnl_base"] * rate
        )
        holdings.loc[snap, "lending_value_base"] = (
            holdings.loc[snap, "lending_value_base"] * rate
        )
    holdings.to_csv(target / "holdings.csv", index=False)


def write_remapped_book(
    source: Path, target: Path, plan: RemapPlan | None = None
) -> RemapPlan:
    """Write a copy of `source` into `target` under a new identity scheme."""
    plan = plan or build_plan(source)
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True)

    for name in CSV_FILES:
        frame = pd.read_csv(source / name)
        _substitute_frame(frame, plan).to_csv(target / name, index=False)

    with (source / "rm_notes.json").open(encoding="utf-8") as handle:
        notes = json.load(handle)
    substitutions = plan.all_id_substitutions()
    for note in notes:
        note["note_id"] = plan.notes.get(str(note["note_id"]), note["note_id"])
        note["client_id"] = substitutions.get(str(note["client_id"]), note["client_id"])
        note["rm_id"] = substitutions.get(str(note["rm_id"]), note["rm_id"])
        if note.get("rm_name") == plan.rm_name[0]:
            note["rm_name"] = plan.rm_name[1]
    with (target / "rm_notes.json").open("w", encoding="utf-8") as handle:
        json.dump(notes, handle, indent=2)

    if plan.recurrenced_currency[0]:
        _switch_currency(target, plan)
    return plan


def singhacks_identifiers(source: Path) -> set[str]:
    """Every identifier and name the SingHacks Book uses.

    A remapped artifact that still contains one of these is leaking the
    demonstration dataset into a Book that should not know about it.
    """
    clients = pd.read_csv(source / "clients.csv")
    portfolios = pd.read_csv(source / "portfolios.csv")
    instruments = pd.read_csv(source / "instruments.csv")
    facilities = pd.read_csv(source / "credit_facilities.csv")
    values: set[str] = set()
    values.update(clients.client_id.astype(str))
    values.update(clients.client_name.astype(str))
    values.update(clients.rm_id.astype(str))
    values.update(clients.rm_name.astype(str))
    values.update(portfolios.portfolio_id.astype(str))
    values.update(instruments.instrument_id.astype(str))
    values.update(facilities.facility_id.astype(str))
    return values

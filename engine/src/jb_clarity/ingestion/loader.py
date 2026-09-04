"""Load the supplied challenge files into typed, indexed frames.

Nothing here interprets the data. Loading fails loudly on a missing file, and
records rather than repairs anything unexpected inside one.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

import pandas as pd

REQUIRED_FILES = (
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
    "rm_notes.json",
)

# Identifier columns are read as strings so that a stable record key never
# becomes a float through type inference.
_ID_COLUMNS = (
    "client_id",
    "portfolio_id",
    "instrument_id",
    "facility_id",
    "commitment_id",
    "need_id",
    "transaction_id",
    "mandate_code",
    "rm_id",
    "series_id",
    "note_id",
)


@dataclass(frozen=True)
class RmNote:
    """One dated relationship-manager note."""

    note_id: str
    client_id: str
    note_date: date
    rm_id: str
    rm_name: str
    channel: str
    note: str


@dataclass
class ChallengeData:
    """Every supplied source, indexed for deterministic lookup."""

    root: Path
    clients: pd.DataFrame
    portfolios: pd.DataFrame
    holdings: pd.DataFrame
    instruments: pd.DataFrame
    mandates: pd.DataFrame
    transactions: pd.DataFrame
    facilities: pd.DataFrame
    commitments: pd.DataFrame
    cash_needs: pd.DataFrame
    market: pd.DataFrame
    events: pd.DataFrame
    notes: list[RmNote] = field(default_factory=list)

    @property
    def snapshot_dates(self) -> list[str]:
        """The five supplied snapshot dates, chronologically ordered."""
        return sorted(self.holdings["snapshot_date"].unique().tolist())

    @property
    def latest_snapshot(self) -> str:
        return self.snapshot_dates[-1]

    def client_ids(self) -> list[str]:
        return sorted(self.clients["client_id"].tolist())

    def client(self, client_id: str) -> pd.Series:
        return self.clients.loc[self.clients.client_id == client_id].iloc[0]

    def client_portfolios(self, client_id: str) -> pd.DataFrame:
        return self.portfolios.loc[self.portfolios.client_id == client_id]

    def holdings_at(self, snapshot: str, client_id: str | None = None) -> pd.DataFrame:
        frame = self.holdings.loc[self.holdings.snapshot_date == snapshot]
        if client_id is not None:
            frame = frame.loc[frame.client_id == client_id]
        return frame

    def instrument(self, instrument_id: str) -> pd.Series:
        return self.instruments.loc[self.instruments.instrument_id == instrument_id].iloc[0]

    def mandate_bands(self, mandate_code: str) -> pd.DataFrame:
        return self.mandates.loc[self.mandates.mandate_code == mandate_code]

    def client_notes(self, client_id: str) -> list[RmNote]:
        return sorted(
            (n for n in self.notes if n.client_id == client_id),
            key=lambda n: (n.note_date, n.note_id),
        )

    def client_facilities(self, client_id: str) -> pd.DataFrame:
        return self.facilities.loc[self.facilities.client_id == client_id]

    def client_cash_needs(self, client_id: str) -> pd.DataFrame:
        return self.cash_needs.loc[self.cash_needs.client_id == client_id]

    def client_commitments(self, client_id: str) -> pd.DataFrame:
        return self.commitments.loc[self.commitments.client_id == client_id]

    def market_value(self, series_id: str, snapshot: str) -> float | None:
        row = self.market.loc[
            (self.market.series_id == series_id) & (self.market.snapshot_date == snapshot)
        ]
        if row.empty:
            return None
        return float(row.iloc[0]["value"])


def _read_csv(path: Path) -> pd.DataFrame:
    frame = pd.read_csv(path)
    for column in frame.columns:
        if column in _ID_COLUMNS:
            frame[column] = frame[column].astype("string")
    return frame


def load_challenge_data(data_dir: Path) -> ChallengeData:
    """Load every supplied source file from `data_dir`."""
    data_dir = Path(data_dir)
    missing = [name for name in REQUIRED_FILES if not (data_dir / name).exists()]
    if missing:
        raise FileNotFoundError(
            f"Missing challenge files in {data_dir}: {', '.join(sorted(missing))}"
        )

    with (data_dir / "rm_notes.json").open(encoding="utf-8") as handle:
        raw_notes = json.load(handle)

    notes = [
        RmNote(
            note_id=str(item["note_id"]),
            client_id=str(item["client_id"]),
            note_date=date.fromisoformat(item["note_date"]),
            rm_id=str(item["rm_id"]),
            rm_name=str(item["rm_name"]),
            channel=str(item["channel"]),
            note=str(item["note"]),
        )
        for item in raw_notes
    ]

    return ChallengeData(
        root=data_dir,
        clients=_read_csv(data_dir / "clients.csv"),
        portfolios=_read_csv(data_dir / "portfolios.csv"),
        holdings=_read_csv(data_dir / "holdings.csv"),
        instruments=_read_csv(data_dir / "instruments.csv"),
        mandates=_read_csv(data_dir / "mandates.csv"),
        transactions=_read_csv(data_dir / "transactions.csv"),
        facilities=_read_csv(data_dir / "credit_facilities.csv"),
        commitments=_read_csv(data_dir / "commitments.csv"),
        cash_needs=_read_csv(data_dir / "planned_cash_needs.csv"),
        market=_read_csv(data_dir / "market_context.csv"),
        events=_read_csv(data_dir / "event_log.csv"),
        notes=sorted(notes, key=lambda n: (n.client_id, n.note_date, n.note_id)),
    )

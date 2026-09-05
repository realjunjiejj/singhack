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

from jb_clarity.ingestion import source_contract

REQUIRED_FILES = tuple(
    contract.default_filename for contract in source_contract.TABLES.values()
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
        """The snapshot dates this Book supplies, chronologically ordered.

        Discovered from holdings and validated by the source contract; the
        engine never assumes how many there are.
        """
        return source_contract.discover_snapshots(
            self.holdings["snapshot_date"].tolist(), "holdings.csv"
        )

    @property
    def snapshot_count(self) -> int:
        return len(self.snapshot_dates)

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


def _read_csv(path: Path, contract: source_contract.TableContract) -> pd.DataFrame:
    """Read one canonical table with contract-declared parse-time types.

    Identifier columns are given to pandas as strings up front rather than
    cast afterwards, because inference has already destroyed a key like `0001`
    by the time a later `astype` runs.
    """
    try:
        frame = pd.read_csv(path, dtype=contract.dtype_map())
    except ValueError as error:
        raise source_contract.SourceContractError(
            f"{contract.default_filename}: could not parse with the declared "
            f"column types for table '{contract.canonical_name}'. {error}"
        ) from error

    missing = sorted(set(contract.required_columns) - set(frame.columns))
    if missing:
        raise source_contract.SourceContractError(
            f"{contract.default_filename} is missing required column(s): "
            f"{', '.join(missing)}. Table '{contract.canonical_name}' has grain: "
            f"{contract.grain}."
        )
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

    notes = [_read_note(item, index) for index, item in enumerate(raw_notes)]

    def read(name: str) -> pd.DataFrame:
        contract = source_contract.table(name)
        return _read_csv(data_dir / contract.default_filename, contract)

    return ChallengeData(
        root=data_dir,
        clients=read("clients"),
        portfolios=read("portfolios"),
        holdings=read("holdings"),
        instruments=read("instruments"),
        mandates=read("mandates"),
        transactions=read("transactions"),
        facilities=read("credit_facilities"),
        commitments=read("commitments"),
        cash_needs=read("planned_cash_needs"),
        market=read("market_context"),
        events=read("event_log"),
        notes=sorted(notes, key=lambda n: (n.client_id, n.note_date, n.note_id)),
    )


def _read_note(item: dict, index: int) -> RmNote:
    """Parse one note, naming the record and field when it is malformed."""
    contract = source_contract.RM_NOTES
    where = f"rm_notes.json record {index} ({item.get('note_id', 'no note_id')})"
    missing = sorted(set(contract.required_columns) - set(item))
    if missing:
        raise source_contract.SourceContractError(
            f"{where} is missing required field(s): {', '.join(missing)}."
        )
    try:
        note_date = date.fromisoformat(str(item["note_date"]))
    except ValueError as error:
        raise source_contract.SourceContractError(
            f"{where} has note_date '{item['note_date']}', which is not an ISO "
            "date (YYYY-MM-DD)."
        ) from error
    return RmNote(
        note_id=str(item["note_id"]),
        client_id=str(item["client_id"]),
        note_date=note_date,
        rm_id=str(item.get("rm_id", "")),
        rm_name=str(item.get("rm_name", "")),
        channel=str(item.get("channel", "Note")),
        note=str(item["note"]),
    )

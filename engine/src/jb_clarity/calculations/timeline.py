"""Five-snapshot timelines and grounded event linkage.

`event_log.csv` is the Controlled Event Source. An event is only connected to a
client when one of its declared transmission channels defensibly maps to
something that client actually holds, and the connection is always phrased as
an explanation supported by the event record rather than proven causation.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from jb_clarity.ingestion.loader import ChallengeData

# A transmission channel matches a holding when the channel's key appears in
# the event's `primary_transmission` and the predicate below holds. Anything
# not listed here produces no link, which is preferable to a plausible guess.
_CHANNEL_RULES: dict[str, dict[str, tuple[str, ...]]] = {
    "gold": {"sector": ("Gold",), "sub_asset_class": ("Precious Metals",)},
    "precious metals": {"sector": ("Gold",), "sub_asset_class": ("Precious Metals",)},
    "inflation hedges": {"sector": ("Gold",), "sub_asset_class": ("Inflation Linked",)},
    "inflation-sensitive assets": {"sub_asset_class": ("Inflation Linked",), "sector": ("Gold",)},
    "energy": {"sector": ("Energy",)},
    "lng": {"sector": ("Energy",)},
    "shipping": {"name": ("shipping", "marine", "orient")},
    "transport": {"name": ("shipping", "marine", "orient")},
    "us technology": {"sector": ("Information Technology",)},
    "concentrated equity": {"sub_asset_class": ("Single Stock",)},
    "duration": {"sub_asset_class": ("Government Bond", "Subordinated Perpetual")},
    "long-duration fixed income": {
        "sub_asset_class": ("Government Bond", "Subordinated Perpetual")
    },
    "rate-sensitive credit": {
        "sub_asset_class": ("Investment Grade Credit", "High Yield Credit")
    },
    "growth equity valuations": {"sector": ("Information Technology",)},
    "european fixed income": {"currency_asset": ("EUR|Fixed Income",)},
    "eur assets": {"currency": ("EUR",)},
    "private credit": {"sub_asset_class": ("Private Credit",)},
    "semi-liquid alternatives": {"liquidity_tier": ("Quarterly Gate",)},
    "em credit": {"sub_asset_class": ("Emerging Market Debt",)},
    "oil-linked structured products": {"underlying": ("energy", "oil", "brent")},
}


@dataclass(frozen=True)
class SnapshotPoint:
    snapshot_date: str
    total_usd: float
    by_asset_class_usd: dict[str, float]

    def asset_class_usd(self, asset_class: str) -> float:
        return self.by_asset_class_usd.get(asset_class, 0.0)


@dataclass
class ClientTimeline:
    client_id: str
    points: list[SnapshotPoint] = field(default_factory=list)

    @property
    def first(self) -> SnapshotPoint:
        return self.points[0]

    @property
    def last(self) -> SnapshotPoint:
        return self.points[-1]

    @property
    def change_usd(self) -> float:
        return self.last.total_usd - self.first.total_usd

    @property
    def change_pct(self) -> float:
        if not self.first.total_usd:
            return 0.0
        return 100.0 * self.change_usd / self.first.total_usd

    def asset_class_change_usd(self, asset_class: str) -> float:
        return self.last.asset_class_usd(asset_class) - self.first.asset_class_usd(asset_class)


@dataclass(frozen=True)
class EventLink:
    """One Controlled Event Source record connected to a client's holdings."""

    event_index: int
    event_date: str
    event_type: str
    region: str
    description: str
    primary_transmission: str
    severity: str
    matched_channels: tuple[str, ...]
    matched_instruments: tuple[tuple[str, str, float], ...]
    # Which holdings each individual channel reached. Keeping this split
    # matters: a single-stock energy position can match a generic
    # "concentrated equity" channel, and reporting it under a technology
    # event's headline would be indefensible in front of a client.
    matches_by_channel: tuple[tuple[str, tuple[tuple[str, str, float], ...]], ...] = ()

    @property
    def matched_value_usd(self) -> float:
        return sum(value for _, _, value in self.matched_instruments)


def build_client_timeline(data: ChallengeData, client_id: str) -> ClientTimeline:
    """Total and asset-class values at each of the five supplied snapshots."""
    timeline = ClientTimeline(client_id=client_id)
    for snapshot in data.snapshot_dates:
        holdings = data.holdings_at(snapshot, client_id)
        timeline.points.append(
            SnapshotPoint(
                snapshot_date=snapshot,
                total_usd=float(holdings["market_value_usd"].sum()),
                by_asset_class_usd={
                    str(k): float(v)
                    for k, v in holdings.groupby("asset_class", dropna=False)[
                        "market_value_usd"
                    ]
                    .sum()
                    .items()
                },
            )
        )
    return timeline


def _instrument_matches(instrument: pd.Series, rule: dict[str, tuple[str, ...]]) -> bool:
    for attribute, wanted in rule.items():
        if attribute == "name":
            haystack = str(instrument.get("instrument_name", "")).lower()
            if any(token in haystack for token in wanted):
                return True
        elif attribute == "underlying":
            haystack = str(instrument.get("underlying_reference", "")).lower()
            if any(token in haystack for token in wanted):
                return True
        elif attribute == "currency_asset":
            combined = f"{instrument.get('currency')}|{instrument.get('asset_class')}"
            if combined in wanted:
                return True
        else:
            if str(instrument.get(attribute, "")) in wanted:
                return True
    return False


def link_events(
    data: ChallengeData, client_id: str, snapshot: str, minimum_usd: float = 0.0
) -> list[EventLink]:
    """Connect Controlled Event Source records to what the client holds."""
    holdings = data.holdings_at(snapshot, client_id)
    if holdings.empty:
        return []

    instruments = data.instruments.set_index("instrument_id")
    positions = (
        holdings.groupby(["instrument_id", "instrument_name"], dropna=False)[
            "market_value_usd"
        ]
        .sum()
        .reset_index()
    )

    links: list[EventLink] = []
    for index, event in data.events.iterrows():
        transmission = str(event["primary_transmission"])
        channels = [c.strip() for c in transmission.split(",") if c.strip()]

        matched_channels: list[str] = []
        matched: dict[str, tuple[str, str, float]] = {}
        by_channel: list[tuple[str, tuple[tuple[str, str, float], ...]]] = []

        for channel in channels:
            rule = _CHANNEL_RULES.get(channel.lower())
            if rule is None:
                continue
            channel_hits = []
            for row in positions.itertuples():
                instrument_id = str(row.instrument_id)
                if instrument_id not in instruments.index:
                    continue
                if _instrument_matches(instruments.loc[instrument_id], rule):
                    channel_hits.append(
                        (instrument_id, str(row.instrument_name), float(row.market_value_usd))
                    )
            if channel_hits:
                matched_channels.append(channel)
                channel_hits.sort(key=lambda hit: -hit[2])
                by_channel.append((channel, tuple(channel_hits)))
                for hit in channel_hits:
                    matched[hit[0]] = hit

        if not matched:
            continue
        total = sum(v for _, _, v in matched.values())
        if total < minimum_usd:
            continue

        links.append(
            EventLink(
                event_index=int(index),
                event_date=str(event["event_date"]),
                event_type=str(event["event_type"]),
                region=str(event["region"]),
                description=str(event["description"]),
                primary_transmission=str(event["primary_transmission"]),
                severity=str(event["severity"]),
                matched_channels=tuple(matched_channels),
                matched_instruments=tuple(
                    sorted(matched.values(), key=lambda item: -item[2])
                ),
                matches_by_channel=tuple(by_channel),
            )
        )

    return sorted(links, key=lambda link: (link.event_date, link.event_index))

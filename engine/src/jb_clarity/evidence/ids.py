"""Stable identifier construction.

Identifiers are derived from the data, never from iteration order, so two runs
over the same inputs produce the same identifiers and Builder 2 can bookmark a
case or packet safely.
"""

from __future__ import annotations

from jb_clarity.domain.enums import SignalType


def _slug(signal_type: SignalType | str) -> str:
    return str(signal_type).upper().replace("-", "_").replace(" ", "_")


def case_id(client_id: str) -> str:
    return f"CASE-{client_id}"


def packet_id(client_id: str, signal_type: SignalType | str) -> str:
    return f"PACKET-{client_id}-{_slug(signal_type)}"


def signal_id(client_id: str, signal_type: SignalType | str, discriminator: str = "") -> str:
    base = f"SIG-{client_id}-{_slug(signal_type)}"
    return f"{base}-{discriminator}" if discriminator else base


def evidence_item_id(client_id: str, signal_type: SignalType | str, key: str) -> str:
    return f"EV-{client_id}-{_slug(signal_type)}-{_slug(key)}"


def claim_id(prefix: str, client_id: str, signal_type: SignalType | str, key: str) -> str:
    return f"{prefix}-{client_id}-{_slug(signal_type)}-{_slug(key)}"


def metric_id(client_id: str, signal_type: SignalType | str, key: str) -> str:
    return f"M-{client_id}-{_slug(signal_type)}-{_slug(key)}"


def open_loop_id(client_id: str, note_id: str, category: str) -> str:
    """One note can carry more than one kind of loop, so the category is part
    of the identifier."""
    return f"OL-{client_id}-{note_id}-{_slug(category)}"


def governance_clock_id(client_id: str, kind: str) -> str:
    return f"GOV-{client_id}-{_slug(kind)}"

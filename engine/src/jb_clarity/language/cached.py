"""Loading cached Client-Ready drafts from validated fixtures.

Fixtures hold reviewed wording for the deep cases, including the client's own
reporting language. They are data, not prompts, and they are validated against
the generated Evidence Packets on every build.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

FIXTURE_DIR = Path(__file__).parent / "fixtures"


@dataclass(frozen=True)
class CachedDraft:
    client_id: str
    language: str
    canonical_language: str
    content: str
    evidence_item_ids: tuple[str, ...]


@lru_cache(maxsize=1)
def load_fixtures() -> tuple[CachedDraft, ...]:
    """Every cached draft shipped with the engine, ordered deterministically."""
    drafts: list[CachedDraft] = []
    if not FIXTURE_DIR.exists():
        return ()
    for path in sorted(FIXTURE_DIR.glob("*.json")):
        with path.open(encoding="utf-8") as handle:
            payload = json.load(handle)
        drafts.append(
            CachedDraft(
                client_id=str(payload["clientId"]),
                language=str(payload["language"]),
                canonical_language=str(payload["canonicalLanguage"]),
                content=str(payload["content"]),
                evidence_item_ids=tuple(payload.get("evidenceItemIds", [])),
            )
        )
    return tuple(drafts)


def drafts_for(client_id: str) -> list[CachedDraft]:
    return [draft for draft in load_fixtures() if draft.client_id == client_id]

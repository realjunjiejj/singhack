"""Small helpers for text the Relationship Manager actually reads.

"2 holding(s)" is the sort of thing that tells a client they are looking at
machine output. Everything the RM sees should read as though a person wrote it.
"""

from __future__ import annotations


def count_noun(count: int, singular: str, plural: str | None = None) -> str:
    """Render a count with a correctly inflected noun: `1 holding`, `2 holdings`."""
    if plural is None:
        plural = f"{singular}s"
    return f"{count} {singular if count == 1 else plural}"


def count_verb(count: int, singular: str, plural: str) -> str:
    """Render a count with an agreeing verb: `1 holding falls`, `2 holdings fall`."""
    return singular if count == 1 else plural


def sentence(text: str) -> str:
    """Capitalise a fragment so joined sentences read correctly."""
    text = text.strip()
    if not text:
        return text
    return text[0].upper() + text[1:]

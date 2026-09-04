"""Validation for any Client-Ready draft, cached or generated.

Language may re-word a conclusion. It may never change a number, invent a
citation, or introduce a fact the Evidence Packet does not contain. A draft
that breaks any of those rules is rejected and the cached content stands.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# Numbers that carry financial meaning: amounts, percentages, dates and years.
# Thousands separators and decimal points are normalised so that formatting
# differences between languages are not mistaken for changed figures.
_NUMBER = re.compile(r"\d[\d,.  ]*\d|\d")


@dataclass
class ValidationResult:
    ok: bool
    errors: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:  # pragma: no cover - trivial
        return self.ok


def financial_tokens(text: str) -> set[str]:
    """Every numeric token in `text`, normalised for comparison."""
    tokens = set()
    for raw in _NUMBER.findall(text):
        cleaned = raw.replace(",", "").replace(" ", "").replace(" ", "")
        cleaned = cleaned.rstrip(".")
        if cleaned:
            tokens.add(cleaned)
    return tokens


def validate_draft(
    content: str,
    canonical_content: str,
    cited_item_ids: list[str],
    available_item_ids: set[str],
) -> ValidationResult:
    """Check one draft against its canonical version and its packet."""
    errors: list[str] = []

    unknown = sorted(set(cited_item_ids) - available_item_ids)
    if unknown:
        errors.append(
            "Draft cites evidence items that are not in this client's packets: "
            + ", ".join(unknown)
        )

    canonical_tokens = financial_tokens(canonical_content)
    draft_tokens = financial_tokens(content)

    introduced = sorted(draft_tokens - canonical_tokens)
    if introduced:
        errors.append(
            "Draft introduces figures absent from the canonical version: "
            + ", ".join(introduced)
        )

    missing = sorted(canonical_tokens - draft_tokens)
    if missing:
        errors.append(
            "Draft drops figures present in the canonical version: " + ", ".join(missing)
        )

    if not cited_item_ids:
        errors.append("Draft cites no evidence items.")

    return ValidationResult(ok=not errors, errors=errors)

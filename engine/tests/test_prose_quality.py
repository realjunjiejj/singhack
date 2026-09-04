"""Everything the RM reads must be well-formed and traceable.

An insight an RM cannot read aloud in a meeting is not usable, and a figure
that appears in prose but nowhere in the evidence is exactly the confident
fabrication the engine exists to prevent.
"""

from __future__ import annotations

import json
import re

import pytest

# Words that mean a template leaked instead of rendering. Matched on word
# boundaries because "financing" legitimately contains "nan".
PLACEHOLDER = re.compile(
    r"(?<![A-Za-z])(nan|None|TODO|FIXME|null|undefined|Infinity)(?![A-Za-z])"
)
# Only audit figures large enough to be a financial quantity; percentages and
# small ordinals are checked by their own tests.
SIGNIFICANT = 1000.0


def _rm_facing_text(case) -> list[str]:
    brief = case.meeting_brief
    return [
        case.conclusion,
        case.why_now,
        brief.what_changed,
        brief.why_it_matters,
        brief.opening_question,
        *brief.uncertainties,
        *brief.discussion_options,
        *[signal.summary for signal in case.anticipatory_signals],
        *[loop.summary for loop in case.open_loops],
        *[clock.summary for clock in case.governance_clocks],
    ]


def _figures(text: str) -> set[str]:
    found = set()
    for raw in re.findall(r"\d[\d,]*(?:\.\d+)?", text):
        cleaned = raw.replace(",", "").rstrip(".")
        if cleaned and float(cleaned) >= SIGNIFICANT:
            found.add(f"{float(cleaned):.2f}")
    return found


def _evidence_figures(packets) -> set[str]:
    blob = json.dumps([p.model_dump(mode="json", by_alias=True) for p in packets])
    found = set()
    for raw in re.findall(r"\d[\d,]*(?:\.\d+)?", blob):
        cleaned = raw.replace(",", "").rstrip(".")
        if not cleaned:
            continue
        value = float(cleaned)
        # Presentation rounds to whole units, so accept either neighbour.
        found.update(
            {
                f"{value:.2f}",
                f"{round(value):.2f}",
                f"{float(int(value)):.2f}",
                f"{float(int(value) + 1):.2f}",
            }
        )
    return found


def test_no_figure_in_prose_is_absent_from_the_evidence(model, packets_by_client):
    offenders = []
    for case in model.client_cases:
        available = _evidence_figures(packets_by_client[case.client_id])
        for text in _rm_facing_text(case):
            for figure in _figures(text):
                if figure not in available:
                    offenders.append(f"{case.client_id}: {figure} in {text[:60]}")
    assert not offenders, "; ".join(offenders[:5])


def test_no_placeholder_text_reaches_the_rm(model):
    offenders = []
    for case in model.client_cases:
        for text in _rm_facing_text(case):
            found = PLACEHOLDER.search(text)
            if found:
                offenders.append(f"{case.client_id}: '{found.group()}' in {text[:60]}")
    assert not offenders, "; ".join(offenders[:5])


def test_no_doubled_spaces_or_stray_whitespace(model):
    offenders = []
    for case in model.client_cases:
        for text in _rm_facing_text(case):
            if "  " in text or text != text.strip():
                offenders.append(f"{case.client_id}: {text[:60]!r}")
    assert not offenders, "; ".join(offenders[:5])


@pytest.mark.parametrize("field", ["conclusion", "why_now"])
def test_headline_fields_are_well_formed_sentences(model, field):
    offenders = []
    for case in model.client_cases:
        text = getattr(case, field)
        if not text or not text[0].isupper():
            offenders.append(f"{case.client_id}: {text[:50]!r}")
        elif not text.rstrip().endswith((".", "?", "!")):
            offenders.append(f"{case.client_id} unterminated: {text[-40:]!r}")
    assert not offenders, "; ".join(offenders[:5])


def test_every_signal_summary_is_a_sentence(model):
    offenders = []
    for case in model.client_cases:
        for signal in case.anticipatory_signals:
            text = signal.summary
            if not text or not text.rstrip().endswith((".", "?", "!")):
                offenders.append(f"{case.client_id}/{signal.type}: {text[-40:]!r}")
    assert not offenders, "; ".join(offenders[:5])


def test_opening_questions_are_questions(model):
    for case in model.client_cases:
        assert case.meeting_brief.opening_question.rstrip().endswith("?")


def test_briefs_offer_between_one_and_three_discussion_options(model):
    for case in model.client_cases:
        assert 1 <= len(case.meeting_brief.discussion_options) <= 3


def test_no_rm_facing_text_asserts_a_prediction(model):
    """The engine explains and calculates; it never forecasts."""
    # "guaranteed coverage" is a defined liquidity term, not a prediction, so
    # the patterns below target forecasting language specifically.
    forbidden = (
        "will rise",
        "will fall",
        "will recover",
        "we expect the market",
        "is likely to return",
        "we guarantee",
        "guaranteed to",
        "is certain to",
        "will outperform",
    )
    offenders = []
    for case in model.client_cases:
        for text in _rm_facing_text(case):
            lowered = text.lower()
            for phrase in forbidden:
                if phrase in lowered:
                    offenders.append(f"{case.client_id}: '{phrase}'")
    assert not offenders, "; ".join(offenders[:5])


def test_stress_tests_are_never_described_as_forecasts(model):
    for case in model.client_cases:
        if case.collateral_stress_test is None:
            continue
        assert case.collateral_stress_test.forecast is False
        assert "not a forecast" in case.collateral_stress_test.label.lower()

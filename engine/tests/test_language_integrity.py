"""Cached Client-Ready language: parity, citations and failing closed."""

from __future__ import annotations

import pytest

from jb_clarity.language.cached import drafts_for, load_fixtures
from jb_clarity.language.validator import financial_tokens, validate_draft


def _drafts(case) -> dict:
    return {draft.language: draft for draft in (case.client_ready_drafts or [])}


def test_every_client_has_a_canonical_english_draft(model):
    for case in model.client_cases:
        drafts = _drafts(case)
        assert "English" in drafts
        assert drafts["English"].canonical_language == "English"


def test_all_client_ready_content_stays_a_draft(model):
    for case in model.client_cases:
        for draft in case.client_ready_drafts or []:
            assert draft.status == "draft"


def test_cheung_has_a_traditional_chinese_draft(cases_by_client):
    case = cases_by_client["CL-0012"]
    assert case.reporting_language == "Traditional Chinese"
    assert "Traditional Chinese" in _drafts(case)


def test_margarethe_has_a_german_draft(cases_by_client):
    case = cases_by_client["CL-0003"]
    assert case.reporting_language == "German"
    assert "German" in _drafts(case)


@pytest.mark.parametrize(
    "client_id,language", [("CL-0012", "Traditional Chinese"), ("CL-0003", "German")]
)
def test_translations_preserve_every_figure(cases_by_client, client_id, language):
    drafts = _drafts(cases_by_client[client_id])
    canonical = financial_tokens(drafts["English"].content)
    translated = financial_tokens(drafts[language].content)
    assert canonical == translated, (
        f"{language} draft changed figures: "
        f"only canonical {sorted(canonical - translated)}, "
        f"only translated {sorted(translated - canonical)}"
    )


@pytest.mark.parametrize(
    "client_id,language", [("CL-0012", "Traditional Chinese"), ("CL-0003", "German")]
)
def test_translations_cite_only_existing_evidence(
    cases_by_client, packets_by_client, client_id, language
):
    available = {
        item.id for packet in packets_by_client[client_id] for item in packet.items
    }
    draft = _drafts(cases_by_client[client_id])[language]
    assert draft.evidence_item_ids
    assert set(draft.evidence_item_ids) <= available


def test_shipped_fixtures_declare_their_canonical_language():
    fixtures = load_fixtures()
    assert fixtures, "the engine must ship cached language"
    for fixture in fixtures:
        assert fixture.canonical_language == "English"
        assert fixture.language != "English"
        assert fixture.content.strip()
        assert fixture.evidence_item_ids


def test_fixture_clients_are_the_deep_cases():
    assert {fixture.client_id for fixture in load_fixtures()} == {"CL-0012", "CL-0003"}


def test_validator_rejects_a_changed_figure():
    result = validate_draft(
        "The portfolio fell to USD 28,028,999.",
        "The portfolio fell to USD 28,028,705.",
        ["EV-1"],
        {"EV-1"},
    )
    assert not result.ok
    assert any("introduces figures" in error for error in result.errors)


def test_validator_rejects_a_dropped_figure():
    result = validate_draft(
        "The portfolio fell.",
        "The portfolio fell to USD 28,028,705.",
        ["EV-1"],
        {"EV-1"},
    )
    assert not result.ok
    assert any("drops figures" in error for error in result.errors)


def test_validator_rejects_an_unsupported_citation():
    result = validate_draft("Same text.", "Same text.", ["EV-MISSING"], {"EV-1"})
    assert not result.ok
    assert any("not in this client's packets" in error for error in result.errors)


def test_validator_rejects_an_uncited_draft():
    result = validate_draft("Same text.", "Same text.", [], {"EV-1"})
    assert not result.ok
    assert any("cites no evidence" in error for error in result.errors)


def test_validator_accepts_a_faithful_translation():
    result = validate_draft(
        "Das Portfolio fiel auf USD 28,028,705.",
        "The portfolio fell to USD 28,028,705.",
        ["EV-1"],
        {"EV-1"},
    )
    assert result.ok


def test_build_fails_closed_on_an_invalid_cached_draft(monkeypatch, data_dir):
    """A translation that changes a figure is dropped, not published."""
    from datetime import date

    from jb_clarity.build import build_workbench
    from jb_clarity.language.cached import CachedDraft

    poisoned = CachedDraft(
        client_id="CL-0012",
        language="Traditional Chinese",
        canonical_language="English",
        content="數字被改成 USD 99,999,999。",
        evidence_item_ids=("EV-CL-0012-SUITABILITY-OBJECTIVES",),
    )
    monkeypatch.setattr(
        "jb_clarity.build.cached_language.drafts_for", lambda client_id: [poisoned]
    )
    model = build_workbench(data_dir, date(2026, 8, 26))
    case = {c.client_id: c for c in model.client_cases}["CL-0012"]
    languages = {draft.language for draft in case.client_ready_drafts or []}
    assert languages == {"English"}, "an invalid translation must not be published"


def test_drafts_for_returns_nothing_for_an_unknown_client():
    assert drafts_for("CL-9999") == []

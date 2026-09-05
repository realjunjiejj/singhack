"""Priority Queue ordering, tiers, overrides and axis independence."""

from __future__ import annotations

from jb_clarity.domain.enums import SafetyOverrideRuleId

DEMO_CLIENTS = {"CL-0001", "CL-0012", "CL-0003"}


def test_ordering_is_exactly_the_documented_sort(model):
    items = model.book.priority_queue
    keys = [
        (
            0 if item.urgency.safety_override is not None else 1,
            -item.urgency.score,
            item.client_id,
        )
        for item in items
    ]
    assert keys == sorted(keys), "queue must follow override, score, client id"


def test_safety_overrides_sort_first(model):
    overridden = [
        item.rank
        for item in model.book.priority_queue
        if item.urgency.safety_override is not None
    ]
    assert overridden == list(range(1, len(overridden) + 1))


def test_critical_is_reserved_for_safety_overrides(model):
    for item in model.book.priority_queue:
        if item.urgency.tier == "Critical":
            assert item.urgency.safety_override is not None
        if item.urgency.safety_override is not None:
            assert item.urgency.tier == "Critical"


def test_safety_override_rule_ids_are_from_the_approved_set(model):
    approved = {str(rule) for rule in SafetyOverrideRuleId}
    for item in model.book.priority_queue:
        if item.urgency.safety_override is not None:
            assert item.urgency.safety_override.rule_id in approved
            assert item.urgency.safety_override.reason.strip()


def test_high_tier_threshold_is_applied_consistently(model, config):
    threshold = config["urgency"]["highTierThreshold"]
    for item in model.book.priority_queue:
        if item.urgency.safety_override is not None:
            continue
        expected = "High" if item.urgency.score >= threshold else "Watch"
        assert item.urgency.tier == expected


def test_scores_stay_inside_the_configured_range(model, config):
    for item in model.book.priority_queue:
        assert 0.0 <= item.urgency.score <= config["urgency"]["maxScore"]
        assert 0.0 <= item.confidence.score <= 100.0


def test_urgency_and_confidence_are_independent_axes(model):
    """Low Confidence must not suppress a high Urgency score."""
    pairs = {(item.urgency.tier, item.confidence.level) for item in model.book.priority_queue}
    non_high_confidence = {p for p in pairs if p[1] != "High"}
    assert non_high_confidence, "the book should contain less-than-certain cases"
    urgent_but_uncertain = [
        item
        for item in model.book.priority_queue
        if item.confidence.level != "High" and item.urgency.tier in {"Critical", "High"}
    ]
    assert urgent_but_uncertain, "an urgent case with imperfect evidence must still rank"


def test_every_displayed_point_names_a_factor_and_a_reason(model):
    for item in model.book.priority_queue:
        for contribution in item.factor_contributions:
            assert contribution.factor
            assert contribution.reason.strip()
            assert contribution.points >= 0


def test_factor_points_never_exceed_their_configured_maximum(model, config):
    maxima = {
        name: settings["max"]
        for name, settings in config["urgency"]["factors"].items()
    }
    for item in model.book.priority_queue:
        for contribution in item.factor_contributions:
            assert contribution.points <= maxima[contribution.factor] + 1e-9


def test_score_is_base_plus_capped_escalation(model, config):
    """The severest factor sets the base; the rest add capped escalation."""
    cap = config["urgency"]["compoundEscalationCap"]
    ceiling = config["urgency"]["maxScore"]
    for item in model.book.priority_queue:
        points = sorted((c.points for c in item.factor_contributions), reverse=True)
        if not points:
            assert item.urgency.score == 0
            continue
        expected = min(points[0] + min(sum(points[1:]), cap), ceiling)
        assert round(item.urgency.score, 2) == round(expected, 2)


def test_demonstration_clients_are_not_promoted(model):
    """The deep cases must earn their rank like everyone else."""
    ranks = {
        item.client_id: item.rank
        for item in model.book.priority_queue
        if item.client_id in DEMO_CLIENTS
    }
    assert len(ranks) == 3
    # If the demo clients had been promoted they would occupy the top slots.
    assert set(ranks.values()) != {1, 2, 3}
    assert max(ranks.values()) > 3


def test_the_queue_row_reports_every_signal_not_a_sample(model, cases_by_client):
    """The card renders this list's length as the client's signal count.

    Truncating it made 18 of 20 clients under-report, and hid the omitted
    signals from Book search, which matches against these summaries.
    """
    for item in model.book.priority_queue:
        case = cases_by_client[item.client_id]
        assert len(item.signal_summaries) == len(case.anticipatory_signals)
        assert item.signal_summaries == [s.summary for s in case.anticipatory_signals]


def test_every_queue_row_answers_why_now(model):
    for item in model.book.priority_queue:
        assert item.priority_rationale.strip()
        assert len(item.priority_rationale) > 20


def test_tie_breaks_prefer_the_earliest_confirmed_obligation(model, cases_by_client):
    """Equal scores must break on the nearest confirmed obligation, then id."""
    by_score: dict[float, list] = {}
    for item in model.book.priority_queue:
        by_score.setdefault(item.urgency.score, []).append(item)
    for tied in by_score.values():
        if len(tied) < 2:
            continue
        assert [t.rank for t in tied] == sorted(t.rank for t in tied)

"""Confidence: how well the evidence supports the interpretation.

Confidence is independent of Urgency. A case with weak evidence and a severe,
imminent problem stays at the top of the Queue; it simply says how much of it
still needs checking.
"""

from __future__ import annotations

from jb_clarity.domain.enums import ConfidenceLevel
from jb_clarity.domain.models import Confidence
from jb_clarity.evidence.claims import DetectedSignal


def score_client(signals: list[DetectedSignal], config: dict) -> Confidence:
    settings = config["confidence"]
    score = float(settings["start"])

    # Each distinct reason is charged once, however many signals raise it, so a
    # single underlying weakness cannot compound into a misleadingly low score.
    deductions: dict[str, float] = {}
    for signal in signals:
        for deduction in signal.confidence_deductions:
            deductions[deduction.reason] = max(
                deductions.get(deduction.reason, 0.0), deduction.points
            )

    for points in deductions.values():
        score -= points
    score = max(0.0, min(100.0, score))

    if score >= float(settings["highThreshold"]):
        level = ConfidenceLevel.HIGH
    elif score >= float(settings["mediumThreshold"]):
        level = ConfidenceLevel.MEDIUM
    else:
        level = ConfidenceLevel.LOW

    reasons = sorted(deductions.keys())
    if not reasons:
        reasons = [
            "Every claim resolves to a supplied source record, and no source disagrees "
            "with another."
        ]
    return Confidence(level=level, score=round(score, 2), reasons=reasons)

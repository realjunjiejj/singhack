"""The artifact must satisfy the shared contract exactly."""

from __future__ import annotations

import jsonschema
import pytest


def test_artifact_validates_against_the_published_schema(artifact, schema):
    jsonschema.Draft202012Validator(schema).validate(artifact)


def test_schema_itself_is_a_valid_2020_12_schema(schema):
    jsonschema.Draft202012Validator.check_schema(schema)


def test_required_nullable_fields_are_present_even_when_null(artifact):
    for item in artifact["book"]["priorityQueue"]:
        assert "safetyOverride" in item["urgency"]
    for case in artifact["clientCases"]:
        assert "safetyOverride" in case["urgency"]
        assert "specialistSuggestion" in case["meetingBrief"]


def test_optional_fields_are_omitted_rather_than_null(artifact):
    for case in artifact["clientCases"]:
        assert case.get("collateralStressTest") is not None or True
        if "collateralStressTest" in case:
            assert case["collateralStressTest"] is not None
        if "clientReadyDrafts" in case:
            assert case["clientReadyDrafts"] is not None


def test_money_and_measures_use_declared_units(artifact):
    for case in artifact["clientCases"]:
        for point in case["timeline"]:
            for measure in point["metrics"].values():
                assert measure["unit"] in {"currency", "percent"}
                if measure["unit"] == "currency":
                    assert measure["currency"] == "USD"


@pytest.mark.parametrize("collection", ["clientCases", "evidencePackets"])
def test_identifiers_are_unique(artifact, collection):
    key = "caseId" if collection == "clientCases" else "packetId"
    ids = [entry[key] for entry in artifact[collection]]
    assert len(ids) == len(set(ids))


def test_case_and_packet_identifiers_are_stable_and_predictable(artifact):
    case_ids = {case["caseId"] for case in artifact["clientCases"]}
    assert "CASE-CL-0001" in case_ids
    packet_ids = {packet["packetId"] for packet in artifact["evidencePackets"]}
    assert "PACKET-CL-0001-CREDIT" in packet_ids


def test_every_packet_belongs_to_a_declared_case(artifact):
    case_ids = {case["caseId"] for case in artifact["clientCases"]}
    for packet in artifact["evidencePackets"]:
        assert packet["caseId"] in case_ids


def test_cases_reference_only_their_own_packets(artifact):
    packets = {p["packetId"]: p for p in artifact["evidencePackets"]}
    for case in artifact["clientCases"]:
        for packet_id in case["evidencePacketIds"]:
            assert packet_id in packets
            assert packets[packet_id]["clientId"] == case["clientId"]

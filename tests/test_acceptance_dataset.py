"""Consistency checks for the proposed acceptance corpus; not a scoring implementation."""
import json
from pathlib import Path

DATASET = Path(__file__).parent / "fixtures" / "acceptance" / "jobs-v1.json"


def load_cases():
    return json.loads(DATASET.read_text(encoding="utf-8"))


def test_corpus_has_unique_cases_and_explicit_review_provenance():
    data = load_cases()
    cases = data["cases"]
    assert data["synthetic"] is True
    assert len(cases) >= 20
    assert len({c["caseId"] for c in cases}) == len(cases)
    assert data["reviewStatus"] in {"PENDING_RAFAEL", "APPROVED"}
    for case in cases:
        assert case["review"]["status"] in {"PENDING_RAFAEL", "APPROVED"}
        if case["review"]["status"] == "APPROVED":
            assert case["review"].get("reviewedBy") == "Rafael"
            assert case["review"].get("reviewedAt")
    if data["reviewStatus"] == "APPROVED":
        assert all(c["review"]["status"] == "APPROVED" for c in cases)
    assert {c["proposed"]["eligibility"] for c in cases} == {
        "ELIGIBLE", "INELIGIBLE", "NEEDS_REVIEW"
    }


def test_identity_scenarios_are_internally_consistent():
    cases = {c["caseId"]: c for c in load_cases()["cases"]}
    first = cases["J01"]["job"]
    replay = cases["J21"]["job"]
    assert replay == first
    update = cases["J23"]["job"]
    assert (update["source"], update["externalId"]) == (
        first["source"], first["externalId"]
    )
    assert update["description"] != first["description"]
    collision = cases["J22"]["job"]
    assert collision["externalId"] == first["externalId"]
    assert collision["source"] != first["source"]
    copy = cases["J24"]["job"]
    assert (copy["title"], copy["company"]) == (first["title"], first["company"])
    assert copy["source"] != first["source"]
    for case in cases.values():
        if "relation" in case:
            assert case["relation"]["target"] in cases

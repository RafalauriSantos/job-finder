from core.recalibration import build_recalibration_report


def test_recalibration_matches_feedback_to_decisions_without_changing_weights():
    state = {
        "recent_decisions": [{"identity_fingerprint": "fp", "category": "POTENCIALMENTE_COMPATIVEL", "source": "gupy"}],
        "feedback": [
            {"fingerprint": "fp", "feedback": "applied"},
            {"fingerprint": "fp", "feedback": "interview"},
            {"fingerprint": "fp", "feedback": "rejected"},
        ],
    }
    report = build_recalibration_report(state)
    assert report["matched_feedback_count"] == 3
    assert report["by_category"]["POTENCIALMENTE_COMPATIVEL"]["positive"] == 2
    assert report["automatic_weight_change"] is False

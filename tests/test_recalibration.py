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
    assert report["by_category"]["POTENCIALMENTE_COMPATIVEL"]["positive"] == 1
    assert report["automatic_weight_change"] is False


def test_outcomes_do_not_mean_irrelevance_and_one_vacancy_cannot_trigger_recalibration():
    state = {
        "recent_decisions": [{"identity_fingerprint": "fp", "category": "COMPATIVEL", "source": "gupy"}],
        "feedback": [
            {"fingerprint": "fp", "feedback": "applied"},
            {"fingerprint": "fp", "feedback": "interview"},
            {"fingerprint": "fp", "feedback": "rejected"},
            {"fingerprint": "other", "feedback": "not_applied"},
        ],
    }
    report = build_recalibration_report(state)
    assert report["relevance_vacancies"] == 1
    assert report["by_category"]["COMPATIVEL"] == {"positive": 1, "negative": 0}
    assert report["recommendations"] == []
    state["feedback"].append({"fingerprint": "fp", "feedback": "irrelevant"})
    assert build_recalibration_report(state)["by_category"]["COMPATIVEL"] == {"positive": 0, "negative": 1}

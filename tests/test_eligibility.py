from core.eligibility import classify_score


def test_zero_score_is_veto():
    assert classify_score(0, 50) == "VETO"


def test_positive_score_below_threshold_is_low_score():
    assert classify_score(49, 50) == "LOW_SCORE"


def test_score_at_threshold_is_approved():
    assert classify_score(50, 50) == "APPROVED"

from core.ranking import order_for_alerts
from models.job import Job


def _job(title, freshness, match, learning=0):
    job = Job(title=title, company="Empresa", workplace_type="remote")
    job.freshness_score = freshness
    job.match_score = match
    job.learning_interest_score = learning
    return job


def test_alert_order_prioritizes_freshness_then_match_then_learning():
    old_strong = _job("Java Pleno antigo", 20, 95, 80)
    fresh_mid = _job("Java Pleno recente", 100, 75, 60)
    fresh_learning = _job("Java aprendizado", 100, 75, 90)

    ordered = order_for_alerts([old_strong, fresh_mid, fresh_learning])

    assert [job.title for job in ordered] == [
        "Java aprendizado",
        "Java Pleno recente",
        "Java Pleno antigo",
    ]

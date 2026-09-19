from models.job import Job
from core.scoring import calculate_match_score


def test_ranking_exposes_separate_components_and_evidence():
    job = Job(
        title="Desenvolvedor Java Pleno",
        company="Empresa Tech",
        workplace_type="remote",
        description="Java, Spring Boot, APIs e testes automatizados.",
        technologies=["java"],
    )

    score, reasons = calculate_match_score(job)

    assert score >= 0
    assert job.score_breakdown["seniority"] == 10
    assert job.score_breakdown["freshness"] == 0
    assert "Pleno" in " ".join(reasons)
    assert job.ranking_evidence["seniority"] == "mid"


def test_pleno_with_senior_signals_is_kept_with_explicit_risk():
    job = Job(
        title="Desenvolvedor Java Pleno",
        company="Empresa Tech",
        workplace_type="remote",
        description="Liderança técnica e experiência mínima de 5 anos com Java.",
    )

    score, reasons = calculate_match_score(job)

    assert score > 0
    assert job.score_breakdown["risk"] < 0
    assert job.ranking_evidence["risk"] == "senior_signals"
    assert any("risco" in reason.lower() for reason in reasons)


def test_title_without_seniority_keeps_unknown_evidence():
    job = Job(
        title="Desenvolvedor Java",
        company="Empresa Tech",
        workplace_type="remote",
        description="Java e APIs REST.",
    )

    calculate_match_score(job)

    assert job.seniority == "unknown"
    assert job.ranking_evidence["seniority"] == "unknown"


def test_recent_publication_gets_separate_freshness_score():
    job = Job(
        title="Desenvolvedor Java Pleno",
        company="Empresa Tech",
        workplace_type="remote",
        description="Java e APIs REST.",
        published_at="2026-09-19T10:00:00+00:00",
    )

    calculate_match_score(job, now="2026-09-19T12:00:00+00:00")

    assert job.freshness_score > 0
    assert job.score_breakdown["freshness"] == job.freshness_score

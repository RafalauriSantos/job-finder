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

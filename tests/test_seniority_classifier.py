from core.scoring import classify_seniority, calculate_match_score
from models.job import Job


def test_classifies_junior_title():
    assert classify_seniority("Desenvolvedor Frontend Junior") == "junior"


def test_classifies_mid_title():
    assert classify_seniority("Desenvolvedor Pleno React") == "mid"


def test_classifies_explicit_senior_title():
    assert classify_seniority("Tech Lead Backend") == "senior"


def test_does_not_treat_pl_as_senior_fragment():
    assert classify_seniority("Analista de Plataforma") == "unknown"


def test_company_fifteen_years_does_not_trigger_five_years_risk():
    job = Job(
        title="Desenvolvedor Java Junior", company="BairesDev",
        workplace_type="remote",
        description="A empresa atua há mais de 15 anos. Requisitos: Java e Git.",
        technologies=["java", "git"],
    )

    _, reasons = calculate_match_score(job)

    assert not any("Risco de requisito sênior" in reason for reason in reasons)

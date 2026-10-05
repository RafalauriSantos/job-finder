from core.eligibility import classify_score
from core.eligibility import classify_evidence, classify_location
from models.job import Job
from core.normalizer import is_location_allowed


def test_zero_score_is_veto():
    assert classify_score(0, 50) == "VETO"


def test_positive_score_below_threshold_is_low_score():
    assert classify_score(49, 50) == "LOW_SCORE"


def test_score_at_threshold_is_approved():
    assert classify_score(50, 50) == "APPROVED"


def test_rss_low_evidence_is_rejected():
    job = Job(title="Dev React", company="Indeed", workplace_type="unknown", evidence_level="LOW_EVIDENCE")
    job.add_source("rss", "rss-1", "https://news.example/1")

    assert classify_evidence(job) == "LOW_EVIDENCE"


def test_structured_job_evidence_is_eligible():
    job = Job(
        title="Dev React",
        company="Empresa",
        workplace_type="remote",
        description="React e Node.js para desenvolvimento de APIs.",
        evidence_level="HIGH_EVIDENCE",
    )
    job.add_source("gupy", "gupy-1", "https://empresa.gupy.io/jobs/1")

    assert classify_evidence(job) == "APPROVED"


def test_location_decision_uses_regional_policy():
    allowed, _ = is_location_allowed("hybrid", "Sorocaba, SP")
    rejected, _ = is_location_allowed("hybrid", "São Paulo, SP")
    assert allowed is True
    assert rejected is False

    job = Job(title="Dev", company="Empresa", workplace_type="hybrid", location="Sorocaba, SP")
    assert classify_location(job)[0] == "APPROVED"


def test_location_description_overrides_home_office_title_when_hybrid_travel_is_required():
    job = Job(
        title="Pessoa Desenvolvedora Node.js Pleno - Home office",
        company="Monjuá",
        workplace_type="remote",
        location="Porto Alegre, RS",
        description="Modalidade de trabalho híbrido, com deslocamento para Porto Alegre uma semana por mês.",
    )

    decision, reason = classify_location(job)

    assert decision == "LOCATION_REJECTED"
    assert "hybrid" in reason.lower() or "híbrido" in reason.lower()


def test_location_detects_feminine_hybrid_workplace():
    job = Job(
        title="Desenvolvedora",
        company="Empresa",
        workplace_type="remote",
        location="Campinas, SP",
        description="Modalidade híbrida, com presença semanal no escritório.",
    )

    assert classify_location(job)[0] == "LOCATION_REJECTED"


def test_ambiguous_external_location_is_not_assumed_remote():
    job = Job(
        title="Pessoa Desenvolvedora",
        company="Empresa",
        workplace_type="unknown",
        location="Campinas, SP",
        description="Modelo de trabalho não informado.",
    )

    assert classify_location(job)[0] == "LOCATION_REJECTED"


def test_explicit_remote_description_overrides_hybrid_header():
    job = Job(
        title="Desenvolvedor Full-Stack JavaScript Júnior",
        company="4DF Connect",
        workplace_type="hybrid",
        location="São Paulo, SP",
        description="Esta vaga é para atuação remota, podendo ser exercida de qualquer lugar do Brasil.",
    )
    decision, reason = classify_location(job)
    assert decision == "APPROVED"
    assert job.workplace_type == "remote"
    assert "Remoto" in reason

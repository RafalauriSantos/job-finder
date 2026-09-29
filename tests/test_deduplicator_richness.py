from core.deduplicator import Deduplicator, semantic_fingerprint
from models.job import Job


def test_deduplicator_prefers_richer_record_when_rss_arrives_first():
    shallow = Job(
        title="Desenvolvedor React",
        company="Empresa Tech",
        workplace_type="remote",
        location="Brasil",
        evidence_level="LOW_EVIDENCE",
    )
    shallow.add_source("rss", "rss-1", "https://news.example/item")

    rich = Job(
        title="Desenvolvedor React",
        company="Empresa Tech",
        workplace_type="remote",
        description="React, TypeScript, testes e integração com API.",
        location="Brasil",
        technologies=["React", "TypeScript"],
        canonical_url="https://empresa.gupy.io/jobs/1",
        evidence_level="HIGH_EVIDENCE",
    )
    rich.add_source("gupy", "1", rich.canonical_url)

    merged = Deduplicator().process([shallow, rich])[0]

    assert merged.description == rich.description
    assert merged.evidence_level == "HIGH_EVIDENCE"
    assert set(merged.sources) == {"rss", "gupy"}


def test_deduplicator_replaces_default_fields_with_structured_values():
    basic = Job(
        title="Desenvolvedor React",
        company="Empresa Tech",
        workplace_type="remote",
        location="Brasil",
        job_type="CLT",
        salary="Não informado",
    )
    basic.add_source("linkedin", "li-1", "https://linkedin.com/jobs/1")

    structured = Job(
        title="Desenvolvedor React",
        company="Empresa Tech",
        workplace_type="remote",
        location="Brasil",
        job_type="PJ",
        salary="R$ 4.000",
        description="Descrição estruturada da vaga.",
        canonical_url="https://empresa.example/jobs/1",
        evidence_level="HIGH_EVIDENCE",
    )
    structured.add_source("gupy", "g-1", structured.canonical_url)

    merged = Deduplicator().process([basic, structured])[0]

    assert merged.salary == "R$ 4.000"
    assert merged.job_type == "PJ"
    assert merged.canonical_url == structured.canonical_url


def test_deduplicator_preserves_earliest_publication_date_from_duplicate_sources():
    newer = Job(
        title="Desenvolvedor React",
        company="Empresa Tech",
        workplace_type="remote",
        location="Brasil",
        published_at="2026-09-19T10:00:00+00:00",
    )
    newer.add_source("linkedin", "li-1", "https://linkedin.com/jobs/1")

    older = Job(
        title="Desenvolvedor React",
        company="Empresa Tech",
        workplace_type="remote",
        location="Brasil",
        published_at="2026-09-18T10:00:00+00:00",
    )
    older.add_source("gupy", "g-1", "https://empresa.gupy.io/jobs/1")

    merged = Deduplicator().process([newer, older])[0]

    assert merged.published_at == "2026-09-18T10:00:00+00:00"


def test_deduplicator_collapses_near_identical_reposts_but_keeps_alternative_urls():
    description = (
        "Vaga para construir integrações com APIs, automações e aplicações web. "
        "Requisitos obrigatórios: experiência prática com Node.js e Git. "
        "A equipe trabalha com revisões de código, testes automatizados e entregas frequentes. "
        "A pessoa vai colaborar com desenvolvimento, produto e operações em projetos digitais. "
    ) * 5
    first = Job(
        title="AI Developer (Remote, Florianópolis)", company="Blacksmith Agency",
        workplace_type="remote", location="Brasil", description=description,
    )
    first.add_source("linkedin", "job-1", "https://linkedin.example/jobs/1")
    second = Job(
        title="AI Automation Engineer (Remote, Goiânia)", company="Blacksmith Agency",
        workplace_type="remote", location="Brasil", description=description,
    )
    second.add_source("linkedin", "job-2", "https://linkedin.example/jobs/2")

    merged = Deduplicator().process([first, second])

    assert len(merged) == 1
    assert merged[0].analysis["duplicate_listings"][0]["url"] == "https://linkedin.example/jobs/2"
    assert semantic_fingerprint(first) == semantic_fingerprint(second)

import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.job import Job


def test_identity_fingerprint_immutable_on_description_change():
    """Garante que a identidade da vaga não mude quando o RH altera o texto da descrição."""
    job1 = Job(
        title="Desenvolvedor Frontend Júnior",
        company="Startup Exemplo",
        workplace_type="remote",
        location="Brasil",
        description="Descrição original da vaga com React e TypeScript.",
    )

    job2 = Job(
        title="Desenvolvedor Frontend Júnior",
        company="Startup Exemplo",
        workplace_type="remote",
        location="Brasil",
        description="Descrição atualizada: agora inclui bônus e horário flexível.",
    )

    assert job1.identity_fingerprint == job2.identity_fingerprint
    assert job1.content_hash != job2.content_hash


def test_identity_fingerprint_differs_on_location_or_workplace():
    """Garante que a identidade mude se a modalidade ou localização forem diferentes."""
    job_remote = Job(
        title="Desenvolvedor Júnior",
        company="TechCorp",
        workplace_type="remote",
        location="Brasil",
    )
    job_onsite = Job(
        title="Desenvolvedor Júnior",
        company="TechCorp",
        workplace_type="on-site",
        location="Sorocaba",
    )

    assert job_remote.identity_fingerprint != job_onsite.identity_fingerprint


def test_url_tripartite_and_evidence_level_fields():
    """Garante que os novos campos da SPEC-008 existam no Job."""
    job = Job(
        title="Dev Node.js",
        company="Empresa X",
        workplace_type="remote",
        raw_url="https://news.google.com/rss/articles/CBMi123",
        resolved_url="https://jobs.lever.co/empresa/vaga-123?utm_source=google",
        canonical_url="https://jobs.lever.co/empresa/vaga-123",
        evidence_level="HIGH_EVIDENCE",
    )

    assert job.raw_url == "https://news.google.com/rss/articles/CBMi123"
    assert job.resolved_url == "https://jobs.lever.co/empresa/vaga-123?utm_source=google"
    assert job.canonical_url == "https://jobs.lever.co/empresa/vaga-123"
    assert job.evidence_level == "HIGH_EVIDENCE"
    assert job.primary_url == "https://jobs.lever.co/empresa/vaga-123"

    d = job.to_dict()
    assert d["raw_url"] == job.raw_url
    assert d["canonical_url"] == job.canonical_url
    assert d["evidence_level"] == job.evidence_level

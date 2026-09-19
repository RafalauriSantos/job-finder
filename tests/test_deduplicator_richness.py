from core.deduplicator import Deduplicator
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

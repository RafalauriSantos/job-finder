import json
import pytest
from pathlib import Path
from models.job import Job
from core.scoring import calculate_match_score
from core.normalizer import is_location_allowed
from core.deduplicator import Deduplicator

FIXTURES_DIR = Path(__file__).parent / "fixtures"

class TestFixturesGroundTruth:
    def test_junior_matching_reaches_high_score_and_approved_location(self):
        with open(FIXTURES_DIR / "junior_matching.json", encoding="utf-8") as f:
            data = json.load(f)
        
        job = Job(
            title=data["title"],
            company=data["company"],
            workplace_type=data["workplace_type"],
            location=data["location"],
            description=data["description"]
        )
        job.add_source(data["source"], data["id"], data["url"])
        
        # 1. Localidade Remota deve ser permitida
        allowed, reason = is_location_allowed(job.workplace_type, job.location, job.title)
        assert allowed is True
        assert "Remoto" in reason
        
        # 2. Score deve ser alto (Junior + Remoto + Core Techs: React, TypeScript, Node, PostgreSQL)
        score, reasons = calculate_match_score(job)
        assert score >= 80, f"Score esperado >= 80, obteve {score}. Razões: {reasons}"
        assert any("Junior" in r or "Júnior" in r for r in reasons)
        assert any("react" in r.lower() for r in reasons)
        assert any("node" in r.lower() for r in reasons)

    def test_senior_react_is_severely_penalized(self):
        with open(FIXTURES_DIR / "senior_react.json", encoding="utf-8") as f:
            data = json.load(f)
        
        job = Job(
            title=data["title"],
            company=data["company"],
            workplace_type=data["workplace_type"],
            location=data["location"],
            description=data["description"]
        )
        job.add_source(data["source"], data["id"], data["url"])
        
        score, reasons = calculate_match_score(job)
        # Sênior deve receber penalidade de -60, resultando em 0
        assert score == 0
        assert any("Senior" in r or "Sênior" in r for r in reasons)

    def test_hybrid_sp_capital_is_rejected_by_location_policy(self):
        with open(FIXTURES_DIR / "hybrid_sp_capital.json", encoding="utf-8") as f:
            data = json.load(f)
        
        job = Job(
            title=data["title"],
            company=data["company"],
            workplace_type=data["workplace_type"],
            location=data["location"],
            description=data["description"]
        )
        job.add_source(data["source"], data["id"], data["url"])
        
        # Híbrido em São Paulo (Capital) DEVE ser descartado (não é Tatuí nem Sorocaba)
        allowed, reason = is_location_allowed(job.workplace_type, job.location, job.title)
        assert allowed is False
        assert "fora da região" in reason or "fora da regiao" in reason or "Tatuí" in reason

    def test_multi_source_deduplication_merges_gupy_and_linkedin(self):
        with open(FIXTURES_DIR / "multi_source_same_job.json", encoding="utf-8") as f:
            data = json.load(f)
        
        gupy_job = Job(
            title=data["gupy_version"]["title"],
            company=data["gupy_version"]["company"],
            workplace_type=data["gupy_version"]["workplace_type"],
            location=data["gupy_version"]["location"],
            description=data["gupy_version"]["description"]
        )
        gupy_job.add_source(data["gupy_version"]["source"], data["gupy_version"]["id"], data["gupy_version"]["url"])
        
        li_job = Job(
            title=data["linkedin_version"]["title"],
            company=data["linkedin_version"]["company"],
            workplace_type=data["linkedin_version"]["workplace_type"],
            location=data["linkedin_version"]["location"],
            description=data["linkedin_version"]["description"]
        )
        li_job.add_source(data["linkedin_version"]["source"], data["linkedin_version"]["id"], data["linkedin_version"]["url"])
        
        dedup = Deduplicator()
        unique = dedup.process([gupy_job, li_job])
        
        assert len(unique) == 1
        merged_job = unique[0]
        assert len(merged_job.sources) == 2
        assert "gupy" in merged_job.sources
        assert "linkedin" in merged_job.sources

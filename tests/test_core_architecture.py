import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.job import Job
from core.normalizer import normalize_title, normalize_workplace, is_location_allowed, extract_technologies
from core.scoring import calculate_match_score
from core.deduplicator import Deduplicator


class TestJobModel:
    def test_job_creates_fingerprint_and_merges_sources(self):
        job1 = Job(
            title="Desenvolvedor Full Stack Júnior",
            company="Goomer",
            workplace_type="remote",
            description="Vaga para atuar com React e Node.js no time de tecnologia",
        )
        job1.add_source("linkedin", "12345", "https://linkedin.com/jobs/12345")

        job2 = Job(
            title="Desenvolvedor Full Stack Júnior",
            company="Goomer",
            workplace_type="remote",
            description="Vaga para atuar com React e Node.js no time de tecnologia",
        )
        job2.add_source("gupy", "98765", "https://goomer.gupy.io/jobs/98765")

        # Ambas as vagas devem gerar a MESMA fingerprint
        assert job1.fingerprint == job2.fingerprint

        # Deduplicator deve fundir as duas fontes
        dedup = Deduplicator()
        unified = dedup.process([job1, job2])

        assert len(unified) == 1
        assert "linkedin" in unified[0].sources
        assert "gupy" in unified[0].sources
        assert unified[0].sources["linkedin"].url == "https://linkedin.com/jobs/12345"
        assert unified[0].sources["gupy"].url == "https://goomer.gupy.io/jobs/98765"

    def test_different_locations_produce_different_fingerprints(self):
        """Vagas com mesmo título e empresa em localidades distintas geram fingerprints diferentes."""
        job_sorocaba = Job(
            title="Desenvolvedor Java Junior",
            company="GFT Brasil",
            workplace_type="on-site",
            location="Sorocaba - SP",
            description="Atuação no escritório de Sorocaba",
        )
        job_curitiba = Job(
            title="Desenvolvedor Java Junior",
            company="GFT Brasil",
            workplace_type="on-site",
            location="Curitiba - PR",
            description="Atuação no escritório de Curitiba",
        )
        assert job_sorocaba.fingerprint != job_curitiba.fingerprint

    def test_description_updates_preserve_identity_fingerprint_but_change_content_hash(self):
        """Pequenas correções de texto na descrição pelo RH não alteram a identidade canônica."""
        job_original = Job(
            title="Desenvolvedor React Junior",
            company="Goomer",
            workplace_type="remote",
            location="Remoto",
            description="Buscamos dev júnior com React e Node.",
        )
        job_edited_by_hr = Job(
            title="Desenvolvedor React Junior",
            company="Goomer",
            workplace_type="remote",
            location="Remoto",
            description="Buscamos dev júnior com React, Node e Tailwind (corrigido typo).",
        )
        # Identidade Canônica permanece a MESMA (não gera falsa duplicata)
        assert job_original.identity_fingerprint == job_edited_by_hr.identity_fingerprint
        assert job_original.fingerprint == job_edited_by_hr.fingerprint
        # Mas o content_hash detecta a alteração de conteúdo
        assert job_original.content_hash != job_edited_by_hr.content_hash


class TestNormalizer:
    def test_normalizes_workplace(self):
        assert normalize_workplace("Presencial", title_text="Vaga Home Office") == "remote"
        assert normalize_workplace("", location_text="São Paulo (Híbrido)") == "hybrid"

    def test_location_allowed_rules(self):
        # Remoto sempre aceito
        allowed, _ = is_location_allowed("remote", location_text="Manaus, AM")
        assert allowed is True

        # Híbrido em Sorocaba aceito
        allowed, _ = is_location_allowed("hybrid", location_text="Sorocaba, SP")
        assert allowed is True

        # Híbrido em Boituva aceito
        allowed, _ = is_location_allowed("hybrid", location_text="Boituva, SP")
        assert allowed is True

        # Híbrido em São Paulo capital rejeitado
        allowed, _ = is_location_allowed("hybrid", location_text="São Paulo, SP")
        assert allowed is False

    def test_extract_technologies(self):
        desc = "Buscamos profissional com domínio de TypeScript, React.js e PostgreSQL para backend com Node.js"
        techs = extract_technologies(desc)
        assert "typescript" in techs
        assert "react" in techs
        assert "postgresql" in techs
        assert "node.js" in techs


class TestScoring:
    def test_calculates_high_score_for_matching_candidate_cv(self):
        job = Job(
            title="Pessoa Desenvolvedora Full Stack Júnior",
            company="Goomer",
            workplace_type="remote",
            description="Requisitos: React, TypeScript, Node.js e PostgreSQL",
            technologies=["react", "typescript", "node.js", "postgresql"],
        )
        score, reasons = calculate_match_score(job)
        # Deve receber pontuação alta (> 80)
        assert score >= 80
        assert any("Stack Core" in r for r in reasons)
        assert any("Nível Júnior" in r for r in reasons)
        assert any("Remota" in r for r in reasons)

    def test_penalizes_senior_positions(self):
        job = Job(
            title="Tech Lead / Desenvolvedor Sênior",
            company="Empresa X",
            workplace_type="remote",
            description="Liderança de time",
        )
        score, reasons = calculate_match_score(job)
        assert score == 0
        assert any("Senioridade alta" in r for r in reasons)

    def test_learning_interest_is_separate_from_match_score(self):
        job = Job(
            title="Desenvolvedor Java Junior",
            company="Empresa X",
            workplace_type="remote",
            description="Java, Spring e Git",
        )
        score, _ = calculate_match_score(job)
        assert score > 0
        assert job.learning_interest_score > 0
        assert job.learning_interest_score <= 100

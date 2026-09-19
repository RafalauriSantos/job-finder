import pytest
from core.scoring import calculate_match_score
from core.normalizer import is_location_allowed
from models.job import Job
from core.deduplicator import Deduplicator
from storage.state_store import StateStore

class TestOperationalMatrix10Cases:
    """
    Bateria de validação dos 10 casos fundamentais de decisão operacional:
    1. Full Stack Jr + remoto + stack -> Encontrar + Notificar
    2. Backend Jr + remoto + Node -> Encontrar + Notificar
    3. Java Jr + remoto -> Encontrar + Notificar
    4. Pleno remoto -> Encontrar + Rejeitar
    5. Senior remoto -> Encontrar + Rejeitar
    6. Jr presencial RJ -> Encontrar + Rejeitar (localidade fora do raio)
    7. Jr híbrido SP Capital -> Encontrar + Rejeitar (localidade fora do raio)
    8. Jr presencial Sorocaba -> Encontrar + Aceitar
    9. Mesma vaga Gupy + LinkedIn -> 1 Job unificado com 2 fontes
    10. Vaga encontrada novamente -> Não notificar novamente
    """

    def test_case_1_fullstack_jr_remote_stack(self):
        job = Job(
            title="Desenvolvedor Full Stack Júnior",
            company="Empresa Alpha",
            workplace_type="remote",
            location="Brasil",
            description="React, TypeScript, Node.js e PostgreSQL"
        )
        job.add_source("gupy", "101", "https://alpha.gupy.io/jobs/101")
        loc_ok, _ = is_location_allowed(job.workplace_type, job.location, job.title)
        score, reasons = calculate_match_score(job)
        assert loc_ok is True
        assert score >= 80

    def test_case_2_backend_jr_remote_node(self):
        job = Job(
            title="Desenvolvedor Backend Jr",
            company="Beta Corp",
            workplace_type="remote",
            location="Brasil",
            description="Node.js, TypeScript e APIs REST"
        )
        job.add_source("linkedin", "202", "https://linkedin.com/jobs/view/202")
        loc_ok, _ = is_location_allowed(job.workplace_type, job.location, job.title)
        score, reasons = calculate_match_score(job)
        assert loc_ok is True
        assert score >= 70

    def test_case_3_java_jr_remote(self):
        job = Job(
            title="Desenvolvedor Java Junior",
            company="Gamma Tech",
            workplace_type="remote",
            location="Brasil",
            description="Spring Boot, Java 17, Docker e Git"
        )
        job.add_source("gupy", "303", "https://gamma.gupy.io/jobs/303")
        loc_ok, _ = is_location_allowed(job.workplace_type, job.location, job.title)
        score, reasons = calculate_match_score(job)
        assert loc_ok is True
        assert score >= 65

    def test_case_4_pleno_remote_is_eligible_for_evaluation(self):
        job = Job(
            title="Desenvolvedor Pleno Full Stack",
            company="Delta Soft",
            workplace_type="remote",
            location="Brasil",
            description="React, Node.js e PostgreSQL"
        )
        job.add_source("linkedin", "404", "https://linkedin.com/jobs/view/404")
        score, reasons = calculate_match_score(job)
        assert score >= 50
        assert job.seniority == "mid"
        assert any("Pleno compatível" in reason for reason in reasons)

    def test_case_5_senior_remote_rejected(self):
        job = Job(
            title="Senior Full Stack Engineer",
            company="Epsilon Global",
            workplace_type="remote",
            location="Brasil",
            description="React, TypeScript, Node.js e liderança técnica"
        )
        job.add_source("linkedin", "505", "https://linkedin.com/jobs/view/505")
        score, reasons = calculate_match_score(job)
        assert score == 0

    def test_case_6_jr_onsite_rj_rejected(self):
        job = Job(
            title="Desenvolvedor Júnior",
            company="Zeta Rio",
            workplace_type="on-site",
            location="Rio de Janeiro, RJ",
            description="React e Node.js"
        )
        loc_ok, reason = is_location_allowed(job.workplace_type, job.location, job.title)
        assert loc_ok is False
        assert "fora da região" in reason

    def test_case_7_jr_hybrid_sp_capital_rejected(self):
        job = Job(
            title="Desenvolvedor Júnior",
            company="Eta Paulista",
            workplace_type="hybrid",
            location="São Paulo, SP",
            description="Node.js e React"
        )
        loc_ok, reason = is_location_allowed(job.workplace_type, job.location, job.title)
        assert loc_ok is False
        assert "fora da região" in reason

    def test_case_8_jr_onsite_sorocaba_accepted(self):
        job = Job(
            title="Desenvolvedor Júnior",
            company="Theta Sorocaba Tech",
            workplace_type="on-site",
            location="Sorocaba, SP",
            description="Node.js e PostgreSQL"
        )
        loc_ok, reason = is_location_allowed(job.workplace_type, job.location, job.title)
        assert loc_ok is True
        assert "Sorocaba" in reason

    def test_case_9_multi_source_gupy_linkedin_merged(self):
        job_gupy = Job(
            title="Desenvolvedor Java Junior",
            company="Goomer",
            workplace_type="remote",
            location="Brasil",
            description="Desenvolvimento de APIs com Java e Spring"
        )
        job_gupy.add_source("gupy", "901", "https://goomer.gupy.io/jobs/901")

        job_li = Job(
            title="Desenvolvedor Java Junior",
            company="Goomer",
            workplace_type="remote",
            location="Brasil",
            description="Desenvolvimento de APIs com Java e Spring"
        )
        job_li.add_source("linkedin", "902", "https://linkedin.com/jobs/view/902")

        dedup = Deduplicator()
        unique = dedup.process([job_gupy, job_li])
        assert len(unique) == 1
        assert len(unique[0].sources) == 2
        assert "gupy" in unique[0].sources
        assert "linkedin" in unique[0].sources

    def test_case_10_seen_job_not_notified_again(self, tmp_path):
        state_file = tmp_path / "state.json"
        store = StateStore(str(state_file))
        
        job = Job(
            title="Desenvolvedor React Jr",
            company="Iota Corp",
            workplace_type="remote",
            location="Brasil",
            description="React e TypeScript"
        )
        job.add_source("gupy", "1001", "https://iota.gupy.io/jobs/1001")
        fp = job.fingerprint

        # Primeira rodada: não vista
        assert store.is_seen(fp, "1001") is False
        store.mark_seen(fp, ["1001"])
        store.save()

        # Segunda rodada: já vista -> ignora
        store_round2 = StateStore(str(state_file))
        assert store_round2.is_seen(fp, "1001") is True

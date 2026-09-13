import os
import sys
from unittest.mock import patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.job import Job
from core.normalizer import is_pcd_exclusive, is_location_allowed
from core.scoring import evaluate_job


# Conjunto rotulado de teste de qualidade (Ground Truth Benchmark)
# Categorias:
# - SHOULD_NOTIFY: Oportunidade real compatível com o perfil
# - REJECT_PCD: Vaga afirmativa/exclusiva PCD
# - REJECT_LOCATION: Localidade incompatível com a regra estrita
# - REJECT_SENIOR: Vaga sênior ou lead
# - REJECT_DEGREE: Vaga júnior mas que exige ensino superior completo obrigatório
# - REJECT_NON_JOB: Notícia institucional, despedida ou desabafo
BENCHMARK_GROUND_TRUTH = [
    # --- Casos Positivos (Deve Notificar >= 50) ---
    {
        "id": "GT-POS-01",
        "title": "Desenvolvedor React Junior",
        "company": "Goomer",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Buscamos dev júnior para atuar com React, TypeScript e Tailwind no time de produto. Aceitamos estudantes e formados em cursos técnicos.",
        "expected": "SHOULD_NOTIFY",
        "mock_llm": {"is_real_job_opportunity": True, "cv_compatibility_score": 95, "reasoning": "Vaga Jr React/TS compatível", "recommendation": "APPLY_NOW"}
    },
    {
        "id": "GT-POS-02",
        "title": "Desenvolvedor Java Junior",
        "company": "GFT Brasil",
        "workplace_type": "on-site",
        "location": "Sorocaba - SP",
        "description": "Vaga presencial em Sorocaba para dev Java/Spring júnior.",
        "expected": "SHOULD_NOTIFY",
        "mock_llm": {"is_real_job_opportunity": True, "cv_compatibility_score": 90, "reasoning": "Java Jr em Sorocaba na GFT", "recommendation": "APPLY_NOW"}
    },
    {
        "id": "GT-POS-03",
        "title": "Estágio em Desenvolvimento Web",
        "company": "Startup Tech",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Estágio para quem está cursando graduação ou técnico em TI. Atuação com Node.js e React.",
        "expected": "SHOULD_NOTIFY",
        "mock_llm": {"is_real_job_opportunity": True, "cv_compatibility_score": 90, "reasoning": "Estágio Node/React remoto", "recommendation": "APPLY_NOW"}
    },
    {
        "id": "GT-POS-04",
        "title": "Desenvolvedor Full Stack Jr",
        "company": "Empresa Parceira",
        "workplace_type": "hybrid",
        "location": "Tatuí - SP",
        "description": "Atuação híbrida na cidade de Tatuí com TypeScript, React e Supabase.",
        "expected": "SHOULD_NOTIFY",
        "mock_llm": {"is_real_job_opportunity": True, "cv_compatibility_score": 92, "reasoning": "Fullstack Jr híbrido Tatuí", "recommendation": "APPLY_NOW"}
    },

    # --- Casos Negativos: Veto Semântico / Não-Vaga ---
    {
        "id": "GT-NEG-NONJOB",
        "title": "Despedida da Goomer e próximos passos",
        "company": "Goomer",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Hoje encerro minha jornada na Goomer como desenvolvedor React. Agradeço imensamente ao time!",
        "expected": "REJECT_NON_JOB",
        "mock_llm": {"is_real_job_opportunity": False, "cv_compatibility_score": 0, "reasoning": "Post de despedida de ex-colaborador", "recommendation": "SKIP"}
    },

    # --- Casos Negativos: Vagas PCD Afirmativas ---
    {
        "id": "GT-NEG-PCD-01",
        "title": "Desenvolvedor Frontend Jr - Exclusivo PCD",
        "company": "Fintech SA",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Vaga afirmativa voltada exclusivamente para profissionais com deficiência.",
        "expected": "REJECT_PCD",
        "mock_llm": None
    },
    {
        "id": "GT-NEG-PCD-02",
        "title": "Pessoa Desenvolvedora Junior (PCD)",
        "company": "Banco Digital",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Oportunidade afirmativa PCD.",
        "expected": "REJECT_PCD",
        "mock_llm": None
    },

    # --- Casos Negativos: Localização Incompatível ---
    {
        "id": "GT-NEG-LOC-01",
        "title": "Desenvolvedor Front-end React Jr",
        "company": "Agência Digital",
        "workplace_type": "hybrid",
        "location": "São Paulo - Capital (Av. Paulista)",
        "description": "Vaga híbrida 3x na semana na Paulista.",
        "expected": "REJECT_LOCATION",
        "mock_llm": None
    },
    {
        "id": "GT-NEG-LOC-02",
        "title": "Desenvolvedor Node.js Jr",
        "company": "Software House",
        "workplace_type": "on-site",
        "location": "Curitiba - PR",
        "description": "Presencial obrigatório em Curitiba.",
        "expected": "REJECT_LOCATION",
        "mock_llm": None
    },

    # --- Casos Negativos: Senioridade Alta ---
    {
        "id": "GT-NEG-SENIOR-01",
        "title": "Tech Lead / Especialista React",
        "company": "Goomer",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Liderança técnica para o time de frontend.",
        "expected": "REJECT_SENIOR",
        "mock_llm": None
    },
    {
        "id": "GT-NEG-SENIOR-02",
        "title": "Desenvolvedor Full Stack Sênior",
        "company": "Startup",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Buscamos sênior com 7+ anos de experiência.",
        "expected": "REJECT_SENIOR",
        "mock_llm": None
    },

    # --- Casos Negativos: Formação Superior Obrigatória (Detectada pelo LLM) ---
    {
        "id": "GT-NEG-DEGREE",
        "title": "Desenvolvedor React Junior",
        "company": "Corporação Tradicional",
        "workplace_type": "remote",
        "location": "Remoto",
        "description": "Requisitos obrigatórios inegociáveis: Diploma de Bacharelado em Ciência da Computação ou Engenharia de Software concluído (obrigatório).",
        "expected": "REJECT_DEGREE",
        "mock_llm": {"is_real_job_opportunity": True, "cv_compatibility_score": 15, "reasoning": "Exige bacharelado completo obrigatório; candidato cursa Fatec/técnico", "recommendation": "SKIP"}
    },
]


class TestRadarQualityMetrics:
    """
    Avaliação formal de Radar Quality:
    Testa a esteira inteira (Filtro PCD -> Filtro Regional -> Scoring Heurístico -> LLM Judge -> Decisão Final)
    e calcula métricas de Machine Learning / Data Engineering (Precision e Recall).
    """

    def _evaluate_single_case(self, case: dict) -> str:
        job = Job(
            title=case["title"],
            company=case["company"],
            workplace_type=case["workplace_type"],
            location=case["location"],
            description=case["description"],
        )

        # 1. Filtro PCD
        is_pcd, _ = is_pcd_exclusive(job.title)
        if is_pcd:
            return "DISCARD_PCD"

        # 2. Filtro Localização
        loc_ok, _ = is_location_allowed(job.workplace_type, job.location, job.title)
        if not loc_ok:
            return "DISCARD_LOCATION"

        # 3. Scoring com Mock do LLM Judge
        mock_llm = case.get("mock_llm")
        with patch("core.llm_judge.judge", return_value=mock_llm):
            score, reasons = evaluate_job(job)

        if score <= 0:
            return "DISCARD_SENIOR_OR_VETO"
        if score < 50:
            return "DISCARD_LOW_SCORE"
        return "NOTIFY"

    def test_precision_and_recall_benchmarks(self):
        tp = 0  # True Positives: vaga elegível e NOTIFICADA
        fp = 0  # False Positives: vaga inelegível mas NOTIFICADA (lixo no celular)
        tn = 0  # True Negatives: vaga inelegível e DESCARTADA
        fn = 0  # False Negatives: vaga elegível mas DESCARTADA (oportunidade perdida)

        results = []
        for case in BENCHMARK_GROUND_TRUTH:
            actual_decision = self._evaluate_single_case(case)
            is_predicted_notify = (actual_decision == "NOTIFY")
            is_actual_notify = (case["expected"] == "SHOULD_NOTIFY")

            if is_actual_notify and is_predicted_notify:
                tp += 1
            elif not is_actual_notify and is_predicted_notify:
                fp += 1
            elif not is_actual_notify and not is_predicted_notify:
                tn += 1
            elif is_actual_notify and not is_predicted_notify:
                fn += 1

            results.append({
                "id": case["id"],
                "expected": case["expected"],
                "decision": actual_decision,
                "correct": (is_predicted_notify == is_actual_notify)
            })

        # Precision = TP / (TP + FP) -> mede a pureza dos alertas
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        # Recall = TP / (TP + FN) -> mede se deixamos passar oportunidades
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0

        print(f"\n==========================================")
        print(f" [*] RADAR QUALITY BENCHMARK REPORT")
        print(f"==========================================")
        print(f"|-- Total de Casos de Teste: {len(BENCHMARK_GROUND_TRUTH)}")
        print(f"|-- True Positives (TP):     {tp}")
        print(f"|-- True Negatives (TN):     {tn}")
        print(f"|-- False Positives (FP):    {fp}")
        print(f"|-- False Negatives (FN):    {fn}")
        print(f"|-----------------------------------------")
        print(f"|-- Precision (Pureza):      {precision * 100:.1f}%")
        print(f"|-- Recall (Cobertura):      {recall * 100:.1f}%")
        print(f"==========================================\n")

        # ASSERTIVIDADE CRÍTICA DE PRODUTO:
        # Precision deve ser 100% (zero spam / zero falsos positivos)
        assert precision == 1.0, f"Precision abaixo de 100%: {precision}. Falsos positivos detectados!"
        # Recall deve ser 100% no benchmark (zero oportunidades ideais perdidas)
        assert recall == 1.0, f"Recall abaixo de 100%: {recall}. Falsos negativos detectados!"

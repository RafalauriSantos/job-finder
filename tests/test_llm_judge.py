import os
import sys
from unittest.mock import patch, MagicMock
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.job import Job
from core import llm_judge
from core.scoring import evaluate_job


class TestLlmJudgeUnits:
    def test_should_invoke_judge_threshold(self):
        assert llm_judge.should_invoke_judge(30) is True
        assert llm_judge.should_invoke_judge(29) is False
        assert llm_judge.should_invoke_judge(0) is False
        assert llm_judge.should_invoke_judge(85) is True

    def test_get_profile_loads_data(self):
        profile = llm_judge.get_profile()
        assert isinstance(profile, dict)
        assert "stack_core" in profile
        assert "React" in profile["stack_core"]

    def test_judge_returns_none_when_no_api_key(self):
        with patch.dict(os.environ, {}, clear=True):
            result = llm_judge.judge("Dev", "Corp", "Desc")
            assert result is None

    def test_judge_calls_gemini_when_gemini_key_present(self):
        fake_response = {
            "is_real_job_opportunity": True,
            "cv_compatibility_score": 85,
            "reasoning": "Vaga React com match",
            "recommendation": "APPLY_NOW"
        }
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_gemini_key"}, clear=True):
            with patch("core.llm_judge._call_gemini", return_value=fake_response) as mock_gemini:
                result = llm_judge.judge("Dev React", "Goomer", "React, Node.js")
                assert mock_gemini.called
                assert result["cv_compatibility_score"] == 85

    def test_judge_handles_api_exception_gracefully(self):
        with patch.dict(os.environ, {"GEMINI_API_KEY": "fake_gemini_key"}, clear=True):
            with patch("core.llm_judge._call_gemini", side_effect=Exception("API down")):
                result = llm_judge.judge("Dev", "Corp", "Desc")
                assert result is None


class TestEvaluateJobIntegration:
    def test_skips_judge_when_heuristic_score_below_floor(self):
        """Vaga com score < 30 nem bate na API do LLM."""
        job = Job(
            title="Analista Administrativo",
            company="Empresa Genérica",
            workplace_type="remote",
        )
        with patch("core.llm_judge.judge") as mock_judge:
            score, reasons = evaluate_job(job)
            assert not mock_judge.called
            assert score < 30

    def test_fallback_to_heuristic_when_judge_fails(self):
        """Se o LLM falhar, a vaga preserva seu score heurístico intacto."""
        job = Job(
            title="Desenvolvedor React Junior",
            company="Startup",
            workplace_type="remote",
        )
        with patch("core.llm_judge.judge", return_value=None):
            score, reasons = evaluate_job(job)
            assert score >= 50
            assert any("react" in r.lower() or "júnior" in r.lower() or "junior" in r.lower() for r in reasons)

    def test_llm_veto_zeros_score(self):
        """Veto do LLM (ex: notícia ou desabafo) zera o score e adiciona razão."""
        job = Job(
            title="Desenvolvedor React Junior",
            company="Goomer",
            workplace_type="remote",
        )
        fake_llm_result = {
            "is_real_job_opportunity": False,
            "cv_compatibility_score": 0,
            "reasoning": "Texto é um post de despedida de funcionário, não uma vaga",
            "recommendation": "SKIP"
        }
        with patch("core.llm_judge.judge", return_value=fake_llm_result):
            score, reasons = evaluate_job(job)
            assert score == 0
            assert any("não é vaga real" in r for r in reasons)

    def test_combined_score_weighting(self):
        """Score combinado: 30% heurístico + 70% LLM."""
        job = Job(
            title="Desenvolvedor React Junior",
            company="Goomer",
            workplace_type="remote",
        )
        # Heurístico vai dar ~75
        fake_llm_result = {
            "is_real_job_opportunity": True,
            "cv_compatibility_score": 90,
            "reasoning": "Vaga Júnior com fit total na stack",
            "recommendation": "APPLY_NOW"
        }
        with patch("core.llm_judge.judge", return_value=fake_llm_result):
            score, reasons = evaluate_job(job)
            assert score > 70
            assert any("LLM Judge:" in r for r in reasons)

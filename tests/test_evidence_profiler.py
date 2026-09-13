import os
import sys
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.job import Job
from core.evidence import profile_job_evidence, should_route_to_llm


def test_profile_empty_description_is_low_evidence():
    job = Job(
        title="Desenvolvedor Júnior",
        company="Empresa RSS",
        workplace_type="unknown",
        description="",
    )
    profile = profile_job_evidence(job)
    assert profile["level"] == "LOW_EVIDENCE"
    assert profile["score"] < 40
    assert should_route_to_llm(job) is False


def test_profile_rich_gupy_description_is_high_evidence():
    desc = (
        "Estamos buscando um Desenvolvedor Full Stack Júnior para nosso time de tecnologia. "
        "Requisitos essenciais: React, TypeScript, Node.js, PostgreSQL e Tailwind CSS. "
        "Diferencial: Experiência com Docker, Supabase e metodologias ágeis. "
        "Benefícios: Plano de saúde, VR/VA, horário flexível e trabalho 100% remoto."
    )
    job = Job(
        title="Desenvolvedor Full Stack Júnior",
        company="Fintech Digital",
        workplace_type="remote",
        location="São Paulo, SP",
        description=desc,
    )
    profile = profile_job_evidence(job)
    assert profile["level"] == "HIGH_EVIDENCE"
    assert profile["score"] >= 60
    assert should_route_to_llm(job) is True


def test_profile_medium_evidence():
    desc = "Vaga dev React e Node.js para atuar em Sorocaba. Enviar currículo."
    job = Job(
        title="Desenvolvedor Web",
        company="Agência Local",
        workplace_type="hybrid",
        location="Sorocaba",
        description=desc,
    )
    profile = profile_job_evidence(job)
    # Com descrição curta (~70 chars) mas localização e título válidos
    assert profile["level"] in ["LOW_EVIDENCE", "MEDIUM_EVIDENCE"]

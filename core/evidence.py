from typing import Dict, Any
from models.job import Job


def profile_job_evidence(job: Job) -> Dict[str, Any]:
    """
    Avalia a densidade de evidência da vaga (SPEC-008).
    Classificação:
    - LOW_EVIDENCE: < 200 caracteres de descrição ou texto raso.
    - MEDIUM_EVIDENCE: 200 a 500 caracteres com dados parciais.
    - HIGH_EVIDENCE: >= 500 caracteres ou descrição estruturada.
    """
    desc = (job.description or "").strip()
    desc_len = len(desc)

    evidence_score = 0
    signals = []

    # 1. Densidade da Descrição (até 50 pontos)
    if desc_len >= 500:
        evidence_score += 50
        signals.append("Descrição longa e detalhada (>= 500 chars)")
    elif desc_len >= 200:
        evidence_score += 30
        signals.append("Descrição média (200-499 chars)")
    elif desc_len > 0:
        evidence_score += 10
        signals.append("Descrição curta (< 200 chars)")
    else:
        signals.append("Descrição ausente")

    # 2. Qualidade do Título (até 20 pontos)
    title_words = len(job.title.split())
    if title_words >= 3:
        evidence_score += 20
        signals.append("Título bem estruturado")
    elif title_words >= 1:
        evidence_score += 10

    # 3. Metadados de Localidade e Modalidade (até 20 pontos)
    if job.workplace_type and job.workplace_type != "unknown":
        evidence_score += 10
        signals.append(f"Modalidade explícita: {job.workplace_type}")
    if job.location:
        evidence_score += 10
        signals.append(f"Localidade informada: {job.location}")

    # 4. Empresa Identificada (10 pontos)
    if job.company and job.company.lower() not in ["rss", "unknown", ""]:
        evidence_score += 10

    # Classificação
    if evidence_score >= 60:
        level = "HIGH_EVIDENCE"
    elif evidence_score >= 35:
        level = "MEDIUM_EVIDENCE"
    else:
        level = "LOW_EVIDENCE"

    job.evidence_level = level

    return {
        "level": level,
        "score": evidence_score,
        "signals": signals,
        "desc_length": desc_len,
    }


def should_route_to_llm(job: Job) -> bool:
    """
    Regra de decisão da SPEC-008:
    Vagas LOW_EVIDENCE (especialmente RSS raso ou sem metadados suficientes)
    NÃO devem consumir a cota de 15 RPM do Gemini 2.5 Flash-Lite.
    Vagas MEDIUM_EVIDENCE e HIGH_EVIDENCE possuem evidência suficiente e são roteadas ao LLM.
    """
    profile = profile_job_evidence(job)
    return profile["level"] in ["MEDIUM_EVIDENCE", "HIGH_EVIDENCE"]

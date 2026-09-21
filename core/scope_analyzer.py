"""Analise explicavel do escopo real de uma vaga.

O titulo continua sendo um sinal, mas nao e mais tratado como verdade absoluta.
Esta camada e deliberadamente deterministica para que cada alerta possa ser
auditado e para que o aprendizado do bot nao dependa apenas do LLM.
"""

import re
import unicodedata
from typing import Dict, List

from models.job import Job


CATEGORIES = (
    "COMPATIVEL",
    "POTENCIALMENTE_COMPATIVEL",
    "DESAFIADORA_VALIDA",
    "INCOMPATIVEL",
)


def _clean(value: str) -> str:
    value = unicodedata.normalize("NFD", value or "").lower()
    return "".join(c for c in value if unicodedata.category(c) != "Mn")


def _hits(text: str, signals: List[str]) -> List[str]:
    return [signal for signal in signals if signal in text]


def _declared_level(title: str) -> str:
    text = _clean(title)
    if re.search(r"\b(senior|sr|lead|staff|principal|especialista|arquiteto)\b", text):
        return "senior"
    if re.search(r"\b(pleno|pl)\b", text):
        return "mid"
    if re.search(r"\b(junior|jr|estagio|trainee|entry level|developer i)\b", text):
        return "junior"
    return "unknown"


def _requirements(text: str) -> Dict[str, List[str]]:
    """Classifica linhas por contexto, sem tentar inventar tecnologias."""
    mandatory: List[str] = []
    desirable: List[str] = []
    mode = "mandatory"
    for raw_line in (text or "").splitlines():
        line = raw_line.strip(" -*•\t")
        if not line:
            continue
        normalized = _clean(line)
        if any(marker in normalized for marker in ("desejavel", "diferencial", "diferenciais", "sera um plus", "nice to have")):
            mode = "desirable"
            continue
        if any(marker in normalized for marker in ("requisitos obrigatorios", "requisitos necessarios", "obrigatorio", "necessario", "o que buscamos")):
            mode = "mandatory"
            continue
        if len(line) >= 3 and (line.startswith(("-", "•")) or mode in ("mandatory", "desirable")):
            (desirable if mode == "desirable" else mandatory).append(line)
    return {"mandatory": mandatory, "desirable": desirable}


def _education_barriers(text: str) -> List[str]:
    """Detect completed-degree requirements that the profile cannot satisfy."""
    barriers = []
    for raw_line in (text or "").splitlines():
        line = _clean(raw_line)
        if not any(term in line for term in (
            "ensino superior completo", "graduacao completa", "graduacao concluida",
            "superior completo", "formacao superior concluida",
        )):
            continue
        if any(exception in line for exception in (
            "ou em andamento", "em andamento", "cursando", "desejavel",
            "desejaveis", "diferencial",
        )):
            continue
        barriers.append(raw_line.strip())
    return barriers


def analyze_scope(job: Job, profile: Dict = None) -> Dict:
    """Retorna a decisao de compatibilidade com evidencia legivel."""
    from core.llm_judge import get_profile

    profile = profile or get_profile()
    title = _clean(job.title)
    description = _clean(job.description)
    text = f"{title} {description}"
    declared = _declared_level(job.title)

    support = _hits(text, [
        "sob orientacao", "com acompanhamento", "sob supervisao", "apoio ao desenvolvimento",
        "correcoes simples", "testes basicos", "vontade de aprender", "mentoria",
        "nao esperamos que voce saiba tudo", "estamos formando o time",
    ])
    advanced = _hits(text, [
        "autonomia", "arquitetura", "alta disponibilidade", "escalabilidade", "lideranca",
        "liderar time", "tech lead", "decisoes tecnicas", "mentorar", "ownership",
        "microsservicos", "microservicos", "5 anos", "6 anos", "7 anos",
    ])
    hard_barriers = _hits(text, [
        "liderar time", "tech lead", "5 anos", "6 anos", "7 anos", "exclusiva para pcd",
    ])
    education_barriers = _education_barriers(job.description)
    hard_barriers.extend(education_barriers)

    if len(advanced) >= 2 or any(x in advanced for x in ("tech lead", "liderar time", "5 anos", "6 anos")):
        operational = "senior"
    elif support and declared in ("mid", "senior") and not advanced:
        operational = "junior_to_mid"
    elif support:
        operational = "junior"
    else:
        operational = declared

    core = {_clean(x) for x in profile.get("stack_core", [])}
    secondary = {_clean(x) for x in profile.get("stack_secundaria", [])}
    skills_text = f"{title} {description}"
    core_matches = sorted(x for x in core if x and x in skills_text)
    secondary_matches = sorted(x for x in secondary if x and x in skills_text)
    reqs = _requirements(job.description)

    evidence = min(100, 20 + len(core_matches) * 15 + len(secondary_matches) * 8 + len(support) * 5)
    compatibility = min(100, 25 + len(core_matches) * 15 + len(secondary_matches) * 7)
    if declared == "junior":
        compatibility += 15
    if operational == "junior_to_mid":
        compatibility += 10
    if operational == "senior":
        compatibility -= 25
    compatibility = max(0, min(100, compatibility))

    potential = min(100, compatibility + len(secondary_matches) * 8 + (15 if support else 0))
    if hard_barriers:
        category = "INCOMPATIVEL"
    elif compatibility >= 60:
        category = "COMPATIVEL"
    elif potential >= 45:
        category = "POTENCIALMENTE_COMPATIVEL"
    elif potential >= 35:
        category = "DESAFIADORA_VALIDA"
    else:
        category = "INCOMPATIVEL"

    gaps = [item for item in reqs["mandatory"] if not any(match in _clean(item) for match in core_matches + secondary_matches)]
    reasons = []
    if declared != operational and operational != "unknown":
        reasons.append(f"titulo indica {declared}, mas o escopo operacional parece {operational}")
    if support:
        reasons.append("ha sinais de acompanhamento e tarefas de entrada")
    if advanced:
        reasons.append(f"escopo avancado detectado: {', '.join(advanced[:3])}")
    if core_matches:
        reasons.append(f"evidencias da stack principal: {', '.join(core_matches[:5])}")
    if gaps:
        reasons.append(f"possiveis lacunas obrigatorias: {', '.join(gaps[:2])}")

    return {
        "declared_level": declared,
        "operational_level": operational,
        "level_confidence": "high" if support or advanced else "medium",
        "responsibilities": support + advanced,
        "mandatory_requirements": reqs["mandatory"],
        "desirable_requirements": reqs["desirable"],
        "hard_barriers": hard_barriers,
        "education_barriers": education_barriers,
        "matched_evidence": core_matches + secondary_matches,
        "trainable_gaps": gaps[:5],
        "compatibility_score": compatibility,
        "potential_score": potential,
        "evidence_score": evidence,
        "category": category,
        "reasoning": "; ".join(reasons) or "evidencia insuficiente para uma conclusao forte",
    }

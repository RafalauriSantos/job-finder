"""Analise explicavel do escopo real de uma vaga.

O titulo continua sendo um sinal, mas nao e mais tratado como verdade absoluta.
Esta camada e deliberadamente deterministica para que cada alerta possa ser
auditado e para que o aprendizado do bot nao dependa apenas do LLM.
"""

import re
import html
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
    return [signal for signal in signals if re.search(r"(?<!\w)" + re.escape(signal) + r"(?!\w)", text)]


def _declared_level(title: str) -> str:
    text = _clean(title)
    if re.search(r"\b(senior|sr|lead|staff|principal|especialista|arquiteto)\b", text):
        return "senior"
    if re.search(r"\b(pleno|pl)\b", text):
        return "mid"
    if re.search(r"\b(junior|jr|estagio|estagiario|estagiaria|intern|internship|trainee|entry level|developer i)\b", text):
        return "junior"
    return "unknown"


def _requirements(text: str) -> Dict[str, List[str]]:
    """Extract concise requirement clauses instead of treating the whole ad as mandatory."""
    mandatory: List[str] = []
    desirable: List[str] = []
    text = re.sub(r"<[^>]+>", "\n", html.unescape(text or ""))
    original_text = text
    text = re.sub(r"\s+[-•]\s+", "\n", text)
    header_patterns = [
        ("desirable", r"desej[aá]ve(?:l|is)|diferencia(?:l|is)|ser[aá] um plus|nice to have|preferred qualifications"),
        ("mandatory", r"requisitos obrigat[oó]rios|requisitos necess[aá]rios|requisitos e qualifica[cç][oõ]es|qualifica[cç][oõ]es|o que buscamos|o que voc[eê] precisa ter|what we are looking for|required skills|must-have skills|what you bring|mandatory requirements"),
        ("end", r"responsabilidades|o que voc[eê] vai fazer|o que voc[eê] far[aá]|what you will do|responsibilities|benef[ií]cios|informa[cç][oõ]es adicionais|about the company|sobre a empresa"),
    ]
    for kind, pattern in header_patterns:
        text = re.sub(rf"(?i)\b(?:{pattern})\s*:?", f"\n__{kind.upper()}__\n", text)

    mode = None
    # Splitting on sentence/list punctuation also handles flattened LinkedIn
    # descriptions while keeping ordinary company introductions out of the set.
    for raw_clause in re.split(r"\n+|[;.!?]+|,(?=\s*(?:[A-Z0-9]|com |experi|ingl[eê]s|React|Node|Java|Python))", text):
        line = raw_clause.strip(" -*•\t:")
        if not line:
            continue
        marker = line.strip("_").upper()
        if marker == "MANDATORY":
            mode = "mandatory"
            continue
        if marker == "DESIRABLE":
            mode = "desirable"
            continue
        if marker == "END":
            mode = None
            continue
        if mode is None:
            continue
        normalized = _clean(line)
        # Exclude generic marketing statements and retain requirement-like
        # clauses (known skills, education, experience, language, or availability).
        if not any(re.search(pattern, normalized) for pattern in (
            r"\b(react|typescript|javascript|node|postgres|supabase|java|spring|python|docker|git|angular|vue|next|figma|aws|azure|laravel|n8n|langchain|langgraph|rag|pandas|numpy|scikit|sklearn|oracle|sql server|sql|api|english|ingles|graduacao|superior|experiencia|experience|degree|bachelor|master|availability|disponibilidade|crm|gtm|ga4|function calling|tool use)\b",
        )):
            continue
        target = desirable if mode == "desirable" else mandatory
        if line not in target:
            target.append(line)
    # Keep explicit inline clauses when a flat source omits section headings.
    clauses = re.split(r"\n+|(?<=[.!?])\s+", original_text)
    for clause in clauses:
        line = clause.strip(" -*•\t")
        normalized = _clean(line)
        if re.match(r"(?:obrigatorio|obrigatoria|necessario|necessaria)\s*:", normalized):
            if line not in mandatory:
                mandatory.append(line)
        elif re.match(r"(?:desejavel|desejaveis|diferencial|diferenciais)\s*:", normalized):
            if line not in desirable:
                desirable.append(line)
        elif re.search(r"\b(english|ingles|bachelor|degree|graduacao|ensino superior)\b", normalized):
            if line not in mandatory and line not in desirable:
                mandatory.append(line)
    inline_desirable = [item for item in desirable if re.match(r"(?i)^\s*(?:desej[aá]vel|diferencial)\s*:", item)]
    for inline in inline_desirable:
        value = inline.split(":", 1)[1].strip()
        desirable = [item for item in desirable if item == inline or item != value]
    return {"mandatory": mandatory, "desirable": desirable}


def _technology_hits(text: str) -> List[str]:
    from core.normalizer import KNOWN_TECHNOLOGIES

    normalized = _clean(text)
    return sorted({name for name, aliases in KNOWN_TECHNOLOGIES if _hits(normalized, [_clean(alias) for alias in aliases])})


def _profile_skill_names(profile: Dict) -> set:
    values = profile.get("stack_core", []) + profile.get("stack_secundaria", [])
    return set(_technology_hits(" ".join(values)))


def _education_barriers(text: str) -> List[str]:
    """Detect completed-degree requirements that the profile cannot satisfy."""
    barriers = []
    clauses = re.split(r"\n+|(?<=[.!?])\s+|;", html.unescape(text or ""))
    for raw_line in clauses:
        line = _clean(raw_line)
        if not any(term in line for term in (
            "ensino superior completo", "graduacao completa", "graduacao concluida",
            "superior completo", "formacao superior concluida", "completed bachelor",
            "bachelor degree required", "bachelor's degree required", "must have a bachelor",
            "completed degree required", "degree completed required",
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

    reqs = _requirements(job.description)
    profile_skills = _profile_skill_names(profile)
    relevant_text = f"{job.title} {' '.join(reqs['mandatory'])}"
    matched_technologies = sorted(set(_technology_hits(relevant_text)) & profile_skills)
    core = set(_technology_hits(" ".join(profile.get("stack_core", []))))
    secondary = set(_technology_hits(" ".join(profile.get("stack_secundaria", []))))
    core_matches = sorted(set(matched_technologies) & core)
    secondary_matches = sorted(set(matched_technologies) & secondary)

    hard_barriers = list(hard_barriers)
    profile_language = _clean(profile.get("english_level", ""))
    mandatory_text = " ".join(reqs["mandatory"])
    if profile_language in {"basic", "basic-intermediate", "beginner", "basico", "basico-intermediario"}:
        if re.search(r"\b(advanced|fluent|fluency|proficient|native|avancado|fluente|fluencia|proficiente|nativo)\b.{0,35}\b(english|ingles)\b|\b(english|ingles)\b.{0,35}\b(advanced|fluent|fluency|proficient|native|avancado|fluente|fluencia|proficiente|nativo)\b", _clean(mandatory_text)):
            hard_barriers.append("nível avançado/fluência de inglês exigido; perfil informado: básico-intermediário")

    skill_evidence = profile.get("skills_evidence", {})
    missing_required_skills = sorted({
        technology
        for requirement in reqs["mandatory"]
        for technology in _technology_hits(requirement)
        if technology not in profile_skills
    })
    for requirement in reqs["mandatory"]:
        clause_technologies = _technology_hits(requirement)
        year_requirement = bool(re.search(r"\b\d+\s*\+?\s*(?:years?|anos?)\b", _clean(requirement)))
        for technology in clause_technologies:
            evidence = skill_evidence.get(technology, {})
            if year_requirement and (
                technology not in profile_skills
                or evidence.get("level") in {"learning", "beginner", "project", "iniciante", "em desenvolvimento"}
            ):
                hard_barriers.append(f"experiência mínima exigida em {technology} não comprovada")

    evidence = min(100, 20 + len(core_matches) * 15 + len(secondary_matches) * 8 + len(support) * 5)
    compatibility = min(100, 25 + len(core_matches) * 15 + len(secondary_matches) * 7)
    if declared == "junior":
        compatibility += 15
    if operational == "junior_to_mid":
        compatibility += 10
    if operational == "senior":
        compatibility -= 25
    compatibility -= min(30, len(missing_required_skills) * 8)
    compatibility = max(0, min(100, compatibility))

    potential = min(100, compatibility + len(secondary_matches) * 8 + (15 if support else 0))
    if hard_barriers or (len(missing_required_skills) >= 4 and not support):
        category = "INCOMPATIVEL"
    elif compatibility >= 60 and not missing_required_skills:
        category = "COMPATIVEL"
    elif potential >= 45:
        category = "POTENCIALMENTE_COMPATIVEL"
    elif potential >= 35:
        category = "DESAFIADORA_VALIDA"
    else:
        category = "INCOMPATIVEL"

    gaps = [f"Requisito técnico obrigatório sem evidência no perfil: {item}" for item in missing_required_skills]
    gaps.extend(
        item for item in reqs["mandatory"]
        if not _technology_hits(item) and any(term in _clean(item) for term in ("english", "ingles", "graduacao", "superior", "bachelor", "master"))
    )
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

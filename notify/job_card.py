"""One evidence-based presentation shared by Telegram and email."""
import html
import re
from urllib.parse import urlsplit

from core.scope_analyzer import _clean, _requirements, _hits


def clean(value, limit=180):
    text = re.sub(r"\s+", " ", html.unescape(str(value or ""))).strip()
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def escape(value):
    return html.escape(value, quote=True)


def application_url(job):
    candidates = [job.primary_url] + [source.url for source in job.sources.values()]
    for value in candidates:
        value = html.unescape(value or "").strip()
        parsed = urlsplit(value)
        if parsed.scheme in {"http", "https"} and parsed.netloc:
            return value
    return ""


def build_card(job):
    """Keep internal scores in storage; never present defaults as confirmed facts."""
    title = clean(job.title)
    company = clean(job.company, 100)
    workplace = {"remote": "Remoto", "hybrid": "Híbrido", "on-site": "Presencial"}.get(
        job.workplace_type, "Modalidade a confirmar")
    location = clean(job.location, 100)
    if location and _clean(location) not in {_clean(workplace), "remote", "remoto", "unknown", "nao informado"}:
        workplace += f" · {location}"
    lines = [f"<b>{escape(title)}</b>", escape(f"{company} · {workplace}")]
    technologies = list(dict.fromkeys(clean(t, 30) for t in job.technologies if t))[:4]
    if technologies:
        lines.extend(["", escape(" · ".join(technologies))])

    # job_type historically defaults to CLT even for internships. Only show
    # contract labels supported explicitly by the source description.
    contracts = [label for label in ("CLT", "PJ") if re.search(rf"\b{label}\b", job.description or "", re.I)]
    facts = []
    internship = bool(re.search(r"\b(intern|internship|estagio|estagiario|estagiaria)\b", _clean(title)))
    if not internship and len(contracts) == 1 and job.job_type.upper() == contracts[0]:
        facts.append(contracts[0])
    salary = clean(job.salary, 100)
    if salary and _clean(salary) not in {"nao informado", "a combinar", "unknown", "nao divulgado"}:
        facts.append(salary)
    if facts:
        lines.append(escape(" · ".join(facts)))

    analysis = job.analysis or {}
    matched = list(dict.fromkeys(clean(t, 30) for t in analysis.get("matched_evidence", []) if t))[:3]
    reason = ("Tecnologias do seu perfil encontradas: " + ", ".join(matched) + ".") if matched else "Confira os requisitos antes de se candidatar."
    if job.compatibility_category in {"POTENCIALMENTE_COMPATIVEL", "DESAFIADORA_VALIDA"}:
        reason = "Possibilidade de progressão. " + reason
    lines.extend(["", escape(reason)])

    # Select cautions independently of score explanations (which can hide
    # requirements after the first three reasons).
    cautions = []
    for barrier in analysis.get("hard_barriers", []):
        if _hits(_clean(job.description), [_clean(barrier)]):
            cautions.append("Requisito a conferir: " + clean(barrier, 140))
    requirements = _requirements(job.description).get("mandatory", [])
    for requirement in requirements:
        normalized = _clean(requirement)
        if re.search(r"\b(ingles|english|bacharelado|bachelor|graduacao|superior completo)\b", normalized):
            match = re.search(r"\b(ingles|english|bacharelado|bachelor|graduacao|superior completo)\b", normalized)
            # Preserve the context around the requirement, not the start of a
            # long company introduction that happened to share the same line.
            start = max(0, match.start() - 55)
            excerpt = requirement[start:match.end() + 100]
            if start:
                excerpt = "…" + excerpt.split(" ", 1)[-1]
            cautions.append("Confira no anúncio: " + clean(excerpt, 160))
    if job.ranking_evidence.get("risk") or analysis.get("operational_level") == "senior":
        cautions.append("Os requisitos podem estar acima do nível anunciado.")
    if job.evidence_level == "LOW_EVIDENCE":
        cautions.append("Há poucas informações disponíveis sobre os requisitos.")
    cautions = list(dict.fromkeys(cautions))
    if cautions:
        lines.extend(["", "<b>Atenção:</b> " + escape(" ".join(cautions[:2]))])
    return "\n".join(lines), application_url(job)

from typing import Literal
from models.job import Job
from core.normalizer import is_location_allowed, normalize_workplace, ALLOWED_REGIONAL_CITIES


Decision = Literal["VETO", "LOW_SCORE", "APPROVED"]


def classify_score(score: int, minimum_score: int) -> Decision:
    """Classifica o resultado final do scoring em uma decisão do funil."""
    if score <= 0:
        return "VETO"
    if score < minimum_score:
        return "LOW_SCORE"
    return "APPROVED"


def classify_evidence(job: Job) -> str:
    """Bloqueia somente RSS raso; fontes estruturadas seguem para scoring."""
    if "rss" in job.sources and job.evidence_level == "LOW_EVIDENCE":
        return "LOW_EVIDENCE"
    return "APPROVED"


def classify_location(job: Job):
    """Aplica a política regional existente e preserva o motivo."""
    description = job.description or ""
    effective_workplace = job.workplace_type
    if effective_workplace == "unknown":
        effective_workplace = normalize_workplace("", description, job.title)
    combined = f"{job.location} {job.title} {description}".lower()
    known_location = bool(job.location and job.location.lower() not in {"brasil", "brazil", "remoto", "a confirmar"})
    regional = any(city in combined for city in ALLOWED_REGIONAL_CITIES)
    if effective_workplace == "unknown" and known_location and not regional:
        return "LOCATION_REJECTED", "Localidade explícita fora da região aceita e modalidade não confirmada"
    allowed, reason = is_location_allowed(effective_workplace, job.location, f"{job.title} {description}")
    return ("APPROVED" if allowed else "LOCATION_REJECTED", reason)

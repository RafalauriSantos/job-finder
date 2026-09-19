from typing import Literal
from models.job import Job
from core.normalizer import is_location_allowed


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
    allowed, reason = is_location_allowed(job.workplace_type, job.location, job.title)
    return ("APPROVED" if allowed else "LOCATION_REJECTED", reason)

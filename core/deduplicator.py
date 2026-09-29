from difflib import SequenceMatcher
from hashlib import sha256
from typing import Dict, List
import re
import unicodedata
from models.job import Job
from core.normalizer import normalize_published_at


class Deduplicator:
    """
    Gerencia a deduplicação de vagas e a fusão de múltiplas fontes para a mesma oportunidade.
    """
    def __init__(self):
        self.jobs_by_fingerprint: Dict[str, Job] = {}

    def process(self, candidate_jobs: List[Job]) -> List[Job]:
        """
        Recebe uma lista de vagas brutas de coletores diferentes.
        Se uma vaga com a mesma fingerprint já existe, funde suas fontes em vez de duplicar.
        Retorna a lista de vagas únicas.
        """
        for candidate in candidate_jobs:
            if not isinstance(candidate.analysis, dict):
                candidate.analysis = {}
            candidate.analysis["semantic_fingerprint"] = semantic_fingerprint(candidate)
            fp = candidate.fingerprint
            semantic_match = next((
                existing for existing in self.jobs_by_fingerprint.values()
                if self._semantic_duplicate(existing, candidate)
            ), None)
            existing_job = self.jobs_by_fingerprint.get(fp) or semantic_match
            if existing_job:
                existing_job.analysis.setdefault("semantic_fingerprint", semantic_fingerprint(existing_job))
                # Já temos essa vaga! Faz merge das fontes em vez de descartar
                if self._richness(candidate) > self._richness(existing_job):
                    self._merge_richer_fields(existing_job, candidate)
                else:
                    self._merge_publication_date(existing_job, candidate)
                for source_name, source_obj in candidate.sources.items():
                    if source_name == "linkedin" and source_obj.source_job_id != existing_job.sources.get(source_name, source_obj).source_job_id:
                        listings = existing_job.analysis.setdefault("duplicate_listings", [])
                        listing = {
                            "title": candidate.title,
                            "location": candidate.location,
                            "url": source_obj.url,
                            "source_job_id": source_obj.source_job_id,
                        }
                        if listing not in listings:
                            listings.append(listing)
                    existing_job.add_source(
                        source_name=source_name,
                        source_job_id=source_obj.source_job_id,
                        url=source_obj.url,
                    )
            else:
                self.jobs_by_fingerprint[fp] = candidate

        return list(self.jobs_by_fingerprint.values())

    @staticmethod
    def _normalize_identity_text(value: str) -> str:
        value = unicodedata.normalize("NFD", value or "").lower()
        value = "".join(char for char in value if unicodedata.category(char) != "Mn")
        return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", value)).strip()

    @classmethod
    def _semantic_duplicate(cls, left: Job, right: Job) -> bool:
        """Merge near-identical reposts while preserving their separate URLs."""
        company_left = cls._normalize_identity_text(left.company)
        company_right = cls._normalize_identity_text(right.company)
        if not company_left or company_left != company_right:
            return False
        description_left = cls._normalize_identity_text(left.description)
        description_right = cls._normalize_identity_text(right.description)
        if min(len(description_left), len(description_right)) < 500:
            return False
        similarity = SequenceMatcher(None, description_left, description_right, autojunk=False).ratio()
        if similarity < 0.985:
            return False
        title_left = set(cls._normalize_identity_text(left.title).split())
        title_right = set(cls._normalize_identity_text(right.title).split())
        family_terms = {"developer", "desenvolvedor", "engineer", "engenheiro", "ai", "software", "frontend", "backend", "fullstack"}
        return bool((title_left & title_right) & family_terms)

    @staticmethod
    def _richness(job: Job) -> int:
        """Estima a qualidade dos dados sem usar score de compatibilidade."""
        score = min(len(job.description or ""), 2000) // 40
        score += 10 if job.canonical_url or job.resolved_url else 0
        score += 5 if job.location else 0
        score += 5 if job.job_type and job.job_type != "CLT" else 0
        score += min(len(job.technologies), 8) * 3
        score += {"HIGH_EVIDENCE": 15, "MEDIUM_EVIDENCE": 8, "LOW_EVIDENCE": 0}.get(job.evidence_level, 0)
        return score

    @staticmethod
    def _merge_richer_fields(target: Job, source: Job):
        """Atualiza conteúdo rico; as fontes são mescladas separadamente."""
        for field in ("description", "location", "job_type", "salary", "technologies", "canonical_url", "resolved_url"):
            value = getattr(source, field)
            target_value = getattr(target, field)
            target_is_default = not target_value or (
                isinstance(target_value, str)
                and target_value in {"Não informado", "Nao informado", "CLT"}
            )
            if value and (target_is_default or field in {"description", "technologies"}):
                setattr(target, field, value)
        if source.evidence_level == "HIGH_EVIDENCE" or (
            source.evidence_level == "MEDIUM_EVIDENCE" and target.evidence_level == "LOW_EVIDENCE"
        ):
            target.evidence_level = source.evidence_level
        Deduplicator._merge_publication_date(target, source)

    @staticmethod
    def _merge_publication_date(target: Job, source: Job):
        source_date = normalize_published_at(source.published_at)
        target_date = normalize_published_at(target.published_at)
        if source_date and (not target_date or source_date < target_date):
            target.published_at = source_date


def semantic_fingerprint(job: Job) -> str:
    """Stable alert identity for long, near-identical reposts from one employer."""
    company = Deduplicator._normalize_identity_text(job.company)
    description = Deduplicator._normalize_identity_text(job.description)
    if len(description) < 500:
        return job.fingerprint
    role_words = {
        "ai", "developer", "desenvolvedor", "engineer", "engenheiro", "automation",
        "integration", "software", "generative", "applied", "remote", "remoto",
        "home", "office", "junior", "júnior", "pleno", "mid", "level",
    }
    body_words = [word for word in description.split() if word not in role_words]
    material = f"{company}|{' '.join(body_words)}"
    return sha256(material.encode("utf-8")).hexdigest()


def delivery_fingerprint(job: Job) -> str:
    return (job.analysis or {}).get("semantic_fingerprint") or job.fingerprint

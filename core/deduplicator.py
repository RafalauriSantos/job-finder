from typing import Dict, List
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
            fp = candidate.fingerprint
            if fp in self.jobs_by_fingerprint:
                # Já temos essa vaga! Faz merge das fontes em vez de descartar
                existing_job = self.jobs_by_fingerprint[fp]
                if self._richness(candidate) > self._richness(existing_job):
                    self._merge_richer_fields(existing_job, candidate)
                else:
                    self._merge_publication_date(existing_job, candidate)
                for source_name, source_obj in candidate.sources.items():
                    existing_job.add_source(
                        source_name=source_name,
                        source_job_id=source_obj.source_job_id,
                        url=source_obj.url,
                    )
            else:
                self.jobs_by_fingerprint[fp] = candidate

        return list(self.jobs_by_fingerprint.values())

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

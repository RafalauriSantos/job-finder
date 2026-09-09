from typing import Dict, List
from models.job import Job


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
                for source_name, source_obj in candidate.sources.items():
                    existing_job.add_source(
                        source_name=source_name,
                        source_job_id=source_obj.source_job_id,
                        url=source_obj.url,
                    )
            else:
                self.jobs_by_fingerprint[fp] = candidate

        return list(self.jobs_by_fingerprint.values())

from abc import ABC, abstractmethod
from typing import List
from models.job import Job
from dataclasses import dataclass, field


@dataclass
class CollectionResult:
    jobs: List[Job]
    status: str
    issues: list = field(default_factory=list)


def collect_result(collector):
    collector.collection_issues = []
    try:
        jobs = collector.collect()
    except Exception as exc:
        return CollectionResult([], 'FAILED', [type(exc).__name__])
    issues = list(collector.collection_issues)
    for query in getattr(collector, 'query_stats', []):
        status = query.get('status', 'UNKNOWN')
        if status not in ('OK', 'EMPTY', 'SUCCESS'):
            issues.append(status)
    return CollectionResult(jobs, ('PARTIAL' if jobs else 'FAILED') if issues else 'OK', issues)


class BaseCollector(ABC):
    def report_issue(self, issue):
        if not hasattr(self, 'collection_issues'):
            self.collection_issues = []
        self.collection_issues.append(issue)

    """
    Interface abstrata para qualquer coletor de vagas (Gupy, LinkedIn, RSS, etc).
    Garante que a descoberta seja independente da classificação e envio.
    """
    @abstractmethod
    def collect(self) -> List[Job]:
        """Executa a coleta e retorna uma lista de instâncias de Job padronizadas."""
        pass

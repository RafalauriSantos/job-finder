from abc import ABC, abstractmethod
from typing import List
from models.job import Job


class BaseCollector(ABC):
    """
    Interface abstrata para qualquer coletor de vagas (Gupy, LinkedIn, RSS, etc).
    Garante que a descoberta seja independente da classificação e envio.
    """
    @abstractmethod
    def collect(self) -> List[Job]:
        """Executa a coleta e retorna uma lista de instâncias de Job padronizadas."""
        pass

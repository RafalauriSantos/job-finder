from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import hashlib
import json


@dataclass
class JobSource:
    source_name: str       # "gupy", "linkedin", "google_news", etc.
    source_job_id: str     # ID original na plataforma
    url: str               # Link direto para a candidatura
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class Job:
    title: str
    company: str
    workplace_type: str                  # "remote", "hybrid", "on-site", "unknown"
    location: str = ""
    description: str = ""
    job_type: str = "CLT"                # "CLT", "PJ", "Estágio", "Trainee"
    salary: str = "Não informado"
    technologies: List[str] = field(default_factory=list)
    seniority: str = "junior"            # "intern", "junior", "mid", "senior", "unknown"
    match_score: int = 0                 # 0 a 100
    match_reasons: List[str] = field(default_factory=list)
    sources: Dict[str, JobSource] = field(default_factory=dict)
    first_seen: str = field(default_factory=lambda: datetime.now().isoformat())

    def add_source(self, source_name: str, source_job_id: str, url: str):
        """Associa uma nova fonte a esta vaga (suporte a vaga multi-fonte)."""
        if source_name not in self.sources:
            self.sources[source_name] = JobSource(
                source_name=source_name,
                source_job_id=str(source_job_id),
                url=url,
            )

    @property
    def primary_url(self) -> str:
        """Retorna o melhor link de candidatura disponível."""
        # Preferência: link oficial direto
        for src in ["gupy", "linkedin", "career_page"]:
            if src in self.sources and self.sources[src].url:
                return self.sources[src].url
        if self.sources:
            return next(iter(self.sources.values())).url
        return ""

    @property
    def fingerprint(self) -> str:
        """
        Gera uma assinatura única robusta para evitar duplicações.
        Combina: empresa normalizada + título normalizado + modalidade + 
        os primeiros 200 caracteres da descrição limpa (quando disponível).
        """
        norm_company = self.company.strip().lower()
        norm_title = self.title.strip().lower()
        norm_workplace = self.workplace_type.strip().lower()
        
        # Pega amostra da descrição para diferenciar vagas com mesmo título na mesma empresa
        desc_sample = " ".join(self.description.lower().split()[:30]) if self.description else ""

        payload = f"{norm_company}|{norm_title}|{norm_workplace}|{desc_sample}"
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "company": self.company,
            "workplace_type": self.workplace_type,
            "location": self.location,
            "description": self.description,
            "job_type": self.job_type,
            "salary": self.salary,
            "technologies": self.technologies,
            "seniority": self.seniority,
            "match_score": self.match_score,
            "match_reasons": self.match_reasons,
            "primary_url": self.primary_url,
            "sources": {
                name: {
                    "source_name": s.source_name,
                    "source_job_id": s.source_job_id,
                    "url": s.url,
                    "first_seen": s.first_seen,
                }
                for name, s in self.sources.items()
            },
            "fingerprint": self.fingerprint,
            "first_seen": self.first_seen,
        }

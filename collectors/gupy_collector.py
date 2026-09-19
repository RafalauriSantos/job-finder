import json
from typing import List, Dict, Any
import requests
from collectors.base import BaseCollector
from models.job import Job
from core.normalizer import normalize_title, normalize_workplace, extract_technologies

GUPY_MCP_URL = "https://candidates.mcp.api.gupy.io/mcp"

JOB_TYPE_TRANSLATIONS = {
    "vacancy_type_effective": "Efetivo (CLT)",
    "vacancy_type_internship": "Estágio",
    "vacancy_type_trainee": "Trainee",
    "vacancy_type_apprentice": "Jovem Aprendiz",
    "vacancy_legal_entity": "Pessoa Jurídica (PJ)",
    "vacancy_type_temporary": "Temporário",
    "vacancy_type_freelancer": "Freelancer",
    "vacancy_type_outsource": "Terceirizado",
    "vacancy_type_talent_pool": "Banco de Talentos",
}


class GupyCollector(BaseCollector):
    def __init__(self, http_session: requests.Session, queries: List[Dict[str, Any]]):
        self.http = http_session
        self.queries = queries
        self.query_stats: List[Dict[str, Any]] = []
        self._last_query_status = "UNKNOWN"

    def _query_api(self, args: Dict[str, Any]) -> List[Dict[str, Any]]:
        api_args = {key: value for key, value in args.items() if key != "query_id"}
        body = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {
                "name": "search_jobs",
                "arguments": api_args,
            },
        }
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        try:
            resp = self.http.post(GUPY_MCP_URL, json=body, headers=headers, timeout=15)
            if resp.status_code != 200:
                self._last_query_status = f"HTTP_{resp.status_code}"
                return []

            resp.encoding = "utf-8"
            for line in resp.text.splitlines():
                if line.startswith("data:"):
                    payload = json.loads(line[5:].strip())
                    content_text = payload.get("result", {}).get("content", [{}])[0].get("text", "{}")
                    parsed = json.loads(content_text)
                    self._last_query_status = "OK"
                    return parsed.get("data", {}).get("data", [])
        except Exception as e:
            self._last_query_status = "ERROR"
            print(f"[ERRO GupyCollector] {e}")
        self._last_query_status = "EMPTY"
        return []

    def collect(self) -> List[Job]:
        discovered_jobs: List[Job] = []

        for q_args in self.queries:
            raw_jobs = self._query_api(q_args)
            self.query_stats.append({
                "parameters": dict(q_args),
                "results": len(raw_jobs),
                "status": self._last_query_status,
            })
            for raw in raw_jobs:
                job_id = str(raw.get("id"))
                title = normalize_title(raw.get("name", ""))
                company = raw.get("careerPageName", "").strip() or "Empresa Gupy"
                city = raw.get("city", "")
                state = raw.get("state", "")
                loc = f"{city}, {state}".strip(", ")
                raw_workplace = raw.get("workplaceType") or ""
                workplace = normalize_workplace(raw_workplace, location_text=loc, title_text=title)
                raw_type = raw.get("type", "")
                job_type = JOB_TYPE_TRANSLATIONS.get(raw_type, raw_type or "CLT")
                salary_label = raw.get("salary", {}).get("label", "Não informado")
                description = raw.get("description", "")
                
                # URL canônica
                career_page = raw.get("careerPageName", "").strip().lower()
                canonical_url = raw.get("jobUrl")
                if not canonical_url:
                    canonical_url = f"https://{career_page}.gupy.io/jobs/{job_id}" if career_page else "https://gupy.io"

                techs = extract_technologies(f"{title} {description}")

                job = Job(
                    title=title,
                    company=company,
                    workplace_type=workplace,
                    location=loc,
                    description=description,
                    job_type=job_type,
                    salary=salary_label,
                    technologies=techs,
                    published_at=raw.get("publishedAt") or raw.get("createdAt") or "",
                )
                job.add_source("gupy", job_id, canonical_url)
                discovered_jobs.append(job)

        return discovered_jobs

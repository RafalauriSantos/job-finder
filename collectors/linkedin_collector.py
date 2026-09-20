import re
import urllib.parse
from html import unescape
from typing import List, Dict, Any
import requests
from collectors.base import BaseCollector
from models.job import Job
from core.normalizer import normalize_title, normalize_workplace, extract_technologies
from core.url_resolver import sanitize_canonical_url


class LinkedInCollector(BaseCollector):
    def __init__(self, http_session: requests.Session, searches: List[Dict[str, Any]]):
        self.http = http_session
        self.searches = searches
        self.query_stats: List[Dict[str, Any]] = []

    def _enrich_job(self, job: Job, headers: Dict[str, str]) -> bool:
        """Tenta obter descrição pública; falhas mantêm o cartão original."""
        try:
            response = self.http.get(job.sources["linkedin"].url, headers=headers, timeout=6)
            if response.status_code != 200:
                return False
            html = response.text
            description_match = re.search(
                r'<div[^>]+class="[^"]*(?:show-more-less-html__markup|description__text)[^"]*"[^>]*>(.*?)</div>',
                html,
                re.DOTALL | re.IGNORECASE,
            )
            if not description_match:
                description_match = re.search(
                    r'<meta[^>]+name="description"[^>]+content="([^"]+)"',
                    html,
                    re.IGNORECASE,
                )
            if not description_match:
                return False
            description = re.sub(r"<[^>]+>", " ", description_match.group(1))
            description = re.sub(r"\s+", " ", unescape(description)).strip()
            if len(description) < 40:
                return False
            job.description = description
            job.technologies = extract_technologies(f"{job.title} {description}")
            job.evidence_level = "MEDIUM_EVIDENCE"
            final_url = getattr(response, "url", "") or ""
            if final_url and final_url != job.sources["linkedin"].url:
                job.resolved_url = final_url
                job.canonical_url = sanitize_canonical_url(final_url)
            return True
        except Exception:
            return False

    def _query_search(self, search_cfg: Dict[str, Any]) -> List[Job]:
        keywords = search_cfg.get("query") or search_cfg.get("keywords", "Desenvolvedor Junior")
        if isinstance(keywords, (list, tuple)):
            keywords = " OR ".join(str(value) for value in keywords if value)
        keywords = str(keywords).strip() or "Desenvolvedor Junior"
        recent_hours = search_cfg.get("published_within_hours")
        time_range = search_cfg.get("time_range")
        if not time_range and recent_hours is not None:
            time_range = f"r{int(recent_hours) * 3600}"
        time_range = time_range or "r3600"
        geo_id = search_cfg.get("geo_id", "106057199")
        max_pages = max(1, int(search_cfg.get("max_pages", 1)))

        base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        base_params = {
            "keywords": keywords,
            "f_TPR": time_range,
            "geoId": geo_id,
        }
        for key in ("experience", "workplace_type", "job_type", "function", "industry"):
            value = search_cfg.get(key)
            if value:
                base_params[key] = value
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        jobs = []
        seen_ids = set()
        stats = {
            "keywords": keywords,
            "time_range": time_range,
            "seniority": search_cfg.get("seniority"),
            "published_within_hours": recent_hours,
            "geo_id": geo_id,
            "max_pages": max_pages,
            "pages": 0,
            "cards": 0,
            "parsed_jobs": 0,
            "status": "OK",
            "enrichment_attempts": 0,
            "enrichment_successes": 0,
        }
        try:
            for page in range(max_pages):
                stats["pages"] += 1
                params = {**base_params, "start": page * 25}
                query_str = urllib.parse.urlencode(params)
                target_url = f"{base_url}?{query_str}"
                resp = self.http.get(target_url, headers=headers, timeout=15)
                if resp.status_code != 200:
                    stats["status"] = f"HTTP_{resp.status_code}"
                    print(f"[ALERTA LinkedInCollector] Requisição falhou para '{keywords}' com status {resp.status_code}.")
                    break

                resp.encoding = "utf-8"
                cards = re.findall(r'<li[^>]*>(.*?)</li>', resp.text, re.DOTALL)
                stats["cards"] += len(cards)
                if not cards:
                    break

                page_new_jobs = 0
                for card in cards:
                    urn_match = re.search(r'data-entity-urn=\"urn:li:jobPosting:(\d+)\"', card)
                    title_match = re.search(r'<h3[^>]*class=\"[^\"]*base-search-card__title[^\"]*\"[^>]*>\s*([^<]+)\s*</h3>', card)
                    company_match = re.search(r'<h4[^>]*class=\"[^\"]*base-search-card__subtitle[^\"]*\"[^>]*>.*?<a[^>]*>\s*([^<]+)\s*</a>', card, re.DOTALL)
                    link_match = re.search(r'<a[^>]*class=\"[^\"]*base-card__full-link[^\"]*\"[^>]*href=\"([^\"]+)\"', card)
                    loc_match = re.search(r'<span[^>]*class=\"[^\"]*job-search-card__location[^\"]*\"[^>]*>\s*([^<]+)\s*</span>', card)

                    if not title_match or not link_match:
                        continue

                    raw_title = title_match.group(1).strip()
                    title = normalize_title(raw_title)
                    company = company_match.group(1).strip() if company_match else "LinkedIn"
                    raw_link = link_match.group(1).split("?")[0]
                    job_id = urn_match.group(1) if urn_match else raw_link.split("-")[-1]
                    if job_id in seen_ids:
                        continue
                    seen_ids.add(job_id)
                    page_new_jobs += 1
                    location = loc_match.group(1).strip() if loc_match else "Brasil"

                    workplace = normalize_workplace("", location_text=location, title_text=title)
                    techs = extract_technologies(title)

                    job = Job(
                        title=title,
                        company=company,
                        workplace_type=workplace,
                        location=location,
                        technologies=techs,
                    )
                    job.add_source("linkedin", job_id, raw_link)
                    jobs.append(job)
                if page_new_jobs == 0:
                    break

            # Enrich all cards up to a bounded per-query budget. A limit of one
            # allowed shallow LinkedIn cards to reach scoring without evidence.
            enrichment_limit = max(0, int(search_cfg.get("detail_enrichment_limit", 8)))
            if search_cfg.get("enrich_details", False):
                for job in jobs[:enrichment_limit]:
                    stats["enrichment_attempts"] += 1
                    if self._enrich_job(job, headers):
                        stats["enrichment_successes"] += 1

        except Exception as e:
            stats["status"] = "ERROR"
            stats["error"] = str(e)
            print(f"[ERRO LinkedInCollector] {e}")

        stats["parsed_jobs"] = len(jobs)
        self.query_stats.append(stats)
        return jobs

    def collect(self) -> List[Job]:
        discovered: List[Job] = []
        for s in self.searches:
            jobs = self._query_search(s)
            discovered.extend(jobs)
        return discovered

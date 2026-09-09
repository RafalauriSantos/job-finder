import re
import urllib.parse
from typing import List, Dict, Any
import requests
from collectors.base import BaseCollector
from models.job import Job
from core.normalizer import normalize_title, normalize_workplace, extract_technologies


class LinkedInCollector(BaseCollector):
    def __init__(self, http_session: requests.Session, searches: List[Dict[str, Any]]):
        self.http = http_session
        self.searches = searches

    def _query_search(self, search_cfg: Dict[str, Any]) -> List[Job]:
        keywords = search_cfg.get("keywords", "Desenvolvedor Junior")
        time_range = search_cfg.get("time_range", "r3600")
        geo_id = search_cfg.get("geo_id", "106057199")

        base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
        params = {
            "keywords": keywords,
            "f_TPR": time_range,
            "geoId": geo_id,
            "start": 0,
        }
        query_str = urllib.parse.urlencode(params)
        target_url = f"{base_url}?{query_str}"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
        }

        jobs = []
        try:
            resp = self.http.get(target_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                return []

            resp.encoding = "utf-8"
            cards = re.findall(r'<li[^>]*>(.*?)</li>', resp.text, re.DOTALL)

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

        except Exception as e:
            print(f"[ERRO LinkedInCollector] {e}")

        return jobs

    def collect(self) -> List[Job]:
        discovered: List[Job] = []
        for s in self.searches:
            jobs = self._query_search(s)
            discovered.extend(jobs)
        return discovered

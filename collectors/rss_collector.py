import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any
import requests
from collectors.base import BaseCollector
from models.job import Job
from core.normalizer import normalize_title


class RssCollector(BaseCollector):
    """Coletor de vagas via feeds RSS 2.0 e Atom (Google News, Google Alerts, etc)."""

    def __init__(self, http_session: requests.Session, configs: List[Dict[str, Any]]):
        self.http = http_session
        self.configs = configs

    def _parse_feed(self, feed_url: str) -> List[Dict[str, str]]:
        """Faz fetch e parse do XML do feed, retorna lista de {id, title, link}."""
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        try:
            resp = self.http.get(feed_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"[ALERTA RssCollector] Feed retornou status {resp.status_code}: {feed_url[:80]}")
                return []

            root = ET.fromstring(resp.content)
            items = []

            # 1. Formato Atom (Google Alerts)
            ns = {"atom": "http://www.w3.org/2005/Atom"}
            entries = root.findall("atom:entry", ns)
            if entries:
                for entry in entries:
                    item_id = entry.findtext("atom:id", default="", namespaces=ns)
                    title = entry.findtext("atom:title", default="", namespaces=ns)
                    link_elem = entry.find("atom:link", ns)
                    link = link_elem.attrib.get("href", "") if link_elem is not None else ""
                    title_clean = re.sub(r"<[^>]+>", "", title).strip()
                    items.append({"id": item_id or link, "title": title_clean, "link": link})
                return items

            # 2. Formato RSS 2.0 (Google News)
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item"):
                    guid = item.findtext("guid") or item.findtext("link") or ""
                    title = item.findtext("title", default="")
                    link = item.findtext("link", default="")
                    title_clean = re.sub(r"<[^>]+>", "", title).strip()
                    items.append({"id": guid or link, "title": title_clean, "link": link})
                return items

        except Exception as e:
            print(f"[ERRO RssCollector] {e}")
        return []

    def _matches_filters(self, title_lower: str, config: Dict[str, Any]) -> bool:
        """Aplica keyword/exclude_keyword filters do config ao título do item RSS."""
        keywords = [k.lower() for k in config.get("keywords", [])]
        exclude = [k.lower() for k in config.get("exclude_keywords", [])]

        if exclude:
            if any(kw in title_lower for kw in exclude):
                return False

        if keywords:
            if not any(kw in title_lower for kw in keywords):
                return False

        return True

    def collect(self) -> List[Job]:
        discovered: List[Job] = []

        for cfg in self.configs:
            feed_url = cfg.get("url", "")
            company = cfg.get("company", cfg.get("description", "RSS"))
            if not feed_url:
                continue

            raw_items = self._parse_feed(feed_url)

            for item in raw_items:
                title_clean = normalize_title(item["title"])
                title_lower = title_clean.lower()

                if not self._matches_filters(title_lower, cfg):
                    continue

                job = Job(
                    title=title_clean,
                    company=company,
                    workplace_type="unknown",
                    location="",
                    description="",
                    job_type="Vaga Externa",
                    salary="Nao informado",
                )
                job.add_source("rss", str(item["id"]), item["link"])
                discovered.append(job)

        return discovered

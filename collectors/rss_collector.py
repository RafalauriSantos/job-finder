import re
import email.utils
from datetime import datetime, timezone, timedelta
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional, Tuple
import requests
from collectors.base import BaseCollector
from models.job import Job
from core.normalizer import normalize_title
from core.url_resolver import resolve_url_tripartite, calculate_noise_score


def parse_feed_datetime(date_str: str) -> Optional[datetime]:
    """
    Faz parse robusto de timestamps de feeds (RFC-822/1123 e ISO-8601),
    convertendo sempre para UTC.
    """
    if not date_str:
        return None
    date_str = date_str.strip()

    # 1. Tenta RFC-822 / RFC-1123 (RSS 2.0 padrão)
    try:
        parsed_tuple = email.utils.parsedate_to_datetime(date_str)
        if parsed_tuple:
            return parsed_tuple.astimezone(timezone.utc)
    except Exception:
        pass

    # 2. Tenta ISO-8601 (Atom padrão)
    try:
        clean_iso = date_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_iso)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass

    return None


def classify_freshness(dt: Optional[datetime], max_age_hours: int = 72) -> Tuple[str, str]:
    """
    Classifica recência da vaga sem assunções destrutivas.
    Retorna (status, reason): FRESH | STALE | UNKNOWN
    """
    if dt is None:
        return "UNKNOWN", "Data ausente ou em formato não reconhecido"

    now_utc = datetime.now(timezone.utc)
    age = now_utc - dt

    if age < timedelta(0):
        # Data no futuro por clock skew
        return "FRESH", "Timestamp recente (clock skew leve)"

    if age <= timedelta(hours=max_age_hours):
        return "FRESH", f"Vaga recente publicada há {int(age.total_seconds() // 3600)}h"

    return "STALE", f"Vaga com idade superior a {max_age_hours}h ({int(age.total_seconds() // 3600)}h)"


class RssCollector(BaseCollector):
    """Coletor de vagas via feeds RSS 2.0 e Atom com suporte à SPEC-008."""

    def __init__(self, http_session: requests.Session, configs: List[Dict[str, Any]], resolve_urls: bool = False):
        self.http = http_session
        self.configs = configs
        self.resolve_urls = resolve_urls

    def _parse_feed(self, feed_url: str) -> List[Dict[str, Any]]:
        """Faz fetch e parse do XML do feed, retorna lista de {id, title, link, pub_date}."""
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
                    raw_date = entry.findtext("atom:updated", default="", namespaces=ns) or entry.findtext("atom:published", default="", namespaces=ns)
                    title_clean = re.sub(r"<[^>]+>", "", title).strip()
                    items.append({
                        "id": item_id or link,
                        "title": title_clean,
                        "link": link,
                        "raw_date": raw_date
                    })
                return items

            # 2. Formato RSS 2.0 (Google News)
            channel = root.find("channel")
            if channel is not None:
                for item in channel.findall("item"):
                    guid = item.findtext("guid") or item.findtext("link") or ""
                    title = item.findtext("title", default="")
                    link = item.findtext("link", default="")
                    raw_date = item.findtext("pubDate", default="")
                    title_clean = re.sub(r"<[^>]+>", "", title).strip()
                    items.append({
                        "id": guid or link,
                        "title": title_clean,
                        "link": link,
                        "raw_date": raw_date
                    })
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

                # Filtro anti-ruído de páginas agregadoras (SPEC-008)
                noise_score, _ = calculate_noise_score(title_clean, item["link"])
                if noise_score >= 2:
                    # Descarte de páginas de contagem de vagas agregadas
                    continue

                if not self._matches_filters(title_lower, cfg):
                    continue

                # Parse temporal e filtro de recência (SPEC-008)
                dt = parse_feed_datetime(item.get("raw_date", ""))
                freshness, _ = classify_freshness(dt, max_age_hours=cfg.get("max_age_hours", 72))
                if freshness == "STALE":
                    # Descarta se tiver certeza comprovada de que a vaga tem mais de 72h
                    continue

                raw_link = item["link"]
                resolved_link = raw_link
                canonical_link = raw_link

                if self.resolve_urls and "news.google.com" in raw_link:
                    _, resolved_link, canonical_link, _ = resolve_url_tripartite(raw_link, self.http)

                job = Job(
                    title=title_clean,
                    company=company,
                    workplace_type="unknown",
                    location="",
                    description="",
                    job_type="Vaga Externa",
                    salary="Nao informado",
                    raw_url=raw_link,
                    resolved_url=resolved_link,
                    canonical_url=canonical_link,
                    evidence_level="LOW_EVIDENCE",  # RSS nativo tem metadado raso
                    published_at=dt.isoformat() if dt else "",
                )
                job.add_source("rss", str(item["id"]), canonical_link or raw_link)
                discovered.append(job)

        return discovered

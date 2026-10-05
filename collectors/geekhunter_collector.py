"""Public GeekHunter collector using the public listing and job pages."""
import html
import re
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import urljoin, urlsplit

import requests

from collectors.base import BaseCollector
from models.job import Job
from core.normalizer import normalize_title, normalize_workplace, extract_technologies, has_explicit_remote_signal


class GeekHunterCollector(BaseCollector):
    BASE_URL = 'https://www.geekhunter.com/pt/vagas'

    def __init__(self, http_session: requests.Session, keywords: Optional[List[str]] = None,
                 exclude_keywords: Optional[List[str]] = None, max_jobs: int = 30):
        self.http = http_session
        self.keywords = [str(x).lower() for x in (keywords or [])]
        self.exclude_keywords = [str(x).lower() for x in (exclude_keywords or [])]
        self.max_jobs = max(1, int(max_jobs))
        self.collection_attempts = []

    @staticmethod
    def _text(value):
        return re.sub(r'\s+', ' ', html.unescape(re.sub(r'<[^>]+>', ' ', value or ''))).strip()

    @staticmethod
    def _meta(page, name):
        match = re.search(r'<meta[^>]+(?:name|property)=["\']' + re.escape(name) +
                          r'["\'][^>]+content=["\']([^"\']+)', page, re.I)
        return html.unescape(match.group(1)).strip() if match else ''

    def _matches(self, text):
        lower = text.lower()
        return (not self.keywords or any(k in lower for k in self.keywords)) and not any(
            k in lower for k in self.exclude_keywords)

    @staticmethod
    def _is_allowed_url(url):
        parsed = urlsplit(url or '')
        host = (parsed.hostname or '').lower().rstrip('.')
        return parsed.scheme == 'https' and (host == 'geekhunter.com' or host.endswith('.geekhunter.com'))

    def collect(self):
        started = datetime.now(timezone.utc).isoformat()
        try:
            listing = self.http.get(self.BASE_URL, headers={'User-Agent': 'WorkHunter/1.0'}, timeout=20)
            if listing.status_code != 200:
                self.record_attempt('geekhunter', 'listing', started, http_status=listing.status_code,
                                    error_type=f'HTTP_{listing.status_code}')
                return []
            links = list(dict.fromkeys(urljoin(listing.url, value) for value in re.findall(
                r'href=["\']([^"\']+/jobs/[^"\']+)', listing.text, re.I)))[:self.max_jobs]
            self.record_attempt('geekhunter', 'listing', started, http_status=listing.status_code,
                                result_count=len(links), native_ids=links)
        except Exception as exc:
            self.record_attempt('geekhunter', 'listing', started, error_type=type(exc).__name__, reason=str(exc))
            self.report_issue(type(exc).__name__)
            return []

        jobs = []
        for url in links:
            detail_started = datetime.now(timezone.utc).isoformat()
            try:
                response = self.http.get(url, headers={'User-Agent': 'WorkHunter/1.0'}, timeout=20)
                if not self._is_allowed_url(getattr(response, 'url', url)):
                    self.record_attempt('geekhunter', 'detail', detail_started, query={'url': url},
                                        error_type='UNTRUSTED_REDIRECT')
                    continue
                if response.status_code != 200 or '/not-found' in response.url:
                    self.record_attempt('geekhunter', 'detail', detail_started, query={'url': url},
                                        http_status=response.status_code, error_type='NOT_FOUND' if '/not-found' in response.url else f'HTTP_{response.status_code}')
                    continue
                title_raw = self._meta(response.text, 'og:title') or re.search(
                    r'<title[^>]*>(.*?)</title>', response.text, re.I | re.S).group(1)
                title = normalize_title(self._text(title_raw).split(' em ')[0])
                meta_description = self._meta(response.text, 'description') or self._meta(response.text, 'og:description')
                page_text = self._text(response.text)
                combined = f'{title} {meta_description} {page_text}'
                if not self._matches(combined):
                    continue
                company = self._text(title_raw).split(' em ', 1)[1] if ' em ' in self._text(title_raw) else 'GeekHunter'
                location_match = re.search(r'([A-ZÁÀÂÃÉÊÍÓÔÕÚÇ][^|]{2,40}(?:,| -) [A-Z]{2})', page_text)
                location = location_match.group(1).strip() if location_match else 'Brasil'
                location = re.sub(r'^(?:Address|address)"?\s*:\s*"?', '', location).split('"')[0].strip()
                workplace = normalize_workplace('', location, combined)
                if has_explicit_remote_signal(combined):
                    workplace = 'remote'
                job = Job(title=title, company=company, workplace_type=workplace, location=location,
                          description=meta_description or page_text[:12000], technologies=extract_technologies(combined),
                          raw_url=url, resolved_url=response.url, canonical_url=response.url)
                native_id = urlsplit(response.url).path.rstrip('/').split('/')[-1]
                job.add_source('geekhunter', native_id, response.url)
                jobs.append(job)
                self.record_attempt('geekhunter', 'detail', detail_started, query={'url': url},
                                    http_status=response.status_code, result_count=1, native_ids=[native_id])
            except Exception as exc:
                self.record_attempt('geekhunter', 'detail', detail_started, query={'url': url},
                                    error_type=type(exc).__name__, reason=str(exc))
                self.report_issue(type(exc).__name__)
        return jobs

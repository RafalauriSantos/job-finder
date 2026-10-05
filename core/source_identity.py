"""Stable source identity and URL normalization for collection diagnostics."""
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

TRACKING_KEYS = {'trk', 'trackingid', 'lipi', 'refid', 'position', 'currentjobid', 'jobboardsource'}


@dataclass(frozen=True)
class SourceIdentity:
    source: str
    native_id: str | None
    normalized_url: str
    identity_status: str


def normalize_job_url(url: str) -> str:
    parts = urlsplit((url or '').strip())
    query = [(key, value) for key, value in parse_qsl(parts.query, keep_blank_values=True)
             if not key.lower().startswith('utm_') and key.lower() not in TRACKING_KEYS]
    host = parts.netloc.lower()
    path = re.sub(r'/+', '/', parts.path).rstrip('/') or '/'
    return urlunsplit((parts.scheme.lower(), host, path, urlencode(sorted(query)), ''))


def extract_source_identity(url: str) -> SourceIdentity:
    original_parts = urlsplit((url or '').strip())
    normalized = normalize_job_url(url)
    parts = urlsplit(normalized)
    host = parts.netloc.lower()
    path = parts.path
    source = 'unknown'
    native_id = None
    if 'linkedin.com' in host:
        source = 'linkedin'
        match = re.search(r'/jobs/(?:view|job)/([0-9]+)', path)
        native_id = match.group(1) if match else next(
            (value for key, value in parse_qsl(original_parts.query) if key.lower() == 'currentjobid' and value.isdigit()), None)
    elif 'gupy.io' in host:
        source = 'gupy'
        match = re.search(r'/jobs?/([^/]+)', path)
        native_id = match.group(1) if match else None
    elif host == 'github.com' or host.endswith('.github.com'):
        source = 'github'
        match = re.search(r'/([^/]+/[^/]+)/issues/([0-9]+)', path)
        native_id = f'{match.group(1)}#{match.group(2)}' if match else None
    elif 'trampos.co' in host:
        source = 'trampos'
        match = re.search(r'/oportunidades/([^/]+)', path)
        native_id = match.group(1) if match else None
    return SourceIdentity(source, native_id, normalized, 'identity_resolved' if native_id else 'identity_unresolved')

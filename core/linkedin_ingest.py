"""Safe local ingestion for LinkedIn browser/extension captures.

This module never logs credentials or browser data. It only accepts content that
the user or a local browser integration explicitly captured.
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass
from datetime import datetime, timezone
from urllib.parse import urlsplit, urlunsplit


JOB_WORDS = re.compile(r"\b(vaga|vagas|contratando|oportunidade|hiring|recrut)\b", re.I)
TECH_WORDS = re.compile(r"\b(desenvolvedor|developer|engenheiro|engineer|dev|api|javascript|python|java|frontend|backend|full.?stack|integraç)\b", re.I)
POST_TIME = re.compile(r"\b\d+\s*(?:min|h|d|sem|mês|mes|ano)\s*•", re.I)


def extract_post_body(text: str) -> str:
    """Discard feed heading and author bio before screening a captured post."""
    match = POST_TIME.search(text or "")
    if not match:
        return ""
    body = (text or "")[match.end():].strip()
    return re.sub(r"^Seguir\s*", "", body, flags=re.I).strip()


def normalize_url(url: str) -> str:
    parts = urlsplit((url or "").strip())
    if not parts.scheme or not parts.netloc:
        return ""
    host = parts.hostname.lower() if parts.hostname else ""
    path = parts.path.rstrip("/") or "/"
    return urlunsplit((parts.scheme.lower(), host, path, "", ""))


def content_fingerprint(url: str, text: str, author: str = "") -> str:
    normalized = normalize_url(url)
    if normalized and re.search(r"/(?:feed/update/|posts/|jobs/view/)", normalized):
        identity = normalized
    else:
        # The feed often exposes no permalink. Whitespace, author labels and
        # comment counters can change while the same post remains visible.
        identity = re.sub(r"\W+", "", (text or "").casefold())[:500]
    return hashlib.sha256(identity.encode("utf-8")).hexdigest()


def looks_like_opportunity(text: str) -> bool:
    text = text or ""
    return bool(JOB_WORDS.search(text) and TECH_WORDS.search(text))


@dataclass(frozen=True)
class CapturedOpportunity:
    url: str
    text: str
    author: str = ""
    collected_at: str = ""
    source_type: str = "post"

    @property
    def fingerprint(self) -> str:
        return content_fingerprint(self.url, self.text, self.author)

    def payload(self) -> dict:
        return {
            "source": "linkedin",
            "source_type": self.source_type,
            "url": normalize_url(self.url),
            "text": self.text.strip(),
            "author": self.author.strip(),
            "collected_at": self.collected_at or datetime.now(timezone.utc).isoformat(),
            "fingerprint": self.fingerprint,
        }


class RateController:
    """Local safety governor for optional browser collection."""
    def __init__(self, max_actions_per_hour=12, min_interval_seconds=120):
        self.max_actions_per_hour = int(max_actions_per_hour)
        self.min_interval_seconds = int(min_interval_seconds)
        self._actions = []
        self._paused_until = 0.0

    def allow(self, now: float) -> bool:
        self._actions = [t for t in self._actions if now - t < 3600]
        return now >= self._paused_until and len(self._actions) < self.max_actions_per_hour and (
            not self._actions or now - self._actions[-1] >= self.min_interval_seconds
        )

    def record(self, now: float):
        self._actions.append(now)

    def pause(self, now: float, seconds: int = 3600):
        self._paused_until = max(self._paused_until, now + seconds)

    @property
    def state(self):
        return "PAUSED" if self._paused_until else "HEALTHY"

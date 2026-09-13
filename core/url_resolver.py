import re
from typing import Tuple, List
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse
import requests


TRACKING_PARAMS = {
    "utm_source", "utm_medium", "utm_campaign", "utm_term", "utm_content",
    "gclid", "fbclid", "msclkid", "ref", "source", "ref_src", "trk"
}


def sanitize_canonical_url(url: str) -> str:
    """
    Remove parâmetros de tracking e fragmentos da URL, gerando uma URL canônica limpa.
    """
    if not url:
        return ""
    parsed = urlparse(url)
    clean_query = [
        (k, v) for k, v in parse_qsl(parsed.query)
        if k.lower() not in TRACKING_PARAMS
    ]
    new_query = urlencode(clean_query)
    clean_parts = (
        parsed.scheme,
        parsed.netloc,
        parsed.path.rstrip("/"),
        parsed.params,
        new_query,
        ""  # fragment removido
    )
    return urlunparse(clean_parts)


def calculate_noise_score(title: str, url: str = "") -> Tuple[int, List[str]]:
    """
    Calcula pontuação de ruído anti-agregador (SPEC-008).
    Detecta páginas de busca agregada, estatísticas salariais e listagens de SEO.
    """
    score = 0
    reasons = []

    import unicodedata
    clean_title = "".join(c for c in unicodedata.normalize("NFD", title.lower()) if unicodedata.category(c) != "Mn")
    url_lower = url.lower()

    # 1. Padrão de contagem de vagas ("285 vagas de...", "14 oportunidades...")
    if re.search(r"\b\d+\s+(?:vagas?|oportunidades?|jobs?)\b", clean_title):
        score += 2
        reasons.append("Padrão de contagem de vagas agregadas no título (+2)")

    # 2. Estatísticas salariais ("salários de desenvolvedor...", "faixa salarial")
    if re.search(r"\bsalarios?\s+de\b|\bfaixa\s+salarial\b", clean_title) or "/salarios/" in url_lower:
        score += 1
        reasons.append("Página de pesquisa salarial / estatística (+1)")

    # 3. Páginas de avaliação / diretório de empresas
    if re.search(r"\bavaliacoes?\s+da\s+empresa\b|\btrabalhar\s+na\b", clean_title) or "/avaliacoes/" in url_lower:
        score += 1
        reasons.append("Página de diretório ou avaliação de empresa (+1)")

    # 4. URLs explícitas de busca / agregação
    if any(pattern in url_lower for pattern in ["srch_", "/busca", "/jobs?q=", "search?q="]):
        score += 1
        reasons.append("URL com padrão de busca/listagem agregada (+1)")

    return score, reasons


def resolve_url_tripartite(raw_url: str, session: requests.Session, timeout: int = 6) -> Tuple[str, str, str, str]:
    """
    Resolve URLs intermediárias (ex: Google News) para obter a URL de destino real.
    Retorna (raw_url, resolved_url, canonical_url, status)
    Status: "RESOLVED", "URL_UNRESOLVED"
    """
    if not raw_url:
        return "", "", "", "URL_UNRESOLVED"

    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

    # Tentativa 1: HEAD com allow_redirects
    try:
        resp = session.head(raw_url, headers=headers, allow_redirects=True, timeout=timeout)
        if resp.url and resp.url != raw_url:
            resolved = resp.url
            canonical = sanitize_canonical_url(resolved)
            return raw_url, resolved, canonical, "RESOLVED"
        elif resp.status_code < 400:
            canonical = sanitize_canonical_url(resp.url or raw_url)
            return raw_url, resp.url or raw_url, canonical, "RESOLVED"
    except Exception:
        pass

    # Tentativa 2: GET com stream=True (não baixa o corpo todo)
    try:
        resp = session.get(raw_url, headers=headers, stream=True, allow_redirects=True, timeout=timeout)
        resolved = resp.url or raw_url
        canonical = sanitize_canonical_url(resolved)
        resp.close()
        return raw_url, resolved, canonical, "RESOLVED"
    except Exception:
        pass

    # Fallback caso falhe: preserva raw e marca UNRESOLVED
    return raw_url, raw_url, sanitize_canonical_url(raw_url), "URL_UNRESOLVED"

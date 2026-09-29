"""Expansão determinística de consultas configuradas por fonte."""

from copy import deepcopy
from hashlib import sha1
from typing import Any, Dict, List


def unique_searches(searches: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Deduplicate by the actual request parameters, preserving distinct queries."""
    unique: List[Dict[str, Any]] = []
    seen = set()
    for search in searches:
        key = (
            str(search.get("query") or search.get("keywords") or "").strip().casefold(),
            search.get("time_range") or search.get("published_within_hours"),
            str(search.get("geo_id") or "106057199"),
            tuple(sorted((name, str(search.get(name))) for name in (
                "experience", "workplace_type", "job_type", "function", "industry"
            ) if search.get(name))),
        )
        if key in seen:
            continue
        seen.add(key)
        unique.append(search)
    return unique


def rotate_searches(searches: List[Dict[str, Any]], limit: int, slot: int) -> List[Dict[str, Any]]:
    """Spread a large query plan fairly across cycles without starving its tail."""
    if limit <= 0 or not searches:
        return []
    if len(searches) <= limit:
        return list(searches)
    start = (max(0, int(slot)) * limit) % len(searches)
    ordered = searches[start:] + searches[:start]
    return ordered[:limit]


def plan_searches(monitors: List[Dict[str, Any]], source_type: str) -> List[Dict[str, Any]]:
    """Gera consultas sem alterar os monitores originais.

    Um monitor pode usar ``query_variants`` para testar termos equivalentes.
    Monitores antigos continuam produzindo exatamente uma consulta.
    """
    planned: List[Dict[str, Any]] = []
    for index, monitor in enumerate(monitors):
        if monitor.get("type") != source_type:
            continue

        variants = monitor.get("query_variants")
        if not variants:
            variants = [monitor.get("keywords_search") or monitor.get("term") or monitor.get("description", "")]
        elif isinstance(variants, str):
            variants = [variants]

        seniorities = monitor.get("seniority_variants") or [monitor.get("seniority")]
        seniorities = [value for value in seniorities if value]
        if not seniorities:
            seniorities = [None]

        for variant_index, variant in enumerate(variants):
            for seniority_index, seniority in enumerate(seniorities):
                query = deepcopy(monitor)
                query["query"] = str(variant).strip()
                if seniority is not None:
                    query["seniority"] = seniority
                if monitor.get("recent_window_hours") is not None:
                    query["published_within_hours"] = monitor["recent_window_hours"]
                query["query_id"] = sha1(
                    f"{source_type}:{index}:{variant_index}:{seniority_index}:{query['query']}:{seniority}".encode("utf-8")
                ).hexdigest()[:12]
                planned.append(query)
    return planned

"""Expansão determinística de consultas configuradas por fonte."""

from copy import deepcopy
from hashlib import sha1
from typing import Any, Dict, List


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

        for variant_index, variant in enumerate(variants):
            query = deepcopy(monitor)
            query["query"] = str(variant).strip()
            query["query_id"] = sha1(
                f"{source_type}:{index}:{variant_index}:{query['query']}".encode("utf-8")
            ).hexdigest()[:12]
            planned.append(query)
    return planned

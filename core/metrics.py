from typing import Any, Dict


def summarize_cycle(
    raw_count: int,
    unique_count: int,
    notified_count: int,
    discarded_counts: Dict[str, int],
    source_statuses: Dict[str, str],
) -> Dict[str, Any]:
    """Produz métricas honestas do ciclo sem inferir precisão ou recall."""
    duplicate_count = max(0, raw_count - unique_count)
    duplicate_rate = duplicate_count / raw_count if raw_count else 0.0
    return {
        "raw_count": raw_count,
        "unique_count": unique_count,
        "duplicate_count": duplicate_count,
        "duplicate_rate": duplicate_rate,
        "notified_count": notified_count,
        "discarded_counts": dict(discarded_counts),
        "source_failures": [
            source for source, status in source_statuses.items()
            if str(status).startswith("FALHA") or status in {'FAILED', 'PARTIAL'}
        ],
        "precision_estimate": None,
        "recall_estimate": None,
        "precision_recall_note": "Feedback humano ainda não registrado",
    }

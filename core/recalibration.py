"""Recalibracao conservadora baseada em feedback humano.

A funcao gera sinais para revisao de pesos; nao modifica configuracao
automaticamente, evitando que poucos cliques distorcam o radar.
"""

from typing import Any, Dict


def build_recalibration_report(state: Dict[str, Any]) -> Dict[str, Any]:
    feedback = state.get("feedback", [])
    decisions = state.get("recent_decisions", [])
    by_category: Dict[str, Dict[str, int]] = {}
    by_source: Dict[str, Dict[str, int]] = {}
    # One relevance vote per vacancy. Employer rejection and not applying are
    # outcomes, not evidence of poor fit. Keep all events in the audit history.
    relevance = {}
    for entry in feedback:
        if entry.get("fingerprint") and entry.get("feedback") in {"applied", "interview", "hired", "irrelevant"}:
            relevance[entry["fingerprint"]] = entry
    for entry in relevance.values():
        fp = entry.get("fingerprint")
        decision = next((d for d in reversed(decisions) if d.get("identity_fingerprint") == fp), {})
        category = decision.get("category") or "unknown"
        source = decision.get("source") or "unknown"
        for bucket, key in ((by_category, category), (by_source, source)):
            values = bucket.setdefault(key, {"positive": 0, "negative": 0})
            if entry.get("feedback") in {"applied", "interview", "hired"}:
                values["positive"] += 1
            elif entry.get("feedback") == "irrelevant":
                values["negative"] += 1

    recommendations = []
    for category, values in by_category.items():
        if category == "unknown":
            continue
        total = values["positive"] + values["negative"]
        if total >= 3 and values["negative"] >= values["positive"] * 2:
            recommendations.append(f"revisar limiar da categoria {category}: feedback predominantemente negativo")
        elif total >= 3 and values["positive"] >= values["negative"] * 2:
            recommendations.append(f"preservar ou ampliar a categoria {category}: feedback predominantemente positivo")

    return {
        "feedback_count": len(feedback),
        "relevance_vacancies": len(relevance),
        "matched_feedback_count": sum(
            1 for item in feedback
            if any(d.get("identity_fingerprint") == item.get("fingerprint") for d in decisions)
        ),
        "by_category": by_category,
        "by_source": by_source,
        "recommendations": recommendations,
        "automatic_weight_change": False,
    }

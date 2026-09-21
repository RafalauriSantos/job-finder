from core.llm_judge import normalize_result


def test_old_llm_response_is_upgraded_to_structured_contract():
    result = normalize_result({
        "is_real_job_opportunity": True,
        "cv_compatibility_score": 42,
        "reasoning": "escopo parcialmente alinhado",
        "recommendation": "MAYBE",
    })
    assert result["potential_score"] == 42
    assert result["category"] == "DESAFIADORA_VALIDA"
    assert result["mandatory_requirements"] == []


def test_hard_barrier_always_makes_result_incompatible():
    result = normalize_result({"is_real_job_opportunity": True, "cv_compatibility_score": 90, "potential_score": 90, "hard_barriers": ["lideranca"]})
    assert result["category"] == "INCOMPATIVEL"

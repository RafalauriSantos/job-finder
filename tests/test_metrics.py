from core.metrics import summarize_cycle


def test_summarize_cycle_reports_duplicates_and_source_failures():
    metrics = summarize_cycle(
        raw_count=100,
        unique_count=60,
        notified_count=4,
        discarded_counts={"score": 10, "seniority": 20},
        source_statuses={"gupy": "OK", "linkedin": "FALHA (timeout)"},
    )

    assert metrics["duplicate_count"] == 40
    assert metrics["duplicate_rate"] == 0.4
    assert metrics["source_failures"] == ["linkedin"]
    assert metrics["precision_estimate"] is None
    assert metrics["recall_estimate"] is None

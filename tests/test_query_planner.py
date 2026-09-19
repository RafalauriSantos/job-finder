from core.query_planner import plan_searches


def test_query_planner_expands_variants_without_mutating_monitor():
    monitor = {
        "type": "linkedin",
        "keywords_search": "desenvolvedor",
        "query_variants": ["dev", "developer"],
        "time_range": "r3600",
    }

    planned = plan_searches([monitor], "linkedin")

    assert [query["query"] for query in planned] == ["dev", "developer"]
    assert len({query["query_id"] for query in planned}) == 2
    assert "query" not in monitor


def test_query_planner_preserves_legacy_single_query():
    planned = plan_searches([{"type": "gupy", "term": "Java", "limit": 20}], "gupy")

    assert len(planned) == 1
    assert planned[0]["query"] == "Java"
    assert planned[0]["limit"] == 20

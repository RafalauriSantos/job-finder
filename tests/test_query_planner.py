from core.query_planner import plan_searches
from core.query_planner import unique_searches, rotate_searches


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


def test_linkedin_query_variants_are_not_deduplicated_by_monitor_description():
    planned = plan_searches([{
        "type": "linkedin",
        "description": "LinkedIn React / Frontend",
        "query_variants": ["React Junior", "React Pleno", "frontend React"],
        "time_range": "r7200",
        "geo_id": "brasil",
    }], "linkedin")

    selected = unique_searches(planned)

    assert [item["query"] for item in selected] == ["React Junior", "React Pleno", "frontend React"]


def test_linkedin_duplicate_query_from_different_monitors_runs_once():
    planned = plan_searches([
        {"type": "linkedin", "description": "first", "query_variants": ["React Junior"], "time_range": "r7200"},
        {"type": "linkedin", "description": "second", "query_variants": ["React Junior"], "time_range": "r7200"},
    ], "linkedin")

    assert len(unique_searches(planned)) == 1


def test_limited_linkedin_searches_rotate_without_starving_later_queries():
    searches = [{"query": f"query-{index}"} for index in range(22)]

    first = rotate_searches(searches, limit=8, slot=0)
    second = rotate_searches(searches, limit=8, slot=1)
    third = rotate_searches(searches, limit=8, slot=2)

    assert len(first) == len(second) == len(third) == 8
    assert len({item["query"] for item in first + second + third}) == 22

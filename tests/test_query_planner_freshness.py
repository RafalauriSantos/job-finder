import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.query_planner import plan_searches


def test_builds_recent_queries_for_junior_and_pleno_title_variants():
    queries = plan_searches(
        [
            {
                "type": "linkedin",
                "query_variants": ["desenvolvedor", "developer"],
                "seniority_variants": ["junior", "mid"],
                "recent_window_hours": 24,
            }
        ],
        "linkedin",
    )

    assert [(query["query"], query["seniority"], query["published_within_hours"]) for query in queries] == [
        ("desenvolvedor", "junior", 24),
        ("desenvolvedor", "mid", 24),
        ("developer", "junior", 24),
        ("developer", "mid", 24),
    ]
    assert all(query["query_id"] for query in queries)

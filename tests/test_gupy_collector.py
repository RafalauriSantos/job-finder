import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collectors.gupy_collector import GupyCollector


class MockResponse:
    status_code = 200
    encoding = "utf-8"

    def __init__(self):
        self.text = "data: " + json.dumps({
            "result": {
                "content": [{
                    "text": json.dumps({
                        "data": {"data": [{
                            "id": 42,
                            "name": "Desenvolvedor Java",
                            "careerPageName": "Empresa Tech",
                            "city": "Sorocaba",
                            "state": "SP",
                            "jobUrl": "https://empresa.gupy.io/jobs/42",
                            "description": "Java e Spring",
                        }]}
                    })
                }]
            }
        })


class MockSession:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append(kwargs)
        return MockResponse()


def test_gupy_collector_records_query_parameters_and_result_count():
    collector = GupyCollector(MockSession(), [{"term": "Java", "limit": 20}])

    jobs = collector.collect()

    assert len(jobs) == 1
    assert collector.query_stats == [{
        "parameters": {"term": "Java", "limit": 20},
        "results": 1,
        "status": "OK",
    }]


def test_gupy_collector_distinguishes_http_failure_from_empty_result():
    class FailedSession:
        def post(self, *args, **kwargs):
            response = MockResponse()
            response.status_code = 503
            return response

    collector = GupyCollector(FailedSession(), [{"term": "Java"}])

    assert collector.collect() == []
    assert collector.query_stats[0]["status"] == "HTTP_503"


def test_gupy_collector_forwards_seniority_and_recent_window():
    session = MockSession()
    collector = GupyCollector(session, [{
        "term": "developer",
        "seniority": "mid",
        "published_within_hours": 24,
        "query_id": "internal-id",
    }])

    collector.collect()

    arguments = session.calls[0]["json"]["params"]["arguments"]
    assert arguments["seniority"] == "mid"
    assert arguments["published_within_hours"] == 24
    assert "query_id" not in arguments

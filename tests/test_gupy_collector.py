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
    def post(self, *args, **kwargs):
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

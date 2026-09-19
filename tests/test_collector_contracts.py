import requests

from collectors.github_collector import GithubIssuesCollector
from collectors.rss_collector import RssCollector
from collectors.trampos_collector import TramposCollector


class Response:
    def __init__(self, status_code=200, content=b"", payload=None):
        self.status_code = status_code
        self.content = content
        self._payload = payload
        self.text = content.decode("utf-8", errors="replace")

    def json(self):
        if isinstance(self._payload, Exception):
            raise self._payload
        return self._payload


class Session:
    def __init__(self, response):
        self.response = response

    def get(self, *args, **kwargs):
        return self.response


def test_github_http_failure_returns_empty_collection():
    collector = GithubIssuesCollector(Session(Response(status_code=503)), repos=["org/repo"])
    assert collector.collect() == []


def test_github_empty_payload_returns_empty_collection():
    collector = GithubIssuesCollector(Session(Response(payload=[])), repos=["org/repo"])
    assert collector.collect() == []


def test_rss_malformed_xml_returns_empty_collection():
    collector = RssCollector(Session(Response(content=b"<rss>broken")), [{"url": "https://feed.example/rss"}])
    assert collector.collect() == []


def test_trampos_empty_payload_returns_empty_collection():
    collector = TramposCollector(Session(Response(payload={"opportunities": []})), max_pages=1)
    assert collector.collect() == []


def test_trampos_http_failure_returns_empty_collection():
    collector = TramposCollector(Session(Response(status_code=502)), max_pages=1)
    assert collector.collect() == []

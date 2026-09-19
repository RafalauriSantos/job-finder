import os
import sys
import pytest
import requests
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collectors.linkedin_collector import LinkedInCollector


SAMPLE_LINKEDIN_HTML = """
<ul class="jobs-search__results-list">
    <li>
        <div class="base-card" data-entity-urn="urn:li:jobPosting:3910293841">
            <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/desenvolvedor-junior-at-empresa-tech-3910293841?utm_campaign=google"></a>
            <div class="base-search-card__info">
                <h3 class="base-search-card__title">
                    Desenvolvedor Frontend Júnior (React)
                </h3>
                <h4 class="base-search-card__subtitle">
                    <a href="https://br.linkedin.com/company/empresa-tech">
                        Empresa Tech Inovadora
                    </a>
                </h4>
                <span class="job-search-card__location">
                    Sorocaba, SP
                </span>
            </div>
        </div>
    </li>
    <li>
        <!-- Card incompleto sem link nem titulo para testar resiliência -->
        <div class="base-card">
            <span class="job-search-card__location">São Paulo, SP</span>
        </div>
    </li>
    <li>
        <div class="base-card" data-entity-urn="urn:li:jobPosting:9920192831">
            <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/desenvolvedor-backend-node-9920192831"></a>
            <div class="base-search-card__info">
                <h3 class="base-search-card__title">
                    Desenvolvedor Backend Node.js
                </h3>
                <h4 class="base-search-card__subtitle">
                    <a href="#">Startup X</a>
                </h4>
                <span class="job-search-card__location">
                    Remoto
                </span>
            </div>
        </div>
    </li>
</ul>
"""


class MockResponse:
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.encoding = "utf-8"


def test_linkedin_collector_parses_html_successfully(monkeypatch):
    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: MockResponse(SAMPLE_LINKEDIN_HTML, 200))

    collector = LinkedInCollector(session, [{"keywords": "Desenvolvedor Junior"}])
    jobs = collector.collect()

    assert len(jobs) == 2
    
    j1 = jobs[0]
    assert "React" in j1.title or "react" in j1.technologies
    assert j1.company == "Empresa Tech Inovadora"
    assert j1.location == "Sorocaba, SP"
    assert "linkedin" in j1.sources
    assert j1.sources["linkedin"].source_job_id == "3910293841"

    j2 = jobs[1]
    assert "Node" in j2.title or "node.js" in j2.technologies
    assert j2.company == "Startup X"
    assert j2.workplace_type == "remote"


def test_linkedin_collector_handles_http_errors_gracefully(monkeypatch):
    session = requests.Session()
    # Simula status 429 Too Many Requests ou 500 do LinkedIn
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: MockResponse("", 429))

    collector = LinkedInCollector(session, [{"keywords": "Python Junior"}])
    jobs = collector.collect()

    assert jobs == []


def test_linkedin_collector_handles_malformed_html(monkeypatch):
    session = requests.Session()
    # HTML corrompido ou inesperado
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: MockResponse("<div>Unexpected structure</div>", 200))

    collector = LinkedInCollector(session, [{"keywords": "Java Junior"}])
    jobs = collector.collect()

    assert jobs == []


def test_linkedin_collector_preserves_filters_and_paginates(monkeypatch):
    session = requests.Session()
    calls = []

    def fake_get(url, **kwargs):
        calls.append(url)
        return MockResponse(SAMPLE_LINKEDIN_HTML if len(calls) == 1 else "<ul></ul>", 200)

    monkeypatch.setattr(session, "get", fake_get)
    collector = LinkedInCollector(session, [{
        "keywords": "desenvolvedor",
        "time_range": "r3600",
        "experience": "2",
        "workplace_type": "2",
        "max_pages": 3,
    }])

    jobs = collector.collect()

    assert len(jobs) == 2
    assert len(calls) == 2
    query = parse_qs(urlparse(calls[0]).query)
    assert query["f_TPR"] == ["r3600"]
    assert query["experience"] == ["2"]
    assert query["workplace_type"] == ["2"]
    assert parse_qs(urlparse(calls[1]).query)["start"] == ["25"]

import os
import sys
import pytest
import requests

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.url_resolver import resolve_url_tripartite, sanitize_canonical_url, calculate_noise_score


def test_sanitize_canonical_url_strips_tracking():
    raw = "https://jobs.lever.co/empresa/vaga-123?utm_source=google&utm_medium=news&gclid=XYZ#apply"
    expected = "https://jobs.lever.co/empresa/vaga-123"
    assert sanitize_canonical_url(raw) == expected


def test_calculate_noise_score_detects_aggregation_pages():
    # Página típica de busca agregada no Glassdoor / Indeed
    title_noise = "285 vagas de junior software em Mauá, SP"
    url_noise = "https://www.glassdoor.com.br/Vaga/maua-junior-software-vagas-SRCH_IL.0,4_IC2499298_KO5,20.htm"
    score, reasons = calculate_noise_score(title_noise, url_noise)
    assert score >= 2
    assert "Padrão de contagem de vagas agregadas" in reasons or any("contagem" in r.lower() for r in reasons)


def test_calculate_noise_score_detects_salary_pages():
    title_salary = "Salários de Desenvolvedor Júnior na Empresa X"
    url_salary = "https://www.glassdoor.com.br/Salarios/desenvolvedor-junior-salario.htm"
    score, reasons = calculate_noise_score(title_salary, url_salary)
    assert score >= 1
    assert any("salarial" in r.lower() for r in reasons)


def test_calculate_noise_score_clean_job_is_zero():
    title_clean = "Desenvolvedor Frontend Júnior (React / Node)"
    url_clean = "https://jobs.lever.co/empresa/123-abc"
    score, reasons = calculate_noise_score(title_clean, url_clean)
    assert score == 0
    assert len(reasons) == 0


def test_resolve_url_tripartite_success(monkeypatch):
    class MockResponse:
        def __init__(self, url, status_code=200):
            self.url = url
            self.status_code = status_code

        def close(self):
            pass

    session = requests.Session()

    def mock_head(url, *args, **kwargs):
        return MockResponse("https://jobs.lever.co/fintech/vaga-dev-jr?utm_source=google_news")

    monkeypatch.setattr(session, "head", mock_head)

    raw = "https://news.google.com/rss/articles/CBMi123"
    raw_out, res_out, can_out, status = resolve_url_tripartite(raw, session)

    assert raw_out == raw
    assert res_out == "https://jobs.lever.co/fintech/vaga-dev-jr?utm_source=google_news"
    assert can_out == "https://jobs.lever.co/fintech/vaga-dev-jr"
    assert status == "RESOLVED"


def test_resolve_url_tripartite_fallback_on_head_failure(monkeypatch):
    session = requests.Session()

    def mock_head(url, *args, **kwargs):
        raise requests.RequestException("HEAD blocked by server")

    class MockStreamGet:
        def __init__(self, url):
            self.url = url
            self.status_code = 200

        def close(self):
            pass

    def mock_get(url, *args, **kwargs):
        return MockStreamGet("https://trampos.co/oportunidades/12345")

    monkeypatch.setattr(session, "head", mock_head)
    monkeypatch.setattr(session, "get", mock_get)

    raw = "https://news.google.com/rss/articles/CBMi456"
    raw_out, res_out, can_out, status = resolve_url_tripartite(raw, session)

    assert res_out == "https://trampos.co/oportunidades/12345"
    assert can_out == "https://trampos.co/oportunidades/12345"
    assert status == "RESOLVED"

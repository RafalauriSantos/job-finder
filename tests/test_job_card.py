from datetime import datetime, timedelta
from unittest.mock import Mock

import monitor
from models.job import Job
from notify.job_card import build_card
from core.scope_analyzer import analyze_scope


def test_card_preserves_education_caution_outside_first_three_reasons():
    job = Job(title="API Intern", company="CI&amp;T", workplace_type="remote",
              description="Requirements\nBachelor degree required\nTypeScript and Node.js",
              match_reasons=["a", "b", "c", "formation barrier"], job_type="CLT")
    body, _ = build_card(job)
    assert "CI&amp;T" in body and "amp;amp" not in body
    assert "Bachelor degree required" in body
    assert "CLT" not in body and "Não informado" not in body


def test_card_escapes_untrusted_text_and_limits_size_without_losing_caution():
    job = Job(title="<b>" + "X" * 8000, company="A & B", workplace_type="hybrid",
              description="Obrigatório: inglês intermediário", technologies=["<Java>"] * 50)
    body, _ = build_card(job)
    assert "&lt;b&gt;" in body and "A &amp; B" in body
    assert "inglês intermediário" in body
    assert len(body) < 1500


def test_card_uses_safe_single_destination_and_progression_without_false_match():
    job = Job(title="Dev", company="Empresa", workplace_type="unknown",
              canonical_url="javascript:alert(1)", compatibility_category="DESAFIADORA_VALIDA")
    job.add_source("gupy", "1", "https://empresa.gupy.io/jobs/1")
    body, url = build_card(job)
    assert url == "https://empresa.gupy.io/jobs/1"
    assert "progressão" in body and "compatível" not in body


def test_card_does_not_turn_desirable_english_into_required_caution():
    job = Job(title="Dev", company="Empresa", workplace_type="remote",
              description="Requisitos obrigatórios\nJava\nDiferenciais\nInglês avançado")
    body, _ = build_card(job)
    assert "Atenção:" not in body


def test_scope_does_not_match_java_in_javascript_or_git_in_digital():
    job = Job(title="JavaScript Intern", company="Digital", workplace_type="remote",
              description="JavaScript para produto digital")
    result = analyze_scope(job, {"stack_core": ["Java", "Git"], "stack_secundaria": []})
    assert result["matched_evidence"] == []
    assert result["declared_level"] == "junior"


def test_scope_keeps_inline_mandatory_and_desirable_requirements():
    job = Job(title="Dev", company="Empresa", workplace_type="remote",
              description="Obrigatório: Java\nDesejável: Docker")
    result = analyze_scope(job, {"stack_core": ["Java"], "stack_secundaria": []})
    assert result["mandatory_requirements"] == ["Obrigatório: Java"]
    assert result["desirable_requirements"] == ["Desejável: Docker"]


def test_flat_description_keeps_english_before_nice_to_have_and_ignores_company_age():
    job = Job(title="Java Junior", company="Empresa", workplace_type="remote",
              description="Há mais de 15 anos, criamos software. - Inglês avançado. Nice to have: - Docker.",
              analysis={"hard_barriers": ["5 anos"]})
    body, _ = build_card(job)
    assert "Inglês avançado" in body
    assert "5 anos" not in body
    assert "criamos software" not in body
    assert analyze_scope(job, {"stack_core": ["Java"]})["hard_barriers"] == []


def test_weekly_status_waits_seven_days_and_daily_remains_supported():
    store, notifier = Mock(), Mock()
    store.state = {}
    store.get_last_heartbeat.return_value = (datetime.now() - timedelta(days=2)).date().isoformat()
    config = {"heartbeat": {"enabled": True, "frequency": "weekly", "hour_start": 0}}
    monitor.check_heartbeat(config, store, notifier)
    notifier.send_heartbeat.assert_not_called()
    store.get_last_heartbeat.return_value = (datetime.now() - timedelta(days=7)).date().isoformat()
    monitor.check_heartbeat(config, store, notifier)
    notifier.send_heartbeat.assert_called_once()
    store.set_last_heartbeat.assert_called_once()

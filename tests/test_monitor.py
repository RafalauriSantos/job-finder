import json
import os
import sys
import tempfile
import xml.etree.ElementTree as ET
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from monitor import (
    matches_filters,
    query_rss,
    load_state,
    save_state,
    send_telegram,
    query_gupy_mcp,
)


class TestFilters:
    def test_accepts_valid_keywords(self):
        job = {"name": "Desenvolvedor Java Júnior", "description": "Trabalhar com Spring Boot", "workplaceType": "remote"}
        monitor_cfg = {"keywords": ["java", "python"], "exclude_keywords": ["senior"], "only_remote": False}
        assert matches_filters(job, monitor_cfg) is True

    def test_rejects_blacklisted_keywords(self):
        job = {"name": "Desenvolvedor Java Sênior", "description": "Liderança técnica", "workplaceType": "remote"}
        monitor_cfg = {"keywords": ["java"], "exclude_keywords": ["senior", "sênior", "lead"], "only_remote": False}
        assert matches_filters(job, monitor_cfg) is False

    def test_rejects_non_remote_when_only_remote_is_true(self):
        job = {"name": "Dev Python Jr", "description": "Vaga presencial em SP", "workplaceType": "on-site"}
        monitor_cfg = {"keywords": ["python"], "exclude_keywords": [], "only_remote": True}
        assert matches_filters(job, monitor_cfg) is False

    def test_strict_location_accepts_remote(self):
        job = {"name": "Dev React Jr", "workplaceType": "remote", "location": "Recife, PE"}
        monitor_cfg = {"keywords": ["react"], "exclude_keywords": [], "strict_location": True}
        assert matches_filters(job, monitor_cfg) is True

    def test_strict_location_accepts_sorocaba_tatui_hybrid(self):
        job = {"name": "Desenvolvedor Node Jr", "workplaceType": "hybrid", "location": "Sorocaba, SP"}
        monitor_cfg = {"keywords": ["node"], "exclude_keywords": [], "strict_location": True}
        assert matches_filters(job, monitor_cfg) is True

    def test_strict_location_rejects_hybrid_outside_region(self):
        job = {"name": "Dev Fullstack Jr", "workplaceType": "hybrid", "location": "São Paulo, SP"}
        monitor_cfg = {"keywords": ["fullstack"], "exclude_keywords": [], "strict_location": True}
        assert matches_filters(job, monitor_cfg) is False


class TestRSSParser:
    def test_parses_atom_feed_correctly(self):
        sample_atom = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<feed xmlns="http://www.w3.org/2005/Atom">'
            b'  <entry>'
            b'    <id>tag:google.com,2013:googlealerts/feed:12345</id>'
            b'    <title type="html">Vaga: &lt;b&gt;Flavia Nasser&lt;/b&gt; Contrata</title>'
            b'    <link href="https://exemplo.com/vaga/123"/>'
            b'  </entry>'
            b'</feed>'
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = sample_atom

        with patch("monitor.HTTP.get", return_value=mock_resp):
            jobs = query_rss("https://fake-feed.xml", "Flavia Nasser")
            assert len(jobs) == 1
            assert jobs[0]["name"] == "Vaga: Flavia Nasser Contrata"
            assert jobs[0]["jobUrl"] == "https://exemplo.com/vaga/123"
            assert jobs[0]["careerPageName"] == "Flavia Nasser"

    def test_parses_rss_20_feed_correctly(self):
        sample_rss = (
            b'<?xml version="1.0" encoding="UTF-8"?>'
            b'<rss version="2.0">'
            b'  <channel>'
            b'    <item>'
            b'      <guid>gft-job-999</guid>'
            b'      <title>GFT e DIO lancam novo Bootcamp Starter</title>'
            b'      <link>https://jobs.gft.com/job/999</link>'
            b'    </item>'
            b'  </channel>'
            b'</rss>'
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = sample_rss

        with patch("monitor.HTTP.get", return_value=mock_resp):
            jobs = query_rss("https://fake-feed.xml", "GFT Brasil")
            assert len(jobs) == 1
            assert jobs[0]["id"] == "gft-job-999"
            assert "Bootcamp Starter" in jobs[0]["name"]
            assert jobs[0]["jobUrl"] == "https://jobs.gft.com/job/999"


class TestStatePersistence:
    def test_loads_legacy_list_and_saves_dict(self, monkeypatch):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_state_file = os.path.join(tmpdir, "test_seen.json")
            # Cria estado no formato legado (apenas lista de IDs)
            with open(test_state_file, "w", encoding="utf-8") as f:
                json.dump([101, 102, 103], f)

            monkeypatch.setattr("monitor.STATE_FILE", test_state_file)

            state = load_state()
            assert state["seen_ids"] == [101, 102, 103]

            # Adiciona novo ID e salva
            state["seen_ids"].append(104)
            save_state(state)

            reloaded = load_state()
            assert 104 in reloaded["seen_ids"]


class TestTelegramNotification:
    def test_telegram_sends_correct_payload_and_buttons(self, monkeypatch):
        monkeypatch.setattr("monitor.TELEGRAM_BOT_TOKEN", "fake_token_123")
        monkeypatch.setattr("monitor.TELEGRAM_CHAT_ID", "123456789")

        mock_post = MagicMock()
        mock_post.return_value.status_code = 200

        with patch("monitor.HTTP.post", mock_post):
            success = send_telegram(
                title="Desenvolvedor Java Jr",
                company="GFT Brasil",
                workplace="Remoto",
                job_type="CLT",
                salary="A combinar",
                url="https://jobs.gft.com/123",
            )

            assert success is True
            assert mock_post.called
            call_args = mock_post.call_args[1]["json"]
            assert call_args["chat_id"] == "123456789"
            assert "Desenvolvedor Java Jr" in call_args["text"]
            assert call_args["disable_web_page_preview"] is True
            assert "inline_keyboard" in call_args["reply_markup"]
            assert call_args["reply_markup"]["inline_keyboard"][0][0]["url"] == "https://jobs.gft.com/123"

    def test_heartbeat_daily_respects_state_and_triggers(self, monkeypatch):
        from monitor import check_heartbeat
        monkeypatch.setattr("monitor.TELEGRAM_BOT_TOKEN", "fake_token_123")
        monkeypatch.setattr("monitor.TELEGRAM_CHAT_ID", "123456789")

        mock_post = MagicMock()
        mock_post.return_value.status_code = 200

        config = {
            "heartbeat": {"enabled": True, "frequency": "daily", "hour_start": 0},
            "monitors": [{"type": "gupy", "description": "M1"}],
        }
        state = {"seen_ids": [], "last_heartbeat": ""}

        with patch("monitor.HTTP.post", mock_post):
            check_heartbeat(config, state)
            assert mock_post.called
            assert state["last_heartbeat"] != ""

            # Segunda chamada no mesmo dia não deve disparar de novo
            mock_post.reset_mock()
            check_heartbeat(config, state)
            assert not mock_post.called


class TestLiveGupyAPI:
    def test_gupy_endpoint_responds_200(self):
        """Teste de fumaça real para garantir que o endpoint público da Gupy continua ativo."""
        jobs = query_gupy_mcp({"careerPageName": "goomer", "limit": 1})
        # Deve retornar uma lista (mesmo que vazia se não houver vagas abertas)
        assert isinstance(jobs, list)


class TestLinkedInParser:
    def test_parses_linkedin_card_correctly(self):
        from monitor import query_linkedin
        sample_html = (
            '<li>'
            '  <div class="base-card" data-entity-urn="urn:li:jobPosting:99887766">'
            '    <a class="base-card__full-link" href="https://br.linkedin.com/jobs/view/99887766?ref=123"></a>'
            '    <h3 class="base-search-card__title">Desenvolvedor React Jr</h3>'
            '    <h4 class="base-search-card__subtitle"><a href="#">Tech Corp</a></h4>'
            '    <span class="job-search-card__location">Remoto, Brasil</span>'
            '  </div>'
            '</li>'
        )

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.text = sample_html

        with patch("monitor.HTTP.get", return_value=mock_resp):
            jobs = query_linkedin("React Junior")
            assert len(jobs) == 1
            assert jobs[0]["id"] == "li-99887766"
            assert jobs[0]["name"] == "Desenvolvedor React Jr"
            assert jobs[0]["careerPageName"] == "Tech Corp"
            assert jobs[0]["workplaceType"] == "remote"
            assert jobs[0]["jobUrl"] == "https://br.linkedin.com/jobs/view/99887766"

    def test_live_linkedin_guest_api_responds(self):
        """Teste de fumaça real para a Guest API do LinkedIn."""
        from monitor import query_linkedin
        jobs = query_linkedin("Desenvolvedor Junior", time_range="r86400")
        assert isinstance(jobs, list)

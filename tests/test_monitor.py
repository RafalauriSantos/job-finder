import json
import os
import sys
import tempfile
from unittest.mock import MagicMock, patch
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from models.job import Job
from core.normalizer import is_location_allowed, extract_technologies
from core.scoring import calculate_match_score
from core.deduplicator import Deduplicator
from notify.telegram_notifier import TelegramNotifier
from storage.state_store import StateStore
from collectors.gupy_collector import GupyCollector
from collectors.linkedin_collector import LinkedInCollector


class TestFiltersAndLocation:
    def test_strict_location_rules(self):
        # Remoto aceito
        allowed, _ = is_location_allowed("remote", "Recife, PE")
        assert allowed is True

        # Híbrido em Sorocaba aceito
        allowed, _ = is_location_allowed("hybrid", "Sorocaba, SP")
        assert allowed is True

        # Híbrido em Boituva aceito
        allowed, _ = is_location_allowed("hybrid", "Boituva, SP")
        assert allowed is True

        # Híbrido em São Paulo capital rejeitado
        allowed, _ = is_location_allowed("hybrid", "São Paulo, SP")
        assert allowed is False


class TestStateStorePersistence:
    def test_loads_legacy_and_persists_fingerprints(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "seen.json")
            with open(test_file, "w", encoding="utf-8") as f:
                json.dump({"seen_ids": ["123", "456"], "last_heartbeat": "2026-09-08"}, f)

            store = StateStore(test_file)
            assert store.is_seen("fake_fp", "123") is True
            assert store.is_seen("fake_fp", "999") is False

            store.mark_seen("fp_novo", ["999"])
            store.save()

            reloaded = StateStore(test_file)
            assert reloaded.is_seen("fp_novo") is True
            assert "999" in reloaded.state["seen_ids"]

    def test_records_decision_audit_trail(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "seen.json")
            store = StateStore(test_file)
            store.record_decision(
                job_id="job-101",
                source="github",
                identity_fingerprint="fp-canonico",
                content_hash="hash-desc",
                decision="DISCARD_PCD",
                decision_reason="Titulo contem 'PCD'",
                heuristic_score=0,
                final_score=0
            )
            store.save()

            reloaded = StateStore(test_file)
            assert len(reloaded.state.get("recent_decisions", [])) == 1
            entry = reloaded.state["recent_decisions"][0]
            assert entry["job_id"] == "job-101"
            assert entry["decision"] == "DISCARD_PCD"
            assert entry["identity_fingerprint"] == "fp-canonico"
            assert "timestamp" in entry

    def test_failed_delivery_is_not_marked_as_seen(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(os.path.join(tmpdir, "seen.json"))

            store.record_delivery("fp-falha", ["job-101"], delivered=False)

            assert store.is_seen("fp-falha", "job-101") is False
            assert store.get_delivery("fp-falha")["status"] == "DELIVERY_FAILED"
            assert store.get_delivery("fp-falha")["attempts"] == 1

    def test_successful_delivery_is_marked_as_seen_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(os.path.join(tmpdir, "seen.json"))

            store.record_delivery("fp-ok", ["job-202"], delivered=True)
            store.record_delivery("fp-ok", ["job-202"], delivered=True)

            assert store.is_seen("fp-ok", "job-202") is True
            assert store.get_delivery("fp-ok")["status"] == "DELIVERED"
            assert store.get_delivery("fp-ok")["attempts"] == 2

    def test_delivery_retry_uses_backoff_and_attempt_limit(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(os.path.join(tmpdir, "seen.json"))

            assert store.delivery_retry_allowed("new-fp") is True
            store.record_delivery("retry-fp", ["job-1"], delivered=False)
            assert store.delivery_retry_allowed("retry-fp") is False
            assert store.delivery_retry_allowed("retry-fp", ignore_backoff=True) is True

            store.record_delivery("retry-fp", ["job-1"], delivered=False)
            store.record_delivery("retry-fp", ["job-1"], delivered=False)
            assert store.delivery_retry_allowed("retry-fp", ignore_backoff=True) is False

    def test_records_source_health_history(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            store = StateStore(os.path.join(tmpdir, "seen.json"))

            store.record_source_health("linkedin", "OK", 12, {"queries": 3})
            store.save()
            reloaded = StateStore(os.path.join(tmpdir, "seen.json"))

            health = reloaded.state["source_health"][-1]
            assert health["source"] == "linkedin"
            assert health["discovered"] == 12
            assert health["details"]["queries"] == 3

    def test_pruning_limits_retention(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            test_file = os.path.join(tmpdir, "seen.json")
            store = StateStore(test_file)
            # Insere 15 IDs e 15 decisões simuladas
            store.state["seen_ids"] = [f"id-{i}" for i in range(15)]
            store.state["seen_fingerprints"] = [f"fp-{i}" for i in range(15)]
            store.state["recent_decisions"] = [{"decision": f"d-{i}"} for i in range(15)]

            # Executa prune com limites baixos
            store.prune(max_seen_ids=5, max_fingerprints=5, max_decisions=5)
            store.save()

            reloaded = StateStore(test_file)
            assert len(reloaded.state["seen_ids"]) == 5
            assert reloaded.state["seen_ids"] == ["id-10", "id-11", "id-12", "id-13", "id-14"]
            assert len(reloaded.state["seen_fingerprints"]) == 5
            assert reloaded.state["seen_fingerprints"] == ["fp-10", "fp-11", "fp-12", "fp-13", "fp-14"]
            assert len(reloaded.state["recent_decisions"]) == 5



class TestTelegramNotifier:
    def test_telegram_sends_formatted_alert_with_score_and_buttons(self):
        mock_http = MagicMock()
        mock_http.post.return_value.status_code = 200

        notifier = TelegramNotifier("fake_token", "fake_chat", mock_http)
        job = Job(
            title="Desenvolvedor React Jr",
            company="Goomer",
            workplace_type="remote",
            match_score=95,
            match_reasons=["Nível Júnior", "Stack Core React"],
        )
        job.add_source("gupy", "101", "https://goomer.gupy.io/jobs/101")
        job.add_source("linkedin", "202", "https://linkedin.com/jobs/202")

        success = notifier.send_job_alert(job)
        assert success is True
        assert mock_http.post.called

        call_json = mock_http.post.call_args[1]["json"]
        assert "MATCH COMPATÍVEL: 95/100" in call_json["text"]
        assert "Goomer" in call_json["text"]
        buttons = call_json["reply_markup"]["inline_keyboard"]
        # Deve ter botões para ambas as fontes (GUPY e LINKEDIN)
        assert len(buttons) == 2


class TestCollectorsLiveSmoke:
    def test_live_gupy_collector_structure(self):
        import requests
        col = GupyCollector(requests.Session(), [{"term": "React", "limit": 1}])
        jobs = col.collect()
        assert isinstance(jobs, list)

    def test_live_linkedin_collector_structure(self):
        import requests
        col = LinkedInCollector(requests.Session(), [{"keywords": "Desenvolvedor Junior", "time_range": "r86400"}])
        jobs = col.collect()
        assert isinstance(jobs, list)

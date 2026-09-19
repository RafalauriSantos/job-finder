import json

import monitor
from models.job import Job
from storage.state_store import StateStore


class EmptyCollector:
    def __init__(self, *args, **kwargs):
        self.query_stats = []

    def collect(self):
        return []


class FakeGupyCollector:
    def __init__(self, *args, **kwargs):
        self.query_stats = [{"parameters": {"term": "React"}, "results": 1, "status": "OK"}]

    def collect(self):
        job = Job(
            title="Desenvolvedor React Junior",
            company="Goomer",
            workplace_type="remote",
            location="Brasil",
            description="React, TypeScript, Node.js, PostgreSQL, testes e APIs.",
            technologies=["React", "TypeScript", "Node.js", "PostgreSQL"],
            evidence_level="HIGH_EVIDENCE",
        )
        job.add_source("gupy", "gupy-1", "https://goomer.gupy.io/jobs/1")
        return [job]


class FakeNotifier:
    def __init__(self, *args, **kwargs):
        self.alerts = []

    def send_job_alert(self, job):
        self.alerts.append(job)
        return True

    def send_heartbeat(self, *args, **kwargs):
        return False


def test_run_check_processes_and_persists_one_job_without_network(monkeypatch, tmp_path):
    state_file = tmp_path / "seen.json"
    config = {
        "min_match_score": 50,
        "heartbeat": {"enabled": False},
        "monitors": [
            {"type": "gupy", "term": "React", "limit": 1},
            {"type": "linkedin", "keywords_search": "React"},
            {"type": "rss", "url": "https://feed.example/rss"},
            {"type": "github_issues", "repos": []},
            {"type": "trampos", "keywords": ["react"]},
        ],
    }
    notifier = FakeNotifier()

    monkeypatch.setattr(monitor, "load_config", lambda: config)
    monkeypatch.setattr(monitor, "STATE_FILE", str(state_file))
    monkeypatch.setattr(monitor, "GupyCollector", FakeGupyCollector)
    monkeypatch.setattr(monitor, "LinkedInCollector", EmptyCollector)
    monkeypatch.setattr(monitor, "RssCollector", EmptyCollector)
    monkeypatch.setattr(monitor, "GithubIssuesCollector", EmptyCollector)
    monkeypatch.setattr(monitor, "TramposCollector", EmptyCollector)
    monkeypatch.setattr(monitor, "TelegramNotifier", lambda *args, **kwargs: notifier)

    monitor.run_check()

    saved = StateStore(str(state_file))
    assert len(notifier.alerts) == 1
    assert saved.state["recent_decisions"][-1]["decision"] == "DELIVERED"
    assert saved.is_seen(notifier.alerts[0].fingerprint, "gupy-1") is True

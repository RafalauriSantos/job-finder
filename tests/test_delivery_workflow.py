from core.delivery_workflow import finalize_delivery
from storage.state_store import StateStore
from models.job import Job


def test_failed_delivery_is_audited_and_remains_retryable(tmp_path):
    store = StateStore(str(tmp_path / "seen.json"))
    job = Job(title="Dev React", company="Empresa", workplace_type="remote")
    job.add_source("linkedin", "job-1", "https://linkedin.com/jobs/1")

    status = finalize_delivery(store, job, ["job-1"], sent=False, score=61, reason="Aprovada")

    assert status == "DELIVERY_FAILED"
    assert store.is_seen(job.fingerprint, "job-1") is False
    assert store.get_delivery(job.fingerprint)["status"] == "DELIVERY_FAILED"
    assert store.state["recent_decisions"][-1]["decision"] == "DELIVERY_FAILED"

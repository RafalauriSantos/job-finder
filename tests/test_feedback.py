import pytest

from storage.state_store import StateStore


def test_feedback_is_persisted_and_summarized(tmp_path):
    store = StateStore(str(tmp_path / "state.json"))
    store.record_feedback("fp-1", "applied", "stack alinhada")
    store.record_feedback("fp-2", "not_applied")
    assert store.feedback_summary() == {"total": 2, "by_feedback": {"applied": 1, "not_applied": 1}}


def test_feedback_rejects_unknown_values(tmp_path):
    store = StateStore(str(tmp_path / "state.json"))
    with pytest.raises(ValueError):
        store.record_feedback("fp-1", "maybe")

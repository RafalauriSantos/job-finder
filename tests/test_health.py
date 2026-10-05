from storage.sqlite_store import SQLiteStore
from core.health import health_snapshot


def test_health_snapshot_reports_healthy_runtime(tmp_path):
    store = SQLiteStore(tmp_path / 'state.db')
    with store.connect() as db:
        db.execute("INSERT INTO cycles(started,finished,status) VALUES ('2026-10-04T12:00:00+00:00','2026-10-04T12:01:00+00:00','COMPLETED')")
    result = health_snapshot(store, tmp_path, cycle_max_age_seconds=200000)
    assert result['database'] == 'OK'
    assert result['last_cycle_status'] == 'COMPLETED'
    assert result['status'] == 'HEALTHY'


def test_health_snapshot_marks_stale_cycle_degraded(tmp_path):
    store = SQLiteStore(tmp_path / 'state.db')
    with store.connect() as db:
        db.execute("INSERT INTO cycles(started,finished,status) VALUES ('2020-01-01T12:00:00+00:00','2020-01-01T12:01:00+00:00','COMPLETED')")
    result = health_snapshot(store, tmp_path, cycle_max_age_seconds=60)
    assert result['status'] == 'DEGRADED'
    assert 'cycle_stale' in result['issues']

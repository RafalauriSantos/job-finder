from storage.sqlite_store import SQLiteStore
import requests
from collectors.gupy_collector import GupyCollector


class _EmptyResponse:
    status_code = 200
    text = 'data: {"result":{"content":[{"text":"{\\"data\\":{\\"data\\":[]}}"}]}}'


def test_empty_response_is_a_successful_auditable_attempt():
    class Session:
        def post(self, *args, **kwargs):
            return _EmptyResponse()
    collector = GupyCollector(Session(), [{'term': 'python'}])
    assert collector.collect() == []
    assert collector.collection_attempts[0]['http_status'] == 200
    assert collector.collection_attempts[0]['result_count'] == 0


def test_timeout_is_recorded_without_breaking_collection():
    class Session:
        def post(self, *args, **kwargs):
            raise requests.Timeout('read timeout')
    collector = GupyCollector(Session(), [{'term': 'python'}])
    assert collector.collect() == []
    attempt = collector.collection_attempts[0]
    assert attempt['timed_out'] is True
    assert attempt['error_type'] == 'Timeout'


def test_collection_attempts_and_manual_cases_are_persisted(tmp_path):
    store = SQLiteStore(tmp_path / 'state.db')
    store.record_collection_attempt({
        'cycle_id': 'cycle-1', 'source': 'linkedin', 'operation': 'search',
        'query': 'python', 'query_hash': 'abc', 'page': 0,
        'http_status': 429, 'result_count': 0, 'native_ids': [],
        'error_type': 'HTTP_429', 'timed_out': False, 'retry_count': 1,
        'reason': 'rate limit',
        'duration_ms': 12,
    })
    store.record_manual_case('https://www.linkedin.com/jobs/view/123/?trk=x', 'linkedin', '123')
    fresh = SQLiteStore(store.filepath)
    with fresh.connect() as db:
        attempt = db.execute('SELECT source,http_status,native_ids,duration_ms FROM collection_attempts').fetchone()
        manual = db.execute('SELECT normalized_url,native_id,identity_status FROM manual_cases').fetchone()
    assert attempt == ('linkedin', 429, '[]', 12)
    assert manual == ('https://www.linkedin.com/jobs/view/123', '123', 'identity_resolved')


def test_collection_attempt_serializes_structured_query(tmp_path):
    store = SQLiteStore(tmp_path / 'state.db')
    store.record_collection_attempt({
        'cycle_id': 'cycle-2', 'source': 'gupy', 'operation': 'search',
        'query': {'term': 'python', 'limit': 20}, 'started': '2026-01-01T00:00:00+00:00',
        'finished': '2026-01-01T00:00:00.100000+00:00', 'duration_ms': 100,
    })
    with store.connect() as db:
        assert db.execute('SELECT query FROM collection_attempts').fetchone()[0] == '{"limit": 20, "term": "python"}'

import json

from storage.sqlite_store import SQLiteStore
from workhunter_cli import diagnose


def test_diagnose_classifies_collected_and_uncollected_cases(tmp_path):
    store = SQLiteStore(tmp_path / 'state.db')
    store.record_manual_case('https://www.linkedin.com/jobs/view/123/?trk=x')
    store.record_manual_case('https://www.linkedin.com/jobs/view/999/?trk=x')
    store.record_collection_attempt({
        'cycle_id': 'c', 'source': 'linkedin', 'operation': 'search',
        'native_ids': ['123'], 'http_status': 200,
    })
    with store.connect() as db:
        db.execute('INSERT INTO jobs(source,external_id,payload) VALUES (?,?,?)',
                   ('linkedin', '123', json.dumps({'sources': {'linkedin': {'url': 'https://www.linkedin.com/jobs/view/123'}}})))
    result = diagnose(store)
    assert {item['native_id']: item['classification'] for item in result} == {
        '123': 'collected_no_decision', '999': 'not_collected'
    }

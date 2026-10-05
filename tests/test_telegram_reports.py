import json

from core.telegram_inbox import poll_manual_urls
from core.telegram_reports import command_response
from storage.sqlite_store import SQLiteStore


def _store(tmp_path):
    store = SQLiteStore(tmp_path / 'state.db')
    report = {
        'duration_seconds': 30.0,
        'sources': {
            'linkedin': {'status': 'SUCCESS', 'discovered': 4},
            'gupy': {'status': 'DEGRADED', 'discovered': 2},
        },
        'funnel': {
            'raw': 6, 'unique': 5, 'seen': 1,
            'discarded': {'location': 1, 'score': 1}, 'notified': 2,
        },
        'llm_calls_today': 2,
        'llm_fallbacks': 1,
    }
    with store.connect() as db:
        db.execute('INSERT INTO cycles(started,finished,status,report) VALUES (?,?,?,?)',
                   ('2026-10-05T12:00:00+00:00', '2026-10-05T12:00:30+00:00',
                    'DEGRADED', json.dumps(report)))
    return store


def test_daily_report_aggregates_persisted_cycle(tmp_path):
    report = command_response('/relatorio', _store(tmp_path))
    assert 'Ciclos concluídos: 1' in report
    assert 'Encontradas: 6' in report
    assert 'Alertas enviados: 2' in report
    assert 'gupy' in report


def test_commands_have_expected_responses(tmp_path):
    store = _store(tmp_path)
    assert 'Comandos do WorkHunter' in command_response('/ajuda', store)
    assert 'Último ciclo' in command_response('/status', store)
    assert 'linkedin' in command_response('/fontes', store)
    assert 'Últimas decisões' in command_response('/ultimas', store)
    assert 'Problemas' in command_response('/problemas', store)


def test_unknown_command_is_ignored(tmp_path):
    assert command_response('/desconhecido', _store(tmp_path)) is None


def test_telegram_command_is_replied_to_without_entering_manual_queue(tmp_path):
    store = _store(tmp_path)

    class Response:
        status_code = 200

        def json(self):
            return {'result': [{'update_id': 7, 'message': {
                'chat': {'id': '42'}, 'from': {'id': '99'}, 'text': '/ajuda'
            }}]}

    class Http:
        def __init__(self):
            self.posts = []

        def get(self, url, **kwargs):
            return Response()

        def post(self, url, **kwargs):
            self.posts.append(kwargs['json'])
            return Response()

    http = Http()
    assert poll_manual_urls(store, http, 'token', '42', '99') == 1
    assert 'Comandos do WorkHunter' in http.posts[0]['text']
    with store.connect() as db:
        assert db.execute('SELECT COUNT(*) FROM manual_analysis_queue').fetchone()[0] == 0

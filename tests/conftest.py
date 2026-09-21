import socket
import sys

import pytest


@pytest.fixture(autouse=True)
def isolated_runtime(monkeypatch, tmp_path):
    for name in ('GEMINI_API_KEY', 'ANTHROPIC_API_KEY', 'TELEGRAM_BOT_TOKEN',
                 'TELEGRAM_CHAT_ID', 'RESEND_API_KEY', 'GITHUB_TOKEN'):
        monkeypatch.delenv(name, raising=False)
    def denied(*args, **kwargs):
        raise RuntimeError('Network disabled in unit tests')

    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'create_connection', denied)
    monitor = sys.modules.get('monitor')
    if monitor is not None:
        monkeypatch.setattr(monitor, 'HEALTH_REPORT_FILE', str(tmp_path / 'health.json'))

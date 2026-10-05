"""Send the local WorkHunter heartbeat to the external Cloudflare watchdog."""
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from dotenv import load_dotenv

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
load_dotenv(Path.home() / '.job-finder' / 'secrets.env', override=False)

from storage.sqlite_store import SQLiteStore
from core.health import health_snapshot


def service_active(name):
    result = subprocess.run(['systemctl', '--user', 'is-active', name],
                            capture_output=True, text=True, timeout=5)
    return result.returncode == 0 and result.stdout.strip() == 'active'


def main():
    endpoint = os.getenv('WORKHUNTER_HEARTBEAT_URL', '').rstrip('/')
    secret = os.getenv('WORKHUNTER_HEARTBEAT_TOKEN', '')
    if not endpoint or not secret:
        return 0
    payload = {
        'service': 'workhunter',
        'last_cycle_at': datetime.now(timezone.utc).isoformat(),
        'job_finder': 'active' if service_active('job-finder.service') else 'inactive',
        'telegram_worker': 'active' if service_active('workhunter-inbox.service') else 'inactive',
    }
    data_dir = os.getenv('JOB_FINDER_DATA_DIR', str(os.path.expanduser('~/.job-finder')))
    try:
        payload['health'] = health_snapshot(SQLiteStore(os.path.join(data_dir, 'state.db')), data_dir)
        payload['last_cycle_at'] = payload['health'].get('last_cycle_at') or payload['last_cycle_at']
    except Exception:
        payload['health'] = {'status': 'OFFLINE', 'issues': ['health_check_failed']}
    response = requests.post(endpoint, headers={'Authorization': f'Bearer {secret}',
                                                  'Content-Type': 'application/json'},
                             json=payload, timeout=15)
    response.raise_for_status()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

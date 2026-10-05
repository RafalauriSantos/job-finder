"""Long-polling Telegram worker, independent from scheduled collection."""
import os
import sys
import time
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
os.environ.setdefault('JOB_FINDER_RUNTIME_LOG', str(Path.home() / '.job-finder' / 'manual-worker.log'))
os.environ['JOB_FINDER_MANUAL_ONLY'] = '1'

import monitor
from core.local_runtime import data_directory
from core.telegram_inbox import poll_manual_urls
from storage.sqlite_store import SQLiteStore
from workhunter_worker import run


def main():
    """Wait for Telegram updates and run analysis only when a URL arrives."""
    token = monitor.TELEGRAM_BOT_TOKEN
    chat_id = monitor.TELEGRAM_CHAT_ID
    allowed_user_id = os.getenv('TELEGRAM_ALLOWED_USER_ID')
    database = data_directory() / 'state.db'
    while True:
        try:
            store = SQLiteStore(database)
            handled = poll_manual_urls(
                store, monitor.HTTP, token, chat_id, allowed_user_id,
                poll_timeout=45, request_timeout=60,
            )
            if handled:
                # The update was already consumed. The one-shot manual cycle
                # must process the queue without opening a second getUpdates
                # request and without running the normal collectors.
                os.environ['JOB_FINDER_SKIP_TELEGRAM_POLL'] = '1'
                run()
        except Exception as exc:
            print(f'manual worker failed: {type(exc).__name__}: {exc}', flush=True)
            traceback.print_exc()
            time.sleep(5)


if __name__ == '__main__':
    main()

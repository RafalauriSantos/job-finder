"""Local one-shot execution. The OS lock is released even after process death."""
import argparse
import json
import os
import subprocess
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from core.local_schedule import is_due, interval_at
from storage.sqlite_store import SQLiteStore


@contextmanager
def exclusive_process(path):
    handle = Path(path).open('a+b')
    locked = False
    try:
        handle.seek(0)
        if os.name == 'nt':
            import msvcrt
            try:
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
                locked = True
            except OSError:
                pass
        else:
            import fcntl
            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                locked = True
            except BlockingIOError:
                pass
        yield locked
    finally:
        handle.close()


def data_directory():
    # MSIX parents (such as Codex) can redirect AppData into a private overlay.
    # A Startup-launched process must see the same database, credentials and lock.
    return Path(os.environ.get('JOB_FINDER_DATA_DIR', str(Path.home() / '.job-finder')))


def diagnostic(store):
    now = datetime.now(timezone.utc)
    with store.connect() as db:
        cycle = db.execute('SELECT id,started,finished,status,revision FROM cycles ORDER BY id DESC LIMIT 1').fetchone()
        uncertain = db.execute("SELECT COUNT(*) FROM channel_attempts WHERE status='UNKNOWN'").fetchone()[0]
        pending = db.execute("SELECT status,COUNT(*) FROM outbox WHERE status!='DELIVERED' GROUP BY status").fetchall()
    last = datetime.fromisoformat(cycle[1]) if cycle else None
    return {'database': store.filepath, 'last_cycle': cycle,
            'due': is_due(now, last),
            'next_check_due': (last + interval_at(now)).isoformat() if last else now.isoformat(),
            'pending_deliveries': dict(pending),
            'uncertain_attempts': uncertain}


def execute_cycle(monitor, store, due_only=False):
    now = datetime.now(timezone.utc)
    with store.connect() as db:
        timeout_seconds = int(os.environ.get('JOB_FINDER_CYCLE_TIMEOUT_SECONDS', '240'))
        active = db.execute(
            "SELECT id,started FROM cycles WHERE status='RUNNING' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if active:
            active_started = datetime.fromisoformat(active[1])
            if (now - active_started).total_seconds() <= timeout_seconds:
                return 'NOT_DUE' if due_only else 'BUSY'
            db.execute("UPDATE cycles SET status='INTERRUPTED',finished=? WHERE id=?",
                       (now.isoformat(), active[0]))
        previous = db.execute(
            "SELECT started FROM cycles WHERE status != 'RUNNING' ORDER BY id DESC LIMIT 1"
        ).fetchone()
        if due_only and not is_due(now, datetime.fromisoformat(previous[0]) if previous else None):
            return 'NOT_DUE'
        revision = subprocess.run(['git', 'rev-parse', 'HEAD'], capture_output=True, text=True, check=True).stdout.strip()
        if subprocess.run(['git', 'status', '--porcelain', '--untracked-files=no'],
                          capture_output=True, text=True, check=True).stdout.strip():
            revision += '+dirty'
        cycle = db.execute('INSERT INTO cycles(started,status,revision) VALUES (?, ?, ?)',
                           (now.isoformat(), 'RUNNING', revision)).lastrowid
    try:
        store.backup(Path(store.filepath).parent / 'backups')
        monitor.run_check()
    except BaseException:
        with store.connect() as db:
            db.execute('UPDATE cycles SET finished=?,status=? WHERE id=?',
                       (datetime.now(timezone.utc).isoformat(), 'FAILED', cycle))
        raise
    report = json.loads(Path(monitor.HEALTH_REPORT_FILE).read_text(encoding='utf-8'))
    status = 'DEGRADED' if report.get('status') == 'DEGRADED' else 'COMPLETED'
    with store.connect() as db:
        db.execute('UPDATE cycles SET finished=?,status=? WHERE id=?',
                   (datetime.now(timezone.utc).isoformat(), status, cycle))
    return status


def main(monitor, argv):
    parser = argparse.ArgumentParser()
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument('--once', action='store_true')
    modes.add_argument('--due', action='store_true')
    modes.add_argument('--diagnose', action='store_true')
    modes.add_argument('--migrate', metavar='JSON')
    modes.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    directory = data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    database = directory / 'state.db'
    with exclusive_process(directory / 'run.lock') as acquired:
        if not acquired:
            print('BUSY: another local cycle holds the lock')
            return
        if not database.exists() and not args.migrate:
            raise RuntimeError('State not initialized: run --migrate with the existing JSON first')
        store = SQLiteStore(database)
        if args.migrate:
            print(json.dumps(store.import_json(args.migrate)))
            store.backup(directory / 'backups')
            return
        if args.diagnose:
            print(json.dumps(diagnostic(store), indent=2))
            return
        monitor.StateStore = SQLiteStore
        monitor.STATE_FILE = str(database)
        monitor.HEALTH_REPORT_FILE = str(directory / 'cycle_health.json')
        if args.dry_run:
            os.environ['JOB_FINDER_SIMULATION'] = '1'
            # A private copy prevents simulated notifications from changing live state.
            import sqlite3
            from contextlib import closing
            with tempfile.TemporaryDirectory(prefix='job-finder-simulation-') as temp:
                copied = Path(temp) / 'state.db'
                with closing(sqlite3.connect(database)) as src, closing(sqlite3.connect(copied)) as dst:
                    src.backup(dst)
                monitor.STATE_FILE = str(copied)
                monitor.HEALTH_REPORT_FILE = str(Path(temp) / 'health.json')
                class SilentNotifier:
                    def __init__(self, *a, **kw):
                        pass
                    def send_job_alert(self, job):
                        return True
                    def send_heartbeat(self, *a, **kw):
                        return False
                monitor.TelegramNotifier = SilentNotifier
                monitor.ResendEmailNotifier = SilentNotifier
                monitor.run_check()
            print('SIMULATION: notifications suppressed; production state unchanged')
            return
        print(execute_cycle(monitor, store, args.due))

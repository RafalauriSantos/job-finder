"""Transactional compatibility adapter while the Python pipeline is migrated."""
import hashlib
import json
import sqlite3
import time
from contextlib import closing, contextmanager
from datetime import datetime, timezone
from pathlib import Path

from storage.state_store import StateStore


class SQLiteStore(StateStore):
    def __init__(self, filepath):
        self.filepath = str(filepath)
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            if db.execute('PRAGMA quick_check').fetchone()[0] != 'ok':
                raise sqlite3.DatabaseError('State integrity check failed')
            db.executescript('''
                CREATE TABLE IF NOT EXISTS metadata(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS claims(fingerprint TEXT PRIMARY KEY, expires REAL NOT NULL);
                CREATE TABLE IF NOT EXISTS events(id INTEGER PRIMARY KEY, kind TEXT NOT NULL, payload TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS cycles(id INTEGER PRIMARY KEY, started TEXT NOT NULL,
                    finished TEXT, status TEXT NOT NULL, revision TEXT);
                CREATE TABLE IF NOT EXISTS channel_attempts(id INTEGER PRIMARY KEY,
                    fingerprint TEXT NOT NULL, channel TEXT NOT NULL, status TEXT NOT NULL,
                    created TEXT NOT NULL);
                CREATE TABLE IF NOT EXISTS outbox(fingerprint TEXT PRIMARY KEY, payload TEXT NOT NULL,
                    status TEXT NOT NULL, attempts INTEGER NOT NULL DEFAULT 0, retry_at REAL NOT NULL DEFAULT 0);
                CREATE TABLE IF NOT EXISTS jobs(source TEXT NOT NULL, external_id TEXT NOT NULL,
                    payload TEXT NOT NULL, PRIMARY KEY(source,external_id));
            ''')
            db.execute("INSERT OR IGNORE INTO metadata VALUES ('state', ?)",
                       (json.dumps({'seen_ids': [], 'seen_fingerprints': [], 'last_heartbeat': ''}),))
        self.state = self._load()

    @contextmanager
    def connect(self):
        db = sqlite3.connect(self.filepath, timeout=10)
        try:
            db.execute('PRAGMA synchronous=FULL')
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    def _load(self):
        with self.connect() as db:
            self._snapshot = db.execute("SELECT value FROM metadata WHERE key='state'").fetchone()[0]
        return json.loads(self._snapshot)

    def _persist(self, db):
        value = json.dumps(self.state, ensure_ascii=False)
        changed = db.execute("UPDATE metadata SET value=? WHERE key='state' AND value=?",
                             (value, self._snapshot)).rowcount
        if not changed:
            raise RuntimeError('State changed concurrently; refusing to overwrite')
        return value

    def save(self):
        with self.connect() as db:
            value = self._persist(db)
        self._snapshot = value

    def claim_delivery(self, fingerprint, now=None, lease_seconds=600):
        now = time.time() if now is None else now
        with self.connect() as db:
            db.execute('DELETE FROM claims WHERE expires <= ?', (now,))
            if fingerprint in self.state.get('seen_fingerprints', []):
                return False
            claimed = db.execute('INSERT OR IGNORE INTO claims VALUES (?, ?)',
                                 (fingerprint, now + lease_seconds)).rowcount
            if not claimed:
                return False
            value = self._persist(db)
        self._snapshot = value
        return True

    def release_delivery_claim(self, fingerprint):
        with self.connect() as db:
            value = self._persist(db)
            db.execute('DELETE FROM claims WHERE fingerprint=?', (fingerprint,))
        self._snapshot = value

    def event(self, kind, payload):
        with self.connect() as db:
            db.execute('INSERT INTO events(kind,payload) VALUES (?,?)',
                       (kind, json.dumps(payload, ensure_ascii=False)))

    def record_decision(self, *args, **kwargs):
        super().record_decision(*args, **kwargs)
        self.event('decision', self.state['recent_decisions'][-1])
        self.save()

    def record_source_health(self, *args, **kwargs):
        super().record_source_health(*args, **kwargs)
        self.event('source_health', self.state['source_health'][-1])
        self.save()

    def record_llm_call(self):
        result = super().record_llm_call()
        self.save()
        return result

    def record_delivery(self, fingerprint, source_ids, delivered):
        super().record_delivery(fingerprint, source_ids, delivered)
        self.release_delivery_claim(fingerprint)

    def record_channel(self, fingerprint, channel, status):
        with self.connect() as db:
            db.execute('INSERT INTO channel_attempts(fingerprint,channel,status,created) VALUES (?,?,?,?)',
                       (fingerprint, channel, status, datetime.now(timezone.utc).isoformat()))

    def remember_job(self, job):
        from dataclasses import asdict
        payload = json.dumps(asdict(job), ensure_ascii=False)
        with self.connect() as db:
            for source, item in job.sources.items():
                db.execute('INSERT INTO jobs VALUES (?,?,?) ON CONFLICT(source,external_id) '
                           'DO UPDATE SET payload=excluded.payload', (source, item.source_job_id, payload))

    def enqueue(self, job):
        from dataclasses import asdict
        with self.connect() as db:
            db.execute("INSERT OR IGNORE INTO outbox(fingerprint,payload,status) VALUES (?,?,'PENDING')",
                       (job.fingerprint, json.dumps(asdict(job), ensure_ascii=False)))

    def pending_jobs(self):
        from models.job import Job, JobSource
        with self.connect() as db:
            rows = db.execute("SELECT payload FROM outbox WHERE status IN ('PENDING','FAILED') "
                              'AND attempts < 3 AND retry_at <= ?', (time.time(),)).fetchall()
        jobs = []
        for row in rows:
            data = json.loads(row[0])
            data['sources'] = {key: JobSource(**value) for key, value in data['sources'].items()}
            jobs.append(Job(**data))
        return jobs

    def import_json(self, source):
        raw = Path(source).read_bytes()
        digest = hashlib.sha256(raw).hexdigest()
        data = json.loads(raw)
        if isinstance(data, list):
            data = {'seen_ids': data}
        if not isinstance(data, dict):
            raise ValueError('Unsupported legacy state')
        for key in ('seen_ids', 'seen_fingerprints'):
            if key in data and not isinstance(data[key], list):
                raise ValueError(f'Invalid legacy field: {key}')
        with self.connect() as db:
            imported = db.execute("SELECT value FROM metadata WHERE key='legacy_import'").fetchone()
            if imported:
                if imported[0] != digest:
                    raise ValueError('Different legacy state already imported')
                return {'imported': False}
            if self.state.get('seen_fingerprints') or self.state.get('deliveries'):
                raise ValueError('Migration requires an empty destination')
            backup = Path(self.filepath).with_suffix('.legacy.json')
            if backup.exists():
                if backup.read_bytes() != raw:
                    raise ValueError('Legacy backup differs; refusing to replace it')
            else:
                with backup.open('xb') as handle:
                    handle.write(raw)
            data['legacy_seen_ids'] = list(dict.fromkeys(str(x) for x in data.pop('seen_ids', [])))
            data['seen_ids'] = []
            data.pop('delivery_claims', None)
            self.state.update(data)
            value = self._persist(db)
            db.execute("INSERT INTO metadata VALUES ('legacy_import', ?)", (digest,))
        self._snapshot = value
        return {'imported': True, 'legacy_ids': len(data['legacy_seen_ids']),
                'fingerprints': len(data.get('seen_fingerprints', []))}

    def backup(self, directory):
        directory = Path(directory)
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"state-{datetime.now(timezone.utc):%Y-%m-%d}.db"
        if not target.exists():
            temporary = target.with_suffix('.tmp')
            with closing(sqlite3.connect(self.filepath)) as source, closing(sqlite3.connect(temporary)) as dest:
                source.backup(dest)
                if dest.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise sqlite3.DatabaseError('Backup integrity check failed')
            temporary.replace(target)
        with closing(sqlite3.connect(target)) as restored:
            if restored.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise sqlite3.DatabaseError('Existing backup integrity check failed')
        for old in sorted(directory.glob('state-*.db'), reverse=True)[7:]:
            old.unlink()
        return target

"""Small operator CLI for WorkHunter investigation data."""
import argparse
import json
import os
from pathlib import Path

from storage.sqlite_store import SQLiteStore
from core.source_identity import extract_source_identity


def diagnose(store):
    """Classify manually found cases using durable collection and decision evidence."""
    with store.connect() as db:
        manual = db.execute('''SELECT url,normalized_url,source,native_id,identity_status,manual_found_at
                               FROM manual_cases ORDER BY manual_found_at''').fetchall()
        jobs = db.execute('SELECT source,external_id,payload FROM jobs').fetchall()
        attempts = db.execute('SELECT source,native_ids,error_type,http_status,timed_out FROM collection_attempts').fetchall()
        decisions = [json.loads(row[0]) for row in db.execute(
            "SELECT payload FROM events WHERE kind='decision'").fetchall()]

    job_keys = {(str(source), str(external_id)) for source, external_id, _ in jobs}
    job_urls = set()
    for _, _, payload in jobs:
        try:
            data = json.loads(payload)
            for source in data.get('sources', {}).values():
                job_urls.add(extract_source_identity(source.get('url', '')).normalized_url)
        except (TypeError, ValueError):
            continue
    attempt_keys = set()
    for source, native_ids, *_ in attempts:
        try:
            attempt_keys.update((str(source), str(value)) for value in json.loads(native_ids))
        except (TypeError, ValueError):
            pass

    output = []
    for url, normalized, source, native_id, identity_status, found_at in manual:
        key = (str(source), str(native_id)) if native_id else None
        collected = (key in job_keys if key else normalized in job_urls) if (key or normalized) else False
        seen_by_collection = key in attempt_keys if key else normalized in job_urls
        matching = [item for item in decisions if (
            str(item.get('source')) == str(source) and
            (str(item.get('job_id')) == str(native_id) if native_id else item.get('raw_url') == url)
        )]
        if matching:
            decision = matching[-1].get('decision', '')
            classification = 'approved_or_notified' if decision in {'DELIVERED', 'DELIVERY_FAILED'} else 'collected_discarded'
        elif collected:
            classification = 'collected_no_decision'
        elif seen_by_collection:
            classification = 'seen_in_collection_not_persisted'
        elif identity_status == 'identity_unresolved':
            classification = 'identity_unresolved'
        else:
            classification = 'not_collected'
        output.append({'url': url, 'source': source, 'native_id': native_id,
                       'identity_status': identity_status, 'manual_found_at': found_at,
                       'classification': classification})
    return output


def main(argv=None):
    parser = argparse.ArgumentParser(prog='workhunter')
    sub = parser.add_subparsers(dest='command', required=True)
    add = sub.add_parser('add', help='register a manually found job URL')
    add.add_argument('url')
    sub.add_parser('diagnose', help='classify manually found URLs against collection evidence')
    sub.add_parser('worker-once', help='run one isolated manual analysis cycle')
    sub.add_parser('health', help='show operational health checks')
    args = parser.parse_args(argv)
    if args.command == 'add':
        data_dir = Path(os.getenv('JOB_FINDER_DATA_DIR', Path.home() / '.job-finder'))
        SQLiteStore(data_dir / 'state.db').record_manual_case(args.url)
        print('manual case registered')
        return 0
    if args.command == 'diagnose':
        data_dir = Path(os.getenv('JOB_FINDER_DATA_DIR', Path.home() / '.job-finder'))
        result = diagnose(SQLiteStore(data_dir / 'state.db'))
        if not result:
            print('no manual cases registered')
        else:
            for item in result:
                print(f"{item['classification']}: {item['source']}:{item['native_id'] or '-'} {item['url']}")
        return 0
    if args.command == 'worker-once':
        from workhunter_worker import run as run_worker
        return run_worker()
    if args.command == 'health':
        from core.health import health_snapshot
        data_dir = Path(os.getenv('JOB_FINDER_DATA_DIR', Path.home() / '.job-finder'))
        print(json.dumps(health_snapshot(SQLiteStore(data_dir / 'state.db'), data_dir), ensure_ascii=False, indent=2))
        return 0
    return 2


if __name__ == '__main__':
    raise SystemExit(main())

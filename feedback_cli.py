"""Registra feedback humano sobre uma vaga e imprime sinais de recalibracao.

Exemplo:
  python feedback_cli.py --fingerprint ABC --feedback applied --note "candidatei"
  python feedback_cli.py --report
"""

import argparse
import json
from pathlib import Path

from core.recalibration import build_recalibration_report
from storage.state_store import StateStore
from storage.sqlite_store import SQLiteStore


def default_state_path() -> str:
    return str(Path.home() / "AppData" / "Local" / "JobFinder" / "state.db")


def main() -> int:
    parser = argparse.ArgumentParser(description="Feedback do radar de vagas")
    parser.add_argument("--state", default=default_state_path())
    parser.add_argument("--fingerprint")
    parser.add_argument("--feedback", choices=["applied", "not_applied", "interview", "rejected", "irrelevant", "hired"])
    parser.add_argument("--note", default="")
    parser.add_argument("--report", action="store_true")
    parser.add_argument("--recent", action="store_true", help="lista vagas recentes para feedback")
    args = parser.parse_args()
    store = SQLiteStore(args.state) if str(args.state).lower().endswith(".db") else StateStore(args.state)
    if args.recent:
        entries = []
        if isinstance(store, SQLiteStore):
            import sqlite3
            with sqlite3.connect(store.filepath) as connection:
                rows = connection.execute(
                    "SELECT fingerprint,payload,status FROM outbox ORDER BY rowid DESC LIMIT 20"
                ).fetchall()
            for fingerprint, payload, status in rows:
                data = json.loads(payload)
                entries.append({
                    "fingerprint": fingerprint,
                    "status": status,
                    "title": data.get("title", ""),
                    "company": data.get("company", ""),
                    "source": next(iter(data.get("sources", {})), "unknown"),
                    "score": data.get("match_score", 0),
                })
        else:
            for delivery in reversed(store.state.get("deliveries", [])[-20:]):
                entries.append(delivery)
        print(json.dumps(entries, ensure_ascii=False, indent=2))
        return 0
    if args.report:
        print(json.dumps(build_recalibration_report(store.state), ensure_ascii=False, indent=2))
        return 0
    if not args.fingerprint or not args.feedback:
        parser.error("--fingerprint e --feedback sao obrigatorios, exceto com --report")
    store.record_feedback(args.fingerprint, args.feedback, args.note)
    store.save()
    print(json.dumps(store.feedback_summary(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

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
    args = parser.parse_args()
    store = SQLiteStore(args.state) if str(args.state).lower().endswith(".db") else StateStore(args.state)
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

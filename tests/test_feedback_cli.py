import json
import sqlite3

from feedback_cli import main


def test_feedback_cli_records_feedback(monkeypatch, tmp_path, capsys):
    state = tmp_path / "state.json"
    monkeypatch.setattr("sys.argv", ["feedback_cli.py", "--state", str(state), "--fingerprint", "fp", "--feedback", "applied"])
    assert main() == 0
    assert json.loads(state.read_text(encoding="utf-8"))["feedback"][0]["feedback"] == "applied"


def test_feedback_cli_prints_report(monkeypatch, tmp_path, capsys):
    state = tmp_path / "state.json"
    state.write_text(json.dumps({"feedback": [], "recent_decisions": []}), encoding="utf-8")
    monkeypatch.setattr("sys.argv", ["feedback_cli.py", "--state", str(state), "--report"])
    assert main() == 0
    assert "feedback_count" in capsys.readouterr().out


def test_feedback_cli_defaults_to_production_sqlite(monkeypatch, tmp_path, capsys):
    from feedback_cli import default_state_path
    db = tmp_path / "state.db"
    monkeypatch.setattr("feedback_cli.default_state_path", lambda: str(db))
    monkeypatch.setattr("sys.argv", ["feedback_cli.py", "--fingerprint", "fp-1", "--feedback", "applied"])

    assert main() == 0
    with sqlite3.connect(db) as connection:
        state = json.loads(connection.execute("select value from metadata where key='state'").fetchone()[0])
    assert state["feedback"][0]["fingerprint"] == "fp-1"


def test_feedback_cli_lists_recent_sqlite_jobs(monkeypatch, tmp_path, capsys):
    from storage.sqlite_store import SQLiteStore
    db = tmp_path / "state.db"
    store = SQLiteStore(db)
    store.enqueue(__import__("models.job", fromlist=["Job"]).Job(title="Dev Java", company="Empresa", workplace_type="remote", match_score=80))
    monkeypatch.setattr("feedback_cli.default_state_path", lambda: str(db))
    monkeypatch.setattr("sys.argv", ["feedback_cli.py", "--recent"])

    assert main() == 0
    assert "Dev Java" in capsys.readouterr().out

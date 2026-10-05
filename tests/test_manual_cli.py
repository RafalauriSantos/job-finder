def test_manual_cli_add_records_url(tmp_path, monkeypatch):
    from workhunter_cli import main
    monkeypatch.setenv('JOB_FINDER_DATA_DIR', str(tmp_path))
    assert main(['add', 'https://www.linkedin.com/jobs/view/456/?trk=foo']) == 0
    from storage.sqlite_store import SQLiteStore
    store = SQLiteStore(tmp_path / 'state.db')
    with store.connect() as db:
        row = db.execute('SELECT native_id,source FROM manual_cases').fetchone()
        queue = db.execute('SELECT status FROM manual_analysis_queue').fetchone()
    assert row == ('456', 'linkedin')
    assert queue == ('PENDING',)

from core.linkedin_ingest import CapturedOpportunity, RateController, content_fingerprint, extract_post_body, looks_like_opportunity, normalize_url
from collectors.manual_collector import ManualCollector
from storage.sqlite_store import SQLiteStore


def test_capture_normalizes_tracking_and_has_stable_fingerprint():
    assert normalize_url("https://www.linkedin.com/feed/update/urn:li:activity:1?trk=x") == "https://www.linkedin.com/feed/update/urn:li:activity:1"
    assert content_fingerprint("https://x.test/a?trk=1", "x") == content_fingerprint("https://x.test/a?trk=2", "x")
    assert content_fingerprint("https://www.linkedin.com/feed/", "Vaga Dev 1") != content_fingerprint("https://www.linkedin.com/feed/", "Vaga Dev 2")
    assert content_fingerprint("https://www.linkedin.com/feed/", "VAGA\nDev", "A") == content_fingerprint("https://www.linkedin.com/feed/", "VAGA Dev", "B")


def test_only_recruitment_technical_posts_are_forwarded():
    assert looks_like_opportunity("Estamos contratando Desenvolvedor JavaScript Júnior")
    assert not looks_like_opportunity("Artigo sobre carreira e tecnologia")
    assert not looks_like_opportunity(extract_post_body("Publicação no feed\nValter Silva\nJava | React\n4 min •\nSeguir\nMinha história com vaga de estágio"))
    assert looks_like_opportunity(extract_post_body("Publicação no feed\nJessica Oliveira\nHeadhunter\n1 d •\nSeguir\nVAGA | DESENVOLVEDOR JÚNIOR"))


def test_capture_payload_is_pipeline_compatible():
    payload = CapturedOpportunity("https://linkedin.com/post/1", "Vaga de API Developer remoto").payload()
    assert payload["source"] == "linkedin"
    assert payload["source_type"] == "post"
    assert payload["fingerprint"]


def test_rate_controller_enforces_interval_and_hourly_limit():
    controller = RateController(max_actions_per_hour=1, min_interval_seconds=120)
    assert controller.allow(1000)
    controller.record(1000)
    assert not controller.allow(1001)
    assert not controller.allow(2000)


def test_captured_post_reaches_existing_job_pipeline(tmp_path):
    store = SQLiteStore(tmp_path / 'state.db')
    text = ('Publicação no feed\n200DEV\nEstamos contratando!\n'
            'Desenvolvedor Júnior - Integrações\n100% remoto no Brasil\n'
            'Experiência com APIs REST e webhooks.')
    queue_id = store.record_manual_case('https://www.linkedin.com/feed/', source='linkedin',
        native_id=content_fingerprint('https://www.linkedin.com/feed/', text), raw_text=text, author='200DEV')
    class NeverFetch:
        def get(self, *_args, **_kwargs):
            raise AssertionError('captured text must not be fetched again')
    jobs = ManualCollector(NeverFetch(), store).collect()
    assert len(jobs) == 1
    assert 'Desenvolvedor Júnior' in jobs[0].title
    assert jobs[0].description == text
    assert jobs[0].company == '200DEV'
    assert jobs[0].workplace_type == 'remote'
    with store.connect() as db:
        assert db.execute('SELECT status,result FROM manual_analysis_queue WHERE id=?', (queue_id,)).fetchone() == ('DONE', 'FULL_EVIDENCE')

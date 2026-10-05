from core.source_identity import extract_source_identity, normalize_job_url


def test_linkedin_tracking_params_do_not_change_identity():
    first = extract_source_identity('https://www.linkedin.com/jobs/view/123456789/?trk=feed&position=2')
    second = extract_source_identity('https://www.linkedin.com/jobs/view/123456789?utm_source=x')
    assert first.native_id == second.native_id == '123456789'
    assert first.normalized_url == second.normalized_url == 'https://www.linkedin.com/jobs/view/123456789'


def test_unknown_url_is_kept_but_identity_is_explicitly_unresolved():
    identity = extract_source_identity('https://example.com/jobs/backend?utm_campaign=x')
    assert identity.normalized_url == 'https://example.com/jobs/backend'
    assert identity.native_id is None
    assert identity.identity_status == 'identity_unresolved'

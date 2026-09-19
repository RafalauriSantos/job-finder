from datetime import datetime, timezone

from core.normalizer import normalize_published_at, publication_age_bucket


def test_normalizes_iso_and_epoch_publication_dates():
    assert normalize_published_at("2026-09-19T10:00:00Z") == "2026-09-19T10:00:00+00:00"
    assert normalize_published_at(1789812000) == "2026-09-19T10:00:00+00:00"


def test_classifies_publication_age_and_unknown_date():
    now = datetime(2026, 9, 19, 12, tzinfo=timezone.utc)

    assert publication_age_bucket("2026-09-19T10:00:00Z", now=now) == "recent"
    assert publication_age_bucket("2026-09-15T10:00:00Z", now=now) == "old"
    assert publication_age_bucket("", now=now) == "unknown"

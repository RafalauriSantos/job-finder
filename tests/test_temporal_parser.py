import os
import sys
from datetime import datetime, timezone, timedelta
import pytest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from collectors.rss_collector import parse_feed_datetime, classify_freshness


def test_parse_rfc822_date():
    raw = "Sun, 13 Sep 2026 18:00:00 GMT"
    dt = parse_feed_datetime(raw)
    assert dt is not None
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2026
    assert dt.month == 9
    assert dt.day == 13
    assert dt.hour == 18


def test_parse_iso8601_date():
    raw = "2026-09-13T18:00:00Z"
    dt = parse_feed_datetime(raw)
    assert dt is not None
    assert dt.tzinfo == timezone.utc
    assert dt.year == 2026
    assert dt.month == 9
    assert dt.day == 13


def test_parse_invalid_date_returns_none():
    assert parse_feed_datetime("data_invalida_123") is None
    assert parse_feed_datetime("") is None


def test_classify_freshness_fresh():
    now_utc = datetime.now(timezone.utc)
    recent = now_utc - timedelta(hours=24)
    status, reason = classify_freshness(recent, max_age_hours=72)
    assert status == "FRESH"


def test_classify_freshness_stale():
    now_utc = datetime.now(timezone.utc)
    old = now_utc - timedelta(hours=96)
    status, reason = classify_freshness(old, max_age_hours=72)
    assert status == "STALE"
    assert "superior a 72h" in reason


def test_classify_freshness_unknown():
    status, reason = classify_freshness(None)
    assert status == "UNKNOWN"
    assert "Data ausente" in reason

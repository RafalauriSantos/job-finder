from datetime import timedelta


def interval_at(now, configured_minutes=60):
    """Use the configured cadence; it must be short enough for the source window."""
    return timedelta(minutes=max(1, int(configured_minutes or 60)))


def is_due(now, last_started, configured_minutes=60):
    return last_started is None or now >= last_started + interval_at(now, configured_minutes)

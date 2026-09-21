from datetime import timedelta
from zoneinfo import ZoneInfo


def interval_at(now):
    local = now.astimezone(ZoneInfo('America/Sao_Paulo'))
    return timedelta(hours=1 if local.weekday() >= 5 else 3)


def is_due(now, last_started):
    return last_started is None or now >= last_started + interval_at(now)

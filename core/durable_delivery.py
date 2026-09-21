import time

from core.delivery_workflow import finalize_delivery


def deliver(store, job, source_ids, telegram, email):
    store.enqueue(job)
    with store.connect() as db:
        changed = db.execute("UPDATE outbox SET status='SENDING',attempts=attempts+1 "
                             "WHERE fingerprint=? AND status IN ('PENDING','FAILED') "
                             'AND attempts < 3 AND retry_at <= ?', (job.fingerprint, time.time())).rowcount
    if not changed:
        return False
    sent = False
    outcome = 'FAILED'
    for channel, notifier in [('telegram', telegram), ('email', email)]:
        # Persist uncertainty BEFORE the external side effect.
        with store.connect() as db:
            attempt = db.execute('INSERT INTO channel_attempts(fingerprint,channel,status,created) '
                                 "VALUES (?,?,'UNKNOWN',datetime('now'))", (job.fingerprint, channel)).lastrowid
        try:
            sent = notifier.send_job_alert(job)
            outcome = 'DELIVERED' if sent else getattr(notifier, 'last_status', 'UNKNOWN')
        except Exception:
            outcome = 'UNKNOWN'
        with store.connect() as db:
            db.execute('UPDATE channel_attempts SET status=? WHERE id=?', (outcome, attempt))
        if sent or outcome == 'UNKNOWN':
            break
    with store.connect() as db:
        db.execute('UPDATE outbox SET status=?,retry_at=? WHERE fingerprint=?',
                   (outcome, time.time() + 300, job.fingerprint))
    if outcome != 'UNKNOWN':
        finalize_delivery(store, job, source_ids, sent, job.match_score,
                          job.match_reasons[0] if job.match_reasons else 'Approved')
    return sent

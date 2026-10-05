"""Minimal inbound Telegram adapter for manual job URLs."""
import re
import json
from urllib.parse import urlparse, parse_qs, unquote

URL_RE = re.compile(r'https?://[^\s<>]+', re.IGNORECASE)
LINKEDIN_HOSTS = {'linkedin.com', 'www.linkedin.com', 'lnkd.in'}


def _safe_linkedin_url(url):
    parsed = urlparse(url or '')
    host = (parsed.hostname or '').lower().rstrip('.')
    return (parsed.scheme.lower() in {'http', 'https'} and
            (host in LINKEDIN_HOSTS or host.endswith('.linkedin.com')) and
            host not in {'localhost', '127.0.0.1', '::1', '0.0.0.0'})


def extract_job_urls(text):
    return [url.rstrip('.,);]}>') for url in URL_RE.findall(text or '')
            if urlparse(url).scheme in {'http', 'https'}]


def resolve_linkedin_share(url, http):
    """Follow LinkedIn's safety wrapper/short link to expose the job URL."""
    parsed = urlparse(url)
    nested = parse_qs(parsed.query).get('url', [])
    candidate = unquote(nested[0]) if nested else url
    if not (_safe_linkedin_url(url) and _safe_linkedin_url(candidate)):
        return url
    try:
        response = http.get(candidate, allow_redirects=True, timeout=10,
                            headers={'User-Agent': 'Mozilla/5.0'})
        resolved = getattr(response, 'url', '') or candidate
        return resolved if _safe_linkedin_url(resolved) else ''
    except Exception:
        return candidate


def poll_manual_urls(store, http, token, chat_id, allowed_user_id=None):
    """Consume authorized messages and register URLs; returns number registered."""
    if not token or not chat_id or http is None:
        return 0
    with store.connect() as db:
        row = db.execute("SELECT value FROM metadata WHERE key='telegram_update_offset'").fetchone()
        offset = int(row[0]) if row else 0
    response = http.get(f'https://api.telegram.org/bot{token}/getUpdates',
                        params={'offset': offset, 'timeout': 0, 'allowed_updates': '["message"]'}, timeout=10)
    if response.status_code != 200:
        return 0
    updates = response.json().get('result', [])
    registered = 0
    next_offset = offset
    for update in updates:
        next_offset = max(next_offset, int(update.get('update_id', 0)) + 1)
        message = update.get('message', {})
        sender_chat = str(message.get('chat', {}).get('id', ''))
        if sender_chat != str(chat_id):
            continue
        if allowed_user_id and str(message.get('from', {}).get('id', '')) != str(allowed_user_id):
            continue
        for url in extract_job_urls(message.get('text', '')):
            resolved_url = resolve_linkedin_share(url, http)
            if not resolved_url:
                continue
            queue_id = store.record_manual_case(resolved_url)
            registered += 1
            response = http.post(f'https://api.telegram.org/bot{token}/sendMessage',
                      json={'chat_id': chat_id, 'text': '🔎 Link recebido. Identificando a fonte e iniciando a análise...'}, timeout=10)
            try:
                message_id = response.json()['result']['message_id']
                with store.connect() as db:
                    db.execute('UPDATE manual_analysis_queue SET telegram_chat_id=?,telegram_message_id=? WHERE id=?',
                               (str(chat_id), message_id, queue_id))
            except (ValueError, KeyError, TypeError):
                pass
    if next_offset != offset:
        with store.connect() as db:
            db.execute("INSERT INTO metadata(key,value) VALUES('telegram_update_offset',?) "
                       "ON CONFLICT(key) DO UPDATE SET value=excluded.value", (str(next_offset),))
    return registered


def notify_finished_manual_analyses(store, http, token):
    if not token or http is None:
        return 0
    with store.connect() as db:
        rows = db.execute('''SELECT q.id,q.telegram_chat_id,q.telegram_message_id,q.result,q.error,
            c.source,c.native_id,c.normalized_url FROM manual_analysis_queue q
            JOIN manual_cases c ON c.id=q.manual_case_id
            WHERE q.status IN ('DONE','FAILED') AND q.notified_at IS NULL
            AND q.telegram_chat_id IS NOT NULL''').fetchall()
        decisions = [json.loads(row[0]) for row in db.execute("SELECT payload FROM events WHERE kind='decision'").fetchall()]
    sent = 0
    for qid, chat, message, result, error, source, native_id, url in rows:
        candidate_ids = {str(native_id), f'{source}:{native_id}'}
        matches = [d for d in decisions if str(d.get('job_id')) in candidate_ids and d.get('source') == source]
        decision = matches[-1] if matches else None
        if decision:
            label = decision.get('decision', 'UNKNOWN')
            reason = decision.get('decision_reason', 'não informado')
            if label == 'DISCARD_LOCATION':
                text = ("⚠️ Esta vaga foi descartada pelo filtro de localização.\n\n"
                        f"Motivo: {reason}\n\n"
                        "A modalidade remota não ficou confirmada ou a localidade está fora da região aceita.")
            elif label == 'DISCARD_LOW_EVIDENCE':
                text = ("⚠️ Não consegui confirmar informações suficientes sobre esta vaga.\n\n"
                        f"Motivo: {reason}\n\n"
                        "O LinkedIn não liberou detalhes públicos suficientes para uma avaliação segura.")
            else:
                text = f"{'✅' if label in {'DELIVERED','APPROVED'} else '❌'} Análise concluída.\n\nDecisão: {label}\nScore: {decision.get('final_score', 'N/D')}\nMotivo: {reason}"
        elif error:
            text = f"⚠️ Não consegui concluir a análise.\n\nEtapa: busca da vaga\nMotivo: {error}"
        else:
            seen_ids = {str(value) for value in store.state.get('seen_ids', [])}
            if str(native_id) in seen_ids or f'{source}:{native_id}' in seen_ids:
                text = ('ℹ️ Esta vaga já havia sido processada anteriormente.\n\n'
                        'Ela foi ignorada agora para evitar duplicidade.\n'
                        f'Evidência obtida: {result or "não registrada"}.')
            else:
                text = ('⚠️ A vaga foi buscada, mas a decisão final não foi registrada.\n\n'
                        f'Evidência obtida: {result or "não registrada"}.\n'
                        'Ela ficará disponível para nova tentativa.')
        response = http.post(f'https://api.telegram.org/bot{token}/editMessageText',
                             json={'chat_id': chat, 'message_id': message, 'text': text}, timeout=10)
        if response.status_code == 200:
            with store.connect() as db:
                db.execute('UPDATE manual_analysis_queue SET notified_at=datetime(?) WHERE id=?',
                           ('now', qid))
            sent += 1
    return sent

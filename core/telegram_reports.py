"""Read-only Telegram reports built from durable WorkHunter cycle data."""
from __future__ import annotations

import json
import unicodedata
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo


LOCAL_ZONE = ZoneInfo("America/Sao_Paulo")


def _parse(value):
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(value)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except (TypeError, ValueError):
        return None


def _rows(store, limit=20000):
    with store.connect() as db:
        return db.execute(
            "SELECT id,started,finished,status,report,mode FROM cycles ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()


def _reports_for_day(store, now=None):
    now = now or datetime.now(timezone.utc)
    local_now = now.astimezone(LOCAL_ZONE)
    start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
    result = []
    for cycle_id, started, finished, status, raw_report, mode in _rows(store):
        parsed = _parse(started)
        if parsed and parsed.astimezone(LOCAL_ZONE).date() == start.date():
            try:
                report = json.loads(raw_report) if raw_report else {}
            except (TypeError, ValueError):
                report = {}
            # Older manual-only cycles predate the mode column. Their empty,
            # zero-duration reports are excluded from the collection report.
            legacy_empty_manual = (
                not mode and report.get('duration_seconds', 0) == 0
                and _number(report, 'funnel', 'raw') == 0
            )
            if legacy_empty_manual:
                continue
            result.append({
                'id': cycle_id, 'started': started, 'finished': finished,
                'status': status, 'report': report, 'mode': mode or 'scheduled',
            })
    return result


def _number(report, *path):
    value = report
    for key in path:
        if not isinstance(value, dict):
            return 0
        value = value.get(key, 0)
    return value if isinstance(value, (int, float)) else 0


def _friendly_datetime(value):
    parsed = _parse(value)
    if not parsed:
        return 'horário desconhecido'
    local = parsed.astimezone(LOCAL_ZONE)
    return local.strftime('%d/%m às %H:%M')


def _friendly_status(value):
    return {
        'COMPLETED': 'Concluído', 'DEGRADED': 'Concluído com alertas',
        'FAILED': 'Falhou', 'INTERRUPTED': 'Interrompido',
        'RUNNING': 'Em andamento', 'SUCCESS': 'Normal', 'OK': 'Normal',
        'NOT_CONFIGURED': 'Não configurada',
    }.get(value, str(value or 'Indisponível').replace('_', ' ').title())


def _friendly_source(value):
    return {
        'linkedin': 'LinkedIn', 'gupy': 'Gupy', 'github': 'GitHub',
        'geekhunter': 'GeekHunter', 'trampos': 'Trampos', 'rss': 'RSS',
    }.get(str(value).lower(), str(value).replace('_', ' ').title())


def _friendly_decision(value):
    return {
        'DISCARD_SCOPE': 'Descartada por compatibilidade',
        'DISCARD_LOCATION': 'Descartada por localização',
        'DISCARD_LOW_EVIDENCE': 'Descartada por pouca evidência',
        'DISCARD_LOW_SCORE': 'Descartada por pontuação',
        'DISCARD_PCD': 'Descartada pelo filtro PCD',
        'DISCARD_SENIOR_OR_VETO': 'Descartada por senioridade ou relevância',
        'DELIVERED': 'Alerta enviado', 'APPROVED': 'Aprovada',
    }.get(value, str(value or 'Decisão não identificada').replace('_', ' ').title())


def _short_job_id(value):
    value = str(value or 'vaga sem identificador')
    source, separator, identifier = value.partition(':')
    if separator:
        label = _friendly_source(source)
        identifier = identifier or 'identificador não resolvido'
        if len(identifier) > 18:
            identifier = identifier[:14] + '…'
        return f'{label} · {identifier}'
    return value if len(value) <= 22 else value[:18] + '…'


def build_daily_report(store, now=None):
    now = now or datetime.now(timezone.utc)
    cycles = _reports_for_day(store, now)
    raw = unique = notified = 0
    discarded = 0
    llm_calls = fallbacks = 0
    durations = []
    degraded = failed = interrupted = 0
    source_failures = defaultdict(int)
    for cycle in cycles:
        report = cycle['report']
        raw += _number(report, 'funnel', 'raw')
        unique += _number(report, 'funnel', 'unique')
        notified += _number(report, 'funnel', 'notified')
        funnel = report.get('funnel', {})
        discarded += _number(funnel, 'seen')
        for value in (funnel.get('discarded') or {}).values():
            if isinstance(value, (int, float)):
                discarded += value
        # The monitor stores this as a day-to-date counter, so summing it per
        # cycle would double-count. The largest value is the end-of-day total.
        llm_calls = max(llm_calls, _number(report, 'llm_calls_today'))
        fallbacks += _number(report, 'llm_fallbacks')
        duration = report.get('duration_seconds')
        if isinstance(duration, (int, float)):
            durations.append(duration)
        if cycle['status'] == 'DEGRADED':
            degraded += 1
        if cycle['status'] in {'FAILED', 'INTERRUPTED'}:
            failed += 1
        if cycle['status'] == 'INTERRUPTED':
            interrupted += 1
        for source, details in (report.get('sources') or {}).items():
            if isinstance(details, dict) and details.get('status') not in {'SUCCESS', 'OK', 'NOT_CONFIGURED'}:
                source_failures[source] += 1
    average = round(sum(durations) / len(durations), 1) if durations else 0
    return (
        "📊 <b>Relatório do WorkHunter — hoje</b>\n\n"
        f"🕒 <b>Atualizado em:</b> {now.astimezone(LOCAL_ZONE).strftime('%d/%m às %H:%M')}\n"
        "<i>Os números abaixo estão acumulados até este horário.</i>\n\n"
        f"⏱ <b>Operação</b>\n"
        f"• Ciclos concluídos: {len(cycles) - failed}\n"
        f"• Ciclos degradados: {degraded}\n"
        f"• Ciclos com falha: {failed}\n"
        f"• Ciclos interrompidos: {interrupted}\n"
        f"• Duração média: {str(average).replace('.', ',')}s\n\n"
        f"🔎 <b>Vagas</b>\n"
        f"• Encontradas: {raw}\n"
        f"• Únicas: {unique}\n"
        f"• Descartadas: {discarded}\n"
        f"• Alertas enviados: {notified}\n\n"
        f"🤖 <b>Análise</b>\n"
        f"• Chamadas LLM registradas: {llm_calls}\n"
        f"• Análises com fallback heurístico: {fallbacks}\n\n"
        f"⚠️ <b>Problemas</b>\n"
        f"• Fontes degradadas: {', '.join(sorted(source_failures)) or 'nenhuma'}\n"
        f"• Cobertura dos ciclos: {'há ciclos sem relatório final' if interrupted else 'completa'}"
    )


def build_status(store):
    with store.connect() as db:
        cycle = db.execute(
            "SELECT started,finished,status,mode FROM cycles ORDER BY id DESC LIMIT 1"
        ).fetchone()
        pending = db.execute(
            "SELECT COUNT(*) FROM outbox WHERE status!='DELIVERED'"
        ).fetchone()[0]
        manual = db.execute(
            "SELECT COUNT(*) FROM manual_analysis_queue WHERE status='PENDING'"
        ).fetchone()[0]
    if not cycle:
        cycle_text = 'nenhum ciclo registrado ainda'
        cycle_details = ''
    else:
        cycle_text = _friendly_status(cycle[2])
        when = _friendly_datetime(cycle[0])
        kind = 'coleta programada' if cycle[3] != 'manual' else 'análise manual'
        cycle_details = f"\n• Quando: {when} · {kind}"
    return (
        "🩺 <b>Status do WorkHunter</b>\n\n"
        f"• Último ciclo: {cycle_text}{cycle_details}\n"
        f"• Entregas pendentes: {pending}\n"
        f"• Análises manuais pendentes: {manual}\n"
        f"• Banco local: funcionando"
    )


def build_sources(store, now=None):
    cycles = _reports_for_day(store, now)
    stats = defaultdict(lambda: {'cycles': 0, 'discovered': 0, 'failures': 0})
    for cycle in cycles:
        for source, details in (cycle['report'].get('sources') or {}).items():
            if not isinstance(details, dict):
                continue
            stats[source]['cycles'] += 1
            stats[source]['discovered'] += details.get('discovered', 0) or 0
            if details.get('status') not in {'SUCCESS', 'OK', 'NOT_CONFIGURED'}:
                stats[source]['failures'] += 1
    if not stats:
        return ('📡 <b>Fontes</b>\n\n'
                'Ainda não houve uma coleta programada registrada hoje.\n'
                'O monitor está aguardando o próximo horário.')
    lines = ['📡 <b>Fontes — hoje</b>', '']
    for source in sorted(stats):
        item = stats[source]
        status = 'normal' if item['failures'] == 0 else f"{item['failures']} alerta(s)"
        lines.append(f"• {_friendly_source(source)}: {item['discovered']} vagas · {status}")
    return '\n'.join(lines)


def build_latest(store):
    with store.connect() as db:
        rows = db.execute(
            "SELECT payload FROM events WHERE kind='decision' ORDER BY id DESC LIMIT 5"
        ).fetchall()
    lines = ['🧾 <b>Últimas decisões registradas</b>',
             '<i>Histórico recente, independentemente da data.</i>', '']
    for row in rows:
        try:
            item = json.loads(row[0])
        except (TypeError, ValueError):
            continue
        decision = _friendly_decision(item.get('decision'))
        lines.append(f"• {decision}\n  {_short_job_id(item.get('job_id'))}")
        reason = str(item.get('reason') or '').strip()
        if reason:
            lines.append(f"  Motivo: {reason[:120]}{'…' if len(reason) > 120 else ''}")
    return '\n'.join(lines) if len(lines) > 3 else '🧾 <b>Últimas decisões registradas</b>\n\nNenhuma decisão registrada.'


def build_problems(store, now=None):
    cycles = _reports_for_day(store, now)
    problems = []
    for cycle in cycles:
        if cycle['status'] in {'FAILED', 'INTERRUPTED', 'DEGRADED'}:
            problems.append(f"ciclo {cycle['id']}: {_friendly_status(cycle['status'])}")
        for source, details in (cycle['report'].get('sources') or {}).items():
            if isinstance(details, dict) and details.get('status') not in {'SUCCESS', 'OK', 'NOT_CONFIGURED'}:
                problems.append(f"{_friendly_source(source)}: {_friendly_status(details.get('status'))}")
    if not problems:
        return '✅ <b>Problemas</b>\n\nNenhuma falha foi registrada nas coletas programadas de hoje.'
    return '⚠️ <b>Problemas — hoje</b>\n\n' + '\n'.join(f'• {item}' for item in problems[-20:])


def command_response(command, store, now=None):
    command = command.strip().lower().split('@', 1)[0]
    command = ''.join(
        char for char in unicodedata.normalize('NFKD', command)
        if not unicodedata.combining(char)
    )
    if not command.startswith('/'):
        command = '/' + command
    responses = {
        '/start': lambda store: ('👋 <b>Olá! Eu sou o WorkHunter.</b>\n\n'
                                 'Posso monitorar vagas, analisar links e mostrar o estado do sistema.\n\n'
                                 + command_response('/ajuda', store, now)),
        '/relatorio': lambda current_store: build_daily_report(current_store, now),
        '/status': build_status,
        '/fontes': lambda current_store: build_sources(current_store, now),
        '/ultimas': build_latest,
        '/problemas': lambda current_store: build_problems(current_store, now),
    }
    if command == '/ajuda':
        return ('🤖 <b>Comandos do WorkHunter</b>\n\n'
                '• /relatorio — resumo dos ciclos de hoje\n'
                '• /status — situação atual dos serviços e filas\n'
                '• /fontes — desempenho das fontes hoje\n'
                '• /ultimas — últimas decisões do histórico\n'
                '• /problemas — falhas e fontes degradadas\n'
                '• /ajuda — esta lista')
    builder = responses.get(command)
    return builder(store) if builder else None

import json
import os
import sys
import time
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

from models.job import Job
from core.normalizer import is_location_allowed, is_pcd_exclusive
from core.scoring import evaluate_job
from core.deduplicator import Deduplicator
from collectors.gupy_collector import GupyCollector
from collectors.linkedin_collector import LinkedInCollector
from collectors.rss_collector import RssCollector
from collectors.github_collector import GithubIssuesCollector
from collectors.trampos_collector import TramposCollector
from notify.telegram_notifier import TelegramNotifier
from notify.email_notifier import ResendEmailNotifier
from storage.state_store import StateStore
from core.query_planner import plan_searches
from core.delivery_workflow import finalize_delivery
from core.eligibility import classify_score, classify_evidence, classify_location
from core.scope_analyzer import analyze_scope
from core.metrics import summarize_cycle
from core.ranking import order_for_alerts
from collectors.base import collect_result

if os.getenv('JOB_FINDER_LOCAL_RUNTIME') != '1':
    load_dotenv()

# Garante suporte a UTF-8 no console do Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CONFIG_FILE = "config.json"
STATE_FILE = "seen_jobs.json"
HEALTH_REPORT_FILE = "cycle_health.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
ALERT_EMAIL_FROM = os.getenv("ALERT_EMAIL_FROM")
ALERT_EMAIL_TO = os.getenv("ALERT_EMAIL_TO")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def get_http_session() -> requests.Session:
    """Retorna sessão requests com retentativas automáticas e backoff exponencial."""
    session = requests.Session()
    retries = Retry(
        total=3,
        backoff_factor=1.5,
        status_forcelist=[429, 500, 502, 503, 504],
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retries)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


HTTP = get_http_session()


def load_config() -> dict:
    if not os.path.exists(CONFIG_FILE):
        return {"check_interval_minutes": 60, "monitors": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def check_heartbeat(config: dict, store: StateStore, notifier: TelegramNotifier):
    """Verifica se deve enviar o heartbeat diário ao Telegram."""
    hb_cfg = config.get("heartbeat", {})
    if not hb_cfg.get("enabled", False):
        return

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    target_hour = hb_cfg.get("hour_start", 9)

    if store.get_last_heartbeat() == today_str:
        return

    if now.hour >= target_hour:
        monitors_count = len(config.get("monitors", []))
        total_tracked = len(store.state.get("seen_fingerprints", []))
        if notifier.send_heartbeat(monitors_count, total_tracked):
            print(f"[{now.strftime('%H:%M:%S')}] 💚 Heartbeat diário enviado ao Telegram.")
            store.set_last_heartbeat(today_str)
            store.save()


def run_check():
    config = load_config()
    store = StateStore(STATE_FILE)
    notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HTTP)
    email_notifier = ResendEmailNotifier(
        RESEND_API_KEY, ALERT_EMAIL_FROM, ALERT_EMAIL_TO, HTTP
    )
    durable = hasattr(store, 'pending_jobs')
    recovered_deliveries = 0
    if durable:
        from core.durable_delivery import deliver
        for pending in store.pending_jobs():
            ids = [f'{name}:{item.source_job_id}' for name, item in pending.sources.items()]
            recovered_deliveries += int(deliver(store, pending, ids, notifier, email_notifier))
    deduplicator = Deduplicator()
    min_score = config.get("min_match_score", 50)  # Padrão: 50 pts mínimos para alertar
    progression_min_score = config.get("progression_min_score", 35)

    monitors = config.get("monitors", [])
    start_time = time.time()
    now_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{now_str}] Iniciando patrulha com {len(monitors)} monitor(es)...")

    # 1. Agrupa configurações por tipo de coletor
    gupy_queries = []
    linkedin_searches = []
    rss_configs = []
    github_configs = []
    trampos_configs = []

    for m in monitors:
        m_type = m.get("type", "")
        if m_type == "gupy":
            for planned_query in plan_searches([m], "gupy"):
                query_args = {
                    k: v for k, v in planned_query.items()
                    if k not in ["type", "description", "only_remote", "strict_location", "keywords", "exclude_keywords", "query", "query_variants"]
                }
                if "term" not in query_args:
                    query_args["term"] = planned_query["query"]
                if "limit" not in query_args:
                    query_args["limit"] = 20
                query_args["query_id"] = planned_query["query_id"]
                gupy_queries.append(query_args)
        elif m_type == "linkedin":
            for planned_query in plan_searches([m], "linkedin"):
                search = dict(planned_query)
                search["keywords"] = planned_query["query"]
                search["max_pages"] = m.get("max_pages", 3)
                linkedin_searches.append(search)
        elif m_type == "rss":
            rss_configs.append(m)
        elif m_type == "github_issues":
            github_configs.append(m)
        elif m_type == "trampos":
            trampos_configs.append(m)

    # 2. Executa a Coleta (Fase de Descoberta / Recall Alto)
    discovered_gupy = []
    discovered_linkedin = []
    discovered_rss = []
    discovered_github = []
    discovered_trampos = []
    gupy_status = "OK"
    linkedin_status = "OK"
    linkedin_query_stats = []
    gupy_query_stats = []
    rss_status = "OK"
    github_status = "OK"
    trampos_status = "OK"

    if gupy_queries:
        try:
            gupy_col = GupyCollector(
                HTTP,
                gupy_queries,
                detail_limit=config.get("gupy_detail_enrichment_limit", 5),
                max_age_hours=config.get("gupy_max_age_hours", 72),
            )
            result = collect_result(gupy_col)
            discovered_gupy, gupy_status = result.jobs, result.status
            gupy_query_stats = gupy_col.query_stats
        except Exception as e:
            gupy_status = f"FALHA ({e})"

    if linkedin_searches:
        try:
            max_linkedin_queries = int(config.get("linkedin_max_queries", 8))
            unique_searches = []
            seen_search_keys = set()
            for search in linkedin_searches:
                key = (
                    search.get("description") or search.get("query") or search.get("keywords"),
                    search.get("time_range") or search.get("published_within_hours"),
                    search.get("geo_id"),
                )
                if key in seen_search_keys:
                    continue
                seen_search_keys.add(key)
                unique_searches.append(search)
            linkedin_searches = unique_searches[:max_linkedin_queries]
            li_col = LinkedInCollector(HTTP, linkedin_searches)
            result = collect_result(li_col)
            discovered_linkedin, linkedin_status = result.jobs, result.status
            linkedin_query_stats = li_col.query_stats
            failed_queries = [
                item.get("status", "UNKNOWN")
                for item in linkedin_query_stats
                if item.get("status") not in {"OK", "UNKNOWN"}
            ]
            if failed_queries and not discovered_linkedin:
                linkedin_status = f"FALHA ({', '.join(failed_queries)})"
        except Exception as e:
            linkedin_status = f"FALHA ({e})"

    if rss_configs:
        try:
            rss_col = RssCollector(
                HTTP,
                rss_configs,
                resolve_urls=config.get("resolve_rss_urls", False),
                min_description_chars=config.get("rss_min_description_chars", 0),
            )
            result = collect_result(rss_col)
            discovered_rss, rss_status = result.jobs, result.status
        except Exception as e:
            rss_status = f"FALHA ({e})"

    if github_configs:
        try:
            for cfg in github_configs:
                gh_col = GithubIssuesCollector(
                    HTTP,
                    repos=cfg.get("repos"),
                    keywords=cfg.get("keywords"),
                    exclude_keywords=cfg.get("exclude_keywords"),
                    max_pages=cfg.get("max_pages", 3),
                    lookback_days=cfg.get("lookback_days", 1),
                    fallback_lookback_days=cfg.get("fallback_lookback_days", 3),
                    strict_freshness=cfg.get("strict_freshness", True),
                )
                result = collect_result(gh_col)
                discovered_github.extend(result.jobs)
                if result.status != 'OK':
                    github_status = result.status
        except Exception as e:
            github_status = f"FALHA ({e})"

    if trampos_configs:
        try:
            for cfg in trampos_configs:
                t_col = TramposCollector(
                    HTTP,
                    keywords=cfg.get("keywords"),
                    exclude_keywords=cfg.get("exclude_keywords"),
                    max_pages=cfg.get("max_pages", 1)
                )
                result = collect_result(t_col)
                discovered_trampos.extend(result.jobs)
                if result.status != 'OK':
                    trampos_status = result.status
        except Exception as e:
            trampos_status = f"FALHA ({e})"

    discovered_jobs = discovered_gupy + discovered_linkedin + discovered_rss + discovered_github + discovered_trampos

    # 3. Deduplicação e Fusão de Múltiplas Fontes
    unique_jobs = deduplicator.process(discovered_jobs)

    # 4. Decisão e Classificação (Scoring + Localidade Estrita + Filtro PCD)
    notified_count = recovered_deliveries
    discarded_seen = 0
    discarded_pcd = 0
    discarded_location = 0
    discarded_senior = 0
    discarded_score = 0
    fallback_count = 0
    approved_jobs = []

    for idx, job in enumerate(unique_jobs, 1):
        fp = job.fingerprint
        source_ids = [s.source_job_id for s in job.sources.values()]
        if durable:
            store.remember_job(job)
            source_ids = [f'{name}:{item.source_job_id}' for name, item in job.sources.items()]

        # Se já foi notificada anteriormente, ignora
        if store.is_seen(fp, source_ids[0] if source_ids else ""):
            discarded_seen += 1
            continue
        if not store.delivery_retry_allowed(fp):
            discarded_seen += 1
            continue

        # Auditoria individual da decisão
        print(f"\n--- [Auditoria Vaga #{idx}] ---")
        print(f"Empresa: {job.company} | Título: {job.title}")
        print(f"Modalidade: {job.workplace_type} | Local: {job.location or 'Não especificado'}")

        job_id = source_ids[0] if source_ids else "unknown"
        primary_source = next(iter(job.sources.keys()), "unknown")

        # Heurística PCD: bloqueia apenas com sinal forte no título
        is_pcd, pcd_reason = is_pcd_exclusive(job.title)
        if is_pcd:
            job.pcd_signal = "TITLE"
            print(f"✗ PCD: BLOQUEADA ({pcd_reason})")
            print(f"DECISÃO: DESCARTADA (Vaga Afirmativa PCD)")
            discarded_pcd += 1
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DISCARD_PCD", pcd_reason,
                raw_url=job.raw_url, canonical_url=job.canonical_url, evidence_level=job.evidence_level
            )
            store.mark_seen(fp, source_ids)
            continue

        # Validação de Localidade Estrita (Tatuí / Sorocaba / Remoto)
        location_decision, loc_reason = classify_location(job)
        if location_decision == "LOCATION_REJECTED":
            print(f"✗ Localização: REJEITADA ({loc_reason})")
            print(f"DECISÃO: DESCARTADA (Filtro Regional)")
            discarded_location += 1
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DISCARD_LOCATION", loc_reason,
                raw_url=job.raw_url, canonical_url=job.canonical_url, evidence_level=job.evidence_level
            )
            store.mark_seen(fp, source_ids)
            continue
        else:
            print(f"✓ Localização: APROVADA ({loc_reason})")

        # Google News/RSS normalmente entrega apenas um título e um link de notícia.
        # Sem descrição ou metadados suficientes, não há evidência para transformar
        # o item em alerta de candidatura; isso evita ruído no Telegram.
        if classify_evidence(job) == "LOW_EVIDENCE":
            reason = "RSS sem evidência suficiente para confirmar uma vaga real"
            print(f"✗ Evidência: INSUFICIENTE ({reason})")
            print("DECISÃO: DESCARTADA (RSS raso)")
            discarded_score += 1
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DISCARD_LOW_EVIDENCE", reason,
                raw_url=job.raw_url, canonical_url=job.canonical_url,
                evidence_level=job.evidence_level
            )
            store.mark_seen(fp, source_ids)
            continue

        # A LinkedIn card without its public detail is only a lead, not enough
        # evidence for an alert. Keep it audited as seen and wait for a later
        # enriched observation instead of sending a misleading recommendation.
        if "linkedin" in job.sources and not (job.description or "").strip():
            reason = "LinkedIn sem descrição pública enriquecida; destino e requisitos não confirmados"
            print(f"✗ Evidência: INSUFICIENTE ({reason})")
            discarded_score += 1
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DISCARD_LOW_EVIDENCE", reason,
                raw_url=job.raw_url, canonical_url=job.canonical_url,
                evidence_level=job.evidence_level
            )
            # Não marcar como visto: o detalhe público pode ficar disponível
            # no próximo ciclo, e a vaga deve poder ser enriquecida novamente.
            continue

        # Cálculo do Score: Juiz Semântico com Fallback Heurístico
        # A análise de escopo acontece antes da decisão final: o título anunciado
        # pode ser pleno, mas a rotina diária ainda ser compatível com júnior.
        scope = analyze_scope(job)
        job.analysis = scope
        job.compatibility_category = scope["category"]
        job.potential_score = scope["potential_score"]
        job.operational_seniority = scope["operational_level"]
        job.ranking_evidence["declared_seniority"] = scope["declared_level"]
        job.ranking_evidence["operational_seniority"] = scope["operational_level"]

        score, reasons = evaluate_job(job, is_rss=("rss" in job.sources))
        if any("LLM Judge" in r for r in reasons):
            store.record_llm_call()
        if any("Fallback Heurístico Ativado" in r for r in reasons):
            fallback_count += 1

        job.match_score = score
        job.match_reasons = reasons + [f"Categoria: {scope['category']}", f"Leitura do escopo: {scope['reasoning']}"]

        # O canal de progressão permite disputar vagas de pleno cujo escopo
        # seja acessível, sem misturá-las às vagas diretamente compatíveis.
        progression = (
            scope["category"] == "POTENCIALMENTE_COMPATIVEL"
            and scope["potential_score"] >= max(45, progression_min_score)
            and scope["declared_level"] == "mid"
            and scope["operational_level"] in {"junior", "junior_to_mid"}
            and len((job.description or "").strip()) >= 180
            and not scope["hard_barriers"]
        )

        decision = classify_score(score, min_score)
        if decision == "VETO":
            veto_reason = next((r for r in reasons if "LLM Judge" in r), None)
            label = "Vaga não-real (Veto LLM)" if veto_reason else "Senioridade/Relevância"
            print(f"✗ {label}: BLOQUEADA (Score <= 0)")
            for r in reasons:
                print(f"   • {r}")
            print(f"DECISÃO: DESCARTADA ({label})")
            discarded_senior += 1
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DISCARD_SENIOR_OR_VETO", veto_reason or label, final_score=score,
                raw_url=job.raw_url, canonical_url=job.canonical_url, evidence_level=job.evidence_level
            )
            store.mark_seen(fp, source_ids)
            continue

        if decision == "LOW_SCORE":
            if progression:
                print(f"~ Oportunidade de progressao: {scope['category']} (potencial {scope['potential_score']}/100)")
                approved_jobs.append((job, source_ids, job.match_reasons))
                continue
            print(f"✗ Match Score: {score}/100 (Abaixo do mínimo {min_score})")
            for r in reasons:
                print(f"   • {r}")
            print(f"DECISÃO: DESCARTADA (Score insuficiente)")
            discarded_score += 1
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DISCARD_LOW_SCORE", reasons[0] if reasons else "Score insuficiente", final_score=score,
                raw_url=job.raw_url, canonical_url=job.canonical_url, evidence_level=job.evidence_level
            )
            store.mark_seen(fp, source_ids)
            continue

        # Aprovada em todos os critérios; a entrega ocorre após ordenar o lote.
        approved_jobs.append((job, source_ids, reasons))

    for job, source_ids, reasons in sorted(
        approved_jobs,
        key=lambda item: (
            item[0].freshness_score,
            item[0].match_score,
            item[0].learning_interest_score,
        ),
        reverse=True,
    ):
        fp = job.fingerprint
        if durable:
            notified_count += int(deliver(store, job, source_ids, notifier, email_notifier))
            continue
        if not store.claim_delivery(fp):
            discarded_seen += 1
            continue
        print(f"✓ Match Score: {job.match_score}/100 (Aprovado >= {min_score})")
        for reason in reasons:
            print(f"   • {reason}")
        print(f"🎯 DECISÃO: NOTIFICAR TELEGRAM")

        sent = notifier.send_job_alert(job)
        delivery_channel = "telegram"
        if not sent:
            print("⚠️ Telegram falhou; tentando fallback por e-mail via Resend.")
            sent = email_notifier.send_job_alert(job)
            delivery_channel = "email" if sent else "none"
        if sent:
            notified_count += 1
            print(f"✓ Alerta entregue pelo canal: {delivery_channel}")
        else:
            print("⚠️ Telegram e Resend falharam; vaga ficará disponível para retry no próximo ciclo.")
        finalize_delivery(store, job, source_ids, sent, job.match_score, reasons[0] if reasons else "Aprovada")

    elapsed = time.time() - start_time
    max_cycle_seconds = config.get("max_cycle_seconds", 180)
    llm_usage = store.get_llm_usage()
    today_llm_calls = llm_usage.get("calls", 0)

    # Relatório Estruturado do Funil e Saúde do Sistema
    print("\n" + "=" * 48)
    print(" 📊 FUNIL DE EXECUÇÃO E SAÚDE DO SISTEMA")
    print("=" * 48)
    print(f"├─ Gupy:     {gupy_status:<8} | {len(discovered_gupy)} vaga(s)")
    for query in gupy_query_stats:
        print(
            f"│  └─ parâmetros={list(query['parameters'].keys())} "
            f"resultados={query['results']} status={query['status']}"
        )
    print(f"├─ LinkedIn: {linkedin_status:<8} | {len(discovered_linkedin)} vaga(s)")
    for query in linkedin_query_stats:
        print(
            f"│  └─ busca='{query['keywords']}' janela={query['time_range']} "
                f"páginas={query['pages']} cartões={query['cards']} "
            f"válidas={query['parsed_jobs']} enriquecidas={query.get('enrichment_successes', 0)}/"
            f"{query.get('enrichment_attempts', 0)} status={query['status']}"
        )
    print(f"├─ RSS:      {rss_status:<8} | {len(discovered_rss)} vaga(s)")
    print(f"├─ GitHub:   {github_status:<8} | {len(discovered_github)} vaga(s)")
    print("├" + "─" * 46)
    print(f"├─ Descoberta Bruta:    {len(discovered_jobs)}")
    print(f"├─ Vagas Únicas:        {len(unique_jobs)}")
    print(f"├─ Já Vistas:           {discarded_seen}")
    print(f"├─ Rejeitadas PCD:      {discarded_pcd}")
    print(f"├─ Rejeitadas Região:   {discarded_location}")
    print(f"├─ Rejeitadas Nível:    {discarded_senior}")
    print(f"├─ Rejeitadas Score:    {discarded_score}")
    print(f"├─ 🎯 Notificadas:       {notified_count}")
    cycle_metrics = summarize_cycle(
        len(discovered_jobs),
        len(unique_jobs),
        notified_count,
        {"pcd": discarded_pcd, "location": discarded_location, "seniority": discarded_senior, "score": discarded_score},
        {"gupy": gupy_status, "linkedin": linkedin_status, "rss": rss_status, "github": github_status, "trampos": trampos_status},
    )
    health_report = {
        "finished_at": datetime.now().isoformat(timespec="seconds"),
        "status": "DEGRADED" if cycle_metrics['source_failures'] else "SUCCESS",
        "duration_seconds": round(elapsed, 1),
        "sources": {
            "gupy": {"status": gupy_status, "discovered": len(discovered_gupy), "queries": gupy_query_stats},
            "linkedin": {"status": linkedin_status, "discovered": len(discovered_linkedin), "queries": linkedin_query_stats},
            "rss": {"status": rss_status, "discovered": len(discovered_rss)},
            "github": {"status": github_status, "discovered": len(discovered_github)},
            "trampos": {"status": trampos_status, "discovered": len(discovered_trampos)},
        },
        "funnel": {
            "raw": len(discovered_jobs),
            "unique": len(unique_jobs),
            "seen": discarded_seen,
            "discarded": {
                "pcd": discarded_pcd,
                "location": discarded_location,
                "seniority": discarded_senior,
                "score": discarded_score,
            },
            "notified": notified_count,
        },
        "metrics": cycle_metrics,
        "llm_calls_today": today_llm_calls,
        "llm_fallbacks": fallback_count,
    }
    with open(HEALTH_REPORT_FILE, "w", encoding="utf-8") as report_file:
        json.dump(health_report, report_file, ensure_ascii=False, indent=2)
    print(f"├─ Duplicatas:           {cycle_metrics['duplicate_count']} ({cycle_metrics['duplicate_rate']:.1%})")
    print(f"├─ Precisão/Recall:      N/D ({cycle_metrics['precision_recall_note']})")
    print(f"├─ Falhas de fonte:      {', '.join(cycle_metrics['source_failures']) or 'nenhuma'}")
    print("├" + "─" * 46)
    print(f"├─ LLM Calls Hoje:     {today_llm_calls}/1000 (RPD)")
    fallback_str = f"{fallback_count} vaga(s)" if fallback_count > 0 else "0 (LLM 100% ativo)"
    print(f"├─ Fallback Heurístico: {fallback_str}")
    print(f"├─ Duração:             {elapsed:.1f}s")
    if elapsed > max_cycle_seconds:
        print(f"⚠️ Limite operacional excedido: {elapsed:.1f}s > {max_cycle_seconds}s")
    print(f"└─ Status do Ciclo:     {health_report['status']}")
    print("=" * 48 + "\n")

    if fallback_count > 0:
        print(f"⚠️  ALERTA: O Fallback Heurístico foi acionado em {fallback_count} vaga(s) devido a indisponibilidade ou rate limit da IA!\n")

    # 5. Heartbeat e Persistência
    store.record_source_health("gupy", gupy_status, len(discovered_gupy), gupy_query_stats)
    store.record_source_health("linkedin", linkedin_status, len(discovered_linkedin), linkedin_query_stats)
    store.record_source_health("rss", rss_status, len(discovered_rss))
    store.record_source_health("github", github_status, len(discovered_github))
    store.record_source_health("trampos", trampos_status, len(discovered_trampos))
    if durable:
        from core.operational_alerts import update_source_alerts, send_operational
        update_source_alerts(store, {
            'gupy': gupy_status if gupy_queries else 'NOT_CONFIGURED',
            'linkedin': linkedin_status if linkedin_searches else 'NOT_CONFIGURED',
            'rss': rss_status if rss_configs else 'NOT_CONFIGURED',
            'github': github_status if github_configs else 'NOT_CONFIGURED',
            'trampos': trampos_status if trampos_configs else 'NOT_CONFIGURED',
        }, lambda message: send_operational(HTTP, message))
    check_heartbeat(config, store, notifier)
    store.save()


def main():
    if any(flag in sys.argv for flag in ('--due', '--diagnose', '--migrate', '--dry-run')) or ('--once' in sys.argv and os.getenv('JOB_FINDER_LOCAL_RUNTIME') == '1'):
        from core.local_runtime import main as local_main
        local_main(sys.modules[__name__], sys.argv[1:])
        return
    config = load_config()
    interval = config.get("check_interval_minutes", 60) * 60

    if "--once" in sys.argv:
        run_check()
        return

    if "--heartbeat" in sys.argv:
        store = StateStore(STATE_FILE)
        notifier = TelegramNotifier(TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID, HTTP)
        monitors_count = len(config.get("monitors", []))
        total_tracked = len(store.state.get("seen_fingerprints", []))
        ok = notifier.send_heartbeat(monitors_count, total_tracked)
        if ok:
            print("💚 Heartbeat de teste enviado com sucesso ao Telegram!")
        else:
            print("❌ Falha ao enviar Heartbeat.")
        return

    print("========================================")
    print("   JOB FINDER - RADAR PROFISSIONAL      ")
    print("========================================")
    print(f"Intervalo: {interval // 60} minuto(s)")
    print("Pressione Ctrl+C para parar.\n")

    while True:
        try:
            run_check()
            time.sleep(interval)
        except KeyboardInterrupt:
            print("\nMonitor encerrado pelo usuário.")
            break
        except Exception as e:
            print(f"Erro inesperado: {e}")
            time.sleep(30)


if __name__ == "__main__":
    main()

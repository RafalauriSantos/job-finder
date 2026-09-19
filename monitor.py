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
from storage.state_store import StateStore
from core.query_planner import plan_searches

load_dotenv()

# Garante suporte a UTF-8 no console do Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CONFIG_FILE = "config.json"
STATE_FILE = "seen_jobs.json"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
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
    deduplicator = Deduplicator()
    min_score = config.get("min_match_score", 50)  # Padrão: 50 pts mínimos para alertar

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
            gupy_col = GupyCollector(HTTP, gupy_queries)
            discovered_gupy = gupy_col.collect()
            gupy_query_stats = gupy_col.query_stats
        except Exception as e:
            gupy_status = f"FALHA ({e})"

    if linkedin_searches:
        try:
            li_col = LinkedInCollector(HTTP, linkedin_searches)
            discovered_linkedin = li_col.collect()
            linkedin_query_stats = li_col.query_stats
        except Exception as e:
            linkedin_status = f"FALHA ({e})"

    if rss_configs:
        try:
            rss_col = RssCollector(
                HTTP,
                rss_configs,
                resolve_urls=config.get("resolve_rss_urls", False),
            )
            discovered_rss = rss_col.collect()
        except Exception as e:
            rss_status = f"FALHA ({e})"

    if github_configs:
        try:
            for cfg in github_configs:
                gh_col = GithubIssuesCollector(
                    HTTP,
                    repos=cfg.get("repos"),
                    keywords=cfg.get("keywords"),
                    exclude_keywords=cfg.get("exclude_keywords")
                )
                discovered_github.extend(gh_col.collect())
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
                discovered_trampos.extend(t_col.collect())
        except Exception as e:
            trampos_status = f"FALHA ({e})"

    discovered_jobs = discovered_gupy + discovered_linkedin + discovered_rss + discovered_github + discovered_trampos

    # 3. Deduplicação e Fusão de Múltiplas Fontes
    unique_jobs = deduplicator.process(discovered_jobs)

    # 4. Decisão e Classificação (Scoring + Localidade Estrita + Filtro PCD)
    notified_count = 0
    discarded_seen = 0
    discarded_pcd = 0
    discarded_location = 0
    discarded_senior = 0
    discarded_score = 0
    fallback_count = 0

    for idx, job in enumerate(unique_jobs, 1):
        fp = job.fingerprint
        source_ids = [s.source_job_id for s in job.sources.values()]

        # Se já foi notificada anteriormente, ignora
        if store.is_seen(fp, source_ids[0] if source_ids else ""):
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
        loc_allowed, loc_reason = is_location_allowed(job.workplace_type, job.location, job.title)
        if not loc_allowed:
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
        if "rss" in job.sources and job.evidence_level == "LOW_EVIDENCE":
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

        # Cálculo do Score: Juiz Semântico com Fallback Heurístico
        score, reasons = evaluate_job(job, is_rss=("rss" in job.sources))
        if any("LLM Judge" in r for r in reasons):
            store.record_llm_call()
        if any("Fallback Heurístico Ativado" in r for r in reasons):
            fallback_count += 1

        job.match_score = score
        job.match_reasons = reasons

        if score <= 0:
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

        if score < min_score:
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

        # Aprovada em todos os critérios
        print(f"✓ Match Score: {score}/100 (Aprovado >= {min_score})")
        for r in reasons:
            print(f"   • {r}")
        print(f"🎯 DECISÃO: NOTIFICAR TELEGRAM")

        sent = notifier.send_job_alert(job)
        if sent:
            notified_count += 1
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DELIVERED", reasons[0] if reasons else "Aprovada", final_score=score,
                raw_url=job.raw_url, canonical_url=job.canonical_url, evidence_level=job.evidence_level
            )
            store.record_delivery(fp, source_ids, delivered=True)
        else:
            print("⚠️ Entrega Telegram falhou; vaga ficará disponível para retry no próximo ciclo.")
            store.record_decision(
                job_id, primary_source, job.identity_fingerprint, job.content_hash,
                "DELIVERY_FAILED", "Falha ao enviar alerta pelo Telegram", final_score=score,
                raw_url=job.raw_url, canonical_url=job.canonical_url, evidence_level=job.evidence_level
            )
            store.record_delivery(fp, source_ids, delivered=False)

    elapsed = time.time() - start_time
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
            f"válidas={query['parsed_jobs']} status={query['status']}"
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
    print("├" + "─" * 46)
    print(f"├─ LLM Calls Hoje:     {today_llm_calls}/1000 (RPD)")
    fallback_str = f"{fallback_count} vaga(s)" if fallback_count > 0 else "0 (LLM 100% ativo)"
    print(f"├─ Fallback Heurístico: {fallback_str}")
    print(f"├─ Duração:             {elapsed:.1f}s")
    print(f"└─ Status do Ciclo:     SUCCESS")
    print("=" * 48 + "\n")

    if fallback_count > 0:
        print(f"⚠️  ALERTA: O Fallback Heurístico foi acionado em {fallback_count} vaga(s) devido a indisponibilidade ou rate limit da IA!\n")

    # 5. Heartbeat e Persistência
    check_heartbeat(config, store, notifier)
    store.save()


def main():
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

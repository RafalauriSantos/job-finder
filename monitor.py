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
from core.normalizer import is_location_allowed
from core.scoring import calculate_match_score
from core.deduplicator import Deduplicator
from collectors.gupy_collector import GupyCollector
from collectors.linkedin_collector import LinkedInCollector
from notify.telegram_notifier import TelegramNotifier
from storage.state_store import StateStore

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
    now_str = datetime.now().strftime("%H:%M:%S")
    print(f"[{now_str}] Iniciando patrulha com {len(monitors)} monitor(es)...")

    # 1. Agrupa configurações por tipo de coletor
    gupy_queries = []
    linkedin_searches = []

    for m in monitors:
        m_type = m.get("type", "")
        if m_type == "gupy":
            query_args = {
                k: v for k, v in m.items()
                if k not in ["type", "description", "only_remote", "strict_location", "keywords", "exclude_keywords"]
            }
            if "limit" not in query_args:
                query_args["limit"] = 20
            gupy_queries.append(query_args)
        elif m_type == "linkedin":
            linkedin_searches.append({
                "keywords": m.get("keywords_search") or m.get("description"),
                "time_range": m.get("time_range", "r3600"),
                "geo_id": m.get("geo_id", "106057199"),
            })

    # 2. Executa a Coleta (Fase de Descoberta / Recall Alto)
    discovered_jobs = []
    if gupy_queries:
        gupy_col = GupyCollector(HTTP, gupy_queries)
        discovered_jobs.extend(gupy_col.collect())

    if linkedin_searches:
        li_col = LinkedInCollector(HTTP, linkedin_searches)
        discovered_jobs.extend(li_col.collect())

    print(f"[{datetime.now().strftime('%H:%M:%S')}] Total descoberto bruto: {len(discovered_jobs)} vaga(s).")

    # 3. Deduplicação e Fusão de Múltiplas Fontes
    unique_jobs = deduplicator.process(discovered_jobs)

    # 4. Decisão e Classificação (Scoring + Localidade Estrita)
    notified_count = 0

    for job in unique_jobs:
        fp = job.fingerprint
        source_ids = [s.source_job_id for s in job.sources.values()]

        # Se já foi notificada anteriormente, ignora
        if store.is_seen(fp, source_ids[0] if source_ids else ""):
            continue

        # Validação de Localidade Estrita (Tatuí / Sorocaba / Remoto)
        loc_allowed, loc_reason = is_location_allowed(job.workplace_type, job.location, job.title)
        if not loc_allowed:
            continue

        # Cálculo do Match Score com o CV
        score, reasons = calculate_match_score(job)
        job.match_score = score
        job.match_reasons = reasons

        if score >= min_score:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 MATCH {score}/100: {job.title} ({job.company})")
            sent = notifier.send_job_alert(job)
            if sent:
                notified_count += 1

        # Marca como vista para nunca repetir a mesma vaga
        store.mark_seen(fp, source_ids)

    # 5. Heartbeat e Persistência
    check_heartbeat(config, store, notifier)
    store.save()

    if notified_count == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Nenhuma nova vaga acima do threshold de pontuação.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Concluído: {notified_count} vaga(s) qualificada(s) notificada(s)!")


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

import json
import os
import re
import sys
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from dotenv import load_dotenv

load_dotenv()

# Garante suporte a UTF-8 no console do Windows
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

CONFIG_FILE = "config.json"
STATE_FILE = "seen_jobs.json"
GUPY_MCP_URL = "https://candidates.mcp.api.gupy.io/mcp"

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")


def get_http_session():
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


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"check_interval_minutes": 15, "monitors": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    """Carrega o estado com suporte retrocompatível a listas ou dicionários."""
    default_state = {"seen_ids": [], "last_heartbeat": ""}
    if not os.path.exists(STATE_FILE):
        return default_state
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return {"seen_ids": data, "last_heartbeat": ""}
            if isinstance(data, dict):
                return {
                    "seen_ids": data.get("seen_ids", []),
                    "last_heartbeat": data.get("last_heartbeat", ""),
                }
            return default_state
    except Exception:
        return default_state


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def send_telegram(title, company, workplace, job_type, salary, url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    msg = (
        f"🚨 <b>NOVA VAGA ENCONTRADA!</b>\n\n"
        f"🏢 <b>Empresa:</b> {company}\n"
        f"💼 <b>Cargo:</b> {title}\n"
        f"📍 <b>Modelo:</b> {workplace}\n"
        f"📋 <b>Tipo:</b> {job_type}\n"
        f"💰 <b>Salário:</b> {salary}\n"
    )

    # Botão nativo e limpo no Telegram (Inline Keyboard)
    reply_markup = {
        "inline_keyboard": [
            [
                {"text": "🚀 Abrir Candidatura / Informações", "url": url}
            ]
        ]
    }

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": True,
        "reply_markup": reply_markup,
    }

    try:
        r = HTTP.post(api_url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[ERRO Telegram] {e}")
        return False


def send_telegram_heartbeat(monitors_count):
    """Envia 'prova de vida' silenciosa no Telegram."""
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False

    msg = (
        f"💚 <b>Radar Operacional — Prova de Vida</b>\n\n"
        f"Seu monitor de vagas está rodando ativamente na nuvem.\n"
        f"🏢 <b>Monitores ativos:</b> {monitors_count}\n"
        f"⏱️ <b>Frequência:</b> a cada 1 hora\n"
        f"Status: 100% Saudável."
    )

    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_notification": True,
    }

    try:
        r = HTTP.post(api_url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[ERRO Telegram Heartbeat] {e}")
        return False


def send_discord(title, company, workplace, job_type, salary, url):
    if not DISCORD_WEBHOOK_URL:
        return False
    payload = {
        "embeds": [
            {
                "title": f"🚨 Nova Vaga: {title}",
                "url": url,
                "color": 3447003,
                "fields": [
                    {"name": "Empresa", "value": company, "inline": True},
                    {"name": "Modelo", "value": workplace, "inline": True},
                    {"name": "Tipo", "value": job_type, "inline": True},
                    {"name": "Salário", "value": salary, "inline": False},
                ],
                "footer": {"text": "Job Finder Alert"},
            }
        ]
    }
    try:
        r = HTTP.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
        return r.status_code in [200, 204]
    except Exception as e:
        print(f"[ERRO Discord] {e}")
        return False


def notify(title, company, workplace, job_type, salary, url):
    tg = send_telegram(title, company, workplace, job_type, salary, url)
    dc = send_discord(title, company, workplace, job_type, salary, url)
    if not tg and not dc:
        print(f"  -> [ALERTA] {company} | {title} | {url}")


def query_gupy_mcp(args):
    """Consulta vagas na API oficial da Gupy."""
    body = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {
            "name": "search_jobs",
            "arguments": args,
        },
    }
    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json, text/event-stream",
    }
    resp = HTTP.post(GUPY_MCP_URL, json=body, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []

    for line in resp.text.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line[5:].strip())
            content_text = payload.get("result", {}).get("content", [{}])[0].get("text", "{}")
            parsed = json.loads(content_text)
            return parsed.get("data", {}).get("data", [])
    return []


def query_rss(feed_url, default_company=""):
    """Consulta vagas em feeds RSS/Atom (Google Alerts, Google News, etc)."""
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
    try:
        resp = HTTP.get(feed_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        root = ET.fromstring(resp.content)
        items = []

        # 1. Suporte a formato Atom (usado por Google Alerts)
        ns = {"atom": "http://www.w3.org/2005/Atom"}
        entries = root.findall("atom:entry", ns)
        if entries:
            for entry in entries:
                item_id = entry.findtext("atom:id", default="", namespaces=ns)
                title = entry.findtext("atom:title", default="", namespaces=ns)
                link_elem = entry.find("atom:link", ns)
                link = link_elem.attrib.get("href", "") if link_elem is not None else ""
                title_clean = re.sub(r"<[^>]+>", "", title).strip()
                items.append({
                    "id": item_id or link,
                    "name": title_clean,
                    "careerPageName": default_company,
                    "workplaceType": "A consultar",
                    "type": "Vaga Externa",
                    "salary": {"label": "Não informado"},
                    "jobUrl": link,
                })
            return items

        # 2. Suporte a formato RSS 2.0 (Google News e feeds padrão)
        channel = root.find("channel")
        if channel is not None:
            for item in channel.findall("item"):
                guid = item.findtext("guid") or item.findtext("link") or ""
                title = item.findtext("title", default="")
                link = item.findtext("link", default="")
                title_clean = re.sub(r"<[^>]+>", "", title).strip()
                items.append({
                    "id": guid or link,
                    "name": title_clean,
                    "careerPageName": default_company,
                    "workplaceType": "A consultar",
                    "type": "Vaga Externa",
                    "salary": {"label": "Não informado"},
                    "jobUrl": link,
                })
            return items
    except Exception as e:
        print(f"[ERRO RSS Parser] {e}")
    return []


def check_heartbeat(config, state):
    """Verifica se deve enviar o heartbeat semanal."""
    hb_cfg = config.get("heartbeat", {})
    if not hb_cfg.get("enabled", False):
        return

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    target_day = hb_cfg.get("day_of_week", 0)  # 0 = Segunda-feira

    if now.weekday() == target_day and state.get("last_heartbeat") != today_str:
        monitors_count = len(config.get("monitors", []))
        if send_telegram_heartbeat(monitors_count):
            print(f"[{now.strftime('%H:%M:%S')}] 💚 Heartbeat semanal enviado ao Telegram.")
            state["last_heartbeat"] = today_str


def matches_filters(job, monitor_cfg):
    """Aplica filtros opcionais (apenas remoto, palavras-chave, exclusões)."""
    title = job.get("name", "").lower()
    description = job.get("description", "").lower()
    workplace = job.get("workplaceType", "").lower()

    # 1. Filtro 'only_remote'
    if monitor_cfg.get("only_remote", False):
        if workplace != "remote":
            return False

    # 2. Filtro 'exclude_keywords' (blacklist)
    exclude = [k.lower() for k in monitor_cfg.get("exclude_keywords", [])]
    if any(ex in title for ex in exclude):
        return False

    # 3. Filtro 'keywords' (whitelist)
    keywords = [k.lower() for k in monitor_cfg.get("keywords", [])]
    if keywords:
        has_match = any(kw in title or kw in description for kw in keywords)
        if not has_match:
            return False

    return True


def run_check():
    config = load_config()
    state = load_state()
    seen_ids = set(state.get("seen_ids", []))
    monitors = config.get("monitors", [])
    now = datetime.now().strftime("%H:%M:%S")

    print(f"[{now}] Checando {len(monitors)} monitor(es)...")
    total_new = 0

    for monitor in monitors:
        desc = monitor.get("description", "Monitor")
        m_type = monitor.get("type", "gupy")

        try:
            if m_type == "rss":
                feed_url = monitor.get("url")
                company_name = monitor.get("company", desc)
                jobs = query_rss(feed_url, company_name)
            else:
                query_args = {
                    k: v
                    for k, v in monitor.items()
                    if k not in ["type", "description", "only_remote", "keywords", "exclude_keywords"]
                }
                if "limit" not in query_args:
                    query_args["limit"] = 20
                jobs = query_gupy_mcp(query_args)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{desc}] Erro na consulta: {e}")
            continue

        for job in jobs:
            job_id = job.get("id")
            if job_id not in seen_ids:
                if not matches_filters(job, monitor):
                    continue

                total_new += 1
                seen_ids.add(job_id)
                name = job.get("name")
                company = job.get("careerPageName") or desc
                workplace = job.get("workplaceType", "Não especificado").capitalize()
                job_type = job.get("type", "Não especificado")
                salary_info = job.get("salary", {}).get("label", "Não informado")
                url = job.get("jobUrl") or f"https://{job.get('careerPageName')}.gupy.io/job/{job_id}"

                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 NOVA VAGA: {name} ({company})")
                notify(name, company, workplace, job_type, salary_info, url)

    state["seen_ids"] = list(seen_ids)
    check_heartbeat(config, state)
    save_state(state)

    if total_new == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Nenhuma vaga nova detectada.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Concluído: {total_new} vaga(s) nova(s) notificada(s)!")


def main():
    config = load_config()
    interval = config.get("check_interval_minutes", 15) * 60

    if "--once" in sys.argv:
        run_check()
        return

    if "--heartbeat" in sys.argv:
        monitors_count = len(config.get("monitors", []))
        ok = send_telegram_heartbeat(monitors_count)
        if ok:
            print("💚 Heartbeat de teste enviado com sucesso ao Telegram!")
        else:
            print("❌ Falha ao enviar Heartbeat.")
        return

    print("========================================")
    print("   JOB FINDER - MONITOR MULTI-EMPRESA   ")
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

import json
import os
import sys
import time
from datetime import datetime
import requests
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


def load_config():
    if not os.path.exists(CONFIG_FILE):
        return {"check_interval_minutes": 10, "monitors": []}
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def load_state():
    if not os.path.exists(STATE_FILE):
        return []
    try:
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return []


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(list(state), f, indent=2, ensure_ascii=False)


def send_telegram(title, company, workplace, job_type, salary, url):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        return False
    msg = (
        f"🚨 <b>NOVA VAGA ENCONTRADA!</b>\n\n"
        f"🏢 <b>Empresa:</b> {company}\n"
        f"💼 <b>Cargo:</b> {title}\n"
        f"📍 <b>Modelo:</b> {workplace}\n"
        f"📋 <b>Tipo:</b> {job_type}\n"
        f"💰 <b>Salário:</b> {salary}\n\n"
        f"👉 <a href='{url}'>Clique aqui para se candidatar</a>"
    )
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": msg,
        "parse_mode": "HTML",
        "disable_web_page_preview": False,
    }
    try:
        r = requests.post(api_url, json=payload, timeout=10)
        return r.status_code == 200
    except Exception as e:
        print(f"[ERRO Telegram] {e}")
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
        r = requests.post(DISCORD_WEBHOOK_URL, json=payload, timeout=10)
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
    resp = requests.post(GUPY_MCP_URL, json=body, headers=headers, timeout=15)
    if resp.status_code != 200:
        return []

    for line in resp.text.splitlines():
        if line.startswith("data:"):
            payload = json.loads(line[5:].strip())
            content_text = payload.get("result", {}).get("content", [{}])[0].get("text", "{}")
            parsed = json.loads(content_text)
            return parsed.get("data", {}).get("data", [])
    return []


def run_check():
    config = load_config()
    seen_ids = set(load_state())
    monitors = config.get("monitors", [])
    now = datetime.now().strftime("%H:%M:%S")

    print(f"[{now}] Checando {len(monitors)} monitor(es)...")
    total_new = 0

    for monitor in monitors:
        desc = monitor.get("description", "Monitor")
        query_args = {k: v for k, v in monitor.items() if k != "description"}
        if "limit" not in query_args:
            query_args["limit"] = 20

        try:
            jobs = query_gupy_mcp(query_args)
        except Exception as e:
            print(f"[{datetime.now().strftime('%H:%M:%S')}] [{desc}] Erro na consulta: {e}")
            continue

        for job in jobs:
            job_id = job.get("id")
            if job_id not in seen_ids:
                total_new += 1
                seen_ids.add(job_id)
                name = job.get("name")
                company = job.get("careerPageName") or desc
                workplace = job.get("workplaceType", "Não especificado")
                job_type = job.get("type", "Não especificado")
                salary_info = job.get("salary", {}).get("label", "Não informado")
                url = job.get("jobUrl") or f"https://{job.get('careerPageName')}.gupy.io/job/{job_id}"

                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 NOVA VAGA: {name} ({company})")
                notify(name, company, workplace, job_type, salary_info, url)

    save_state(seen_ids)
    if total_new == 0:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Nenhuma vaga nova detectada.")
    else:
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Concluído: {total_new} vaga(s) nova(s) notificada(s)!")


def main():
    config = load_config()
    interval = config.get("check_interval_minutes", 10) * 60

    if "--once" in sys.argv:
        run_check()
        return

    print("========================================")
    print("   JOB FINDER - MONITOR MINIMALISTA     ")
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

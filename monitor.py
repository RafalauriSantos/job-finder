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


JOB_TYPE_TRANSLATIONS = {
    "vacancy_type_effective": "Efetivo (CLT)",
    "vacancy_type_internship": "Estágio",
    "vacancy_type_trainee": "Trainee",
    "vacancy_type_apprentice": "Jovem Aprendiz",
    "vacancy_legal_entity": "Pessoa Jurídica (PJ)",
    "vacancy_type_temporary": "Temporário",
    "vacancy_type_freelancer": "Freelancer",
    "vacancy_type_outsource": "Terceirizado",
    "vacancy_type_talent_pool": "Banco de Talentos",
    "vacancy_type_associate": "Associado",
}

WORKPLACE_TRANSLATIONS = {
    "remote": "Remoto 🌐",
    "hybrid": "Híbrido 🏢/🏠",
    "on-site": "Presencial 🏢",
}


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

    resp.encoding = "utf-8"

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
                desc_text = item.findtext("description", default="")
                title_clean = re.sub(r"<[^>]+>", "", title).strip()
                desc_clean = re.sub(r"<[^>]+>", "", desc_text).strip()
                full_text = f"{title_clean} {desc_clean}".lower()

                # Inferência de modelo de trabalho em posts
                if "remoto" in full_text or "home office" in full_text or "remote" in full_text:
                    workplace = "remote"
                elif "híbrido" in full_text or "hibrido" in full_text or "hybrid" in full_text:
                    workplace = "hybrid"
                elif "presencial" in full_text or "on-site" in full_text:
                    workplace = "on-site"
                else:
                    workplace = "A consultar"

                items.append({
                    "id": guid or link,
                    "name": title_clean,
                    "description": desc_clean,
                    "careerPageName": default_company,
                    "location": title_clean,
                    "workplaceType": workplace,
                    "type": "Post no LinkedIn / Rede",
                    "salary": {"label": "Consultar post"},
                    "jobUrl": link,
                })
            return items
    except Exception as e:
        print(f"[ERRO RSS Parser] {e}")
    return []


def query_linkedin(keywords, time_range="r3600", geo_id="106057199", workplace_types=None, experience_levels=None):
    """Consulta vagas recentes via LinkedIn Guest API pública sem necessidade de login."""
    import urllib.parse
    base_url = "https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search"
    params = {
        "keywords": keywords,
        "f_TPR": time_range,
        "geoId": geo_id,
        "start": 0,
    }
    if workplace_types:
        params["f_WT"] = ",".join(str(w) for w in workplace_types)
    if experience_levels:
        params["f_E"] = ",".join(str(e) for e in experience_levels)

    query_str = urllib.parse.urlencode(params)
    target_url = f"{base_url}?{query_str}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "pt-BR,pt;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    try:
        resp = HTTP.get(target_url, headers=headers, timeout=15)
        if resp.status_code != 200:
            return []

        resp.encoding = "utf-8"
        html = resp.text

        # Encontra cada card de vaga <li>
        cards = re.findall(r'<li[^>]*>(.*?)</li>', html, re.DOTALL)
        jobs = []

        for card in cards:
            # URN / ID da vaga
            urn_match = re.search(r'data-entity-urn=\"urn:li:jobPosting:(\d+)\"', card)
            title_match = re.search(r'<h3[^>]*class=\"[^\"]*base-search-card__title[^\"]*\"[^>]*>\s*([^<]+)\s*</h3>', card)
            company_match = re.search(r'<h4[^>]*class=\"[^\"]*base-search-card__subtitle[^\"]*\"[^>]*>.*?<a[^>]*>\s*([^<]+)\s*</a>', card, re.DOTALL)
            link_match = re.search(r'<a[^>]*class=\"[^\"]*base-card__full-link[^\"]*\"[^>]*href=\"([^\"]+)\"', card)
            loc_match = re.search(r'<span[^>]*class=\"[^\"]*job-search-card__location[^\"]*\"[^>]*>\s*([^<]+)\s*</span>', card)

            if not title_match or not link_match:
                continue

            job_id = urn_match.group(1) if urn_match else link_match.group(1).split("?")[0]
            title = title_match.group(1).strip()
            company = company_match.group(1).strip() if company_match else "LinkedIn"
            raw_link = link_match.group(1).split("?")[0]
            location = loc_match.group(1).strip() if loc_match else "Brasil"

            # Identifica modelo de trabalho pela localização ou título
            loc_lower = location.lower()
            title_lower = title.lower()
            if "remoto" in loc_lower or "remote" in loc_lower or "remoto" in title_lower or "remote" in title_lower:
                workplace = "remote"
            elif "híbrido" in loc_lower or "hibrido" in loc_lower or "hybrid" in loc_lower or "híbrido" in title_lower or "hibrido" in title_lower:
                workplace = "hybrid"
            else:
                workplace = "on-site"

            jobs.append({
                "id": f"li-{job_id}",
                "name": title,
                "careerPageName": company,
                "location": location,
                "workplaceType": workplace,
                "type": "Efetivo (CLT) / Estágio",
                "salary": {"label": "Não informado"},
                "jobUrl": raw_link,
            })

        return jobs
    except Exception as e:
        print(f"[ERRO LinkedIn Parser] {e}")
        return []



def check_heartbeat(config, state):
    """Verifica se deve enviar o heartbeat (diário ou semanal)."""
    hb_cfg = config.get("heartbeat", {})
    if not hb_cfg.get("enabled", False):
        return

    now = datetime.now()
    today_str = now.strftime("%Y-%m-%d")
    frequency = hb_cfg.get("frequency", "daily")  # "daily" ou "weekly"
    target_day = hb_cfg.get("day_of_week", 0)  # 0 = Segunda-feira (para semanal)
    target_hour = hb_cfg.get("hour_start", 9)  # Horário de envio preferencial

    # Se já enviou hoje, não envia de novo
    if state.get("last_heartbeat") == today_str:
        return

    should_send = False
    if frequency == "daily":
        if now.hour >= target_hour:
            should_send = True
    elif frequency == "weekly":
        if now.weekday() == target_day and now.hour >= target_hour:
            should_send = True

    if should_send:
        monitors_count = len(config.get("monitors", []))
        if send_telegram_heartbeat(monitors_count):
            print(f"[{now.strftime('%H:%M:%S')}] 💚 Heartbeat ({frequency}) enviado ao Telegram.")
            state["last_heartbeat"] = today_str


def matches_filters(job, monitor_cfg):
    """Aplica filtros opcionais (apenas remoto, palavras-chave, exclusões e localidade)."""
    title = job.get("name", "").lower()
    description = job.get("description", "").lower()
    workplace = (job.get("workplaceType") or "").lower()
    location = (job.get("location") or job.get("city") or "").lower()

    # 1. Filtro 'only_remote'
    if monitor_cfg.get("only_remote", False):
        if workplace != "remote":
            return False

    # 2. Regra de Localidade Estrita (Híbrido/Presencial apenas Tatuí, Sorocaba, Votorantim, Boituva, Itapetininga)
    if monitor_cfg.get("strict_location", True):
        if workplace in ["hybrid", "on-site"]:
            allowed_cities = ["tatuí", "tatui", "sorocaba", "votorantim", "boituva", "itapetininga"]
            is_near = any(city in location or city in title or city in description for city in allowed_cities)
            if not is_near:
                return False

    # 3. Filtro 'exclude_keywords' (blacklist)
    exclude = [k.lower() for k in monitor_cfg.get("exclude_keywords", [])]
    if any(ex in title for ex in exclude):
        return False

    # 4. Filtro 'keywords' (whitelist)
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
            elif m_type == "linkedin":
                keywords = monitor.get("keywords_search") or monitor.get("description")
                time_range = monitor.get("time_range", "r3600")
                geo_id = monitor.get("geo_id", "106057199")
                workplace_types = monitor.get("workplace_types", [2, 3])
                experience_levels = monitor.get("experience_levels", [1, 2])
                jobs = query_linkedin(
                    keywords=keywords,
                    time_range=time_range,
                    geo_id=geo_id,
                    workplace_types=workplace_types,
                    experience_levels=experience_levels,
                )
            else:
                query_args = {
                    k: v
                    for k, v in monitor.items()
                    if k not in ["type", "description", "only_remote", "strict_location", "keywords", "exclude_keywords"]
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
                raw_workplace = (job.get("workplaceType") or "").lower()
                workplace_label = WORKPLACE_TRANSLATIONS.get(raw_workplace, raw_workplace.capitalize() or "Não especificado")
                loc = job.get("location") or job.get("city")
                if loc:
                    workplace_label = f"{workplace_label} ({loc})"

                raw_type = job.get("type", "")
                job_type = JOB_TYPE_TRANSLATIONS.get(raw_type, raw_type or "Não especificado")
                salary_info = job.get("salary", {}).get("label", "Não informado")
                # Garante URL válida: se vier da Gupy, usa rota canônica /jobs/{id}
                url = job.get("jobUrl")
                if not url:
                    career_page = job.get("careerPageName", "").strip().lower()
                    if career_page:
                        url = f"https://{career_page}.gupy.io/jobs/{job_id}"
                    else:
                        url = "https://gupy.io"

                print(f"[{datetime.now().strftime('%H:%M:%S')}] 🎯 NOVA VAGA: {name} ({company})")
                notify(name, company, workplace_label, job_type, salary_info, url)

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

import os
import requests
from models.job import Job

WORKPLACE_EMOJIS = {
    "remote": "Remoto 🌐",
    "hybrid": "Híbrido 🏢/🏠",
    "on-site": "Presencial 🏢",
    "unknown": "A confirmar 📍",
}


class TelegramNotifier:
    def __init__(self, bot_token: str, chat_id: str, http_session: requests.Session):
        self.token = bot_token
        self.chat_id = chat_id
        self.http = http_session

    def send_job_alert(self, job: Job) -> bool:
        if not self.token or not self.chat_id:
            return False

        workplace_label = WORKPLACE_EMOJIS.get(job.workplace_type, job.workplace_type)
        if job.location:
            workplace_label = f"{workplace_label} ({job.location})"

        techs_str = ", ".join(job.technologies) if job.technologies else "Geral / Consultar vaga"

        msg = (
            f"🎯 <b>MATCH COMPATÍVEL: {job.match_score}/100</b>\n\n"
            f"💼 <b>Cargo:</b> {job.title}\n"
            f"🏢 <b>Empresa:</b> {job.company}\n"
            f"📍 <b>Modelo:</b> {workplace_label}\n"
            f"📋 <b>Regime:</b> {job.job_type}\n"
            f"🛠️ <b>Tecnologias:</b> {techs_str}\n"
            f"💰 <b>Salário:</b> {job.salary}\n"
        )

        if job.match_reasons:
            msg += "\n💡 <b>Motivos do Match:</b>\n"
            for r in job.match_reasons[:3]:
                msg += f"• {r}\n"

        # Monta botões dinâmicos para todas as fontes descobertas (Gupy, LinkedIn, etc)
        buttons = []
        for src_name, src_obj in job.sources.items():
            btn_label = f"🚀 Abrir no {src_name.upper()}"
            buttons.append([{"text": btn_label, "url": src_obj.url}])

        reply_markup = {"inline_keyboard": buttons}
        api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
            "reply_markup": reply_markup,
        }

        try:
            r = self.http.post(api_url, json=payload, timeout=10)
            return r.status_code == 200
        except Exception as e:
            print(f"[ERRO TelegramNotifier] {e}")
            return False

    def send_heartbeat(self, monitors_count: int, jobs_tracked: int) -> bool:
        if not self.token or not self.chat_id:
            return False

        msg = (
            f"💚 <b>Radar Operacional — Prova de Vida</b>\n\n"
            f"Seu monitor de vagas está ativo na nuvem.\n"
            f"🏢 <b>Monitores ativos:</b> {monitors_count}\n"
            f"💾 <b>Vagas no radar:</b> {jobs_tracked}\n"
            f"⏱️ <b>Frequência:</b> a cada 1 hora\n"
            f"Status: 100% Saudável."
        )

        api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": msg,
            "parse_mode": "HTML",
            "disable_notification": True,
        }

        try:
            r = self.http.post(api_url, json=payload, timeout=10)
            return r.status_code == 200
        except Exception as e:
            print(f"[ERRO TelegramNotifier Heartbeat] {e}")
            return False

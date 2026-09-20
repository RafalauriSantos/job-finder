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
        self.last_status = 'FAILED'
        if not self.token or not self.chat_id:
            return False

        workplace_label = WORKPLACE_EMOJIS.get(job.workplace_type, job.workplace_type)
        if job.location:
            workplace_label = f"{workplace_label} ({job.location})"

        techs_str = ", ".join(job.technologies) if job.technologies else "Geral / Consultar vaga"

        category = job.compatibility_category or "COMPATIVEL"
        headline = "OPORTUNIDADE DE PROGRESSAO" if category != "COMPATIVEL" else "MATCH COMPATÍVEL"
        potential = job.potential_score or job.match_score
        msg = (
            f"🎯 <b>{headline}: {job.match_score}/100</b>\n"
            f"🧭 <b>Categoria:</b> {category} | Potencial: {potential}/100\n\n"
            f"💼 <b>Cargo:</b> {job.title}\n"
            f"🏢 <b>Empresa:</b> {job.company}\n"
            f"📍 <b>Modelo:</b> {workplace_label}\n"
            f"📋 <b>Regime:</b> {job.job_type}\n"
            f"🛠️ <b>Tecnologias:</b> {techs_str}\n"
            f"💰 <b>Salário:</b> {job.salary}\n"
        )

        msg += f"📈 <b>Senioridade:</b> {job.seniority}\n"
        if job.operational_seniority and job.operational_seniority != job.seniority:
            msg += f"🔎 <b>Escopo real estimado:</b> {job.operational_seniority}\n"
        if job.ranking_evidence.get("risk"):
            msg += "⚠️ <b>Atenção:</b> requisitos podem estar acima do nível declarado.\n"

        if job.match_reasons:
            msg += "\n💡 <b>Motivos do Match:</b>\n"
            for r in job.match_reasons[:3]:
                msg += f"• {r}\n"

        linkedin_source = job.sources.get("linkedin")
        if job.canonical_url and linkedin_source and job.canonical_url != linkedin_source.url:
            msg += f"\n🔗 <b>Destino final detectado:</b> {job.canonical_url}\n"

        # Monta botões dinâmicos para todas as fontes descobertas (Gupy, LinkedIn, etc)
        buttons = []
        for src_name, src_obj in job.sources.items():
            btn_label = f"🚀 Abrir no {src_name.upper()}"
            buttons.append([{"text": btn_label, "url": src_obj.url}])
        source_urls = [src.url for src in job.sources.values()]
        if job.canonical_url and job.canonical_url not in source_urls:
            buttons.append([{"text": "🔎 Abrir destino final", "url": job.canonical_url}])

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
            self.last_status = 'DELIVERED' if r.status_code == 200 else ('UNKNOWN' if r.status_code >= 500 else 'FAILED')
            return r.status_code == 200
        except Exception as e:
            self.last_status = 'UNKNOWN'
            print(f"[ERRO TelegramNotifier] {type(e).__name__}")
            return False

    def send_heartbeat(self, monitors_count: int, jobs_tracked: int) -> bool:
        if not self.token or not self.chat_id:
            return False

        msg = (
            f"💚 <b>Radar Operacional — Prova de Vida</b>\n\n"
            f"Seu monitor executou neste computador.\n"
            f"🏢 <b>Monitores ativos:</b> {monitors_count}\n"
            f"💾 <b>Vagas no radar:</b> {jobs_tracked}\n"
            f"Esta mensagem confirma o canal de envio, não a saúde de todas as fontes."
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
            print(f"[ERRO TelegramNotifier Heartbeat] {type(e).__name__}")
            return False

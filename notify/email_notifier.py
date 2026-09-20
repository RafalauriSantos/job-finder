import html
from typing import Optional

import requests

from models.job import Job


class ResendEmailNotifier:
    """Entrega alertas por e-mail via API REST do Resend."""

    endpoint = "https://api.resend.com/emails"

    def __init__(
        self,
        api_key: Optional[str],
        sender: Optional[str],
        recipient: Optional[str],
        http_session: requests.Session,
    ):
        self.api_key = api_key
        self.sender = sender
        self.recipient = recipient
        self.http = http_session

    def send_job_alert(self, job: Job) -> bool:
        self.last_status = 'FAILED'
        if not self.api_key or not self.sender or not self.recipient:
            return False

        links = "".join(
            f'<li><a href="{html.escape(source.url, quote=True)}">'
            f'{html.escape(name.upper())}</a></li>'
            for name, source in job.sources.items()
        )
        source_urls = [source.url for source in job.sources.values()]
        if job.canonical_url and job.canonical_url not in source_urls:
            links += (
                f'<li><a href="{html.escape(job.canonical_url, quote=True)}">'
                "DESTINO FINAL DETECTADO</a></li>"
            )
        reasons = "".join(f"<li>{html.escape(reason)}</li>" for reason in job.match_reasons[:5])
        risk = "<p><strong>Atenção:</strong> requisitos podem estar acima do nível declarado.</p>" if job.ranking_evidence.get("risk") else ""
        final_url_html = (
            f"<p><strong>URL final:</strong> {html.escape(job.canonical_url)}</p>"
            if job.canonical_url and job.canonical_url not in source_urls else ""
        )
        body = (
            f"<h2>Match compatível: {job.match_score}/100</h2>"
            f"<p><strong>Cargo:</strong> {html.escape(job.title)}</p>"
            f"<p><strong>Empresa:</strong> {html.escape(job.company)}</p>"
            f"<p><strong>Senioridade:</strong> {html.escape(job.seniority)}</p>"
            f"<p><strong>Modelo:</strong> {html.escape(job.workplace_type)}"
            f" ({html.escape(job.location or 'Não informado')})</p>"
            + final_url_html
            + f"{risk}<h3>Motivos</h3><ul>{reasons}</ul>"
            + f"<h3>Links</h3><ul>{links}</ul>"
        )
        payload = {
            "from": self.sender,
            "to": [self.recipient],
            "subject": f"Job Finder: {job.title} na {job.company}",
            "html": body,
        }
        try:
            response = self.http.post(
                self.endpoint,
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                timeout=10,
            )
            self.last_status = 'DELIVERED' if response.status_code in {200, 201} else ('UNKNOWN' if response.status_code >= 500 else 'FAILED')
            return response.status_code in {200, 201}
        except Exception as exc:
            self.last_status = 'UNKNOWN'
            print(f"[ERRO ResendEmailNotifier] {type(exc).__name__}")
            return False

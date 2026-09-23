import html
from typing import Optional

import requests

from models.job import Job
from notify.job_card import build_card, clean


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

        card, url = build_card(job)
        body = "<p>" + card.replace("\n", "<br>") + "</p>"
        if url:
            body += f'<p><a href="{html.escape(url, quote=True)}">Ver vaga</a></p>'
        payload = {
            "from": self.sender,
            "to": [self.recipient],
            "subject": f"Job Finder: {clean(job.title)} na {clean(job.company)}",
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

from models.job import Job
from notify.email_notifier import ResendEmailNotifier


class Response:
    status_code = 200


class Session:
    def __init__(self):
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return Response()


def test_resend_notifier_sends_job_email_with_links_and_reasons():
    session = Session()
    notifier = ResendEmailNotifier(
        api_key="re_test",
        sender="radar@example.com",
        recipient="rafael@example.com",
        http_session=session,
    )
    job = Job(
        title="Desenvolvedor Java Pleno",
        company="Empresa Tech",
        workplace_type="remote",
        match_score=78,
        match_reasons=["Pleno compatível", "Java e Spring"],
    )
    job.add_source("gupy", "42", "https://empresa.gupy.io/jobs/42")

    assert notifier.send_job_alert(job) is True
    payload = session.calls[0][1]["json"]
    assert payload["from"] == "radar@example.com"
    assert payload["to"] == ["rafael@example.com"]
    assert "Desenvolvedor Java Pleno" in payload["html"]
    assert "https://empresa.gupy.io/jobs/42" in payload["html"]
    assert "Pleno compatível" in payload["html"]


def test_resend_notifier_exposes_external_final_destination():
    session = Session()
    notifier = ResendEmailNotifier("re_test", "radar@example.com", "rafael@example.com", session)
    job = Job(title="Dev Júnior", company="Empresa", workplace_type="remote")
    job.add_source("linkedin", "42", "https://linkedin.com/jobs/view/42")
    job.canonical_url = "https://candidatos.jobbol.com.br/vaga/42"

    assert notifier.send_job_alert(job) is True
    body = session.calls[0][1]["json"]["html"]
    assert "DESTINO FINAL DETECTADO" in body
    assert job.canonical_url in body

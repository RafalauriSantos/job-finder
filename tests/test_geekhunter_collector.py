from collectors.geekhunter_collector import GeekHunterCollector


class Response:
    def __init__(self, text, url, status_code=200):
        self.text, self.url, self.status_code = text, url, status_code


class Session:
    def get(self, url, **kwargs):
        if url.endswith('/pt/vagas'):
            return Response('<a href="/pt/acme/jobs/dev-junior">vaga</a>', 'https://www.geekhunter.com/pt/vagas')
        return Response('''<html><head><title>Dev Junior em Acme</title>
          <meta property="og:description" content="Atuação remota. JavaScript e TypeScript. Requisitos obrigatórios.">
          </head><body>Remoto Brasil Requisitos obrigatórios JavaScript TypeScript</body></html>''', url)


def test_geekhunter_collects_public_listing_and_detail():
    jobs = GeekHunterCollector(Session(), keywords=['javascript']).collect()
    assert len(jobs) == 1
    assert jobs[0].company == 'Acme'
    assert jobs[0].workplace_type == 'remote'
    assert 'JavaScript' in jobs[0].description

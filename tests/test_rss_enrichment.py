from collectors.rss_collector import RssCollector


class MockResponse:
    status_code = 200
    content = b"""
    <rss version='2.0'><channel>
      <item>
        <guid>rss-1</guid>
        <title>Vaga Desenvolvedor Java Junior</title>
        <link>https://news.google.com/rss/articles/abc</link>
        <pubDate>Fri, 18 Sep 2026 12:00:00 GMT</pubDate>
      </item>
    </channel></rss>
    """


class MockSession:
    def get(self, *args, **kwargs):
        return MockResponse()

    def head(self, *args, **kwargs):
        response = type("Response", (), {})()
        response.url = "https://jobs.example.com/java-junior?utm_source=news"
        response.status_code = 200
        return response


def test_rss_collector_keeps_raw_and_resolved_canonical_urls():
    collector = RssCollector(
        MockSession(),
        [{"url": "https://feed.example/rss", "keywords": ["java"]}],
        resolve_urls=True,
    )

    jobs = collector.collect()

    assert len(jobs) == 1
    assert jobs[0].raw_url.startswith("https://news.google.com")
    assert jobs[0].resolved_url.startswith("https://jobs.example.com")
    assert jobs[0].canonical_url == "https://jobs.example.com/java-junior"
    assert jobs[0].published_at.endswith("+00:00")


class OfficialPageSession(MockSession):
    def get(self, url, *args, **kwargs):
        if url.startswith("https://jobs.example.com"):
            page = type("Response", (), {})()
            page.status_code = 200
            page.text = "<html><meta name='description' content='Desenvolvedor Java Junior para atuar em APIs, testes, banco de dados e integrações em equipe de tecnologia.'></html>"
            return page
        return MockResponse()


def test_rss_promotes_resolved_official_page_with_description():
    collector = RssCollector(
        OfficialPageSession(),
        [{"url": "https://feed.example/rss", "keywords": ["java"]}],
        resolve_urls=True,
    )

    jobs = collector.collect()

    assert jobs[0].evidence_level == "MEDIUM_EVIDENCE"
    assert "Desenvolvedor Java Junior" in jobs[0].description


def test_rss_evidence_gate_discards_shallow_non_official_items():
    collector = RssCollector(
        MockSession(),
        [{"url": "https://feed.example/rss", "keywords": ["java"]}],
        resolve_urls=True,
        min_description_chars=120,
    )

    assert collector.collect() == []

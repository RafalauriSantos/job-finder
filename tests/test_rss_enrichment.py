from collectors.rss_collector import RssCollector


class MockResponse:
    status_code = 200
    content = b"""
    <rss version='2.0'><channel>
      <item>
        <guid>rss-1</guid>
        <title>Vaga Desenvolvedor Java Júnior</title>
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

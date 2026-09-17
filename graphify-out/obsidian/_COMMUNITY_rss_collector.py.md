---
type: community
cohesion: 0.13
members: 28
---

# rss_collector.py

**Cohesion:** 0.13 - loosely connected
**Members:** 28 nodes

## Members
- [[Calcula pontuação de ruído anti-agregador (SPEC-008). Detecta páginas de busca…]] - rationale - core/url_resolver.py
- [[Classifica recência da vaga sem assunções destrutivas. Retorna (status,…]] - rationale - collectors/rss_collector.py
- [[Faz parse robusto de timestamps de feeds (RFC-8221123 e ISO-8601), convertendo…]] - rationale - collectors/rss_collector.py
- [[Remove parâmetros de tracking e fragmentos da URL, gerando uma URL canônica…]] - rationale - core/url_resolver.py
- [[Resolve URLs intermediárias (ex Google News) para obter a URL de destino real.…]] - rationale - core/url_resolver.py
- [[Session_5]] - code
- [[calculate_noise_score()]] - code - core/url_resolver.py
- [[classify_freshness()]] - code - collectors/rss_collector.py
- [[datetime]] - code
- [[parse_feed_datetime()]] - code - collectors/rss_collector.py
- [[resolve_url_tripartite()]] - code - core/url_resolver.py
- [[rss_collector.py]] - code - collectors/rss_collector.py
- [[sanitize_canonical_url()]] - code - core/url_resolver.py
- [[test_calculate_noise_score_clean_job_is_zero()]] - code - tests/test_url_resolution.py
- [[test_calculate_noise_score_detects_aggregation_pages()]] - code - tests/test_url_resolution.py
- [[test_calculate_noise_score_detects_salary_pages()]] - code - tests/test_url_resolution.py
- [[test_classify_freshness_fresh()]] - code - tests/test_temporal_parser.py
- [[test_classify_freshness_stale()]] - code - tests/test_temporal_parser.py
- [[test_classify_freshness_unknown()]] - code - tests/test_temporal_parser.py
- [[test_parse_invalid_date_returns_none()]] - code - tests/test_temporal_parser.py
- [[test_parse_iso8601_date()]] - code - tests/test_temporal_parser.py
- [[test_parse_rfc822_date()]] - code - tests/test_temporal_parser.py
- [[test_resolve_url_tripartite_fallback_on_head_failure()]] - code - tests/test_url_resolution.py
- [[test_resolve_url_tripartite_success()]] - code - tests/test_url_resolution.py
- [[test_sanitize_canonical_url_strips_tracking()]] - code - tests/test_url_resolution.py
- [[test_temporal_parser.py]] - code - tests/test_temporal_parser.py
- [[test_url_resolution.py]] - code - tests/test_url_resolution.py
- [[url_resolver.py]] - code - core/url_resolver.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/rss_collectorpy
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_RssCollector]]
- 4 edges to [[_COMMUNITY_LinkedInCollector]]
- 3 edges to [[_COMMUNITY_Job]]
- 2 edges to [[_COMMUNITY_monitor.py]]

## Top bridge nodes
- [[rss_collector.py]] - degree 15, connects to 4 communities
- [[datetime]] - degree 6, connects to 2 communities
- [[resolve_url_tripartite()]] - degree 9, connects to 1 community
- [[classify_freshness()]] - degree 8, connects to 1 community
- [[parse_feed_datetime()]] - degree 8, connects to 1 community
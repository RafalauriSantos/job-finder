---
type: community
cohesion: 0.10
members: 40
---

# LinkedInCollector

**Cohesion:** 0.10 - loosely connected
**Members:** 40 nodes

## Members
- [[dot-__init__()_1]] - code - collectors/gupy_collector.py
- [[dot-__init__()_2]] - code - collectors/linkedin_collector.py
- [[dot-__init__()_8]] - code - tests/test_linkedin_collector.py
- [[dot-_query_api()]] - code - collectors/gupy_collector.py
- [[dot-_query_search()]] - code - collectors/linkedin_collector.py
- [[dot-collect()]] - code - collectors/base.py
- [[dot-collect()_2]] - code - collectors/gupy_collector.py
- [[dot-collect()_3]] - code - collectors/linkedin_collector.py
- [[dot-test_live_gupy_collector_structure()]] - code - tests/test_monitor.py
- [[dot-test_live_linkedin_collector_structure()]] - code - tests/test_monitor.py
- [[ABC]] - code
- [[Any]] - code
- [[Any_1]] - code
- [[BaseCollector]] - code - collectors/base.py
- [[Classifica a modalidade em 'remote', 'hybrid', 'on-site' ou 'unknown'.]] - rationale - core/normalizer.py
- [[Executa a coleta e retorna uma lista de instâncias de Job padronizadas.]] - rationale - collectors/base.py
- [[GupyCollector]] - code - collectors/gupy_collector.py
- [[Interface abstrata para qualquer coletor de vagas (Gupy, LinkedIn, RSS, etc).…]] - rationale - collectors/base.py
- [[Job_2]] - code
- [[Job_4]] - code
- [[Job_5]] - code
- [[Limpa ruídos, acentuação, emojis e caracteres especiais do título para evitar…]] - rationale - core/normalizer.py
- [[LinkedInCollector]] - code - collectors/linkedin_collector.py
- [[MockResponse]] - code - tests/test_linkedin_collector.py
- [[Session_1]] - code
- [[Session_2]] - code
- [[TestCollectorsLiveSmoke]] - code - tests/test_monitor.py
- [[_load_allowed_cities()]] - code - core/normalizer.py
- [[base.py]] - code - collectors/base.py
- [[github_collector.py]] - code - collectors/github_collector.py
- [[gupy_collector.py]] - code - collectors/gupy_collector.py
- [[linkedin_collector.py]] - code - collectors/linkedin_collector.py
- [[normalize_title()]] - code - core/normalizer.py
- [[normalize_workplace()]] - code - core/normalizer.py
- [[normalizer.py]] - code - core/normalizer.py
- [[test_linkedin_collector.py]] - code - tests/test_linkedin_collector.py
- [[test_linkedin_collector_handles_http_errors_gracefully()]] - code - tests/test_linkedin_collector.py
- [[test_linkedin_collector_handles_malformed_html()]] - code - tests/test_linkedin_collector.py
- [[test_linkedin_collector_parses_html_successfully()]] - code - tests/test_linkedin_collector.py
- [[trampos_collector.py]] - code - collectors/trampos_collector.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/LinkedInCollector
SORT file.name ASC
```

## Connections to other communities
- 36 edges to [[_COMMUNITY_Job]]
- 12 edges to [[_COMMUNITY_monitor.py]]
- 7 edges to [[_COMMUNITY_TramposCollector]]
- 5 edges to [[_COMMUNITY_GithubIssuesCollector]]
- 4 edges to [[_COMMUNITY_rss_collector.py]]
- 3 edges to [[_COMMUNITY_RssCollector]]
- 3 edges to [[_COMMUNITY_StateStore]]
- 1 edge to [[_COMMUNITY_is_pcd_exclusive]]

## Top bridge nodes
- [[normalizer.py]] - degree 18, connects to 5 communities
- [[BaseCollector]] - degree 15, connects to 5 communities
- [[normalize_title()]] - degree 13, connects to 5 communities
- [[LinkedInCollector]] - degree 19, connects to 3 communities
- [[GupyCollector]] - degree 14, connects to 3 communities
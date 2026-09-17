---
type: community
cohesion: 0.09
members: 34
---

# RssCollector

**Cohesion:** 0.09 - loosely connected
**Members:** 34 nodes

## Members
- [[dot-__init__()_3]] - code - collectors/rss_collector.py
- [[dot-_make_collector()]] - code - tests/test_pcd_and_rss.py
- [[dot-_matches_filters()_1]] - code - collectors/rss_collector.py
- [[dot-_parse_feed()]] - code - collectors/rss_collector.py
- [[dot-collect()_4]] - code - collectors/rss_collector.py
- [[dot-test_empty_feed_returns_empty_list()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_exclude_keyword_filter_applied()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_generic_internship_without_tech_penalized()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_job_signal_scores_high()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_keyword_filter_applied()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_news_signal_scores_low()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_non_tech_bakery_vetoed_in_rss()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_parses_atom_feed()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_parses_rss_20_feed()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_rss_source_name_is_rss()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_senior_penalized_in_rss()]] - code - tests/test_pcd_and_rss.py
- [[Any_2]] - code
- [[Aplica keywordexclude_keyword filters do config ao título do item RSS.]] - rationale - collectors/rss_collector.py
- [[Coletor de vagas via feeds RSS 2.0 e Atom com suporte à SPEC-008.]] - rationale - collectors/rss_collector.py
- [[Cria um RssCollector com HTTP mockado retornando o XML fornecido.]] - rationale - tests/test_pcd_and_rss.py
- [[Faz fetch e parse do XML do feed, retorna lista de {id, title, link, pub_date}.]] - rationale - collectors/rss_collector.py
- [[Itens com exclude_keywords são removidos.]] - rationale - tests/test_pcd_and_rss.py
- [[Job_6]] - code
- [[Jobs vindos do RSS devem ter 'rss' como chave no sources dict.]] - rationale - tests/test_pcd_and_rss.py
- [[RssCollector]] - code - collectors/rss_collector.py
- [[Scoring dedicado para itens RSSGoogle News. RSS não tem campos estruturados…]] - rationale - core/scoring.py
- [[Session_3]] - code
- [[Somente itens com keywords sobrevivem.]] - rationale - tests/test_pcd_and_rss.py
- [[TestRssCollector]] - code - tests/test_pcd_and_rss.py
- [[TestRssRelevanceScoring]] - code - tests/test_pcd_and_rss.py
- [[Testa o coletor RSS com XML mockado.]] - rationale - tests/test_pcd_and_rss.py
- [[Testa o scoring dedicado para itens RSS.]] - rationale - tests/test_pcd_and_rss.py
- [[calculate_rss_relevance()]] - code - core/scoring.py
- [[test_pcd_and_rss.py]] - code - tests/test_pcd_and_rss.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/RssCollector
SORT file.name ASC
```

## Connections to other communities
- 13 edges to [[_COMMUNITY_Job]]
- 5 edges to [[_COMMUNITY_rss_collector.py]]
- 5 edges to [[_COMMUNITY_StateStore]]
- 3 edges to [[_COMMUNITY_LinkedInCollector]]
- 3 edges to [[_COMMUNITY_is_pcd_exclusive]]
- 2 edges to [[_COMMUNITY_monitor.py]]
- 2 edges to [[_COMMUNITY_evaluate_job]]

## Top bridge nodes
- [[RssCollector]] - degree 16, connects to 6 communities
- [[test_pcd_and_rss.py]] - degree 11, connects to 4 communities
- [[calculate_rss_relevance()]] - degree 12, connects to 2 communities
- [[TestRssCollector]] - degree 12, connects to 2 communities
- [[TestRssRelevanceScoring]] - degree 10, connects to 2 communities
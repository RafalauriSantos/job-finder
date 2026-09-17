---
type: community
cohesion: 0.16
members: 19
---

# GithubIssuesCollector

**Cohesion:** 0.16 - loosely connected
**Members:** 19 nodes

## Members
- [[dot-__init__()]] - code - collectors/github_collector.py
- [[dot-_determine_seniority()]] - code - collectors/github_collector.py
- [[dot-_determine_workplace_type()]] - code - collectors/github_collector.py
- [[dot-_extract_company_from_title()]] - code - collectors/github_collector.py
- [[dot-_get_headers()]] - code - collectors/github_collector.py
- [[dot-_matches_filters()]] - code - collectors/github_collector.py
- [[dot-collect()_1]] - code - collectors/github_collector.py
- [[dot-sample_issues()]] - code - tests/test_github_collector.py
- [[dot-test_auth_headers_with_github_token()]] - code - tests/test_github_collector.py
- [[dot-test_auth_headers_without_github_token()]] - code - tests/test_github_collector.py
- [[dot-test_collect_and_parsing()]] - code - tests/test_github_collector.py
- [[Coletor de vagas via GitHub Issues (ecossistema aberto de vagas dev no Brasil).…]] - rationale - collectors/github_collector.py
- [[GithubIssuesCollector]] - code - collectors/github_collector.py
- [[Job_3]] - code
- [[Session]] - code
- [[Tenta extrair o nome da empresa do título padrão de issues de vagas.]] - rationale - collectors/github_collector.py
- [[TestGithubIssuesCollector]] - code - tests/test_github_collector.py
- [[fixture]] - code
- [[test_github_collector.py]] - code - tests/test_github_collector.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/GithubIssuesCollector
SORT file.name ASC
```

## Connections to other communities
- 5 edges to [[_COMMUNITY_LinkedInCollector]]
- 2 edges to [[_COMMUNITY_monitor.py]]
- 1 edge to [[_COMMUNITY_Job]]

## Top bridge nodes
- [[GithubIssuesCollector]] - degree 18, connects to 3 communities
- [[dot-collect()_1]] - degree 8, connects to 1 community
- [[dot-_determine_workplace_type()]] - degree 3, connects to 1 community
- [[test_github_collector.py]] - degree 3, connects to 1 community
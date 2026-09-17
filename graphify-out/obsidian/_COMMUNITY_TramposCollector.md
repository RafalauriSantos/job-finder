---
type: community
cohesion: 0.16
members: 20
---

# TramposCollector

**Cohesion:** 0.16 - loosely connected
**Members:** 20 nodes

## Members
- [[dot-__init__()_4]] - code - collectors/trampos_collector.py
- [[dot-_matches_filters()_2]] - code - collectors/trampos_collector.py
- [[dot-collect()_5]] - code - collectors/trampos_collector.py
- [[Any_3]] - code
- [[Avalia a densidade de evidência da vaga (SPEC-008). Classificação -…]] - rationale - core/evidence.py
- [[Coletor de vagas via API pública REST da Trampos.co (SPEC-008). Consome…]] - rationale - collectors/trampos_collector.py
- [[Job_7]] - code
- [[Job_9]] - code
- [[Regra de decisão da SPEC-008 Vagas LOW_EVIDENCE (especialmente RSS raso ou sem…]] - rationale - core/evidence.py
- [[Session_4]] - code
- [[TramposCollector]] - code - collectors/trampos_collector.py
- [[evidence.py]] - code - core/evidence.py
- [[profile_job_evidence()]] - code - core/evidence.py
- [[should_route_to_llm()]] - code - core/evidence.py
- [[test_evidence_profiler.py]] - code - tests/test_evidence_profiler.py
- [[test_profile_empty_description_is_low_evidence()]] - code - tests/test_evidence_profiler.py
- [[test_profile_medium_evidence()]] - code - tests/test_evidence_profiler.py
- [[test_profile_rich_gupy_description_is_high_evidence()]] - code - tests/test_evidence_profiler.py
- [[test_trampos_collector.py]] - code - tests/test_trampos_collector.py
- [[test_trampos_collector_maps_api_response_to_job()]] - code - tests/test_trampos_collector.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/TramposCollector
SORT file.name ASC
```

## Connections to other communities
- 9 edges to [[_COMMUNITY_Job]]
- 7 edges to [[_COMMUNITY_LinkedInCollector]]
- 2 edges to [[_COMMUNITY_monitor.py]]
- 1 edge to [[_COMMUNITY_evaluate_job]]

## Top bridge nodes
- [[TramposCollector]] - degree 11, connects to 3 communities
- [[should_route_to_llm()]] - degree 9, connects to 2 communities
- [[profile_job_evidence()]] - degree 11, connects to 1 community
- [[test_evidence_profiler.py]] - degree 8, connects to 1 community
- [[dot-collect()_5]] - degree 6, connects to 1 community
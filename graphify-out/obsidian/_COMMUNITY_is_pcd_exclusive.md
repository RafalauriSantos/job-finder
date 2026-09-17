---
type: community
cohesion: 0.13
members: 22
---

# is_pcd_exclusive

**Cohesion:** 0.13 - loosely connected
**Members:** 22 nodes

## Members
- [[dot-_evaluate_single_case()]] - code - tests/test_radar_quality.py
- [[dot-test_allows_normal_job()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_allows_pcd_only_in_description()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_allows_pcd_substring_in_word()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_blocks_pcd_case_insensitive()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_blocks_pcd_in_title()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_blocks_pcd_with_dots()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_blocks_pessoa_com_deficiencia()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_blocks_pessoas_com_deficiencia_plural()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_pcd_signal_recorded_on_job()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_precision_and_recall_benchmarks()]] - code - tests/test_radar_quality.py
- [[Avaliação formal de Radar Quality Testa a esteira inteira (Filtro PCD -…]] - rationale - tests/test_radar_quality.py
- [[Heurística detecta se a vaga é afirmativaexclusiva para PCD com base no…]] - rationale - core/normalizer.py
- [[O campo pcd_signal do Job deve registrar a origem do sinal.]] - rationale - tests/test_pcd_and_rss.py
- [[P.C.D. deve ser detectado após remoção de pontos.]] - rationale - tests/test_pcd_and_rss.py
- [[PCD mencionado apenas na descrição não deve bloquear (título limpo).]] - rationale - tests/test_pcd_and_rss.py
- [[SPCDAM não deve casar com bpcdb (PCD dentro de palavra).]] - rationale - tests/test_pcd_and_rss.py
- [[TestPcdFilter]] - code - tests/test_pcd_and_rss.py
- [[TestRadarQualityMetrics]] - code - tests/test_radar_quality.py
- [[Testa a heurística de detecção de vaga afirmativaexclusiva PCD.]] - rationale - tests/test_pcd_and_rss.py
- [[Vaga regular sem PCD no título NÃO deve ser bloqueada.]] - rationale - tests/test_pcd_and_rss.py
- [[is_pcd_exclusive()]] - code - core/normalizer.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/is_pcd_exclusive
SORT file.name ASC
```

## Connections to other communities
- 7 edges to [[_COMMUNITY_Job]]
- 3 edges to [[_COMMUNITY_RssCollector]]
- 2 edges to [[_COMMUNITY_monitor.py]]
- 1 edge to [[_COMMUNITY_LinkedInCollector]]
- 1 edge to [[_COMMUNITY_evaluate_job]]
- 1 edge to [[_COMMUNITY_StateStore]]

## Top bridge nodes
- [[is_pcd_exclusive()]] - degree 16, connects to 4 communities
- [[TestPcdFilter]] - degree 14, connects to 3 communities
- [[dot-_evaluate_single_case()]] - degree 6, connects to 2 communities
- [[TestRadarQualityMetrics]] - degree 5, connects to 1 community
- [[dot-test_pcd_signal_recorded_on_job()]] - degree 4, connects to 1 community
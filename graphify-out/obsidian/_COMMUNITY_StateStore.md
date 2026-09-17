---
type: community
cohesion: 0.07
members: 35
---

# StateStore

**Cohesion:** 0.07 - loosely connected
**Members:** 35 nodes

## Members
- [[dot-__init__()_7]] - code - storage/state_store.py
- [[dot-_load()]] - code - storage/state_store.py
- [[dot-get_last_heartbeat()]] - code - storage/state_store.py
- [[dot-get_llm_usage()]] - code - storage/state_store.py
- [[dot-is_seen()]] - code - storage/state_store.py
- [[dot-mark_seen()]] - code - storage/state_store.py
- [[dot-prune()]] - code - storage/state_store.py
- [[dot-record_decision()]] - code - storage/state_store.py
- [[dot-record_llm_call()]] - code - storage/state_store.py
- [[dot-save()]] - code - storage/state_store.py
- [[dot-set_last_heartbeat()]] - code - storage/state_store.py
- [[dot-test_429_retry_and_backoff()]] - code - tests/test_llm_judge.py
- [[dot-test_get_profile_loads_data()]] - code - tests/test_llm_judge.py
- [[dot-test_judge_calls_gemini_when_gemini_key_present()]] - code - tests/test_llm_judge.py
- [[dot-test_judge_handles_api_exception_gracefully()]] - code - tests/test_llm_judge.py
- [[dot-test_judge_returns_none_when_no_api_key()]] - code - tests/test_llm_judge.py
- [[dot-test_loads_legacy_and_persists_fingerprints()]] - code - tests/test_monitor.py
- [[dot-test_mixed_types_normalized()]] - code - tests/test_pcd_and_rss.py
- [[dot-test_pacing_enforced()]] - code - tests/test_llm_judge.py
- [[dot-test_pruning_limits_retention()]] - code - tests/test_monitor.py
- [[dot-test_records_decision_audit_trail()]] - code - tests/test_monitor.py
- [[dot-test_rpd_tracking_in_state_store()]] - code - tests/test_llm_judge.py
- [[dot-test_should_invoke_judge_threshold()]] - code - tests/test_llm_judge.py
- [[Any_5]] - code
- [[Mantém o tamanho do arquivo de estado sob controle estrito (ADR-001). Evita…]] - rationale - storage/state_store.py
- [[Persistência do estado do monitor (fingerprints vistas, datas e heartbeat).]] - rationale - storage/state_store.py
- [[Registra a trilha de auditoria para responder por que cada vaga foi aceita ou…]] - rationale - storage/state_store.py
- [[Registra uma chamada ao LLM no contador diário (RPD tracking). NOTA DE…]] - rationale - storage/state_store.py
- [[Retorna o uso diário de chamadas ao LLM.]] - rationale - storage/state_store.py
- [[StateStore]] - code - storage/state_store.py
- [[TestLlmJudgeUnits]] - code - tests/test_llm_judge.py
- [[TestSeenIdsNormalization]] - code - tests/test_pcd_and_rss.py
- [[TestStateStorePersistence]] - code - tests/test_monitor.py
- [[Testa que seen_ids são normalizados para string.]] - rationale - tests/test_pcd_and_rss.py
- [[Verifica se a vaga já foi vista por fingerprint ou por ID específico.]] - rationale - storage/state_store.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/StateStore
SORT file.name ASC
```

## Connections to other communities
- 16 edges to [[_COMMUNITY_Job]]
- 6 edges to [[_COMMUNITY_monitor.py]]
- 5 edges to [[_COMMUNITY_RssCollector]]
- 3 edges to [[_COMMUNITY_LinkedInCollector]]
- 1 edge to [[_COMMUNITY_evaluate_job]]
- 1 edge to [[_COMMUNITY_is_pcd_exclusive]]

## Top bridge nodes
- [[StateStore]] - degree 41, connects to 6 communities
- [[TestStateStorePersistence]] - degree 10, connects to 3 communities
- [[TestSeenIdsNormalization]] - degree 6, connects to 2 communities
- [[TestLlmJudgeUnits]] - degree 11, connects to 1 community
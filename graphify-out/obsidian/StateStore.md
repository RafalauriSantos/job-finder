---
source_file: "storage/state_store.py"
type: "code"
community: "StateStore"
location: "L6"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/StateStore
---

# StateStore

## Connections
- [[dot-__init__()_7]] - `method` [EXTRACTED]
- [[dot-_load()]] - `method` [EXTRACTED]
- [[dot-get_last_heartbeat()]] - `method` [EXTRACTED]
- [[dot-get_llm_usage()]] - `method` [EXTRACTED]
- [[dot-is_seen()]] - `method` [EXTRACTED]
- [[dot-mark_seen()]] - `method` [EXTRACTED]
- [[dot-prune()]] - `method` [EXTRACTED]
- [[dot-record_decision()]] - `method` [EXTRACTED]
- [[dot-record_llm_call()]] - `method` [EXTRACTED]
- [[dot-save()]] - `method` [EXTRACTED]
- [[dot-set_last_heartbeat()]] - `method` [EXTRACTED]
- [[dot-test_case_10_seen_job_not_notified_again()]] - `calls` [EXTRACTED]
- [[dot-test_loads_legacy_and_persists_fingerprints()]] - `calls` [EXTRACTED]
- [[dot-test_mixed_types_normalized()]] - `calls` [EXTRACTED]
- [[dot-test_pruning_limits_retention()]] - `calls` [EXTRACTED]
- [[dot-test_records_decision_audit_trail()]] - `calls` [EXTRACTED]
- [[dot-test_rpd_tracking_in_state_store()]] - `calls` [EXTRACTED]
- [[dot-test_sliding_window_deduplication_and_failure_recovery()]] - `calls` [EXTRACTED]
- [[Persistência do estado do monitor (fingerprints vistas, datas e heartbeat).]] - `rationale_for` [EXTRACTED]
- [[TestCollectorsLiveSmoke]] - `uses` [INFERRED]
- [[TestEvaluateJobIntegration]] - `uses` [INFERRED]
- [[TestFiltersAndLocation]] - `uses` [INFERRED]
- [[TestLlmJudgeUnits]] - `uses` [INFERRED]
- [[TestOperationalMatrix10Cases]] - `uses` [INFERRED]
- [[TestPcdFilter]] - `uses` [INFERRED]
- [[TestRssCollector]] - `uses` [INFERRED]
- [[TestRssRelevanceScoring]] - `uses` [INFERRED]
- [[TestSeenIdsNormalization]] - `uses` [INFERRED]
- [[TestSlidingWindowResilience]] - `uses` [INFERRED]
- [[TestStateStorePersistence]] - `uses` [INFERRED]
- [[TestTelegramNotifier]] - `uses` [INFERRED]
- [[check_heartbeat()]] - `references` [EXTRACTED]
- [[main()]] - `calls` [EXTRACTED]
- [[monitor.py]] - `imports` [EXTRACTED]
- [[run_check()]] - `calls` [EXTRACTED]
- [[state_store.py]] - `contains` [EXTRACTED]
- [[test_llm_judge.py]] - `imports` [EXTRACTED]
- [[test_monitor.py]] - `imports` [EXTRACTED]
- [[test_operational_matrix.py]] - `imports` [EXTRACTED]
- [[test_pcd_and_rss.py]] - `imports` [EXTRACTED]
- [[test_resilience_sliding_window.py]] - `imports` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/StateStore
---
type: community
cohesion: 0.06
members: 80
---

# Job

**Cohesion:** 0.06 - loosely connected
**Members:** 80 nodes

## Members
- [[dot-__init__()_5]] - code - core/deduplicator.py
- [[dot-add_source()]] - code - models/job.py
- [[dot-content_hash()]] - code - models/job.py
- [[dot-fingerprint()]] - code - models/job.py
- [[dot-identity_fingerprint()]] - code - models/job.py
- [[dot-primary_url()]] - code - models/job.py
- [[dot-process()]] - code - core/deduplicator.py
- [[dot-test_calculates_high_score_for_matching_candidate_cv()]] - code - tests/test_core_architecture.py
- [[dot-test_case_10_seen_job_not_notified_again()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_1_fullstack_jr_remote_stack()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_2_backend_jr_remote_node()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_3_java_jr_remote()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_4_pleno_remote_rejected()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_5_senior_remote_rejected()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_6_jr_onsite_rj_rejected()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_7_jr_hybrid_sp_capital_rejected()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_8_jr_onsite_sorocaba_accepted()]] - code - tests/test_operational_matrix.py
- [[dot-test_case_9_multi_source_gupy_linkedin_merged()]] - code - tests/test_operational_matrix.py
- [[dot-test_description_updates_preserve_identity_fingerprint_but_change_content_hash()]] - code - tests/test_core_architecture.py
- [[dot-test_different_locations_produce_different_fingerprints()]] - code - tests/test_core_architecture.py
- [[dot-test_extract_technologies()]] - code - tests/test_core_architecture.py
- [[dot-test_hybrid_sp_capital_is_rejected_by_location_policy()]] - code - tests/test_fixtures_ground_truth.py
- [[dot-test_job_creates_fingerprint_and_merges_sources()]] - code - tests/test_core_architecture.py
- [[dot-test_junior_matching_reaches_high_score_and_approved_location()]] - code - tests/test_fixtures_ground_truth.py
- [[dot-test_location_allowed_rules()]] - code - tests/test_core_architecture.py
- [[dot-test_multi_source_deduplication_merges_gupy_and_linkedin()]] - code - tests/test_fixtures_ground_truth.py
- [[dot-test_normalizes_workplace()]] - code - tests/test_core_architecture.py
- [[dot-test_penalizes_senior_positions()]] - code - tests/test_core_architecture.py
- [[dot-test_senior_react_is_severely_penalized()]] - code - tests/test_fixtures_ground_truth.py
- [[dot-test_sliding_window_deduplication_and_failure_recovery()]] - code - tests/test_resilience_sliding_window.py
- [[dot-test_strict_location_rules()]] - code - tests/test_monitor.py
- [[dot-to_dict()]] - code - models/job.py
- [[Alias para identity_fingerprint garantindo compatibilidade com o pipeline…]] - rationale - models/job.py
- [[Aplica a regra estrita de localidade - Remoto 100% Permitido em qualquer…]] - rationale - core/normalizer.py
- [[Associa uma nova fonte a esta vaga (suporte a vaga multi-fonte).]] - rationale - models/job.py
- [[Bateria de validação dos 10 casos fundamentais de decisão operacional 1. Full…]] - rationale - tests/test_operational_matrix.py
- [[Calcula o Match Score (0 a 100) da vaga contra o perfil técnico configurado em…]] - rationale - core/scoring.py
- [[Deduplicator]] - code - core/deduplicator.py
- [[Garante que a identidade da vaga não mude quando o RH altera o texto da…]] - rationale - tests/test_identity_fingerprint.py
- [[Garante que a identidade mude se a modalidade ou localização forem diferentes.]] - rationale - tests/test_identity_fingerprint.py
- [[Garante que os novos campos da SPEC-008 existam no Job.]] - rationale - tests/test_identity_fingerprint.py
- [[Gerencia a deduplicação de vagas e a fusão de múltiplas fontes para a mesma…]] - rationale - core/deduplicator.py
- [[Hash do conteúdo textual da vaga. Permite auditar se a descrição sofreu…]] - rationale - models/job.py
- [[Identidade Canônica da Vaga (Imutável contra edições de texto pelo RH).…]] - rationale - models/job.py
- [[Job_8]] - code
- [[Job_11]] - code - models/job.py
- [[JobSource]] - code - models/job.py
- [[Pequenas correções de texto na descrição pelo RH não alteram a identidade…]] - rationale - tests/test_core_architecture.py
- [[Recebe uma lista de vagas brutas de coletores diferentes. Se uma vaga com a…]] - rationale - core/deduplicator.py
- [[Retorna o melhor link de candidatura disponível.]] - rationale - models/job.py
- [[Simula o cenário do audit - Execução 1000 vaga A coletada e persistida. -…]] - rationale - tests/test_resilience_sliding_window.py
- [[TestFiltersAndLocation]] - code - tests/test_monitor.py
- [[TestFixturesGroundTruth]] - code - tests/test_fixtures_ground_truth.py
- [[TestJobModel]] - code - tests/test_core_architecture.py
- [[TestNormalizer]] - code - tests/test_core_architecture.py
- [[TestOperationalMatrix10Cases]] - code - tests/test_operational_matrix.py
- [[TestScoring]] - code - tests/test_core_architecture.py
- [[TestSlidingWindowResilience]] - code - tests/test_resilience_sliding_window.py
- [[Vagas com mesmo título e empresa em localidades distintas geram fingerprints…]] - rationale - tests/test_core_architecture.py
- [[Varre o texto da vaga e extrai tecnologias conhecidas da stack do candidato.]] - rationale - core/normalizer.py
- [[_load_priority_companies()]] - code - core/scoring.py
- [[calculate_match_score()]] - code - core/scoring.py
- [[deduplicator.py]] - code - core/deduplicator.py
- [[extract_technologies()]] - code - core/normalizer.py
- [[is_location_allowed()]] - code - core/normalizer.py
- [[job.py]] - code - models/job.py
- [[matches_any()]] - code - core/scoring.py
- [[scoring.py]] - code - core/scoring.py
- [[state_store.py]] - code - storage/state_store.py
- [[test_core_architecture.py]] - code - tests/test_core_architecture.py
- [[test_fixtures_ground_truth.py]] - code - tests/test_fixtures_ground_truth.py
- [[test_identity_fingerprint.py]] - code - tests/test_identity_fingerprint.py
- [[test_identity_fingerprint_differs_on_location_or_workplace()]] - code - tests/test_identity_fingerprint.py
- [[test_identity_fingerprint_immutable_on_description_change()]] - code - tests/test_identity_fingerprint.py
- [[test_llm_judge.py]] - code - tests/test_llm_judge.py
- [[test_monitor.py]] - code - tests/test_monitor.py
- [[test_operational_matrix.py]] - code - tests/test_operational_matrix.py
- [[test_radar_quality.py]] - code - tests/test_radar_quality.py
- [[test_resilience_sliding_window.py]] - code - tests/test_resilience_sliding_window.py
- [[test_url_tripartite_and_evidence_level_fields()]] - code - tests/test_identity_fingerprint.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/Job
SORT file.name ASC
```

## Connections to other communities
- 36 edges to [[_COMMUNITY_LinkedInCollector]]
- 19 edges to [[_COMMUNITY_monitor.py]]
- 16 edges to [[_COMMUNITY_StateStore]]
- 16 edges to [[_COMMUNITY_evaluate_job]]
- 13 edges to [[_COMMUNITY_RssCollector]]
- 9 edges to [[_COMMUNITY_TramposCollector]]
- 7 edges to [[_COMMUNITY_is_pcd_exclusive]]
- 3 edges to [[_COMMUNITY_rss_collector.py]]
- 1 edge to [[_COMMUNITY_GithubIssuesCollector]]

## Top bridge nodes
- [[Job_11]] - degree 92, connects to 9 communities
- [[job.py]] - degree 24, connects to 5 communities
- [[scoring.py]] - degree 18, connects to 4 communities
- [[Deduplicator]] - degree 26, connects to 3 communities
- [[test_monitor.py]] - degree 21, connects to 3 communities
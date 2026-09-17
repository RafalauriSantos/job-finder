# Graph Report - .  (2026-09-17)

## Corpus Check
- cluster-only mode — file stats not available

## Summary
- 369 nodes · 816 edges · 18 communities (17 shown, 1 thin omitted)
- Extraction: 91% EXTRACTED · 9% INFERRED · 0% AMBIGUOUS · INFERRED: 76 edges (avg confidence: 0.52)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `74d5ef45`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Job
- LinkedInCollector
- .evaluate
- StateStore
- RssCollector
- rss_collector.py
- evaluate_job
- is_pcd_exclusive
- TramposCollector
- GithubIssuesCollector
- monitor.py
- test_acceptance_dataset.py
- com.jobfinder:job-finder-matching

## God Nodes (most connected - your core abstractions)
1. `Job` - 92 edges
2. `StateStore` - 41 edges
3. `Deduplicator` - 26 edges
4. `is_location_allowed()` - 20 edges
5. `calculate_match_score()` - 20 edges
6. `LinkedInCollector` - 19 edges
7. `GithubIssuesCollector` - 18 edges
8. `evaluate_job()` - 18 edges
9. `RssCollector` - 16 edges
10. `is_pcd_exclusive()` - 16 edges

## Surprising Connections (you probably didn't know these)
- `BaseCollector` --uses--> `Job`  [INFERRED]
  collectors/base.py → models/job.py
- `GithubIssuesCollector` --uses--> `Job`  [INFERRED]
  collectors/github_collector.py → models/job.py
- `GupyCollector` --uses--> `Job`  [INFERRED]
  collectors/gupy_collector.py → models/job.py
- `TestFiltersAndLocation` --uses--> `GupyCollector`  [INFERRED]
  tests/test_monitor.py → collectors/gupy_collector.py
- `TestStateStorePersistence` --uses--> `GupyCollector`  [INFERRED]
  tests/test_monitor.py → collectors/gupy_collector.py

## Import Cycles
- None detected.

## Communities (18 total, 1 thin omitted)

### Community 0 - "Job"
Cohesion: 0.06
Nodes (35): Deduplicator, Job, Recebe uma lista de vagas brutas de coletores diferentes. Se uma vaga com a…, Gerencia a deduplicação de vagas e a fusão de múltiplas fontes para a mesma…, extract_technologies(), is_location_allowed(), Varre o texto da vaga e extrai tecnologias conhecidas da stack do candidato., Aplica a regra estrita de localidade: - Remoto: 100% Permitido em qualquer… (+27 more)

### Community 1 - "LinkedInCollector"
Cohesion: 0.10
Nodes (22): ABC, BaseCollector, Job, Executa a coleta e retorna uma lista de instâncias de Job padronizadas., Interface abstrata para qualquer coletor de vagas (Gupy, LinkedIn, RSS, etc).…, GupyCollector, Any, Job (+14 more)

### Community 2 - ".evaluate"
Cohesion: 0.11
Nodes (14): CandidateProfile, DeterministicJobEvaluator, EvaluationResult, EvaluationStatus, ELIGIBLE, INELIGIBLE, NEEDS_REVIEW, Evidence (+6 more)

### Community 3 - "StateStore"
Cohesion: 0.07
Nodes (12): Any, Registra a trilha de auditoria para responder por que cada vaga foi aceita ou…, Mantém o tamanho do arquivo de estado sob controle estrito (ADR-001). Evita…, Verifica se a vaga já foi vista por fingerprint ou por ID específico., Persistência do estado do monitor (fingerprints vistas, datas e heartbeat)., Registra uma chamada ao LLM no contador diário (RPD tracking). NOTA DE…, Retorna o uso diário de chamadas ao LLM., StateStore (+4 more)

### Community 4 - "RssCollector"
Cohesion: 0.09
Nodes (17): Any, Job, Session, Aplica keyword/exclude_keyword filters do config ao título do item RSS., Coletor de vagas via feeds RSS 2.0 e Atom com suporte à SPEC-008., Faz fetch e parse do XML do feed, retorna lista de {id, title, link, pub_date}., RssCollector, calculate_rss_relevance() (+9 more)

### Community 5 - "rss_collector.py"
Cohesion: 0.13
Nodes (24): classify_freshness(), parse_feed_datetime(), Faz parse robusto de timestamps de feeds (RFC-822/1123 e ISO-8601), convertendo…, Classifica recência da vaga sem assunções destrutivas. Retorna (status,…, calculate_noise_score(), Session, Remove parâmetros de tracking e fragmentos da URL, gerando uma URL canônica…, Calcula pontuação de ruído anti-agregador (SPEC-008). Detecta páginas de busca… (+16 more)

### Community 6 - "evaluate_job"
Cohesion: 0.11
Nodes (21): _call_anthropic(), _call_gemini(), _enforce_pacing(), get_profile(), judge(), Any, LLM Judge: camada semântica que roda em cima do scoring heurístico. Só é…, Chama a API da Anthropic (Claude Haiku). (+13 more)

### Community 7 - "is_pcd_exclusive"
Cohesion: 0.13
Nodes (11): is_pcd_exclusive(), Heurística: detecta se a vaga é afirmativa/exclusiva para PCD com base no…, Testa a heurística de detecção de vaga afirmativa/exclusiva PCD., P.C.D. deve ser detectado após remoção de pontos., Vaga regular sem PCD no título NÃO deve ser bloqueada., PCD mencionado apenas na descrição não deve bloquear (título limpo)., SPCDAM não deve casar com \\bpcd\\b (PCD dentro de palavra)., O campo pcd_signal do Job deve registrar a origem do sinal. (+3 more)

### Community 8 - "TramposCollector"
Cohesion: 0.16
Nodes (14): Job, Session, Coletor de vagas via API pública REST da Trampos.co (SPEC-008). Consome…, TramposCollector, profile_job_evidence(), Any, Job, Avalia a densidade de evidência da vaga (SPEC-008). Classificação: -… (+6 more)

### Community 9 - "GithubIssuesCollector"
Cohesion: 0.16
Nodes (7): GithubIssuesCollector, Job, Session, Coletor de vagas via GitHub Issues (ecossistema aberto de vagas dev no Brasil).…, Tenta extrair o nome da empresa do título padrão de issues de vagas., fixture, TestGithubIssuesCollector

### Community 10 - "monitor.py"
Cohesion: 0.17
Nodes (12): check_heartbeat(), get_http_session(), load_config(), main(), Session, Retorna sessão requests com retentativas automáticas e backoff exponencial., Verifica se deve enviar o heartbeat diário ao Telegram., run_check() (+4 more)

### Community 11 - "test_acceptance_dataset.py"
Cohesion: 0.60
Nodes (4): load_cases(), Consistency checks for the proposed acceptance corpus; not a scoring…, test_corpus_has_unique_cases_and_explicit_review_provenance(), test_identity_scenarios_are_internally_consistent()

## Knowledge Gaps
- **4 isolated node(s):** `com.jobfinder:job-finder-matching`, `ELIGIBLE`, `INELIGIBLE`, `NEEDS_REVIEW`
  These have ≤1 connection - possible missing edges or undocumented components.
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Job` connect `Job` to `LinkedInCollector`, `StateStore`, `RssCollector`, `rss_collector.py`, `evaluate_job`, `is_pcd_exclusive`, `TramposCollector`, `GithubIssuesCollector`, `monitor.py`?**
  _High betweenness centrality (0.387) - this node is a cross-community bridge._
- **Why does `StateStore` connect `StateStore` to `Job`, `LinkedInCollector`, `RssCollector`, `evaluate_job`, `is_pcd_exclusive`, `monitor.py`?**
  _High betweenness centrality (0.111) - this node is a cross-community bridge._
- **Why does `GithubIssuesCollector` connect `GithubIssuesCollector` to `Job`, `LinkedInCollector`, `monitor.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Are the 25 inferred relationships involving `Job` (e.g. with `BaseCollector` and `GithubIssuesCollector`) actually correct?**
  _`Job` has 25 INFERRED edges - model-reasoned connections that need verification._
- **Are the 12 inferred relationships involving `StateStore` (e.g. with `TestEvaluateJobIntegration` and `TestLlmJudgeUnits`) actually correct?**
  _`StateStore` has 12 INFERRED edges - model-reasoned connections that need verification._
- **Are the 11 inferred relationships involving `Deduplicator` (e.g. with `Job` and `TestJobModel`) actually correct?**
  _`Deduplicator` has 11 INFERRED edges - model-reasoned connections that need verification._
- **What connects `com.jobfinder:job-finder-matching`, `ELIGIBLE`, `INELIGIBLE` to the rest of the system?**
  _4 weakly-connected nodes found - possible documentation gaps or missing edges._
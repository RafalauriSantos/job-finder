---
type: community
cohesion: 0.11
members: 27
---

# evaluate_job

**Cohesion:** 0.11 - loosely connected
**Members:** 27 nodes

## Members
- [[dot-test_429_exhaustion_all_models_falls_back_cleanly()]] - code - tests/test_llm_judge.py
- [[dot-test_combined_score_weighting()]] - code - tests/test_llm_judge.py
- [[dot-test_fallback_to_heuristic_when_judge_fails()]] - code - tests/test_llm_judge.py
- [[dot-test_llm_veto_zeros_score()]] - code - tests/test_llm_judge.py
- [[dot-test_skips_judge_when_heuristic_score_below_floor()]] - code - tests/test_llm_judge.py
- [[Any_4]] - code
- [[Avalia a vaga usando o provedor de IA disponível (Gemini Grátis ou Claude).…]] - rationale - core/llm_judge.py
- [[Cenário de pico real 429 persistente em todas as retentativas e em ambos os…]] - rationale - tests/test_llm_judge.py
- [[Chama a API da Anthropic (Claude Haiku).]] - rationale - core/llm_judge.py
- [[Chama a API do Google Gemini com rate pacing (4.5s) e retry com backoff em caso…]] - rationale - core/llm_judge.py
- [[Garante espaçamento de ~4.5s (+ jitter) entre chamadas sucessivas ao LLM (15…]] - rationale - core/llm_judge.py
- [[Job_10]] - code
- [[LLM Judge camada semântica que roda em cima do scoring heurístico. Só é…]] - rationale - core/llm_judge.py
- [[Ponto único de entrada do funil (SPEC-008). Roda o heurístico primeiro (sempre,…]] - rationale - core/scoring.py
- [[Score combinado 30% heurístico + 70% LLM.]] - rationale - tests/test_llm_judge.py
- [[Se o LLM falhar, a vaga preserva seu score heurístico intacto e marca fallback.]] - rationale - tests/test_llm_judge.py
- [[TestEvaluateJobIntegration]] - code - tests/test_llm_judge.py
- [[Vaga com score  30 nem bate na API do LLM.]] - rationale - tests/test_llm_judge.py
- [[Veto do LLM (ex notícia ou desabafo) zera o score e adiciona razão.]] - rationale - tests/test_llm_judge.py
- [[_call_anthropic()]] - code - core/llm_judge.py
- [[_call_gemini()]] - code - core/llm_judge.py
- [[_enforce_pacing()]] - code - core/llm_judge.py
- [[evaluate_job()]] - code - core/scoring.py
- [[get_profile()]] - code - core/llm_judge.py
- [[judge()]] - code - core/llm_judge.py
- [[llm_judge.py]] - code - core/llm_judge.py
- [[should_invoke_judge()]] - code - core/llm_judge.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/evaluate_job
SORT file.name ASC
```

## Connections to other communities
- 16 edges to [[_COMMUNITY_Job]]
- 2 edges to [[_COMMUNITY_RssCollector]]
- 2 edges to [[_COMMUNITY_monitor.py]]
- 1 edge to [[_COMMUNITY_TramposCollector]]
- 1 edge to [[_COMMUNITY_is_pcd_exclusive]]
- 1 edge to [[_COMMUNITY_StateStore]]

## Top bridge nodes
- [[evaluate_job()]] - degree 18, connects to 5 communities
- [[TestEvaluateJobIntegration]] - degree 8, connects to 2 communities
- [[Job_10]] - degree 3, connects to 2 communities
- [[llm_judge.py]] - degree 9, connects to 1 community
- [[get_profile()]] - degree 4, connects to 1 community
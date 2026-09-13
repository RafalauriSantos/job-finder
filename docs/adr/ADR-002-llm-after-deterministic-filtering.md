# ADR-002: Deterministic Filtering Before LLM Evaluation

- **Status**: Accepted (Retrospectively documented)
- **Decision Date**: Originates from LLM integration (commit `4ad19ef`)
- **Documented**: 2026-09-13

## Context
Evaluating job descriptions using Large Language Models (LLMs) allows deep semantic understanding of job requirements versus a candidate profile. However, external LLM APIs involve network latency, request rate limits, potential usage costs, and probabilistic output variability.

## Decision
Never send raw, unvetted job listings directly to the LLM. All candidate opportunities must first traverse deterministic filtering gates (location matching, affirmative-action PCD heuristic, explicit seniority exclusion) and exceed a minimum relevance score threshold before qualifying for semantic evaluation.

## Alternatives Considered
1. **End-to-End LLM Filtering**: Pass every collected raw job directly to the LLM. Discarded due to rapid quota exhaustion, high latency, and unnecessary processing of clearly non-matching roles.
2. **Purely Heuristic Engine**: Rely solely on regex and keyword counts without LLM. Discarded due to inability to resolve ambiguous descriptions, modern versus legacy stack nuances, or deceptive junior titles.

## Consequences

### Positive
- Substantially reduces the number of LLM API calls.
- Reduces the probability of exhausting available API quotas.
- Lowers batch cycle execution latency.
- Guarantees deterministic rejection of obvious non-matches (e.g., explicit Senior roles or incompatible geographical locations).

### Negative & Trade-offs
- If deterministic regexes or location rules are overly strict, a potentially valid job could be eliminated before the LLM can evaluate it (mitigated by Ground Truth test suites).

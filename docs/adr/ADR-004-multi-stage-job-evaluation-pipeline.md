# ADR-004: Multi-Stage Job Evaluation Pipeline

- **Status**: Accepted (Retrospectively documented)
- **Decision Date**: Originates from modular architecture (commit `4c239c0`) and evidence profiling (commit `b1c9aae`)
- **Documented**: 2026-09-13

## Context
Determining whether a newly discovered job opening is genuinely relevant to a candidate cannot be resolved cleanly by a single boolean check or naive keyword search. Simple filters produce high false-positive rates (e.g., senior positions containing "junior" in mentorship expectations) or high false-negative rates (e.g., relevant roles written in natural language without exact keyword matches).

## Decision
Organize candidate job evaluation into a progressive multi-stage processing pipeline:

```
Stage 1: Discovery (Heterogeneous collectors with source-specific constraints)
               ↓
Stage 2: Deterministic Guards (Fast rejection: location, affirmative PCD, explicit senior)
               ↓
Stage 3: Heuristic Scoring (-100 to +100 based on stack signals and entry-level indicators)
               ↓
Stage 4: Evidence Density Profiling (Assess text richness: HIGH, MEDIUM, LOW)
               ↓
Stage 5: Semantic Verification (Constrained LLM evaluation against candidate CV profile)
               ↓
Stage 6: Audit Trail & Dispatch (Record verdict in seen_jobs.json; notify via Telegram)
```

## Consequences

### Positive
- Clear separation of concerns across pipeline stages.
- Each stage can be independently tested with deterministic unit test suites.
- Decisions are fully auditable through recorded reasons and scores in the state store.
- Balanced recall in early stages with high precision in later stages.

### Negative & Trade-offs
- Multiple sequential stages require well-defined data contracts (`Job` model) across all layers.
- Adds architectural complexity compared to a single-script filter.

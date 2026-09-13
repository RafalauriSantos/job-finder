# Engineering Methodology

## Evolution of Development Process

The project did not begin with a formal specification-driven process. It evolved incrementally as operational requirements and domain edge cases emerged.

Early phases prioritized rapid discovery and multi-channel ingestion. As the system grew to handle multiple heterogeneous sources, subtle deduplication edge cases, and external rate limits, development shifted toward an explicit specification-driven and test-driven workflow.

### Current Workflow for System Changes

For architectural, core scoring, or ingestion modifications, changes follow this cycle:

```
Demand / Operational Edge Case
               ↓
Specification & Failure Analysis
               ↓
Acceptance Criteria Definition
               ↓
Ground-Truth Fixtures & Unit Tests
               ↓
Implementation in Core / Collectors
               ↓
Automated Verification (pytest)
               ↓
Operational / Batch Verification
```

Test-first development is used where appropriate for core logic and regression-sensitive changes, backed by deterministic test fixtures.

---

## AI in the Engineering Lifecycle

To maintain technical clarity, artificial intelligence is categorized into two distinct roles within this project:

### 1. AI-Assisted Development (Build Time)
Large Language Models (LLMs) are used during the development phase as engineering support tools for:
- Exploring alternative architectural patterns and trade-offs.
- Generating adversarial test cases and realistic job payload fixtures.
- Drafting initial boilerplate implementations based on strict interface contracts.
- Identifying edge cases in string normalization, regex patterns, and character encoding.

**Rule of Trust**: Code and tests produced with AI assistance are never assumed correct by default. Every behavior must be validated through automated test execution and observable runtime behavior.

### 2. AI at Runtime (Execution Pipeline)
At runtime, an LLM (`gemini-2.5-flash-lite`) acts strictly as a **Semantic Judge** in an isolated stage of the processing pipeline:
- It is **not** the primary discovery mechanism (collectors handle discovery).
- It is **not** invoked for all incoming items (deterministic heuristics filter out non-matches first).
- It evaluates whether a job's stated requirements, responsibilities, and stack match the candidate's actual profile when keyword matching produces ambiguity.
- It receives structured evidence extracted by the pipeline and is constrained to a binary verdict schema accompanied by a concise explanation.

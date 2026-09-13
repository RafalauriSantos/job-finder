# Evolution History

This document records the architectural and operational progression of the project, reconstructed directly from the repository commit history.

## 1. Initial Gupy Monitor (Commits 4586140 → 54cfb2f)
- **Problem**: Need an automated way to track software engineering job openings on Gupy without manual polling.
- **Change**: Created an initial script querying Gupy's public search endpoint, formatting notifications for Telegram, and running periodically via GitHub Actions.
- **Consequence**: State was stored in `seen_jobs.json` and committed back to the repository to avoid duplicate alerts without requiring an external database.

## 2. Operational Resilience & Target Company Radars (Commits 5243a4c → cf28ebb)
- **Problem**: Network transient failures, rate limits, and character encoding issues (UTF-8) on Gupy's API caused lost runs or corrupted messages.
- **Change**: Added HTTP retries with exponential backoff (`urllib3.util.retry`), UTF-8 response handling, daily health heartbeats, and dedicated query profiles for targeted companies (Goomer, GFT, Flavia Nasser).
- **Consequence**: Reduced operational failures caused by transient drops; established focused monitoring for specific target organizations.

## 3. LinkedIn Ingestion & Regional Filtering (Commits f1c5612 → 5454e76)
- **Problem**: Key opportunities were posted exclusively on LinkedIn, and many listed jobs required on-site presence outside the candidate's geographical reach.
- **Change**: Integrated an unauthenticated LinkedIn Guest Search collector (avoiding credentials and session expiration). Added geographic normalizer enforcing remote work or specific regional municipalities (Sorocaba, Tatuí, Itapetininga, Boituva).
- **Consequence**: Increased ingestion recall while filtering out non-relocatable on-site positions.

## 4. Modular Architecture & Ground-Truth Testing (Commits 4c239c0 → a1d3754)
- **Problem**: Monolithic script became hard to maintain, evaluate, and test as collection channels multiplied. False positives (e.g., senior roles misclassified as junior) were leaking through.
- **Change**: Refactored monolithic script into a clean layered structure (`models/`, `collectors/`, `core/`, `storage/`, `notify/`). Introduced scoring engine (-100 to +100), word-boundary regex for seniority detection, collector telemetry, and automated tests with ground-truth fixtures.
- **Consequence**: Deterministic rejection of Senior roles and non-regional positions, with test suites verifying regression prevention.

## 5. Semantic Evaluation & Multi-Source Expansion (Commits 4ad19ef → ead7457)
- **Problem**: Keyword matching alone cannot reliably distinguish between junior roles with modern stacks versus legacy stacks or misleading titles. GitHub communities (`vagas-br`) and RSS indices (Google News / Indeed) presented unstructured text.
- **Change**: Added `GithubIssuesCollector`, `RssCollector`, and an optional LLM-based semantic judge (`gemini-2.5-flash-lite`). Added an affirmative-action (PCD) title heuristic to prevent false positives from generic diversity disclaimers. Added rate-pacing (4.5s) and 429 backoff tracking.
- **Consequence**: Jobs with high or ambiguous scores can be evaluated against the candidate's actual curriculum by an LLM without incurring cost on obvious non-matches.

## 6. Identity, Evidence & Hardening (Commits 4802126 → b1c9aae)
- **Problem**: The same opening published across Gupy, LinkedIn, and GitHub generated duplicate alerts. URLs contained volatile tracking parameters. Incomplete RSS snippets consumed LLM calls unnecessarily.
- **Change**: Decoupled `identity_fingerprint` (canonical company + normalized title + workplace type) from `content_hash`. Implemented tripartite URL resolution (`raw` → `resolved` → `canonical`) with anti-noise scoring. Added `EvidenceDensityProfiler` so the LLM is only invoked when sufficient textual evidence exists. Added `TramposCollector` and a sliding-window decision audit trail in `seen_jobs.json`.
- **Consequence**: Cross-channel deduplication, reduced URL tracking noise, reduced unnecessary LLM usage while helping preserve available quota, and expanded test suite to 84 passing test cases.

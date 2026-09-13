# ADR-003: Identity and Content Decoupling

- **Status**: Accepted (Retrospectively documented)
- **Decision Date**: Originates from fingerprint refactoring (commit `4802126`)
- **Documented**: 2026-09-13

## Context
Hiring opportunities are regularly posted across multiple recruitment channels (e.g., Gupy, LinkedIn, and GitHub Issues) with disparate URLs, formatting variations, and minor textual revisions over time. Using a single naive hash (such as URL hash or full description hash) caused two failure modes:
1. Duplicate alerts when the same job was discovered through different sources.
2. Missed duplicate detection or unwanted re-alerts when a recruiter edited a minor typo in the job description.

## Decision
Decouple job uniqueness into two distinct identifiers:
1. `identity_fingerprint`: A deterministic hash composed of `canonical_company + normalized_title + workplace_type`. Answers: *"Is this conceptually the same opening?"*
2. `content_hash`: A hash of the normalized description text. Answers: *"Has the descriptive content of this opening materially changed?"*

## Alternatives Considered
1. **Source-Specific ID Matching**: Store only platform IDs (e.g., Gupy job ID, LinkedIn job ID). Fails to identify cross-platform postings of the same vacancy.
2. **Full Text Exact Hashing**: A single change in punctuation or whitespace yields a completely different hash, triggering duplicate notifications for the same opening.

## Consequences

### Positive
- Cross-channel deduplication accurately identifies equivalent jobs regardless of source platform.
- Textual updates can be tracked independently without treating the job as a brand-new posting.

### Negative & Trade-offs
- Multiple distinct openings at the same company that share an identical generic title (e.g., two distinct "Desenvolvedor Júnior" openings across different teams) could collide if not differentiated by workplace type or explicit IDs.

# ADR-001: Git-Based State Persistence

- **Status**: Accepted (Retrospectively documented)
- **Decision Date**: Originates from initial implementation (commit `54cfb2f`)
- **Documented**: 2026-09-13

## Context
The monitoring runner executes periodically via GitHub Actions in ephemeral virtual machine runners. It must remember which job IDs and fingerprints have already been observed and alerted on, in order to prevent redundant notifications across runs.

## Decision
Persist execution state and observed identifiers directly in a JSON file (`seen_jobs.json`) versioned within the Git repository, committing and pushing changes back to the repository branch at the end of each run.

## Alternatives Considered
1. **External Managed Database (e.g., Supabase / Cloud SQL)**: Adds credential management, network dependencies, connection pool setup, and potential hosting maintenance costs.
2. **Key-Value Cache (e.g., Redis / Upstash)**: Provides high write throughput, but introduces an external point of failure and additional infrastructure configuration for a low-volume batch process.
3. **Artifact Storage**: Ephemeral and requires manual retention cleanup; lacks commit history.

## Consequences

### Positive
- No additional infrastructure or database hosting cost.
- Fully compatible with standard GitHub Actions execution model.
- Minimal operational complexity with native Git diff visibility for state changes.
- State history is versioned and auditable over time.

### Negative & Trade-offs
- Not suitable for concurrent multi-worker execution.
- Introduces potential merge conflicts if simultaneous runs overlap (mitigated by serialized cron scheduling).
- Mixes operational runtime state with repository code history.

## Why This is Acceptable Now
The system is a single-user / single-profile scheduled batch process operating at small scale, where simplicity and self-contained operation outweigh the need for high-concurrency database storage.

# Job Finder Reliability and Quality Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the local Job Finder runner recoverable and observable, ensure alerts carry defensible freshness evidence, and measure vacancy relevance with Rafael's feedback.

**Architecture:** Keep the existing Python collectors, SQLite state, deterministic filters, optional LLM judge, and Telegram/Resend delivery. Implement this as three independently testable workstreams: local runner reliability, source freshness/coverage, and relevance feedback. Do not combine these changes with the planned Java/Hermes migration.

**Tech Stack:** Python 3.12, pytest, requests, SQLite, Windows Startup/Task Scheduler, Telegram, Resend.

## Global Constraints

- Preserve the current five collector families: LinkedIn, Gupy, GitHub Issues, RSS, and Trampos.
- Do not add sources, redesign scoring, or migrate the production radar to Java in this plan.
- Test runs and simulations must not send real notifications or mutate production state.
- Never resend an `UNKNOWN` delivery until its outcome has been reconciled.
- Keep credentials outside the repository, logs, and exported diagnostic data.
- Keep the weekday three-hour / weekend one-hour collection policy and one-overdue-cycle behavior unless a separately reviewed change is approved.
- Normalize timestamps to timezone-aware UTC for comparison; use `America/Sao_Paulo` only for local scheduling and display.
- Preserve source-specific freshness limits as configuration; do not silently turn an unknown date into a verified recent date.

## Baseline and File Map

### Verified snapshot: 2026-09-22

- [x] Full project suite passed: `.tools/python312/python.exe -m pytest -q` -> 183 passed.
- [x] Isolated dry-run consulted all configured source families without changing production state or sending notifications.
- [x] One real cycle completed: 150 raw records, 82 unique jobs, 68 duplicates, 6 notifications recorded delivered, 9 LLM calls, 0 LLM fallbacks, and no source failures reported.
- [x] A runner that had not produced observable cycles since the prior evening was restarted; its overdue real cycle then completed.
- [x] Confirmed source gaps: Gupy returned 20 candidates without usable publication dates; LinkedIn queries use `r7200` and do not persist an independently parsed publication timestamp; Trampos has no age filter; RSS can retain unknown-date entries.
- [ ] Reconcile one historical `UNKNOWN` notification from 2026-09-20; do not retry it blindly.
- [ ] Observe the next scheduled cycle and confirm the restarted loop continues checking.
- [ ] Diagnose why the old runner stayed alive without observable progress; restart alone is not a root-cause fix.

### Files likely to change

- `deployment/run_local.py`: loop lifecycle, watchdog signal, logging, and child-cycle execution.
- `core/local_runtime.py`: diagnostic data, cycle state, and recovery behavior.
- `core/local_schedule.py`: schedule behavior only if tests expose a real boundary defect.
- `models/job.py`: serialized publication-time evidence if the chosen freshness contract requires it.
- `core/freshness.py` (new, only if a shared assessment removes duplication): source-neutral freshness assessment.
- `collectors/linkedin_collector.py`, `collectors/gupy_collector.py`, `collectors/github_collector.py`, `collectors/rss_collector.py`, `collectors/trampos_collector.py`: source-specific freshness and coverage evidence.
- `collectors/base.py`, `monitor.py`, `core/metrics.py`: normalized source outcomes and health report.
- `core/durable_delivery.py`, `storage/sqlite_store.py`, `feedback_cli.py`: only where delivery reconciliation or human feedback requires persistence changes.
- `tests/test_local_runtime.py`, `tests/test_gupy_collector.py`, `tests/test_linkedin_collector.py`, `tests/test_github_collector.py`, `tests/test_rss_enrichment.py`, `tests/test_trampos_collector.py`, `tests/test_collector_contracts.py`, `tests/test_monitor_integration.py`, `tests/test_delivery_workflow.py`: focused regression coverage.
- `docs/engineering/local-reliability.md`: update operational truth after the rollout, including the login/sleep limitation and verified evidence.

---

## Workstream A: Delivery and Local Runner Reliability

### Task A1: Reconcile the uncertain historical delivery

**Files:** Read `%LOCALAPPDATA%/JobFinder/state.db` and the private runtime logs; modify delivery state only through an audited store operation.

- [ ] Inspect the `UNKNOWN` outbox payload and identify its vacancy and Telegram attempt time without exposing credentials.
- [ ] Compare that attempt with Telegram's conversation history or another authoritative delivery receipt.
- [ ] If receipt is confirmed, mark the existing attempt/outbox record delivered and record the evidence; do not create a new notification.
- [ ] If receipt is disproven, record the failed outcome first and authorize a single retry for that fingerprint.
- [ ] If outcome cannot be established, leave it `UNKNOWN`, record the unresolved reason, and show it in diagnostics. Do not guess.
- [ ] Add or extend a test in `tests/test_delivery_workflow.py` proving an `UNKNOWN` item is not automatically retried and that an explicit reconciliation changes only the intended fingerprint.
- [ ] Run `.tools/python312/python.exe -m pytest tests/test_delivery_workflow.py tests/test_local_runtime.py -q` and confirm no live message was sent.

**Acceptance:** No uncertain item is silently dropped or duplicated; its final state has an auditable reason.

### Task A2: Reproduce and diagnose the stalled runner

**Files:** `deployment/run_local.py`, `core/local_runtime.py`, `tests/test_local_runtime.py`, and a focused new `tests/test_local_runner.py` if needed.

- [ ] Record the current runner PID, start time, command line, last heartbeat, last completed cycle, and child-process state.
- [ ] Add a regression test for a runner process that remains alive but stops making check progress; the test must fail before the fix.
- [ ] Make each five-minute watchdog check write a timestamped heartbeat and structured outcome (`NOT_DUE`, `COMPLETED`, `DEGRADED`, `FAILED`, `TIMED_OUT`, or `BUSY`).
- [ ] Ensure child output and exceptions reach the private rotating log even when the parent uses `pythonw.exe`.
- [ ] Ensure a timed-out child cannot continue as an orphan and cannot hold the process lock indefinitely.
- [ ] Extend `--diagnose` to report runner heartbeat age, last cycle, due state, lock state, unresolved deliveries, and the effective data directory.
- [ ] Verify a failed child is retried on a later watchdog check, not in a tight loop; verify a healthy active cycle is never interrupted by a second trigger.
- [ ] Run the focused tests, then the full suite: `.tools/python312/python.exe -m pytest -q`.

**Acceptance:** An alive-but-stalled process becomes visible within ten minutes; one failed cycle does not permanently disable future checks; there is never more than one active cycle.

### Task A3: Make Windows startup behavior explicit and recoverable

**Files:** `deployment/install_startup_runner.ps1`, `deployment/install_local_task.ps1`, `docs/engineering/local-reliability.md`.

- [ ] Inspect whether a user-level scheduled task can be registered with restart-on-failure on this machine; do not assume elevated or pre-login privileges.
- [ ] Prefer a task with an explicit logon trigger and restart policy if registration is permitted; otherwise keep the Startup shortcut and document that it starts only after login.
- [ ] Test that installation does not create duplicate shortcuts/tasks or launch a second runner.
- [ ] Test restart after a simulated runner exit and confirm the process lock prevents overlap.
- [ ] Document that sleep, shutdown, network loss, and an unlogged-in session pause local collection; do not claim 24/7 availability.
- [ ] Reconfirm GitHub Actions is not an active competing producer before any production scheduling change.

**Acceptance:** There is one documented production trigger. The exact login requirement is verified on this machine, and duplicate schedulers cannot be active together.

### Task A4: Reconcile cycle time budget

**Files:** `config.json`, `deployment/run_local.py`, `monitor.py`, and the relevant monitor/runtime tests.

- [ ] Measure per-source and per-stage durations for at least three controlled runs before changing concurrency or limits.
- [ ] Add a regression test that an operational-budget breach is recorded as degraded even if the collection eventually succeeds.
- [ ] Keep the hard child timeout above the measured normal cycle duration; do not solve duration by silently dropping configured queries or sources.
- [ ] Optimize only demonstrated bottlenecks (for example, bounded independent source calls or avoiding repeated enrichment), preserving request timeouts and rate limits.
- [ ] Run isolated simulation and verify all currently configured sources and query counts remain present.

**Acceptance:** All cycles finish under the hard timeout; target p95 duration is at most 150 seconds over the observation period, giving headroom against the 180-second operational budget. Any breach is visible and does not report an unqualified success.

---

## Workstream B: Freshness and Source Coverage

### Task B1: Define a shared freshness contract

**Files:** `core/freshness.py` (new if justified), `models/job.py`, `tests/test_temporal_parser.py`, and serialization tests for `Job`.

- [ ] Add test cases first for recent, exactly-at-cutoff, stale, missing, invalid, timezone-naive, and future timestamps.
- [ ] Define one assessment result with status `RECENT`, `STALE`, or `UNKNOWN`, the parsed publication time, observation time, age, evidence source, and reason.
- [ ] Distinguish a platform publication timestamp from a search-window filter and from an inferred/unknown date.
- [ ] Keep comparisons timezone-aware and deterministic by injecting `now` into the assessment function.
- [ ] Preserve backward compatibility when serializing/deserializing existing `Job` records that lack freshness evidence.
- [ ] Run focused tests and confirm old stored jobs still load.

**Acceptance:** Every source can express what it knows about age without inventing a timestamp; existing SQLite job payloads remain readable.

### Task B2: Enforce freshness for Trampos

**Files:** `collectors/trampos_collector.py`, `config.json`, `tests/test_trampos_collector.py`, `tests/test_collector_contracts.py`.

- [ ] Add failing tests for fresh, older-than-cutoff, missing, malformed, and future `published_at` values.
- [ ] Add a configurable `max_age_hours` for Trampos; initially compare 24-hour and 72-hour dry-run yields before selecting the production value.
- [ ] Exclude confirmed-stale vacancies; count them separately from keyword-filtered vacancies.
- [ ] Retain unknown-age items only as `UNKNOWN` evidence; route them to review or suppress automatic alerting according to the accepted policy, never label them recent.
- [ ] Record API page count, raw count, filtered count, stale count, unknown-date count, and eligible count.
- [ ] Test pagination and stop conditions using deterministic fixtures; do not make real network calls in unit tests.
- [ ] Run `.tools/python312/python.exe -m pytest tests/test_trampos_collector.py tests/test_collector_contracts.py -q`.

**Acceptance:** No Trampos alert exceeds the configured age limit; missing or invalid dates are visible and cannot masquerade as current.

### Task B3: Verify LinkedIn posting time rather than trusting the query alone

**Files:** `collectors/linkedin_collector.py`, `config.json`, `tests/test_linkedin_collector.py`, `tests/test_query_planner_freshness.py`.

- [ ] Add fixtures for LinkedIn cards with exact timestamps, relative time labels, missing time labels, and malformed markup.
- [ ] Parse the displayed posting-time evidence where available and anchor relative labels to the injected observation time.
- [ ] Record `f_TPR` as search-window evidence when no card timestamp can be extracted; do not claim an exact publication time from the filter alone.
- [ ] Compare `r3600` (one hour) and current `r7200` (two hours) in isolated runs by query, unique job ID, and eligible count before changing production configuration.
- [ ] Keep query wording, pagination, and page caps unchanged during this comparison so the effect of the time window is measurable.
- [ ] Decide whether unknown-time results are sent, held for review, or suppressed; record the policy and expose the evidence level in the alert.
- [ ] Verify every query reports requested window, pages, cards, parsed jobs, time-evidence counts, and failures.
- [ ] Run focused collector/planner tests and an isolated live dry-run; do not send alerts during comparison.

**Acceptance:** Every LinkedIn alert records either a validated posting time or an explicitly identified query-window-only basis. The chosen one-hour/two-hour setting is supported by observed yield and freshness evidence.

### Task B4: Make Gupy's missing dates visible and recoverable

**Files:** `collectors/gupy_collector.py`, `collectors/base.py`, `monitor.py`, `tests/test_gupy_collector.py`, `tests/test_collector_contracts.py`.

- [ ] Add tests proving a successful API response with candidates missing dates is not reported as a fully healthy, complete search.
- [ ] For candidates missing dates, use the existing bounded detail endpoint when within the enrichment budget; record whether detail enrichment supplied a usable timestamp.
- [ ] Count returned candidates, date-missing candidates, invalid dates, stale candidates, accepted jobs, and detail calls per query.
- [ ] Represent all-candidates-discarded-for-missing-date as a degraded/insufficient-freshness result, not plain `OK`.
- [ ] Preserve the strict configured age limit unless a measured policy change is separately reviewed.
- [ ] Run Gupy and collector-contract tests with network disabled.

**Acceptance:** A Gupy query that returns candidates but yields zero eligible vacancies due to missing dates is explicitly visible in the cycle report and operational alert policy.

### Task B5: Audit freshness and pagination for GitHub and RSS

**Files:** `collectors/github_collector.py`, `collectors/rss_collector.py`, `config.json`, `tests/test_github_collector.py`, `tests/test_rss_enrichment.py`, `tests/test_temporal_parser.py`.

- [ ] Add tests for issue creation time versus update time; only creation time determines vacancy age.
- [ ] Measure whether old-but-recently-updated issues can occupy the current first three pages and hide new issues.
- [ ] Compare the current repository issues endpoint with a created-date-filtered GitHub search strategy, including unauthenticated/authenticated rate-limit behavior, before changing endpoints.
- [ ] Preserve and report repository/page coverage; distinguish zero recent issues from unqueried repositories or failed pages.
- [ ] Add RSS tests for stale, recent, missing, and invalid dates, including the configured per-feed age limit and official-feed exceptions.
- [ ] Count RSS unknown-date items and show whether each was held, retained, or discarded.
- [ ] Run all source tests offline with fixtures; use a separate explicit dry-run for live source verification.

**Acceptance:** GitHub's 24-hour window and pagination coverage are explainable; RSS's treatment of unknown dates is visible and consistent with its configured policy.

### Task B6: Normalize collection health outcomes

**Files:** `collectors/base.py`, `monitor.py`, `core/metrics.py`, `tests/test_collector_contracts.py`, `tests/test_monitor_integration.py`, `tests/test_metrics.py`.

- [ ] Add tests for successful non-empty, successful empty, partial-with-results, partial-without-results, invalid response, parse failure, and timestamp-data insufficiency.
- [ ] Represent per-query/per-page issues rather than collapsing them into a single source-wide string.
- [ ] Ensure warnings such as `MISSING_PUBLICATION_DATE` affect source coverage status.
- [ ] Keep source failure isolated: valid results from other sources must survive one source's failure.
- [ ] Extend `cycle_health.json` with raw, accepted, stale, unknown-age, duplicate, filtered, and failed counts by source.
- [ ] Verify the human-readable report and persisted health report contain the same status/counts.

**Acceptance:** `OK` means a completed interpretable query; empty, partial, degraded, and failed coverage are distinguishable in both logs and persisted diagnostics.

---

## Workstream C: Relevance and Human Feedback

### Task C1: Establish a feedback baseline before retuning scores

**Files:** `feedback_cli.py`, `core/metrics.py`, `tests/test_feedback.py`, `tests/test_feedback_cli.py`, `docs/engineering/methodology.md`.

- [ ] Review the six real alerts from the verified cycle and label each as relevant, irrelevant, or uncertain; preserve the reason and do not infer a label from delivery success.
- [ ] Add a report of precision based only on explicit human labels; keep recall as `N/D` until there is a defensible set of missed vacancies.
- [ ] Capture false-positive categories: seniority, education requirement, location/work mode, technology mismatch, stale/uncertain age, and application destination.
- [ ] Capture false-negative examples from vacancies Rafael found manually, including the source and search term where known.
- [ ] Do not alter score weights until a minimum review sample exists; document that sample threshold before tuning.
- [ ] Add fixture-backed regression cases for any confirmed false positive/negative before changing filters.

**Acceptance:** Quality changes are tied to labeled examples; delivery counts are never reported as relevance or precision.

### Task C2: Validate candidate relevance and destination links

**Files:** `core/url_resolver.py`, `core/evidence.py`, `core/eligibility.py`, `tests/test_url_resolution.py`, `tests/test_eligibility.py`, `tests/test_fixtures_ground_truth.py`.

- [ ] For each reviewed alert, verify the resolved destination domain and whether it reaches the employer or application system.
- [ ] Record aggregator/intermediate redirects separately from the final application URL.
- [ ] Add fixtures for dead links, redirect chains, login walls, and destination mismatch.
- [ ] Keep uncertain application destinations visible in the alert; do not represent a search-result URL as a verified application link.
- [ ] Do not change seniority or score weights in this task; feed confirmed cases into the later calibration decision.

**Acceptance:** Every delivered vacancy has a usable source link and an explicit destination-confidence result.

---

## Rollout Gates

### Gate 1: Local regression safety

- [ ] All new behavior has a failing test first, followed by the minimal implementation and a passing focused test.
- [ ] Run the full suite: `.tools/python312/python.exe -m pytest -q`.
- [ ] Run `.tools/python312/python.exe -m compileall core collectors deployment monitor.py`.
- [ ] Run `git diff --check` and inspect the complete diff for unrelated changes and secret leakage.
- [ ] Confirm ordinary tests and simulations cannot send Telegram/Resend messages or modify `%LOCALAPPDATA%/JobFinder/state.db`.

### Gate 2: Isolated end-to-end simulation

- [ ] Run `deployment/run_local.py --diagnose` and save a redacted baseline.
- [ ] Run `deployment/run_local.py --dry-run` against copied state and confirm all configured sources/queries are represented.
- [ ] Verify the run report accounts for every raw candidate as accepted, duplicate, filtered, stale, unknown-age, or failed.
- [ ] Compare the one-hour and two-hour LinkedIn windows and Trampos age thresholds using the same date-stamped sample window.
- [ ] Confirm production database hashes/state and notification history are unchanged by simulation.

### Gate 3: Controlled production validation

- [ ] Take and validate a SQLite backup before the first production change.
- [ ] Reconcile the historical `UNKNOWN` delivery before any notification workflow change.
- [ ] Pause any other producer before enabling/replacing a local trigger; never run GitHub Actions and local production collection together.
- [ ] Run one controlled real cycle and inspect source health, freshness evidence, accepted jobs, duplicate count, decisions, Telegram status, and Resend fallback status.
- [ ] Confirm one alert delivery per fingerprint and no automatic retry of uncertain attempts.
- [ ] Verify the runner heartbeat and next due time after completion.

### Gate 4: Seven-day operational observation

- [ ] Observe at least seven consecutive days while the notebook is available, including weekdays and a weekend.
- [ ] Record each expected and actual check, cycle duration, source status, freshness coverage, raw/accepted counts, notification outcome, and runner heartbeat.
- [ ] Investigate every missed due window, unknown notification, source degradation, stale alert, or duplicate.
- [ ] Confirm p95 cycle duration is at most 150 seconds and no cycle exceeds the 240-second hard timeout.
- [ ] Confirm no overlapping cycles, no unexplained lost state, and no controlled duplicate delivery.
- [ ] At the end, update `docs/engineering/local-reliability.md` with real evidence and remaining limitations; never claim uptime while the notebook sleeps or is off.

## Definition of Done

- [ ] Historical uncertain delivery is reconciled or explicitly remains unresolved without retry.
- [ ] The runner's last check and last success are diagnosable; a stalled loop is detected within ten minutes and recovers without overlap.
- [ ] Every automated alert has a publication timestamp or explicit trusted search-window evidence; unknown age is never silently called recent.
- [ ] Trampos age, LinkedIn card/query evidence, Gupy missing-date counts, RSS unknown-date counts, and GitHub pagination are represented in reports.
- [ ] Source status distinguishes healthy-empty from partial, insufficient freshness data, and failure.
- [ ] Relevance metrics are based on Rafael's labels, not merely the number of delivered alerts.
- [ ] Full test suite, isolated simulation, controlled cycle, backup restore, and seven-day observation are documented.
- [ ] No Java/Hermes migration or unrelated score/source redesign was included.

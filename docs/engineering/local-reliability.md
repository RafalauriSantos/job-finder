# Local reliability rollout

Status: local production runner active; independent pre-login Task Scheduler execution remains
blocked by Windows permissions. On 2026-09-20, S4U and interactive task registration returned
Access denied, so the startup fallback is used.

The no-elevation fallback is `deployment/install_startup_runner.ps1`. It runs after the
Windows user logs in, checks every five minutes, and uses the same SQLite/process lock. It
does not satisfy pre-login execution; it is the practical fallback for this machine when
Task Scheduler registration is denied. Existing GitHub startup shortcuts are moved to a
timestamped backup folder by the installer rather than deleted.

## Verification record (2026-09-20)

- `.tools/python312/python.exe -m pytest -q`: 166 project tests passed;
  16 are local infrastructure regression scenarios. Socket connections are denied by default.
- Coverage includes stale writer refusal, transaction rollback, corrupt state, repeat migration,
  backup reopening, expired delivery claim, process lock release, timezone boundaries,
  namespaced identity, confirmed fallback, uncertain delivery and source recovery alerts.
- `git diff --check` passed (Windows line-ending warnings only).
- Downloads and the existing runner's JSON state had identical SHA-256 hashes when inspected.
- No real notification, logged-out execution or seven-day observation was performed.
- Existing uncommitted changes were preserved. This branch is not deployed or pushed.
- Controlled dry-run reached all configured sources without notification side effects:
  Gupy 26, LinkedIn 117, RSS 48, GitHub 2 raw jobs; 193 raw, 116 unique, 4 location
  rejects, 44 level rejects, 47 score rejects, 21 would-be alerts, 53.5 seconds, no
  source failures. Ten jobs used the heuristic fallback because no live AI provider was
  available in the isolated run. Production SQLite remained unchanged.
- First real local cycle completed at 2026-09-20: Gupy 26, LinkedIn 117, RSS 47,
  GitHub 2; 192 raw, 115 unique, 18 alerts delivered, 9 LLM calls, 0 pending and
  0 uncertain channel attempts. The local `pythonw` loop remained alive afterward;
  diagnosis reported `COMPLETED`, `due=false`, next cycle one hour later.
- GitHub workflow `Job Monitor` was disabled remotely (`disabled_manually`, workflow id
  353470765). Its local YAML is also configured as disabled, preventing accidental manual
  production runs.
- The persistent loop catches unexpected cycle exceptions, records the exception type and
  remains alive for the next five-minute check instead of waiting for another Windows login.
- First real local cycle completed at 2026-09-20: Gupy 26, LinkedIn 117, RSS 47,
  GitHub 2; 192 raw, 115 unique, 18 alerts delivered, 9 LLM calls, 0 pending and
  0 uncertain channel attempts. The local `pythonw` loop remained alive afterward;
  diagnosis reported `COMPLETED`, `due=false`, next cycle one hour later.
- GitHub schedule was removed and its job was disabled for manual dispatch. The active
  production process is the local runner only.

## Decisions

- Python remains the production implementation; Java/PostgreSQL is a later migration.
- SQLite uses transactional compatibility state plus separate jobs, outbox, channel attempts,
  cycle records and append-only decision/source events. The snapshot is a temporary adapter,
  not the final Java domain model. Concurrent stale writers fail instead of overwriting.
- OS process lock covers the entire local cycle, including manual executions through the launcher.
- Timezone is America/Sao_Paulo. Scheduling checks every five minutes; one overdue cycle
  runs after offline time. No backlog replay. Weekends use one hour; weekdays three hours.
- Unknown notification outcomes require investigation; they are not automatically retried.
- Source collection success does not prove vacancy relevance or complete source coverage.

## Commands

Use a dedicated Python environment with requirements installed beforehand.
The windowless entry point is `deployment/run_local.py` (use python.exe for interactive diagnosis).
Data defaults to `%LOCALAPPDATA%/JobFinder`; JOB_FINDER_DATA_DIR overrides it.
Keep `secrets.env` in that private directory, never in Git. Restrict directory permissions
to the owner and SYSTEM before importing real state.

1. Inspect the actual runner checkout and state. Do not assume Downloads has the latest state.
2. Run `deployment/run_local.py --migrate <authoritative-seen_jobs.json>` into staging data first.
3. Run `deployment/run_local.py --diagnose` and `deployment/run_local.py --dry-run`.
   Dry-run contacts sources and may use configured AI, but sends no notifications and uses copied state.
4. Validate a backup restore in a separate directory. Inspect uncertain legacy deliveries.
5. Register `deployment/install_local_task.ps1 -Pythonw <dedicated-pythonw.exe>` disabled.
   S4U registration can require local privileges; registration is not evidence of network access.
   `-AllowLoginOnly` is an explicit fallback only: it avoids elevation but runs after user login.
6. Confirm execution with the user logged out and that sources can be reached. If S4U cannot
   access network resources in this environment, use an explicitly configured task account or
   document login-only operation. Never claim startup-independent execution without that test.
7. Pause the old GitHub schedule, wait for active work to finish, take final backup, migrate
   authoritative state, then enable the new task. Never enable both producers.
8. Remove state commits and production collection from GitHub only after the replacement works.

## Acceptance / rollback

Seven days of observation including weekday/weekend remain required. Check no overlapping
cycles, no controlled duplicate deliveries, restored backups and overdue starts within ten
minutes while Windows is available. Offline Windows cannot report its own outage.

Before rollback disable the local task, wait for its process, export/reconcile DELIVERED and
UNKNOWN outbox/channel records into the previous state's seen set, validate that snapshot,
then enable the old scheduler. Never simply restore an old JSON: that can resend alerts.

## Remaining rollout gates

- Production checkout/state authority and private credentials verified.
- S4U task installed and execution/network access validated, including logged-out operation.
- Operational source-failure alerts tested offline; critical-persistence/channel receipt requires live validation.
- Real controlled cycle and channel receipt confirmed, GitHub producer retired.
- Seven-day observation completed. No current claim of full production readiness.

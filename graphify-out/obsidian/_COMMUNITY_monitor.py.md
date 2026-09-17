---
type: community
cohesion: 0.17
members: 18
---

# monitor.py

**Cohesion:** 0.17 - loosely connected
**Members:** 18 nodes

## Members
- [[dot-__init__()_6]] - code - notify/telegram_notifier.py
- [[dot-send_heartbeat()]] - code - notify/telegram_notifier.py
- [[dot-send_job_alert()]] - code - notify/telegram_notifier.py
- [[dot-test_telegram_sends_formatted_alert_with_score_and_buttons()]] - code - tests/test_monitor.py
- [[Job_12]] - code
- [[Retorna sessão requests com retentativas automáticas e backoff exponencial.]] - rationale - monitor.py
- [[Session_6]] - code
- [[Session_7]] - code
- [[TelegramNotifier]] - code - notify/telegram_notifier.py
- [[TestTelegramNotifier]] - code - tests/test_monitor.py
- [[Verifica se deve enviar o heartbeat diário ao Telegram.]] - rationale - monitor.py
- [[check_heartbeat()]] - code - monitor.py
- [[get_http_session()]] - code - monitor.py
- [[load_config()]] - code - monitor.py
- [[main()]] - code - monitor.py
- [[monitor.py]] - code - monitor.py
- [[run_check()]] - code - monitor.py
- [[telegram_notifier.py]] - code - notify/telegram_notifier.py

## Live Query (requires Dataview plugin)

```dataview
TABLE source_file, type FROM #community/monitorpy
SORT file.name ASC
```

## Connections to other communities
- 19 edges to [[_COMMUNITY_Job]]
- 12 edges to [[_COMMUNITY_LinkedInCollector]]
- 6 edges to [[_COMMUNITY_StateStore]]
- 2 edges to [[_COMMUNITY_GithubIssuesCollector]]
- 2 edges to [[_COMMUNITY_rss_collector.py]]
- 2 edges to [[_COMMUNITY_RssCollector]]
- 2 edges to [[_COMMUNITY_TramposCollector]]
- 2 edges to [[_COMMUNITY_is_pcd_exclusive]]
- 2 edges to [[_COMMUNITY_evaluate_job]]

## Top bridge nodes
- [[monitor.py]] - degree 29, connects to 9 communities
- [[run_check()]] - degree 15, connects to 8 communities
- [[TelegramNotifier]] - degree 15, connects to 3 communities
- [[TestTelegramNotifier]] - degree 8, connects to 3 communities
- [[check_heartbeat()]] - degree 5, connects to 1 community
"""Windowless Task Scheduler entry point; logs stay outside the checkout."""
import logging
from logging.handlers import RotatingFileHandler
import os
from pathlib import Path
import re
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def main():
    if '--dry-run' in sys.argv:
        os.environ['JOB_FINDER_SIMULATION'] = '1'
    from core.local_runtime import data_directory
    directory = data_directory()
    directory.mkdir(parents=True, exist_ok=True)
    handler = RotatingFileHandler(directory / 'runtime.log', maxBytes=2_000_000,
                                  backupCount=7, encoding='utf-8')
    handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger = logging.getLogger('local-runner')
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)
    logger.propagate = False
    from dotenv import load_dotenv
    load_dotenv(directory / 'secrets.env', override=True)
    secrets = [value for key, value in os.environ.items()
               if any(part in key for part in ('TOKEN', 'KEY', 'PASSWORD')) and len(value) > 6]

    class LogStream:
        def write(self, text):
            for secret in secrets:
                text = text.replace(secret, '[REDACTED]')
            text = re.sub(r'bot\d+:[\w-]+', 'bot[REDACTED]', text)
            for line in text.splitlines():
                if line.strip():
                    logger.info(line)
        def flush(self):
            handler.flush()

    sys.stdout = sys.stderr = LogStream()
    os.chdir(ROOT)
    os.environ['JOB_FINDER_LOCAL_RUNTIME'] = '1'
    try:
        import monitor
        from core.local_runtime import main as run
        arguments = sys.argv[1:] or ['--due']
        if '--loop' in arguments:
            arguments = [arg for arg in arguments if arg != '--loop'] or ['--due']
            timeout_seconds = int(os.environ.get('JOB_FINDER_CYCLE_TIMEOUT_SECONDS', '240'))
            logger.info('Local runner started; checking every 5 minutes; cycle timeout=%ss', timeout_seconds)
            while True:
                started = time.monotonic()
                try:
                    # Isolate each collection so a hung network call cannot freeze
                    # the watchdog permanently. The child owns the cycle lock.
                    command = [sys.executable, str(Path(__file__).resolve()), *arguments]
                    creationflags = getattr(subprocess, 'CREATE_NO_WINDOW', 0)
                    completed = subprocess.run(
                        command,
                        cwd=ROOT,
                        env=os.environ.copy(),
                        timeout=timeout_seconds,
                        creationflags=creationflags,
                    )
                    logger.info('Cycle process finished: exit=%s duration=%.1fs',
                                completed.returncode, time.monotonic() - started)
                    if completed.returncode:
                        logger.error('Cycle process failed: exit=%s', completed.returncode)
                except subprocess.TimeoutExpired:
                    logger.error('Cycle process timed out after %ss; next check will recover', timeout_seconds)
                except Exception as exc:
                    # The watchdog must stay alive after one bad cycle; the next
                    # five-minute check can recover transient source/runtime errors.
                    logger.error('Cycle failed: %s; retrying on next check', type(exc).__name__)
                time.sleep(300)
        else:
            run(monitor, arguments)
    except Exception as exc:
        logger.error('Cycle failed: %s (use local diagnostic; secrets omitted)', type(exc).__name__)
        import sqlite3
        if isinstance(exc, (sqlite3.DatabaseError, OSError)):
            import requests
            from core.operational_alerts import send_operational
            with requests.Session() as http:
                send_operational(http, 'Job Finder: critical local storage/runtime failure. Collection stopped; check local diagnostics.')
        return 1
    finally:
        handler.flush()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())

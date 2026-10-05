"""Long-lived manual analysis worker, independent from the scheduled radar."""
import time
import traceback
import os
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from workhunter_worker import run
os.environ.setdefault('JOB_FINDER_RUNTIME_LOG', str(Path.home() / '.job-finder' / 'manual-worker.log'))

while True:
    try:
        run()
    except Exception as exc:
        print(f'manual worker failed: {type(exc).__name__}: {exc}', flush=True)
        traceback.print_exc()
    time.sleep(10)

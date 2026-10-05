"""Run one isolated manual analysis cycle."""
import os
import sys
from deployment.run_local import main

def run():
    os.environ['JOB_FINDER_MANUAL_ONLY'] = '1'
    sys.argv = ['run_local.py', '--once']
    return main()

if __name__ == '__main__':
    raise SystemExit(run())

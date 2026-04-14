"""
Background update checker — periodically git-fetches and checks
whether the current branch is behind its upstream.

Usage:
    import update_checker
    update_checker.start()          # kicks off background thread
    if update_checker.available:    # True when upstream has new commits
        ...
"""

import subprocess
import threading
import time

available = False


def _check():
    global available
    try:
        subprocess.run(['git', 'fetch', '--quiet'],
                       capture_output=True, timeout=30)
        result = subprocess.run(
            ['git', 'rev-list', '--count', 'HEAD..@{u}'],
            capture_output=True, text=True, timeout=10)
        available = int(result.stdout.strip()) > 0
    except Exception:
        pass  # no network, no upstream, etc.


def start(interval=1800):
    """Start periodic background checks (default every 30 min)."""
    def _loop():
        time.sleep(60)  # let system settle after boot
        while True:
            _check()
            time.sleep(interval)
    threading.Thread(target=_loop, daemon=True).start()

"""
Background update checker — periodically git-fetches and checks whether a newer
version is available, lighting the "update available" indicator in the menu.

Mirrors the two update modes of start.sh / visuals/refresh.py:
  - Dev cabinet (.dev flag present): follow the tip of `main`. Update available
    when origin/main is ahead of HEAD.
  - Distribution cabinet (no .dev): run the highest release tag. These cabinets
    run in DETACHED HEAD at a tag, so the old `HEAD..@{u}` check always threw
    (no upstream) and the indicator never lit. Instead, compare the currently
    checked-out commit against the highest tag now available from origin.

Usage:
    import update_checker
    update_checker.start()          # kicks off background thread
    if update_checker.available:    # True when a newer version exists
        ...
"""

import os
import re
import subprocess
import threading
import time

available = False

_REPO_DIR = os.path.dirname(os.path.abspath(__file__))
_DEV = os.path.exists(os.path.join(_REPO_DIR, ".dev"))


def _git(*args, timeout=15):
    """Run a git command in the repo dir. Returns (ok, stdout)."""
    try:
        result = subprocess.run(
            ["git", "-c", "safe.directory=*"] + list(args),
            cwd=_REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception:
        return False, ""


def _latest_tag():
    """Highest vMAJOR.MINOR release tag known locally (matches start.sh)."""
    ok, out = _git("tag", "-l", "v*")
    if not ok or not out:
        return ""
    return max(out.split(), key=lambda t: [int(n) for n in re.findall(r"\d+", t)])


def _rev(ref):
    ok, out = _git("rev-parse", ref)
    return out if ok else None


def _check():
    global available
    try:
        if _DEV:
            # Dev: is origin/main ahead of HEAD?
            _git("fetch", "origin", "main", timeout=30)
            head = _rev("HEAD")
            upstream = _rev("origin/main")
            available = bool(head and upstream and head != upstream)
        else:
            # Distribution: is a higher tag available than the one we're on?
            # --prune-tags so a tag deleted upstream (a rollback) also un-lights.
            _git("fetch", "--tags", "--force", "--prune", "--prune-tags",
                 "origin", timeout=30)
            tag = _latest_tag()
            if not tag:
                available = False
                return
            head = _rev("HEAD")
            target = _rev(tag)
            available = bool(head and target and head != target)
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

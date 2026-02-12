"""
Refresh - Update & Rollback utility
====================================
Page 1: Pull latest code from remote and restart.
Page 2: Revert to the version saved before the last update.

Controls:
  Left/Right - Switch page
  Up/Down    - Select YES/NO
  Button     - Confirm selection
"""

import os
import sys
import subprocess
import threading
from . import Visual, Display, Colors, GRID_SIZE


REPO_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROLLBACK_FILE = os.path.join(REPO_DIR, ".rollback_ref")
DEV_FLAG = os.path.join(REPO_DIR, ".dev")
BRANCH = "main" if os.path.exists(DEV_FLAG) else "stable"


def _git(*args, timeout=15):
    """Run a git command in the repo directory."""
    try:
        result = subprocess.run(
            ["git", "-c", "safe.directory=*"] + list(args),
            cwd=REPO_DIR,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        return result.returncode == 0, result.stdout.strip()
    except Exception:
        return False, ""


def _short_hash(ref="HEAD"):
    ok, out = _git("rev-parse", "--short", ref)
    return out if ok else "?"


def _commit_date(ref="HEAD"):
    ok, out = _git("log", "-1", "--format=%Y-%m-%d", ref)
    return out if ok else "?"


class Refresh(Visual):
    name = "UPDATE"
    description = "Restart arcade"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.page = 0  # 0 = update, 1 = rollback
        self.selection = 1  # 0 = YES, 1 = NO (default to NO)
        self.confirmed = False

        # --- Update page state ---
        self.pull_started = False
        self.pull_done = False
        self.pull_msg = ""

        # --- Rollback page state ---
        self.rolling_back = False
        self.rollback_done = False
        self.rollback_msg = ""

        # Shared
        self.restart_timer = 0.0

        # Current version info
        self.version_hash = _short_hash("HEAD")
        self.current_date = _commit_date("HEAD")

        # Fetch remote in background to avoid blocking the UI
        self.remote_hash = "..."
        self.is_latest = False
        self._fetch_done = False
        self._fetch_thread = threading.Thread(target=self._fetch_remote,
                                              daemon=True)
        self._fetch_thread.start()

        # Rollback info
        self.rollback_hash = ""
        self.rollback_date = ""
        self.has_rollback = False
        if os.path.exists(ROLLBACK_FILE):
            try:
                with open(ROLLBACK_FILE, "r") as f:
                    ref = f.read().strip()
                if ref:
                    ok, _ = _git("cat-file", "-t", ref)
                    if ok:
                        self.rollback_hash = _short_hash(ref)
                        self.rollback_date = _commit_date(ref)
                        self.has_rollback = True
            except Exception:
                pass

    def _fetch_remote(self):
        """Background thread: fetch remote and resolve remote hash."""
        _git("fetch", "origin", BRANCH, timeout=10)
        self.remote_hash = _short_hash("origin/" + BRANCH)
        self.is_latest = (self.version_hash == self.remote_hash)
        self._fetch_done = True

    def handle_input(self, input_state) -> bool:
        if self.confirmed:
            return True

        # Page switching with left/right
        if input_state.left_pressed or input_state.right_pressed:
            self.page = 1 - self.page
            self.selection = 1  # Reset to NO on page switch
            return True

        if input_state.up_pressed or input_state.down_pressed:
            # On rollback page with no rollback available, ignore
            if self.page == 1 and not self.has_rollback:
                return False
            self.selection = 1 - self.selection
            return True

        if input_state.action_l or input_state.action_r:
            if self.page == 1 and not self.has_rollback:
                self.wants_exit = True
                return True
            if self.selection == 0:
                self.confirmed = True
            else:
                self.wants_exit = True
            return True

        return False

    def update(self, dt: float):
        self.time += dt

        if not self.confirmed:
            return

        if self.page == 0:
            self._update_pull(dt)
        else:
            self._update_rollback(dt)

    def _update_pull(self, dt):
        if not self.pull_started:
            self.pull_started = True

            # Save current HEAD as rollback point before pulling
            ok, current_ref = _git("rev-parse", "HEAD")
            if ok and current_ref:
                try:
                    with open(ROLLBACK_FILE, "w") as f:
                        f.write(current_ref)
                except Exception:
                    pass

            ok, output = _git("pull", "origin", BRANCH)
            if ok:
                if "Already up to date" in output:
                    self.pull_msg = "UP TO DATE"
                else:
                    self.pull_msg = "PULLED"
            else:
                self.pull_msg = "PULL FAILED"

            self.pull_done = True
            self.restart_timer = 0.0

        if self.pull_done:
            self.restart_timer += dt
            if self.restart_timer >= 1.5:
                os.execv(sys.executable, [sys.executable] + sys.argv)

    def _update_rollback(self, dt):
        if not self.rolling_back:
            self.rolling_back = True
            try:
                with open(ROLLBACK_FILE, "r") as f:
                    ref = f.read().strip()
                ok, _ = _git("checkout", ref, "--", ".")
                if ok:
                    self.rollback_msg = "REVERTED"
                    try:
                        os.remove(ROLLBACK_FILE)
                    except Exception:
                        pass
                else:
                    self.rollback_msg = "FAILED"
            except Exception:
                self.rollback_msg = "FAILED"
            self.rollback_done = True
            self.restart_timer = 0.0

        if self.rollback_done:
            self.restart_timer += dt
            if self.restart_timer >= 1.5:
                os.execv(sys.executable, [sys.executable] + sys.argv)

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.page == 0:
            self._draw_update()
        else:
            self._draw_rollback()

    def _draw_update(self):
        if self.confirmed:
            if not self.pull_done:
                self.display.draw_text_small(2, 24, "PULLING...", Colors.CYAN)
                dots = int(self.time * 3) % 4
                self.display.draw_text_small(2, 38, "." * dots, Colors.GRAY)
            else:
                msg_color = Colors.GREEN if self.pull_msg == "PULLED" else Colors.YELLOW
                self.display.draw_text_small(2, 14, self.pull_msg, msg_color)
                self.display.draw_text_small(2, 28, "RESTARTING", Colors.CYAN)
                dots = int(self.restart_timer * 3) % 4
                self.display.draw_text_small(2, 42, "." * dots, Colors.GRAY)
            return

        # Title + page tabs
        self._draw_tabs()

        # Version info
        branch_color = Colors.YELLOW if BRANCH == "main" else Colors.GREEN
        self.display.draw_text_small(2, 12, BRANCH, branch_color)
        self.display.draw_text_small(2, 20, "NOW:" + self.version_hash, Colors.GRAY)
        if not self._fetch_done:
            self.display.draw_text_small(2, 28, "CHECKING...", Colors.GRAY)
        elif self.is_latest:
            self.display.draw_text_small(2, 28, "=LATEST", Colors.GREEN)
        else:
            self.display.draw_text_small(2, 28, "NEW:" + self.remote_hash, Colors.WHITE)

        # Description
        self.display.draw_text_small(2, 38, "RESTART?", Colors.WHITE)

        # YES / NO options
        self._draw_yes_no(48)

    def _draw_rollback(self):
        if self.confirmed:
            if not self.rollback_done:
                self.display.draw_text_small(2, 24, "REVERTING...", Colors.CYAN)
                dots = int(self.time * 3) % 4
                self.display.draw_text_small(2, 38, "." * dots, Colors.GRAY)
            else:
                msg_color = Colors.GREEN if self.rollback_msg == "REVERTED" else Colors.RED
                self.display.draw_text_small(2, 14, self.rollback_msg, msg_color)
                self.display.draw_text_small(2, 28, "RESTARTING", Colors.CYAN)
                dots = int(self.restart_timer * 3) % 4
                self.display.draw_text_small(2, 42, "." * dots, Colors.GRAY)
            return

        # Title + page tabs
        self._draw_tabs()

        if not self.has_rollback:
            self.display.draw_text_small(2, 18, "NO ROLLBACK", Colors.YELLOW)
            self.display.draw_text_small(2, 28, "AVAILABLE", Colors.YELLOW)
            self.display.draw_text_small(2, 42, "NOW:" + self.version_hash, Colors.GRAY)
            self.display.draw_text_small(2, 50, self.current_date, Colors.GRAY)
            return

        # Show current vs rollback
        self.display.draw_text_small(2, 12, "NOW:" + self.version_hash, Colors.WHITE)
        self.display.draw_text_small(2, 20, "OLD:" + self.rollback_hash, Colors.YELLOW)

        # Revert prompt
        self.display.draw_text_small(2, 30, "REVERT?", Colors.WHITE)

        self._draw_yes_no(40)

    def _draw_tabs(self):
        """Draw page tab indicators at top."""
        upd_color = Colors.CYAN if self.page == 0 else Colors.GRAY
        rb_color = Colors.CYAN if self.page == 1 else Colors.GRAY
        self.display.draw_text_small(2, 2, "UPD", upd_color)
        self.display.draw_text_small(20, 2, "|", Colors.GRAY)
        self.display.draw_text_small(26, 2, "RLBK", rb_color)
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

    def _draw_yes_no(self, y):
        """Draw YES/NO selection at given y."""
        yes_color = Colors.YELLOW if self.selection == 0 else Colors.GRAY
        no_color = Colors.YELLOW if self.selection == 1 else Colors.GRAY
        if self.selection == 0:
            self.display.draw_text_small(2, y, ">", Colors.YELLOW)
        else:
            self.display.draw_text_small(2, y + 8, ">", Colors.YELLOW)
        self.display.draw_text_small(9, y, "YES", yes_color)
        self.display.draw_text_small(9, y + 8, "NO", no_color)

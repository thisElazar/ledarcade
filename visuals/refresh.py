"""
Refresh - Restart the arcade with latest code
===============================================
Saves the current commit as a rollback point, pulls from the
stable branch, then restarts the arcade process regardless of
pull outcome.

Controls:
  Up/Down    - Select YES/NO
  Button     - Confirm selection
"""

import os
import sys
import subprocess
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



class Refresh(Visual):
    name = "UPDATE"
    description = "Restart arcade"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.selection = 1  # 0 = YES, 1 = NO (default to NO)
        self.confirmed = False
        self.pull_started = False
        self.pull_done = False
        self.pull_msg = ""
        self.restart_timer = 0.0

        # Current version info
        self.version_hash = _short_hash("HEAD")

        # Fetch remote to check for updates
        self.remote_hash = "?"
        self.is_latest = False
        _git("fetch", "origin", BRANCH, timeout=10)
        self.remote_hash = _short_hash("origin/" + BRANCH)
        self.is_latest = (self.version_hash == self.remote_hash)

    def handle_input(self, input_state) -> bool:
        if self.confirmed:
            return True

        if input_state.up_pressed or input_state.down_pressed:
            self.selection = 1 - self.selection
            return True

        if input_state.left_pressed or input_state.right_pressed:
            self.wants_exit = True
            return True

        if input_state.action_l or input_state.action_r:
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

        # Attempt git pull once (best-effort)
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

            # Pull from stable branch explicitly
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

        # Always restart after showing status briefly
        if self.pull_done:
            self.restart_timer += dt
            if self.restart_timer >= 1.5:
                os.execv(sys.executable, [sys.executable] + sys.argv)

    def draw(self):
        self.display.clear(Colors.BLACK)

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

        # Title + version
        self.display.draw_text_small(2, 2, "UPDATE", Colors.CYAN)
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

        # Version info
        branch_color = Colors.YELLOW if BRANCH == "main" else Colors.GREEN
        self.display.draw_text_small(2, 12, BRANCH, branch_color)
        self.display.draw_text_small(2, 20, "NOW:" + self.version_hash, Colors.GRAY)
        if self.is_latest:
            self.display.draw_text_small(2, 28, "=LATEST", Colors.GREEN)
        else:
            self.display.draw_text_small(2, 28, "NEW:" + self.remote_hash, Colors.WHITE)

        # Description
        self.display.draw_text_small(2, 38, "RESTART?", Colors.WHITE)

        # YES / NO options
        yes_color = Colors.YELLOW if self.selection == 0 else Colors.GRAY
        no_color = Colors.YELLOW if self.selection == 1 else Colors.GRAY

        if self.selection == 0:
            self.display.draw_text_small(2, 48, ">", Colors.YELLOW)
        else:
            self.display.draw_text_small(2, 56, ">", Colors.YELLOW)

        self.display.draw_text_small(9, 48, "YES", yes_color)
        self.display.draw_text_small(9, 56, "NO", no_color)

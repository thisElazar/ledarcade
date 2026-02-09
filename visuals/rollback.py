"""
Rollback - Revert to previous version
======================================
Reverts the arcade to the version saved before the last update.
The rollback point is stored in .rollback_ref by the update utility.

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


class Rollback(Visual):
    name = "ROLLBACK"
    description = "Revert last update"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.selection = 1  # 0 = YES, 1 = NO (default to NO)
        self.confirmed = False
        self.rolling_back = False
        self.done = False
        self.result_msg = ""
        self.restart_timer = 0.0

        # Read rollback info
        self.current_hash = _short_hash("HEAD")
        self.current_date = _commit_date("HEAD")
        self.rollback_hash = ""
        self.rollback_date = ""
        self.has_rollback = False

        if os.path.exists(ROLLBACK_FILE):
            try:
                with open(ROLLBACK_FILE, "r") as f:
                    ref = f.read().strip()
                if ref:
                    # Verify the ref exists
                    ok, _ = _git("cat-file", "-t", ref)
                    if ok:
                        self.rollback_hash = _short_hash(ref)
                        self.rollback_date = _commit_date(ref)
                        self.has_rollback = True
            except Exception:
                pass

    def handle_input(self, input_state) -> bool:
        if self.confirmed:
            return True

        if not self.has_rollback:
            if input_state.action_l or input_state.action_r or \
               input_state.left_pressed or input_state.right_pressed:
                self.wants_exit = True
                return True
            return False

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

        if not self.rolling_back:
            self.rolling_back = True
            try:
                with open(ROLLBACK_FILE, "r") as f:
                    ref = f.read().strip()
                ok, _ = _git("checkout", ref, "--", ".")
                if ok:
                    self.result_msg = "REVERTED"
                    # Remove rollback file so they can't double-revert
                    try:
                        os.remove(ROLLBACK_FILE)
                    except Exception:
                        pass
                else:
                    self.result_msg = "FAILED"
            except Exception:
                self.result_msg = "FAILED"
            self.done = True
            self.restart_timer = 0.0

        if self.done:
            self.restart_timer += dt
            if self.restart_timer >= 1.5:
                os.execv(sys.executable, [sys.executable] + sys.argv)

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.confirmed:
            if not self.done:
                self.display.draw_text_small(2, 24, "REVERTING...", Colors.CYAN)
                dots = int(self.time * 3) % 4
                self.display.draw_text_small(2, 38, "." * dots, Colors.GRAY)
            else:
                msg_color = Colors.GREEN if self.result_msg == "REVERTED" else Colors.RED
                self.display.draw_text_small(2, 14, self.result_msg, msg_color)
                self.display.draw_text_small(2, 28, "RESTARTING", Colors.CYAN)
                dots = int(self.restart_timer * 3) % 4
                self.display.draw_text_small(2, 42, "." * dots, Colors.GRAY)
            return

        # Title
        self.display.draw_text_small(2, 2, "ROLLBACK", Colors.CYAN)
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

        if not self.has_rollback:
            self.display.draw_text_small(2, 18, "NO ROLLBACK", Colors.YELLOW)
            self.display.draw_text_small(2, 28, "AVAILABLE", Colors.YELLOW)
            self.display.draw_text_small(2, 42, "NOW:" + self.current_hash, Colors.GRAY)
            self.display.draw_text_small(2, 50, self.current_date, Colors.GRAY)
            return

        # Show current vs rollback
        self.display.draw_text_small(2, 12, "NOW:" + self.current_hash, Colors.WHITE)
        self.display.draw_text_small(2, 20, "OLD:" + self.rollback_hash, Colors.YELLOW)

        # Revert prompt
        self.display.draw_text_small(2, 30, "REVERT?", Colors.WHITE)

        yes_color = Colors.YELLOW if self.selection == 0 else Colors.GRAY
        no_color = Colors.YELLOW if self.selection == 1 else Colors.GRAY
        if self.selection == 0:
            self.display.draw_text_small(2, 40, ">", Colors.YELLOW)
        else:
            self.display.draw_text_small(2, 48, ">", Colors.YELLOW)
        self.display.draw_text_small(9, 40, "YES", yes_color)
        self.display.draw_text_small(9, 48, "NO", no_color)

        self.display.draw_text_small(2, 58, "BTN:CONFIRM", Colors.GRAY)

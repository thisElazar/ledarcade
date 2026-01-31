"""
Refresh - Restart the arcade with latest code
===============================================
Attempts a git pull, then restarts the arcade process
regardless of pull outcome. The restart is the point —
new code may already be on disk from a prior deploy.

Controls:
  Up/Down    - Select YES/NO
  Button     - Confirm selection
"""

import os
import sys
import subprocess
from . import Visual, Display, Colors, GRID_SIZE


class Refresh(Visual):
    name = "REFRESH"
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
            repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            try:
                result = subprocess.run(
                    ["git", "pull"],
                    cwd=repo_dir,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                if result.returncode == 0:
                    output = result.stdout.strip()
                    if "Already up to date" in output:
                        self.pull_msg = "UP TO DATE"
                    else:
                        self.pull_msg = "PULLED"
                else:
                    self.pull_msg = "PULL FAILED"
            except Exception:
                self.pull_msg = "PULL SKIPPED"
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

        # Title
        self.display.draw_text_small(2, 2, "REFRESH", Colors.CYAN)

        # Separator
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

        # Description
        self.display.draw_text_small(2, 14, "PULL + ", Colors.WHITE)
        self.display.draw_text_small(2, 22, "RESTART?", Colors.WHITE)

        # YES / NO options
        yes_color = Colors.YELLOW if self.selection == 0 else Colors.GRAY
        no_color = Colors.YELLOW if self.selection == 1 else Colors.GRAY

        if self.selection == 0:
            self.display.draw_text_small(2, 34, ">", Colors.YELLOW)
        else:
            self.display.draw_text_small(2, 44, ">", Colors.YELLOW)

        self.display.draw_text_small(9, 34, "YES", yes_color)
        self.display.draw_text_small(9, 44, "NO", no_color)

        # Hint
        self.display.draw_text_small(2, 54, "BTN:CONFIRM", Colors.GRAY)

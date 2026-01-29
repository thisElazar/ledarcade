"""
Shutdown - System power off with confirmation
===============================================
Safely shuts down the Raspberry Pi.

Controls:
  Up/Down    - Select YES/NO
  Button     - Confirm selection
"""

import os
from . import Visual, Display, Colors, GRID_SIZE


class Shutdown(Visual):
    name = "SHUTDOWN"
    description = "Power off"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.selection = 1  # 0 = YES, 1 = NO (default to NO)
        self.confirmed = False
        self.shutdown_timer = 0.0

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
                # YES — begin shutdown
                self.confirmed = True
                self.shutdown_timer = 0.0
            else:
                # NO — go back to menu
                self.wants_exit = True
            return True

        return False

    def update(self, dt: float):
        self.time += dt

        if self.confirmed:
            self.shutdown_timer += dt
            # Show message briefly, then shut down
            if self.shutdown_timer >= 2.0:
                os.system("sudo shutdown -h now")

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.confirmed:
            # Shutting down message
            self.display.draw_text_small(2, 20, "SHUTTING", Colors.RED)
            self.display.draw_text_small(2, 28, "DOWN...", Colors.RED)

            # Countdown dots
            dots = int(self.shutdown_timer * 3) % 4
            self.display.draw_text_small(2, 42, "." * dots, Colors.GRAY)
            return

        # Title
        self.display.draw_text_small(2, 2, "SHUTDOWN", Colors.RED)

        # Separator
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

        # Warning
        self.display.draw_text_small(2, 14, "POWER OFF?", Colors.WHITE)

        # YES / NO options
        yes_color = Colors.YELLOW if self.selection == 0 else Colors.GRAY
        no_color = Colors.YELLOW if self.selection == 1 else Colors.GRAY

        # Selection indicator
        if self.selection == 0:
            self.display.draw_text_small(2, 30, ">", Colors.YELLOW)
        else:
            self.display.draw_text_small(2, 40, ">", Colors.YELLOW)

        self.display.draw_text_small(9, 30, "YES", yes_color)
        self.display.draw_text_small(9, 40, "NO", no_color)

        # Hint
        self.display.draw_text_small(2, 54, "BTN:CONFIRM", Colors.GRAY)

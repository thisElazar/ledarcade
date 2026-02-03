"""
Input Test - Live input diagnostic
====================================
Shows real-time joystick and button state for hardware debugging.

Controls:
  All inputs shown live on screen
  Hold both buttons 2s to exit
"""

from . import Visual, Display, Colors, GRID_SIZE


class InputTest(Visual):
    name = "INPUT TEST"
    description = "Test inputs"
    category = "utility"
    custom_exit = True  # bypass runner's default visual exit hold

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.exit_hold = 0.0

    def handle_input(self, input_state) -> bool:
        # Store input state for drawing — don't exit on button press
        self._input = input_state
        # Hold both buttons 2s to exit
        if input_state.action_l_held and input_state.action_r_held:
            self.exit_hold += 0  # accumulated in update via dt
        else:
            self.exit_hold = 0.0
        return True

    def update(self, dt: float):
        self.time += dt
        inp = getattr(self, '_input', None)
        if inp and inp.action_l_held and inp.action_r_held:
            self.exit_hold += dt
            if self.exit_hold >= 2.0:
                self.wants_exit = True
        else:
            self.exit_hold = 0.0

    def _draw_dpad(self, cx, cy):
        """Draw joystick state as a d-pad with lit directions."""
        off = (50, 50, 50)
        on = Colors.RED

        # Center
        self.display.draw_rect(cx, cy, 4, 4, (80, 80, 80))

        inp = getattr(self, '_input', None)

        # Up
        color = on if (inp and inp.up) else off
        self.display.draw_rect(cx, cy - 5, 4, 4, color)

        # Down
        color = on if (inp and inp.down) else off
        self.display.draw_rect(cx, cy + 5, 4, 4, color)

        # Left
        color = on if (inp and inp.left) else off
        self.display.draw_rect(cx - 5, cy, 4, 4, color)

        # Right
        color = on if (inp and inp.right) else off
        self.display.draw_rect(cx + 5, cy, 4, 4, color)

    def _draw_button(self, cx, cy, radius, pressed, label):
        """Draw a button circle that lights up when pressed."""
        off = (50, 50, 50)
        on = Colors.WHITE

        color = on if pressed else off
        # Draw filled circle approximation
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self.display.set_pixel(cx + dx, cy + dy, color)

        # Label below
        label_x = cx - (len(label) * 5 - 1) // 2
        self.display.draw_text_small(label_x, cy + radius + 2, label, Colors.GRAY)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Title
        self.display.draw_text_small(2, 2, "INPUT TEST", Colors.CYAN)

        # Separator
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

        inp = getattr(self, '_input', None)

        # Draw joystick d-pad on left side
        self._draw_dpad(13, 25)

        # Direction labels
        self.display.draw_text_small(2, 38, "JOYSTICK", Colors.GRAY)

        # Draw buttons on right side
        btn_l = inp.action_l_held if inp else False
        btn_r = inp.action_r_held if inp else False
        self._draw_button(40, 25, 4, btn_l, "L")
        self._draw_button(54, 25, 4, btn_r, "R")

        # Active indicator — show text for what's pressed
        y = 48
        if inp:
            parts = []
            if inp.up:
                parts.append("UP")
            if inp.down:
                parts.append("DN")
            if inp.left:
                parts.append("LF")
            if inp.right:
                parts.append("RT")
            if inp.action_l_held:
                parts.append("BL")
            if inp.action_r_held:
                parts.append("BR")

            if parts:
                text = " ".join(parts)
                self.display.draw_text_small(2, y, text, Colors.YELLOW)
            else:
                self.display.draw_text_small(2, y, "NO INPUT", (60, 60, 60))
        else:
            self.display.draw_text_small(2, y, "NO INPUT", (60, 60, 60))

        # Exit hold progress bar
        if self.exit_hold > 0:
            bar_w = int((self.exit_hold / 2.0) * 60)
            bar_w = min(60, bar_w)
            if bar_w > 0:
                self.display.draw_rect(2, 56, bar_w, 2, Colors.RED)

        # Blinking dot to show the screen is live
        if int(self.time * 3) % 2 == 0:
            self.display.set_pixel(61, 2, Colors.GREEN)

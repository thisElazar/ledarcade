"""
Controls - Live input reference
====================================
Shows the arcade panel control layout with live input feedback.
Press buttons and directions to see them light up.

Controls:
  All inputs shown live on screen
  Hold both buttons 2s to exit
"""

from . import Visual, Display, Colors, GRID_SIZE


class Controls(Visual):
    name = "CONTROLS"
    description = "Button guide"
    category = "utility"
    custom_exit = True

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.exit_hold = 0.0

    def handle_input(self, input_state) -> bool:
        self._input = input_state
        if input_state.action_l_held and input_state.action_r_held:
            pass  # accumulated in update via dt
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

    def _draw_button(self, cx, cy, radius, pressed):
        """Draw a button circle that lights up when pressed."""
        off = (50, 50, 50)
        on = Colors.WHITE

        color = on if pressed else off
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self.display.set_pixel(cx + dx, cy + dy, color)

    def draw(self):
        self.display.clear(Colors.BLACK)

        inp = getattr(self, '_input', None)

        # Title
        self.display.draw_text_small(2, 2, "CONTROLS", Colors.CYAN)

        # Blinking dot to show the screen is live
        if int(self.time * 3) % 2 == 0:
            self.display.set_pixel(61, 2, Colors.GREEN)

        # Separator
        self.display.draw_line(2, 9, 61, 9, Colors.GRAY)

        # Joystick d-pad on left side
        self._draw_dpad(13, 22)
        self.display.draw_text_small(24, 19, "MOVE", Colors.WHITE)

        # Buttons on right side
        btn_l = inp.action_l_held if inp else False
        btn_r = inp.action_r_held if inp else False
        self._draw_button(13, 42, 4, btn_l)
        self._draw_button(27, 42, 4, btn_r)
        self.display.draw_text_small(34, 39, "ACTION", Colors.WHITE)

        # Hold both to exit
        self.display.draw_text_small(2, 55, "HOLD BOTH:BACK", Colors.YELLOW)

        # Exit hold progress bar
        if self.exit_hold > 0:
            bar_w = int((self.exit_hold / 2.0) * 60)
            bar_w = min(60, bar_w)
            if bar_w > 0:
                self.display.draw_rect(2, 62, bar_w, 2, Colors.RED)

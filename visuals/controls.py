"""
Controls - Input reference display
====================================
Shows the arcade panel control layout and button functions.

Controls:
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

    def _draw_joystick(self, cx, cy):
        """Draw a small joystick icon with directional arrows."""
        # Center knob
        self.display.set_pixel(cx, cy, Colors.RED)
        self.display.set_pixel(cx + 1, cy, Colors.RED)
        self.display.set_pixel(cx, cy + 1, Colors.RED)
        self.display.set_pixel(cx + 1, cy + 1, Colors.RED)

        # Up arrow
        self.display.set_pixel(cx, cy - 2, (180, 40, 40))
        self.display.set_pixel(cx + 1, cy - 2, (180, 40, 40))
        self.display.set_pixel(cx, cy - 1, (180, 40, 40))
        self.display.set_pixel(cx + 1, cy - 1, (180, 40, 40))

        # Down arrow
        self.display.set_pixel(cx, cy + 3, (180, 40, 40))
        self.display.set_pixel(cx + 1, cy + 3, (180, 40, 40))
        self.display.set_pixel(cx, cy + 2, (180, 40, 40))
        self.display.set_pixel(cx + 1, cy + 2, (180, 40, 40))

        # Left arrow
        self.display.set_pixel(cx - 2, cy, (180, 40, 40))
        self.display.set_pixel(cx - 2, cy + 1, (180, 40, 40))
        self.display.set_pixel(cx - 1, cy, (180, 40, 40))
        self.display.set_pixel(cx - 1, cy + 1, (180, 40, 40))

        # Right arrow
        self.display.set_pixel(cx + 3, cy, (180, 40, 40))
        self.display.set_pixel(cx + 3, cy + 1, (180, 40, 40))
        self.display.set_pixel(cx + 2, cy, (180, 40, 40))
        self.display.set_pixel(cx + 2, cy + 1, (180, 40, 40))

    def _draw_button(self, cx, cy, color):
        """Draw a small circular button."""
        self.display.set_pixel(cx, cy, color)
        self.display.set_pixel(cx + 1, cy, color)
        self.display.set_pixel(cx, cy + 1, color)
        self.display.set_pixel(cx + 1, cy + 1, color)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Title
        self.display.draw_text_small(2, 2, "CONTROLS", Colors.CYAN)

        # Separator
        for x in range(2, 62):
            self.display.set_pixel(x, 9, Colors.GRAY)

        # Joystick section
        self._draw_joystick(8, 17)
        self.display.draw_text_small(17, 14, "MOVE", Colors.WHITE)
        self.display.draw_text_small(17, 21, "NAVIGATE", Colors.GRAY)

        # Buttons section
        self._draw_button(6, 33, Colors.WHITE)
        self._draw_button(11, 33, Colors.WHITE)
        self.display.draw_text_small(17, 32, "ACTION", Colors.WHITE)
        self.display.draw_text_small(17, 39, "SELECT", Colors.GRAY)

        # Exit info
        self.display.draw_text_small(2, 48, "HOLD BOTH", Colors.YELLOW)
        self.display.draw_text_small(2, 55, "BUTTONS:BACK", Colors.YELLOW)

        # Exit hold progress bar
        if self.exit_hold > 0:
            bar_w = int((self.exit_hold / 2.0) * 60)
            bar_w = min(60, bar_w)
            if bar_w > 0:
                self.display.draw_rect(2, 62, bar_w, 2, Colors.RED)

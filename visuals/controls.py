"""
Controls - Input reference display
====================================
Shows the arcade panel control layout and button functions.

Controls:
  Any button - Exit to menu
"""

from . import Visual, Display, Colors, GRID_SIZE


class Controls(Visual):
    name = "CONTROLS"
    description = "Button guide"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def handle_input(self, input_state) -> bool:
        if (input_state.action_l or input_state.action_r or
                input_state.up_pressed or input_state.down_pressed or
                input_state.left_pressed or input_state.right_pressed):
            self.wants_exit = True
            return True
        return False

    def update(self, dt: float):
        self.time += dt

    def _draw_joystick(self, cx, cy):
        """Draw a small joystick icon with directional arrows."""
        # Center knob
        self.display.set_pixel(cx, cy, Colors.WHITE)
        self.display.set_pixel(cx + 1, cy, Colors.WHITE)
        self.display.set_pixel(cx, cy + 1, Colors.WHITE)
        self.display.set_pixel(cx + 1, cy + 1, Colors.WHITE)

        # Up arrow
        self.display.set_pixel(cx, cy - 2, Colors.CYAN)
        self.display.set_pixel(cx + 1, cy - 2, Colors.CYAN)
        self.display.set_pixel(cx, cy - 1, Colors.CYAN)
        self.display.set_pixel(cx + 1, cy - 1, Colors.CYAN)

        # Down arrow
        self.display.set_pixel(cx, cy + 3, Colors.CYAN)
        self.display.set_pixel(cx + 1, cy + 3, Colors.CYAN)
        self.display.set_pixel(cx, cy + 2, Colors.CYAN)
        self.display.set_pixel(cx + 1, cy + 2, Colors.CYAN)

        # Left arrow
        self.display.set_pixel(cx - 2, cy, Colors.CYAN)
        self.display.set_pixel(cx - 2, cy + 1, Colors.CYAN)
        self.display.set_pixel(cx - 1, cy, Colors.CYAN)
        self.display.set_pixel(cx - 1, cy + 1, Colors.CYAN)

        # Right arrow
        self.display.set_pixel(cx + 3, cy, Colors.CYAN)
        self.display.set_pixel(cx + 3, cy + 1, Colors.CYAN)
        self.display.set_pixel(cx + 2, cy, Colors.CYAN)
        self.display.set_pixel(cx + 2, cy + 1, Colors.CYAN)

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
        self._draw_button(6, 33, Colors.RED)
        self._draw_button(11, 33, Colors.BLUE)
        self.display.draw_text_small(17, 32, "ACTION", Colors.WHITE)
        self.display.draw_text_small(17, 39, "SELECT", Colors.GRAY)

        # Exit info
        self.display.draw_text_small(2, 50, "HOLD 2S:MENU", Colors.YELLOW)

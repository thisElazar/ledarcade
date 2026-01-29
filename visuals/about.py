"""
About - System information display
===================================
Shows hardware details for the LED arcade system.

Controls:
  Any button - Exit to menu
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


class About(Visual):
    name = "ABOUT"
    description = "System info"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

    def handle_input(self, input_state) -> bool:
        # Any button press exits
        if (input_state.action_l or input_state.action_r or
                input_state.up_pressed or input_state.down_pressed or
                input_state.left_pressed or input_state.right_pressed):
            self.wants_exit = True
            return True
        return False

    def update(self, dt: float):
        self.time += dt

    def _get_pulse_color(self, base_color, intensity=0.3):
        """Apply a gentle pulse to a color based on time."""
        pulse = 0.5 + 0.5 * math.sin(self.time * 2)
        factor = 1.0 - intensity + intensity * pulse
        return (
            min(255, int(base_color[0] * factor)),
            min(255, int(base_color[1] * factor)),
            min(255, int(base_color[2] * factor))
        )

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Title
        pulse_title = self._get_pulse_color(Colors.CYAN, 0.2)
        self.display.draw_text_small(2, 2, "SYSTEM", pulse_title)

        # Separator line
        for x in range(2, 62):
            self.display.set_pixel(x, 9, Colors.GRAY)

        # Hardware info
        self.display.draw_text_small(2, 13, "64X64 RGB", Colors.WHITE)
        self.display.draw_text_small(2, 20, "LED MATRIX", Colors.WHITE)

        # More info
        self.display.draw_text_small(2, 32, "HUB75", Colors.GRAY)
        self.display.draw_text_small(2, 39, "RASPBERRY PI", Colors.WHITE)

        # Fun stats
        self.display.draw_text_small(2, 50, "4096 PIXELS", Colors.GRAY)

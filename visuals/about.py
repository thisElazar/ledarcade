"""
About - System information display
===================================
Shows hardware details for the LED arcade system.
Second page shows a retro terminal "HELLO WORLD" easter egg.

Controls:
  Button   - Exit to menu
  Joystick - Hidden second page
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
        self.page = 0  # 0 = system info, 1 = hello world

    def handle_input(self, input_state) -> bool:
        # Buttons always exit
        if input_state.action_l or input_state.action_r:
            self.wants_exit = True
            return True
        # Joystick is the secret — advances to hello world page, then exits
        if (input_state.up_pressed or input_state.down_pressed or
                input_state.left_pressed or input_state.right_pressed):
            if self.page == 0:
                self.page = 1
                self.time = 0.0
            else:
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

    def _draw_system_info(self):
        """Draw page 0: system information."""
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
        self.display.draw_text_small(2, 39, "RASPBERRY PI 3", Colors.WHITE)

        # Fun stats
        self.display.draw_text_small(2, 50, "4096 PIXELS", Colors.GRAY)

        # Footer
        self.display.draw_line(0, 56, 63, 56, Colors.DARK_GRAY)
        self.display.draw_text_small(2, 58, "BTN:EXIT", Colors.GRAY)

    def _draw_hello_world(self):
        """Draw page 1: retro green terminal with typewriter effect."""
        TERM_GREEN = (0, 255, 65)
        DIM_GREEN = (0, 100, 25)

        # Terminal prompt and message
        full_text = "> HELLO WORLD"
        chars_per_sec = 8
        visible_chars = min(len(full_text), int(self.time * chars_per_sec))
        typed_text = full_text[:visible_chars]
        typing_done = visible_chars >= len(full_text)

        # Scanline effect - subtle horizontal lines
        for y in range(0, GRID_SIZE, 4):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (0, 8, 2))

        # Terminal header
        self.display.draw_text_small(2, 2, "TERMINAL", DIM_GREEN)
        for x in range(2, 62):
            self.display.set_pixel(x, 9, DIM_GREEN)

        # Typed text
        self.display.draw_text_small(2, 24, typed_text, TERM_GREEN)

        # Blinking cursor
        cursor_x = 2 + visible_chars * 5
        if cursor_x < GRID_SIZE - 4:
            # Blink every 0.5s
            if typing_done:
                cursor_on = int(self.time * 2) % 2 == 0
            else:
                cursor_on = True  # Solid while typing
            if cursor_on:
                self.display.draw_rect(cursor_x, 24, 4, 6, TERM_GREEN)

        # Credits fade in after typing finishes
        if typing_done:
            self.display.draw_text_small(2, 40, "ELAZAR & CLAUDE", DIM_GREEN)

        # Footer
        self.display.draw_line(0, 56, 63, 56, DIM_GREEN)
        self.display.draw_text_small(2, 58, "BTN:EXIT", DIM_GREEN)

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.page == 0:
            self._draw_system_info()
        else:
            self._draw_hello_world()

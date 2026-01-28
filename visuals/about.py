"""
About - System information and credits
======================================
Shows version info, controls reference, and system details.

Controls:
  Up/Down - Scroll between pages
  Action  - Cycle color theme
  Escape  - Exit
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


class About(Visual):
    name = "ABOUT"
    description = "Credits"
    category = "utility"

    # Color themes
    THEMES = [
        (Colors.CYAN, Colors.WHITE, Colors.GRAY),      # Default: cyan title, white text, gray dim
        (Colors.GREEN, Colors.LIME, Colors.GRAY),      # Matrix green
        (Colors.MAGENTA, Colors.PINK, Colors.PURPLE),  # Synthwave
        (Colors.ORANGE, Colors.YELLOW, Colors.RED),    # Fire
        (Colors.BLUE, Colors.CYAN, Colors.PURPLE),     # Ocean
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.page = 0
        self.num_pages = 2
        self.theme_index = 0
        self.page_transition = 0.0  # For smooth page transitions

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Page navigation
        if input_state.down and self.page < self.num_pages - 1:
            self.page += 1
            self.page_transition = 1.0
            consumed = True
        if input_state.up and self.page > 0:
            self.page -= 1
            self.page_transition = 1.0
            consumed = True

        # Theme cycling
        if input_state.action:
            self.theme_index = (self.theme_index + 1) % len(self.THEMES)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        # Decay page transition effect
        if self.page_transition > 0:
            self.page_transition = max(0, self.page_transition - dt * 4)

    def _get_pulse_color(self, base_color, intensity=0.3):
        """Apply a gentle pulse to a color based on time."""
        pulse = 0.5 + 0.5 * math.sin(self.time * 2)
        factor = 1.0 - intensity + intensity * pulse
        return (
            min(255, int(base_color[0] * factor)),
            min(255, int(base_color[1] * factor)),
            min(255, int(base_color[2] * factor))
        )

    def _draw_page_indicator(self, title_color):
        """Draw small dots showing current page."""
        base_x = 28
        y = 60
        for i in range(self.num_pages):
            if i == self.page:
                self.display.set_pixel(base_x + i * 4, y, title_color)
                self.display.set_pixel(base_x + i * 4 + 1, y, title_color)
            else:
                self.display.set_pixel(base_x + i * 4, y, Colors.DARK_GRAY)
                self.display.set_pixel(base_x + i * 4 + 1, y, Colors.DARK_GRAY)

    def _draw_page_0(self, title_color, text_color, dim_color):
        """Main info page: title, version, controls."""
        # Title with pulse effect
        pulse_title = self._get_pulse_color(title_color, 0.2)
        self.display.draw_text_small(2, 2, "LED ARCADE", pulse_title)

        # Separator line
        for x in range(2, 62):
            self.display.set_pixel(x, 9, dim_color)

        # Version
        self.display.draw_text_small(2, 13, "V1.0", text_color)

        # Controls section
        self.display.draw_text_small(2, 22, "CONTROLS:", dim_color)
        self.display.draw_text_small(2, 29, "^V<> MOVE", text_color)
        self.display.draw_text_small(2, 36, "SPC  ACTION", text_color)
        self.display.draw_text_small(2, 43, "Z    ALT", text_color)
        self.display.draw_text_small(2, 50, "Q    BACK", text_color)

    def _draw_page_1(self, title_color, text_color, dim_color):
        """System info page."""
        # Title
        pulse_title = self._get_pulse_color(title_color, 0.2)
        self.display.draw_text_small(2, 2, "SYSTEM", pulse_title)

        # Separator line
        for x in range(2, 62):
            self.display.set_pixel(x, 9, dim_color)

        # Hardware info
        self.display.draw_text_small(2, 13, "64X64 RGB", text_color)
        self.display.draw_text_small(2, 20, "LED MATRIX", text_color)

        # More info
        self.display.draw_text_small(2, 32, "HUB75", dim_color)
        self.display.draw_text_small(2, 39, "RASPBERRY PI", text_color)

        # Fun stats or credits
        self.display.draw_text_small(2, 50, "4096 PIXELS", dim_color)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Get current theme colors
        title_color, text_color, dim_color = self.THEMES[self.theme_index]

        # Draw current page
        if self.page == 0:
            self._draw_page_0(title_color, text_color, dim_color)
        elif self.page == 1:
            self._draw_page_1(title_color, text_color, dim_color)

        # Draw page indicator
        self._draw_page_indicator(title_color)

        # Draw subtle transition flash
        if self.page_transition > 0:
            flash_intensity = int(30 * self.page_transition)
            # Add slight flash overlay effect by brightening a few pixels
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if (x + y) % 8 == 0:
                        current = self.display.get_pixel(x, y)
                        brightened = (
                            min(255, current[0] + flash_intensity),
                            min(255, current[1] + flash_intensity),
                            min(255, current[2] + flash_intensity)
                        )
                        self.display.set_pixel(x, y, brightened)

"""
Brightness - Display brightness control
========================================
Adjust the LED panel brightness.

Controls:
  Up/Down - Adjust brightness
  Button  - Accept and return to menu
"""

from . import Visual, Display, Colors, GRID_SIZE


class Settings(Visual):
    name = "BRIGHTNESS"
    description = "Adjust brightness"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        # Initialize brightness from hardware if available, otherwise default to 80
        if hasattr(self.display, 'matrix'):
            self.brightness = self.display.matrix.brightness
        else:
            self.brightness = 80
        self.step = 5  # Brightness adjustment step

    def set_brightness(self, value):
        """Set brightness and apply to hardware if available."""
        # Clamp to valid range (minimum 10 to avoid black screen)
        value = max(10, min(100, value))
        self.brightness = value
        # Try to apply to hardware if available
        if hasattr(self.display, 'matrix'):
            self.display.matrix.brightness = value

    def handle_input(self, input_state) -> bool:
        if input_state.up_pressed:
            self.set_brightness(self.brightness + self.step)
            return True
        elif input_state.down_pressed:
            self.set_brightness(self.brightness - self.step)
            return True

        # Button press accepts and exits
        if input_state.action_l or input_state.action_r:
            self.wants_exit = True
            return True

        return False

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Title
        self.display.draw_text_small(2, 2, "BRIGHTNESS", Colors.CYAN)
        self.display.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

        # Draw brightness bar
        bar_x = 2
        bar_y = 20
        bar_width = 50
        bar_height = 8

        # Bar outline
        self.display.draw_rect(bar_x, bar_y, bar_width, bar_height, Colors.GRAY, filled=False)

        # Filled portion based on brightness (10-100 maps to bar width)
        fill_width = int((self.brightness - 10) / 90 * (bar_width - 2))
        if fill_width > 0:
            # Use a color gradient from dim to bright
            if self.brightness < 40:
                bar_color = Colors.RED
            elif self.brightness < 70:
                bar_color = Colors.YELLOW
            else:
                bar_color = Colors.GREEN
            self.display.draw_rect(bar_x + 1, bar_y + 1, fill_width, bar_height - 2, bar_color)

        # Percentage display
        self.display.draw_text_small(54, 22, f"{self.brightness}", Colors.WHITE)

        # Instructions at bottom
        self.display.draw_line(0, 50, 63, 50, Colors.DARK_GRAY)
        self.display.draw_text_small(2, 54, "BTN:ACCEPT", Colors.GRAY)

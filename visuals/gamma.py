"""
Gamma - Display gamma curve adjustment
=======================================
Adjust gamma and toe-lift settings with live preview.

Controls:
  Up/Down   - Select parameter (GAMMA or TOE)
  Left/Right - Adjust selected value
  Button     - Accept and return to menu
"""

from . import Visual, Display, Colors, GRID_SIZE


class Gamma(Visual):
    name = "GAMMA"
    description = "Adjust gamma curve"
    category = "utility"
    custom_exit = True  # We handle our own exit via wants_exit

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        import settings as persistent
        self.gamma = persistent.get_gamma()
        self.toe = persistent.get_toe()
        self.selected = 0  # 0 = GAMMA, 1 = TOE

    def _apply(self):
        """Apply current gamma/toe to display (live preview)."""
        self.display.set_gamma(self.gamma, self.toe)

    def _curve(self, x):
        """Compute gamma+toe curve for normalized x (0-1)."""
        return min(1.0, max(0.0, x ** self.gamma + self.toe * x * (1 - x) ** 2))

    def handle_input(self, input_state) -> bool:
        if input_state.up_pressed:
            self.selected = 0
            return True
        elif input_state.down_pressed:
            self.selected = 1
            return True

        if input_state.left_pressed or input_state.right_pressed:
            delta = 1 if input_state.right_pressed else -1
            if self.selected == 0:
                self.gamma = max(1.0, min(3.0, round(self.gamma + delta * 0.1, 1)))
            else:
                self.toe = max(0.0, min(0.50, round(self.toe + delta * 0.05, 2)))
            self._apply()
            return True

        if input_state.action_l or input_state.action_r:
            # Save and exit
            import settings as persistent
            persistent.set_gamma(self.gamma)
            persistent.set_toe(self.toe)
            self.wants_exit = True
            return True

        return False

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Title
        d.draw_text_small(2, 2, "GAMMA", Colors.CYAN)
        d.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

        # Parameter rows
        gamma_color = Colors.WHITE if self.selected == 0 else Colors.GRAY
        toe_color = Colors.WHITE if self.selected == 1 else Colors.GRAY

        # GAMMA row
        d.draw_text_small(2, 13, "GAMMA", gamma_color)
        d.draw_text_small(26, 13, f"{self.gamma:.1f}", gamma_color)
        if self.selected == 0:
            d.set_pixel(49, 15, gamma_color)
            d.set_pixel(50, 14, gamma_color)
            d.set_pixel(50, 16, gamma_color)
            d.set_pixel(54, 15, gamma_color)
            d.set_pixel(53, 14, gamma_color)
            d.set_pixel(53, 16, gamma_color)

        # TOE row
        d.draw_text_small(2, 21, "TOE", toe_color)
        d.draw_text_small(26, 21, f"{self.toe:.2f}", toe_color)
        if self.selected == 1:
            d.set_pixel(49, 23, toe_color)
            d.set_pixel(50, 22, toe_color)
            d.set_pixel(50, 24, toe_color)
            d.set_pixel(54, 23, toe_color)
            d.set_pixel(53, 22, toe_color)
            d.set_pixel(53, 24, toe_color)

        d.draw_line(0, 28, 63, 28, Colors.DARK_GRAY)

        # Gradient bar: corrected (through gamma+toe curve)
        d.draw_text_small(2, 31, "CURVE", Colors.GRAY)
        bar_y = 37
        for x in range(64):
            norm = x / 63.0
            val = int(self._curve(norm) * 255)
            d.set_pixel(x, bar_y, (val, val, val))
            d.set_pixel(x, bar_y + 1, (val, val, val))
            d.set_pixel(x, bar_y + 2, (val, val, val))

        # Gradient bar: linear reference
        d.draw_text_small(2, 42, "LINEAR", Colors.GRAY)
        ref_y = 48
        for x in range(64):
            val = int((x / 63.0) * 255)
            d.set_pixel(x, ref_y, (val, val, val))
            d.set_pixel(x, ref_y + 1, (val, val, val))
            d.set_pixel(x, ref_y + 2, (val, val, val))

        # Footer
        d.draw_line(0, 53, 63, 53, Colors.DARK_GRAY)
        d.draw_text_small(2, 56, "BTN:ACCEPT", Colors.GRAY)

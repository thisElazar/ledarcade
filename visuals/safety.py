"""
Safety - Epilepsy, Colorblindness & Accessibility Settings
==========================================================
Settings hub for display accessibility features.

Controls:
  Up/Down    - Navigate between options
  Left/Right - Toggle/cycle/adjust the selected option
  Button     - Accept and return to menu
"""

from . import Visual, Display, Colors, GRID_SIZE


# Colorblind mode cycle order and short display labels
_CB_MODES = ["none", "protanopia", "deuteranopia", "tritanopia"]
_CB_LABELS = {"none": "NONE", "protanopia": "PROT", "deuteranopia": "DEUT",
              "tritanopia": "TRIT"}


class Safety(Visual):
    name = "SAFETY"
    description = "Accessibility settings"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        import settings as persistent
        self.epilepsy = persistent.get_epilepsy_safe()
        self.cb_mode = persistent.get_colorblind_mode()
        self.max_bright = persistent.get_max_brightness_pct()
        self.cursor = 0  # 0=epilepsy, 1=colorblind, 2=max brightness

    def _apply(self):
        """Persist settings and push to display's safety pipeline."""
        import settings as persistent
        persistent.set_epilepsy_safe(self.epilepsy)
        persistent.set_colorblind_mode(self.cb_mode)
        persistent.set_max_brightness_pct(self.max_bright)
        if hasattr(self.display, 'set_safety'):
            self.display.set_safety(
                colorblind_mode=self.cb_mode,
                epilepsy_safe=self.epilepsy,
                max_brightness_pct=self.max_bright,
            )

    def handle_input(self, input_state) -> bool:
        # Navigate options
        if input_state.up_pressed:
            self.cursor = (self.cursor - 1) % 3
            return True
        if input_state.down_pressed:
            self.cursor = (self.cursor + 1) % 3
            return True

        # Button press: accept and exit
        if input_state.action_l or input_state.action_r:
            self.wants_exit = True
            return True

        # Left/right: toggle/cycle/adjust the selected option
        if input_state.left_pressed or input_state.right_pressed:
            if self.cursor == 0:
                self.epilepsy = not self.epilepsy
            elif self.cursor == 1:
                idx = _CB_MODES.index(self.cb_mode)
                step = 1 if input_state.right_pressed else -1
                self.cb_mode = _CB_MODES[(idx + step) % len(_CB_MODES)]
            elif self.cursor == 2:
                step = 5 if input_state.right_pressed else -5
                self.max_bright = max(10, min(100, self.max_bright + step))
            self._apply()
            return True

        return False

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Title
        d.draw_text_small(2, 2, "SAFETY", Colors.CYAN)
        d.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

        # Row positions
        rows = [14, 26, 38]
        labels = ["EPILEPSY", "COLOR", "MAX BRT"]

        for i, (y, label) in enumerate(zip(rows, labels)):
            selected = (i == self.cursor)
            # Selection indicator
            prefix_color = Colors.YELLOW if selected else Colors.GRAY
            label_color = Colors.WHITE if selected else Colors.GRAY

            # Draw cursor arrow
            if selected:
                d.draw_text_small(2, y, ">", Colors.YELLOW)

            # Label
            d.draw_text_small(8, y, label, label_color)

            # Value
            if i == 0:
                val = "ON" if self.epilepsy else "OFF"
                val_color = Colors.GREEN if self.epilepsy else Colors.RED
            elif i == 1:
                val = _CB_LABELS.get(self.cb_mode, "NONE")
                val_color = Colors.GREEN if self.cb_mode != "none" else prefix_color
            else:
                val = str(self.max_bright)
                val_color = Colors.WHITE if selected else Colors.GRAY

            d.draw_text_small(42, y, val, val_color)

        # Instructions at bottom
        d.draw_line(0, 52, 63, 52, Colors.DARK_GRAY)
        d.draw_text_small(2, 55, "BTN:ACCEPT", Colors.GRAY)

"""
Safety - Epilepsy, Colorblindness & Accessibility Settings
==========================================================
Settings hub for display accessibility features.

Controls:
  Up/Down    - Navigate between options
  Left/Right - Toggle/cycle/adjust the selected option
  Button     - Accept and return to menu (on REFRESH: open the test pattern)

Test pattern:
  Left/Right - Change the refresh rate, live
  Button     - Back to the list
"""

from . import Visual, Display, Colors, GRID_SIZE


# Colorblind mode cycle order and short display labels
_CB_MODES = ["none", "protanopia", "deuteranopia", "tritanopia"]
_CB_LABELS = {"none": "NONE", "protanopia": "PROT", "deuteranopia": "DEUT",
              "tritanopia": "TRIT"}

# Below this the whole panel flickers visibly, so EPILEPSY skips those rates
_FLICKER_HZ = 60
# Wait this long after the last press before reopening the matrix, so
# stepping through several rates reopens it once, not at every step
_APPLY_DELAY = 0.4

_BARS = [Colors.WHITE, Colors.YELLOW, Colors.CYAN, Colors.GREEN,
         Colors.MAGENTA, Colors.RED, Colors.BLUE, Colors.GRAY]


class Safety(Visual):
    name = "SAFETY"
    description = "Accessibility settings"
    category = "utility"
    GUIDE = {
        'desc': 'Accessibility settings in one place: reduce flashing for photosensitivity, switch on colorblind-friendly palettes, and other display-comfort options.',
        'legend': {
            'COLOR': 'Colorblind filter (NONE=off, PROT=protanopia, DEUT=deuteranopia, TRIT=tritanopia).',
            'MAX BRT': 'Maximum brightness percentage the panel is allowed to use.',
            'REFRESH': 'Locks the LED refresh rate in Hz so cameras film it without rolling bands (OFF=unlocked). The button opens a test pattern.',
        },
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        import settings as persistent
        self.epilepsy = persistent.get_epilepsy_safe()
        self.cb_mode = persistent.get_colorblind_mode()
        self.max_bright = persistent.get_max_brightness_pct()
        self.refresh = persistent.get_refresh_hz()
        self._refresh_applied = self.refresh  # what the matrix is running at
        self._apply_timer = None              # seconds until the matrix reopens
        self.pattern = False                  # the full-screen test pattern is up
        self.cursor = 0  # 0=epilepsy, 1=colorblind, 2=max brightness, 3=refresh

    def _refresh_choices(self):
        import settings as persistent
        if self.epilepsy:
            return [hz for hz in persistent.REFRESH_CHOICES if hz == 0 or hz >= _FLICKER_HZ]
        return persistent.REFRESH_CHOICES

    def _step_refresh(self, step):
        choices = self._refresh_choices()
        i = choices.index(self.refresh) if self.refresh in choices else 0
        self.refresh = choices[(i + step) % len(choices)]
        self._apply_timer = _APPLY_DELAY

    def _apply(self):
        """Persist settings and push to display's safety pipeline."""
        import settings as persistent
        persistent.set_epilepsy_safe(self.epilepsy)
        persistent.set_colorblind_mode(self.cb_mode)
        persistent.set_max_brightness_pct(self.max_bright)
        persistent.set_refresh_hz(self.refresh)
        if hasattr(self.display, 'set_safety'):
            self.display.set_safety(
                colorblind_mode=self.cb_mode,
                epilepsy_safe=self.epilepsy,
                max_brightness_pct=self.max_bright,
            )

    def _apply_refresh(self):
        """Reopen the matrix at the new rate. The setting is saved first, so if
        reopening fails the restart comes back at that rate anyway."""
        self._apply_timer = None
        if self.refresh == self._refresh_applied:
            return
        self._refresh_applied = self.refresh
        if hasattr(self.display, 'set_refresh_hz'):
            try:
                self.display.set_refresh_hz(self.refresh)
            except Exception as e:
                import os
                import sys
                print(f"Refresh change failed ({e}); restarting")
                os.execv(sys.executable, [sys.executable] + sys.argv)

    def handle_input(self, input_state) -> bool:
        if self.pattern:
            if input_state.left_pressed or input_state.right_pressed:
                self._step_refresh(1 if input_state.right_pressed else -1)
                self._apply()
                return True
            if input_state.action_l or input_state.action_r:
                self.pattern = False
                return True
            return False

        # Navigate options
        if input_state.up_pressed:
            self.cursor = (self.cursor - 1) % 4
            return True
        if input_state.down_pressed:
            self.cursor = (self.cursor + 1) % 4
            return True

        # Button press: accept and exit, or open the refresh test pattern
        if input_state.action_l or input_state.action_r:
            if self.cursor == 3:
                self.pattern = True
            else:
                self._apply_refresh()
                self.wants_exit = True
            return True

        # Left/right: toggle/cycle/adjust the selected option
        if input_state.left_pressed or input_state.right_pressed:
            if self.cursor == 0:
                self.epilepsy = not self.epilepsy
                if self.refresh not in self._refresh_choices():
                    self.refresh = 120   # leave the flickering rates behind
                    self._apply_timer = 0.0
            elif self.cursor == 1:
                idx = _CB_MODES.index(self.cb_mode)
                step = 1 if input_state.right_pressed else -1
                self.cb_mode = _CB_MODES[(idx + step) % len(_CB_MODES)]
            elif self.cursor == 2:
                step = 5 if input_state.right_pressed else -5
                self.max_bright = max(10, min(100, self.max_bright + step))
            elif self.cursor == 3:
                self._step_refresh(1 if input_state.right_pressed else -1)
            self._apply()
            return True

        return False

    def update(self, dt: float):
        self.time += dt
        if self._apply_timer is not None:
            self._apply_timer -= dt
            if self._apply_timer <= 0:
                self._apply_refresh()

    def _refresh_label(self):
        return f"{self.refresh} HZ" if self.refresh else "OFF"

    def _draw_pattern(self):
        """Colour bars, a grey ramp and a white field, the things a rolling
        shutter bands most visibly, with a line sweeping across for motion."""
        d = self.display
        d.clear(Colors.BLACK)
        d.draw_text_small(2, 2, "REFRESH", Colors.CYAN)
        label = self._refresh_label()
        d.draw_text_small(62 - len(label) * 4, 2, label,
                          Colors.GREEN if self.refresh else Colors.RED)
        for i, color in enumerate(_BARS):
            d.draw_rect(i * 8, 9, 8, 20, color)
        for i in range(16):
            v = i * 17
            d.draw_rect(i * 4, 29, 4, 8, (v, v, v))
        d.draw_rect(0, 37, 64, 14, Colors.WHITE)
        x = int(self.time * 32) % 64
        d.draw_line(x, 9, x, 50, Colors.BLACK)
        d.draw_text_small(2, 55, "L/R:HZ BTN:BACK", Colors.GRAY)

    def draw(self):
        if self.pattern:
            self._draw_pattern()
            return

        d = self.display
        d.clear(Colors.BLACK)

        # Title
        d.draw_text_small(2, 2, "SAFETY", Colors.CYAN)
        d.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

        # Row positions
        rows = [13, 23, 33, 43]
        labels = ["EPILEPSY", "COLOR", "MAX BRT", "REFRESH"]

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
            elif i == 2:
                val = str(self.max_bright)
                val_color = Colors.WHITE if selected else Colors.GRAY
            else:
                val = str(self.refresh) if self.refresh else "OFF"
                val_color = Colors.GREEN if self.refresh else Colors.RED

            d.draw_text_small(42, y, val, val_color)

        # Instructions at bottom
        d.draw_line(0, 52, 63, 52, Colors.DARK_GRAY)
        hint = "BTN:TEST" if self.cursor == 3 else "BTN:ACCEPT"
        d.draw_text_small(2, 55, hint, Colors.GRAY)

"""
Timers - Idle, cycle, and sleep timer settings
================================================
Configure timing behavior for the arcade.

Controls:
  Up/Down    - Select parameter
  Left/Right - Adjust value
  Button     - Accept and return to menu
"""

from . import Visual, Display, Colors, GRID_SIZE


class Timers(Visual):
    name = "IDLE TIMERS"
    description = "Idle, cycle, sleep timers"
    category = "utility"
    custom_exit = True

    PARAMS = [
        # (label, setting_key, min, max, step, fmt)
        ("IDLE",   "idle_timeout",          15, 300, 15, "s"),
        ("CYCLE",  "cycle_duration",        10, 120,  5, "s"),
        ("TITLES", "titles_cycle_duration",  3, 120,  1, "s"),
        ("SLEEP",  "sleep_timer",            0, 180,  5, "m"),
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.selected = 0
        import settings as persistent
        self.values = [
            persistent.get_idle_timeout(),
            persistent.get_cycle_duration(),
            persistent.get_titles_cycle_duration(),
            persistent.get_sleep_timer(),
        ]

    def handle_input(self, input_state) -> bool:
        if input_state.up_pressed:
            self.selected = (self.selected - 1) % len(self.PARAMS)
            return True
        elif input_state.down_pressed:
            self.selected = (self.selected + 1) % len(self.PARAMS)
            return True

        if input_state.left_pressed or input_state.right_pressed:
            _, _, lo, hi, step, _ = self.PARAMS[self.selected]
            delta = step if input_state.right_pressed else -step
            self.values[self.selected] = max(lo, min(hi, self.values[self.selected] + delta))
            return True

        if input_state.action_l or input_state.action_r:
            import settings as persistent
            persistent.set_idle_timeout(self.values[0])
            persistent.set_cycle_duration(self.values[1])
            persistent.set_titles_cycle_duration(self.values[2])
            persistent.set_sleep_timer(self.values[3])
            self.wants_exit = True
            return True

        return False

    def update(self, dt: float):
        self.time += dt

    def _fmt_value(self, idx):
        label, _, _, _, _, unit = self.PARAMS[idx]
        val = self.values[idx]
        if unit == "m" and val == 0:
            return "OFF"
        if unit == "m":
            if val >= 60:
                h = val // 60
                m = val % 60
                return f"{h}H{m:02d}" if m else f"{h}H"
            return f"{val}M"
        # seconds — show as minutes:seconds if >= 60
        if val >= 60:
            m = val // 60
            s = val % 60
            return f"{m}M{s:02d}" if s else f"{m}M"
        return f"{val}S"

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Title
        d.draw_text_small(2, 2, "TIMERS", Colors.CYAN)
        d.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

        # Parameter rows
        for i, (label, _, _, _, _, _) in enumerate(self.PARAMS):
            y = 14 + i * 9
            color = Colors.WHITE if i == self.selected else Colors.GRAY

            d.draw_text_small(2, y, label, color)
            val_str = self._fmt_value(i)
            d.draw_text_small(30, y, val_str, color)

            # Arrow indicators for selected row
            if i == self.selected:
                ay = y + 2
                # Left arrow
                d.set_pixel(52, ay, color)
                d.set_pixel(53, ay - 1, color)
                d.set_pixel(53, ay + 1, color)
                # Right arrow
                d.set_pixel(57, ay, color)
                d.set_pixel(56, ay - 1, color)
                d.set_pixel(56, ay + 1, color)

        # Descriptions
        d.draw_line(0, 51, 63, 51, Colors.DARK_GRAY)
        descs = [
            "SCREENSAVER DELAY",
            "VISUAL ROTATION",
            "TITLE CARD TIME",
            "AUTO POWER OFF",
        ]
        d.draw_text_small(2, 53, descs[self.selected], Colors.DARK_GRAY)

        # Footer
        d.draw_line(0, 59, 63, 59, Colors.DARK_GRAY)
        d.draw_text_small(2, 61, "BTN:ACCEPT", Colors.GRAY)

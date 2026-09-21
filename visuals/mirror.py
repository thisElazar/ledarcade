"""
Mirror - Live Display Mirror Settings
=====================================
Switches the live mirror (mirror.py) on or off and sets its network port, so
run_mirror.py on a laptop can show what the panel is showing.

Controls:
  Up/Down    - Navigate between options
  Left/Right - Toggle the mirror
  Button     - On PORT: edit the number; elsewhere: accept and return to menu

Editing the port:
  Left/Right - Pick a digit
  Up/Down    - Change it
  Button     - Set the port
"""

from . import Visual, Display, Colors
from mirror import PORT_RANGE


class Mirror(Visual):
    name = "MIRROR"
    description = "Watch the panel on a laptop"
    category = "utility"
    GUIDE = {
        'desc': 'Lets a computer on the same network show what the panel is showing, live. Off until you switch it on here; the port can be changed if another device already uses it.',
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        import settings as persistent
        self.enabled = persistent.get_mirror_enabled()
        self.port = persistent.get_mirror_port()
        self.cursor = 0       # 0=mirror on/off, 1=port
        self.digits = None    # the port's five digits while it is being edited
        self.digit = 0

    def _apply(self):
        """Persist settings and reopen the display's mirror tap."""
        import settings as persistent
        persistent.set_mirror_enabled(self.enabled)
        persistent.set_mirror_port(self.port)
        if hasattr(self.display, 'set_mirror'):
            self.display.set_mirror(self.enabled, self.port)

    def handle_input(self, input_state) -> bool:
        if self.digits is not None:
            return self._edit_port(input_state)

        if input_state.up_pressed or input_state.down_pressed:
            self.cursor = 1 - self.cursor
            return True

        if input_state.action_l or input_state.action_r:
            if self.cursor == 1:
                self.digits = [int(c) for c in f"{self.port:05d}"]
                self.digit = 0
            else:
                self.wants_exit = True
            return True

        if (input_state.left_pressed or input_state.right_pressed) and self.cursor == 0:
            self.enabled = not self.enabled
            self._apply()
            return True

        return False

    def _edit_port(self, input_state) -> bool:
        if input_state.left_pressed or input_state.right_pressed:
            step = 1 if input_state.right_pressed else -1
            self.digit = (self.digit + step) % 5
            return True
        if input_state.up_pressed or input_state.down_pressed:
            step = 1 if input_state.up_pressed else -1
            self.digits[self.digit] = (self.digits[self.digit] + step) % 10
            return True
        if input_state.action_l or input_state.action_r:
            port = int("".join(map(str, self.digits)))
            self.port = max(PORT_RANGE[0], min(PORT_RANGE[1], port))
            self.digits = None
            self._apply()
            return True
        return False

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        d.draw_text_small(2, 2, "MIRROR", Colors.CYAN)
        d.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

        editing = self.digits is not None
        for i, (y, label) in enumerate(((14, "MIRROR"), (26, "PORT"))):
            selected = (i == self.cursor)
            if selected:
                d.draw_text_small(2, y, ">", Colors.YELLOW)
            d.draw_text_small(8, y, label, Colors.WHITE if selected else Colors.GRAY)

        d.draw_text_small(42, 14, "ON" if self.enabled else "OFF",
                          Colors.GREEN if self.enabled else Colors.RED)

        if editing:
            d.draw_text_small(42, 26, "".join(map(str, self.digits)), Colors.YELLOW)
            x = 42 + self.digit * 4
            d.draw_line(x, 32, x + 2, 32, Colors.WHITE)
            d.draw_text_small(2, 40, f"{PORT_RANGE[0]}-{PORT_RANGE[1]}", Colors.GRAY)
        else:
            d.draw_text_small(42, 26, str(self.port),
                              Colors.WHITE if self.cursor == 1 else Colors.GRAY)

        d.draw_line(0, 52, 63, 52, Colors.DARK_GRAY)
        hint = "BTN:SET" if editing else "BTN:EDIT" if self.cursor == 1 else "BTN:ACCEPT"
        d.draw_text_small(2, 55, hint, Colors.GRAY)

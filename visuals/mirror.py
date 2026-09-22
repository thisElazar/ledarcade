"""
Mirror - Live Display Mirror Settings
=====================================
Switches the live mirror (mirror.py) on or off and sets its network port, so
run_mirror.py on a laptop can show what the panel is showing; switches HDMI
output, the same picture on a screen plugged into the Pi; and switches WEB,
which serves that picture to any browser on the network (run_web_mirror.py)
on the same PORT. With WEB selected, the line at the bottom is the address to
open; the port to add to it is the one above.

Controls:
  Up/Down    - Navigate between options
  Left/Right - Toggle MIRROR, HDMI or WEB
  Button     - On PORT: edit the number; elsewhere: accept and return to menu

Editing the port:
  Left/Right - Pick a digit
  Up/Down    - Change it
  Button     - Set the port
"""

from . import Visual, Display, Colors
from mirror import PORT_RANGE, lan_address


class Mirror(Visual):
    name = "MIRROR"
    description = "Watch the panel on a bigger screen"
    category = "utility"
    GUIDE = {
        'desc': 'Shows what the panel is showing somewhere bigger, live: on a computer on the same network, in a web browser on any phone or laptop there, or on a TV plugged into the HDMI port. All three are off until you switch them on here; the network port can be changed if another device already uses it. With WEB on, open the address shown at the bottom, followed by that port, in a browser.',
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        import settings as persistent
        self.enabled = persistent.get_mirror_enabled()
        self.port = persistent.get_mirror_port()
        self.hdmi = persistent.get_mirror_hdmi()
        self.web = persistent.get_mirror_web()
        self.address = lan_address() if self.web else ""
        self.cursor = 0       # 0=mirror on/off, 1=port, 2=hdmi, 3=web
        self.digits = None    # the port's five digits while it is being edited
        self.digit = 0

    def _apply(self):
        """Persist settings and reopen the display's mirror tap."""
        import settings as persistent
        persistent.set_mirror_enabled(self.enabled)
        persistent.set_mirror_port(self.port)
        persistent.set_mirror_hdmi(self.hdmi)
        persistent.set_mirror_web(self.web)
        self.address = lan_address() if self.web else ""
        if hasattr(self.display, 'set_mirror'):
            self.display.set_mirror(self.enabled, self.port, self.hdmi, self.web)

    def handle_input(self, input_state) -> bool:
        if self.digits is not None:
            return self._edit_port(input_state)

        if input_state.up_pressed or input_state.down_pressed:
            self.cursor = (self.cursor + (1 if input_state.down_pressed else -1)) % 4
            return True

        if input_state.action_l or input_state.action_r:
            if self.cursor == 1:
                self.digits = [int(c) for c in f"{self.port:05d}"]
                self.digit = 0
            else:
                self.wants_exit = True
            return True

        if (input_state.left_pressed or input_state.right_pressed) and self.cursor != 1:
            if self.cursor == 0:
                self.enabled = not self.enabled
            elif self.cursor == 2:
                self.hdmi = not self.hdmi
            else:
                self.web = not self.web
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
        for i, (y, label) in enumerate(((14, "MIRROR"), (24, "PORT"), (34, "HDMI"), (44, "WEB"))):
            if editing and y == 44:
                continue   # the port's range is shown on that line instead
            selected = (i == self.cursor)
            if selected:
                d.draw_text_small(2, y, ">", Colors.YELLOW)
            d.draw_text_small(8, y, label, Colors.WHITE if selected else Colors.GRAY)

        for y, on in ((14, self.enabled), (34, self.hdmi), (44, self.web)):
            if editing and y == 44:
                continue   # as above: the range takes that line
            d.draw_text_small(42, y, "ON" if on else "OFF", Colors.GREEN if on else Colors.RED)

        if editing:
            d.draw_text_small(42, 24, "".join(map(str, self.digits)), Colors.YELLOW)
            x = 42 + self.digit * 4
            d.draw_line(x, 30, x + 2, 30, Colors.WHITE)
            d.draw_text_small(2, 44, f"{PORT_RANGE[0]}-{PORT_RANGE[1]}", Colors.GRAY)
        else:
            d.draw_text_small(42, 24, str(self.port),
                              Colors.WHITE if self.cursor == 1 else Colors.GRAY)

        d.draw_line(0, 52, 63, 52, Colors.DARK_GRAY)
        if self.cursor == 3 and self.web and self.address and not editing:
            # 15 characters fit from x=2, and 255.255.255.255 is exactly 15
            d.draw_text_small(2, 55, self.address, Colors.CYAN)
        else:
            hint = "BTN:SET" if editing else "BTN:EDIT" if self.cursor == 1 else "BTN:ACCEPT"
            d.draw_text_small(2, 55, hint, Colors.GRAY)

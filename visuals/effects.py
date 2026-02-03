"""
Effects - Screensaver Transition Settings
==========================================
Toggle which transition effects are used in the idle screensaver.

Controls:
  Up/Down   - Navigate transitions
  Left/Right - Toggle on/off
  Button    - Accept and return to menu
"""

from . import Visual, Display, Colors, GRID_SIZE
from transitions import TRANSITION_TYPES, get_enabled_transitions, set_transition_enabled


class Effects(Visual):
    name = "EFFECTS"
    description = "Transition settings"
    category = "utility"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.cursor = 0
        self.scroll_offset = 0
        self.max_visible = 6  # How many items fit on screen

    def handle_input(self, input_state) -> bool:
        if input_state.up_pressed:
            self.cursor = max(0, self.cursor - 1)
            # Scroll up if cursor goes above visible area
            if self.cursor < self.scroll_offset:
                self.scroll_offset = self.cursor
            return True
        elif input_state.down_pressed:
            self.cursor = min(len(TRANSITION_TYPES) - 1, self.cursor + 1)
            # Scroll down if cursor goes below visible area
            if self.cursor >= self.scroll_offset + self.max_visible:
                self.scroll_offset = self.cursor - self.max_visible + 1
            return True
        elif input_state.left_pressed or input_state.right_pressed:
            # Toggle the selected transition
            if 0 <= self.cursor < len(TRANSITION_TYPES):
                t = TRANSITION_TYPES[self.cursor]
                enabled = get_enabled_transitions()
                currently_on = t in enabled
                set_transition_enabled(t, not currently_on)
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
        self.display.draw_text_small(2, 2, "EFFECTS", Colors.CYAN)
        self.display.draw_line(0, 9, 63, 9, Colors.DARK_GRAY)

        # Get enabled transitions
        enabled = get_enabled_transitions()

        # Draw transition list
        y = 12
        for i in range(self.scroll_offset, min(self.scroll_offset + self.max_visible, len(TRANSITION_TYPES))):
            t = TRANSITION_TYPES[i]
            is_selected = (i == self.cursor)
            is_enabled = (t in enabled)

            # Highlight selected row
            if is_selected:
                self.display.draw_rect(0, y, 64, 7, (30, 30, 40))

            # Checkbox
            box_x = 2
            if is_enabled:
                self.display.draw_rect(box_x, y + 1, 5, 5, Colors.GREEN)
            else:
                self.display.draw_rect(box_x, y + 1, 5, 5, Colors.DARK_GRAY, filled=False)

            # Transition name (truncate if needed)
            name = t.name[:10]
            text_color = Colors.WHITE if is_selected else Colors.GRAY
            self.display.draw_text_small(10, y + 1, name, text_color)

            y += 7

        # Scroll indicators
        if self.scroll_offset > 0:
            self.display.draw_text_small(58, 12, "^", Colors.GRAY)
        if self.scroll_offset + self.max_visible < len(TRANSITION_TYPES):
            self.display.draw_text_small(58, 47, "v", Colors.GRAY)

        # Instructions at bottom
        self.display.draw_line(0, 54, 63, 54, Colors.DARK_GRAY)
        self.display.draw_text_small(2, 57, "L/R:TOGGLE", Colors.GRAY)

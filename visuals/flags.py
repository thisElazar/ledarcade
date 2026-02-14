"""
FLAGS OF THE WORLD - National Flag Display
============================================
120+ country flags rendered from pre-built bitmap data, grouped by continent.
Flag images sourced from flagcdn.com, pre-rendered at 60x40 via tools/build_flags.py.
"""

from . import Visual, Colors
from .flag_data import FLAGS as FLAG_DATA, FLAG_W, FLAG_H

# Flag position: centered horizontally, with room for label below
FX = (64 - FLAG_W) // 2
FY = 6

# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------
GROUPS = [
    ('ALL',      'ALL COUNTRIES'),
    ('AFRICA',   'AFRICA'),
    ('AMERICAS', 'AMERICAS'),
    ('ASIA',     'ASIA'),
    ('EUROPE',   'EUROPE'),
    ('OCEANIA',  'OCEANIA'),
]


def _build_group_indices():
    all_sorted = sorted(range(len(FLAG_DATA)), key=lambda i: FLAG_DATA[i][0])
    indices = {'ALL': all_sorted}
    for key in ['AFRICA', 'AMERICAS', 'ASIA', 'EUROPE', 'OCEANIA']:
        indices[key] = [i for i, f in enumerate(FLAG_DATA) if f[1] == key]
    return indices


class Flags(Visual):
    name = "FLAGS"
    description = "Flags of the world"
    category = "household"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.flag_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 5.0
        self.overlay_timer = 0.0
        self.scroll_offset = 0.0

    def _current_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_flag(self):
        lst = self._current_list()
        if not lst:
            return FLAG_DATA[0]
        return FLAG_DATA[lst[self.flag_pos % len(lst)]]

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.flag_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.flag_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.left_pressed:
            lst = self._current_list()
            if lst:
                self.flag_pos = (self.flag_pos - 1) % len(lst)
            self.cycle_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.right_pressed:
            lst = self._current_list()
            if lst:
                self.flag_pos = (self.flag_pos + 1) % len(lst)
            self.cycle_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.scroll_offset += dt * 20
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                lst = self._current_list()
                if lst:
                    self.flag_pos = (self.flag_pos + 1) % len(lst)
                self.scroll_offset = 0.0

    def draw(self):
        d = self.display
        d.clear()

        flag = self._current_flag()
        name, continent, pixels = flag

        # Blit flag pixel data
        for y, row in enumerate(pixels):
            for x, color in enumerate(row):
                d.set_pixel(FX + x, FY + y, color)

        # Flag border
        d.draw_rect(FX - 1, FY - 1, FLAG_W + 2, FLAG_H + 2,
                     (40, 40, 40), filled=False)

        # Country name at bottom
        label = name
        label_y = FY + FLAG_H + 4
        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            total_w = len(label + "    ") * 4
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, label_y, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, label_y, label, Colors.WHITE)

        # Group overlay
        if self.overlay_timer > 0:
            _, gname = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, gname, c)

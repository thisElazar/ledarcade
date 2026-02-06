"""
Spectroscope - Emission Spectra
================================
Real element emission lines on black background.
Vertical colored lines at correct wavelength positions.

Controls:
  Up/Down    - Cycle element groups (ALL, NOBLE, ALKALI, etc.)
  Left/Right - Browse elements within group
  Space      - Toggle auto-cycle
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


def _wavelength_to_rgb(nm):
    """Convert visible wavelength (380-700nm) to RGB color."""
    if nm < 380 or nm > 700:
        return (0, 0, 0)

    if nm < 440:
        r = -(nm - 440) / (440 - 380)
        g = 0.0
        b = 1.0
    elif nm < 490:
        r = 0.0
        g = (nm - 440) / (490 - 440)
        b = 1.0
    elif nm < 510:
        r = 0.0
        g = 1.0
        b = -(nm - 510) / (510 - 490)
    elif nm < 580:
        r = (nm - 510) / (580 - 510)
        g = 1.0
        b = 0.0
    elif nm < 645:
        r = 1.0
        g = -(nm - 645) / (645 - 580)
        b = 0.0
    else:
        r = 1.0
        g = 0.0
        b = 0.0

    # Intensity falloff at edges
    if nm < 420:
        factor = 0.3 + 0.7 * (nm - 380) / 40
    elif nm > 680:
        factor = 0.3 + 0.7 * (700 - nm) / 20
    else:
        factor = 1.0

    return (int(r * factor * 255), int(g * factor * 255), int(b * factor * 255))


# Element spectral data: (symbol, name, group, [(wavelength_nm, intensity 0-1), ...])
ELEMENTS = [
    ('H', 'HYDROGEN', 'nonmetal', [
        (410.2, 0.3), (434.0, 0.5), (486.1, 0.8), (656.3, 1.0),
    ]),
    ('He', 'HELIUM', 'noble', [
        (388.9, 0.4), (447.1, 0.5), (471.3, 0.3), (492.2, 0.6),
        (501.6, 0.5), (587.6, 1.0), (667.8, 0.7), (706.5, 0.4),
    ]),
    ('Li', 'LITHIUM', 'alkali', [
        (391.5, 0.2), (413.3, 0.3), (460.3, 0.4), (497.2, 0.3), (670.8, 1.0),
    ]),
    ('Na', 'SODIUM', 'alkali', [
        (498.3, 0.2), (568.8, 0.3), (589.0, 1.0), (589.6, 0.95), (616.1, 0.2),
    ]),
    ('K', 'POTASSIUM', 'alkali', [
        (404.7, 0.5), (691.1, 0.3), (766.5, 0.9), (769.9, 1.0),
    ]),
    ('Ne', 'NEON', 'noble', [
        (540.1, 0.3), (585.2, 0.5), (588.2, 0.4), (603.0, 0.6),
        (607.4, 0.5), (616.4, 0.7), (621.7, 0.6), (626.6, 0.8),
        (633.4, 0.7), (638.3, 0.9), (640.2, 1.0), (650.7, 0.6),
        (659.9, 0.5), (692.9, 0.4),
    ]),
    ('Ar', 'ARGON', 'noble', [
        (394.7, 0.3), (404.4, 0.4), (415.9, 0.5), (419.1, 0.4),
        (420.1, 0.6), (425.9, 0.5), (427.2, 0.4), (430.0, 0.3),
        (696.5, 0.7), (706.7, 0.6), (714.7, 0.5),
    ]),
    ('Kr', 'KRYPTON', 'noble', [
        (427.4, 0.5), (431.9, 0.4), (436.3, 0.6), (437.6, 0.3),
        (445.4, 0.4), (450.2, 0.3), (557.0, 0.5), (587.1, 0.6),
    ]),
    ('Xe', 'XENON', 'noble', [
        (462.4, 0.6), (467.1, 0.4), (473.4, 0.5), (480.7, 0.7),
        (492.3, 0.4), (529.2, 0.5), (541.9, 0.3), (597.0, 0.4),
    ]),
    ('Hg', 'MERCURY', 'transition', [
        (404.7, 0.7), (435.8, 1.0), (491.6, 0.3), (546.1, 0.8),
        (577.0, 0.6), (579.1, 0.55), (615.0, 0.2), (690.7, 0.15),
    ]),
    ('Fe', 'IRON', 'transition', [
        (382.0, 0.4), (385.6, 0.3), (404.6, 0.5), (427.2, 0.6),
        (430.8, 0.5), (438.4, 0.7), (440.5, 0.6), (489.1, 0.3),
        (492.1, 0.4), (495.8, 0.35), (516.7, 0.3), (527.0, 0.25),
    ]),
    ('Cu', 'COPPER', 'transition', [
        (402.3, 0.3), (406.3, 0.2), (427.5, 0.4), (465.1, 0.3),
        (510.6, 0.7), (515.3, 0.6), (521.8, 1.0), (578.2, 0.4),
    ]),
    ('Ca', 'CALCIUM', 'alkaline', [
        (393.4, 0.8), (396.8, 0.7), (422.7, 0.9), (430.3, 0.4),
        (443.5, 0.3), (445.5, 0.35), (526.5, 0.2), (558.9, 0.15),
        (612.2, 0.3), (616.2, 0.5), (643.9, 0.2), (646.3, 0.3),
    ]),
    ('Sr', 'STRONTIUM', 'alkaline', [
        (407.8, 0.5), (421.6, 0.6), (460.7, 1.0), (481.2, 0.3),
        (496.2, 0.2), (550.4, 0.15), (640.8, 0.3), (687.8, 0.4),
    ]),
    ('Ba', 'BARIUM', 'alkaline', [
        (455.4, 0.7), (493.4, 0.8), (553.5, 1.0), (577.8, 0.4),
        (585.4, 0.3), (611.1, 0.2), (614.2, 0.25), (649.7, 0.35),
        (659.5, 0.3),
    ]),
    ('N', 'NITROGEN', 'nonmetal', [
        (391.4, 0.3), (395.6, 0.35), (399.5, 0.4), (404.1, 0.45),
        (444.7, 0.3), (460.1, 0.2), (463.1, 0.25), (500.5, 0.2),
        (567.0, 0.15), (575.3, 0.2), (648.3, 0.3),
    ]),
    ('O', 'OXYGEN', 'nonmetal', [
        (394.7, 0.3), (407.6, 0.2), (436.8, 0.25), (441.5, 0.3),
        (533.0, 0.2), (543.5, 0.15), (615.8, 0.5), (645.4, 0.3),
    ]),
    ('Cs', 'CAESIUM', 'alkali', [
        (455.5, 0.6), (459.3, 0.4), (535.1, 0.3), (566.5, 0.2),
        (601.1, 0.3), (621.3, 0.2), (672.3, 0.4), (697.3, 0.3),
    ]),
    ('Mg', 'MAGNESIUM', 'alkaline', [
        (383.2, 0.5), (383.8, 0.45), (470.3, 0.2), (516.7, 0.3),
        (517.3, 0.6), (518.4, 0.8),
    ]),
    ('Zn', 'ZINC', 'transition', [
        (468.0, 0.6), (472.2, 0.5), (481.1, 0.7), (518.2, 0.3),
        (530.9, 0.2), (589.4, 0.15), (636.2, 0.4),
    ]),
]

# Groups for cycling
GROUPS = [
    ('all', 'ALL', (255, 255, 255)),
    ('noble', 'NOBLE GASES', (180, 130, 255)),
    ('alkali', 'ALKALI', (255, 100, 80)),
    ('alkaline', 'ALKALINE', (255, 170, 50)),
    ('transition', 'TRANSITION', (255, 210, 100)),
    ('nonmetal', 'NONMETALS', (80, 160, 255)),
]


def _build_group_indices():
    """Build mapping from group key to element indices."""
    indices = {'all': list(range(len(ELEMENTS)))}
    for i, (sym, name, group, lines) in enumerate(ELEMENTS):
        indices.setdefault(group, []).append(i)
    return indices


# Wavelength range mapped to 64 pixels
WL_MIN = 380.0
WL_MAX = 700.0


class Spectroscope(Visual):
    name = "SPECTROSCOPE"
    description = "Element emission spectra"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.elem_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 6.0
        self.overlay_timer = 0.0
        self.label_timer = 0.0
        self.scroll_offset = 0.0

    def _current_elem_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_elem_index(self):
        elem_list = self._current_elem_list()
        if not elem_list:
            return 0
        return elem_list[self.elem_pos % len(elem_list)]

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.elem_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.elem_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.left_pressed:
            elem_list = self._current_elem_list()
            if elem_list:
                self.elem_pos = (self.elem_pos - 1) % len(elem_list)
            self.cycle_timer = 0.0
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.right_pressed:
            elem_list = self._current_elem_list()
            if elem_list:
                self.elem_pos = (self.elem_pos + 1) % len(elem_list)
            self.cycle_timer = 0.0
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                elem_list = self._current_elem_list()
                if elem_list:
                    self.elem_pos = (self.elem_pos + 1) % len(elem_list)
                self.label_timer = 0.0
                self.scroll_offset = 0.0

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        idx = self._current_elem_index()
        sym, name, group, lines = ELEMENTS[idx]

        # Draw dim wavelength scale reference at bottom
        for x in range(GRID_SIZE):
            nm = WL_MIN + (WL_MAX - WL_MIN) * x / (GRID_SIZE - 1)
            rgb = _wavelength_to_rgb(nm)
            dim = (rgb[0] // 12, rgb[1] // 12, rgb[2] // 12)
            d.set_pixel(x, 53, dim)

        # Draw emission lines
        pulse = 0.85 + 0.15 * math.sin(self.time * 2.0)
        for wl, intensity in lines:
            if wl < WL_MIN or wl > WL_MAX:
                continue

            x = int((wl - WL_MIN) / (WL_MAX - WL_MIN) * (GRID_SIZE - 1))
            x = max(0, min(GRID_SIZE - 1, x))

            rgb = _wavelength_to_rgb(wl)
            bright = intensity * pulse
            color = (
                min(255, int(rgb[0] * bright)),
                min(255, int(rgb[1] * bright)),
                min(255, int(rgb[2] * bright)),
            )

            # Draw vertical line
            line_height = int(4 + intensity * 44)
            y_start = 52 - line_height
            for y in range(y_start, 53):
                # Slight fade at top
                frac = (y - y_start) / max(1, line_height)
                fade = 0.5 + 0.5 * frac
                c = (int(color[0] * fade), int(color[1] * fade), int(color[2] * fade))
                d.set_pixel(x, y, c)

            # Glow: adjacent pixels at half brightness
            glow = (color[0] // 3, color[1] // 3, color[2] // 3)
            for y in range(y_start + 2, 53):
                if x > 0:
                    d.set_pixel(x - 1, y, glow)
                if x < GRID_SIZE - 1:
                    d.set_pixel(x + 1, y, glow)

        # Bottom label: 3 phases
        phase = int(self.label_timer / 4) % 3
        if phase == 0:
            label = name
        elif phase == 1:
            label = f"{sym} SPECTRUM"
        else:
            label = "EMISSION LINES"

        # Reset scroll on phase change
        if not hasattr(self, '_last_phase') or self._last_phase != phase:
            self._last_phase = phase
            self.scroll_offset = 0

        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            char_w = 4
            total_w = len(label + "    ") * char_w
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, 58, label, Colors.WHITE)

        # Group overlay
        if self.overlay_timer > 0:
            _, gname, gcolor = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(gcolor[0] * alpha), int(gcolor[1] * alpha), int(gcolor[2] * alpha))
            d.draw_text_small(2, 2, gname, oc)

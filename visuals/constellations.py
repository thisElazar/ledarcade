"""
CONSTELLATIONS - Night Sky Star Map
====================================
28 constellations with real star positions (Hipparcos/SIMBAD J2000)
projected onto a 50x50 working area. Grouped by zodiac and season.
Stars fade in, constellation lines draw, then hold.
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Constellation data — real star positions projected to 50x50 grid
# stars: [(x, y, magnitude)] mag 1=Vmag<2, 2=Vmag 2-3.5, 3=Vmag>3.5
# lines: IAU standard stick figures (Sky & Telescope / Alan MacRobert)
# Offset by (OX, OY) = (7, 4) when drawn to center on 64x64
# ---------------------------------------------------------------------------
CONSTELLATIONS = [
    # ==================== ZODIAC (12) ====================
    {'name': 'ARIES', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'HAMAL',
     'stars': [(36, 24, 2), (46, 33, 2), (47, 39, 3), (3, 11, 3)],
     'lines': [(0, 1), (1, 2), (0, 3)]},
    {'name': 'TAURUS', 'season': 'WINTER', 'zodiac': True,
     'bright_star': 'ALDEBARAN',
     'stars': [(28, 32, 1), (8, 11, 1), (47, 19, 2), (3, 24, 2),
               (42, 39, 2), (31, 27, 3), (31, 33, 2), (34, 33, 3),
               (33, 30, 3)],
     'lines': [(3, 7), (7, 6), (7, 5), (6, 4), (4, 1),
               (5, 0), (0, 2)]},
    {'name': 'GEMINI', 'season': 'WINTER', 'zodiac': True,
     'bright_star': 'POLLUX',
     'stars': [(3, 13, 1), (8, 5, 1), (36, 38, 1), (43, 25, 2),
               (33, 19, 2), (47, 25, 2), (15, 26, 3), (4, 21, 3),
               (32, 45, 2)],
     'lines': [(0, 4), (4, 3), (3, 2), (2, 8), (1, 7),
               (7, 6), (5, 6), (6, 4)]},
    {'name': 'CANCER', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'ALTARF',
     'stars': [(36, 47, 3), (14, 41, 3), (22, 19, 3), (21, 27, 3),
               (20, 3, 3)],
     'lines': [(0, 1), (1, 2), (1, 3), (3, 4)]},
    {'name': 'LEO', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'REGULUS',
     'stars': [(39, 36, 1), (3, 32, 2), (35, 24, 2), (15, 23, 2),
               (47, 18, 2), (39, 28, 3), (15, 30, 2), (45, 14, 3),
               (36, 18, 2)],
     'lines': [(0, 5), (5, 2), (5, 4), (5, 6), (4, 8),
               (8, 7), (7, 2), (2, 3), (3, 1), (3, 6), (6, 1)]},
    {'name': 'VIRGO', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'SPICA',
     'stars': [(23, 36, 1), (34, 26, 2), (29, 14, 2), (40, 26, 3),
               (20, 26, 2), (30, 21, 2), (47, 23, 3), (27, 31, 3),
               (14, 23, 3), (3, 31, 3)],
     'lines': [(5, 6), (6, 2), (2, 3), (3, 1), (2, 0),
               (2, 4), (4, 7), (7, 8), (4, 9)]},
    {'name': 'LIBRA', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'ZUBENESCHAMALI',
     'stars': [(42, 19, 2), (28, 3, 2), (35, 40, 2), (17, 47, 3),
               (18, 16, 3), (8, 20, 3)],
     'lines': [(0, 1), (1, 2), (1, 4), (0, 4), (4, 3), (3, 5)]},
    {'name': 'SCORPIUS', 'season': 'SUMMER', 'zodiac': True,
     'bright_star': 'ANTARES',
     'stars': [(35, 15, 1), (9, 35, 1), (7, 47, 1), (46, 8, 2),
               (44, 3, 2), (26, 30, 2), (5, 39, 2), (47, 15, 2),
               (38, 14, 2), (32, 19, 2), (17, 47, 2), (26, 37, 2),
               (25, 45, 3), (3, 41, 2), (10, 36, 2), (3, 35, 2)],
     'lines': [(3, 4), (4, 9), (4, 5), (3, 15), (5, 0), (0, 8),
               (8, 7), (7, 11), (11, 12), (12, 13), (13, 2),
               (2, 10), (10, 6), (6, 14), (14, 1)]},
    {'name': 'SAGITTARIUS', 'season': 'SUMMER', 'zodiac': True,
     'bright_star': 'KAUS AUSTRALIS',
     'stars': [(34, 46, 1), (13, 21, 2), (8, 32, 2), (37, 32, 2),
               (42, 18, 2), (47, 33, 2), (20, 23, 2), (5, 25, 2),
               (3, 4, 2)],
     'lines': [(4, 3), (4, 0), (3, 0), (7, 0), (3, 5),
               (5, 1), (5, 2), (0, 2), (1, 6), (2, 6), (8, 3)]},
    {'name': 'CAPRICORNUS', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'DENEB ALGEDI',
     'stars': [(3, 17, 2), (45, 15, 2), (47, 10, 3), (6, 19, 3),
               (13, 31, 3), (23, 20, 3), (30, 40, 3), (33, 37, 3),
               (15, 19, 3)],
     'lines': [(3, 0), (3, 4), (0, 8), (8, 7), (7, 5),
               (4, 2), (5, 6), (6, 1), (2, 1)]},
    {'name': 'AQUARIUS', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'SADALSUUD',
     'stars': [(33, 19, 2), (23, 12, 2), (8, 32, 2), (8, 21, 3),
               (14, 12, 3), (47, 24, 3), (18, 13, 3), (16, 12, 3),
               (19, 21, 3), (23, 29, 3), (3, 38, 3)],
     'lines': [(4, 0), (0, 1), (1, 7), (1, 6), (7, 5),
               (5, 6), (1, 3), (3, 8), (8, 9), (9, 10), (9, 2)]},
    {'name': 'PISCES', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'ALPHERG',
     'stars': [(11, 25, 3), (47, 39, 3), (36, 35, 3), (41, 36, 3),
               (44, 35, 3), (3, 39, 3), (19, 34, 3), (23, 34, 3),
               (9, 36, 3), (12, 36, 3), (16, 34, 3), (16, 9, 3),
               (14, 12, 3), (16, 15, 3), (17, 19, 3), (40, 40, 3),
               (44, 41, 3)],
     'lines': [(0, 13), (13, 14), (14, 0), (0, 12), (12, 1),
               (1, 11), (11, 2), (2, 3), (3, 4), (4, 5),
               (5, 6), (6, 9), (9, 8), (8, 10), (10, 7), (7, 6)]},

    # ==================== NON-ZODIAC (16) ====================
    {'name': 'ORION', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'BETELGEUSE',
     'stars': [(14, 9, 1), (36, 44, 1), (30, 11, 1), (24, 28, 1),
               (22, 30, 1), (18, 47, 2), (27, 26, 2), (25, 3, 2),
               (31, 31, 2), (25, 39, 2)],
     'lines': [(7, 0), (7, 2), (0, 2), (0, 4), (2, 6),
               (6, 3), (3, 4), (6, 5), (5, 1), (4, 8), (4, 9)]},
    {'name': 'URSA MAJOR', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'ALIOTH',
     'stars': [(46, 13, 1), (47, 23, 2), (33, 28, 2), (27, 22, 2),
               (17, 24, 1), (9, 26, 2), (3, 37, 1)],
     'lines': [(0, 1), (1, 2), (2, 3), (3, 0), (3, 4),
               (4, 5), (5, 6)]},
    {'name': 'URSA MINOR', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'POLARIS',
     'stars': [(3, 12, 1), (47, 35, 2), (45, 38, 2), (40, 23, 3),
               (37, 16, 3), (44, 29, 3), (42, 32, 3)],
     'lines': [(0, 4), (4, 3), (3, 5), (5, 6), (6, 2), (2, 1), (1, 5)]},
    {'name': 'CASSIOPEIA', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'SCHEDAR',
     'stars': [(34, 37, 2), (47, 28, 2), (27, 23, 2), (15, 25, 2),
               (3, 13, 2)],
     'lines': [(1, 0), (0, 2), (2, 3), (3, 4)]},
    {'name': 'CYGNUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'DENEB',
     'stars': [(8, 3, 1), (18, 16, 2), (6, 32, 2), (44, 47, 2),
               (37, 3, 2)],
     'lines': [(0, 1), (1, 2), (1, 3), (1, 4)]},
    {'name': 'LYRA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'VEGA',
     'stars': [(41, 3, 1), (22, 42, 3), (9, 47, 2), (15, 17, 3),
               (30, 12, 3)],
     'lines': [(0, 4), (0, 3), (4, 3), (3, 1), (3, 2), (1, 2)]},
    {'name': 'AQUILA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ALTAIR',
     'stars': [(18, 15, 1), (20, 11, 2), (15, 21, 3), (6, 37, 2),
               (33, 28, 2), (44, 47, 2), (44, 3, 2), (17, 33, 3)],
     'lines': [(5, 4), (4, 6), (4, 2), (6, 7), (6, 2),
               (2, 1), (2, 3), (1, 0)]},
    {'name': 'CANIS MAJOR', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'SIRIUS',
     'stars': [(30, 5, 1), (21, 42, 1), (14, 34, 1), (45, 9, 1),
               (3, 43, 2), (47, 45, 2), (18, 26, 2)],
     'lines': [(3, 0), (0, 2), (2, 1), (2, 4), (0, 6),
               (6, 5), (6, 1)]},
    {'name': 'PEGASUS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'ENIF',
     'stars': [(23, 29, 2), (24, 13, 2), (3, 29, 2), (47, 35, 2),
               (30, 34, 2), (30, 10, 2), (39, 40, 3)],
     'lines': [(0, 1), (0, 2), (3, 6), (6, 0), (5, 4), (4, 1)]},
    {'name': 'ANDROMEDA', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'ALPHERATZ',
     'stars': [(47, 44, 2), (24, 31, 2), (3, 18, 2), (35, 41, 2),
               (13, 6, 3), (29, 26, 3), (31, 21, 3)],
     'lines': [(0, 3), (3, 1), (1, 2), (1, 5), (5, 6), (6, 4)]},
    {'name': 'PERSEUS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'MIRFAK',
     'stars': [(25, 14, 1), (30, 30, 2), (15, 47, 2), (14, 32, 2),
               (31, 7, 2), (19, 18, 2), (31, 34, 2), (36, 3, 3),
               (30, 23, 3)],
     'lines': [(5, 2), (2, 3), (3, 0), (0, 4), (4, 7),
               (7, 8), (8, 0), (8, 1), (1, 6), (1, 2)]},
    {'name': 'DRACO', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ELTANIN',
     'stars': [(13, 33, 2), (15, 32, 2), (33, 23, 3), (21, 25, 2),
               (17, 22, 2), (6, 21, 2), (13, 29, 3), (26, 27, 2),
               (11, 17, 3), (3, 19, 3), (42, 19, 3), (47, 20, 3)],
     'lines': [(10, 11), (11, 5), (5, 9), (9, 4), (4, 3), (3, 2),
               (2, 7), (7, 8), (0, 1), (0, 6), (1, 6), (6, 7)]},
    {'name': 'CORONA BOREALIS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ALPHECCA',
     'stars': [(38, 37, 2), (47, 23, 3), (27, 39, 3), (18, 41, 3),
               (8, 36, 3), (40, 9, 3), (3, 18, 3)],
     'lines': [(5, 1), (1, 0), (0, 2), (2, 3), (3, 4), (4, 6)]},
    {'name': 'CORVUS', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'GIENAH',
     'stars': [(32, 8, 2), (9, 40, 2), (14, 3, 2), (39, 36, 2),
               (41, 47, 3)],
     'lines': [(0, 1), (0, 2), (2, 3), (1, 3), (2, 4)]},
    {'name': 'CRUX', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'ACRUX',
     'stars': [(29, 47, 1), (10, 22, 1), (25, 3, 1), (40, 15, 2),
               (35, 27, 3)],
     'lines': [(0, 2), (1, 3)]},
    {'name': 'CENTAURUS', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'RIGIL KENTAURUS',
     'stars': [(3, 47, 1), (13, 46, 1), (13, 3, 2), (37, 26, 2),
               (20, 34, 2), (4, 14, 2), (47, 29, 2), (16, 23, 2),
               (26, 4, 2)],
     'lines': [(0, 1), (1, 5), (5, 4), (5, 6), (6, 4),
               (4, 7), (2, 4), (3, 7), (8, 6)]},
]

# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------
GROUPS = [
    ('ALL',    'ALL'),
    ('ZODIAC', 'ZODIAC'),
    ('WINTER', 'WINTER'),
    ('SPRING', 'SPRING'),
    ('SUMMER', 'SUMMER'),
    ('AUTUMN', 'AUTUMN'),
]

BG_COLOR = (3, 3, 12)

# Star size by magnitude
MAG_PATTERNS = {
    1: [(-1, 0), (1, 0), (0, -1), (0, 1), (0, 0)],  # 3px cross
    2: [(0, 0), (1, 0), (0, 1)],  # 2px
    3: [(0, 0)],  # 1px dot
}

# Animation timing
FADE_IN_T = 1.5
LINE_DRAW_T = 2.5
HOLD_T = 4.0
TOTAL_T = FADE_IN_T + LINE_DRAW_T + HOLD_T

# Offset to center 50x50 working area in 64x64
OX, OY = 7, 4


def _build_group_indices():
    indices = {'ALL': list(range(len(CONSTELLATIONS)))}
    indices['ZODIAC'] = [i for i, c in enumerate(CONSTELLATIONS) if c['zodiac']]
    for season in ['WINTER', 'SPRING', 'SUMMER', 'AUTUMN']:
        indices[season] = [i for i, c in enumerate(CONSTELLATIONS)
                           if c['season'] == season]
    return indices


class Constellations(Visual):
    name = "CONSTELLATIONS"
    description = "Night sky star map"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.const_pos = 0
        self.auto_cycle = True
        self.anim_timer = 0.0
        self.overlay_timer = 0.0
        self.label_timer = 0.0
        self.scroll_offset = 0.0
        # Background field stars
        self.field_stars = [(random.randint(0, 63), random.randint(0, 63),
                             random.uniform(0, math.pi * 2),
                             random.uniform(0.2, 0.7))
                            for _ in range(30)]

    def _current_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_const(self):
        lst = self._current_list()
        if not lst:
            return CONSTELLATIONS[0]
        return CONSTELLATIONS[lst[self.const_pos % len(lst)]]

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.const_pos = 0
            self.anim_timer = 0.0
            self.overlay_timer = 2.5
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.const_pos = 0
            self.anim_timer = 0.0
            self.overlay_timer = 2.5
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.left_pressed:
            lst = self._current_list()
            if lst:
                self.const_pos = (self.const_pos - 1) % len(lst)
            self.anim_timer = 0.0
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.right_pressed:
            lst = self._current_list()
            if lst:
                self.const_pos = (self.const_pos + 1) % len(lst)
            self.anim_timer = 0.0
            self.label_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.label_timer += dt
        self.scroll_offset += dt * 20
        self.anim_timer += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle and self.anim_timer >= TOTAL_T:
            self.anim_timer = 0.0
            lst = self._current_list()
            if lst:
                self.const_pos = (self.const_pos + 1) % len(lst)
            self.label_timer = 0.0
            self.scroll_offset = 0.0

    def draw(self):
        d = self.display
        d.clear(BG_COLOR)

        const = self._current_const()
        stars = const['stars']
        lines = const['lines']
        t = self.anim_timer

        # --- Field stars ---
        for fx, fy, phase, brightness in self.field_stars:
            # Skip if overlapping constellation area
            twinkle = 0.5 + 0.5 * math.sin(self.time * 1.2 + phase)
            v = int(30 * brightness * twinkle)
            d.set_pixel(fx, fy, (v, v, min(255, int(v * 1.3))))

        # --- Star fade-in ---
        star_alpha = min(1.0, t / FADE_IN_T) if t < FADE_IN_T else 1.0

        for i, (sx, sy, mag) in enumerate(stars):
            px, py = sx + OX, sy + OY
            base_v = int(star_alpha * 255)
            if mag == 1:
                v = base_v
            elif mag == 2:
                v = int(base_v * 0.7)
            else:
                v = int(base_v * 0.4)

            color = (v, v, min(255, int(v * 1.1)))
            pattern = MAG_PATTERNS.get(mag, [(0, 0)])
            for dx, dy in pattern:
                d.set_pixel(px + dx, py + dy, color)

        # --- Line draw animation ---
        if t > FADE_IN_T and lines:
            line_t = t - FADE_IN_T
            total_lines = len(lines)
            time_per_line = LINE_DRAW_T / total_lines
            lines_drawn = min(total_lines, line_t / time_per_line)

            for li in range(int(lines_drawn)):
                si, ei = lines[li]
                sx1, sy1 = stars[si][0] + OX, stars[si][1] + OY
                sx2, sy2 = stars[ei][0] + OX, stars[ei][1] + OY
                line_color = (60, 60, 100)
                d.draw_line(sx1, sy1, sx2, sy2, line_color)

            # Partially draw current line
            frac = lines_drawn - int(lines_drawn)
            if int(lines_drawn) < total_lines and frac > 0:
                si, ei = lines[int(lines_drawn)]
                sx1, sy1 = stars[si][0] + OX, stars[si][1] + OY
                sx2, sy2 = stars[ei][0] + OX, stars[ei][1] + OY
                mx = int(sx1 + (sx2 - sx1) * frac)
                my = int(sy1 + (sy2 - sy1) * frac)
                d.draw_line(sx1, sy1, mx, my, (60, 60, 100))

        # --- Bottom label (2-phase: name / bright star) ---
        phase = int(self.label_timer / 4) % 2
        if phase == 0:
            label = const['name']
        else:
            label = const['bright_star']

        if not hasattr(self, '_last_lbl_phase') or self._last_lbl_phase != phase:
            self._last_lbl_phase = phase
            self.scroll_offset = 0

        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            total_w = len(label + "    ") * 4
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, 58, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, 58, label, Colors.WHITE)

        # --- Group overlay ---
        if self.overlay_timer > 0:
            _, gname = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, gname, c)

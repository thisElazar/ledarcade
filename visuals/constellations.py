"""
CONSTELLATIONS - Night Sky Star Map
====================================
28 constellations with real star positions from Hipparcos catalog (VizieR I/239),
gnomonic-projected onto a 50x50 working area. Constellation lines from Stellarium
modern_st sky culture. Grouped by zodiac and season.
Stars fade in, constellation lines draw, then hold.

Regenerate data: python tools/build_constellations.py > /tmp/constellations_data.py
"""

import math
import random
from . import Visual, Display, Colors

# ---------------------------------------------------------------------------
# Constellation data — Hipparcos catalog + Stellarium modern_st polylines
# stars: [(x, y, magnitude)] mag 1=Vmag<1.5, 2=Vmag 1.5-3.5, 3=Vmag>3.5
# lines: Stellarium modern_st stick figures
# Offset by (OX, OY) = (7, 4) when drawn to center on 64x64
# ---------------------------------------------------------------------------
CONSTELLATIONS = [
    # ==================== ZODIAC (12) ====================
    {'name': 'ARIES', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'HAMAL',
     'stars': [(36, 25, 2), (47, 34, 2), (2, 10, 3), (48, 40, 3)],
     'lines': [(3, 1), (1, 0), (0, 2)]},
    {'name': 'TAURUS', 'season': 'WINTER', 'zodiac': True,
     'bright_star': 'ALDEBARAN',
     'stars': [
              (23, 23, 1), (7, 4, 2), (2, 15, 2), (26, 24, 2), (35, 29, 2),
              (26, 19, 3), (48, 33, 3), (29, 24, 3), (47, 32, 3), (28, 22, 3),
              (34, 38, 3), (44, 46, 3)
     ],
     'lines': [
              (2, 0), (0, 3), (3, 7), (7, 9), (9, 5), (5, 1), (8, 10), (6, 11),
              (7, 4), (4, 8)
     ]},
    {'name': 'GEMINI', 'season': 'WINTER', 'zodiac': True,
     'bright_star': 'POLLUX',
     'stars': [
              (2, 15, 1), (7, 8, 2), (33, 39, 2), (39, 26, 2), (29, 22, 2),
              (43, 26, 2), (29, 46, 2), (13, 28, 3), (2, 22, 3), (14, 39, 3),
              (25, 4, 3), (11, 16, 3), (20, 31, 3), (6, 18, 3), (37, 31, 3),
              (48, 24, 3), (17, 11, 3)
     ],
     'lines': [
              (6, 9), (9, 7), (7, 12), (12, 2), (7, 13), (13, 8), (13, 0),
              (13, 11), (11, 16), (16, 1), (16, 10), (16, 4), (4, 14), (4, 3),
              (3, 5), (5, 15)
     ]},
    {'name': 'CANCER', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'ALTARF',
     'stars': [
              (37, 48, 3), (21, 27, 3), (20, 2, 3), (13, 42, 3), (22, 19, 3)
     ],
     'lines': [(3, 1), (1, 0), (1, 4), (4, 2)]},
    {'name': 'LEO', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'REGULUS',
     'stars': [
              (35, 31, 1), (31, 21, 2), (2, 27, 2), (14, 19, 2), (42, 15, 2),
              (14, 26, 2), (32, 16, 2), (35, 25, 2), (39, 12, 3), (10, 33, 3),
              (11, 39, 3), (46, 16, 3), (48, 11, 3)
     ],
     'lines': [
              (0, 7), (7, 1), (1, 6), (6, 8), (8, 4), (1, 3), (3, 2), (2, 5),
              (5, 3), (5, 7), (8, 12), (12, 11), (11, 4), (4, 7), (5, 9),
              (9, 10)
     ]},
    {'name': 'VIRGO', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'SPICA',
     'stars': [
              (23, 36, 1), (34, 26, 2), (29, 14, 2), (21, 25, 2), (30, 22, 2),
              (47, 23, 3), (2, 23, 3), (3, 31, 3), (39, 26, 3), (48, 18, 3),
              (10, 31, 3), (43, 16, 3), (14, 23, 3), (27, 30, 3)
     ],
     'lines': [
              (8, 11), (11, 9), (9, 5), (5, 8), (8, 1), (1, 4), (4, 2),
              (1, 13), (13, 0), (1, 3), (3, 12), (12, 6), (3, 10), (10, 7)
     ]},
    {'name': 'LIBRA', 'season': 'SPRING', 'zodiac': True,
     'bright_star': 'ZUBENESCHAMALI',
     'stars': [
              (23, 2, 2), (37, 17, 2), (30, 38, 2), (13, 44, 3), (13, 48, 3),
              (13, 14, 3)
     ],
     'lines': [(1, 0), (1, 2), (0, 5), (5, 1), (5, 3), (3, 4)]},
    {'name': 'SCORPIUS', 'season': 'SUMMER', 'zodiac': True,
     'bright_star': 'ANTARES',
     'stars': [
              (34, 15, 1), (9, 36, 2), (9, 48, 2), (48, 9, 2), (25, 30, 2),
              (6, 41, 2), (46, 3, 2), (10, 37, 2), (31, 19, 2), (47, 16, 2),
              (38, 14, 2), (4, 43, 2), (25, 37, 2), (2, 37, 2), (18, 47, 2),
              (24, 46, 3), (48, 22, 3), (43, 2, 3)
     ],
     'lines': [
              (6, 3), (3, 9), (3, 10), (10, 0), (0, 8), (8, 4), (4, 12),
              (12, 15), (15, 14), (14, 2), (2, 11), (11, 5), (5, 7), (7, 1),
              (1, 13), (6, 17), (9, 16)
     ]},
    {'name': 'SAGITTARIUS', 'season': 'SUMMER', 'zodiac': True,
     'bright_star': 'KAUS AUSTRALIS',
     'stars': [
              (36, 42, 2), (20, 22, 2), (16, 31, 2), (38, 31, 2), (35, 20, 2),
              (11, 10, 2), (46, 33, 2), (39, 48, 2), (25, 24, 2), (14, 26, 2),
              (18, 10, 3), (14, 11, 3), (43, 10, 3), (4, 2, 3)
     ],
     'lines': [
              (0, 6), (6, 3), (3, 0), (3, 4), (4, 8), (8, 3), (8, 1), (1, 9),
              (9, 2), (2, 8), (2, 0), (0, 7), (4, 12), (13, 5), (5, 11),
              (11, 10), (10, 5)
     ]},
    {'name': 'CAPRICORNUS', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'DENEB ALGEDI',
     'stars': [
              (2, 18, 2), (46, 15, 2), (48, 10, 3), (6, 19, 3), (13, 30, 3),
              (23, 19, 3), (30, 40, 3), (32, 37, 3), (7, 24, 3)
     ],
     'lines': [
              (2, 1), (1, 7), (7, 6), (6, 4), (4, 8), (8, 0), (0, 3), (3, 5),
              (5, 2)
     ]},
    {'name': 'AQUARIUS', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'SADALSUUD',
     'stars': [
              (34, 20, 2), (24, 14, 2), (10, 32, 2), (17, 13, 3), (6, 38, 3),
              (10, 22, 3), (48, 25, 3), (19, 15, 3), (2, 37, 3), (15, 13, 3),
              (11, 29, 3), (21, 22, 3), (4, 20, 3), (23, 29, 3), (3, 24, 3),
              (18, 12, 3)
     ],
     'lines': [
              (6, 0), (0, 1), (1, 7), (7, 3), (3, 9), (3, 15), (15, 1),
              (13, 0), (1, 11), (11, 5), (5, 12), (12, 14), (14, 8), (14, 4),
              (14, 2), (2, 10), (10, 5)
     ]},
    {'name': 'PISCES', 'season': 'AUTUMN', 'zodiac': True,
     'bright_star': 'ALPHERG',
     'stars': [
              (11, 25, 3), (48, 38, 3), (2, 39, 3), (36, 35, 3), (41, 36, 3),
              (7, 32, 3), (19, 34, 3), (45, 35, 3), (23, 34, 3), (8, 36, 3),
              (41, 40, 3), (17, 9, 3), (16, 16, 3), (15, 12, 3), (45, 41, 3)
     ],
     'lines': [
              (12, 13), (13, 11), (11, 12), (12, 0), (0, 5), (5, 2), (2, 9),
              (9, 6), (6, 8), (8, 3), (3, 4), (4, 7), (7, 1), (1, 14),
              (14, 10), (10, 4)
     ]},

    # ==================== NON-ZODIAC (16) ====================
    {'name': 'ORION', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'RIGEL',
     'stars': [
              (31, 46, 1), (16, 22, 1), (27, 23, 2), (23, 35, 2), (21, 36, 2),
              (18, 48, 2), (24, 33, 2), (40, 22, 2), (27, 37, 2), (23, 18, 2),
              (40, 24, 3), (39, 29, 3), (38, 12, 3), (13, 18, 3), (40, 19, 3),
              (16, 2, 3), (11, 10, 3), (10, 11, 3), (37, 30, 3), (13, 2, 3),
              (38, 18, 3), (35, 10, 3)
     ],
     'lines': [
              (1, 4), (4, 5), (4, 3), (3, 6), (6, 2), (6, 8), (8, 0), (1, 2),
              (2, 9), (9, 1), (21, 12), (12, 20), (20, 14), (14, 7), (7, 2),
              (7, 10), (10, 11), (11, 18), (1, 13), (13, 16), (17, 19),
              (19, 15), (15, 16)
     ]},
    {'name': 'URSA MAJOR', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'ALIOTH',
     'stars': [
              (13, 15, 2), (28, 13, 2), (2, 17, 2), (9, 14, 2), (28, 18, 2),
              (21, 20, 2), (27, 29, 2), (35, 32, 2), (48, 22, 2), (41, 21, 2),
              (19, 16, 2), (46, 9, 2), (36, 31, 2), (24, 41, 2), (48, 23, 3),
              (38, 10, 3), (21, 26, 3), (37, 15, 3)
     ],
     'lines': [
              (5, 16), (16, 6), (6, 7), (7, 12), (16, 13), (10, 1), (1, 4),
              (4, 5), (5, 10), (10, 0), (0, 3), (3, 2), (1, 15), (15, 17),
              (15, 11), (11, 17), (17, 4), (17, 9), (9, 14), (14, 8)
     ]},
    {'name': 'URSA MINOR', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'POLARIS',
     'stars': [
              (22, 2, 2), (32, 41, 2), (28, 48, 2), (18, 23, 3), (23, 34, 3),
              (19, 11, 3), (18, 38, 3)
     ],
     'lines': [(0, 5), (5, 3), (3, 4), (4, 6), (6, 2), (2, 1), (1, 4)]},
    {'name': 'CASSIOPEIA', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'SCHEDAR',
     'stars': [
              (26, 24, 2), (34, 39, 2), (48, 28, 2), (12, 25, 2), (2, 11, 2)
     ],
     'lines': [(2, 1), (1, 0), (0, 3), (3, 4)]},
    {'name': 'CYGNUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'DENEB',
     'stars': [
              (19, 18, 1), (25, 27, 2), (16, 38, 2), (37, 18, 2), (45, 48, 2),
              (5, 43, 2), (40, 6, 3), (43, 2, 3), (13, 24, 3), (27, 14, 3)
     ],
     'lines': [
              (0, 1), (1, 2), (1, 4), (1, 3), (3, 6), (6, 7), (6, 9), (9, 0),
              (0, 8), (8, 5), (5, 2)
     ]},
    {'name': 'LYRA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'VEGA',
     'stars': [
              (40, 8, 1), (10, 48, 2), (23, 44, 3), (17, 20, 3), (30, 16, 3),
              (30, 2, 3)
     ],
     'lines': [(0, 5), (5, 4), (4, 0), (4, 3), (3, 1), (1, 2), (2, 4)]},
    {'name': 'AQUILA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ALTAIR',
     'stars': [
              (17, 16, 1), (19, 12, 2), (41, 5, 2), (6, 37, 2), (31, 28, 2),
              (41, 46, 2), (15, 21, 3), (16, 33, 3), (44, 48, 3), (44, 2, 3),
              (25, 38, 3)
     ],
     'lines': [
              (6, 0), (0, 1), (1, 4), (4, 5), (4, 2), (4, 7), (7, 3), (9, 2),
              (5, 8), (3, 10), (10, 5), (5, 2)
     ]},
    {'name': 'CANIS MAJOR', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'SIRIUS',
     'stars': [
              (29, 14, 1), (21, 47, 2), (15, 40, 2), (43, 18, 2), (7, 48, 2),
              (24, 34, 3), (35, 21, 3), (24, 2, 3), (18, 12, 3), (23, 15, 3)
     ],
     'lines': [
              (3, 0), (0, 2), (2, 1), (2, 4), (3, 6), (6, 5), (5, 1), (0, 9),
              (9, 8), (8, 7), (7, 9)
     ]},
    {'name': 'PEGASUS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'ENIF',
     'stars': [
              (6, 11, 2), (48, 37, 2), (24, 15, 2), (23, 30, 2), (2, 29, 2),
              (30, 12, 2), (30, 36, 2), (28, 19, 3), (40, 42, 3), (40, 18, 3),
              (29, 20, 3), (46, 17, 3), (38, 8, 3)
     ],
     'lines': [
              (12, 5), (5, 2), (2, 7), (7, 10), (10, 9), (9, 11), (0, 2),
              (2, 3), (3, 4), (4, 0), (1, 8), (8, 6), (6, 3)
     ]},
    {'name': 'ANDROMEDA', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'ALPHERATZ',
     'stars': [
              (32, 35, 2), (15, 26, 2), (2, 14, 2), (23, 33, 2), (10, 7, 3),
              (48, 14, 3), (38, 10, 3), (19, 22, 3), (21, 42, 3), (38, 13, 3),
              (16, 10, 3), (38, 15, 3), (24, 29, 3), (23, 35, 3), (17, 43, 3),
              (21, 19, 3)
     ],
     'lines': [
              (0, 3), (3, 1), (1, 2), (5, 11), (11, 9), (9, 6), (11, 12),
              (12, 3), (12, 1), (1, 7), (7, 15), (15, 10), (10, 4), (3, 13),
              (13, 8), (8, 14)
     ]},
    {'name': 'PERSEUS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'MIRFAK',
     'stars': [
              (18, 14, 2), (24, 31, 2), (6, 48, 2), (6, 32, 2), (23, 7, 2),
              (12, 18, 2), (25, 34, 2), (27, 2, 3), (23, 23, 3), (10, 47, 3),
              (26, 8, 3), (4, 17, 3), (5, 40, 3), (48, 7, 3), (23, 15, 3),
              (30, 14, 3), (2, 16, 3), (5, 13, 3), (2, 12, 3)
     ],
     'lines': [
              (9, 2), (2, 12), (12, 3), (3, 5), (5, 0), (0, 4), (4, 7),
              (7, 10), (10, 4), (10, 14), (14, 0), (14, 8), (8, 1), (1, 3),
              (1, 6), (5, 11), (11, 16), (16, 18), (18, 17), (14, 15),
              (15, 13)
     ]},
    {'name': 'DRACO', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ELTANIN',
     'stars': [
              (6, 47, 2), (24, 35, 2), (12, 46, 2), (3, 23, 2), (17, 30, 2),
              (33, 36, 2), (11, 19, 3), (41, 24, 3), (9, 40, 3), (48, 3, 3),
              (2, 17, 3), (44, 11, 3), (28, 38, 3), (11, 21, 3), (12, 43, 3)
     ],
     'lines': [
              (9, 11), (11, 7), (7, 5), (5, 12), (12, 1), (1, 4), (4, 13),
              (13, 6), (13, 3), (3, 10), (3, 8), (8, 14), (14, 2), (2, 0),
              (0, 8)
     ]},
    {'name': 'CORONA BOREALIS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ALPHECCA',
     'stars': [
              (39, 38, 2), (48, 22, 3), (28, 40, 3), (7, 36, 3), (41, 8, 3),
              (18, 42, 3), (2, 18, 3)
     ],
     'lines': [(4, 1), (1, 0), (0, 2), (2, 5), (5, 3), (3, 6)]},
    {'name': 'CORVUS', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'GIENAH',
     'stars': [
              (32, 8, 2), (8, 41, 2), (14, 2, 2), (40, 36, 2), (42, 48, 3)
     ],
     'lines': [(2, 0), (0, 3), (3, 1), (1, 2), (3, 4)]},
    {'name': 'CRUX', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'ACRUX',
     'stars': [(29, 48, 1), (9, 22, 1), (25, 2, 2), (41, 15, 2)],
     'lines': [(0, 2), (1, 3)]},
    {'name': 'CENTAURUS', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'RIGIL KENTAURUS',
     'stars': [
              (12, 41, 1), (18, 39, 1), (14, 8, 2), (34, 25, 2), (22, 30, 2),
              (8, 17, 2), (18, 22, 2), (40, 28, 2), (26, 8, 2), (2, 18, 2),
              (19, 15, 2), (17, 15, 3), (17, 19, 3), (48, 37, 3), (23, 12, 3),
              (36, 27, 3), (39, 30, 3), (11, 10, 3), (15, 14, 3), (36, 13, 3),
              (43, 42, 3)
     ],
     'lines': [
              (3, 4), (4, 1), (1, 0), (4, 6), (6, 3), (6, 12), (12, 11),
              (11, 5), (11, 18), (18, 17), (17, 2), (2, 10), (10, 6), (13, 7),
              (7, 15), (15, 3), (15, 16), (16, 20), (10, 14), (14, 8), (8, 19),
              (5, 9)
     ]},
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

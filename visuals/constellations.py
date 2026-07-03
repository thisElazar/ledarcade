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
     'bright_star': 'HIP 40526',
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
     'bright_star': 'HIP 7097',
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

    # ==================== NON-ZODIAC (76) ====================
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
     'bright_star': 'HIP 4427',
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
     'bright_star': 'ALPHERATZ',
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
    {'name': 'CANIS MINOR', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'PROCYON',
     'stars': [(2, 48, 1), (48, 2, 2)],
     'lines': [(0, 1)]},
    {'name': 'AURIGA', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'CAPELLA',
     'stars': [
              (28, 17, 1), (25, 48, 2), (15, 19, 2), (14, 32, 2), (36, 39, 2),
              (33, 21, 2), (32, 26, 2), (33, 26, 3), (17, 2, 3)
     ],
     'lines': [
              (1, 4), (4, 6), (6, 0), (0, 2), (2, 3), (3, 1), (6, 7), (7, 5),
              (5, 0), (0, 8), (8, 2)
     ]},
    {'name': 'MONOCEROS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 30867',
     'stars': [
              (42, 36, 3), (14, 41, 3), (48, 35, 3), (25, 26, 3), (2, 30, 3),
              (44, 18, 3), (41, 13, 3), (35, 21, 3), (38, 9, 3)
     ],
     'lines': [
              (8, 6), (6, 5), (5, 7), (7, 6), (7, 3), (3, 0), (0, 2), (3, 4),
              (4, 1)
     ]},
    {'name': 'LEPUS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'ARNEB',
     'stars': [
              (28, 25, 2), (31, 35, 2), (48, 40, 2), (43, 20, 2), (17, 16, 3),
              (19, 40, 3), (10, 14, 3), (14, 35, 3), (38, 10, 3), (43, 10, 3),
              (2, 16, 3)
     ],
     'lines': [
              (2, 3), (3, 0), (0, 1), (1, 2), (8, 3), (3, 9), (1, 5), (5, 7),
              (7, 10), (10, 6), (6, 4), (4, 0)
     ]},
    {'name': 'COLUMBA', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'PHACT',
     'stars': [
              (41, 7, 2), (30, 14, 2), (2, 5, 3), (48, 13, 3), (24, 45, 3),
              (25, 12, 3)
     ],
     'lines': [(0, 1), (3, 0), (4, 1), (1, 5), (5, 2)]},
    {'name': 'CAELUM', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 21770',
     'stars': [(33, 33, 3), (9, 2, 3), (31, 10, 3), (41, 48, 3)],
     'lines': [(1, 2), (2, 0), (0, 3)]},
    {'name': 'CARINA', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'CANOPUS',
     'stars': [
              (48, 28, 1), (18, 36, 2), (32, 13, 2), (26, 26, 2), (24, 20, 2),
              (18, 25, 2), (7, 32, 2), (12, 37, 2), (8, 28, 2), (10, 27, 2),
              (32, 20, 2), (4, 26, 3), (2, 27, 3), (2, 29, 3), (4, 30, 3)
     ],
     'lines': [
              (0, 1), (1, 7), (7, 6), (6, 8), (8, 9), (9, 5), (5, 4), (8, 11),
              (6, 14), (14, 13), (13, 12), (12, 11), (5, 3), (3, 10), (10, 2)
     ]},
    {'name': 'PUPPIS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'CANOPUS',
     'stars': [
              (39, 48, 1), (13, 37, 2), (14, 26, 2), (27, 21, 2), (11, 2, 2),
              (38, 32, 2), (17, 3, 2), (21, 6, 3), (19, 9, 3), (18, 4, 3),
              (22, 8, 3)
     ],
     'lines': [
              (1, 2), (2, 4), (4, 6), (6, 7), (7, 10), (10, 3), (3, 5), (5, 0),
              (10, 8), (8, 9), (9, 6)
     ]},
    {'name': 'PICTOR', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 32607',
     'stars': [(9, 48, 2), (41, 2, 3), (38, 23, 3)],
     'lines': [(0, 2), (2, 1)]},
    {'name': 'DORADO', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 21281',
     'stars': [
              (36, 13, 2), (10, 37, 3), (47, 2, 3), (8, 48, 3), (3, 40, 3),
              (21, 20, 3)
     ],
     'lines': [(2, 0), (0, 5), (5, 1), (1, 0), (1, 3), (3, 4), (4, 1)]},
    {'name': 'ERIDANUS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'ACHERNAR',
     'stars': [
              (41, 48, 1), (9, 4, 2), (33, 30, 2), (23, 10, 2), (26, 7, 3),
              (21, 25, 3), (40, 42, 3), (30, 16, 3), (28, 7, 3), (18, 23, 3),
              (35, 7, 3), (15, 2, 3), (20, 25, 3), (13, 2, 3), (21, 5, 3),
              (33, 18, 3), (35, 30, 3), (25, 27, 3), (26, 17, 3), (36, 37, 3),
              (37, 11, 3), (30, 32, 3), (28, 16, 3), (26, 9, 3), (36, 14, 3),
              (18, 22, 3), (27, 30, 3), (23, 18, 3), (24, 18, 3), (35, 33, 3)
     ],
     'lines': [
              (1, 13), (13, 11), (11, 14), (14, 3), (3, 23), (23, 4), (4, 8),
              (8, 10), (10, 20), (20, 24), (24, 15), (15, 7), (7, 22),
              (22, 18), (18, 28), (28, 27), (27, 25), (25, 9), (9, 12),
              (12, 5), (5, 17), (17, 26), (26, 21), (21, 2), (2, 16), (16, 29),
              (29, 19), (19, 6), (6, 0)
     ]},
    {'name': 'LYNX', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 45860',
     'stars': [
              (2, 48, 2), (3, 44, 3), (10, 36, 3), (22, 35, 3), (40, 7, 3),
              (48, 2, 3), (8, 42, 3), (37, 23, 3)
     ],
     'lines': [(0, 1), (1, 6), (6, 2), (2, 3), (3, 7), (7, 4), (4, 5)]},
    {'name': 'CAMELOPARDALIS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 23522',
     'stars': [
              (20, 36, 3), (41, 34, 3), (22, 25, 3), (34, 25, 3), (21, 48, 3),
              (10, 2, 3), (32, 15, 3), (9, 17, 3)
     ],
     'lines': [(4, 0), (0, 2), (2, 7), (7, 5), (2, 6), (6, 3), (3, 1)]},
    {'name': 'VOLANS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 41312',
     'stars': [
              (18, 15, 3), (48, 35, 3), (47, 24, 3), (2, 18, 3), (26, 25, 3)
     ],
     'lines': [(3, 0), (0, 4), (4, 2), (2, 1), (1, 4), (4, 3)]},
    {'name': 'MENSA', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 29271',
     'stars': [(2, 41, 3), (48, 9, 3)],
     'lines': [(0, 1)]},
    {'name': 'RETICULUM', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 19780',
     'stars': [(13, 28, 2), (40, 48, 3), (10, 2, 3), (28, 19, 3)],
     'lines': [(0, 1), (1, 3), (3, 2), (2, 0)]},
    {'name': 'HOROLOGIUM', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'HIP 19747',
     'stars': [
              (6, 2, 3), (36, 48, 3), (35, 38, 3), (43, 27, 3), (44, 23, 3),
              (43, 19, 3)
     ],
     'lines': [(0, 5), (5, 4), (4, 3), (3, 2), (2, 1)]},
    {'name': 'PYXIS', 'season': 'WINTER', 'zodiac': False,
     'bright_star': 'NAOS',
     'stars': [(42, 48, 2), (14, 22, 3), (16, 30, 3), (8, 2, 3)],
     'lines': [(0, 2), (2, 1), (1, 3)]},
    {'name': 'BOOTES', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'ARCTURUS',
     'stars': [
              (28, 41, 1), (21, 32, 2), (34, 42, 2), (24, 19, 2), (13, 24, 2),
              (17, 16, 2), (24, 28, 3), (21, 48, 3), (25, 2, 3), (27, 9, 3),
              (37, 43, 3), (28, 2, 3)
     ],
     'lines': [
              (0, 1), (1, 4), (4, 5), (5, 3), (3, 6), (6, 0), (0, 2), (2, 10),
              (0, 7), (3, 9), (9, 8), (8, 11), (11, 9)
     ]},
    {'name': 'HYDRA', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'ALPHARD',
     'stars': [
              (43, 19, 2), (21, 26, 2), (46, 13, 2), (36, 21, 2), (14, 31, 2),
              (47, 13, 2), (33, 27, 3), (39, 20, 3), (38, 21, 3), (44, 15, 3),
              (42, 16, 3), (35, 22, 3), (41, 21, 3), (48, 13, 3), (31, 28, 3),
              (47, 14, 3), (47, 13, 3), (2, 37, 3), (48, 14, 3), (34, 23, 3),
              (40, 20, 3)
     ],
     'lines': [
              (16, 15), (15, 18), (18, 13), (13, 5), (5, 2), (2, 9), (9, 10),
              (10, 0), (0, 12), (12, 20), (20, 7), (7, 8), (8, 3), (3, 11),
              (19, 6), (6, 14), (14, 1), (1, 4), (4, 17)
     ]},
    {'name': 'CANES VENATICI', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'COR CAROLI',
     'stars': [(2, 41, 2), (48, 9, 3)],
     'lines': [(0, 1)]},
    {'name': 'COMA BERENICES', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'HIP 64394',
     'stars': [(4, 4, 3), (5, 48, 3), (46, 2, 3)],
     'lines': [(1, 0), (0, 2)]},
    {'name': 'LEO MINOR', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'HIP 53229',
     'stars': [
              (2, 27, 3), (17, 21, 3), (29, 25, 3), (48, 21, 3), (18, 29, 3)
     ],
     'lines': [(3, 2), (2, 1), (1, 0), (0, 4), (4, 2)]},
    {'name': 'CRATER', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'HIP 55282',
     'stars': [
              (32, 20, 3), (28, 30, 3), (48, 32, 3), (38, 47, 3), (18, 3, 3),
              (11, 32, 3), (28, 6, 3), (2, 28, 3)
     ],
     'lines': [
              (2, 3), (3, 1), (1, 5), (5, 7), (1, 0), (0, 6), (6, 4), (0, 2)
     ]},
    {'name': 'SEXTANS', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'HIP 49641',
     'stars': [(29, 6, 3), (48, 44, 3), (2, 7, 3), (3, 18, 3)],
     'lines': [(1, 0), (0, 2), (2, 3)]},
    {'name': 'ANTLIA', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'HIP 51172',
     'stars': [(17, 17, 3), (48, 31, 3), (2, 33, 3)],
     'lines': [(2, 0), (0, 1)]},
    {'name': 'VELA', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'REGOR',
     'stars': [
              (48, 27, 2), (35, 38, 2), (31, 17, 2), (26, 38, 2), (2, 31, 2),
              (17, 37, 3), (24, 12, 3), (9, 16, 3)
     ],
     'lines': [
              (1, 0), (0, 2), (2, 6), (6, 7), (7, 4), (4, 5), (5, 3), (3, 1)
     ]},
    {'name': 'MUSCA', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'HIP 61585',
     'stars': [
              (15, 22, 2), (9, 15, 2), (2, 39, 3), (48, 8, 3), (18, 42, 3),
              (27, 14, 3)
     ],
     'lines': [(3, 5), (5, 0), (0, 1), (1, 2), (2, 4), (4, 0)]},
    {'name': 'CHAMAELEON', 'season': 'SPRING', 'zodiac': False,
     'bright_star': 'HIP 40702',
     'stars': [
              (48, 24, 3), (20, 21, 3), (2, 27, 3), (18, 29, 3), (4, 22, 3)
     ],
     'lines': [(0, 1), (1, 3), (3, 2), (2, 4), (4, 1)]},
    {'name': 'HERCULES', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'KORNEPHOROS',
     'stars': [
              (35, 34, 2), (22, 44, 2), (31, 22, 2), (22, 30, 2), (23, 15, 2),
              (13, 26, 2), (31, 12, 2), (10, 24, 3), (38, 37, 3), (17, 3, 3),
              (7, 24, 3), (12, 13, 3), (36, 2, 3), (26, 23, 3), (20, 14, 3),
              (33, 8, 3), (38, 3, 3), (18, 28, 3), (38, 44, 3), (43, 6, 3),
              (36, 48, 3)
     ],
     'lines': [
              (3, 1), (1, 0), (0, 8), (0, 2), (2, 13), (2, 6), (6, 15),
              (15, 12), (6, 4), (4, 14), (14, 11), (11, 9), (4, 13), (13, 3),
              (3, 17), (17, 5), (5, 7), (7, 10), (19, 16), (16, 12), (8, 18),
              (18, 20)
     ]},
    {'name': 'OPHIUCHUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'RASALHAGUE',
     'stars': [
              (17, 2, 2), (24, 32, 2), (32, 27, 2), (39, 20, 2), (15, 11, 2),
              (27, 6, 2), (37, 21, 2), (21, 42, 2), (11, 27, 2), (14, 13, 3),
              (34, 14, 3), (35, 35, 3), (20, 48, 3), (34, 33, 3), (36, 37, 3),
              (35, 41, 3), (35, 25, 3)
     ],
     'lines': [
              (0, 5), (5, 10), (10, 3), (3, 6), (6, 16), (16, 2), (5, 2),
              (2, 1), (1, 4), (4, 9), (9, 8), (4, 0), (1, 7), (7, 12), (2, 13),
              (13, 11), (11, 14), (14, 15)
     ]},
    {'name': 'SERPENS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'SABIK',
     'stars': [
              (28, 40, 2), (46, 21, 2), (40, 30, 2), (12, 29, 2), (17, 36, 2),
              (45, 30, 3), (22, 40, 3), (45, 13, 3), (45, 23, 3), (48, 18, 3),
              (43, 13, 3), (45, 11, 3), (46, 10, 3), (2, 22, 3)
     ],
     'lines': [
              (7, 10), (10, 11), (11, 12), (12, 7), (7, 9), (9, 1), (1, 8),
              (8, 5), (5, 2), (0, 6), (6, 4), (4, 3), (3, 13)
     ]},
    {'name': 'SCUTUM', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 91117',
     'stars': [(29, 18, 3), (15, 2, 3), (35, 48, 3), (20, 22, 3)],
     'lines': [(1, 0), (0, 2), (2, 3), (3, 1)]},
    {'name': 'SAGITTA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 98337',
     'stars': [(2, 14, 3), (30, 25, 3), (46, 36, 3), (48, 30, 3)],
     'lines': [(0, 1), (1, 3), (1, 2)]},
    {'name': 'LUPUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 71860',
     'stars': [
              (43, 37, 2), (37, 26, 2), (20, 21, 2), (26, 19, 2), (26, 29, 2),
              (29, 48, 2), (7, 14, 2), (26, 8, 3), (11, 2, 3)
     ],
     'lines': [
              (0, 5), (5, 4), (4, 2), (2, 3), (3, 1), (2, 6), (6, 7), (7, 8),
              (8, 6), (6, 5)
     ]},
    {'name': 'NORMA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 80000',
     'stars': [(18, 48, 3), (7, 24, 3), (43, 40, 3), (39, 2, 3)],
     'lines': [(2, 0), (0, 1), (1, 3), (3, 2)]},
    {'name': 'CORONA AUSTRALIS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 94160',
     'stars': [
              (2, 22, 3), (3, 12, 3), (7, 7, 3), (4, 30, 3), (48, 43, 3)
     ],
     'lines': [(2, 1), (1, 0), (0, 3), (3, 4)]},
    {'name': 'ARA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 85792',
     'stars': [
              (25, 3, 2), (29, 26, 2), (44, 28, 2), (29, 29, 2), (27, 47, 3),
              (2, 6, 3), (48, 41, 3), (45, 17, 3)
     ],
     'lines': [(3, 4), (4, 6), (6, 2), (2, 7), (7, 0), (0, 5), (0, 1)]},
    {'name': 'TRIANGULUM AUSTRALE', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ATRIA',
     'stars': [(2, 43, 2), (29, 7, 2), (48, 39, 2), (40, 24, 3)],
     'lines': [(0, 1), (1, 3), (3, 2), (2, 0)]},
    {'name': 'CIRCINUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 71908',
     'stars': [(42, 48, 2), (13, 2, 3), (8, 6, 3)],
     'lines': [(1, 0), (0, 2)]},
    {'name': 'CEPHEUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ALDERAMIN',
     'stars': [
              (29, 36, 2), (10, 2, 2), (26, 20, 2), (16, 46, 2), (38, 36, 2),
              (9, 28, 3), (11, 45, 3), (15, 48, 3), (41, 33, 3), (24, 45, 3)
     ],
     'lines': [
              (4, 0), (0, 2), (2, 5), (2, 1), (1, 5), (5, 6), (6, 3), (3, 7),
              (7, 9), (9, 0), (8, 4)
     ]},
    {'name': 'DELPHINUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'ROTANEV',
     'stars': [
              (30, 17, 3), (26, 4, 3), (41, 48, 3), (9, 2, 3), (17, 12, 3)
     ],
     'lines': [(2, 0), (0, 1), (1, 3), (3, 4), (4, 0)]},
    {'name': 'EQUULEUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'KITALPHA',
     'stars': [(19, 48, 3), (22, 3, 3), (31, 2, 3)],
     'lines': [(0, 1), (1, 2)]},
    {'name': 'VULPECULA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 95771',
     'stars': [(48, 23, 3), (2, 27, 3)],
     'lines': [(0, 1)]},
    {'name': 'TELESCOPIUM', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 90422',
     'stars': [(7, 2, 2), (3, 48, 3), (47, 2, 3)],
     'lines': [(2, 0), (0, 1)]},
    {'name': 'PAVO', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'PEACOCK',
     'stars': [
              (10, 9, 2), (11, 29, 2), (18, 27, 3), (48, 28, 3), (22, 41, 3),
              (34, 38, 3), (2, 31, 3), (35, 19, 3), (44, 24, 3), (42, 19, 3),
              (32, 29, 3)
     ],
     'lines': [
              (0, 2), (2, 1), (0, 6), (6, 1), (5, 2), (2, 4), (2, 10), (10, 8),
              (8, 3), (8, 9), (9, 7), (7, 2)
     ]},
    {'name': 'APUS', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 72370',
     'stars': [(48, 33, 3), (7, 27, 3), (2, 17, 3), (13, 25, 3)],
     'lines': [(0, 1), (3, 2), (2, 1)]},
    {'name': 'LACERTA', 'season': 'SUMMER', 'zodiac': False,
     'bright_star': 'HIP 111169',
     'stars': [
              (23, 8, 3), (32, 48, 3), (24, 16, 3), (27, 2, 3), (17, 27, 3),
              (33, 42, 3), (23, 31, 3), (28, 20, 3), (26, 11, 3)
     ],
     'lines': [
              (2, 0), (0, 3), (3, 8), (8, 2), (2, 7), (7, 6), (6, 4), (4, 2),
              (6, 5), (5, 1)
     ]},
    {'name': 'CETUS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'DENEB KAITOS',
     'stars': [
              (40, 41, 2), (2, 16, 2), (33, 32, 2), (7, 17, 2), (23, 38, 2),
              (48, 31, 3), (29, 29, 3), (22, 31, 3), (9, 20, 3), (7, 9, 3),
              (12, 11, 3), (3, 10, 3), (14, 23, 3)
     ],
     'lines': [
              (3, 1), (1, 11), (11, 9), (9, 10), (10, 3), (3, 8), (8, 12),
              (12, 7), (7, 4), (4, 0), (0, 5), (5, 2), (2, 6), (6, 7)
     ]},
    {'name': 'TRIANGULUM', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 10064',
     'stars': [(17, 2, 2), (47, 48, 2), (3, 12, 3)],
     'lines': [(1, 0), (0, 2), (2, 1)]},
    {'name': 'FORNAX', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 14879',
     'stars': [(2, 20, 3), (18, 30, 3), (48, 21, 3)],
     'lines': [(0, 1), (1, 2)]},
    {'name': 'SCULPTOR', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 4577',
     'stars': [(2, 19, 3), (41, 35, 3), (48, 25, 3), (35, 15, 3)],
     'lines': [(0, 3), (3, 2), (2, 1)]},
    {'name': 'PISCIS AUSTRINUS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'FOMALHAUT',
     'stars': [
              (2, 24, 1), (13, 16, 3), (4, 32, 3), (19, 31, 3), (48, 34, 3),
              (6, 33, 3), (33, 33, 3), (47, 28, 3)
     ],
     'lines': [
              (0, 2), (2, 5), (5, 3), (3, 6), (6, 4), (4, 7), (7, 6), (6, 1),
              (1, 0)
     ]},
    {'name': 'GRUS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'AL NAIR',
     'stars': [
              (32, 30, 2), (15, 30, 2), (42, 2, 2), (13, 43, 2), (22, 20, 3),
              (8, 48, 3), (35, 8, 3)
     ],
     'lines': [(2, 6), (6, 4), (4, 0), (0, 1), (1, 4), (1, 3), (3, 5)]},
    {'name': 'PHOENIX', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'ANKAA',
     'stars': [
              (39, 4, 2), (16, 18, 2), (2, 7, 2), (48, 17, 3), (2, 26, 3),
              (15, 46, 3)
     ],
     'lines': [(0, 1), (1, 2), (0, 3), (3, 1), (1, 5), (5, 4), (4, 2)]},
    {'name': 'TUCANA', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 110130',
     'stars': [
              (48, 23, 2), (27, 14, 3), (7, 35, 3), (2, 30, 3), (13, 36, 3),
              (42, 36, 3)
     ],
     'lines': [(3, 2), (2, 4), (4, 5), (5, 0), (0, 1), (1, 3)]},
    {'name': 'INDUS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 101772',
     'stars': [
              (48, 4, 2), (35, 46, 3), (22, 27, 3), (2, 35, 3), (43, 21, 3)
     ],
     'lines': [(1, 4), (4, 0), (0, 2), (2, 3), (3, 1)]},
    {'name': 'MICROSCOPIUM', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 102831',
     'stars': [(41, 48, 3), (9, 2, 3)],
     'lines': [(0, 1)]},
    {'name': 'OCTANS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 107089',
     'stars': [(13, 2, 3), (7, 18, 3), (43, 48, 3)],
     'lines': [(2, 0), (0, 1), (1, 2)]},
    {'name': 'HYDRUS', 'season': 'AUTUMN', 'zodiac': False,
     'bright_star': 'HIP 2021',
     'stars': [(41, 48, 2), (30, 2, 2), (9, 40, 2), (23, 21, 3)],
     'lines': [(0, 2), (2, 3), (3, 1), (1, 0)]},
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
    category = "science_macro"
    GUIDE = {
        'desc': 'Real star positions from the Hipparcos catalog (ESA, 1997) with constellation lines from Stellarium. Stars rendered at correct relative brightness. Joystick to rotate the sky.',
        'controls': {
            'Up/Down': 'Switch group',
            'Left/Right': 'Step through constellations',
            'Button': 'Toggle auto-cycle',
        },
    }

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

"""
COINS OF THE WORLD -- Historic Coinage on 64x64 LED Matrix
============================================================
Pixel-art renderings of 18 historic coins from world civilizations,
spanning ancient to modern eras. Each coin is rendered as a filled
circle with rim highlights, interior design pattern, and a rotating
shine arc.

Controls:
  Up/Down    - Cycle eras (ANCIENT / MEDIEVAL / MODERN)
  Left/Right - Cycle coins within era
  Action     - Flip coin (obverse / reverse)
"""

import math
from . import Visual

# ---------------------------------------------------------------------------
# Centre and radius for the coin disc
# ---------------------------------------------------------------------------
CX, CY = 32, 28
R_OUTER = 22
R_INNER = 20

# ---------------------------------------------------------------------------
# Eras
# ---------------------------------------------------------------------------
ERAS = ['ANCIENT', 'MEDIEVAL', 'MODERN']
ERA_COLORS = {
    'ANCIENT':  (180, 160, 80),
    'MEDIEVAL': (160, 140, 100),
    'MODERN':   (140, 160, 180),
}

# ---------------------------------------------------------------------------
# Coin data -- each dict holds everything needed to render one coin
# design: list of (dx, dy) offsets from (CX, CY)
# ---------------------------------------------------------------------------
COINS = [
    # ===== ANCIENT (indices 0-6) =====
    {
        'name': 'LYDIAN STATER', 'origin': 'Lydia 600 BCE', 'era': 'ANCIENT',
        'material': 'Gold', 'color': (220, 190, 80), 'rim': (255, 225, 120),
        'reverse': 'FIRST COIN',
        'design': [
            # Lion head profile facing right
            (-8, -2), (-7, -3), (-6, -4), (-5, -5), (-4, -5),    # mane top
            (-3, -5), (-2, -4), (-1, -3), (0, -3), (1, -2),      # forehead
            (2, -2), (3, -1), (4, -1), (5, 0), (6, 0),           # snout
            (7, 1), (6, 1), (5, 2), (4, 2),                       # jaw
            (3, 3), (2, 3), (1, 3), (0, 3), (-1, 3),             # chin
            (-2, 3), (-3, 2), (-4, 2), (-5, 1), (-6, 1),         # neck
            (-7, 0), (-8, -1),                                     # back
            (-4, -3), (-3, -2), (-2, -1),                         # mane fill
            (2, 0), (3, 0), (4, 1),                               # face fill
            (3, -1), (2, -1), (1, -1), (0, -1),                   # eye line
            (2, 0),                                                # eye
        ],
    },
    {
        'name': 'ATHENIAN OWL', 'origin': 'Athens 5th c BCE', 'era': 'ANCIENT',
        'material': 'Silver', 'color': (200, 200, 210), 'rim': (235, 235, 245),
        'reverse': 'TETRADRACHM',
        'design': [
            # Owl face -- frontal view
            (-4, -4), (-3, -5), (-2, -5), (-1, -5),              # left brow
            (1, -5), (2, -5), (3, -5), (4, -4),                  # right brow
            (-5, -3), (-4, -2), (-3, -2),                        # left eye ring
            (3, -2), (4, -2), (5, -3),                            # right eye ring
            (-3, -3), (3, -3),                                    # eyes
            (0, -2), (0, -1),                                     # beak
            (-1, -1), (1, -1),                                    # beak sides
            (-6, -1), (-6, 0), (-6, 1), (-6, 2),                 # left body
            (6, -1), (6, 0), (6, 1), (6, 2),                     # right body
            (-5, 3), (-4, 3), (-3, 3), (-2, 3),                  # feet left
            (2, 3), (3, 3), (4, 3), (5, 3),                      # feet right
            (-5, 1), (-4, 0), (-3, 1), (-2, 0),                  # wing left
            (2, 0), (3, 1), (4, 0), (5, 1),                      # wing right
            (-1, 1), (0, 1), (1, 1),                              # belly
            (-1, 2), (0, 2), (1, 2),                              # belly low
        ],
    },
    {
        'name': 'ROMAN DENARIUS', 'origin': 'Rome 1st c CE', 'era': 'ANCIENT',
        'material': 'Silver', 'color': (190, 190, 200), 'rim': (225, 225, 235),
        'reverse': 'CAESAR',
        'design': [
            # Profile head facing right (emperor)
            (-2, -7), (-1, -7), (0, -7),                         # top of head
            (-3, -6), (-3, -5), (-3, -4),                        # back of head
            (1, -6), (2, -5), (3, -4),                            # forehead
            (4, -3), (4, -2),                                     # brow
            (5, -1), (5, 0),                                      # nose
            (4, 1), (3, 2),                                       # mouth
            (2, 3), (1, 3), (0, 3),                               # chin
            (-1, 3), (-2, 2), (-3, 1),                            # jaw
            (-3, 0), (-3, -1), (-3, -2),                          # back neck
            (-2, -5), (-1, -5), (0, -5),                         # hair fill
            (-2, -4), (-1, -3), (0, -2), (1, -2),                # face fill
            (1, -1), (2, -1), (3, 0), (2, 1),                    # face fill 2
            # Laurel wreath
            (-4, -5), (-5, -4), (-5, -3), (-4, -2),              # wreath left
            (1, -7), (2, -6), (3, -5),                            # wreath right
        ],
    },
    {
        'name': 'BAN LIANG', 'origin': 'Qin Dynasty', 'era': 'ANCIENT',
        'material': 'Bronze', 'color': (160, 130, 70), 'rim': (195, 165, 105),
        'reverse': 'QIN 221 BCE',
        'design': [
            # Square hole in centre
            (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2),
            (-2, -1), (2, -1),
            (-2, 0), (2, 0),
            (-2, 1), (2, 1),
            (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2),
            # Characters left and right of hole
            (-6, -3), (-6, -2), (-6, -1), (-6, 0), (-6, 1),     # left stroke
            (-5, -1), (-4, -1),                                   # left cross
            (5, -3), (5, -2), (5, -1), (5, 0), (5, 1),          # right stroke
            (6, 0), (7, -1),                                      # right cross
        ],
    },
    {
        'name': 'KARSHAPANA', 'origin': 'Maurya Empire', 'era': 'ANCIENT',
        'material': 'Silver', 'color': (180, 180, 190), 'rim': (215, 215, 225),
        'reverse': 'PUNCH MARK',
        'design': [
            # Punch marks -- scattered circles and dots
            (-5, -4), (-4, -5), (-3, -4), (-4, -3),              # top-left circle
            (4, -4), (5, -5), (6, -4), (5, -3),                  # top-right circle
            (0, -2), (1, -1), (-1, -1), (0, 0),                  # centre diamond
            (-6, 1), (-5, 2), (-7, 2), (-6, 3),                  # bottom-left circle
            (5, 2), (6, 1), (7, 2), (6, 3),                      # bottom-right circle
            (0, 4), (-1, 5), (1, 5), (0, 6),                     # bottom circle
            (-3, 0), (3, 0),                                      # side dots
            (-2, 3), (2, -3),                                     # scatter dots
        ],
    },
    {
        'name': 'PERSIAN DARIC', 'origin': 'Achaemenid', 'era': 'ANCIENT',
        'material': 'Gold', 'color': (210, 185, 75), 'rim': (245, 220, 115),
        'reverse': 'ARCHER KING',
        'design': [
            # Archer/king kneeling with bow
            (0, -6), (0, -5), (-1, -5), (1, -5),                 # crown
            (0, -4), (0, -3), (0, -2),                            # torso
            (-1, -3), (-2, -2), (-3, -1), (-4, 0),               # bow arm
            (-5, 1), (-4, 2), (-3, 1),                            # bow top
            (-5, 3), (-4, 4), (-3, 3),                            # bow bottom
            (1, -2), (2, -1), (3, 0),                             # back arm
            (0, -1), (0, 0),                                      # lower torso
            (-1, 1), (1, 1),                                      # hips
            (-2, 2), (-2, 3), (-2, 4),                            # left leg
            (2, 2), (2, 3), (3, 4),                               # right leg
            (-3, 5), (-1, 5), (1, 5), (4, 5),                    # feet
        ],
    },
    {
        'name': 'CELTIC STATER', 'origin': 'Gaul 2nd c BCE', 'era': 'ANCIENT',
        'material': 'Gold', 'color': (200, 180, 70), 'rim': (235, 215, 110),
        'reverse': 'HORSE',
        'design': [
            # Stylized horse -- abstract Celtic style
            (-6, 0), (-5, -1), (-4, -2), (-3, -3),               # neck
            (-2, -3), (-1, -2), (0, -2), (1, -2),                # back
            (2, -2), (3, -1), (4, 0), (5, 1),                    # rump
            (5, 2), (4, 3),                                       # hind leg
            (-5, 0), (-5, 1), (-5, 2), (-5, 3),                  # front leg
            (-3, -4), (-2, -5), (-1, -5),                        # head
            (-4, -5),                                             # ear
            (0, -1), (1, -1), (2, -1),                            # body fill
            (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0),            # body fill 2
            (-2, 1), (-1, 1), (0, 1), (1, 1),                    # belly
            # Celtic spirals
            (-7, 3), (-6, 4), (-7, 5),                           # spiral 1
            (6, -4), (7, -3), (6, -2),                            # spiral 2
        ],
    },
    # ===== MEDIEVAL (indices 7-11) =====
    {
        'name': 'SOLIDUS', 'origin': 'Byzantium 5th c', 'era': 'MEDIEVAL',
        'material': 'Gold', 'color': (215, 190, 80), 'rim': (250, 225, 120),
        'reverse': 'BYZANTINE',
        'design': [
            # Cross pattern with orbs
            (0, -7), (0, -6), (0, -5), (0, -4), (0, -3),        # cross top
            (0, -2), (0, -1), (0, 0), (0, 1), (0, 2),           # cross centre
            (0, 3), (0, 4), (0, 5),                               # cross bottom
            (-5, 0), (-4, 0), (-3, 0), (-2, 0), (-1, 0),        # cross left
            (1, 0), (2, 0), (3, 0), (4, 0), (5, 0),             # cross right
            # Orbs at cross ends
            (-1, -7), (1, -7),                                    # top orb
            (-1, 5), (1, 5),                                      # bottom orb
            (-5, -1), (-5, 1),                                    # left orb
            (5, -1), (5, 1),                                      # right orb
        ],
    },
    {
        'name': 'ISLAMIC DINAR', 'origin': 'Abbasid 8th c', 'era': 'MEDIEVAL',
        'material': 'Gold', 'color': (210, 185, 75), 'rim': (245, 220, 115),
        'reverse': 'CALIPHATE',
        'design': [
            # Geometric circles and script lines (no figural images)
            # Inner circle
            *[(int(5 * math.cos(a * math.pi / 6)), int(5 * math.sin(a * math.pi / 6)))
              for a in range(12)],
            # Centre dot cluster
            (0, 0), (-1, 0), (1, 0), (0, -1), (0, 1),
            # Script lines (horizontal strokes representing Kufic)
            (-3, -3), (-2, -3), (-1, -3), (0, -3), (1, -3),
            (-2, 3), (-1, 3), (0, 3), (1, 3), (2, 3),
        ],
    },
    {
        'name': 'VIKING PENNY', 'origin': 'Scandinavia 9th c', 'era': 'MEDIEVAL',
        'material': 'Silver', 'color': (185, 185, 195), 'rim': (220, 220, 230),
        'reverse': 'NORSE',
        'design': [
            # Cross
            (0, -5), (0, -4), (0, -3), (0, -2), (0, -1),
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4), (0, 5),
            (-5, 0), (-4, 0), (-3, 0), (-2, 0), (-1, 0),
            (1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
            # Thor's hammer in one quadrant
            (-3, -3), (-4, -4), (-5, -5),                        # handle
            (-5, -6), (-4, -6), (-6, -5), (-6, -4),              # hammer head
        ],
    },
    {
        'name': 'FLORIN', 'origin': 'Florence 1252', 'era': 'MEDIEVAL',
        'material': 'Gold', 'color': (220, 190, 80), 'rim': (255, 225, 120),
        'reverse': 'FIORINO',
        'design': [
            # Fleur-de-lis
            (0, -7), (0, -6),                                     # top point
            (-1, -5), (1, -5),                                    # top spread
            (-2, -4), (2, -4),                                    # outer spread
            (-3, -3), (3, -3), (0, -4), (0, -3),                 # arms up
            (-4, -2), (4, -2),                                    # arm tips
            (-4, -1), (4, -1),                                    # arm tips
            (-3, 0), (3, 0),                                      # arm return
            (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),           # band
            (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),           # band
            (0, 2), (0, 3), (0, 4), (0, 5),                      # stem
            (-1, 5), (1, 5), (-2, 5), (2, 5),                    # base
        ],
    },
    {
        'name': 'VENETIAN DUCAT', 'origin': 'Venice 1284', 'era': 'MEDIEVAL',
        'material': 'Gold', 'color': (215, 185, 75), 'rim': (250, 220, 115),
        'reverse': 'DOGE',
        'design': [
            # Standing figure (saint presenting banner to Doge)
            (-3, -6), (-3, -5),                                   # figure 1 head
            (-4, -4), (-3, -4), (-2, -4),                        # shoulders
            (-3, -3), (-3, -2), (-3, -1), (-3, 0),               # body
            (-4, 1), (-3, 1), (-2, 1),                            # robe
            (-4, 2), (-2, 2),                                     # feet
            (3, -6), (3, -5),                                     # figure 2 head
            (2, -4), (3, -4), (4, -4),                            # shoulders
            (3, -3), (3, -2), (3, -1), (3, 0),                   # body
            (2, 1), (3, 1), (4, 1),                               # robe
            (2, 2), (4, 2),                                       # feet
            # Banner between them
            (0, -5), (0, -4), (0, -3), (0, -2),                  # pole
            (-1, -5), (1, -5), (-1, -4), (1, -4),                # flag
            # Stars
            (-6, -3), (6, -3), (0, 4),
        ],
    },
    # ===== MODERN (indices 12-17) =====
    {
        'name': 'SPANISH REAL', 'origin': 'Spain 16th c', 'era': 'MODERN',
        'material': 'Silver', 'color': (195, 195, 205), 'rim': (230, 230, 240),
        'reverse': 'PIECE OF EIGHT',
        'design': [
            # Pillars of Hercules
            (-5, -5), (-5, -4), (-5, -3), (-5, -2), (-5, -1),
            (-5, 0), (-5, 1), (-5, 2), (-5, 3), (-5, 4),        # left pillar
            (-6, -5), (-4, -5),                                   # left capital
            (-6, 4), (-4, 4),                                     # left base
            (5, -5), (5, -4), (5, -3), (5, -2), (5, -1),
            (5, 0), (5, 1), (5, 2), (5, 3), (5, 4),             # right pillar
            (6, -5), (4, -5),                                     # right capital
            (6, 4), (4, 4),                                       # right base
            # Crown between
            (-1, -6), (0, -7), (1, -6),
            (-1, -5), (0, -5), (1, -5),
            # Waves between pillars
            (-3, 1), (-2, 0), (-1, 1), (0, 0), (1, 1), (2, 0), (3, 1),
            (-3, 3), (-2, 2), (-1, 3), (0, 2), (1, 3), (2, 2), (3, 3),
        ],
    },
    {
        'name': 'JAPANESE MON', 'origin': 'Edo Japan', 'era': 'MODERN',
        'material': 'Bronze', 'color': (150, 120, 60), 'rim': (185, 155, 95),
        'reverse': 'KANEI TSUHO',
        'design': [
            # Square hole in centre (like Ban Liang tradition)
            (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2),
            (-2, -1), (2, -1),
            (-2, 0), (2, 0),
            (-2, 1), (2, 1),
            (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2),
            # Kanji-like strokes around hole
            (-6, -4), (-5, -4), (-4, -4), (-6, -3), (-5, -2),   # top-left char
            (4, -4), (5, -4), (6, -4), (5, -3), (5, -2),        # top-right char
            (-6, 4), (-5, 4), (-4, 4), (-5, 3), (-6, 3),        # bot-left char
            (4, 4), (5, 4), (6, 4), (5, 3), (4, 3),             # bot-right char
        ],
    },
    {
        'name': 'MUGHAL RUPEE', 'origin': 'Mughal India', 'era': 'MODERN',
        'material': 'Silver', 'color': (190, 190, 200), 'rim': (225, 225, 235),
        'reverse': 'AKBAR',
        'design': [
            # Border dots in inner ring
            *[(int(8 * math.cos(a * math.pi / 8)), int(8 * math.sin(a * math.pi / 8)))
              for a in range(16)],
            # Centre calligraphy (abstract lines)
            (-3, -1), (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1), (3, -1),
            (-2, 0), (0, 0), (2, 0),
            (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1),
        ],
    },
    {
        'name': 'SOVEREIGN', 'origin': 'Britain 1817', 'era': 'MODERN',
        'material': 'Gold', 'color': (215, 185, 75), 'rim': (250, 220, 115),
        'reverse': 'ST GEORGE',
        'design': [
            # Cross with shield centre
            (0, -6), (0, -5), (0, -4), (0, -3),                  # cross top
            (0, 3), (0, 4), (0, 5), (0, 6),                      # cross bottom
            (-6, 0), (-5, 0), (-4, 0), (-3, 0),                  # cross left
            (3, 0), (4, 0), (5, 0), (6, 0),                      # cross right
            # Shield centre
            (-2, -2), (-1, -2), (0, -2), (1, -2), (2, -2),
            (-2, -1), (-1, -1), (0, -1), (1, -1), (2, -1),
            (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),
            (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1),
            (-1, 2), (0, 2), (1, 2),                              # shield point
        ],
    },
    {
        'name': 'MORGAN DOLLAR', 'origin': 'USA 1878', 'era': 'MODERN',
        'material': 'Silver', 'color': (200, 200, 210), 'rim': (235, 235, 245),
        'reverse': 'E PLURIBUS',
        'design': [
            # Eagle with spread wings
            (0, -3), (0, -2),                                     # head
            (-1, -1), (0, -1), (1, -1),                          # neck
            (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0),           # body
            # Left wing
            (-3, -1), (-4, -2), (-5, -3), (-6, -4), (-7, -5),
            (-3, 0), (-4, -1), (-5, -2), (-6, -3),
            # Right wing
            (3, -1), (4, -2), (5, -3), (6, -4), (7, -5),
            (3, 0), (4, -1), (5, -2), (6, -3),
            # Tail
            (-1, 1), (0, 1), (1, 1),
            (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2),
            (-1, 3), (0, 3), (1, 3),
            # Shield on breast
            (0, 0),
        ],
    },
    {
        'name': 'SWISS FRANC', 'origin': 'Switzerland 1850', 'era': 'MODERN',
        'material': 'Silver', 'color': (195, 195, 205), 'rim': (230, 230, 240),
        'reverse': 'HELVETIA',
        'design': [
            # Swiss cross
            (-1, -5), (0, -5), (1, -5),
            (-1, -4), (0, -4), (1, -4),
            (-1, -3), (0, -3), (1, -3),
            (-5, -1), (-4, -1), (-3, -1), (-2, -1), (-1, -1),
            (0, -1), (1, -1), (2, -1), (3, -1), (4, -1), (5, -1),
            (-5, 0), (-4, 0), (-3, 0), (-2, 0), (-1, 0),
            (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
            (-5, 1), (-4, 1), (-3, 1), (-2, 1), (-1, 1),
            (0, 1), (1, 1), (2, 1), (3, 1), (4, 1), (5, 1),
            (-1, 3), (0, 3), (1, 3),
            (-1, 4), (0, 4), (1, 4),
            (-1, 5), (0, 5), (1, 5),
        ],
    },
]

# Build per-era index for fast lookup
_ERA_COINS = {era: [] for era in ERAS}
for _i, _c in enumerate(COINS):
    _ERA_COINS[_c['era']].append(_i)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dist_sq(x1, y1, x2, y2):
    return (x2 - x1) ** 2 + (y2 - y1) ** 2


def _blend(base, top, alpha):
    """Blend two RGB tuples."""
    return tuple(int(b + (t - b) * alpha) for b, t in zip(base, top))


def _darken(color, factor=0.55):
    return tuple(max(0, int(c * factor)) for c in color)


def _lighten(color, amount=40):
    return tuple(min(255, c + amount) for c in color)


# ---------------------------------------------------------------------------
# Precompute filled-circle pixel sets for both radii
# ---------------------------------------------------------------------------
_OUTER_PIXELS = set()
_INNER_PIXELS = set()
_RIM_PIXELS = set()

for _y in range(-R_OUTER - 1, R_OUTER + 2):
    for _x in range(-R_OUTER - 1, R_OUTER + 2):
        d2 = _x * _x + _y * _y
        if d2 <= R_OUTER * R_OUTER:
            _OUTER_PIXELS.add((_x, _y))
        if d2 <= R_INNER * R_INNER:
            _INNER_PIXELS.add((_x, _y))

_RIM_PIXELS = _OUTER_PIXELS - _INNER_PIXELS

# Precompute outline pixels for the outer circle
_OUTLINE_PIXELS = set()
for _y in range(-R_OUTER - 1, R_OUTER + 2):
    for _x in range(-R_OUTER - 1, R_OUTER + 2):
        d2 = _x * _x + _y * _y
        r_lo = (R_OUTER - 1) ** 2
        r_hi = (R_OUTER + 1) ** 2
        if r_lo <= d2 <= r_hi:
            _OUTLINE_PIXELS.add((_x, _y))


class Coins(Visual):
    """Historic coins of the world rendered as pixel art on 64x64 LED."""

    name = "COINS"
    description = "Historic coins of the world"
    category = "culture"

    def reset(self):
        self.era_idx = 0
        self.coin_idx_in_era = 0
        self.obverse = True           # True = front, False = reverse text
        self.reveal_timer = 0.0
        self.reveal_duration = 1.5
        self.hold_timer = 0.0
        self.hold_duration = 3.0
        self.shine_angle = 0.0
        self.overlay_timer = 0.0
        self.overlay_text = ''
        self.auto_advance = True
        self._flip_anim = 0.0         # 0 = not flipping
        self._sorted_designs = {}     # cache sorted design by distance
        self._input_cooldown = 0.0

    def _current_coin(self):
        era = ERAS[self.era_idx]
        indices = _ERA_COINS[era]
        idx = indices[self.coin_idx_in_era % len(indices)]
        return COINS[idx]

    def _sorted_design(self, coin):
        """Return design pixels sorted by distance from centre (for reveal)."""
        key = coin['name']
        if key not in self._sorted_designs:
            pts = coin['design']
            self._sorted_designs[key] = sorted(pts, key=lambda p: p[0] ** 2 + p[1] ** 2)
        return self._sorted_designs[key]

    def _advance(self, direction=1):
        """Advance to next/prev coin in current era."""
        era = ERAS[self.era_idx]
        n = len(_ERA_COINS[era])
        self.coin_idx_in_era = (self.coin_idx_in_era + direction) % n
        self.reveal_timer = 0.0
        self.hold_timer = 0.0
        self.obverse = True
        self._flip_anim = 0.0

    def _show_overlay(self, text):
        self.overlay_timer = 1.5
        self.overlay_text = text

    def handle_input(self, input_state):
        if self._input_cooldown > 0:
            return False
        up = input_state.up_pressed
        down = input_state.down_pressed
        left = input_state.left_pressed
        right = input_state.right_pressed
        action = input_state.action_l or input_state.action_r

        if up or down:
            d = -1 if up else 1
            self.era_idx = (self.era_idx + d) % len(ERAS)
            self.coin_idx_in_era = 0
            self.reveal_timer = 0.0
            self.hold_timer = 0.0
            self.obverse = True
            self._flip_anim = 0.0
            self._show_overlay(ERAS[self.era_idx])
            self._input_cooldown = 0.15
            return True

        if left or right:
            d = -1 if left else 1
            self._advance(d)
            self._input_cooldown = 0.15
            return True

        if action:
            self._flip_anim = 0.5  # half-second flip
            self._input_cooldown = 0.15
            return True

        return False

    def update(self, dt):
        super().update(dt)
        if self._input_cooldown > 0:
            self._input_cooldown -= dt

        # Shine rotation
        self.shine_angle += dt * math.pi  # 0.5 rev/sec

        # Overlay countdown
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Flip animation
        if self._flip_anim > 0:
            self._flip_anim -= dt
            if self._flip_anim <= 0:
                self._flip_anim = 0.0
                self.obverse = not self.obverse

        # Reveal animation
        if self.reveal_timer < self.reveal_duration:
            self.reveal_timer = min(self.reveal_duration, self.reveal_timer + dt)
        else:
            # Hold then auto-advance
            self.hold_timer += dt
            if self.hold_timer >= self.hold_duration and self.auto_advance:
                self._advance(1)

    def draw(self):
        d = self.display
        d.clear()

        coin = self._current_coin()
        body_color = coin['color']
        rim_color = coin['rim']
        design_color = _darken(body_color, 0.45)
        inner_rim_color = _lighten(body_color, 15)
        mid_shade = _blend(body_color, (0, 0, 0), 0.15)

        # --- Coin name at top ---
        name = coin['name']
        # Truncate if too wide (4px per char + 1px gap = 5px, 64/5 ~12 chars)
        if len(name) > 12:
            name = name[:12]
        # Centre the name
        text_w = len(name) * 5
        tx = max(0, (64 - text_w) // 2)
        d.draw_text_small(tx, 1, name, (230, 230, 230))

        # --- Flip animation squeeze ---
        flip_scale = 1.0
        if self._flip_anim > 0:
            # Scale from 1->0->1 over 0.5s; at midpoint (0.25s) = 0
            phase = 1.0 - self._flip_anim / 0.5
            flip_scale = abs(1.0 - 2.0 * phase)

        # --- Draw coin body ---
        for (ox, oy) in _OUTER_PIXELS:
            # Apply flip squeeze (horizontal only)
            sx = int(ox * flip_scale)
            px = CX + sx
            py = CY + oy
            if 0 <= px < 64 and 0 <= py < 64:
                if (ox, oy) in _RIM_PIXELS:
                    d.set_pixel(px, py, rim_color)
                else:
                    d.set_pixel(px, py, body_color)

        # Inner rim ring
        for (ox, oy) in _OUTLINE_PIXELS:
            d2 = ox * ox + oy * oy
            r_lo = (R_INNER - 1) ** 2
            r_hi = (R_INNER + 1) ** 2
            if r_lo <= d2 <= r_hi:
                sx = int(ox * flip_scale)
                px = CX + sx
                py = CY + oy
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, inner_rim_color)

        # --- Draw design with reveal ---
        reveal_frac = self.reveal_timer / self.reveal_duration
        sorted_pts = self._sorted_design(coin)
        max_dist = 1.0
        if sorted_pts:
            last = sorted_pts[-1]
            max_dist = max(1.0, math.sqrt(last[0] ** 2 + last[1] ** 2))

        for (ox, oy) in sorted_pts:
            pt_dist = math.sqrt(ox * ox + oy * oy) / max_dist
            if pt_dist > reveal_frac:
                continue
            sx = int(ox * flip_scale)
            px = CX + sx
            py = CY + oy
            if 0 <= px < 64 and 0 <= py < 64:
                d.set_pixel(px, py, design_color)

        # --- Rotating shine arc ---
        arc_len = 6
        for i in range(arc_len):
            a = self.shine_angle + i * 0.12
            sx_f = R_OUTER * math.cos(a)
            sy_f = R_OUTER * math.sin(a)
            sx2 = int(sx_f * flip_scale)
            px = CX + sx2
            py = CY + int(sy_f)
            if 0 <= px < 64 and 0 <= py < 64:
                # Brightness fades along the arc
                bright = 1.0 - i / arc_len
                shine_c = tuple(min(255, int(c + 60 * bright)) for c in rim_color)
                d.set_pixel(px, py, shine_c)

        # --- Bottom text ---
        if self.obverse:
            info = coin['origin']
        else:
            info = coin.get('reverse', coin['origin'])

        # Material tag
        mat = coin['material']
        mat_color = (120, 120, 120)

        # Origin / reverse on line 57
        if len(info) > 12:
            info = info[:12]
        iw = len(info) * 5
        ix = max(0, (64 - iw) // 2)
        d.draw_text_small(ix, 54, info, (160, 160, 160))

        # Material on line 60
        mw = len(mat) * 5
        mx = max(0, (64 - mw) // 2)
        d.draw_text_small(mx, 60, mat, mat_color)

        # --- Era overlay ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            era_name = self.overlay_text
            ec = ERA_COLORS.get(era_name, (180, 180, 180))
            oc = tuple(int(c * alpha) for c in ec)
            bg_alpha = alpha * 0.7
            # Draw background band
            for y in range(24, 34):
                for x in range(0, 64):
                    bg = (int(20 * bg_alpha), int(15 * bg_alpha), int(10 * bg_alpha))
                    px_c = d.get_pixel(x, y) if hasattr(d, 'get_pixel') else (0, 0, 0)
                    if isinstance(px_c, (list, tuple)) and len(px_c) >= 3:
                        blended = tuple(int(p * (1 - bg_alpha) + b) for p, b in zip(px_c[:3], bg))
                        d.set_pixel(x, y, blended)
                    else:
                        d.set_pixel(x, y, bg)
            # Draw era text
            ew = len(era_name) * 5
            ex = max(0, (64 - ew) // 2)
            d.draw_text_small(ex, 27, era_name, oc)

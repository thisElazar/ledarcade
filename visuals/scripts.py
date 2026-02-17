"""
SCRIPTS - World Writing Systems
================================
Stroke-by-stroke animated display of characters across 20+ writing
systems on a 64x64 LED matrix.  Each character is drawn pixel-by-pixel
in its traditional ink color on a paper-toned background.
"""

import math
from . import Visual

# ── Color constants ──────────────────────────────────────────────
WHITE = (255, 255, 255)
DIM_GRAY = (100, 100, 110)
VERY_DIM = (60, 60, 70)
OVERLAY_BG = (0, 0, 0)

# Drawing area
PAPER_X0, PAPER_Y0 = 10, 14
PAPER_X1, PAPER_Y1 = 54, 56
PAPER_W = PAPER_X1 - PAPER_X0
PAPER_H = PAPER_Y1 - PAPER_Y0

# Animation timing
STROKE_DURATION = 0.4   # seconds per stroke
HOLD_DURATION = 2.0     # hold after all strokes drawn
OVERLAY_FADE = 1.5      # overlay display time

# ── Script families ──────────────────────────────────────────────
FAMILIES = [
    'CHINESE', 'JAPANESE', 'KOREAN', 'ARABIC', 'DEVANAGARI',
    'GREEK', 'CYRILLIC', 'HEBREW', 'HIEROGLYPH', 'CUNEIFORM',
    'RUNIC', 'ARMENIAN', 'ETHIOPIC', 'MAYAN', 'INUKTITUT',
    'OTHER',
]

# ── Ink / paper presets ─────────────────────────────────────────
_CHINESE_INK = (180, 30, 20)
_CHINESE_PAPER = (230, 220, 190)
_JAPANESE_INK = (20, 20, 20)
_JAPANESE_PAPER = (230, 225, 215)
_KOREAN_INK = (20, 30, 80)
_KOREAN_PAPER = (225, 225, 230)
_ARABIC_INK = (30, 25, 20)
_ARABIC_PAPER = (225, 215, 190)
_DEVA_INK = (160, 60, 20)
_DEVA_PAPER = (230, 220, 200)
_GREEK_INK = (25, 40, 120)
_GREEK_PAPER = (225, 220, 210)
_CYRILLIC_INK = (20, 20, 20)
_CYRILLIC_PAPER = (225, 225, 230)
_HEBREW_INK = (30, 25, 20)
_HEBREW_PAPER = (225, 220, 200)
_HIERO_INK = (40, 100, 60)
_HIERO_PAPER = (210, 195, 160)
_CUNEI_INK = (50, 40, 30)
_CUNEI_PAPER = (180, 160, 130)
_RUNIC_INK = (20, 20, 20)
_RUNIC_PAPER = (200, 190, 170)
_ARMENIAN_INK = (60, 30, 20)
_ARMENIAN_PAPER = (225, 218, 200)
_ETHIOPIC_INK = (40, 30, 20)
_ETHIOPIC_PAPER = (220, 210, 185)

# ── Character data ───────────────────────────────────────────────
# Each entry: name, script family, concept, origin string,
# ink color, paper color, strokes (list of point-lists),
# optional 'thick': True for 2px brush width.
CHARACTERS = [
    # ── CHINESE ──────────────────────────────────────────────────
    {
        'name': 'SHAN', 'script': 'CHINESE', 'concept': 'MOUNTAIN',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 46)],                       # center vertical
            [(20, 46), (20, 32), (26, 28)],              # left peak
            [(44, 46), (44, 32), (38, 28)],              # right peak
        ],
    },
    {
        'name': 'SHUI', 'script': 'CHINESE', 'concept': 'WATER',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 48)],                        # center vertical
            [(26, 26), (20, 34), (18, 42)],              # left upper curve
            [(24, 36), (18, 46), (16, 50)],              # left lower curve
            [(38, 26), (44, 34), (48, 44)],              # right curve
        ],
    },
    {
        'name': 'HUO', 'script': 'CHINESE', 'concept': 'FIRE',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(27, 26), (26, 28)],                        # dot left
            [(37, 26), (38, 28)],                        # dot right
            [(32, 22), (24, 34), (20, 46)],              # left stroke
            [(32, 22), (40, 34), (44, 46)],              # right stroke
        ],
    },
    {
        'name': 'REN', 'script': 'CHINESE', 'concept': 'PERSON',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (24, 38), (18, 48)],              # left-falling stroke (pie)
            [(32, 20), (40, 38), (46, 48)],              # right-falling stroke (na)
        ],
    },
    {
        'name': 'MU', 'script': 'CHINESE', 'concept': 'TREE',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(20, 32), (44, 32)],                        # horizontal branch
            [(32, 20), (32, 50)],                        # center trunk
            [(32, 38), (22, 48)],                        # left root
            [(32, 38), (42, 48)],                        # right root
        ],
    },
    {
        'name': 'RI', 'script': 'CHINESE', 'concept': 'SUN / DAY',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (40, 22), (40, 46), (24, 46), (24, 22)],  # outer box
            [(24, 34), (40, 34)],                        # middle bar
        ],
    },
    # ── JAPANESE HIRAGANA ────────────────────────────────────────
    {
        'name': 'A', 'script': 'JAPANESE', 'concept': 'AH',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                        # top horizontal
            [(32, 20), (32, 36)],                        # center vertical
            [(22, 32), (28, 40), (38, 46), (44, 40)],   # bottom curve
        ],
    },
    {
        'name': 'KA', 'script': 'JAPANESE', 'concept': 'KA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 24), (44, 24)],                        # top horizontal
            [(36, 20), (30, 32), (24, 48)],              # left diagonal
            [(36, 28), (42, 38), (40, 48)],              # right curve
        ],
    },
    {
        'name': 'SA', 'script': 'JAPANESE', 'concept': 'SA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                        # top bar
            [(22, 32), (42, 32)],                        # middle bar
            [(36, 24), (30, 40), (24, 50)],              # sweeping curve
        ],
    },
    {
        'name': 'NO', 'script': 'JAPANESE', 'concept': 'NO (PARTICLE)',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(38, 22), (28, 26), (22, 34), (24, 42),
             (32, 48), (42, 44), (44, 36), (38, 28)],   # spiraling loop (like の)
        ],
    },
    # ── KOREAN HANGUL ────────────────────────────────────────────
    {
        'name': 'HA', 'script': 'KOREAN', 'concept': 'HA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],                        # top bar
            [(20, 22), (20, 34)],                        # left vertical
            [(44, 22), (44, 34)],                        # right vertical
            [(20, 34), (44, 34)],                        # middle bar
            [(26, 40), (38, 40), (38, 50), (26, 50), (26, 40)],  # bottom box (ieung)
        ],
    },
    {
        'name': 'GA', 'script': 'KOREAN', 'concept': 'GA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],                        # left vertical (giyeok)
            [(22, 22), (38, 22)],                        # top horizontal
            [(22, 36), (38, 36)],                        # giyeok foot
            [(42, 22), (42, 48)],                        # vowel vertical (a)
            [(42, 34), (48, 34)],                        # vowel dash
        ],
    },
    {
        'name': 'NA', 'script': 'KOREAN', 'concept': 'NA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],                        # nieun vertical
            [(22, 48), (36, 48)],                        # nieun foot
            [(42, 22), (42, 48)],                        # vowel vertical (a)
            [(42, 34), (48, 34)],                        # vowel dash
        ],
    },
    {
        'name': 'DA', 'script': 'KOREAN', 'concept': 'DA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 22), (36, 22)],                        # digeut top
            [(22, 22), (22, 36)],                        # digeut left
            [(22, 36), (36, 36)],                        # digeut bottom
            [(42, 22), (42, 48)],                        # vowel vertical
            [(42, 34), (48, 34)],                        # vowel dash
        ],
    },
    # ── ARABIC ───────────────────────────────────────────────────
    {
        'name': 'ALIF', 'script': 'ARABIC', 'concept': 'A',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(34, 20), (34, 48)],                        # single vertical
        ],
    },
    {
        'name': 'BA', 'script': 'ARABIC', 'concept': 'B',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(20, 36), (26, 30), (38, 30), (44, 36)],   # horizontal boat
            [(32, 42), (32, 44)],                        # dot below
        ],
    },
    {
        'name': 'TA', 'script': 'ARABIC', 'concept': 'T',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(20, 36), (26, 30), (38, 30), (44, 36)],   # horizontal boat
            [(30, 24), (30, 26)],                        # left dot above
            [(36, 24), (36, 26)],                        # right dot above
        ],
    },
    {
        'name': 'JIM', 'script': 'ARABIC', 'concept': 'J',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(22, 24), (42, 24)],                        # top bar
            [(42, 24), (42, 38)],                        # right descender
            [(42, 38), (32, 44), (22, 38)],              # bowl curve
            [(32, 34), (32, 36)],                        # dot inside
        ],
    },
    # ── DEVANAGARI ───────────────────────────────────────────────
    {
        'name': 'KA', 'script': 'DEVANAGARI', 'concept': 'KA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],                        # headline (shirorekha)
            [(36, 22), (36, 48)],                        # main vertical
            [(36, 30), (24, 30), (24, 42), (36, 42)],   # left loop
        ],
    },
    {
        'name': 'MA', 'script': 'DEVANAGARI', 'concept': 'MA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],                        # headline
            [(26, 22), (26, 48)],                        # left vertical
            [(40, 22), (40, 48)],                        # right vertical
            [(26, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'GA', 'script': 'DEVANAGARI', 'concept': 'GA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],                        # headline
            [(34, 22), (34, 48)],                        # main vertical
            [(34, 28), (24, 32), (24, 42), (34, 46)],   # left curve
        ],
    },
    {
        'name': 'TA', 'script': 'DEVANAGARI', 'concept': 'TA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],                        # headline
            [(36, 22), (36, 48)],                        # main vertical
            [(22, 32), (36, 32)],                        # cross stroke
            [(22, 32), (22, 44), (36, 44)],              # left arm and bottom
        ],
    },
    # ── GREEK ────────────────────────────────────────────────────
    {
        'name': 'ALPHA', 'script': 'GREEK', 'concept': 'A',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(20, 48), (32, 20), (44, 48)],              # A shape
            [(25, 38), (39, 38)],                        # crossbar
        ],
    },
    {
        'name': 'OMEGA', 'script': 'GREEK', 'concept': 'LONG O',
        'origin': 'IONIC ~400 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 48), (20, 36), (24, 24), (32, 20),
             (40, 24), (44, 36), (42, 48)],              # horseshoe arc
            [(20, 48), (26, 48)],                        # left foot
            [(38, 48), (44, 48)],                        # right foot
        ],
    },
    {
        'name': 'SIGMA', 'script': 'GREEK', 'concept': 'S',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(42, 22), (20, 22)],                        # top bar
            [(20, 22), (32, 35)],                        # upper diagonal
            [(32, 35), (20, 48)],                        # lower diagonal
            [(20, 48), (42, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'PI', 'script': 'GREEK', 'concept': 'P',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(18, 22), (46, 22)],                        # top bar
            [(24, 22), (24, 48)],                        # left leg
            [(40, 22), (40, 48)],                        # right leg
        ],
    },
    {
        'name': 'PHI', 'script': 'GREEK', 'concept': 'PH',
        'origin': 'ARCHAIC ~700 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical shaft
            [(22, 28), (26, 22), (38, 22), (42, 28),
             (42, 40), (38, 46), (26, 46), (22, 40),
             (22, 28)],                                  # oval
        ],
    },
    # ── CYRILLIC ─────────────────────────────────────────────────
    {
        'name': 'ZHE', 'script': 'CYRILLIC', 'concept': 'ZH',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                        # center vertical
            [(18, 20), (28, 34)],                        # upper-left arm
            [(18, 48), (28, 34)],                        # lower-left arm
            [(46, 20), (36, 34)],                        # upper-right arm
            [(46, 48), (36, 34)],                        # lower-right arm
        ],
    },
    {
        'name': 'SHA', 'script': 'CYRILLIC', 'concept': 'SH',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 22), (20, 48)],                        # left vertical
            [(32, 22), (32, 48)],                        # center vertical
            [(44, 22), (44, 48)],                        # right vertical
            [(20, 48), (44, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'YU', 'script': 'CYRILLIC', 'concept': 'YU',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 22), (20, 48)],                        # left vertical
            [(20, 34), (30, 34)],                        # connecting bar
            [(30, 24), (40, 20), (46, 28), (46, 40),
             (40, 48), (30, 44), (30, 24)],              # right circle
        ],
    },
    {
        'name': 'DE', 'script': 'CYRILLIC', 'concept': 'D',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(24, 48), (24, 26), (40, 26)],              # left side + top
            [(40, 26), (40, 48)],                        # right vertical
            [(20, 48), (44, 48)],                        # bottom bar with serifs
            [(20, 48), (20, 50)],                        # left foot
            [(44, 48), (44, 50)],                        # right foot
        ],
    },
    # ── HEBREW ───────────────────────────────────────────────────
    {
        'name': 'ALEPH', 'script': 'HEBREW', 'concept': 'BREATH',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(20, 46), (44, 22)],                        # main diagonal
            [(20, 22), (28, 30)],                        # upper-left arm
            [(36, 38), (44, 46)],                        # lower-right arm
        ],
    },
    {
        'name': 'SHIN', 'script': 'HEBREW', 'concept': 'SH',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],                        # left prong
            [(32, 22), (32, 48)],                        # center prong
            [(42, 22), (42, 48)],                        # right prong
            [(22, 48), (42, 48)],                        # base bar
        ],
    },
    {
        'name': 'BET', 'script': 'HEBREW', 'concept': 'B / HOUSE',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(40, 22), (40, 48)],                        # right vertical (written R-to-L)
            [(40, 22), (24, 22)],                        # top bar
            [(24, 22), (24, 34), (40, 34)],              # curve to midpoint
            [(24, 48), (44, 48)],                        # base bar
        ],
    },
    {
        'name': 'MEM', 'script': 'HEBREW', 'concept': 'M / WATER',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],                        # top bar
            [(42, 22), (42, 48)],                        # right vertical
            [(42, 48), (22, 48)],                        # bottom bar
            [(22, 48), (22, 36)],                        # left vertical (partial)
            [(22, 36), (30, 28)],                        # inner diagonal
        ],
    },
    # ── EGYPTIAN HIEROGLYPHS ─────────────────────────────────────
    {
        'name': 'EYE OF HORUS', 'script': 'HIEROGLYPH', 'concept': 'PROTECTION',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(18, 32), (26, 28), (38, 28), (46, 32)],   # upper lid
            [(18, 36), (26, 40), (38, 40), (46, 36)],   # lower lid
            [(30, 30), (34, 30), (34, 38), (30, 38), (30, 30)],  # pupil
            [(32, 40), (28, 50)],                        # tear drop
            [(28, 50), (22, 48), (18, 44)],              # spiral tail
        ],
    },
    {
        'name': 'ANKH', 'script': 'HIEROGLYPH', 'concept': 'LIFE',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(26, 26), (32, 20), (38, 26), (32, 32), (26, 26)],  # top loop
            [(32, 32), (32, 50)],                        # vertical shaft
            [(22, 38), (42, 38)],                        # crossbar
        ],
    },
    {
        'name': 'SCARAB', 'script': 'HIEROGLYPH', 'concept': 'REBIRTH',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(26, 30), (38, 30), (40, 36), (38, 42),
             (26, 42), (24, 36), (26, 30)],              # body oval
            [(26, 30), (20, 22)],                        # left antenna
            [(38, 30), (44, 22)],                        # right antenna
            [(24, 36), (16, 32)],                        # left wing tip
            [(40, 36), (48, 32)],                        # right wing tip
            [(30, 42), (26, 50)],                        # left leg
            [(34, 42), (38, 50)],                        # right leg
        ],
    },
    {
        'name': 'REED', 'script': 'HIEROGLYPH', 'concept': 'EGYPT (LAND)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 50)],                        # central stalk
            [(32, 26), (24, 22)],                        # left leaf upper
            [(32, 26), (40, 22)],                        # right leaf upper
            [(32, 34), (22, 30)],                        # left leaf middle
            [(32, 34), (42, 30)],                        # right leaf middle
        ],
    },
    # ── CUNEIFORM ────────────────────────────────────────────────
    {
        'name': 'AN', 'script': 'CUNEIFORM', 'concept': 'SKY / GOD',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (24, 28), (32, 28)],              # top wedge
            [(32, 30), (24, 38), (32, 38)],              # middle wedge
            [(32, 40), (24, 48), (32, 48)],              # bottom wedge
            [(36, 24), (44, 24)],                        # right mark
        ],
    },
    {
        'name': 'KI', 'script': 'CUNEIFORM', 'concept': 'EARTH',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(20, 34), (44, 34)],                        # horizontal
            [(32, 20), (32, 48)],                        # vertical cross
            [(22, 24), (28, 34)],                        # upper-left wedge
            [(42, 24), (36, 34)],                        # upper-right wedge
        ],
    },
    {
        'name': 'DINGIR', 'script': 'CUNEIFORM', 'concept': 'DEITY',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (24, 28), (32, 28)],              # top wedge
            [(32, 30), (24, 38), (32, 38)],              # lower wedge
            [(36, 24), (44, 24)],                        # right mark top
            [(36, 34), (44, 34)],                        # right mark bottom
            [(32, 40), (32, 50)],                        # vertical tail
        ],
    },
    {
        'name': 'LU', 'script': 'CUNEIFORM', 'concept': 'PERSON',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (24, 28), (32, 28)],              # head wedge
            [(28, 30), (28, 48)],                        # left body
            [(36, 30), (36, 48)],                        # right body
            [(28, 38), (36, 38)],                        # waist bar
        ],
    },
    # ── RUNIC ────────────────────────────────────────────────────
    {
        'name': 'FEHU', 'script': 'RUNIC', 'concept': 'WEALTH',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(28, 20), (28, 48)],                        # vertical stave
            [(28, 22), (42, 28)],                        # upper arm
            [(28, 30), (42, 36)],                        # lower arm
        ],
    },
    {
        'name': 'ANSUZ', 'script': 'RUNIC', 'concept': 'GOD / ODIN',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(36, 20), (36, 48)],                        # vertical stave
            [(36, 24), (22, 30)],                        # upper-left angle
            [(36, 34), (22, 40)],                        # lower-left angle
        ],
    },
    {
        'name': 'THURISAZ', 'script': 'RUNIC', 'concept': 'GIANT / THOR',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(26, 20), (26, 48)],                        # vertical stave
            [(26, 26), (40, 34)],                        # upper diagonal out
            [(40, 34), (26, 42)],                        # lower diagonal back
        ],
    },
    {
        'name': 'BERKANA', 'script': 'RUNIC', 'concept': 'BIRCH / GROWTH',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(26, 20), (26, 48)],                        # vertical stave
            [(26, 20), (40, 28), (26, 34)],              # upper triangle
            [(26, 34), (40, 42), (26, 48)],              # lower triangle
        ],
    },
    # ── ARMENIAN ─────────────────────────────────────────────────
    {
        'name': 'AYB', 'script': 'ARMENIAN', 'concept': 'A',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (32, 22), (38, 26)],              # top bar curving right
            [(38, 26), (38, 40)],                        # right vertical
            [(38, 40), (32, 48)],                        # right foot
            [(24, 22), (24, 40)],                        # left vertical
            [(24, 40), (30, 48)],                        # left foot
            [(24, 34), (38, 34)],                        # crossbar
        ],
    },
    {
        'name': 'BEN', 'script': 'ARMENIAN', 'concept': 'B',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (38, 22)],                        # top bar
            [(38, 22), (42, 28), (38, 34)],              # upper bump
            [(38, 34), (24, 34)],                        # middle bar
            [(24, 34), (24, 48)],                        # re-enforce left
            [(24, 48), (38, 48)],                        # bottom bar
        ],
    },
    # ── ETHIOPIC / GE'EZ ─────────────────────────────────────────
    {
        'name': 'HA', 'script': 'ETHIOPIC', 'concept': 'H',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (28, 44)],                        # left vertical
            [(36, 22), (36, 44)],                        # right vertical
            [(28, 22), (36, 22)],                        # top bar
            [(28, 34), (36, 34)],                        # middle bar
            [(28, 44), (24, 48)],                        # left foot
            [(36, 44), (40, 48)],                        # right foot
        ],
    },
    {
        'name': 'LE', 'script': 'ETHIOPIC', 'concept': 'L',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (32, 44)],                        # center vertical
            [(26, 26), (32, 22), (38, 26)],              # crown
            [(32, 44), (26, 48)],                        # left foot
            [(32, 44), (38, 48)],                        # right foot
        ],
    },
    # ── MAYAN ────────────────────────────────────────────────────
    {
        'name': 'AJAW', 'script': 'MAYAN', 'concept': 'LORD / RULER',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(24, 28), (28, 28), (28, 32), (24, 32), (24, 28)],  # left eye
            [(36, 28), (40, 28), (40, 32), (36, 32), (36, 28)],  # right eye
            [(28, 38), (36, 38)],                        # mouth bar
            [(30, 40), (30, 42)],                        # left tooth dot
            [(34, 40), (34, 42)],                        # right tooth dot
        ],
    },
    # ── INUKTITUT (Canadian Aboriginal Syllabics) ────────────────
    {
        'name': 'PI', 'script': 'INUKTITUT', 'concept': 'PI',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(22, 44), (32, 22), (42, 44)],              # triangle pointing up
            [(22, 44), (42, 44)],                        # base bar
        ],
    },
    {
        'name': 'KA', 'script': 'INUKTITUT', 'concept': 'KA',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(22, 22), (42, 22)],                        # top bar
            [(22, 22), (32, 44)],                        # left diagonal down
            [(42, 22), (32, 44)],                        # right diagonal down
        ],
    },
    # ── GEORGIAN ─────────────────────────────────────────────────
    {
        'name': 'ANI', 'script': 'OTHER', 'concept': 'AN (LETTER)',
        'origin': 'GEORGIA ~430 AD',
        'ink': (40, 30, 20), 'paper': (225, 215, 200),
        'strokes': [
            [(24, 24), (24, 44), (32, 48), (40, 44), (40, 24)],  # U-shape
            [(32, 20), (32, 34)],                        # center stem
        ],
    },
    {
        'name': 'BAN', 'script': 'OTHER', 'concept': 'BAN (LETTER)',
        'origin': 'GEORGIA ~430 AD',
        'ink': (40, 30, 20), 'paper': (225, 215, 200),
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 36), (32, 42), (24, 36)],   # right curve back
        ],
    },
    {
        'name': 'GAN', 'script': 'OTHER', 'concept': 'GAN (LETTER)',
        'origin': 'GEORGIA ~430 AD',
        'ink': (40, 30, 20), 'paper': (225, 215, 200),
        'strokes': [
            [(26, 22), (38, 22)],                        # top bar
            [(26, 22), (26, 36), (32, 42), (38, 36), (38, 22)],  # rounded body
            [(32, 42), (32, 50)],                        # descender
        ],
    },
    # ── TIBETAN ──────────────────────────────────────────────────
    {
        'name': 'OM', 'script': 'OTHER', 'concept': 'SACRED SYLLABLE',
        'origin': 'TIBET ~650 AD',
        'ink': (130, 30, 30), 'paper': (225, 220, 200), 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],                        # head bar
            [(26, 22), (26, 36), (20, 44)],              # left descender
            [(38, 22), (38, 36), (44, 44)],              # right descender
            [(26, 36), (38, 36)],                        # middle connector
            [(32, 36), (32, 50)],                        # bottom tail
        ],
    },
    {
        'name': 'KA', 'script': 'OTHER', 'concept': 'KA (CONSONANT)',
        'origin': 'TIBET ~650 AD',
        'ink': (130, 30, 30), 'paper': (225, 220, 200), 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],                        # head bar
            [(32, 22), (32, 42)],                        # center vertical
            [(32, 30), (22, 36)],                        # left arm
            [(32, 42), (26, 50)],                        # left foot
            [(32, 42), (38, 50)],                        # right foot
        ],
    },
    # ── TAMIL ────────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'OTHER', 'concept': 'A (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': (20, 60, 20), 'paper': (225, 220, 210),
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],              # top loop
            [(32, 38), (32, 50)],                        # descender
        ],
    },
    {
        'name': 'KA', 'script': 'OTHER', 'concept': 'KA (CONSONANT)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': (20, 60, 20), 'paper': (225, 220, 210),
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],              # top loop (like A)
            [(32, 38), (32, 44)],                        # short descender
            [(26, 44), (38, 44)],                        # bottom bar
            [(38, 44), (44, 50)],                        # tail
        ],
    },
    # ── CHEROKEE ─────────────────────────────────────────────────
    {
        'name': 'TSA', 'script': 'OTHER', 'concept': 'TSA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': (120, 60, 30), 'paper': (220, 210, 185),
        'strokes': [
            [(20, 22), (44, 22)],                        # top bar
            [(32, 22), (32, 48)],                        # center vertical
            [(20, 36), (44, 36)],                        # middle bar
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'A', 'script': 'OTHER', 'concept': 'A (CHEROKEE)',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': (120, 60, 30), 'paper': (220, 210, 185),
        'strokes': [
            [(20, 48), (32, 20), (44, 48)],              # A-shape outer
            [(26, 38), (38, 38)],                        # crossbar
            [(32, 38), (32, 48)],                        # center leg down
        ],
    },
    # ── MONGOLIAN ────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'OTHER', 'concept': 'A (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': (30, 30, 30), 'paper': (220, 215, 200),
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 22), (38, 26), (38, 32), (32, 36)],   # right curve (tooth)
            [(32, 22), (26, 20)],                        # top serif left
        ],
    },
]

# Build family -> character index mapping
_FAMILY_CHARS = {}
for _i, _ch in enumerate(CHARACTERS):
    _fam = _ch['script']
    if _fam not in FAMILIES:
        _fam = 'OTHER'
    _FAMILY_CHARS.setdefault(_fam, []).append(_i)


def _lerp(a, b, t):
    """Linear interpolate between two (x,y) points."""
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _stroke_total_length(pts):
    """Total pixel distance along a stroke's points."""
    total = 0.0
    for i in range(len(pts) - 1):
        dx = pts[i + 1][0] - pts[i][0]
        dy = pts[i + 1][1] - pts[i][1]
        total += math.sqrt(dx * dx + dy * dy)
    return max(total, 1.0)


def _draw_thick_line(display, x0, y0, x1, y1, color):
    """Draw a line with 2px width by drawing the line plus 1px offsets."""
    display.draw_line(x0, y0, x1, y1, color)
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    if dx >= dy:
        # More horizontal: offset vertically
        display.draw_line(x0, y0 + 1, x1, y1 + 1, color)
    else:
        # More vertical: offset horizontally
        display.draw_line(x0 + 1, y0, x1 + 1, y1, color)


class Scripts(Visual):
    name = "SCRIPTS"
    description = "World writing systems"
    category = "culture"

    def reset(self):
        self.char_idx = 0
        self.family_idx = 0
        self.stroke_idx = 0
        self.stroke_progress = 0.0
        self.hold_timer = 0.0
        self.done_drawing = False
        self.auto_advance = True
        self.overlay_timer = OVERLAY_FADE
        self._input_cooldown = 0.0
        self._sync_family()

    def _sync_family(self):
        """Sync family_idx to match current char_idx."""
        ch = CHARACTERS[self.char_idx]
        fam = ch['script'] if ch['script'] in FAMILIES else 'OTHER'
        if fam in FAMILIES:
            self.family_idx = FAMILIES.index(fam)

    def _chars_in_family(self):
        """Return list of character indices in current family."""
        fam = FAMILIES[self.family_idx]
        return _FAMILY_CHARS.get(fam, [])

    def _start_char(self, idx):
        """Start drawing a new character."""
        self.char_idx = idx % len(CHARACTERS)
        self.stroke_idx = 0
        self.stroke_progress = 0.0
        self.hold_timer = 0.0
        self.done_drawing = False
        self.overlay_timer = OVERLAY_FADE
        self._sync_family()

    def handle_input(self, input_state):
        if self._input_cooldown > 0:
            return False
        up = input_state.up_pressed
        down = input_state.down_pressed
        left = input_state.left_pressed
        right = input_state.right_pressed
        action = input_state.action_l or input_state.action_r

        if up or down:
            step = -1 if up else 1
            self.family_idx = (self.family_idx + step) % len(FAMILIES)
            chars = self._chars_in_family()
            while not chars:
                self.family_idx = (self.family_idx + step) % len(FAMILIES)
                chars = self._chars_in_family()
            self._start_char(chars[0])
            self.auto_advance = False
            self._input_cooldown = 0.15
            return True

        if left or right:
            chars = self._chars_in_family()
            if chars:
                try:
                    pos = chars.index(self.char_idx)
                except ValueError:
                    pos = 0
                step = -1 if left else 1
                pos = (pos + step) % len(chars)
                self._start_char(chars[pos])
            self.auto_advance = False
            self._input_cooldown = 0.15
            return True

        if action:
            self._start_char(self.char_idx + 1)
            self.auto_advance = True
            self._input_cooldown = 0.15
            return True

        return False

    def update(self, dt):
        super().update(dt)
        if self._input_cooldown > 0:
            self._input_cooldown -= dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        ch = CHARACTERS[self.char_idx]
        strokes = ch['strokes']

        if self.done_drawing:
            # Hold, then auto-advance
            self.hold_timer += dt
            if self.auto_advance and self.hold_timer >= HOLD_DURATION:
                self._start_char(self.char_idx + 1)
            return

        # Advance stroke progress
        self.stroke_progress += dt / STROKE_DURATION
        if self.stroke_progress >= 1.0:
            self.stroke_progress = 0.0
            self.stroke_idx += 1
            if self.stroke_idx >= len(strokes):
                self.done_drawing = True
                self.stroke_idx = len(strokes) - 1
                self.stroke_progress = 1.0

    def _draw_stroke_line(self, x0, y0, x1, y1, ink, thick):
        """Draw a stroke segment, optionally with 2px thickness."""
        if thick:
            _draw_thick_line(self.display, x0, y0, x1, y1, ink)
        else:
            self.display.draw_line(x0, y0, x1, y1, ink)

    def draw(self):
        d = self.display
        d.clear()

        ch = CHARACTERS[self.char_idx]
        strokes = ch['strokes']
        ink = ch['ink']
        paper = ch['paper']
        thick = ch.get('thick', False)

        # Border color (slightly darker than paper)
        border = (max(0, paper[0] - 40), max(0, paper[1] - 40),
                  max(0, paper[2] - 40))

        # Draw paper background
        d.draw_rect(PAPER_X0, PAPER_Y0, PAPER_W, PAPER_H, paper)

        # Draw border
        for x in range(PAPER_X0, PAPER_X1):
            d.set_pixel(x, PAPER_Y0, border)
            d.set_pixel(x, PAPER_Y1 - 1, border)
        for y in range(PAPER_Y0, PAPER_Y1):
            d.set_pixel(PAPER_X0, y, border)
            d.set_pixel(PAPER_X1 - 1, y, border)

        # Draw completed strokes
        for si in range(min(self.stroke_idx, len(strokes))):
            pts = strokes[si]
            for j in range(len(pts) - 1):
                self._draw_stroke_line(
                    pts[j][0], pts[j][1],
                    pts[j + 1][0], pts[j + 1][1], ink, thick)

        # Draw current stroke in progress
        if self.stroke_idx < len(strokes):
            pts = strokes[self.stroke_idx]
            total_len = _stroke_total_length(pts)
            target_len = total_len * self.stroke_progress

            accum = 0.0
            for j in range(len(pts) - 1):
                seg_dx = pts[j + 1][0] - pts[j][0]
                seg_dy = pts[j + 1][1] - pts[j][1]
                seg_len = math.sqrt(seg_dx * seg_dx + seg_dy * seg_dy)

                if accum + seg_len <= target_len:
                    # Draw full segment
                    self._draw_stroke_line(
                        pts[j][0], pts[j][1],
                        pts[j + 1][0], pts[j + 1][1], ink, thick)
                    accum += seg_len
                else:
                    # Partial segment
                    remain = target_len - accum
                    t = remain / max(seg_len, 0.01)
                    ex, ey = _lerp(pts[j], pts[j + 1], t)
                    self._draw_stroke_line(
                        pts[j][0], pts[j][1],
                        int(ex), int(ey), ink, thick)
                    break

        # Header text
        fam = FAMILIES[self.family_idx]
        concept = ch['concept']
        header = fam + ' / ' + concept
        d.draw_text_small(2, 1, header, WHITE)

        # Origin line at bottom
        origin = ch['origin']
        d.draw_text_small(2, 59, origin, VERY_DIM)

        # Character name at y=7
        char_label = ch['name']
        d.draw_text_small(2, 7, char_label, DIM_GRAY)

        # Overlay on character change
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            # Draw overlay info with fading
            ol_r = int(255 * alpha)
            ol_g = int(255 * alpha)
            ol_b = int(255 * alpha)
            ol_color = (ol_r, ol_g, ol_b)

            # Family index indicator
            chars_in_fam = self._chars_in_family()
            if chars_in_fam:
                try:
                    pos = chars_in_fam.index(self.char_idx) + 1
                except ValueError:
                    pos = 1
                count_str = str(pos) + '/' + str(len(chars_in_fam))
                d.draw_text_small(46, 7, count_str, (
                    int(100 * alpha), int(100 * alpha), int(110 * alpha)))

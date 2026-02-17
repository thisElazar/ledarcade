"""
SCRIPTS - World Writing Systems
================================
Stroke-by-stroke animated display of 830+ characters across 27 writing
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
    'PHOENICIAN', 'HEBREW', 'ARABIC', 'GREEK', 'CYRILLIC',
    'RUNIC', 'OGHAM', 'ARMENIAN', 'GEORGIAN',
    'DEVANAGARI', 'TAMIL', 'BENGALI', 'TIBETAN', 'THAI',
    'KOREAN', 'HIRAGANA', 'KATAKANA', 'CHINESE',
    'ETHIOPIC', 'TIFINAGH', 'NKO',
    'CHEROKEE', 'INUKTITUT', 'MONGOLIAN',
    'HIEROGLYPH', 'CUNEIFORM', 'MAYAN',
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
_PHOEN_INK = (90, 50, 25)
_PHOEN_PAPER = (210, 190, 155)
_OGHAM_INK = (30, 40, 25)
_OGHAM_PAPER = (190, 185, 165)
_TIFI_INK = (50, 35, 100)
_TIFI_PAPER = (215, 205, 180)
_GEORGIAN_INK = (40, 30, 20)
_GEORGIAN_PAPER = (225, 215, 200)
_BENGALI_INK = (140, 40, 25)
_BENGALI_PAPER = (230, 225, 205)
_TAMIL_INK = (20, 60, 20)
_TAMIL_PAPER = (225, 220, 210)
_TIBETAN_INK = (130, 30, 30)
_TIBETAN_PAPER = (225, 220, 200)
_THAI_INK = (80, 30, 100)
_THAI_PAPER = (230, 225, 215)
_CHEROKEE_INK = (120, 60, 30)
_CHEROKEE_PAPER = (220, 210, 185)
_NKO_INK = (50, 30, 20)
_NKO_PAPER = (225, 215, 185)
_MONGOLIAN_INK = (30, 30, 30)
_MONGOLIAN_PAPER = (220, 215, 200)

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
        'name': 'A', 'script': 'HIRAGANA', 'concept': 'AH',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                        # top horizontal
            [(32, 20), (32, 36)],                        # center vertical
            [(22, 32), (28, 40), (38, 46), (44, 40)],   # bottom curve
        ],
    },
    {
        'name': 'KA', 'script': 'HIRAGANA', 'concept': 'KA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 24), (44, 24)],                        # top horizontal
            [(36, 20), (30, 32), (24, 48)],              # left diagonal
            [(36, 28), (42, 38), (40, 48)],              # right curve
        ],
    },
    {
        'name': 'SA', 'script': 'HIRAGANA', 'concept': 'SA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                        # top bar
            [(22, 32), (42, 32)],                        # middle bar
            [(36, 24), (30, 40), (24, 50)],              # sweeping curve
        ],
    },
    {
        'name': 'NO', 'script': 'HIRAGANA', 'concept': 'NO (PARTICLE)',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(38, 22), (28, 26), (22, 34), (24, 42),
             (32, 48), (42, 44), (44, 36), (38, 28)],   # spiraling loop (like の)
        ],
    },
    # ── HIRAGANA (continued) ────────────────────────────────────
    {
        'name': 'I', 'script': 'HIRAGANA', 'concept': 'I',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (24, 30), (22, 40), (24, 48)],
            [(38, 22), (36, 32), (38, 44), (40, 48)],
        ],
    },
    {
        'name': 'U', 'script': 'HIRAGANA', 'concept': 'U',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(30, 20), (32, 22)],
            [(34, 24), (32, 32), (28, 40), (30, 46), (36, 48)],
        ],
    },
    {
        'name': 'E', 'script': 'HIRAGANA', 'concept': 'E',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(34, 26), (30, 34), (24, 40), (28, 46), (36, 48), (42, 44)],
        ],
    },
    {
        'name': 'O', 'script': 'HIRAGANA', 'concept': 'O',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(34, 20), (34, 48)],
            [(34, 34), (28, 40), (24, 46), (28, 50), (36, 46), (40, 40)],
        ],
    },
    {
        'name': 'KI', 'script': 'HIRAGANA', 'concept': 'KI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(22, 32), (42, 32)],
            [(36, 20), (32, 36)],
            [(30, 38), (28, 44), (32, 48), (38, 46)],
        ],
    },
    {
        'name': 'KU', 'script': 'HIRAGANA', 'concept': 'KU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 20), (28, 34), (40, 48)],
        ],
    },
    {
        'name': 'KE', 'script': 'HIRAGANA', 'concept': 'KE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 30), (36, 28)],
            [(38, 20), (36, 32), (34, 42), (38, 48)],
        ],
    },
    {
        'name': 'KO', 'script': 'HIRAGANA', 'concept': 'KO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],
            [(22, 42), (42, 42)],
        ],
    },
    {
        'name': 'SHI', 'script': 'HIRAGANA', 'concept': 'SHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(30, 20), (28, 30), (26, 40), (28, 46), (34, 48), (40, 44)],
        ],
    },
    {
        'name': 'SU', 'script': 'HIRAGANA', 'concept': 'SU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(34, 26), (30, 34), (26, 40), (30, 46), (36, 44), (34, 38)],
        ],
    },
    {
        'name': 'SE', 'script': 'HIRAGANA', 'concept': 'SE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],
            [(34, 22), (34, 46)],
            [(26, 38), (24, 44), (28, 48), (36, 48), (40, 44)],
        ],
    },
    {
        'name': 'SO', 'script': 'HIRAGANA', 'concept': 'SO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(34, 24), (28, 32), (34, 40), (40, 46), (42, 48)],
        ],
    },
    {
        'name': 'TA', 'script': 'HIRAGANA', 'concept': 'TA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(34, 20), (30, 34)],
            [(22, 34), (42, 34)],
            [(34, 34), (30, 42), (34, 48), (40, 44)],
        ],
    },
    {
        'name': 'CHI', 'script': 'HIRAGANA', 'concept': 'CHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(38, 26), (34, 34), (26, 40), (22, 48)],
        ],
    },
    {
        'name': 'TSU', 'script': 'HIRAGANA', 'concept': 'TSU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 28), (28, 32), (36, 32), (44, 26)],
        ],
    },
    {
        'name': 'TE', 'script': 'HIRAGANA', 'concept': 'TE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 26), (44, 26)],
            [(32, 26), (30, 34), (28, 42), (32, 48), (40, 46)],
        ],
    },
    {
        'name': 'TO', 'script': 'HIRAGANA', 'concept': 'TO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(28, 22), (28, 48)],
            [(28, 32), (36, 34), (42, 38)],
        ],
    },
    {
        'name': 'NA', 'script': 'HIRAGANA', 'concept': 'NA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(34, 20), (30, 34)],
            [(28, 34), (24, 40), (28, 46), (34, 44), (32, 38)],
            [(38, 34), (40, 42), (42, 48)],
        ],
    },
    {
        'name': 'NI', 'script': 'HIRAGANA', 'concept': 'NI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(30, 28), (40, 30)],
            [(30, 40), (40, 42)],
        ],
    },
    {
        'name': 'NU', 'script': 'HIRAGANA', 'concept': 'NU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],
            [(36, 28), (28, 36), (24, 42), (28, 48), (36, 46), (40, 40), (36, 34)],
        ],
    },
    {
        'name': 'NE', 'script': 'HIRAGANA', 'concept': 'NE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 30), (38, 28)],
            [(38, 28), (34, 36), (28, 42), (32, 48), (40, 46), (42, 40)],
        ],
    },
    {
        'name': 'HA', 'script': 'HIRAGANA', 'concept': 'HA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 30), (38, 28)],
            [(38, 22), (36, 34), (30, 42), (34, 48), (42, 44)],
        ],
    },
    {
        'name': 'HI', 'script': 'HIRAGANA', 'concept': 'HI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (32, 28), (24, 36), (32, 42), (40, 46)],
        ],
    },
    {
        'name': 'FU', 'script': 'HIRAGANA', 'concept': 'FU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(28, 22), (30, 24)],
            [(36, 22), (34, 24)],
            [(32, 28), (26, 36), (28, 44), (36, 48), (42, 42)],
        ],
    },
    {
        'name': 'HE', 'script': 'HIRAGANA', 'concept': 'HE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 38), (32, 26), (44, 38)],
        ],
    },
    {
        'name': 'HO', 'script': 'HIRAGANA', 'concept': 'HO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(24, 20), (24, 48)],
            [(24, 34), (40, 34)],
            [(36, 34), (34, 42), (38, 48), (44, 44)],
        ],
    },
    {
        'name': 'MA', 'script': 'HIRAGANA', 'concept': 'MA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(34, 20), (34, 42)],
            [(34, 34), (28, 40), (30, 48), (38, 46), (36, 38)],
        ],
    },
    {
        'name': 'MI', 'script': 'HIRAGANA', 'concept': 'MI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (36, 22), (40, 28), (30, 32)],
            [(24, 36), (36, 34), (40, 40), (34, 46), (24, 48)],
        ],
    },
    {
        'name': 'MU', 'script': 'HIRAGANA', 'concept': 'MU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(34, 26), (28, 34), (24, 42), (28, 48), (36, 46), (40, 40)],
            [(36, 32), (38, 34)],
        ],
    },
    {
        'name': 'ME', 'script': 'HIRAGANA', 'concept': 'ME',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(36, 20), (28, 30), (24, 38), (28, 46), (36, 48), (42, 42), (38, 34)],
        ],
    },
    {
        'name': 'MO', 'script': 'HIRAGANA', 'concept': 'MO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(22, 34), (42, 34)],
            [(32, 22), (32, 42), (34, 48)],
        ],
    },
    {
        'name': 'YA', 'script': 'HIRAGANA', 'concept': 'YA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(36, 20), (30, 36)],
            [(30, 36), (28, 44), (34, 48), (42, 44)],
        ],
    },
    {
        'name': 'YU', 'script': 'HIRAGANA', 'concept': 'YU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (24, 44), (30, 48), (38, 44)],
            [(38, 28), (42, 44)],
        ],
    },
    {
        'name': 'YO', 'script': 'HIRAGANA', 'concept': 'YO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(34, 22), (34, 48)],
            [(22, 38), (34, 38)],
        ],
    },
    {
        'name': 'RA', 'script': 'HIRAGANA', 'concept': 'RA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 26), (38, 26)],
            [(34, 26), (30, 34), (26, 42), (30, 48), (38, 46)],
        ],
    },
    {
        'name': 'RI', 'script': 'HIRAGANA', 'concept': 'RI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (24, 32), (26, 42), (30, 46)],
            [(38, 22), (36, 34), (38, 44), (40, 48)],
        ],
    },
    {
        'name': 'RU', 'script': 'HIRAGANA', 'concept': 'RU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 26), (38, 26)],
            [(34, 26), (30, 36), (28, 44), (32, 48), (38, 46), (36, 40)],
        ],
    },
    {
        'name': 'RE', 'script': 'HIRAGANA', 'concept': 'RE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 30), (36, 28), (40, 34), (36, 42), (28, 46), (32, 50), (40, 48)],
        ],
    },
    {
        'name': 'RO', 'script': 'HIRAGANA', 'concept': 'RO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 26), (38, 26)],
            [(34, 26), (30, 36), (26, 44), (30, 50)],
        ],
    },
    {
        'name': 'WA', 'script': 'HIRAGANA', 'concept': 'WA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 30), (38, 28)],
            [(38, 28), (36, 36), (30, 42), (34, 48), (42, 44)],
        ],
    },
    {
        'name': 'WO', 'script': 'HIRAGANA', 'concept': 'WO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(22, 32), (42, 32)],
            [(36, 24), (32, 38), (28, 44), (34, 48), (42, 44)],
        ],
    },
    {
        'name': 'N', 'script': 'HIRAGANA', 'concept': 'N',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(30, 20), (28, 30), (26, 40), (30, 48), (36, 44), (34, 36), (28, 30)],
        ],
    },
    # ── KATAKANA ────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'KATAKANA', 'concept': 'A',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(36, 20), (28, 48)],
        ],
    },
    {
        'name': 'I', 'script': 'KATAKANA', 'concept': 'I',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(36, 20), (28, 34)],
            [(36, 20), (38, 48)],
        ],
    },
    {
        'name': 'U', 'script': 'KATAKANA', 'concept': 'U',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(32, 20), (32, 22)],
            [(22, 28), (42, 28)],
            [(22, 28), (22, 46)],
            [(42, 28), (42, 46)],
        ],
    },
    {
        'name': 'E', 'script': 'KATAKANA', 'concept': 'E',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(32, 24), (32, 46)],
            [(22, 46), (42, 46)],
        ],
    },
    {
        'name': 'O', 'script': 'KATAKANA', 'concept': 'O',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],
            [(34, 20), (34, 48)],
            [(34, 34), (22, 46)],
        ],
    },
    {
        'name': 'KA', 'script': 'KATAKANA', 'concept': 'KA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(36, 20), (36, 48)],
            [(22, 26), (36, 26)],
            [(36, 32), (22, 48)],
        ],
    },
    {
        'name': 'KI', 'script': 'KATAKANA', 'concept': 'KI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(22, 36), (42, 36)],
            [(36, 20), (28, 48)],
        ],
    },
    {
        'name': 'KU', 'script': 'KATAKANA', 'concept': 'KU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 22), (22, 34)],
            [(22, 34), (40, 48)],
        ],
    },
    {
        'name': 'KE', 'script': 'KATAKANA', 'concept': 'KE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 42)],
            [(24, 28), (42, 28)],
            [(40, 22), (36, 48)],
        ],
    },
    {
        'name': 'KO', 'script': 'KATAKANA', 'concept': 'KO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(42, 24), (42, 46)],
            [(22, 46), (42, 46)],
        ],
    },
    {
        'name': 'SA', 'script': 'KATAKANA', 'concept': 'SA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(22, 36), (42, 36)],
            [(36, 22), (28, 48)],
        ],
    },
    {
        'name': 'SHI', 'script': 'KATAKANA', 'concept': 'SHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (24, 26)],
            [(22, 34), (24, 36)],
            [(38, 26), (36, 36), (38, 44), (42, 48)],
        ],
    },
    {
        'name': 'SU', 'script': 'KATAKANA', 'concept': 'SU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(38, 26), (22, 48)],
        ],
    },
    {
        'name': 'SE', 'script': 'KATAKANA', 'concept': 'SE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(34, 20), (34, 48)],
            [(22, 30), (44, 30)],
            [(22, 30), (22, 44)],
        ],
    },
    {
        'name': 'SO', 'script': 'KATAKANA', 'concept': 'SO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (28, 24)],
            [(36, 24), (32, 36), (34, 46), (40, 48)],
        ],
    },
    {
        'name': 'TA', 'script': 'KATAKANA', 'concept': 'TA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(36, 20), (28, 48)],
            [(36, 32), (42, 48)],
        ],
    },
    {
        'name': 'CHI', 'script': 'KATAKANA', 'concept': 'CHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(32, 26), (22, 38), (26, 46), (36, 48), (42, 42)],
        ],
    },
    {
        'name': 'TSU', 'script': 'KATAKANA', 'concept': 'TSU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 22), (24, 24)],
            [(32, 22), (34, 24)],
            [(40, 24), (34, 36), (36, 46), (42, 48)],
        ],
    },
    {
        'name': 'TE', 'script': 'KATAKANA', 'concept': 'TE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 24), (44, 24)],
            [(22, 36), (42, 36)],
            [(32, 36), (32, 48)],
        ],
    },
    {
        'name': 'TO', 'script': 'KATAKANA', 'concept': 'TO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(28, 20), (28, 48)],
            [(28, 30), (42, 38)],
        ],
    },
    {
        'name': 'NA', 'script': 'KATAKANA', 'concept': 'NA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(36, 20), (22, 48)],
        ],
    },
    {
        'name': 'NI', 'script': 'KATAKANA', 'concept': 'NI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],
            [(22, 44), (42, 44)],
        ],
    },
    {
        'name': 'NU', 'script': 'KATAKANA', 'concept': 'NU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(38, 26), (24, 44), (28, 48), (36, 44)],
        ],
    },
    {
        'name': 'NE', 'script': 'KATAKANA', 'concept': 'NE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],
            [(24, 28), (42, 28)],
            [(24, 38), (42, 38)],
            [(42, 28), (42, 48)],
        ],
    },
    {
        'name': 'NO', 'script': 'KATAKANA', 'concept': 'NO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 20), (24, 48)],
        ],
    },
    {
        'name': 'HA', 'script': 'KATAKANA', 'concept': 'HA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (36, 34)],
            [(40, 24), (28, 48)],
        ],
    },
    {
        'name': 'HI', 'script': 'KATAKANA', 'concept': 'HI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 26), (42, 30)],
            [(24, 42), (42, 38)],
            [(42, 30), (42, 38)],
        ],
    },
    {
        'name': 'FU', 'script': 'KATAKANA', 'concept': 'FU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(30, 24), (22, 48)],
        ],
    },
    {
        'name': 'HE', 'script': 'KATAKANA', 'concept': 'HE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 38), (32, 26), (44, 38)],
        ],
    },
    {
        'name': 'HO', 'script': 'KATAKANA', 'concept': 'HO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(24, 20), (24, 48)],
            [(24, 36), (42, 36)],
            [(42, 24), (42, 48)],
        ],
    },
    {
        'name': 'MA', 'script': 'KATAKANA', 'concept': 'MA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(22, 36), (42, 36)],
            [(38, 22), (26, 48)],
        ],
    },
    {
        'name': 'MI', 'script': 'KATAKANA', 'concept': 'MI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (40, 26)],
            [(24, 34), (40, 36)],
            [(24, 44), (40, 46)],
        ],
    },
    {
        'name': 'MU', 'script': 'KATAKANA', 'concept': 'MU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 20), (22, 42), (32, 48), (42, 42)],
            [(42, 20), (42, 42)],
        ],
    },
    {
        'name': 'ME', 'script': 'KATAKANA', 'concept': 'ME',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 20), (24, 48)],
            [(24, 30), (42, 40)],
        ],
    },
    {
        'name': 'MO', 'script': 'KATAKANA', 'concept': 'MO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(22, 36), (42, 36)],
            [(32, 22), (32, 48)],
        ],
    },
    {
        'name': 'YA', 'script': 'KATAKANA', 'concept': 'YA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(36, 20), (28, 48)],
            [(36, 30), (44, 48)],
        ],
    },
    {
        'name': 'YU', 'script': 'KATAKANA', 'concept': 'YU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(22, 24), (22, 46)],
            [(22, 46), (42, 46)],
        ],
    },
    {
        'name': 'YO', 'script': 'KATAKANA', 'concept': 'YO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(22, 36), (42, 36)],
            [(42, 24), (42, 48)],
        ],
    },
    {
        'name': 'RA', 'script': 'KATAKANA', 'concept': 'RA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],
            [(22, 26), (22, 48)],
            [(22, 48), (42, 48)],
        ],
    },
    {
        'name': 'RI', 'script': 'KATAKANA', 'concept': 'RI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (26, 44)],
            [(38, 22), (38, 44)],
        ],
    },
    {
        'name': 'RU', 'script': 'KATAKANA', 'concept': 'RU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 22), (22, 42), (32, 48)],
            [(42, 22), (42, 42), (32, 48)],
        ],
    },
    {
        'name': 'RE', 'script': 'KATAKANA', 'concept': 'RE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 22), (42, 28)],
        ],
    },
    {
        'name': 'RO', 'script': 'KATAKANA', 'concept': 'RO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(22, 24), (22, 46)],
            [(22, 46), (42, 46)],
        ],
    },
    {
        'name': 'WA', 'script': 'KATAKANA', 'concept': 'WA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 46)],
            [(24, 26), (42, 26)],
            [(42, 26), (42, 36), (36, 46)],
        ],
    },
    {
        'name': 'WO', 'script': 'KATAKANA', 'concept': 'WO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],
            [(22, 34), (42, 34)],
            [(36, 24), (28, 48)],
        ],
    },
    {
        'name': 'N', 'script': 'KATAKANA', 'concept': 'N',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (26, 24)],
            [(36, 26), (32, 38), (36, 46), (42, 48)],
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
    {
        'name': 'RA', 'script': 'KOREAN', 'concept': 'RA / LA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 30)],                        # right drop
            [(40, 30), (20, 30)],                        # middle bar left
            [(20, 30), (20, 38)],                        # left drop
            [(20, 38), (40, 38)],                        # bottom bar
        ],
    },
    {
        'name': 'MA', 'script': 'KOREAN', 'concept': 'MA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 22), (40, 22)],                        # top bar
            [(20, 22), (20, 46)],                        # left vertical
            [(40, 22), (40, 46)],                        # right vertical
            [(20, 46), (40, 46)],                        # bottom bar
        ],
    },
    {
        'name': 'BA', 'script': 'KOREAN', 'concept': 'BA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 22), (22, 46)],                        # left vertical
            [(38, 22), (38, 46)],                        # right vertical
            [(22, 22), (38, 22)],                        # top bar
            [(22, 34), (38, 34)],                        # middle bar
            [(22, 46), (38, 46)],                        # bottom bar
        ],
    },
    {
        'name': 'SA', 'script': 'KOREAN', 'concept': 'SA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 46), (30, 22)],                        # left diagonal up
            [(30, 22), (40, 46)],                        # right diagonal down
        ],
    },
    {
        'name': 'IEUNG', 'script': 'KOREAN', 'concept': 'AH (SILENT)',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(24, 26), (30, 22), (36, 26), (38, 34),
             (34, 40), (26, 40), (22, 34), (24, 26)],   # circle
        ],
    },
    {
        'name': 'JA', 'script': 'KOREAN', 'concept': 'JA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 26), (44, 26)],                        # top bar
            [(24, 46), (32, 28)],                        # left diagonal up
            [(32, 28), (40, 46)],                        # right diagonal down
        ],
    },
    {
        'name': 'CHA', 'script': 'KOREAN', 'concept': 'CHA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 20), (44, 20)],                        # top hat bar
            [(20, 28), (44, 28)],                        # second bar
            [(24, 48), (32, 30)],                        # left diagonal up
            [(32, 30), (40, 48)],                        # right diagonal down
        ],
    },
    {
        'name': 'KA', 'script': 'KOREAN', 'concept': 'KA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],                        # left vertical
            [(22, 22), (40, 22)],                        # top bar
            [(22, 34), (40, 34)],                        # middle bar
            [(22, 46), (40, 46)],                        # bottom bar (extra)
        ],
    },
    {
        'name': 'TA', 'script': 'KOREAN', 'concept': 'TA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 22), (40, 22)],                        # top bar
            [(22, 22), (22, 46)],                        # left vertical
            [(22, 34), (40, 34)],                        # middle bar
            [(22, 46), (40, 46)],                        # bottom bar (extra)
        ],
    },
    {
        'name': 'PA', 'script': 'KOREAN', 'concept': 'PA',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                        # left vertical
            [(38, 20), (38, 48)],                        # right vertical
            [(22, 20), (38, 20)],                        # top bar
            [(22, 30), (38, 30)],                        # upper-mid bar
            [(22, 40), (38, 40)],                        # lower-mid bar
            [(22, 48), (38, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'HIEUT', 'script': 'KOREAN', 'concept': 'H',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(22, 20), (42, 20)],                        # top hat bar
            [(28, 20), (28, 28)],                        # hat left leg
            [(36, 20), (36, 28)],                        # hat right leg
            [(24, 28), (40, 28)],                        # bar below hat
            [(26, 34), (32, 32), (38, 34), (38, 42),
             (32, 46), (26, 42), (26, 34)],              # circle body
        ],
    },
    {
        'name': 'A', 'script': 'KOREAN', 'concept': 'A VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(28, 20), (28, 48)],                        # vertical line
            [(28, 34), (40, 34)],                        # horizontal tick right
        ],
    },
    {
        'name': 'YA', 'script': 'KOREAN', 'concept': 'YA VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(26, 20), (26, 48)],                        # vertical line
            [(26, 30), (40, 30)],                        # upper tick right
            [(26, 38), (40, 38)],                        # lower tick right
        ],
    },
    {
        'name': 'EO', 'script': 'KOREAN', 'concept': 'EO VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(36, 20), (36, 48)],                        # vertical line
            [(36, 34), (24, 34)],                        # horizontal tick left
        ],
    },
    {
        'name': 'YEO', 'script': 'KOREAN', 'concept': 'YEO VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(38, 20), (38, 48)],                        # vertical line
            [(38, 30), (24, 30)],                        # upper tick left
            [(38, 38), (24, 38)],                        # lower tick left
        ],
    },
    {
        'name': 'O', 'script': 'KOREAN', 'concept': 'O VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 36), (44, 36)],                        # horizontal line
            [(32, 36), (32, 22)],                        # vertical tick up
        ],
    },
    {
        'name': 'YO', 'script': 'KOREAN', 'concept': 'YO VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 38), (44, 38)],                        # horizontal line
            [(28, 38), (28, 22)],                        # left tick up
            [(36, 38), (36, 22)],                        # right tick up
        ],
    },
    {
        'name': 'U', 'script': 'KOREAN', 'concept': 'U VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 30), (44, 30)],                        # horizontal line
            [(32, 30), (32, 46)],                        # vertical tick down
        ],
    },
    {
        'name': 'YU', 'script': 'KOREAN', 'concept': 'YU VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 30), (44, 30)],                        # horizontal line
            [(28, 30), (28, 46)],                        # left tick down
            [(36, 30), (36, 46)],                        # right tick down
        ],
    },
    {
        'name': 'EU', 'script': 'KOREAN', 'concept': 'EU VOWEL',
        'origin': 'SEJONG 1443 AD',
        'ink': _KOREAN_INK, 'paper': _KOREAN_PAPER,
        'strokes': [
            [(20, 34), (44, 34)],                        # single horizontal line
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
    {
        'name': 'THA', 'script': 'ARABIC', 'concept': 'TH',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(20, 36), (26, 30), (38, 30), (44, 36)],   # boat shape
            [(28, 22), (28, 24)],                        # dot 1 above
            [(32, 20), (32, 22)],                        # dot 2 above
            [(36, 22), (36, 24)],                        # dot 3 above
        ],
    },
    {
        'name': 'HA', 'script': 'ARABIC', 'concept': 'H',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(22, 24), (42, 24)],                        # top bar
            [(42, 24), (42, 38)],                        # right descender
            [(42, 38), (32, 44), (22, 38)],              # bowl curve
        ],
    },
    {
        'name': 'KHA', 'script': 'ARABIC', 'concept': 'KH',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(22, 28), (42, 28)],                        # top bar
            [(42, 28), (42, 40)],                        # right descender
            [(42, 40), (32, 46), (22, 40)],              # bowl curve
            [(32, 22), (32, 24)],                        # dot above
        ],
    },
    {
        'name': 'DAL', 'script': 'ARABIC', 'concept': 'D',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(38, 24), (34, 24), (30, 28), (28, 36)],   # small hook/curve
        ],
    },
    {
        'name': 'DHAL', 'script': 'ARABIC', 'concept': 'DH',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(38, 28), (34, 28), (30, 32), (28, 40)],   # small hook/curve
            [(34, 22), (34, 24)],                        # dot above
        ],
    },
    {
        'name': 'RA', 'script': 'ARABIC', 'concept': 'R',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(36, 30), (32, 34), (28, 42), (26, 48)],   # small descending curve
        ],
    },
    {
        'name': 'ZAY', 'script': 'ARABIC', 'concept': 'Z',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(36, 32), (32, 36), (28, 44), (26, 50)],   # descending curve
            [(32, 26), (32, 28)],                        # dot above
        ],
    },
    {
        'name': 'SIN', 'script': 'ARABIC', 'concept': 'S',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(18, 40), (22, 34), (26, 40), (30, 34),
             (34, 40), (38, 34), (44, 40)],              # three teeth
        ],
    },
    {
        'name': 'SHIN', 'script': 'ARABIC', 'concept': 'SH',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(18, 42), (22, 36), (26, 42), (30, 36),
             (34, 42), (38, 36), (44, 42)],              # three teeth
            [(28, 28), (28, 30)],                        # dot 1 above
            [(32, 26), (32, 28)],                        # dot 2 above
            [(36, 28), (36, 30)],                        # dot 3 above
        ],
    },
    {
        'name': 'SAD', 'script': 'ARABIC', 'concept': 'S (EMPHATIC)',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(18, 38), (22, 32), (26, 38), (30, 32),
             (34, 38)],                                  # teeth
            [(34, 38), (40, 32), (44, 28), (44, 34),
             (40, 38), (34, 38)],                        # closing loop
        ],
    },
    {
        'name': 'DAD', 'script': 'ARABIC', 'concept': 'D (EMPHATIC)',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(18, 40), (22, 34), (26, 40), (30, 34),
             (34, 40)],                                  # teeth
            [(34, 40), (40, 34), (44, 30), (44, 36),
             (40, 40), (34, 40)],                        # closing loop
            [(36, 24), (36, 26)],                        # dot above
        ],
    },
    {
        'name': 'TAH', 'script': 'ARABIC', 'concept': 'T (EMPHATIC)',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(22, 42), (22, 36), (32, 32), (42, 36),
             (42, 42), (32, 46), (22, 42)],              # base loop
            [(32, 22), (32, 32)],                        # tall vertical on top
        ],
    },
    {
        'name': 'ZAH', 'script': 'ARABIC', 'concept': 'Z (EMPHATIC)',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(22, 42), (22, 36), (32, 32), (42, 36),
             (42, 42), (32, 46), (22, 42)],              # base loop
            [(32, 24), (32, 32)],                        # tall vertical
            [(36, 20), (36, 22)],                        # dot above
        ],
    },
    {
        'name': 'AIN', 'script': 'ARABIC', 'concept': 'GUTTURAL STOP',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(36, 22), (28, 26), (26, 34), (30, 40),
             (36, 36)],                                  # teardrop/reversed C
            [(30, 40), (26, 48)],                        # tail descending
        ],
    },
    {
        'name': 'GHAIN', 'script': 'ARABIC', 'concept': 'GH',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(36, 26), (28, 30), (26, 38), (30, 44),
             (36, 40)],                                  # teardrop body
            [(30, 44), (26, 50)],                        # tail descending
            [(32, 22), (32, 24)],                        # dot above
        ],
    },
    {
        'name': 'FA', 'script': 'ARABIC', 'concept': 'F',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(28, 36), (32, 30), (38, 30), (42, 34),
             (38, 38), (32, 38), (28, 36)],              # small loop
            [(28, 36), (22, 42)],                        # tail
            [(34, 24), (34, 26)],                        # dot above
        ],
    },
    {
        'name': 'QAF', 'script': 'ARABIC', 'concept': 'Q',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(24, 38), (30, 30), (38, 30), (44, 36),
             (38, 42), (30, 42), (24, 38)],              # bigger loop
            [(24, 38), (20, 48)],                        # tail descending
            [(32, 24), (32, 26)],                        # dot 1 above
            [(38, 24), (38, 26)],                        # dot 2 above
        ],
    },
    {
        'name': 'KAF', 'script': 'ARABIC', 'concept': 'K',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(42, 44), (42, 24)],                        # tall right vertical
            [(42, 44), (24, 44)],                        # bottom bar
            [(30, 34), (34, 30), (38, 34)],              # small zigzag inside
        ],
    },
    {
        'name': 'LAM', 'script': 'ARABIC', 'concept': 'L',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(34, 20), (34, 40), (28, 48)],              # tall vertical curving at bottom
        ],
    },
    {
        'name': 'MIM', 'script': 'ARABIC', 'concept': 'M',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(28, 32), (34, 28), (40, 32), (36, 38),
             (28, 38), (28, 32)],                        # small circle
            [(28, 38), (24, 44)],                        # short tail
        ],
    },
    {
        'name': 'NUN', 'script': 'ARABIC', 'concept': 'N',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(20, 38), (26, 32), (38, 32), (44, 38)],   # boat shape
            [(32, 26), (32, 28)],                        # dot above
        ],
    },
    {
        'name': 'WAW', 'script': 'ARABIC', 'concept': 'W',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(30, 28), (36, 24), (40, 28), (38, 34),
             (32, 36), (30, 28)],                        # small circle head
            [(32, 36), (28, 46)],                        # tail going down
        ],
    },
    {
        'name': 'YA', 'script': 'ARABIC', 'concept': 'Y',
        'origin': 'NABATAEAN ~200 AD',
        'ink': _ARABIC_INK, 'paper': _ARABIC_PAPER, 'thick': True,
        'strokes': [
            [(20, 34), (26, 28), (38, 28), (44, 34)],   # boat shape
            [(30, 40), (30, 42)],                        # dot 1 below
            [(36, 40), (36, 42)],                        # dot 2 below
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
    # ── DEVANAGARI (continued) ──────────────────────────────────
    # Consonants
    {
        'name': 'KHA', 'script': 'DEVANAGARI', 'concept': 'KHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 34), (24, 44), (36, 44)],
            [(24, 34), (20, 28)],
        ],
    },
    {
        'name': 'GHA', 'script': 'DEVANAGARI', 'concept': 'GHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(34, 28), (24, 32), (24, 44)],
            [(24, 44), (34, 44)],
        ],
    },
    {
        'name': 'NGA', 'script': 'DEVANAGARI', 'concept': 'NGA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 36), (32, 42), (38, 36), (38, 22)],
            [(32, 42), (32, 50)],
        ],
    },
    {
        'name': 'CHA', 'script': 'DEVANAGARI', 'concept': 'CHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 34), (42, 34)],
        ],
    },
    {
        'name': 'CHHA', 'script': 'DEVANAGARI', 'concept': 'CHHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 34), (42, 34)],
            [(32, 48), (40, 48)],
        ],
    },
    {
        'name': 'JA', 'script': 'DEVANAGARI', 'concept': 'JA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 30), (24, 38)],
            [(24, 38), (30, 44), (36, 38)],
        ],
    },
    {
        'name': 'JHA', 'script': 'DEVANAGARI', 'concept': 'JHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(24, 30), (40, 30)],
            [(24, 40), (40, 40)],
        ],
    },
    {
        'name': 'NYA', 'script': 'DEVANAGARI', 'concept': 'NYA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 40), (32, 46), (38, 40), (38, 22)],
            [(26, 32), (38, 32)],
        ],
    },
    {
        'name': 'TA_R', 'script': 'DEVANAGARI', 'concept': 'TA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 28), (42, 28)],
        ],
    },
    {
        'name': 'THA_R', 'script': 'DEVANAGARI', 'concept': 'THA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 28), (42, 28)],
            [(32, 36), (42, 42)],
        ],
    },
    {
        'name': 'DA_R', 'script': 'DEVANAGARI', 'concept': 'DA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 36), (36, 42)],
        ],
    },
    {
        'name': 'DHA_R', 'script': 'DEVANAGARI', 'concept': 'DHA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 34), (36, 40)],
            [(24, 44), (36, 44)],
        ],
    },
    {
        'name': 'NA_R', 'script': 'DEVANAGARI', 'concept': 'NA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(24, 32), (40, 32)],
            [(24, 32), (24, 48)],
        ],
    },
    {
        'name': 'THA', 'script': 'DEVANAGARI', 'concept': 'THA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 28), (36, 28)],
            [(22, 28), (22, 42), (30, 48)],
        ],
    },
    {
        'name': 'DA', 'script': 'DEVANAGARI', 'concept': 'DA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 36), (32, 42), (38, 36), (38, 22)],
        ],
    },
    {
        'name': 'DHA', 'script': 'DEVANAGARI', 'concept': 'DHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 36), (32, 42), (38, 36), (38, 22)],
            [(32, 42), (32, 50)],
        ],
    },
    {
        'name': 'NA', 'script': 'DEVANAGARI', 'concept': 'NA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 48)],
            [(38, 22), (38, 48)],
            [(26, 36), (38, 36)],
        ],
    },
    {
        'name': 'PA', 'script': 'DEVANAGARI', 'concept': 'PA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 28), (24, 40)],
        ],
    },
    {
        'name': 'PHA', 'script': 'DEVANAGARI', 'concept': 'PHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 28), (24, 42), (36, 42)],
        ],
    },
    {
        'name': 'BA', 'script': 'DEVANAGARI', 'concept': 'BA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 38), (36, 46)],
        ],
    },
    {
        'name': 'BHA', 'script': 'DEVANAGARI', 'concept': 'BHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 34), (36, 40)],
            [(24, 44), (24, 48)],
        ],
    },
    {
        'name': 'YA', 'script': 'DEVANAGARI', 'concept': 'YA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(24, 22), (24, 34), (36, 40)],
        ],
    },
    {
        'name': 'RA', 'script': 'DEVANAGARI', 'concept': 'RA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (28, 30), (22, 42)],
        ],
    },
    {
        'name': 'LA', 'script': 'DEVANAGARI', 'concept': 'LA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 48)],
            [(26, 48), (40, 48)],
            [(40, 48), (40, 38)],
        ],
    },
    {
        'name': 'VA', 'script': 'DEVANAGARI', 'concept': 'VA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 28), (36, 28)],
            [(22, 28), (22, 38)],
        ],
    },
    {
        'name': 'SHA', 'script': 'DEVANAGARI', 'concept': 'SHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 38)],
            [(38, 22), (38, 38)],
            [(26, 38), (32, 46), (38, 38)],
        ],
    },
    {
        'name': 'SHA_R', 'script': 'DEVANAGARI', 'concept': 'SHA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 28), (36, 28)],
            [(22, 28), (22, 36), (28, 42)],
        ],
    },
    {
        'name': 'SA', 'script': 'DEVANAGARI', 'concept': 'SA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 28), (36, 28)],
            [(22, 28), (22, 40), (36, 40)],
        ],
    },
    {
        'name': 'HA', 'script': 'DEVANAGARI', 'concept': 'HA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 48)],
            [(38, 22), (38, 48)],
            [(26, 34), (32, 40), (38, 34)],
        ],
    },
    # Devanagari Vowels
    {
        'name': 'A', 'script': 'DEVANAGARI', 'concept': 'A (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (26, 36)],
        ],
    },
    {
        'name': 'AA', 'script': 'DEVANAGARI', 'concept': 'AA (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(30, 22), (30, 48)],
            [(30, 30), (22, 36)],
            [(40, 22), (40, 48)],
        ],
    },
    {
        'name': 'I', 'script': 'DEVANAGARI', 'concept': 'I (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(24, 30), (40, 30)],
            [(24, 30), (24, 40)],
        ],
    },
    {
        'name': 'II', 'script': 'DEVANAGARI', 'concept': 'II (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(24, 30), (40, 30)],
            [(24, 30), (24, 42), (32, 42)],
        ],
    },
    {
        'name': 'U', 'script': 'DEVANAGARI', 'concept': 'U (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 40), (24, 48)],
            [(32, 34), (40, 40)],
        ],
    },
    {
        'name': 'UU', 'script': 'DEVANAGARI', 'concept': 'UU (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 40), (24, 48)],
            [(32, 34), (42, 40), (42, 48)],
        ],
    },
    {
        'name': 'E', 'script': 'DEVANAGARI', 'concept': 'E (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(26, 22), (22, 30), (26, 38), (34, 38)],
        ],
    },
    {
        'name': 'AI', 'script': 'DEVANAGARI', 'concept': 'AI (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(26, 22), (22, 30), (26, 38), (34, 38)],
            [(22, 18), (26, 22)],
        ],
    },
    {
        'name': 'O', 'script': 'DEVANAGARI', 'concept': 'O (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(26, 22), (22, 30), (26, 38), (34, 38)],
            [(40, 22), (40, 48)],
        ],
    },
    {
        'name': 'AU', 'script': 'DEVANAGARI', 'concept': 'AU (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _DEVA_INK, 'paper': _DEVA_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(26, 22), (22, 30), (26, 38), (34, 38)],
            [(40, 22), (44, 18)],
        ],
    },
    # ── BENGALI ─────────────────────────────────────────────────
    # Vowels
    {
        'name': 'A', 'script': 'BENGALI', 'concept': 'A (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(34, 30), (24, 36)],
        ],
    },
    {
        'name': 'AA', 'script': 'BENGALI', 'concept': 'AA (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(30, 22), (30, 48)],
            [(30, 30), (22, 36)],
            [(40, 22), (40, 48)],
        ],
    },
    {
        'name': 'I', 'script': 'BENGALI', 'concept': 'I (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 30), (32, 30)],
            [(22, 30), (22, 42), (28, 48)],
        ],
    },
    {
        'name': 'II', 'script': 'BENGALI', 'concept': 'II (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 30), (32, 30)],
            [(22, 30), (22, 44), (32, 44)],
        ],
    },
    {
        'name': 'U', 'script': 'BENGALI', 'concept': 'U (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 38), (26, 46)],
            [(32, 34), (38, 42)],
        ],
    },
    {
        'name': 'UU', 'script': 'BENGALI', 'concept': 'UU (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 38), (26, 46)],
            [(32, 34), (40, 42), (40, 48)],
        ],
    },
    {
        'name': 'E', 'script': 'BENGALI', 'concept': 'E (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(26, 22), (20, 32), (26, 40), (34, 40)],
        ],
    },
    {
        'name': 'AI', 'script': 'BENGALI', 'concept': 'AI (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(26, 22), (20, 32), (26, 40), (34, 40)],
            [(22, 18), (26, 22)],
        ],
    },
    {
        'name': 'O', 'script': 'BENGALI', 'concept': 'O (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(30, 22), (30, 48)],
            [(22, 22), (20, 32), (24, 38), (30, 38)],
            [(40, 22), (40, 48)],
        ],
    },
    {
        'name': 'AU', 'script': 'BENGALI', 'concept': 'AU (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(30, 22), (30, 48)],
            [(22, 22), (20, 32), (24, 38), (30, 38)],
            [(40, 22), (44, 18)],
        ],
    },
    {
        'name': 'RI', 'script': 'BENGALI', 'concept': 'RI (VOWEL)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 40)],
            [(24, 40), (40, 40), (40, 48), (24, 48), (24, 40)],
        ],
    },
    # Bengali Consonants
    {
        'name': 'KA', 'script': 'BENGALI', 'concept': 'KA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 30), (24, 42), (36, 42)],
        ],
    },
    {
        'name': 'KHA', 'script': 'BENGALI', 'concept': 'KHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 34), (24, 44)],
            [(24, 34), (20, 28)],
        ],
    },
    {
        'name': 'GA', 'script': 'BENGALI', 'concept': 'GA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(34, 28), (24, 34), (24, 44), (34, 48)],
        ],
    },
    {
        'name': 'GHA', 'script': 'BENGALI', 'concept': 'GHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (34, 48)],
            [(34, 28), (24, 34), (24, 44)],
            [(24, 44), (34, 44)],
        ],
    },
    {
        'name': 'NGA', 'script': 'BENGALI', 'concept': 'NGA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 38), (32, 44), (38, 38), (38, 22)],
            [(32, 44), (32, 50)],
        ],
    },
    {
        'name': 'CHA', 'script': 'BENGALI', 'concept': 'CHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 36), (42, 36)],
        ],
    },
    {
        'name': 'CHHA', 'script': 'BENGALI', 'concept': 'CHHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 34), (42, 34)],
            [(32, 48), (42, 48)],
        ],
    },
    {
        'name': 'JA', 'script': 'BENGALI', 'concept': 'JA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 30), (24, 40)],
            [(24, 40), (30, 46), (36, 40)],
        ],
    },
    {
        'name': 'JHA', 'script': 'BENGALI', 'concept': 'JHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 32), (42, 32)],
            [(22, 42), (42, 42)],
        ],
    },
    {
        'name': 'NYA', 'script': 'BENGALI', 'concept': 'NYA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 42), (32, 48), (38, 42), (38, 22)],
            [(26, 34), (38, 34)],
        ],
    },
    {
        'name': 'TA_R', 'script': 'BENGALI', 'concept': 'TA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 30), (42, 30)],
        ],
    },
    {
        'name': 'THA_R', 'script': 'BENGALI', 'concept': 'THA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 30), (42, 30)],
            [(32, 38), (42, 44)],
        ],
    },
    {
        'name': 'DA_R', 'script': 'BENGALI', 'concept': 'DA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 38), (36, 44)],
        ],
    },
    {
        'name': 'DHA_R', 'script': 'BENGALI', 'concept': 'DHA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 36), (36, 42)],
            [(24, 46), (36, 46)],
        ],
    },
    {
        'name': 'NA_R', 'script': 'BENGALI', 'concept': 'NA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(32, 22), (32, 48)],
            [(22, 34), (42, 34)],
            [(22, 34), (22, 48)],
        ],
    },
    {
        'name': 'TA', 'script': 'BENGALI', 'concept': 'TA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 32), (36, 32)],
            [(22, 32), (22, 46), (36, 46)],
        ],
    },
    {
        'name': 'THA', 'script': 'BENGALI', 'concept': 'THA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 30), (36, 30)],
            [(22, 30), (22, 44), (30, 50)],
        ],
    },
    {
        'name': 'DA', 'script': 'BENGALI', 'concept': 'DA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 38), (32, 44), (38, 38), (38, 22)],
        ],
    },
    {
        'name': 'DHA', 'script': 'BENGALI', 'concept': 'DHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 38), (32, 44), (38, 38), (38, 22)],
            [(32, 44), (32, 50)],
        ],
    },
    {
        'name': 'NA', 'script': 'BENGALI', 'concept': 'NA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 48)],
            [(38, 22), (38, 48)],
            [(26, 36), (38, 36)],
        ],
    },
    {
        'name': 'PA', 'script': 'BENGALI', 'concept': 'PA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 28), (24, 42)],
        ],
    },
    {
        'name': 'PHA', 'script': 'BENGALI', 'concept': 'PHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 28), (24, 44), (36, 44)],
        ],
    },
    {
        'name': 'BA', 'script': 'BENGALI', 'concept': 'BA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 40), (36, 48)],
        ],
    },
    {
        'name': 'BHA', 'script': 'BENGALI', 'concept': 'BHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 36), (36, 42)],
            [(24, 46), (24, 50)],
        ],
    },
    {
        'name': 'MA', 'script': 'BENGALI', 'concept': 'MA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 48)],
            [(40, 22), (40, 48)],
            [(26, 48), (40, 48)],
        ],
    },
    {
        'name': 'YA', 'script': 'BENGALI', 'concept': 'YA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(24, 22), (24, 36), (36, 42)],
        ],
    },
    {
        'name': 'RA', 'script': 'BENGALI', 'concept': 'RA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(34, 22), (26, 32), (22, 44)],
        ],
    },
    {
        'name': 'LA', 'script': 'BENGALI', 'concept': 'LA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 48)],
            [(26, 48), (40, 48)],
            [(40, 48), (40, 36)],
        ],
    },
    {
        'name': 'SHA', 'script': 'BENGALI', 'concept': 'SHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 40)],
            [(38, 22), (38, 40)],
            [(26, 40), (32, 48), (38, 40)],
        ],
    },
    {
        'name': 'SHA_R', 'script': 'BENGALI', 'concept': 'SHA (RETRO)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 30), (36, 30)],
            [(22, 30), (22, 38), (28, 44)],
        ],
    },
    {
        'name': 'SA', 'script': 'BENGALI', 'concept': 'SA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(22, 30), (36, 30)],
            [(22, 30), (22, 42), (36, 42)],
        ],
    },
    {
        'name': 'HA', 'script': 'BENGALI', 'concept': 'HA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(26, 22), (26, 48)],
            [(38, 22), (38, 48)],
            [(26, 36), (32, 42), (38, 36)],
        ],
    },
    {
        'name': 'RRA', 'script': 'BENGALI', 'concept': 'RRA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 38), (36, 44)],
            [(30, 48), (30, 50)],
        ],
    },
    {
        'name': 'RHA', 'script': 'BENGALI', 'concept': 'RHA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 36), (36, 42)],
            [(24, 46), (36, 46)],
            [(30, 48), (30, 50)],
        ],
    },
    {
        'name': 'YYA', 'script': 'BENGALI', 'concept': 'YYA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 48)],
            [(24, 22), (24, 38), (36, 44)],
            [(24, 48), (24, 50)],
        ],
    },
    {
        'name': 'TA_KH', 'script': 'BENGALI', 'concept': 'TA (KHANDA)',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(36, 22), (36, 42)],
            [(22, 32), (36, 32)],
            [(22, 32), (22, 42), (36, 42)],
        ],
    },
    {
        'name': 'ANUSVR', 'script': 'BENGALI', 'concept': 'ANUSVAR',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(30, 34), (34, 34), (34, 38), (30, 38), (30, 34)],
        ],
    },
    {
        'name': 'VISARG', 'script': 'BENGALI', 'concept': 'VISARGA',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(30, 26), (34, 26), (34, 30), (30, 30), (30, 26)],
            [(30, 40), (34, 40), (34, 44), (30, 44), (30, 40)],
        ],
    },
    {
        'name': 'CHNDRB', 'script': 'BENGALI', 'concept': 'CHANDRABINDU',
        'origin': 'BRAHMI ~300 BC',
        'ink': _BENGALI_INK, 'paper': _BENGALI_PAPER, 'thick': True,
        'strokes': [
            [(26, 34), (32, 30), (38, 34)],
            [(31, 26), (33, 26)],
        ],
    },
    # ── TAMIL (continued) ──────────────────────────────────────
    # Vowels
    {
        'name': 'AA', 'script': 'TAMIL', 'concept': 'AA (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],
            [(32, 38), (32, 50)],
            [(40, 34), (46, 28)],
        ],
    },
    {
        'name': 'I', 'script': 'TAMIL', 'concept': 'I (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 32), (28, 28)],
            [(34, 32), (34, 50)],
        ],
    },
    {
        'name': 'II', 'script': 'TAMIL', 'concept': 'II (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 32), (28, 28)],
            [(34, 32), (34, 50)],
            [(38, 26), (44, 22)],
        ],
    },
    {
        'name': 'U', 'script': 'TAMIL', 'concept': 'U (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 28), (32, 22), (40, 28), (40, 38),
             (32, 44), (24, 38), (24, 28)],
        ],
    },
    {
        'name': 'UU', 'script': 'TAMIL', 'concept': 'UU (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 28), (32, 22), (40, 28), (40, 38),
             (32, 44), (24, 38), (24, 28)],
            [(32, 44), (32, 50)],
        ],
    },
    {
        'name': 'E', 'script': 'TAMIL', 'concept': 'E (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(20, 24), (28, 20), (34, 26), (28, 32), (20, 28)],
            [(34, 26), (34, 50)],
            [(38, 24), (44, 20), (44, 32)],
        ],
    },
    {
        'name': 'EE', 'script': 'TAMIL', 'concept': 'EE (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(20, 24), (28, 20), (34, 26), (28, 32), (20, 28)],
            [(34, 26), (34, 50)],
            [(38, 24), (44, 20), (44, 32)],
            [(44, 32), (46, 38)],
        ],
    },
    {
        'name': 'AI', 'script': 'TAMIL', 'concept': 'AI (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(20, 24), (28, 20), (34, 26), (28, 32), (20, 28)],
            [(34, 26), (34, 50)],
            [(38, 24), (44, 20)],
        ],
    },
    {
        'name': 'O', 'script': 'TAMIL', 'concept': 'O (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],
            [(32, 38), (32, 50)],
            [(18, 20), (24, 24)],
        ],
    },
    {
        'name': 'OO', 'script': 'TAMIL', 'concept': 'OO (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],
            [(32, 38), (32, 50)],
            [(18, 20), (24, 24)],
            [(40, 34), (46, 28)],
        ],
    },
    {
        'name': 'AU', 'script': 'TAMIL', 'concept': 'AU (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],
            [(32, 38), (32, 50)],
            [(18, 20), (24, 24)],
            [(44, 38), (44, 50)],
        ],
    },
    # Tamil Consonants
    {
        'name': 'NGA', 'script': 'TAMIL', 'concept': 'NGA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(26, 24), (34, 20), (40, 26), (34, 32), (26, 28)],
            [(34, 32), (34, 42)],
            [(26, 42), (42, 42)],
        ],
    },
    {
        'name': 'CHA', 'script': 'TAMIL', 'concept': 'CHA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(28, 24), (36, 20), (42, 26), (36, 34), (28, 30)],
            [(36, 34), (36, 50)],
            [(22, 34), (36, 34)],
        ],
    },
    {
        'name': 'NYA', 'script': 'TAMIL', 'concept': 'NYA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 26), (32, 20), (40, 26), (36, 34), (28, 34)],
            [(24, 34), (24, 48)],
            [(40, 34), (40, 48)],
        ],
    },
    {
        'name': 'TA_R', 'script': 'TAMIL', 'concept': 'TA (RETRO)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(26, 24), (34, 20), (40, 26), (34, 32), (26, 28)],
            [(34, 32), (34, 50)],
            [(34, 42), (42, 48)],
        ],
    },
    {
        'name': 'NA_R', 'script': 'TAMIL', 'concept': 'NA (RETRO)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 26), (32, 20), (40, 26), (36, 34)],
            [(36, 34), (28, 34), (24, 40), (28, 48), (36, 48)],
        ],
    },
    {
        'name': 'TA', 'script': 'TAMIL', 'concept': 'TA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(26, 24), (34, 20), (40, 26), (34, 32), (26, 28)],
            [(26, 34), (40, 34)],
            [(34, 34), (34, 50)],
        ],
    },
    {
        'name': 'NA', 'script': 'TAMIL', 'concept': 'NA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(22, 26), (30, 20), (38, 26), (32, 34), (24, 30)],
            [(38, 26), (44, 34), (38, 42), (30, 42)],
            [(30, 42), (30, 50)],
        ],
    },
    {
        'name': 'PA', 'script': 'TAMIL', 'concept': 'PA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 26), (32, 20), (40, 26), (40, 36),
             (32, 42), (24, 36), (24, 26)],
            [(24, 36), (20, 42)],
        ],
    },
    {
        'name': 'MA', 'script': 'TAMIL', 'concept': 'MA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 26), (32, 20), (40, 26), (40, 36),
             (32, 42), (24, 36), (24, 26)],
            [(32, 42), (32, 50)],
        ],
    },
    {
        'name': 'YA', 'script': 'TAMIL', 'concept': 'YA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(22, 28), (30, 22), (38, 28), (34, 36)],
            [(34, 36), (28, 36), (24, 42), (28, 50), (38, 50)],
        ],
    },
    {
        'name': 'RA', 'script': 'TAMIL', 'concept': 'RA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(26, 24), (34, 20), (40, 26), (34, 32), (26, 28)],
            [(34, 32), (34, 44)],
            [(26, 44), (42, 44)],
        ],
    },
    {
        'name': 'LA', 'script': 'TAMIL', 'concept': 'LA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 26), (32, 20), (40, 26), (34, 34)],
            [(34, 34), (34, 50)],
            [(26, 50), (42, 50)],
        ],
    },
    {
        'name': 'VA', 'script': 'TAMIL', 'concept': 'VA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(22, 28), (30, 22), (38, 28), (34, 36)],
            [(34, 36), (34, 50)],
            [(28, 36), (22, 42)],
        ],
    },
    {
        'name': 'ZHA', 'script': 'TAMIL', 'concept': 'ZHA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],
            [(32, 38), (38, 46), (32, 50), (26, 46)],
        ],
    },
    {
        'name': 'LLA', 'script': 'TAMIL', 'concept': 'LLA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 26), (32, 20), (40, 26), (34, 34)],
            [(34, 34), (28, 34), (24, 40), (28, 48),
             (36, 48), (40, 42)],
        ],
    },
    {
        'name': 'RRA', 'script': 'TAMIL', 'concept': 'RRA',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(26, 24), (34, 20), (40, 26), (34, 32), (26, 28)],
            [(34, 32), (40, 40), (34, 48), (26, 44)],
        ],
    },
    {
        'name': 'NA_A', 'script': 'TAMIL', 'concept': 'NA (ALVEOLAR)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(22, 26), (30, 20), (38, 26), (32, 34), (24, 30)],
            [(32, 34), (32, 50)],
            [(24, 50), (40, 50)],
        ],
    },
    # ── TIBETAN (continued) ────────────────────────────────────
    {
        'name': 'KHA', 'script': 'TIBETAN', 'concept': 'KHA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (32, 44)],
            [(32, 30), (22, 36)],
            [(32, 44), (24, 50)],
        ],
    },
    {
        'name': 'GA', 'script': 'TIBETAN', 'concept': 'GA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 44)],
            [(38, 22), (38, 44)],
            [(26, 44), (38, 44)],
        ],
    },
    {
        'name': 'NGA', 'script': 'TIBETAN', 'concept': 'NGA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (32, 44)],
            [(22, 32), (42, 32)],
            [(32, 44), (26, 50)],
        ],
    },
    {
        'name': 'CHA', 'script': 'TIBETAN', 'concept': 'CHA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (32, 48)],
            [(24, 30), (40, 30)],
        ],
    },
    {
        'name': 'CHHA', 'script': 'TIBETAN', 'concept': 'CHHA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (32, 48)],
            [(24, 30), (40, 30)],
            [(32, 48), (40, 48)],
        ],
    },
    {
        'name': 'JA', 'script': 'TIBETAN', 'concept': 'JA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 44)],
            [(38, 22), (38, 44)],
            [(26, 34), (38, 34)],
        ],
    },
    {
        'name': 'NYA', 'script': 'TIBETAN', 'concept': 'NYA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 40), (32, 46), (38, 40), (38, 22)],
        ],
    },
    {
        'name': 'TA', 'script': 'TIBETAN', 'concept': 'TA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(22, 30), (36, 30)],
            [(22, 30), (22, 42)],
        ],
    },
    {
        'name': 'THA', 'script': 'TIBETAN', 'concept': 'THA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(22, 30), (36, 30)],
            [(22, 30), (22, 44), (30, 50)],
        ],
    },
    {
        'name': 'DA', 'script': 'TIBETAN', 'concept': 'DA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 38), (32, 44), (38, 38), (38, 22)],
            [(32, 44), (32, 50)],
        ],
    },
    {
        'name': 'NA', 'script': 'TIBETAN', 'concept': 'NA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 48)],
            [(38, 22), (38, 48)],
            [(26, 36), (38, 36)],
        ],
    },
    {
        'name': 'PA', 'script': 'TIBETAN', 'concept': 'PA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 28), (24, 42)],
        ],
    },
    {
        'name': 'PHA', 'script': 'TIBETAN', 'concept': 'PHA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(36, 28), (24, 28), (24, 42), (36, 42)],
        ],
    },
    {
        'name': 'BA', 'script': 'TIBETAN', 'concept': 'BA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(36, 30), (24, 38), (36, 46)],
        ],
    },
    {
        'name': 'MA', 'script': 'TIBETAN', 'concept': 'MA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 48)],
            [(40, 22), (40, 48)],
            [(26, 48), (40, 48)],
        ],
    },
    {
        'name': 'TSA', 'script': 'TIBETAN', 'concept': 'TSA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (32, 48)],
            [(22, 28), (42, 28)],
            [(22, 38), (42, 38)],
        ],
    },
    {
        'name': 'TSHA', 'script': 'TIBETAN', 'concept': 'TSHA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (32, 48)],
            [(22, 28), (42, 28)],
            [(22, 38), (42, 38)],
            [(32, 48), (38, 50)],
        ],
    },
    {
        'name': 'DZA', 'script': 'TIBETAN', 'concept': 'DZA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 44)],
            [(38, 22), (38, 44)],
            [(26, 44), (32, 50), (38, 44)],
        ],
    },
    {
        'name': 'WA', 'script': 'TIBETAN', 'concept': 'WA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (32, 40), (24, 48)],
            [(32, 34), (40, 42)],
        ],
    },
    {
        'name': 'ZHA', 'script': 'TIBETAN', 'concept': 'ZHA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(22, 30), (36, 30)],
            [(22, 30), (22, 38)],
        ],
    },
    {
        'name': 'ZA', 'script': 'TIBETAN', 'concept': 'ZA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(22, 28), (36, 28)],
            [(22, 28), (22, 40), (36, 40)],
        ],
    },
    {
        'name': 'YA', 'script': 'TIBETAN', 'concept': 'YA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(24, 22), (24, 36), (36, 42)],
        ],
    },
    {
        'name': 'RA', 'script': 'TIBETAN', 'concept': 'RA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(34, 22), (28, 32), (22, 44)],
        ],
    },
    {
        'name': 'LA', 'script': 'TIBETAN', 'concept': 'LA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 48)],
            [(26, 48), (40, 48)],
            [(40, 48), (40, 38)],
        ],
    },
    {
        'name': 'SHA', 'script': 'TIBETAN', 'concept': 'SHA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 40)],
            [(38, 22), (38, 40)],
            [(26, 40), (32, 48), (38, 40)],
        ],
    },
    {
        'name': 'SA', 'script': 'TIBETAN', 'concept': 'SA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(36, 22), (36, 48)],
            [(22, 30), (36, 30)],
            [(22, 30), (22, 42), (36, 42)],
        ],
    },
    {
        'name': 'HA', 'script': 'TIBETAN', 'concept': 'HA',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(26, 22), (26, 48)],
            [(38, 22), (38, 48)],
            [(26, 36), (32, 42), (38, 36)],
        ],
    },
    {
        'name': 'A', 'script': 'TIBETAN', 'concept': 'A (VOWEL)',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(34, 22), (34, 48)],
            [(34, 30), (24, 36)],
        ],
    },
    # ── THAI ────────────────────────────────────────────────────
    {
        'name': 'KO KAI', 'script': 'THAI', 'concept': 'KO KAI (CHICKEN)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 48)],
            [(38, 30), (38, 48)],
        ],
    },
    {
        'name': 'KHO KHAI', 'script': 'THAI', 'concept': 'KHO KHAI (EGG)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(24, 30), (24, 48)],
            [(40, 30), (40, 48)],
            [(24, 48), (40, 48)],
        ],
    },
    {
        'name': 'KHO KHUAT', 'script': 'THAI', 'concept': 'KHO KHUAT (BOTTLE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 48)],
            [(38, 30), (38, 48)],
            [(28, 48), (38, 48)],
        ],
    },
    {
        'name': 'KHO KHWAI', 'script': 'THAI', 'concept': 'KHO KHWAI (BUFFALO)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(24, 30), (24, 48)],
            [(40, 30), (40, 48)],
            [(24, 38), (40, 38)],
        ],
    },
    {
        'name': 'KHO KHON', 'script': 'THAI', 'concept': 'KHO KHON (PERSON)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 48)],
            [(38, 30), (38, 48)],
            [(20, 34), (28, 34)],
        ],
    },
    {
        'name': 'KHO RAKH', 'script': 'THAI', 'concept': 'KHO RAKHANG (BELL)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(24, 30), (24, 48)],
            [(40, 30), (40, 48)],
            [(32, 30), (32, 48)],
        ],
    },
    {
        'name': 'NGO NGU', 'script': 'THAI', 'concept': 'NGO NGU (SNAKE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(26, 24), (32, 20), (38, 24), (38, 34),
             (32, 38), (26, 34), (26, 24)],
            [(26, 38), (26, 50)],
        ],
    },
    {
        'name': 'CHO CHAN', 'script': 'THAI', 'concept': 'CHO CHAN (PLATE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 48)],
            [(22, 36), (34, 36)],
        ],
    },
    {
        'name': 'CHO CHING', 'script': 'THAI', 'concept': 'CHO CHING (CYMBAL)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(36, 30), (36, 48)],
            [(24, 36), (36, 36)],
            [(24, 36), (24, 48)],
        ],
    },
    {
        'name': 'CHO CHANG', 'script': 'THAI', 'concept': 'CHO CHANG (ELEPHANT)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 48)],
            [(38, 30), (38, 48)],
            [(28, 40), (38, 40)],
        ],
    },
    {
        'name': 'SO SO', 'script': 'THAI', 'concept': 'SO SO (CHAIN)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 48)],
            [(26, 42), (42, 42)],
        ],
    },
    {
        'name': 'CHO CHOE', 'script': 'THAI', 'concept': 'CHO CHOE (TREE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 48)],
            [(40, 30), (40, 48)],
            [(30, 48), (40, 48)],
        ],
    },
    {
        'name': 'YO YING', 'script': 'THAI', 'concept': 'YO YING (WOMAN)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(26, 24), (32, 20), (38, 24), (38, 34),
             (32, 38), (26, 34), (26, 24)],
            [(32, 38), (32, 50)],
            [(24, 50), (40, 50)],
        ],
    },
    {
        'name': 'DO CHADA', 'script': 'THAI', 'concept': 'DO CHADA (HEADDRESS)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 48)],
            [(38, 30), (38, 48)],
            [(28, 38), (38, 38)],
            [(28, 48), (38, 48)],
        ],
    },
    {
        'name': 'TO PATAK', 'script': 'THAI', 'concept': 'TO PATAK (GAVEL)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 48)],
            [(40, 30), (40, 48)],
            [(30, 38), (40, 38)],
        ],
    },
    {
        'name': 'THO THAN', 'script': 'THAI', 'concept': 'THO THAN (BASE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 48)],
            [(22, 40), (46, 40)],
        ],
    },
    {
        'name': 'THO NANGM', 'script': 'THAI', 'concept': 'THO NANGMON (ELDER)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 44), (36, 50), (42, 44)],
        ],
    },
    {
        'name': 'THO PHUTH', 'script': 'THAI', 'concept': 'THO PHUTHAO (HERMIT)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 50)],
            [(38, 30), (38, 50)],
            [(28, 50), (38, 50)],
        ],
    },
    {
        'name': 'NO NEN', 'script': 'THAI', 'concept': 'NO NEN (NOVICE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 48)],
            [(40, 30), (40, 48)],
        ],
    },
    {
        'name': 'DO DEK', 'script': 'THAI', 'concept': 'DO DEK (CHILD)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 48)],
            [(26, 48), (42, 48)],
        ],
    },
    {
        'name': 'TO TAO', 'script': 'THAI', 'concept': 'TO TAO (TURTLE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(24, 30), (24, 48)],
            [(40, 30), (40, 48)],
            [(24, 48), (40, 48)],
        ],
    },
    {
        'name': 'THO THUNG', 'script': 'THAI', 'concept': 'THO THUNG (BAG)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 42), (34, 48), (40, 42)],
        ],
    },
    {
        'name': 'THO THAHA', 'script': 'THAI', 'concept': 'THO THAHAN (SOLDIER)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 48)],
            [(40, 30), (40, 48)],
            [(22, 40), (30, 40)],
        ],
    },
    {
        'name': 'THO THONG', 'script': 'THAI', 'concept': 'THO THONG (FLAG)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 48)],
            [(34, 34), (44, 34)],
            [(44, 34), (44, 44)],
        ],
    },
    {
        'name': 'NO NU', 'script': 'THAI', 'concept': 'NO NU (MOUSE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 44), (38, 50)],
        ],
    },
    {
        'name': 'BO BAIMAI', 'script': 'THAI', 'concept': 'BO BAIMAI (LEAF)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(26, 24), (32, 20), (38, 24), (38, 34),
             (32, 38), (26, 34), (26, 24)],
            [(26, 38), (26, 50)],
            [(38, 38), (38, 50)],
        ],
    },
    {
        'name': 'PO PLA', 'script': 'THAI', 'concept': 'PO PLA (FISH)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 48)],
            [(38, 30), (38, 48)],
            [(28, 48), (38, 48)],
        ],
    },
    {
        'name': 'PHO PHUNG', 'script': 'THAI', 'concept': 'PHO PHUNG (BEE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 48)],
            [(40, 30), (40, 48)],
            [(30, 40), (40, 40)],
        ],
    },
    {
        'name': 'FO FA', 'script': 'THAI', 'concept': 'FO FA (LID)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 48)],
            [(22, 34), (46, 34)],
        ],
    },
    {
        'name': 'PHO PHAN', 'script': 'THAI', 'concept': 'PHO PHAN (TRAY)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(24, 30), (24, 48)],
            [(40, 30), (40, 48)],
            [(24, 40), (40, 40)],
            [(24, 48), (40, 48)],
        ],
    },
    {
        'name': 'FO FAN', 'script': 'THAI', 'concept': 'FO FAN (TEETH)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 44), (34, 50), (40, 44), (40, 30)],
        ],
    },
    {
        'name': 'PHO SAMPH', 'script': 'THAI', 'concept': 'PHO SAMPHAO (JUNK)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (24, 40), (30, 50), (40, 50), (46, 40), (40, 30)],
        ],
    },
    {
        'name': 'MO MA', 'script': 'THAI', 'concept': 'MO MA (HORSE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(26, 24), (32, 20), (38, 24), (38, 34),
             (32, 38), (26, 34), (26, 24)],
            [(32, 38), (32, 50)],
        ],
    },
    {
        'name': 'YO YAK', 'script': 'THAI', 'concept': 'YO YAK (GIANT)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 44), (34, 50)],
            [(38, 30), (38, 44), (34, 50)],
        ],
    },
    {
        'name': 'RO RUEA', 'script': 'THAI', 'concept': 'RO RUEA (BOAT)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(34, 30), (34, 50)],
        ],
    },
    {
        'name': 'RU', 'script': 'THAI', 'concept': 'RU (VOWEL)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 44)],
            [(26, 44), (42, 44)],
        ],
    },
    {
        'name': 'LO LING', 'script': 'THAI', 'concept': 'LO LING (MONKEY)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(30, 30), (30, 50)],
            [(40, 30), (40, 50)],
        ],
    },
    {
        'name': 'LU', 'script': 'THAI', 'concept': 'LU (VOWEL)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 44)],
            [(38, 30), (38, 44)],
            [(28, 44), (38, 44)],
        ],
    },
    {
        'name': 'WO WAEN', 'script': 'THAI', 'concept': 'WO WAEN (RING)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(26, 24), (32, 20), (38, 24), (38, 34),
             (32, 38), (26, 34), (26, 24)],
            [(26, 38), (26, 50)],
            [(38, 38), (38, 50)],
            [(26, 50), (38, 50)],
        ],
    },
    {
        'name': 'SO SALA', 'script': 'THAI', 'concept': 'SO SALA (PAVILION)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (34, 48)],
            [(24, 34), (44, 34)],
            [(34, 48), (24, 48)],
        ],
    },
    {
        'name': 'SO RUSI', 'script': 'THAI', 'concept': 'SO RUSI (HERMIT)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(36, 30), (36, 48)],
            [(26, 36), (46, 36)],
        ],
    },
    {
        'name': 'SO SUEA', 'script': 'THAI', 'concept': 'SO SUEA (TIGER)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(28, 30), (28, 48)],
            [(38, 30), (38, 48)],
            [(28, 48), (38, 48)],
            [(20, 36), (28, 36)],
        ],
    },
    {
        'name': 'HO HIP', 'script': 'THAI', 'concept': 'HO HIP (CHEST)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(24, 30), (24, 48)],
            [(40, 30), (40, 48)],
            [(24, 38), (40, 38)],
            [(24, 48), (40, 48)],
        ],
    },
    {
        'name': 'LO CHULA', 'script': 'THAI', 'concept': 'LO CHULA (KITE)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(28, 24), (34, 20), (38, 26), (34, 30), (28, 28)],
            [(34, 30), (26, 40), (34, 50), (42, 40), (34, 30)],
        ],
    },
    {
        'name': 'O ANG', 'script': 'THAI', 'concept': 'O ANG (BASIN)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 40),
             (32, 46), (24, 40), (24, 24)],
        ],
    },
    {
        'name': 'HO NOKHUK', 'script': 'THAI', 'concept': 'HO NOKHUK (OWL)',
        'origin': 'SUKHOTHAI ~1283 AD',
        'ink': _THAI_INK, 'paper': _THAI_PAPER,
        'strokes': [
            [(30, 24), (36, 20), (40, 26), (36, 30), (30, 28)],
            [(24, 30), (24, 48)],
            [(40, 30), (40, 48)],
            [(24, 48), (40, 48)],
            [(32, 38), (32, 48)],
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
    # ── GREEK (continued) ───────────────────────────────────────
    {
        'name': 'BETA', 'script': 'GREEK', 'concept': 'B',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # vertical
            [(22, 20), (36, 20), (42, 24), (42, 30),
             (36, 34)],                                        # upper bump
            [(22, 34), (36, 34), (44, 38), (44, 44),
             (36, 48), (22, 48)],                              # lower bump
        ],
    },
    {
        'name': 'GAMMA', 'script': 'GREEK', 'concept': 'G',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(20, 20), (32, 34)],                              # left diagonal down
            [(44, 20), (32, 34)],                              # right diagonal down
            [(32, 34), (32, 48)],                              # vertical descender
        ],
    },
    {
        'name': 'DELTA', 'script': 'GREEK', 'concept': 'D',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(32, 20), (20, 48)],                              # left side
            [(32, 20), (44, 48)],                              # right side
            [(20, 48), (44, 48)],                              # base
        ],
    },
    {
        'name': 'EPSILON', 'script': 'GREEK', 'concept': 'E',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # vertical
            [(22, 20), (42, 20)],                              # top bar
            [(22, 34), (38, 34)],                              # middle bar
            [(22, 48), (42, 48)],                              # bottom bar
        ],
    },
    {
        'name': 'ZETA', 'script': 'GREEK', 'concept': 'Z',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],                              # top bar
            [(44, 22), (20, 48)],                              # diagonal
            [(20, 48), (44, 48)],                              # bottom bar
        ],
    },
    {
        'name': 'ETA', 'script': 'GREEK', 'concept': 'LONG E',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # left vertical
            [(42, 20), (42, 48)],                              # right vertical
            [(22, 34), (42, 34)],                              # crossbar
        ],
    },
    {
        'name': 'THETA', 'script': 'GREEK', 'concept': 'TH',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(24, 28), (28, 22), (36, 22), (40, 28),
             (40, 40), (36, 46), (28, 46), (24, 40),
             (24, 28)],                                        # oval
            [(24, 34), (40, 34)],                              # horizontal bar
        ],
    },
    {
        'name': 'IOTA', 'script': 'GREEK', 'concept': 'I',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                              # single vertical
        ],
    },
    {
        'name': 'KAPPA', 'script': 'GREEK', 'concept': 'K',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # vertical
            [(42, 20), (22, 34)],                              # upper diagonal
            [(22, 34), (42, 48)],                              # lower diagonal
        ],
    },
    {
        'name': 'LAMBDA', 'script': 'GREEK', 'concept': 'L',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(20, 48), (32, 20)],                              # left side up
            [(32, 20), (44, 48)],                              # right side down
        ],
    },
    {
        'name': 'MU', 'script': 'GREEK', 'concept': 'M',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(20, 48), (20, 20)],                              # left vertical
            [(20, 20), (32, 36)],                              # left diagonal
            [(32, 36), (44, 20)],                              # right diagonal
            [(44, 20), (44, 48)],                              # right vertical
        ],
    },
    {
        'name': 'NU', 'script': 'GREEK', 'concept': 'N',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 48), (22, 20)],                              # left vertical
            [(22, 20), (42, 48)],                              # diagonal
            [(42, 48), (42, 20)],                              # right vertical
        ],
    },
    {
        'name': 'XI', 'script': 'GREEK', 'concept': 'KS',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],                              # top bar
            [(26, 34), (38, 34)],                              # middle bar
            [(22, 48), (42, 48)],                              # bottom bar
        ],
    },
    {
        'name': 'OMICRON', 'script': 'GREEK', 'concept': 'SHORT O',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(24, 28), (28, 22), (36, 22), (40, 28),
             (40, 40), (36, 46), (28, 46), (24, 40),
             (24, 28)],                                        # oval
        ],
    },
    {
        'name': 'RHO', 'script': 'GREEK', 'concept': 'R',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(22, 48), (22, 20)],                              # vertical
            [(22, 20), (36, 20), (42, 24), (42, 30),
             (36, 34), (22, 34)],                              # top bump
        ],
    },
    {
        'name': 'TAU', 'script': 'GREEK', 'concept': 'T',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(18, 22), (46, 22)],                              # top bar
            [(32, 22), (32, 48)],                              # vertical
        ],
    },
    {
        'name': 'UPSILON', 'script': 'GREEK', 'concept': 'U',
        'origin': 'PHOENICIAN ~800 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(20, 20), (32, 34)],                              # left arm down
            [(44, 20), (32, 34)],                              # right arm down
            [(32, 34), (32, 48)],                              # vertical stem
        ],
    },
    {
        'name': 'CHI', 'script': 'GREEK', 'concept': 'CH',
        'origin': 'IONIC ~400 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(20, 20), (44, 48)],                              # diagonal down-right
            [(44, 20), (20, 48)],                              # diagonal down-left
        ],
    },
    {
        'name': 'PSI', 'script': 'GREEK', 'concept': 'PS',
        'origin': 'IONIC ~400 BC',
        'ink': _GREEK_INK, 'paper': _GREEK_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                              # vertical shaft
            [(20, 24), (26, 36), (32, 38)],                    # left arm
            [(44, 24), (38, 36), (32, 38)],                    # right arm
        ],
    },
    # ── CYRILLIC (continued) ────────────────────────────────────
    {
        'name': 'A', 'script': 'CYRILLIC', 'concept': 'A',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 48), (32, 20), (44, 48)],                   # A shape
            [(25, 38), (39, 38)],                              # crossbar
        ],
    },
    {
        'name': 'BE', 'script': 'CYRILLIC', 'concept': 'B',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (42, 20)],                              # top bar
            [(22, 20), (22, 48)],                              # left vertical
            [(22, 48), (36, 48), (42, 44), (42, 38),
             (36, 34), (22, 34)],                              # bottom loop
        ],
    },
    {
        'name': 'VE', 'script': 'CYRILLIC', 'concept': 'V',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # vertical
            [(22, 20), (36, 20), (42, 24), (42, 30),
             (36, 34)],                                        # upper bump
            [(22, 34), (36, 34), (44, 38), (44, 44),
             (36, 48), (22, 48)],                              # lower bump
        ],
    },
    {
        'name': 'GE', 'script': 'CYRILLIC', 'concept': 'G',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (42, 20)],                              # top bar
            [(22, 20), (22, 48)],                              # left vertical down
        ],
    },
    {
        'name': 'DE', 'script': 'CYRILLIC', 'concept': 'D',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(24, 48), (24, 26), (40, 26)],                   # left side + top
            [(40, 26), (40, 48)],                              # right vertical
            [(20, 48), (44, 48)],                              # bottom bar
            [(20, 48), (20, 50)],                              # left foot
            [(44, 48), (44, 50)],                              # right foot
        ],
    },
    {
        'name': 'YE', 'script': 'CYRILLIC', 'concept': 'YE',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # vertical
            [(22, 20), (42, 20)],                              # top bar
            [(22, 34), (38, 34)],                              # middle bar
            [(22, 48), (42, 48)],                              # bottom bar
        ],
    },
    {
        'name': 'YO', 'script': 'CYRILLIC', 'concept': 'YO',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],                              # vertical
            [(22, 22), (42, 22)],                              # top bar
            [(22, 35), (38, 35)],                              # middle bar
            [(22, 48), (42, 48)],                              # bottom bar
            [(28, 18), (28, 20)],                              # left dot
            [(36, 18), (36, 20)],                              # right dot
        ],
    },
    {
        'name': 'ZHE', 'script': 'CYRILLIC', 'concept': 'ZH',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                              # center vertical
            [(18, 20), (28, 34)],                              # upper-left arm
            [(18, 48), (28, 34)],                              # lower-left arm
            [(46, 20), (36, 34)],                              # upper-right arm
            [(46, 48), (36, 34)],                              # lower-right arm
        ],
    },
    {
        'name': 'ZE', 'script': 'CYRILLIC', 'concept': 'Z',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 22), (36, 22), (42, 26), (42, 30),
             (36, 34)],                                        # upper curve (like 3)
            [(36, 34), (42, 38), (42, 44), (36, 48),
             (22, 48)],                                        # lower curve
        ],
    },
    {
        'name': 'I', 'script': 'CYRILLIC', 'concept': 'I',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # left vertical
            [(42, 20), (42, 48)],                              # right vertical
            [(22, 48), (42, 20)],                              # diagonal bottom-L to top-R
        ],
    },
    {
        'name': 'KA', 'script': 'CYRILLIC', 'concept': 'K',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # vertical
            [(42, 20), (22, 34)],                              # upper diagonal
            [(22, 34), (42, 48)],                              # lower diagonal
        ],
    },
    {
        'name': 'EL', 'script': 'CYRILLIC', 'concept': 'L',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(28, 48), (32, 20), (36, 48)],                   # Lambda with legs
            [(20, 48), (28, 48)],                              # left foot
            [(36, 48), (44, 48)],                              # right foot
        ],
    },
    {
        'name': 'EM', 'script': 'CYRILLIC', 'concept': 'M',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 48), (20, 20)],                              # left vertical
            [(20, 20), (32, 36)],                              # left inner diagonal
            [(32, 36), (44, 20)],                              # right inner diagonal
            [(44, 20), (44, 48)],                              # right vertical
        ],
    },
    {
        'name': 'EN', 'script': 'CYRILLIC', 'concept': 'N',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                              # left vertical
            [(42, 20), (42, 48)],                              # right vertical
            [(22, 34), (42, 34)],                              # crossbar
        ],
    },
    {
        'name': 'O', 'script': 'CYRILLIC', 'concept': 'O',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(24, 28), (28, 22), (36, 22), (40, 28),
             (40, 40), (36, 46), (28, 46), (24, 40),
             (24, 28)],                                        # oval
        ],
    },
    {
        'name': 'PE', 'script': 'CYRILLIC', 'concept': 'P',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(18, 22), (46, 22)],                              # top bar
            [(22, 22), (22, 48)],                              # left leg
            [(42, 22), (42, 48)],                              # right leg
        ],
    },
    {
        'name': 'ER', 'script': 'CYRILLIC', 'concept': 'R',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 48), (22, 20)],                              # vertical
            [(22, 20), (36, 20), (42, 24), (42, 30),
             (36, 34), (22, 34)],                              # top bump
        ],
    },
    {
        'name': 'ES', 'script': 'CYRILLIC', 'concept': 'S',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(42, 24), (38, 20), (28, 20), (22, 26),
             (22, 42), (28, 48), (38, 48), (42, 44)],         # C curve
        ],
    },
    {
        'name': 'TE', 'script': 'CYRILLIC', 'concept': 'T',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(18, 22), (46, 22)],                              # top bar
            [(32, 22), (32, 48)],                              # vertical
        ],
    },
    {
        'name': 'U', 'script': 'CYRILLIC', 'concept': 'U',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 20), (32, 34)],                              # left arm down
            [(44, 20), (32, 34)],                              # right arm down
            [(32, 34), (32, 48)],                              # vertical stem
        ],
    },
    {
        'name': 'EF', 'script': 'CYRILLIC', 'concept': 'F',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                              # vertical shaft
            [(22, 28), (26, 22), (38, 22), (42, 28),
             (42, 40), (38, 46), (26, 46), (22, 40),
             (22, 28)],                                        # oval
        ],
    },
    {
        'name': 'KHA', 'script': 'CYRILLIC', 'concept': 'KH',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 20), (44, 48)],                              # diagonal down-right
            [(44, 20), (20, 48)],                              # diagonal down-left
        ],
    },
    {
        'name': 'TSE', 'script': 'CYRILLIC', 'concept': 'TS',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 20), (20, 48)],                              # left vertical
            [(40, 20), (40, 48)],                              # right vertical
            [(20, 48), (44, 48)],                              # bottom bar
            [(44, 48), (44, 52)],                              # descender hook
        ],
    },
    {
        'name': 'CHE', 'script': 'CYRILLIC', 'concept': 'CH',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 20), (22, 34)],                              # left arm down
            [(22, 34), (42, 34)],                              # crossbar
            [(42, 20), (42, 48)],                              # right vertical full
        ],
    },
    {
        'name': 'SHA', 'script': 'CYRILLIC', 'concept': 'SH',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 22), (20, 48)],                              # left vertical
            [(32, 22), (32, 48)],                              # center vertical
            [(44, 22), (44, 48)],                              # right vertical
            [(20, 48), (44, 48)],                              # bottom bar
        ],
    },
    {
        'name': 'SHCHA', 'script': 'CYRILLIC', 'concept': 'SHCH',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(18, 22), (18, 46)],                              # left vertical
            [(30, 22), (30, 46)],                              # center vertical
            [(42, 22), (42, 46)],                              # right vertical
            [(18, 46), (46, 46)],                              # bottom bar
            [(46, 46), (46, 50)],                              # descender hook
        ],
    },
    {
        'name': 'HARD', 'script': 'CYRILLIC', 'concept': 'HARD SIGN',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 20), (28, 20)],                              # top-left serif
            [(28, 20), (28, 48)],                              # vertical
            [(28, 34), (38, 34), (44, 38), (44, 44),
             (38, 48), (28, 48)],                              # bottom-right bump
        ],
    },
    {
        'name': 'YERU', 'script': 'CYRILLIC', 'concept': 'Y',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 20), (20, 48)],                              # left vertical
            [(20, 34), (30, 34), (34, 38), (34, 44),
             (30, 48), (20, 48)],                              # bottom-right bump
            [(42, 20), (42, 48)],                              # right vertical (separate)
        ],
    },
    {
        'name': 'SOFT', 'script': 'CYRILLIC', 'concept': 'SOFT SIGN',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(26, 20), (26, 48)],                              # vertical
            [(26, 34), (38, 34), (44, 38), (44, 44),
             (38, 48), (26, 48)],                              # bottom-right bump
        ],
    },
    {
        'name': 'E', 'script': 'CYRILLIC', 'concept': 'E (REVERSED)',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(22, 24), (26, 20), (36, 20), (42, 26),
             (42, 42), (36, 48), (26, 48), (22, 44)],         # reversed C curve
            [(28, 34), (42, 34)],                              # middle bar
        ],
    },
    {
        'name': 'YU', 'script': 'CYRILLIC', 'concept': 'YU',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(20, 22), (20, 48)],                              # left vertical
            [(20, 34), (30, 34)],                              # connecting bar
            [(30, 24), (40, 20), (46, 28), (46, 40),
             (40, 48), (30, 44), (30, 24)],                    # right circle
        ],
    },
    {
        'name': 'YA', 'script': 'CYRILLIC', 'concept': 'YA',
        'origin': 'GLAGOLITIC ~863 AD',
        'ink': _CYRILLIC_INK, 'paper': _CYRILLIC_PAPER,
        'strokes': [
            [(42, 20), (42, 48)],                              # right vertical
            [(42, 20), (28, 20), (22, 24), (22, 30),
             (28, 34), (42, 34)],                              # top-left bump
            [(32, 34), (20, 48)],                              # left leg
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
    {
        'name': 'GIMEL', 'script': 'HEBREW', 'concept': 'G / CAMEL',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(40, 22), (40, 40)],                        # right vertical
            [(40, 22), (26, 22)],                        # top bar going left
            [(40, 40), (34, 48)],                        # foot angled left
        ],
    },
    {
        'name': 'DALET', 'script': 'HEBREW', 'concept': 'D / DOOR',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 22), (22, 22)],                        # top bar R-to-L
            [(42, 22), (42, 48)],                        # right vertical
        ],
    },
    {
        'name': 'HE', 'script': 'HEBREW', 'concept': 'H / WINDOW',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 22), (22, 22)],                        # top bar
            [(42, 22), (42, 48)],                        # right vertical
            [(22, 28), (22, 48)],                        # left leg (gap at top)
        ],
    },
    {
        'name': 'VAV', 'script': 'HEBREW', 'concept': 'V / HOOK',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(34, 22), (30, 22), (30, 26)],              # small hook at top
            [(30, 22), (30, 48)],                        # vertical stroke
        ],
    },
    {
        'name': 'ZAYIN', 'script': 'HEBREW', 'concept': 'Z / WEAPON',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],                        # T-top bar
            [(32, 22), (32, 48)],                        # vertical shaft
        ],
    },
    {
        'name': 'CHET', 'script': 'HEBREW', 'concept': 'CH / FENCE',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 22), (22, 22)],                        # top bar connecting both
            [(42, 22), (42, 48)],                        # right vertical
            [(22, 22), (22, 48)],                        # left vertical
        ],
    },
    {
        'name': 'TET', 'script': 'HEBREW', 'concept': 'T / WHEEL',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(22, 28), (22, 48), (42, 48), (42, 28)],   # U-shape
            [(22, 28), (28, 22), (32, 30)],              # left side curling inward
        ],
    },
    {
        'name': 'YOD', 'script': 'HEBREW', 'concept': 'Y / HAND',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(34, 28), (32, 24), (30, 28), (32, 34)],   # small comma shape
        ],
    },
    {
        'name': 'KAF', 'script': 'HEBREW', 'concept': 'K / PALM',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 22), (26, 22)],                        # top bar
            [(42, 22), (42, 42), (34, 48), (26, 42)],   # right down and curve left
        ],
    },
    {
        'name': 'LAMED', 'script': 'HEBREW', 'concept': 'L / GOAD',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(36, 48), (36, 30)],                        # lower vertical
            [(36, 30), (30, 20), (28, 22)],              # tall ascending hook
        ],
    },
    {
        'name': 'NUN', 'script': 'HEBREW', 'concept': 'N / SNAKE',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(36, 22), (32, 22)],                        # small top serif
            [(36, 22), (36, 44), (32, 48)],              # vertical with curve
        ],
    },
    {
        'name': 'SAMEKH', 'script': 'HEBREW', 'concept': 'S / SUPPORT',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(24, 22), (40, 22), (40, 48), (24, 48), (24, 22)],  # closed rectangle
        ],
    },
    {
        'name': 'AYIN', 'script': 'HEBREW', 'concept': 'EYE',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(32, 34), (22, 22)],                        # left branch up
            [(32, 34), (42, 22)],                        # right branch up
            [(32, 34), (32, 48)],                        # stem down
        ],
    },
    {
        'name': 'PE', 'script': 'HEBREW', 'concept': 'P / MOUTH',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 22), (24, 22)],                        # top bar
            [(42, 22), (42, 48)],                        # right vertical
            [(42, 48), (24, 48)],                        # bottom bar
            [(24, 48), (24, 36)],                        # left partial vertical
            [(24, 36), (32, 30)],                        # inward spiral hook
        ],
    },
    {
        'name': 'TSADE', 'script': 'HEBREW', 'concept': 'TS / PLANT',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(26, 48), (26, 30), (32, 22)],              # left stroke rising
            [(38, 48), (38, 30), (44, 22)],              # right stroke curving out
        ],
    },
    {
        'name': 'QOF', 'script': 'HEBREW', 'concept': 'Q / MONKEY',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 22), (26, 22)],                        # top bar
            [(42, 22), (42, 36)],                        # right short vertical
            [(26, 22), (26, 50)],                        # left long descender
        ],
    },
    {
        'name': 'RESH', 'script': 'HEBREW', 'concept': 'R / HEAD',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 26), (38, 22), (24, 22)],              # rounded top bar
            [(42, 26), (42, 48)],                        # right vertical
        ],
    },
    {
        'name': 'TAV', 'script': 'HEBREW', 'concept': 'T / MARK',
        'origin': 'PROTO-SINAITIC ~1500 BC',
        'ink': _HEBREW_INK, 'paper': _HEBREW_PAPER,
        'strokes': [
            [(42, 22), (22, 22)],                        # top bar
            [(42, 22), (42, 48)],                        # right vertical
            [(22, 22), (22, 40)],                        # left leg (shorter)
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
    {
        'name': 'URUZ', 'script': 'RUNIC', 'concept': 'AUROCHS',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],                        # left stave
            [(24, 20), (40, 28)],                        # diagonal top
            [(40, 28), (40, 48)],                        # right stave
        ],
    },
    {
        'name': 'RAIDHO', 'script': 'RUNIC', 'concept': 'RIDE',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(26, 20), (26, 48)],                        # vertical stave
            [(26, 20), (40, 28)],                        # upper diagonal out
            [(40, 28), (26, 34)],                        # upper diagonal back
            [(26, 34), (40, 48)],                        # leg diagonal
        ],
    },
    {
        'name': 'KENAZ', 'script': 'RUNIC', 'concept': 'TORCH',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(40, 20), (26, 34)],                        # upper diagonal inward
            [(26, 34), (40, 48)],                        # lower diagonal outward
        ],
    },
    {
        'name': 'GEBO', 'script': 'RUNIC', 'concept': 'GIFT',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(22, 22), (42, 46)],                        # diagonal down-right
            [(42, 22), (22, 46)],                        # diagonal down-left
        ],
    },
    {
        'name': 'WUNJO', 'script': 'RUNIC', 'concept': 'JOY',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(28, 20), (28, 48)],                        # vertical stave
            [(28, 20), (42, 20)],                        # flag top
            [(42, 20), (42, 32)],                        # flag right
            [(42, 32), (28, 32)],                        # flag bottom
        ],
    },
    {
        'name': 'HAGALAZ', 'script': 'RUNIC', 'concept': 'HAIL',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],                        # left stave
            [(40, 20), (40, 48)],                        # right stave
            [(24, 28), (40, 40)],                        # cross bar diagonal
        ],
    },
    {
        'name': 'NAUTHIZ', 'script': 'RUNIC', 'concept': 'NEED',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                        # vertical stave
            [(22, 28), (42, 40)],                        # diagonal cross
        ],
    },
    {
        'name': 'ISA', 'script': 'RUNIC', 'concept': 'ICE',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                        # single vertical stave
        ],
    },
    {
        'name': 'JERA', 'script': 'RUNIC', 'concept': 'YEAR / HARVEST',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 20), (22, 28), (32, 34)],              # upper < shape
            [(32, 34), (42, 42), (32, 48)],              # lower > shape
        ],
    },
    {
        'name': 'EIHWAZ', 'script': 'RUNIC', 'concept': 'YEW TREE',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                        # vertical stave
            [(32, 26), (22, 32)],                        # upper-left branch
            [(32, 38), (42, 44)],                        # lower-right branch
        ],
    },
    {
        'name': 'PERTHRO', 'script': 'RUNIC', 'concept': 'DICE CUP',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(26, 20), (26, 48)],                        # vertical stave
            [(26, 24), (40, 30)],                        # upper arm out
            [(40, 30), (40, 38)],                        # right edge
            [(40, 38), (26, 44)],                        # lower arm back
        ],
    },
    {
        'name': 'ALGIZ', 'script': 'RUNIC', 'concept': 'ELK / PROTECTION',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 48), (32, 20)],                        # vertical stave upward
            [(32, 20), (20, 28)],                        # left prong
            [(32, 20), (44, 28)],                        # right prong
        ],
    },
    {
        'name': 'SOWILO', 'script': 'RUNIC', 'concept': 'SUN',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(40, 20), (24, 30)],                        # upper zig
            [(24, 30), (40, 38)],                        # middle zag
            [(40, 38), (24, 48)],                        # lower zig
        ],
    },
    {
        'name': 'TIWAZ', 'script': 'RUNIC', 'concept': 'TYR / VICTORY',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                        # vertical stave
            [(20, 28), (32, 20)],                        # left arrow arm
            [(44, 28), (32, 20)],                        # right arrow arm
        ],
    },
    {
        'name': 'EHWAZ', 'script': 'RUNIC', 'concept': 'HORSE',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(22, 48), (22, 20)],                        # left stave
            [(22, 20), (32, 34)],                        # left peak to center
            [(32, 34), (42, 20)],                        # center to right peak
            [(42, 20), (42, 48)],                        # right stave
        ],
    },
    {
        'name': 'MANNAZ', 'script': 'RUNIC', 'concept': 'HUMAN',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(22, 48), (22, 20)],                        # left stave
            [(22, 20), (32, 30)],                        # left to center
            [(32, 30), (42, 20)],                        # center to right
            [(42, 20), (42, 48)],                        # right stave
            [(22, 30), (42, 30)],                        # cross bar
        ],
    },
    {
        'name': 'LAGUZ', 'script': 'RUNIC', 'concept': 'WATER / LAKE',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(28, 48), (28, 20)],                        # vertical stave
            [(28, 20), (42, 28)],                        # diagonal arm up-right
        ],
    },
    {
        'name': 'INGWAZ', 'script': 'RUNIC', 'concept': 'ING / FERTILITY',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 20), (44, 34)],                        # top to right
            [(44, 34), (32, 48)],                        # right to bottom
            [(32, 48), (20, 34)],                        # bottom to left
            [(20, 34), (32, 20)],                        # left to top
        ],
    },
    {
        'name': 'DAGAZ', 'script': 'RUNIC', 'concept': 'DAY / DAWN',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(22, 20), (22, 48)],                        # left stave
            [(42, 20), (42, 48)],                        # right stave
            [(22, 20), (42, 34)],                        # upper X arm
            [(42, 20), (22, 34)],                        # upper X arm reverse
            [(22, 34), (42, 48)],                        # lower X arm
            [(42, 34), (22, 48)],                        # lower X arm reverse
        ],
    },
    {
        'name': 'OTHALA', 'script': 'RUNIC', 'concept': 'HERITAGE / HOME',
        'origin': 'ELDER FUTHARK ~150 AD',
        'ink': _RUNIC_INK, 'paper': _RUNIC_PAPER,
        'strokes': [
            [(32, 20), (44, 30)],                        # diamond top-right
            [(44, 30), (32, 40)],                        # diamond right-bottom
            [(32, 40), (20, 30)],                        # diamond bottom-left
            [(20, 30), (32, 20)],                        # diamond left-top
            [(32, 40), (22, 50)],                        # left leg
            [(32, 40), (42, 50)],                        # right leg
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
    {
        'name': 'GIM', 'script': 'ARMENIAN', 'concept': 'G',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (38, 22)],                        # top bar
            [(38, 22), (38, 36)],                        # right partial vertical
            [(38, 36), (30, 48)],                        # diagonal foot
        ],
    },
    {
        'name': 'DA', 'script': 'ARMENIAN', 'concept': 'D',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 48)],                        # right vertical
        ],
    },
    {
        'name': 'ECH', 'script': 'ARMENIAN', 'concept': 'E',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],                        # top bar
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 34), (36, 34)],                        # middle bar
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'ZA', 'script': 'ARMENIAN', 'concept': 'Z',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (24, 48)],                        # diagonal
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'E', 'script': 'ARMENIAN', 'concept': 'E (LONG)',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(32, 22), (24, 30), (24, 42), (32, 48)],   # left curve
            [(32, 22), (40, 30), (40, 42), (32, 48)],   # right curve
        ],
    },
    {
        'name': 'ET', 'script': 'ARMENIAN', 'concept': 'SCHWA',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 34), (40, 34)],                        # middle bar
            [(40, 22), (40, 48)],                        # right vertical
            [(32, 34), (32, 48)],                        # center descender
        ],
    },
    {
        'name': 'TO', 'script': 'ARMENIAN', 'concept': "T'",
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],                        # top bar
            [(32, 22), (32, 48)],                        # center vertical
        ],
    },
    {
        'name': 'ZHE', 'script': 'ARMENIAN', 'concept': 'ZH',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 34), (40, 22)],                        # upper diagonal
            [(24, 34), (40, 48)],                        # lower diagonal
        ],
    },
    {
        'name': 'INI', 'script': 'ARMENIAN', 'concept': 'I',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # center vertical
            [(26, 22), (38, 22)],                        # top serif
            [(26, 48), (38, 48)],                        # bottom serif
        ],
    },
    {
        'name': 'LYUN', 'script': 'ARMENIAN', 'concept': 'L',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 48), (24, 22)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 34)],                        # right short vertical
            [(40, 34), (32, 48)],                        # right foot diagonal
        ],
    },
    {
        'name': 'KHE', 'script': 'ARMENIAN', 'concept': 'KH',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 48)],                        # diagonal down-right
            [(40, 22), (24, 48)],                        # diagonal down-left
            [(24, 22), (40, 22)],                        # top bar
        ],
    },
    {
        'name': 'TSA', 'script': 'ARMENIAN', 'concept': 'TS',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 42), (32, 48)],              # left vertical + foot
            [(40, 22), (40, 42), (32, 48)],              # right vertical + foot
            [(24, 34), (40, 34)],                        # middle bar
        ],
    },
    {
        'name': 'KEN', 'script': 'ARMENIAN', 'concept': 'K',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 34), (40, 22)],                        # upper arm
            [(24, 34), (40, 48)],                        # lower arm
        ],
    },
    {
        'name': 'HO', 'script': 'ARMENIAN', 'concept': 'H',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(40, 22), (40, 48)],                        # right vertical
            [(24, 34), (40, 34)],                        # crossbar
            [(40, 22), (44, 20)],                        # right top serif
        ],
    },
    {
        'name': 'DZA', 'script': 'ARMENIAN', 'concept': 'DZ',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],                        # top bar
            [(26, 22), (26, 36), (32, 42)],              # left down
            [(38, 22), (38, 36), (32, 42)],              # right down
            [(32, 42), (32, 50)],                        # tail
        ],
    },
    {
        'name': 'GHAT', 'script': 'ARMENIAN', 'concept': 'GH',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 48)],                        # right vertical
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'CHEH', 'script': 'ARMENIAN', 'concept': 'CH',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 36), (32, 42)],              # right hook
            [(24, 48), (36, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'MEN', 'script': 'ARMENIAN', 'concept': 'M',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(22, 48), (22, 22)],                        # left vertical
            [(22, 22), (32, 36)],                        # left diagonal down
            [(32, 36), (42, 22)],                        # right diagonal up
            [(42, 22), (42, 48)],                        # right vertical
        ],
    },
    {
        'name': 'YI', 'script': 'ARMENIAN', 'concept': 'Y',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (32, 36)],                        # left diagonal
            [(40, 22), (32, 36)],                        # right diagonal
            [(32, 36), (32, 48)],                        # vertical tail
        ],
    },
    {
        'name': 'NOW', 'script': 'ARMENIAN', 'concept': 'N',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 48)],                        # diagonal
            [(40, 22), (40, 48)],                        # right vertical
        ],
    },
    {
        'name': 'SHA', 'script': 'ARMENIAN', 'concept': 'SH',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],                        # left vertical
            [(32, 22), (32, 48)],                        # center vertical
            [(42, 22), (42, 48)],                        # right vertical
            [(22, 48), (42, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'VO', 'script': 'ARMENIAN', 'concept': 'V',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (32, 48)],                        # left diagonal down
            [(40, 22), (32, 48)],                        # right diagonal down
        ],
    },
    {
        'name': 'CHA', 'script': 'ARMENIAN', 'concept': "CH'",
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 34)],                        # right short descender
            [(24, 34), (40, 34)],                        # middle bar
        ],
    },
    {
        'name': 'PE', 'script': 'ARMENIAN', 'concept': 'P',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 34), (24, 34)],              # right side and back
        ],
    },
    {
        'name': 'JE', 'script': 'ARMENIAN', 'concept': 'J',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(32, 22), (24, 30), (24, 42), (32, 48)],   # left curve
            [(32, 22), (40, 30)],                        # right hook
            [(32, 48), (40, 42)],                        # right foot
        ],
    },
    {
        'name': 'RRA', 'script': 'ARMENIAN', 'concept': 'RR',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 34), (24, 34)],              # upper bump back
            [(24, 34), (40, 48)],                        # leg diagonal
        ],
    },
    {
        'name': 'SE', 'script': 'ARMENIAN', 'concept': 'S',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(40, 22), (24, 22), (24, 34), (40, 34),
             (40, 48), (24, 48)],                        # S-shape path
        ],
    },
    {
        'name': 'VEV', 'script': 'ARMENIAN', 'concept': "V'",
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (32, 36)],                        # left diagonal
            [(40, 22), (32, 36)],                        # right diagonal
            [(32, 36), (24, 48)],                        # left foot
            [(32, 36), (40, 48)],                        # right foot
        ],
    },
    {
        'name': 'TYUN', 'script': 'ARMENIAN', 'concept': 'T',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],                        # top bar
            [(32, 22), (32, 48)],                        # center vertical
            [(26, 48), (38, 48)],                        # bottom serif
        ],
    },
    {
        'name': 'RE', 'script': 'ARMENIAN', 'concept': 'R',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (38, 22)],                        # top bar
            [(38, 22), (42, 28), (38, 34), (24, 34)],   # upper bump
        ],
    },
    {
        'name': 'TSO', 'script': 'ARMENIAN', 'concept': "TS'",
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 42), (32, 48)],              # left down
            [(40, 22), (40, 42), (32, 48)],              # right down
        ],
    },
    {
        'name': 'VYUN', 'script': 'ARMENIAN', 'concept': 'W',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(20, 22), (26, 48)],                        # first V left
            [(26, 48), (32, 22)],                        # first V right
            [(32, 22), (38, 48)],                        # second V left
            [(38, 48), (44, 22)],                        # second V right
        ],
    },
    {
        'name': 'PYUR', 'script': 'ARMENIAN', 'concept': "P'",
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 34)],                        # right partial
            [(24, 34), (40, 34)],                        # middle bar
            [(24, 48), (34, 48)],                        # bottom serif
        ],
    },
    {
        'name': 'KE', 'script': 'ARMENIAN', 'concept': "K'",
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 28), (40, 22)],                        # upper arm out
            [(24, 36), (40, 48)],                        # lower arm out
        ],
    },
    {
        'name': 'O', 'script': 'ARMENIAN', 'concept': 'O',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 34), (32, 22), (40, 34), (32, 48), (24, 34)],  # diamond/circle
        ],
    },
    {
        'name': 'FE', 'script': 'ARMENIAN', 'concept': 'F',
        'origin': 'MESROP 405 AD',
        'ink': _ARMENIAN_INK, 'paper': _ARMENIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],                        # top bar
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 34), (36, 34)],                        # middle bar
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
        'name': 'ANI', 'script': 'GEORGIAN', 'concept': 'AN (LETTER)',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 24), (24, 44), (32, 48), (40, 44), (40, 24)],  # U-shape
            [(32, 20), (32, 34)],                        # center stem
        ],
    },
    {
        'name': 'BAN', 'script': 'GEORGIAN', 'concept': 'BAN (LETTER)',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 36), (32, 42), (24, 36)],   # right curve back
        ],
    },
    {
        'name': 'GAN', 'script': 'GEORGIAN', 'concept': 'GAN (LETTER)',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],                        # top bar
            [(26, 22), (26, 36), (32, 42), (38, 36), (38, 22)],  # rounded body
            [(32, 42), (32, 50)],                        # descender
        ],
    },
    {
        'name': 'DON', 'script': 'GEORGIAN', 'concept': 'D',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],                        # top bar
            [(24, 22), (24, 42), (32, 48), (40, 42), (40, 22)],  # U-shape
        ],
    },
    {
        'name': 'ENI', 'script': 'GEORGIAN', 'concept': 'E',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(24, 34), (36, 34)],                        # middle bar
        ],
    },
    {
        'name': 'VINI', 'script': 'GEORGIAN', 'concept': 'V',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (32, 48)],                        # left diagonal down
            [(40, 22), (32, 48)],                        # right diagonal down
        ],
    },
    {
        'name': 'ZENI', 'script': 'GEORGIAN', 'concept': 'Z',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (24, 48)],                        # diagonal
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'TAN', 'script': 'GEORGIAN', 'concept': 'T',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],                        # top bar
            [(32, 22), (32, 48)],                        # center vertical
        ],
    },
    {
        'name': 'INI', 'script': 'GEORGIAN', 'concept': 'I',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # center vertical
            [(28, 22), (36, 22)],                        # top serif
        ],
    },
    {
        'name': "K'ANI", 'script': 'GEORGIAN', 'concept': "K'",
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 34), (40, 22)],                        # upper arm
            [(24, 34), (40, 48)],                        # lower arm
        ],
    },
    {
        'name': 'LASI', 'script': 'GEORGIAN', 'concept': 'L',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 48), (24, 22)],                        # left vertical up
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 48)],                        # right vertical
        ],
    },
    {
        'name': 'MANI', 'script': 'GEORGIAN', 'concept': 'M',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(22, 48), (22, 22)],                        # left vertical
            [(22, 22), (32, 36)],                        # left peak down
            [(32, 36), (42, 22)],                        # right peak up
            [(42, 22), (42, 48)],                        # right vertical
        ],
    },
    {
        'name': 'NARI', 'script': 'GEORGIAN', 'concept': 'N',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 48)],                        # diagonal
            [(40, 22), (40, 48)],                        # right vertical
        ],
    },
    {
        'name': 'ONI', 'script': 'GEORGIAN', 'concept': 'O',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 34), (32, 22), (40, 34), (32, 48), (24, 34)],  # diamond shape
        ],
    },
    {
        'name': "P'ARI", 'script': 'GEORGIAN', 'concept': "P'",
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 34), (24, 34)],              # right bump back
        ],
    },
    {
        'name': 'ZHANI', 'script': 'GEORGIAN', 'concept': 'ZH',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # center vertical
            [(20, 34), (32, 22)],                        # left arm up
            [(44, 34), (32, 22)],                        # right arm up
        ],
    },
    {
        'name': 'RAE', 'script': 'GEORGIAN', 'concept': 'R',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (38, 22)],                        # top bar
            [(38, 22), (42, 28), (38, 34), (24, 34)],   # bump back
        ],
    },
    {
        'name': 'SANI', 'script': 'GEORGIAN', 'concept': 'S',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(40, 22), (24, 22), (24, 34), (40, 34),
             (40, 48), (24, 48)],                        # S-path
        ],
    },
    {
        'name': "T'ARI", 'script': 'GEORGIAN', 'concept': "T'",
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],                        # top bar
            [(32, 22), (32, 48)],                        # center vertical
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'UNI', 'script': 'GEORGIAN', 'concept': 'U',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 42), (32, 48), (40, 42), (40, 22)],  # U-shape
        ],
    },
    {
        'name': 'PARI', 'script': 'GEORGIAN', 'concept': 'P',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 48)],                        # right vertical
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'KANI', 'script': 'GEORGIAN', 'concept': 'K',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(40, 22), (24, 36)],                        # upper diagonal in
            [(24, 36), (40, 48)],                        # lower diagonal out
        ],
    },
    {
        'name': 'GHANI', 'script': 'GEORGIAN', 'concept': 'GH',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],                        # top bar
            [(26, 22), (26, 36), (32, 42), (38, 36), (38, 22)],  # round body
            [(26, 42), (26, 50)],                        # left descender
        ],
    },
    {
        'name': 'QARI', 'script': 'GEORGIAN', 'concept': 'Q',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 34), (32, 22), (40, 34), (32, 48), (24, 34)],  # circle
            [(32, 48), (32, 52)],                        # tail descender
        ],
    },
    {
        'name': 'SHINI', 'script': 'GEORGIAN', 'concept': 'SH',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],                        # left vertical
            [(32, 22), (32, 48)],                        # center vertical
            [(42, 22), (42, 48)],                        # right vertical
            [(22, 22), (42, 22)],                        # top connecting bar
        ],
    },
    {
        'name': 'CHINI', 'script': 'GEORGIAN', 'concept': 'CH',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 36), (32, 42)],              # right curve in
        ],
    },
    {
        'name': 'TSANI', 'script': 'GEORGIAN', 'concept': 'TS',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 42), (32, 48)],              # left vertical + foot
            [(40, 22), (40, 42), (32, 48)],              # right vertical + foot
        ],
    },
    {
        'name': 'DZILI', 'script': 'GEORGIAN', 'concept': 'DZ',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],                        # top bar
            [(24, 22), (24, 36), (32, 42)],              # left down to center
            [(40, 22), (40, 36), (32, 42)],              # right down to center
            [(32, 42), (32, 50)],                        # descender
        ],
    },
    {
        'name': "TS'ILI", 'script': 'GEORGIAN', 'concept': "TS'",
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 42), (32, 48)],              # left arm
            [(40, 22), (40, 42), (32, 48)],              # right arm
            [(32, 48), (32, 52)],                        # extra tail
        ],
    },
    {
        'name': "CH'ARI", 'script': 'GEORGIAN', 'concept': "CH'",
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(24, 22), (40, 22)],                        # top bar
            [(40, 22), (40, 34)],                        # right short vertical
            [(24, 34), (40, 34)],                        # middle bar
        ],
    },
    {
        'name': 'KHANI', 'script': 'GEORGIAN', 'concept': 'KH',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (40, 48)],                        # diagonal down-right
            [(40, 22), (24, 48)],                        # diagonal down-left
        ],
    },
    {
        'name': 'JANI', 'script': 'GEORGIAN', 'concept': 'J',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(32, 22), (32, 42), (26, 48)],              # vertical with left foot
            [(28, 22), (36, 22)],                        # top serif
        ],
    },
    {
        'name': 'HARI', 'script': 'GEORGIAN', 'concept': 'H',
        'origin': 'GEORGIA ~430 AD',
        'ink': _GEORGIAN_INK, 'paper': _GEORGIAN_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                        # left vertical
            [(40, 22), (40, 48)],                        # right vertical
            [(24, 34), (40, 34)],                        # crossbar
        ],
    },
    # ── TIBETAN ──────────────────────────────────────────────────
    {
        'name': 'OM', 'script': 'TIBETAN', 'concept': 'SACRED SYLLABLE',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],                        # head bar
            [(26, 22), (26, 36), (20, 44)],              # left descender
            [(38, 22), (38, 36), (44, 44)],              # right descender
            [(26, 36), (38, 36)],                        # middle connector
            [(32, 36), (32, 50)],                        # bottom tail
        ],
    },
    {
        'name': 'KA', 'script': 'TIBETAN', 'concept': 'KA (CONSONANT)',
        'origin': 'TIBET ~650 AD',
        'ink': _TIBETAN_INK, 'paper': _TIBETAN_PAPER, 'thick': True,
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
        'name': 'A', 'script': 'TAMIL', 'concept': 'A (VOWEL)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
        'strokes': [
            [(24, 24), (32, 20), (40, 24), (40, 34),
             (32, 38), (24, 34), (24, 24)],              # top loop
            [(32, 38), (32, 50)],                        # descender
        ],
    },
    {
        'name': 'KA', 'script': 'TAMIL', 'concept': 'KA (CONSONANT)',
        'origin': 'TAMIL BRAHMI ~300 BC',
        'ink': _TAMIL_INK, 'paper': _TAMIL_PAPER,
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
        'name': 'TSA', 'script': 'CHEROKEE', 'concept': 'TSA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],                        # top bar
            [(32, 22), (32, 48)],                        # center vertical
            [(20, 36), (44, 36)],                        # middle bar
            [(24, 48), (40, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'A', 'script': 'CHEROKEE', 'concept': 'A',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 48), (32, 20), (44, 48)],              # A-shape outer
            [(26, 38), (38, 38)],                        # crossbar
            [(32, 38), (32, 48)],                        # center leg down
        ],
    },
    {
        'name': 'E', 'script': 'CHEROKEE', 'concept': 'E',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(22, 22), (22, 48)],
            [(22, 35), (38, 35)],
            [(22, 48), (42, 48)],
        ],
    },
    {
        'name': 'I', 'script': 'CHEROKEE', 'concept': 'I',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(32, 22), (32, 48)],
            [(22, 48), (42, 48)],
        ],
    },
    {
        'name': 'O', 'script': 'CHEROKEE', 'concept': 'O',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(26, 22), (38, 22), (44, 30), (44, 40), (38, 48), (26, 48), (20, 40), (20, 30), (26, 22)],
        ],
    },
    {
        'name': 'U', 'script': 'CHEROKEE', 'concept': 'U',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(42, 22), (34, 28), (26, 36), (34, 42), (42, 48)],
        ],
    },
    {
        'name': 'V', 'script': 'CHEROKEE', 'concept': 'V',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 34), (32, 34), (32, 22)],
            [(32, 34), (32, 48)],
        ],
    },
    {
        'name': 'GA', 'script': 'CHEROKEE', 'concept': 'GA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 22), (44, 22)],
            [(32, 22), (20, 48)],
            [(32, 22), (44, 48)],
        ],
    },
    {
        'name': 'KA', 'script': 'CHEROKEE', 'concept': 'KA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(36, 22), (36, 48)],
            [(36, 48), (22, 40)],
        ],
    },
    {
        'name': 'GE', 'script': 'CHEROKEE', 'concept': 'GE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(42, 22), (42, 36)],
            [(22, 36), (42, 36)],
        ],
    },
    {
        'name': 'GI', 'script': 'CHEROKEE', 'concept': 'GI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (32, 35)],
            [(42, 22), (32, 35)],
            [(32, 35), (32, 48)],
        ],
    },
    {
        'name': 'GO', 'script': 'CHEROKEE', 'concept': 'GO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 48), (32, 22), (44, 48)],
            [(26, 36), (38, 36)],
        ],
    },
    {
        'name': 'GU', 'script': 'CHEROKEE', 'concept': 'GU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 35), (44, 35)],
            [(32, 22), (32, 48)],
        ],
    },
    {
        'name': 'GV', 'script': 'CHEROKEE', 'concept': 'GV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22), (32, 48), (22, 22)],
        ],
    },
    {
        'name': 'HA', 'script': 'CHEROKEE', 'concept': 'HA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(38, 22), (38, 48)],
            [(38, 22), (22, 28), (22, 38)],
        ],
    },
    {
        'name': 'HE', 'script': 'CHEROKEE', 'concept': 'HE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(22, 22), (22, 35), (42, 35)],
        ],
    },
    {
        'name': 'HI', 'script': 'CHEROKEE', 'concept': 'HI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(22, 22), (22, 48)],
            [(22, 35), (38, 35)],
        ],
    },
    {
        'name': 'HO', 'script': 'CHEROKEE', 'concept': 'HO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 22), (42, 35)],
            [(22, 48), (42, 35)],
        ],
    },
    {
        'name': 'HU', 'script': 'CHEROKEE', 'concept': 'HU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(42, 22), (22, 22), (22, 48), (42, 48)],
            [(22, 35), (36, 35)],
        ],
    },
    {
        'name': 'HV', 'script': 'CHEROKEE', 'concept': 'HV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(32, 22), (22, 48)],
            [(42, 22), (42, 48)],
        ],
    },
    {
        'name': 'LA', 'script': 'CHEROKEE', 'concept': 'LA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 22), (28, 48), (36, 22), (44, 48)],
        ],
    },
    {
        'name': 'LE', 'script': 'CHEROKEE', 'concept': 'LE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(42, 22), (22, 30), (42, 38), (22, 48)],
        ],
    },
    {
        'name': 'LI', 'script': 'CHEROKEE', 'concept': 'LI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(32, 22), (32, 48)],
        ],
    },
    {
        'name': 'LO', 'script': 'CHEROKEE', 'concept': 'LO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(42, 22), (22, 22), (22, 48), (42, 48)],
            [(22, 48), (42, 35)],
        ],
    },
    {
        'name': 'LU', 'script': 'CHEROKEE', 'concept': 'LU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 22), (36, 35)],
            [(36, 35), (22, 48)],
            [(36, 35), (42, 48)],
        ],
    },
    {
        'name': 'LV', 'script': 'CHEROKEE', 'concept': 'LV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 35), (42, 22)],
            [(22, 35), (42, 48)],
        ],
    },
    {
        'name': 'MA', 'script': 'CHEROKEE', 'concept': 'MA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(36, 22), (36, 48)],
            [(36, 35), (22, 22)],
            [(36, 35), (22, 48)],
        ],
    },
    {
        'name': 'ME', 'script': 'CHEROKEE', 'concept': 'ME',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (32, 48)],
            [(42, 22), (32, 48)],
            [(27, 35), (37, 35)],
        ],
    },
    {
        'name': 'MI', 'script': 'CHEROKEE', 'concept': 'MI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(42, 22), (42, 48)],
            [(22, 35), (42, 35)],
        ],
    },
    {
        'name': 'MO', 'script': 'CHEROKEE', 'concept': 'MO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 48), (22, 22), (32, 35), (42, 22), (42, 48)],
        ],
    },
    {
        'name': 'MU', 'script': 'CHEROKEE', 'concept': 'MU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 22), (42, 35)],
        ],
    },
    {
        'name': 'NA', 'script': 'CHEROKEE', 'concept': 'NA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(42, 22), (22, 48)],
            [(22, 48), (42, 48)],
        ],
    },
    {
        'name': 'NAH', 'script': 'CHEROKEE', 'concept': 'NAH',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(32, 22), (32, 48)],
            [(22, 48), (42, 48)],
            [(22, 35), (42, 35)],
        ],
    },
    {
        'name': 'NE', 'script': 'CHEROKEE', 'concept': 'NE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(42, 22), (22, 35), (42, 48)],
        ],
    },
    {
        'name': 'NI', 'script': 'CHEROKEE', 'concept': 'NI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(42, 22), (42, 48)],
            [(22, 36), (42, 36)],
        ],
    },
    {
        'name': 'NO', 'script': 'CHEROKEE', 'concept': 'NO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(22, 22), (22, 48)],
            [(42, 22), (42, 48)],
        ],
    },
    {
        'name': 'NU', 'script': 'CHEROKEE', 'concept': 'NU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48), (42, 48), (42, 22)],
        ],
    },
    {
        'name': 'NV', 'script': 'CHEROKEE', 'concept': 'NV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 48)],
            [(42, 22), (22, 48)],
            [(32, 22), (32, 48)],
        ],
    },
    {
        'name': 'QUA', 'script': 'CHEROKEE', 'concept': 'QUA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 48), (42, 48)],
            [(42, 48), (42, 35)],
        ],
    },
    {
        'name': 'QUE', 'script': 'CHEROKEE', 'concept': 'QUE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(26, 22), (38, 22), (44, 30), (44, 40), (38, 48), (26, 48), (20, 40), (20, 30), (26, 22)],
            [(36, 42), (44, 50)],
        ],
    },
    {
        'name': 'QUI', 'script': 'CHEROKEE', 'concept': 'QUI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 22), (28, 48), (36, 22), (44, 48)],
            [(24, 35), (40, 35)],
        ],
    },
    {
        'name': 'QUO', 'script': 'CHEROKEE', 'concept': 'QUO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(22, 48), (42, 48)],
            [(22, 22), (22, 48)],
        ],
    },
    {
        'name': 'QUU', 'script': 'CHEROKEE', 'concept': 'QUU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (32, 22), (42, 35), (32, 48), (22, 48)],
        ],
    },
    {
        'name': 'QUV', 'script': 'CHEROKEE', 'concept': 'QUV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 35)],
            [(42, 35), (22, 48)],
            [(32, 22), (32, 48)],
        ],
    },
    {
        'name': 'SA', 'script': 'CHEROKEE', 'concept': 'SA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(42, 22), (22, 22), (22, 35), (42, 35), (42, 48), (22, 48)],
        ],
    },
    {
        'name': 'SE', 'script': 'CHEROKEE', 'concept': 'SE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(42, 22), (42, 36)],
            [(22, 36), (42, 36)],
            [(22, 36), (22, 48)],
        ],
    },
    {
        'name': 'SI', 'script': 'CHEROKEE', 'concept': 'SI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],
            [(22, 30), (42, 30)],
        ],
    },
    {
        'name': 'SO', 'script': 'CHEROKEE', 'concept': 'SO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(26, 22), (38, 22), (44, 30), (44, 40), (38, 48), (26, 48), (20, 40), (20, 30), (26, 22)],
            [(22, 35), (42, 35)],
        ],
    },
    {
        'name': 'SU', 'script': 'CHEROKEE', 'concept': 'SU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 22), (42, 22)],
            [(22, 35), (36, 35)],
        ],
    },
    {
        'name': 'SV', 'script': 'CHEROKEE', 'concept': 'SV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 35)],
            [(22, 48), (42, 35)],
        ],
    },
    {
        'name': 'DA', 'script': 'CHEROKEE', 'concept': 'DA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],
            [(32, 22), (42, 28), (42, 42), (32, 48)],
        ],
    },
    {
        'name': 'DE', 'script': 'CHEROKEE', 'concept': 'DE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 22), (42, 22)],
            [(22, 48), (42, 48)],
        ],
    },
    {
        'name': 'DI', 'script': 'CHEROKEE', 'concept': 'DI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (32, 48)],
            [(42, 22), (32, 48)],
        ],
    },
    {
        'name': 'DO', 'script': 'CHEROKEE', 'concept': 'DO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 22), (42, 22)],
            [(42, 22), (42, 48)],
        ],
    },
    {
        'name': 'DU', 'script': 'CHEROKEE', 'concept': 'DU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 35), (22, 48)],
        ],
    },
    {
        'name': 'DV', 'script': 'CHEROKEE', 'concept': 'DV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(22, 22), (42, 48)],
            [(42, 22), (22, 48)],
        ],
    },
    {
        'name': 'DLA', 'script': 'CHEROKEE', 'concept': 'DLA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 48), (22, 22), (42, 22)],
            [(22, 35), (38, 35)],
        ],
    },
    {
        'name': 'TA', 'script': 'CHEROKEE', 'concept': 'TA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(32, 22), (32, 48)],
            [(22, 48), (42, 48)],
            [(22, 35), (32, 35)],
        ],
    },
    {
        'name': 'TE', 'script': 'CHEROKEE', 'concept': 'TE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(32, 22), (22, 48)],
            [(42, 22), (32, 48)],
        ],
    },
    {
        'name': 'TI', 'script': 'CHEROKEE', 'concept': 'TI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 35), (42, 35)],
            [(42, 22), (42, 48)],
        ],
    },
    {
        'name': 'TO', 'script': 'CHEROKEE', 'concept': 'TO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22), (42, 48), (22, 48)],
            [(32, 22), (32, 48)],
        ],
    },
    {
        'name': 'TU', 'script': 'CHEROKEE', 'concept': 'TU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48), (42, 48)],
            [(32, 35), (42, 35)],
        ],
    },
    {
        'name': 'TV', 'script': 'CHEROKEE', 'concept': 'TV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 48)],
            [(22, 48), (42, 22)],
        ],
    },
    {
        'name': 'TLA', 'script': 'CHEROKEE', 'concept': 'TLA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(26, 22), (26, 48)],
            [(26, 22), (42, 22), (42, 35), (26, 35)],
        ],
    },
    {
        'name': 'TLE', 'script': 'CHEROKEE', 'concept': 'TLE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(22, 22), (22, 48)],
            [(22, 48), (42, 48)],
            [(42, 22), (42, 48)],
        ],
    },
    {
        'name': 'TLI', 'script': 'CHEROKEE', 'concept': 'TLI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(32, 22), (22, 48)],
            [(32, 22), (42, 48)],
            [(22, 35), (42, 35)],
        ],
    },
    {
        'name': 'TLO', 'script': 'CHEROKEE', 'concept': 'TLO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 48), (22, 22)],
            [(22, 48), (42, 48)],
        ],
    },
    {
        'name': 'TLU', 'script': 'CHEROKEE', 'concept': 'TLU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 35), (42, 22)],
        ],
    },
    {
        'name': 'TLV', 'script': 'CHEROKEE', 'concept': 'TLV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(42, 22), (42, 48)],
            [(22, 22), (42, 48)],
        ],
    },
    {
        'name': 'WA', 'script': 'CHEROKEE', 'concept': 'WA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(36, 22), (36, 48)],
            [(36, 22), (22, 22)],
            [(36, 48), (22, 48)],
        ],
    },
    {
        'name': 'WE', 'script': 'CHEROKEE', 'concept': 'WE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 48)],
            [(22, 35), (42, 35)],
        ],
    },
    {
        'name': 'WI', 'script': 'CHEROKEE', 'concept': 'WI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 35), (42, 35)],
            [(32, 22), (32, 48)],
            [(22, 22), (42, 48)],
        ],
    },
    {
        'name': 'WO', 'script': 'CHEROKEE', 'concept': 'WO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22), (42, 48)],
            [(22, 35), (42, 35)],
        ],
    },
    {
        'name': 'WU', 'script': 'CHEROKEE', 'concept': 'WU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (32, 35), (42, 22)],
            [(32, 35), (32, 48)],
        ],
    },
    {
        'name': 'WV', 'script': 'CHEROKEE', 'concept': 'WV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 48), (42, 22)],
            [(42, 22), (42, 48)],
        ],
    },
    {
        'name': 'YA', 'script': 'CHEROKEE', 'concept': 'YA',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (32, 35), (42, 22)],
            [(22, 48), (32, 35), (42, 48)],
        ],
    },
    {
        'name': 'YE', 'script': 'CHEROKEE', 'concept': 'YE',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 22)],
            [(42, 22), (22, 48)],
        ],
    },
    {
        'name': 'YI', 'script': 'CHEROKEE', 'concept': 'YI',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(20, 22), (26, 48), (32, 22), (38, 48), (44, 22)],
        ],
    },
    {
        'name': 'YO', 'script': 'CHEROKEE', 'concept': 'YO',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(42, 22), (42, 48)],
            [(22, 22), (42, 22)],
        ],
    },
    {
        'name': 'YU', 'script': 'CHEROKEE', 'concept': 'YU',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(42, 22), (42, 48)],
            [(22, 48), (42, 48)],
        ],
    },
    {
        'name': 'YV', 'script': 'CHEROKEE', 'concept': 'YV',
        'origin': 'SEQUOYAH 1821 AD',
        'ink': _CHEROKEE_INK, 'paper': _CHEROKEE_PAPER,
        'strokes': [
            [(22, 22), (42, 48)],
            [(22, 35), (42, 35)],
            [(22, 48), (42, 22)],
        ],
    },
    # ── CHINESE (additional oracle bone) ────────────────────────
    {
        'name': 'YUE', 'script': 'CHINESE', 'concept': 'MOON',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(36, 22), (28, 26), (24, 34), (28, 42), (36, 46)],
            [(28, 34), (36, 34)],
        ],
    },
    {
        'name': 'TIAN', 'script': 'CHINESE', 'concept': 'HEAVEN / SKY',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(20, 34), (44, 34)],
            [(32, 22), (24, 48)],
            [(32, 22), (40, 48)],
        ],
    },
    {
        'name': 'DI', 'script': 'CHINESE', 'concept': 'EARTH',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(20, 24), (44, 24)],
            [(20, 36), (44, 36)],
            [(20, 48), (44, 48)],
            [(32, 24), (32, 48)],
        ],
    },
    {
        'name': 'FENG', 'script': 'CHINESE', 'concept': 'WIND',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(22, 22), (42, 22), (42, 40), (22, 40), (22, 22)],
            [(32, 40), (26, 50)],
            [(32, 40), (38, 50)],
        ],
    },
    {
        'name': 'YU', 'script': 'CHINESE', 'concept': 'RAIN',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(18, 22), (46, 22)],
            [(24, 28), (24, 32)],
            [(32, 28), (32, 32)],
            [(40, 28), (40, 32)],
            [(28, 36), (28, 40)],
            [(36, 36), (36, 40)],
        ],
    },
    {
        'name': 'NIAO', 'script': 'CHINESE', 'concept': 'BIRD',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(20, 30), (28, 24), (36, 24), (42, 30)],
            [(42, 30), (42, 40), (36, 46), (28, 46), (24, 40)],
            [(24, 40), (18, 48)],
            [(30, 30), (30, 32)],
        ],
    },
    {
        'name': 'YU2', 'script': 'CHINESE', 'concept': 'FISH',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (40, 28), (40, 38), (32, 44), (24, 38), (24, 28), (32, 20)],
            [(24, 33), (40, 33)],
            [(28, 44), (22, 50)],
            [(36, 44), (42, 50)],
        ],
    },
    {
        'name': 'MA', 'script': 'CHINESE', 'concept': 'HORSE',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (38, 24), (38, 34), (32, 38), (26, 34), (26, 24), (32, 20)],
            [(26, 38), (22, 48)],
            [(32, 38), (32, 48)],
            [(38, 38), (42, 48)],
        ],
    },
    {
        'name': 'NIU', 'script': 'CHINESE', 'concept': 'OX',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(22, 20), (32, 28)],
            [(42, 20), (32, 28)],
            [(32, 28), (32, 48)],
            [(22, 38), (42, 38)],
        ],
    },
    {
        'name': 'YANG', 'script': 'CHINESE', 'concept': 'SHEEP',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(24, 20), (32, 26)],
            [(40, 20), (32, 26)],
            [(32, 26), (32, 48)],
            [(22, 34), (42, 34)],
            [(22, 42), (42, 42)],
        ],
    },
    {
        'name': 'GOU', 'script': 'CHINESE', 'concept': 'DOG',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(28, 22), (28, 40), (22, 48)],
            [(28, 22), (36, 26), (36, 34)],
            [(36, 34), (42, 42)],
        ],
    },
    {
        'name': 'DA', 'script': 'CHINESE', 'concept': 'BIG',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(18, 34), (46, 34)],
            [(32, 20), (32, 48)],
            [(32, 34), (20, 48)],
            [(32, 34), (44, 48)],
        ],
    },
    {
        'name': 'XIAO', 'script': 'CHINESE', 'concept': 'SMALL',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 48)],
            [(24, 30), (22, 34)],
            [(40, 30), (42, 34)],
        ],
    },
    {
        'name': 'ZHONG', 'script': 'CHINESE', 'concept': 'MIDDLE',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(24, 24), (40, 24), (40, 44), (24, 44), (24, 24)],
            [(32, 20), (32, 50)],
        ],
    },
    {
        'name': 'SHANG', 'script': 'CHINESE', 'concept': 'ABOVE',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 22), (32, 38)],
            [(22, 32), (42, 32)],
            [(20, 44), (44, 44)],
        ],
    },
    {
        'name': 'XIA', 'script': 'CHINESE', 'concept': 'BELOW',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(20, 24), (44, 24)],
            [(32, 30), (32, 44)],
            [(22, 36), (42, 36)],
        ],
    },
    {
        'name': 'ZUO', 'script': 'CHINESE', 'concept': 'LEFT',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (22, 30)],
            [(32, 20), (32, 48)],
            [(22, 42), (42, 42)],
        ],
    },
    {
        'name': 'YOU', 'script': 'CHINESE', 'concept': 'RIGHT',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (42, 30)],
            [(32, 20), (32, 48)],
            [(22, 42), (42, 42)],
        ],
    },
    {
        'name': 'WANG', 'script': 'CHINESE', 'concept': 'KING',
        'origin': 'ORACLE BONE ~1200 BC',
        'ink': _CHINESE_INK, 'paper': _CHINESE_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],
            [(20, 35), (44, 35)],
            [(20, 48), (44, 48)],
            [(32, 22), (32, 48)],
        ],
    },
    # ── ETHIOPIC (additional Ge'ez) ─────────────────────────────
    {
        'name': 'HHU', 'script': 'ETHIOPIC', 'concept': 'HHU',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (28, 44)],
            [(36, 22), (36, 44)],
            [(28, 22), (36, 22)],
            [(28, 44), (24, 48)],
            [(36, 44), (40, 48)],
        ],
    },
    {
        'name': 'HI', 'script': 'ETHIOPIC', 'concept': 'HI',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (28, 44)],
            [(36, 22), (36, 44)],
            [(28, 34), (36, 34)],
            [(28, 44), (36, 44)],
        ],
    },
    {
        'name': 'HAA', 'script': 'ETHIOPIC', 'concept': 'HAA',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (28, 48)],
            [(36, 22), (36, 48)],
            [(28, 22), (36, 22)],
            [(28, 48), (36, 48)],
        ],
    },
    {
        'name': 'HEE', 'script': 'ETHIOPIC', 'concept': 'HEE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (28, 44)],
            [(36, 22), (36, 44)],
            [(28, 22), (36, 22)],
            [(28, 34), (36, 34)],
            [(36, 44), (42, 44)],
        ],
    },
    {
        'name': 'HO', 'script': 'ETHIOPIC', 'concept': 'HO',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (28, 44)],
            [(36, 22), (36, 44)],
            [(28, 22), (36, 22)],
            [(28, 44), (36, 44), (36, 48)],
        ],
    },
    {
        'name': 'ME', 'script': 'ETHIOPIC', 'concept': 'ME',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(24, 22), (32, 22), (40, 22)],
            [(24, 22), (24, 44)],
            [(40, 22), (40, 44)],
            [(24, 44), (28, 48)],
            [(40, 44), (36, 48)],
        ],
    },
    {
        'name': 'MU', 'script': 'ETHIOPIC', 'concept': 'MU',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],
            [(24, 22), (24, 44)],
            [(40, 22), (40, 44)],
            [(24, 44), (40, 44)],
        ],
    },
    {
        'name': 'MI', 'script': 'ETHIOPIC', 'concept': 'MI',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],
            [(24, 22), (24, 44)],
            [(40, 22), (40, 44)],
            [(24, 34), (40, 34)],
        ],
    },
    {
        'name': 'MA', 'script': 'ETHIOPIC', 'concept': 'MA',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],
            [(24, 22), (24, 48)],
            [(40, 22), (40, 48)],
        ],
    },
    {
        'name': 'MEE', 'script': 'ETHIOPIC', 'concept': 'MEE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],
            [(24, 22), (24, 44)],
            [(40, 22), (40, 44)],
            [(40, 44), (46, 44)],
        ],
    },
    {
        'name': 'MO', 'script': 'ETHIOPIC', 'concept': 'MO',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(24, 22), (40, 22)],
            [(24, 22), (24, 44)],
            [(40, 22), (40, 44)],
            [(24, 44), (40, 44), (40, 48)],
        ],
    },
    {
        'name': 'SE', 'script': 'ETHIOPIC', 'concept': 'SE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (24, 28), (24, 40), (32, 46)],
            [(32, 22), (40, 28), (40, 40), (32, 46)],
            [(32, 46), (28, 50)],
            [(32, 46), (36, 50)],
        ],
    },
    {
        'name': 'SU', 'script': 'ETHIOPIC', 'concept': 'SU',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (24, 28), (24, 40), (32, 46)],
            [(32, 22), (40, 28), (40, 40), (32, 46)],
            [(32, 46), (32, 50)],
        ],
    },
    {
        'name': 'SI', 'script': 'ETHIOPIC', 'concept': 'SI',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (24, 28), (24, 40), (32, 46)],
            [(32, 22), (40, 28), (40, 40), (32, 46)],
            [(24, 34), (40, 34)],
        ],
    },
    {
        'name': 'SA', 'script': 'ETHIOPIC', 'concept': 'SA',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (24, 28), (24, 44), (32, 48)],
            [(32, 22), (40, 28), (40, 44), (32, 48)],
        ],
    },
    {
        'name': 'SEE', 'script': 'ETHIOPIC', 'concept': 'SEE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (24, 28), (24, 40), (32, 46)],
            [(32, 22), (40, 28), (40, 40), (32, 46)],
            [(40, 40), (46, 40)],
        ],
    },
    {
        'name': 'SO', 'script': 'ETHIOPIC', 'concept': 'SO',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (24, 28), (24, 40), (32, 46)],
            [(32, 22), (40, 28), (40, 40), (32, 46)],
            [(32, 46), (32, 50), (36, 50)],
        ],
    },
    {
        'name': 'RE', 'script': 'ETHIOPIC', 'concept': 'RE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (32, 44)],
            [(24, 26), (32, 22), (40, 26)],
            [(32, 44), (26, 48)],
            [(32, 44), (38, 48)],
        ],
    },
    {
        'name': 'RU', 'script': 'ETHIOPIC', 'concept': 'RU',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (32, 44)],
            [(24, 26), (32, 22), (40, 26)],
            [(32, 44), (32, 50)],
        ],
    },
    {
        'name': 'RI', 'script': 'ETHIOPIC', 'concept': 'RI',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (32, 44)],
            [(24, 26), (32, 22), (40, 26)],
            [(26, 36), (38, 36)],
        ],
    },
    {
        'name': 'RA', 'script': 'ETHIOPIC', 'concept': 'RA',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],
            [(24, 26), (32, 22), (40, 26)],
        ],
    },
    {
        'name': 'REE', 'script': 'ETHIOPIC', 'concept': 'REE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (32, 44)],
            [(24, 26), (32, 22), (40, 26)],
            [(38, 44), (44, 44)],
        ],
    },
    {
        'name': 'RO', 'script': 'ETHIOPIC', 'concept': 'RO',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(32, 22), (32, 44)],
            [(24, 26), (32, 22), (40, 26)],
            [(32, 44), (36, 50)],
        ],
    },
    {
        'name': 'SHE', 'script': 'ETHIOPIC', 'concept': 'SHE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],
            [(26, 22), (22, 34), (26, 44)],
            [(38, 22), (42, 34), (38, 44)],
            [(26, 44), (38, 44)],
        ],
    },
    {
        'name': 'SHU', 'script': 'ETHIOPIC', 'concept': 'SHU',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],
            [(26, 22), (22, 34), (26, 44)],
            [(38, 22), (42, 34), (38, 44)],
            [(32, 44), (32, 50)],
        ],
    },
    {
        'name': 'SHI', 'script': 'ETHIOPIC', 'concept': 'SHI',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],
            [(26, 22), (22, 34), (26, 44)],
            [(38, 22), (42, 34), (38, 44)],
            [(26, 34), (38, 34)],
        ],
    },
    {
        'name': 'SHA', 'script': 'ETHIOPIC', 'concept': 'SHA',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],
            [(26, 22), (22, 34), (26, 48)],
            [(38, 22), (42, 34), (38, 48)],
        ],
    },
    {
        'name': 'SHEE', 'script': 'ETHIOPIC', 'concept': 'SHEE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],
            [(26, 22), (22, 34), (26, 44)],
            [(38, 22), (42, 34), (38, 44)],
            [(38, 44), (44, 44)],
        ],
    },
    {
        'name': 'SHO', 'script': 'ETHIOPIC', 'concept': 'SHO',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(26, 22), (38, 22)],
            [(26, 22), (22, 34), (26, 44)],
            [(38, 22), (42, 34), (38, 44)],
            [(32, 44), (36, 50)],
        ],
    },
    {
        'name': 'QE', 'script': 'ETHIOPIC', 'concept': 'QE',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (36, 22)],
            [(28, 22), (28, 44)],
            [(36, 22), (36, 44)],
            [(28, 44), (24, 48)],
            [(36, 44), (40, 48)],
            [(28, 34), (36, 34)],
        ],
    },
    {
        'name': 'QU', 'script': 'ETHIOPIC', 'concept': 'QU',
        'origin': "GE'EZ ~500 BC",
        'ink': _ETHIOPIC_INK, 'paper': _ETHIOPIC_PAPER,
        'strokes': [
            [(28, 22), (36, 22)],
            [(28, 22), (28, 44)],
            [(36, 22), (36, 44)],
            [(28, 44), (36, 44)],
            [(32, 44), (32, 50)],
        ],
    },
    # ── MONGOLIAN ────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'MONGOLIAN', 'concept': 'A (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 22), (38, 26), (38, 32), (32, 36)],   # right curve (tooth)
            [(32, 22), (26, 20)],                        # top serif left
        ],
    },
    # ── N'KO ────────────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'NKO', 'concept': 'A',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 22), (38, 20)],                        # top tick right
        ],
    },
    {
        'name': 'EE', 'script': 'NKO', 'concept': 'EE',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 26), (38, 22), (42, 26)],              # top hook right
        ],
    },
    {
        'name': 'I', 'script': 'NKO', 'concept': 'I',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(30, 20), (34, 20)],                        # top dot/dash
        ],
    },
    {
        'name': 'E', 'script': 'NKO', 'concept': 'E',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 22), (26, 20)],                        # top tick left
            [(32, 22), (38, 20)],                        # top tick right
        ],
    },
    {
        'name': 'U', 'script': 'NKO', 'concept': 'U',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 48), (38, 50)],                        # bottom tick right
        ],
    },
    {
        'name': 'OO', 'script': 'NKO', 'concept': 'OO',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 48), (26, 50)],                        # bottom tick left
            [(32, 48), (38, 50)],                        # bottom tick right
        ],
    },
    {
        'name': 'O', 'script': 'NKO', 'concept': 'O',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 48), (26, 50)],                        # bottom tick left
        ],
    },
    {
        'name': 'DAGBASINNA', 'script': 'NKO', 'concept': 'NASALIZED',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(28, 34), (36, 34)],                        # cross mark
            [(30, 20), (34, 20)],                        # top dot
        ],
    },
    {
        'name': 'BA', 'script': 'NKO', 'concept': 'BA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 30), (24, 34), (24, 42), (32, 46)],   # left bowl curve
        ],
    },
    {
        'name': 'PA', 'script': 'NKO', 'concept': 'PA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 30), (24, 34), (24, 42), (32, 46)],   # left bowl curve
            [(28, 50), (28, 52)],                        # dot below
        ],
    },
    {
        'name': 'TA', 'script': 'NKO', 'concept': 'TA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 28), (40, 32), (40, 40), (32, 44)],   # right bowl curve
        ],
    },
    {
        'name': 'JA', 'script': 'NKO', 'concept': 'JA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 32), (24, 28)],                        # left upper tick
            [(32, 40), (24, 36)],                        # left lower tick
        ],
    },
    {
        'name': 'CHA', 'script': 'NKO', 'concept': 'CHA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 32), (24, 28)],                        # left upper tick
            [(32, 40), (24, 36)],                        # left lower tick
            [(28, 50), (28, 52)],                        # dot below
        ],
    },
    {
        'name': 'DA', 'script': 'NKO', 'concept': 'DA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 30), (26, 26), (22, 30)],              # left hook top
        ],
    },
    {
        'name': 'RA', 'script': 'NKO', 'concept': 'RA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 34), (38, 30), (42, 34)],              # right curve
        ],
    },
    {
        'name': 'RRA', 'script': 'NKO', 'concept': 'RRA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 34), (38, 30), (42, 34)],              # right curve
            [(37, 50), (37, 52)],                        # dot below
        ],
    },
    {
        'name': 'SA', 'script': 'NKO', 'concept': 'SA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 28), (24, 32), (32, 36)],              # left notch
        ],
    },
    {
        'name': 'GBA', 'script': 'NKO', 'concept': 'GBA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 26), (24, 30), (24, 40), (32, 44)],   # left deep curve
            [(32, 35), (40, 35)],                        # right cross tick
        ],
    },
    {
        'name': 'FA', 'script': 'NKO', 'concept': 'FA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 28), (40, 24), (44, 28)],              # right hook top
        ],
    },
    {
        'name': 'KA', 'script': 'NKO', 'concept': 'KA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 30), (40, 34), (40, 42), (32, 46)],   # right bowl
        ],
    },
    {
        'name': 'LA', 'script': 'NKO', 'concept': 'LA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 32), (40, 28)],                        # right upper tick
            [(32, 40), (40, 36)],                        # right lower tick
        ],
    },
    {
        'name': 'NA WOLOSO', 'script': 'NKO', 'concept': 'NA (SMALL)',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 26), (32, 48)],                        # main vertical (shorter)
            [(32, 34), (26, 38)],                        # left tick
        ],
    },
    {
        'name': 'NA', 'script': 'NKO', 'concept': 'NA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 34), (26, 38)],                        # left tick
            [(32, 22), (38, 20)],                        # top tick right
        ],
    },
    {
        'name': 'MA', 'script': 'NKO', 'concept': 'MA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 28), (24, 32), (24, 42), (32, 46)],   # left curve
            [(32, 28), (40, 32), (40, 42), (32, 46)],   # right curve
        ],
    },
    {
        'name': 'NYA', 'script': 'NKO', 'concept': 'NYA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 30), (22, 34), (32, 38)],              # left diamond notch
            [(30, 20), (34, 20)],                        # top dot
        ],
    },
    {
        'name': 'NYAN', 'script': 'NKO', 'concept': 'NYAN',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 30), (22, 34), (32, 38)],              # left diamond notch
            [(28, 50), (28, 52)],                        # dot below
        ],
    },
    {
        'name': 'WA', 'script': 'NKO', 'concept': 'WA',
        'origin': 'SOLOMANA KANTE 1949 AD',
        'ink': _NKO_INK, 'paper': _NKO_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                        # main vertical
            [(32, 30), (26, 26), (22, 30), (26, 34), (32, 30)],  # left loop
        ],
    },
    # ── MONGOLIAN (additional letters) ──────────────────────────────
    {
        'name': 'E', 'script': 'MONGOLIAN', 'concept': 'E (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 24), (26, 28), (26, 34), (32, 38)],   # left curve (tooth)
            [(32, 18), (38, 20)],                        # top serif right
        ],
    },
    {
        'name': 'I', 'script': 'MONGOLIAN', 'concept': 'I (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 26), (38, 30)],                        # right tick (tooth)
            [(32, 18), (26, 20)],                        # top serif left
        ],
    },
    {
        'name': 'O', 'script': 'MONGOLIAN', 'concept': 'O (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 24), (40, 28), (40, 36), (32, 40)],   # right belly
            [(32, 18), (26, 20)],                        # top serif left
        ],
    },
    {
        'name': 'U', 'script': 'MONGOLIAN', 'concept': 'U (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 34), (40, 38), (40, 44), (32, 48)],   # right low belly
            [(32, 18), (26, 20)],                        # top serif left
        ],
    },
    {
        'name': 'NA', 'script': 'MONGOLIAN', 'concept': 'NA (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 28), (26, 24)],                        # left upper tick
            [(32, 40), (26, 36)],                        # left lower tick
        ],
    },
    {
        'name': 'BA', 'script': 'MONGOLIAN', 'concept': 'BA (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 26), (24, 30), (24, 38), (32, 42)],   # left bowl
            [(32, 18), (38, 20)],                        # top serif right
        ],
    },
    {
        'name': 'QA', 'script': 'MONGOLIAN', 'concept': 'QA (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 22), (40, 26), (40, 32), (32, 36)],   # right upper tooth
            [(32, 38), (40, 42), (40, 48), (32, 50)],   # right lower tooth
        ],
    },
    {
        'name': 'GA', 'script': 'MONGOLIAN', 'concept': 'GA (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 24), (24, 28), (24, 34), (32, 38)],   # left tooth
            [(32, 18), (38, 20)],                        # top serif right
        ],
    },
    {
        'name': 'DA', 'script': 'MONGOLIAN', 'concept': 'DA (MONGOL)',
        'origin': 'MONGOLIA ~1204 AD',
        'ink': _MONGOLIAN_INK, 'paper': _MONGOLIAN_PAPER,
        'strokes': [
            [(32, 18), (32, 50)],                        # vertical spine
            [(32, 28), (38, 24)],                        # right upper tick
            [(32, 28), (26, 24)],                        # left upper tick
        ],
    },
    # ── INUKTITUT (additional syllabics) ────────────────────────────
    {
        'name': 'TI', 'script': 'INUKTITUT', 'concept': 'TI',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(24, 44), (32, 24), (40, 44), (24, 44)],   # triangle pointing up
        ],
    },
    {
        'name': 'TO', 'script': 'INUKTITUT', 'concept': 'TO',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(22, 26), (42, 34), (22, 42), (22, 26)],   # triangle pointing right
        ],
    },
    {
        'name': 'TA', 'script': 'INUKTITUT', 'concept': 'TA',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(24, 24), (32, 44), (40, 24), (24, 24)],   # triangle pointing down
        ],
    },
    {
        'name': 'TE', 'script': 'INUKTITUT', 'concept': 'TE',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(42, 26), (22, 34), (42, 42), (42, 26)],   # triangle pointing left
        ],
    },
    {
        'name': 'NI', 'script': 'INUKTITUT', 'concept': 'NI',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(28, 44), (28, 24)],                        # vertical up
            [(28, 24), (42, 24)],                        # horizontal right (L up)
        ],
    },
    {
        'name': 'NO', 'script': 'INUKTITUT', 'concept': 'NO',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(22, 30), (42, 30)],                        # horizontal right
            [(42, 30), (42, 44)],                        # vertical down (L right)
        ],
    },
    {
        'name': 'NA', 'script': 'INUKTITUT', 'concept': 'NA',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(36, 24), (36, 44)],                        # vertical down
            [(36, 44), (22, 44)],                        # horizontal left (L down)
        ],
    },
    {
        'name': 'NE', 'script': 'INUKTITUT', 'concept': 'NE',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(42, 38), (22, 38)],                        # horizontal left
            [(22, 38), (22, 24)],                        # vertical up (L left)
        ],
    },
    {
        'name': 'MI', 'script': 'INUKTITUT', 'concept': 'MI',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(24, 44), (32, 24)],                        # left diagonal up
            [(32, 24), (40, 44)],                        # right diagonal down
        ],
    },
    {
        'name': 'MO', 'script': 'INUKTITUT', 'concept': 'MO',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(22, 26), (42, 34)],                        # diagonal right-down
            [(42, 34), (22, 42)],                        # diagonal left-down
        ],
    },
    {
        'name': 'MA', 'script': 'INUKTITUT', 'concept': 'MA',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(24, 24), (32, 44)],                        # left diagonal down
            [(32, 44), (40, 24)],                        # right diagonal up
        ],
    },
    {
        'name': 'SI', 'script': 'INUKTITUT', 'concept': 'SI',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(26, 44), (26, 24)],                        # left vertical
            [(26, 24), (38, 24)],                        # top horizontal
            [(38, 24), (38, 44)],                        # right vertical
        ],
    },
    {
        'name': 'SA', 'script': 'INUKTITUT', 'concept': 'SA',
        'origin': 'JAMES EVANS 1840 AD',
        'ink': (30, 30, 80), 'paper': (220, 225, 230),
        'strokes': [
            [(26, 24), (26, 44)],                        # left vertical
            [(26, 44), (38, 44)],                        # bottom horizontal
            [(38, 44), (38, 24)],                        # right vertical
        ],
    },
    # ── HIEROGLYPH (additional signs) ───────────────────────────────
    {
        'name': 'BIRD', 'script': 'HIEROGLYPH', 'concept': 'VULTURE (A)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(22, 30), (28, 24), (36, 24), (42, 28)],   # head and back
            [(42, 28), (44, 36), (40, 44)],              # body curve
            [(40, 44), (30, 48), (20, 46)],              # tail
            [(28, 24), (26, 20)],                        # beak
            [(36, 36), (42, 44)],                        # wing line
        ],
    },
    {
        'name': 'WATER RIPPLE', 'script': 'HIEROGLYPH', 'concept': 'N (WATER)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(20, 28), (26, 24), (32, 28), (38, 24), (44, 28)],  # wave 1
            [(20, 36), (26, 32), (32, 36), (38, 32), (44, 36)],  # wave 2
            [(20, 44), (26, 40), (32, 44), (38, 40), (44, 44)],  # wave 3
        ],
    },
    {
        'name': 'FEATHER', 'script': 'HIEROGLYPH', 'concept': 'MAAT (TRUTH)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 50)],                        # central shaft
            [(32, 24), (24, 28)],                        # left barb 1
            [(32, 30), (24, 34)],                        # left barb 2
            [(32, 36), (24, 40)],                        # left barb 3
            [(32, 24), (40, 28)],                        # right barb 1
            [(32, 30), (40, 34)],                        # right barb 2
            [(32, 36), (40, 40)],                        # right barb 3
        ],
    },
    {
        'name': 'SERPENT', 'script': 'HIEROGLYPH', 'concept': 'COBRA (DJ)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (28, 20), (32, 22)],              # hood top
            [(24, 22), (22, 28)],                        # hood left
            [(32, 22), (34, 28)],                        # hood right
            [(28, 28), (30, 36), (26, 42), (30, 48), (36, 46)],  # S-body
        ],
    },
    {
        'name': 'HAND', 'script': 'HIEROGLYPH', 'concept': 'D (HAND)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(20, 36), (30, 36), (36, 30), (40, 24)],   # arm and wrist
            [(40, 24), (44, 22), (44, 28)],              # thumb
            [(40, 24), (42, 20)],                        # index finger
            [(38, 26), (40, 20)],                        # middle finger
            [(36, 28), (36, 22)],                        # ring finger
        ],
    },
    {
        'name': 'FOOT', 'script': 'HIEROGLYPH', 'concept': 'B (FOOT)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(28, 20), (28, 42)],                        # leg vertical
            [(28, 42), (22, 48), (38, 48)],              # foot sole
            [(38, 48), (42, 44)],                        # toes up
        ],
    },
    {
        'name': 'MOUTH', 'script': 'HIEROGLYPH', 'concept': 'R (MOUTH)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(20, 32), (26, 28), (38, 28), (44, 32),
             (38, 36), (26, 36), (20, 32)],              # lip oval
        ],
    },
    {
        'name': 'HOUSE', 'script': 'HIEROGLYPH', 'concept': 'PR (HOUSE)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22), (44, 48), (20, 48), (20, 22)],  # walls
            [(20, 42), (28, 42), (28, 48)],              # doorway
        ],
    },
    {
        'name': 'BASKET', 'script': 'HIEROGLYPH', 'concept': 'K (BASKET)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(20, 30), (44, 30)],                        # rim
            [(20, 30), (24, 44), (32, 48), (40, 44), (44, 30)],  # bowl
        ],
    },
    {
        'name': 'SUN DISK', 'script': 'HIEROGLYPH', 'concept': 'RA (SUN)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(22, 30), (26, 22), (38, 22), (42, 30),
             (42, 38), (38, 46), (26, 46), (22, 38),
             (22, 30)],                                  # outer circle
            [(31, 33), (33, 33), (33, 35), (31, 35), (31, 33)],  # center dot
        ],
    },
    {
        'name': 'LOTUS', 'script': 'HIEROGLYPH', 'concept': 'LOTUS (REBIRTH)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(32, 50), (32, 30)],                        # stem
            [(32, 30), (26, 22), (22, 24)],              # left petal
            [(32, 30), (38, 22), (42, 24)],              # right petal
            [(32, 30), (32, 20)],                        # center petal
        ],
    },
    {
        'name': 'LION', 'script': 'HIEROGLYPH', 'concept': 'LION (POWER)',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(20, 32), (24, 26), (30, 24)],              # head top
            [(30, 24), (30, 30)],                        # face front
            [(30, 30), (44, 30)],                        # back line
            [(44, 30), (46, 36), (44, 42)],              # haunches
            [(30, 30), (22, 32), (20, 40), (22, 44)],   # chest and front leg
            [(44, 42), (40, 44)],                        # rear leg
            [(44, 36), (48, 28)],                        # tail up
        ],
    },
    {
        'name': 'DJED PILLAR', 'script': 'HIEROGLYPH', 'concept': 'STABILITY',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 50)],                        # central column
            [(24, 50), (40, 50)],                        # base
            [(24, 26), (40, 26)],                        # top cross bar
            [(24, 32), (40, 32)],                        # second cross bar
            [(24, 38), (40, 38)],                        # third cross bar
            [(26, 44), (38, 44)],                        # fourth cross bar
        ],
    },
    {
        'name': 'WAS SCEPTER', 'script': 'HIEROGLYPH', 'concept': 'POWER',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(32, 28), (32, 48)],                        # shaft
            [(28, 48), (36, 48)],                        # base fork
            [(32, 28), (26, 24), (24, 20)],              # animal head left
            [(32, 28), (38, 24), (40, 20)],              # animal ear right
            [(26, 24), (22, 26)],                        # snout
        ],
    },
    {
        'name': 'CARTOUCHE', 'script': 'HIEROGLYPH', 'concept': 'ROYAL NAME',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(22, 24), (42, 24), (46, 28), (46, 40),
             (42, 44), (22, 44), (18, 40), (18, 28),
             (22, 24)],                                  # oval ring
            [(18, 48), (46, 48)],                        # bottom bar
        ],
    },
    {
        'name': 'SEATED MAN', 'script': 'HIEROGLYPH', 'concept': 'MAN / PERSON',
        'origin': 'EGYPT ~3000 BC',
        'ink': _HIERO_INK, 'paper': _HIERO_PAPER, 'thick': True,
        'strokes': [
            [(30, 22), (34, 22), (34, 26), (30, 26), (30, 22)],  # head
            [(32, 26), (32, 36)],                        # torso
            [(32, 32), (38, 28)],                        # arm forward
            [(32, 36), (26, 42), (22, 42)],              # lap (seated)
            [(32, 36), (38, 42), (38, 48)],              # leg down
        ],
    },
    # ── CUNEIFORM (additional signs) ────────────────────────────────
    {
        'name': 'E', 'script': 'CUNEIFORM', 'concept': 'HOUSE / TEMPLE',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(22, 24), (30, 24), (22, 30)],              # top-left wedge
            [(22, 32), (30, 32), (22, 38)],              # mid-left wedge
            [(34, 22), (34, 48)],                        # right vertical
            [(22, 42), (30, 42), (22, 48)],              # bottom-left wedge
        ],
    },
    {
        'name': 'UD', 'script': 'CUNEIFORM', 'concept': 'SUN / DAY',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(32, 26), (24, 34), (32, 34)],              # center wedge down
            [(32, 26), (40, 34), (32, 34)],              # center wedge right-mirror
            [(20, 30), (28, 30), (20, 36)],              # left wedge
            [(44, 30), (36, 30), (44, 36)],              # right wedge
        ],
    },
    {
        'name': 'GU', 'script': 'CUNEIFORM', 'concept': 'BULL',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (32, 22), (24, 28)],              # top wedge
            [(24, 30), (32, 30), (24, 36)],              # middle wedge
            [(36, 24), (44, 24)],                        # right horizontal mark
            [(36, 34), (44, 34)],                        # right horizontal mark 2
            [(28, 40), (28, 50)],                        # left tail vertical
        ],
    },
    {
        'name': 'SAG', 'script': 'CUNEIFORM', 'concept': 'HEAD',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(26, 20), (34, 20), (26, 26)],              # top wedge
            [(26, 28), (34, 28), (26, 34)],              # second wedge
            [(38, 24), (46, 24)],                        # right mark
            [(20, 38), (44, 38)],                        # horizontal bar
            [(32, 38), (32, 50)],                        # vertical below
        ],
    },
    {
        'name': 'A', 'script': 'CUNEIFORM', 'concept': 'WATER',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(22, 24), (30, 24), (22, 30)],              # top wedge
            [(22, 32), (30, 32), (22, 38)],              # middle wedge
            [(22, 40), (30, 40), (22, 46)],              # bottom wedge
        ],
    },
    {
        'name': 'NINDA', 'script': 'CUNEIFORM', 'concept': 'FOOD / BREAD',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(24, 24), (32, 24), (24, 30)],              # top wedge
            [(36, 24), (44, 24)],                        # top right mark
            [(24, 34), (44, 34)],                        # horizontal bar
            [(24, 38), (32, 38), (24, 44)],              # bottom wedge
        ],
    },
    {
        'name': 'DUG', 'script': 'CUNEIFORM', 'concept': 'POT / VESSEL',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (24, 28), (32, 28)],              # top wedge down
            [(32, 28), (32, 48)],                        # vertical shaft
            [(24, 40), (32, 40), (24, 46)],              # bottom wedge
            [(36, 34), (44, 34)],                        # right mark
        ],
    },
    {
        'name': 'LUGAL', 'script': 'CUNEIFORM', 'concept': 'KING',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(26, 20), (34, 20), (26, 26)],              # top wedge (SAG)
            [(26, 28), (34, 28), (26, 34)],              # second wedge
            [(38, 24), (46, 24)],                        # right mark
            [(20, 38), (44, 38)],                        # horizontal bar
            [(26, 40), (34, 40), (26, 46)],              # bottom wedge (GAL)
            [(36, 44), (44, 44)],                        # bottom right mark
        ],
    },
    {
        'name': 'EN', 'script': 'CUNEIFORM', 'concept': 'LORD',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(20, 34), (44, 34)],                        # horizontal
            [(32, 20), (24, 28), (32, 28)],              # top wedge
            [(32, 40), (24, 48), (32, 48)],              # bottom wedge
            [(36, 24), (44, 28)],                        # right diagonal mark
        ],
    },
    {
        'name': 'NAM', 'script': 'CUNEIFORM', 'concept': 'FATE / DESTINY',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(22, 22), (30, 22), (22, 28)],              # top-left wedge
            [(22, 30), (30, 30), (22, 36)],              # mid-left wedge
            [(34, 20), (34, 48)],                        # vertical line
            [(38, 26), (46, 26)],                        # right mark top
            [(38, 36), (46, 36)],                        # right mark bottom
        ],
    },
    {
        'name': 'MU', 'script': 'CUNEIFORM', 'concept': 'NAME / YEAR',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 50)],                        # vertical shaft
            [(32, 24), (24, 30), (32, 30)],              # left wedge top
            [(32, 36), (24, 42), (32, 42)],              # left wedge bottom
        ],
    },
    {
        'name': 'BAR', 'script': 'CUNEIFORM', 'concept': 'OUTSIDE',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(20, 32), (28, 32), (20, 38)],              # left wedge
            [(36, 32), (44, 32), (36, 38)],              # right wedge
        ],
    },
    {
        'name': 'GAL', 'script': 'CUNEIFORM', 'concept': 'GREAT / BIG',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(24, 26), (38, 26), (24, 38)],              # large wedge
            [(40, 30), (46, 30)],                        # right mark
        ],
    },
    {
        'name': 'TUR', 'script': 'CUNEIFORM', 'concept': 'SMALL / CHILD',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(28, 30), (36, 30), (28, 36)],              # small wedge
            [(38, 32), (42, 32)],                        # tiny right mark
        ],
    },
    {
        'name': 'GI', 'script': 'CUNEIFORM', 'concept': 'REED',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (32, 50)],                        # vertical shaft
            [(32, 26), (24, 30), (32, 30)],              # left wedge
            [(36, 26), (44, 26)],                        # right mark
        ],
    },
    {
        'name': 'DUB', 'script': 'CUNEIFORM', 'concept': 'TABLET',
        'origin': 'SUMER ~3100 BC',
        'ink': _CUNEI_INK, 'paper': _CUNEI_PAPER, 'thick': True,
        'strokes': [
            [(22, 22), (30, 22), (22, 28)],              # top-left wedge
            [(34, 22), (42, 22), (34, 28)],              # top-right wedge
            [(20, 34), (44, 34)],                        # horizontal bar
            [(22, 38), (30, 38), (22, 44)],              # bottom-left wedge
            [(34, 38), (42, 38), (34, 44)],              # bottom-right wedge
        ],
    },
    # ── MAYAN (additional day signs) ────────────────────────────────
    {
        'name': 'IMIX', 'script': 'MAYAN', 'concept': 'WATER LILY',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(26, 28), (38, 28), (38, 40), (26, 40), (26, 28)],  # inner circle/face
            [(28, 32), (30, 32)],                        # left eye dot
            [(34, 32), (36, 32)],                        # right eye dot
            [(30, 36), (34, 38)],                        # mouth curve
        ],
    },
    {
        'name': 'IK', 'script': 'MAYAN', 'concept': 'WIND',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(26, 28), (38, 28)],                        # T-top horizontal
            [(32, 28), (32, 42)],                        # T-vertical
            [(26, 42), (38, 42)],                        # T-base bar
        ],
    },
    {
        'name': 'AKBAL', 'script': 'MAYAN', 'concept': 'NIGHT',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(26, 30), (30, 26), (36, 26), (40, 30),
             (40, 38), (36, 42), (30, 42), (26, 38),
             (26, 30)],                                  # dark circle
            [(30, 32), (36, 32)],                        # cross line
        ],
    },
    {
        'name': 'KAN', 'script': 'MAYAN', 'concept': 'CORN / SEED',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(28, 26), (36, 26), (38, 34), (32, 42),
             (26, 34), (28, 26)],                        # kernel/seed shape
            [(30, 32), (34, 32)],                        # inner line
        ],
    },
    {
        'name': 'CHICCHAN', 'script': 'MAYAN', 'concept': 'SNAKE',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(26, 28), (34, 26), (38, 32), (32, 36),
             (26, 34), (28, 40), (36, 42)],              # coiled snake
            [(34, 26), (38, 24)],                        # tongue
        ],
    },
    {
        'name': 'KIMI', 'script': 'MAYAN', 'concept': 'DEATH',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(26, 28), (28, 30), (26, 32)],              # left eye (%)
            [(38, 28), (36, 30), (38, 32)],              # right eye (%)
            [(30, 30), (34, 30)],                        # nose bridge
            [(28, 38), (36, 38)],                        # mouth line
            [(28, 40), (30, 42)],                        # left jaw
            [(36, 40), (34, 42)],                        # right jaw
        ],
    },
    {
        'name': 'MANIK', 'script': 'MAYAN', 'concept': 'DEER',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(28, 42), (28, 28), (32, 26), (36, 28)],   # hand/hoof palm
            [(32, 26), (30, 24)],                        # finger 1
            [(32, 26), (34, 24)],                        # finger 2
            [(36, 28), (38, 26)],                        # finger 3
        ],
    },
    {
        'name': 'LAMAT', 'script': 'MAYAN', 'concept': 'VENUS (STAR)',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(32, 26), (32, 42)],                        # vertical cross
            [(24, 34), (40, 34)],                        # horizontal cross
            [(26, 28), (38, 40)],                        # diagonal 1
            [(38, 28), (26, 40)],                        # diagonal 2
        ],
    },
    {
        'name': 'MULUK', 'script': 'MAYAN', 'concept': 'WATER',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(26, 30), (32, 26), (38, 30)],              # upper wave
            [(26, 36), (32, 32), (38, 36)],              # middle wave
            [(26, 42), (32, 38), (38, 42)],              # lower wave
        ],
    },
    {
        'name': 'OK', 'script': 'MAYAN', 'concept': 'DOG',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(26, 26), (30, 24), (34, 26), (34, 32),
             (30, 34), (26, 32), (26, 26)],              # ear/head shape
            [(36, 28), (40, 26), (40, 32), (36, 32)],   # second ear
            [(30, 38), (34, 38)],                        # snout
        ],
    },
    {
        'name': 'CHUEN', 'script': 'MAYAN', 'concept': 'MONKEY',
        'origin': 'MAYA ~250 AD',
        'ink': (80, 40, 30), 'paper': (200, 185, 155), 'thick': True,
        'strokes': [
            [(20, 20), (44, 20), (44, 48), (20, 48), (20, 20)],  # outer frame
            [(36, 28), (30, 28), (28, 32), (30, 36),
             (34, 36), (36, 32), (36, 28)],              # spiral/curl body
            [(28, 38), (36, 42)],                        # tail curve
            [(30, 28), (28, 26)],                        # ear
        ],
    },
    # ── PHOENICIAN ──────────────────────────────────────────────
    {
        'name': 'ALEPH', 'script': 'PHOENICIAN', 'concept': 'OX',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (32, 40), (40, 22)],              # V-shaped ox head
            [(24, 22), (28, 20)],                         # left horn
            [(40, 22), (36, 20)],                         # right horn
            [(32, 40), (32, 48)],                         # chin/snout down
        ],
    },
    {
        'name': 'BET', 'script': 'PHOENICIAN', 'concept': 'HOUSE',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (40, 22), (40, 36), (24, 36), (24, 22)],  # upper room
            [(24, 36), (40, 36), (40, 48), (24, 48)],    # lower room open left
        ],
    },
    {
        'name': 'GIMEL', 'script': 'PHOENICIAN', 'concept': 'CAMEL',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(26, 22), (38, 22)],                         # top bar
            [(38, 22), (38, 34)],                         # right vertical
            [(38, 34), (26, 48)],                         # diagonal leg
        ],
    },
    {
        'name': 'DALET', 'script': 'PHOENICIAN', 'concept': 'DOOR',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (40, 22)],                         # top lintel
            [(40, 22), (40, 48)],                         # right doorpost
            [(24, 22), (24, 34)],                         # left partial post
        ],
    },
    {
        'name': 'HE', 'script': 'PHOENICIAN', 'concept': 'WINDOW',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (24, 48)],                         # left vertical
            [(24, 22), (40, 22)],                         # top bar
            [(24, 35), (40, 35)],                         # middle bar
            [(24, 48), (40, 48)],                         # bottom bar
        ],
    },
    {
        'name': 'WAW', 'script': 'PHOENICIAN', 'concept': 'HOOK',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (26, 24), (32, 28), (38, 24), (32, 20)],  # top hook circle
            [(32, 28), (32, 48)],                         # vertical stem
        ],
    },
    {
        'name': 'ZAYIN', 'script': 'PHOENICIAN', 'concept': 'WEAPON',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (40, 22)],                         # crossguard
            [(32, 22), (32, 48)],                         # blade
        ],
    },
    {
        'name': 'HET', 'script': 'PHOENICIAN', 'concept': 'FENCE',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (24, 48)],                         # left post
            [(40, 22), (40, 48)],                         # right post
            [(24, 28), (40, 28)],                         # upper rail
            [(24, 40), (40, 40)],                         # lower rail
        ],
    },
    {
        'name': 'TET', 'script': 'PHOENICIAN', 'concept': 'WHEEL',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 28), (32, 22), (40, 28), (40, 42),
             (32, 48), (24, 42), (24, 28)],               # circle body
            [(24, 35), (40, 35)],                         # cross horizontal
            [(32, 22), (32, 48)],                         # cross vertical
        ],
    },
    {
        'name': 'YOD', 'script': 'PHOENICIAN', 'concept': 'HAND',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(32, 22), (26, 30)],                         # arm angled down-left
            [(26, 30), (20, 26)],                         # finger up
            [(26, 30), (20, 34)],                         # finger down
            [(26, 30), (22, 30)],                         # finger left
        ],
    },
    {
        'name': 'KAP', 'script': 'PHOENICIAN', 'concept': 'PALM',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(32, 22), (32, 48)],                         # vertical
            [(32, 22), (22, 30)],                         # upper-left branch
            [(32, 34), (22, 42)],                         # lower-left branch
            [(32, 28), (42, 28)],                         # right mark
        ],
    },
    {
        'name': 'LAMED', 'script': 'PHOENICIAN', 'concept': 'GOAD',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(28, 20), (40, 34)],                         # diagonal shaft
            [(40, 34), (28, 48)],                         # diagonal return
        ],
    },
    {
        'name': 'MEM', 'script': 'PHOENICIAN', 'concept': 'WATER',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(20, 22), (26, 34), (32, 22), (38, 34), (44, 22)],  # zigzag waves
            [(20, 22), (20, 48)],                         # left stem down
        ],
    },
    {
        'name': 'NUN', 'script': 'PHOENICIAN', 'concept': 'SNAKE',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(32, 20), (28, 28), (36, 36), (32, 48)],    # sinuous S-curve
        ],
    },
    {
        'name': 'SAMEKH', 'script': 'PHOENICIAN', 'concept': 'SUPPORT',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (40, 22), (40, 48), (24, 48), (24, 22)],  # outer frame
            [(24, 35), (40, 35)],                         # middle support bar
        ],
    },
    {
        'name': 'AYIN', 'script': 'PHOENICIAN', 'concept': 'EYE',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 30), (32, 24), (40, 30), (40, 40),
             (32, 46), (24, 40), (24, 30)],               # eye outline
            [(30, 34), (34, 34), (34, 38), (30, 38), (30, 34)],  # pupil
        ],
    },
    {
        'name': 'PE', 'script': 'PHOENICIAN', 'concept': 'MOUTH',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 22), (24, 40)],                         # left vertical
            [(24, 22), (40, 22)],                         # top bar
            [(40, 22), (40, 40)],                         # right vertical
            [(24, 40), (32, 48), (40, 40)],               # curved jaw
        ],
    },
    {
        'name': 'TSADE', 'script': 'PHOENICIAN', 'concept': 'PLANT',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(32, 48), (32, 30)],                         # stem
            [(32, 30), (22, 22)],                         # left branch
            [(32, 30), (42, 22)],                         # right branch
            [(32, 38), (24, 34)],                         # left leaf
            [(32, 38), (40, 34)],                         # right leaf
        ],
    },
    {
        'name': 'QOPH', 'script': 'PHOENICIAN', 'concept': 'MONKEY',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(26, 26), (32, 22), (38, 26), (38, 34),
             (32, 38), (26, 34), (26, 26)],               # head circle
            [(32, 38), (32, 50)],                         # tail descender
        ],
    },
    {
        'name': 'RESH', 'script': 'PHOENICIAN', 'concept': 'HEAD',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(26, 26), (32, 22), (38, 26), (38, 34),
             (32, 38), (26, 34), (26, 26)],               # head shape
            [(32, 38), (40, 48)],                         # neck descending
        ],
    },
    {
        'name': 'SHIN', 'script': 'PHOENICIAN', 'concept': 'TOOTH',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(24, 48), (24, 24)],                         # left prong
            [(32, 48), (32, 20)],                         # center prong
            [(40, 48), (40, 24)],                         # right prong
            [(24, 48), (40, 48)],                         # base gumline
        ],
    },
    {
        'name': 'TAW', 'script': 'PHOENICIAN', 'concept': 'MARK',
        'origin': 'PHOENICIA ~1050 BC',
        'ink': _PHOEN_INK, 'paper': _PHOEN_PAPER, 'thick': True,
        'strokes': [
            [(22, 22), (42, 48)],                         # diagonal backslash
            [(42, 22), (22, 48)],                         # diagonal slash (X mark)
        ],
    },
    # ── OGHAM ───────────────────────────────────────────────────
    # Vertical stem (32,20)-(32,48). Notches are short lines along stem.
    # B-series: right horizontal notches
    {
        'name': 'BEITH', 'script': 'OGHAM', 'concept': 'BIRCH',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(32, 34), (40, 34)],                         # 1 right notch
        ],
    },
    {
        'name': 'LUIS', 'script': 'OGHAM', 'concept': 'ROWAN',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(32, 31), (40, 31)],                         # notch 1
            [(32, 37), (40, 37)],                         # notch 2
        ],
    },
    {
        'name': 'FEARN', 'script': 'OGHAM', 'concept': 'ALDER',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(32, 29), (40, 29)],                         # notch 1
            [(32, 34), (40, 34)],                         # notch 2
            [(32, 39), (40, 39)],                         # notch 3
        ],
    },
    {
        'name': 'SAIL', 'script': 'OGHAM', 'concept': 'WILLOW',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(32, 27), (40, 27)],                         # notch 1
            [(32, 32), (40, 32)],                         # notch 2
            [(32, 37), (40, 37)],                         # notch 3
            [(32, 42), (40, 42)],                         # notch 4
        ],
    },
    {
        'name': 'NION', 'script': 'OGHAM', 'concept': 'ASH',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(32, 26), (40, 26)],                         # notch 1
            [(32, 30), (40, 30)],                         # notch 2
            [(32, 34), (40, 34)],                         # notch 3
            [(32, 38), (40, 38)],                         # notch 4
            [(32, 42), (40, 42)],                         # notch 5
        ],
    },
    # H-series: left horizontal notches
    {
        'name': 'UATH', 'script': 'OGHAM', 'concept': 'HAWTHORN',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 34), (32, 34)],                         # 1 left notch
        ],
    },
    {
        'name': 'DAIR', 'script': 'OGHAM', 'concept': 'OAK',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 31), (32, 31)],                         # notch 1
            [(24, 37), (32, 37)],                         # notch 2
        ],
    },
    {
        'name': 'TINNE', 'script': 'OGHAM', 'concept': 'HOLLY',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 29), (32, 29)],                         # notch 1
            [(24, 34), (32, 34)],                         # notch 2
            [(24, 39), (32, 39)],                         # notch 3
        ],
    },
    {
        'name': 'COLL', 'script': 'OGHAM', 'concept': 'HAZEL',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 27), (32, 27)],                         # notch 1
            [(24, 32), (32, 32)],                         # notch 2
            [(24, 37), (32, 37)],                         # notch 3
            [(24, 42), (32, 42)],                         # notch 4
        ],
    },
    {
        'name': 'QUERT', 'script': 'OGHAM', 'concept': 'APPLE',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 26), (32, 26)],                         # notch 1
            [(24, 30), (32, 30)],                         # notch 2
            [(24, 34), (32, 34)],                         # notch 3
            [(24, 38), (32, 38)],                         # notch 4
            [(24, 42), (32, 42)],                         # notch 5
        ],
    },
    # M-series: diagonal lines crossing stem
    {
        'name': 'MUIN', 'script': 'OGHAM', 'concept': 'VINE',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(26, 30), (38, 38)],                         # 1 diagonal
        ],
    },
    {
        'name': 'GORT', 'script': 'OGHAM', 'concept': 'IVY',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(26, 28), (38, 34)],                         # diagonal 1
            [(26, 34), (38, 40)],                         # diagonal 2
        ],
    },
    {
        'name': 'NGETAL', 'script': 'OGHAM', 'concept': 'REED',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(26, 26), (38, 32)],                         # diagonal 1
            [(26, 32), (38, 38)],                         # diagonal 2
            [(26, 38), (38, 44)],                         # diagonal 3
        ],
    },
    {
        'name': 'STRAIF', 'script': 'OGHAM', 'concept': 'BLACKTHORN',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(26, 25), (38, 30)],                         # diagonal 1
            [(26, 30), (38, 35)],                         # diagonal 2
            [(26, 35), (38, 40)],                         # diagonal 3
            [(26, 40), (38, 45)],                         # diagonal 4
        ],
    },
    {
        'name': 'RUIS', 'script': 'OGHAM', 'concept': 'ELDER',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(26, 24), (38, 28)],                         # diagonal 1
            [(26, 28), (38, 32)],                         # diagonal 2
            [(26, 32), (38, 36)],                         # diagonal 3
            [(26, 36), (38, 40)],                         # diagonal 4
            [(26, 40), (38, 44)],                         # diagonal 5
        ],
    },
    # A-series: perpendicular lines crossing stem (both sides)
    {
        'name': 'AILM', 'script': 'OGHAM', 'concept': 'FIR',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 34), (40, 34)],                         # 1 crossing line
        ],
    },
    {
        'name': 'ONN', 'script': 'OGHAM', 'concept': 'GORSE',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 31), (40, 31)],                         # crossing 1
            [(24, 37), (40, 37)],                         # crossing 2
        ],
    },
    {
        'name': 'UR', 'script': 'OGHAM', 'concept': 'HEATHER',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 29), (40, 29)],                         # crossing 1
            [(24, 34), (40, 34)],                         # crossing 2
            [(24, 39), (40, 39)],                         # crossing 3
        ],
    },
    {
        'name': 'EADHADH', 'script': 'OGHAM', 'concept': 'ASPEN',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 27), (40, 27)],                         # crossing 1
            [(24, 32), (40, 32)],                         # crossing 2
            [(24, 37), (40, 37)],                         # crossing 3
            [(24, 42), (40, 42)],                         # crossing 4
        ],
    },
    {
        'name': 'IODHADH', 'script': 'OGHAM', 'concept': 'YEW',
        'origin': 'IRELAND ~400 AD',
        'ink': _OGHAM_INK, 'paper': _OGHAM_PAPER,
        'strokes': [
            [(32, 20), (32, 48)],                         # stem
            [(24, 26), (40, 26)],                         # crossing 1
            [(24, 30), (40, 30)],                         # crossing 2
            [(24, 34), (40, 34)],                         # crossing 3
            [(24, 38), (40, 38)],                         # crossing 4
            [(24, 42), (40, 42)],                         # crossing 5
        ],
    },
    # ── TIFINAGH ────────────────────────────────────────────────
    {
        'name': 'YA', 'script': 'TIFINAGH', 'concept': 'A',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(26, 28), (32, 22), (38, 28), (38, 40),
             (32, 46), (26, 40), (26, 28)],               # circle
        ],
    },
    {
        'name': 'YAB', 'script': 'TIFINAGH', 'concept': 'B',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(28, 22), (28, 48)],                         # left vertical
            [(36, 22), (36, 48)],                         # right vertical
        ],
    },
    {
        'name': 'YAG', 'script': 'TIFINAGH', 'concept': 'G',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(26, 28), (32, 22), (38, 28), (38, 40),
             (32, 46), (26, 40), (26, 28)],               # circle
            [(31, 33), (33, 33), (33, 35), (31, 35), (31, 33)],  # center dot
        ],
    },
    {
        'name': 'YAD', 'script': 'TIFINAGH', 'concept': 'D',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                         # single vertical
        ],
    },
    {
        'name': 'YADH', 'script': 'TIFINAGH', 'concept': 'DH',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 35), (42, 35)],                         # horizontal
            [(32, 22), (32, 48)],                         # vertical cross
        ],
    },
    {
        'name': 'YAF', 'script': 'TIFINAGH', 'concept': 'F',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(31, 24), (33, 24), (33, 26), (31, 26), (31, 24)],  # top dot
            [(26, 40), (28, 40), (28, 42), (26, 42), (26, 40)],  # bottom-left dot
            [(36, 40), (38, 40), (38, 42), (36, 42), (36, 40)],  # bottom-right dot
        ],
    },
    {
        'name': 'YAK', 'script': 'TIFINAGH', 'concept': 'K',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(26, 28), (32, 22), (38, 28), (38, 40),
             (32, 46), (26, 40), (26, 28)],               # circle
            [(38, 34), (46, 34)],                         # line extending right
        ],
    },
    {
        'name': 'YAKH', 'script': 'TIFINAGH', 'concept': 'KH',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 22), (42, 48)],                         # diagonal backslash
            [(42, 22), (22, 48)],                         # diagonal slash (X)
        ],
    },
    {
        'name': 'YAL', 'script': 'TIFINAGH', 'concept': 'L',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(32, 22), (32, 42)],                         # vertical
            [(32, 42), (24, 48)],                         # hook left
        ],
    },
    {
        'name': 'YAM', 'script': 'TIFINAGH', 'concept': 'M',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(20, 35), (44, 35)],                         # single horizontal
        ],
    },
    {
        'name': 'YAN', 'script': 'TIFINAGH', 'concept': 'N',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(30, 33), (34, 33), (34, 37), (30, 37), (30, 33)],  # single dot
        ],
    },
    {
        'name': 'YANY', 'script': 'TIFINAGH', 'concept': 'NY',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 46), (32, 22), (42, 46)],              # chevron up
        ],
    },
    {
        'name': 'YAR', 'script': 'TIFINAGH', 'concept': 'R',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(32, 22), (42, 35), (32, 48), (22, 35), (32, 22)],  # diamond
        ],
    },
    {
        'name': 'YARR', 'script': 'TIFINAGH', 'concept': 'RR',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(24, 24), (40, 24), (40, 46), (24, 46), (24, 24)],  # square
        ],
    },
    {
        'name': 'YAS', 'script': 'TIFINAGH', 'concept': 'S',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 30), (42, 30)],                         # upper horizontal
            [(22, 40), (42, 40)],                         # lower horizontal
        ],
    },
    {
        'name': 'YASH', 'script': 'TIFINAGH', 'concept': 'SH',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                         # center vertical
            [(24, 22), (24, 30)],                         # left prong
            [(40, 22), (40, 30)],                         # right prong
        ],
    },
    {
        'name': 'YAT', 'script': 'TIFINAGH', 'concept': 'T',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 35), (42, 35)],                         # horizontal
            [(32, 22), (32, 48)],                         # vertical (plus sign)
        ],
    },
    {
        'name': 'YATH', 'script': 'TIFINAGH', 'concept': 'TH',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 35), (32, 22), (42, 35)],              # angle bracket up
        ],
    },
    {
        'name': 'YAW', 'script': 'TIFINAGH', 'concept': 'W',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(28, 22), (36, 30), (28, 38), (36, 46)],    # vertical zigzag
        ],
    },
    {
        'name': 'YAY', 'script': 'TIFINAGH', 'concept': 'Y',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 22), (42, 22), (32, 44), (22, 22)],    # triangle pointing down
        ],
    },
    {
        'name': 'YAZ', 'script': 'TIFINAGH', 'concept': 'FREE AMAZIGH',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER, 'thick': True,
        'strokes': [
            [(26, 28), (32, 22), (38, 28), (38, 40),
             (32, 46), (26, 40), (26, 28)],               # outer circle
            [(22, 35), (42, 35)],                         # horizontal cross
            [(32, 22), (32, 48)],                         # vertical cross
        ],
    },
    {
        'name': 'YAZH', 'script': 'TIFINAGH', 'concept': 'ZH',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                         # left vertical
            [(24, 22), (40, 48)],                         # diagonal
            [(40, 22), (40, 48)],                         # right vertical (N shape)
        ],
    },
    {
        'name': 'YEJ', 'script': 'TIFINAGH', 'concept': 'J',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                         # left vertical
            [(40, 22), (40, 48)],                         # right vertical
            [(24, 35), (40, 35)],                         # horizontal bar (H)
        ],
    },
    {
        'name': 'YECH', 'script': 'TIFINAGH', 'concept': 'CH',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(26, 22), (26, 48)],                         # left vertical
            [(38, 22), (38, 48)],                         # right vertical
            [(26, 30), (38, 30)],                         # upper cross
            [(26, 40), (38, 40)],                         # lower cross
        ],
    },
    {
        'name': 'YI', 'script': 'TIFINAGH', 'concept': 'I',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(28, 33), (30, 33), (30, 37), (28, 37), (28, 33)],  # left dot
            [(34, 33), (36, 33), (36, 37), (34, 37), (34, 33)],  # right dot
        ],
    },
    {
        'name': 'YU', 'script': 'TIFINAGH', 'concept': 'U',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],                         # top horizontal
            [(22, 35), (42, 35)],                         # middle horizontal
            [(22, 42), (42, 42)],                         # bottom horizontal
        ],
    },
    {
        'name': 'YUN', 'script': 'TIFINAGH', 'concept': 'N (ALT)',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(32, 22), (32, 48)],                         # vertical
            [(32, 35), (42, 35)],                         # right horizontal
        ],
    },
    {
        'name': 'YUR', 'script': 'TIFINAGH', 'concept': 'R (ALT)',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 44), (32, 24), (42, 44)],              # chevron up
        ],
    },
    {
        'name': 'YUS', 'script': 'TIFINAGH', 'concept': 'S (ALT)',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(26, 22), (26, 48)],                         # vertical spine
            [(26, 24), (38, 24)],                         # tooth 1
            [(26, 30), (38, 30)],                         # tooth 2
            [(26, 36), (38, 36)],                         # tooth 3
            [(26, 42), (38, 42)],                         # tooth 4
        ],
    },
    {
        'name': 'YUSH', 'script': 'TIFINAGH', 'concept': 'SH (ALT)',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(24, 22), (24, 46), (40, 46), (40, 22)],    # U shape open top
        ],
    },
    {
        'name': 'YUTT', 'script': 'TIFINAGH', 'concept': 'TT',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 35), (42, 35)],                         # horizontal
            [(32, 22), (32, 48)],                         # vertical (main plus)
            [(20, 28), (26, 28), (26, 42), (20, 42)],    # left bracket
            [(44, 28), (38, 28), (38, 42), (44, 42)],    # right bracket
        ],
    },
    {
        'name': 'YER', 'script': 'TIFINAGH', 'concept': 'R (VARIANT)',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 40), (26, 28), (32, 24), (38, 28), (42, 40)],  # half circle arc
        ],
    },
    {
        'name': 'YEY', 'script': 'TIFINAGH', 'concept': 'Y (VARIANT)',
        'origin': 'NORTH AFRICA ~200 BC',
        'ink': _TIFI_INK, 'paper': _TIFI_PAPER,
        'strokes': [
            [(22, 22), (32, 42)],                         # left arm down
            [(42, 22), (32, 42)],                         # right arm down (V)
            [(32, 42), (32, 48)],                         # tail
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

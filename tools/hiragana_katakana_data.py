"""
Generated stroke data for Hiragana (42 new) and Katakana (46) characters.
Copy these into the CHARACTERS list in visuals/scripts.py.
"""

# These reference the ink/paper constants already defined in scripts.py:
# _JAPANESE_INK = (20, 20, 20)
# _JAPANESE_PAPER = (230, 225, 215)

_JAPANESE_INK = (20, 20, 20)
_JAPANESE_PAPER = (230, 225, 215)

HIRAGANA_CHARS = [
    # ── HIRAGANA (42 new characters) ───────────────────────────────
    # Vowels
    {
        'name': 'I', 'script': 'HIRAGANA', 'concept': 'I',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (24, 30), (22, 40), (24, 48)],          # left curve
            [(38, 22), (36, 32), (38, 44), (40, 48)],          # right curve
        ],
    },
    {
        'name': 'U', 'script': 'HIRAGANA', 'concept': 'U',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(30, 20), (32, 22)],                               # small tick
            [(34, 24), (32, 32), (28, 40), (30, 46), (36, 48)], # main curve
        ],
    },
    {
        'name': 'E', 'script': 'HIRAGANA', 'concept': 'E',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top horizontal
            [(34, 26), (30, 34), (24, 40), (28, 46), (36, 48), (42, 44)], # curvy body
        ],
    },
    {
        'name': 'O', 'script': 'HIRAGANA', 'concept': 'O',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top horizontal
            [(34, 20), (34, 48)],                               # vertical
            [(34, 34), (28, 40), (24, 46), (28, 50), (36, 46), (40, 40)], # hook loop
        ],
    },
    # K-row
    {
        'name': 'KI', 'script': 'HIRAGANA', 'concept': 'KI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(22, 32), (42, 32)],                               # middle bar
            [(36, 20), (32, 36)],                               # diagonal
            [(30, 38), (28, 44), (32, 48), (38, 46)],          # bottom curve
        ],
    },
    {
        'name': 'KU', 'script': 'HIRAGANA', 'concept': 'KU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 20), (28, 34), (40, 48)],                    # angular < shape
        ],
    },
    {
        'name': 'KE', 'script': 'HIRAGANA', 'concept': 'KE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # left vertical
            [(24, 30), (36, 28)],                               # small horizontal
            [(38, 20), (36, 32), (34, 42), (38, 48)],          # right curve
        ],
    },
    {
        'name': 'KO', 'script': 'HIRAGANA', 'concept': 'KO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],                               # upper bar
            [(22, 42), (42, 42)],                               # lower bar
        ],
    },
    # S-row
    {
        'name': 'SHI', 'script': 'HIRAGANA', 'concept': 'SHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(30, 20), (28, 30), (26, 40), (28, 46), (34, 48), (40, 44)], # J-curve
        ],
    },
    {
        'name': 'SU', 'script': 'HIRAGANA', 'concept': 'SU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal bar
            [(34, 26), (30, 34), (26, 40), (30, 46), (36, 44), (34, 38)], # loop below
        ],
    },
    {
        'name': 'SE', 'script': 'HIRAGANA', 'concept': 'SE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],                               # horizontal bar
            [(34, 22), (34, 46)],                               # vertical
            [(26, 38), (24, 44), (28, 48), (36, 48), (40, 44)], # curved bottom
        ],
    },
    {
        'name': 'SO', 'script': 'HIRAGANA', 'concept': 'SO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top horizontal
            [(34, 24), (28, 32), (34, 40), (40, 46), (42, 48)], # S-curve body
        ],
    },
    # T-row
    {
        'name': 'TA', 'script': 'HIRAGANA', 'concept': 'TA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(34, 20), (30, 34)],                               # slanting vertical
            [(22, 34), (42, 34)],                               # middle bar
            [(34, 34), (30, 42), (34, 48), (40, 44)],          # curve
        ],
    },
    {
        'name': 'CHI', 'script': 'HIRAGANA', 'concept': 'CHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal bar
            [(38, 26), (34, 34), (26, 40), (22, 48)],          # curving stroke
        ],
    },
    {
        'name': 'TSU', 'script': 'HIRAGANA', 'concept': 'TSU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 28), (28, 32), (36, 32), (44, 26)],          # wide curve/smile
        ],
    },
    {
        'name': 'TE', 'script': 'HIRAGANA', 'concept': 'TE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 26), (44, 26)],                               # top horizontal
            [(32, 26), (30, 34), (28, 42), (32, 48), (40, 46)], # curving down
        ],
    },
    {
        'name': 'TO', 'script': 'HIRAGANA', 'concept': 'TO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(28, 22), (28, 48)],                               # vertical
            [(28, 32), (36, 34), (42, 38)],                    # small horizontal curving away
        ],
    },
    # N-row
    {
        'name': 'NA', 'script': 'HIRAGANA', 'concept': 'NA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top horizontal
            [(34, 20), (30, 34)],                               # slanting vertical
            [(28, 34), (24, 40), (28, 46), (34, 44), (32, 38)], # loop
            [(38, 34), (40, 42), (42, 48)],                    # separate right stroke
        ],
    },
    {
        'name': 'NI', 'script': 'HIRAGANA', 'concept': 'NI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # left vertical
            [(30, 28), (40, 30)],                               # upper tick
            [(30, 40), (40, 42)],                               # lower tick
        ],
    },
    {
        'name': 'NU', 'script': 'HIRAGANA', 'concept': 'NU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],                               # horizontal bar
            [(36, 28), (28, 36), (24, 42), (28, 48), (36, 46), (40, 40), (36, 34)], # knot loop
        ],
    },
    {
        'name': 'NE', 'script': 'HIRAGANA', 'concept': 'NE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # vertical
            [(24, 30), (38, 28)],                               # cross stroke
            [(38, 28), (34, 36), (28, 42), (32, 48), (40, 46), (42, 40)], # loop curve
        ],
    },
    # H-row
    {
        'name': 'HA', 'script': 'HIRAGANA', 'concept': 'HA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # left vertical
            [(24, 30), (38, 28)],                               # cross stroke
            [(38, 22), (36, 34), (30, 42), (34, 48), (42, 44)], # right curve with loop
        ],
    },
    {
        'name': 'HI', 'script': 'HIRAGANA', 'concept': 'HI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (32, 28), (24, 36), (32, 42), (40, 46)], # S-curve
        ],
    },
    {
        'name': 'FU', 'script': 'HIRAGANA', 'concept': 'FU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(28, 22), (30, 24)],                               # left dot
            [(36, 22), (34, 24)],                               # right dot
            [(32, 28), (26, 36), (28, 44), (36, 48), (42, 42)], # curved body
        ],
    },
    {
        'name': 'HE', 'script': 'HIRAGANA', 'concept': 'HE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 38), (32, 26), (44, 38)],                    # chevron/mountain shape
        ],
    },
    {
        'name': 'HO', 'script': 'HIRAGANA', 'concept': 'HO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(24, 20), (24, 48)],                               # left vertical
            [(24, 34), (40, 34)],                               # middle bar
            [(36, 34), (34, 42), (38, 48), (44, 44)],          # bottom right loop
        ],
    },
    # M-row
    {
        'name': 'MA', 'script': 'HIRAGANA', 'concept': 'MA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top horizontal
            [(34, 20), (34, 42)],                               # vertical
            [(34, 34), (28, 40), (30, 48), (38, 46), (36, 38)], # loop below
        ],
    },
    {
        'name': 'MI', 'script': 'HIRAGANA', 'concept': 'MI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (36, 22), (40, 28), (30, 32)],          # upper curve
            [(24, 36), (36, 34), (40, 40), (34, 46), (24, 48)], # lower loop
        ],
    },
    {
        'name': 'MU', 'script': 'HIRAGANA', 'concept': 'MU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal bar
            [(34, 26), (28, 34), (24, 42), (28, 48), (36, 46), (40, 40)], # curved body with loop
            [(36, 32), (38, 34)],                               # small tick
        ],
    },
    {
        'name': 'ME', 'script': 'HIRAGANA', 'concept': 'ME',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(36, 20), (28, 30), (24, 38), (28, 46), (36, 48), (42, 42), (38, 34)], # loop stroke
        ],
    },
    {
        'name': 'MO', 'script': 'HIRAGANA', 'concept': 'MO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top bar
            [(22, 34), (42, 34)],                               # middle bar
            [(32, 22), (32, 42), (34, 48)],                    # vertical curving
        ],
    },
    # Y-row
    {
        'name': 'YA', 'script': 'HIRAGANA', 'concept': 'YA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top horizontal
            [(36, 20), (30, 36)],                               # left diagonal
            [(30, 36), (28, 44), (34, 48), (42, 44)],          # curve at bottom
        ],
    },
    {
        'name': 'YU', 'script': 'HIRAGANA', 'concept': 'YU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (24, 44), (30, 48), (38, 44)],          # left curve body
            [(38, 28), (42, 44)],                               # right stroke
        ],
    },
    {
        'name': 'YO', 'script': 'HIRAGANA', 'concept': 'YO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top horizontal
            [(34, 22), (34, 48)],                               # vertical
            [(22, 38), (34, 38)],                               # small bar
        ],
    },
    # R-row
    {
        'name': 'RA', 'script': 'HIRAGANA', 'concept': 'RA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 26), (38, 26)],                               # short horizontal
            [(34, 26), (30, 34), (26, 42), (30, 48), (38, 46)], # curving body
        ],
    },
    {
        'name': 'RI', 'script': 'HIRAGANA', 'concept': 'RI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (24, 32), (26, 42), (30, 46)],          # left curved stroke
            [(38, 22), (36, 34), (38, 44), (40, 48)],          # right curved stroke
        ],
    },
    {
        'name': 'RU', 'script': 'HIRAGANA', 'concept': 'RU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 26), (38, 26)],                               # short horizontal
            [(34, 26), (30, 36), (28, 44), (32, 48), (38, 46), (36, 40)], # vertical into loop
        ],
    },
    {
        'name': 'RE', 'script': 'HIRAGANA', 'concept': 'RE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # vertical
            [(24, 30), (36, 28), (40, 34), (36, 42), (28, 46), (32, 50), (40, 48)], # curving loop
        ],
    },
    {
        'name': 'RO', 'script': 'HIRAGANA', 'concept': 'RO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 26), (38, 26)],                               # short horizontal
            [(34, 26), (30, 36), (26, 44), (30, 50)],          # simple curve (no tight loop)
        ],
    },
    # W-row
    {
        'name': 'WA', 'script': 'HIRAGANA', 'concept': 'WA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # vertical
            [(24, 30), (38, 28)],                               # cross stroke
            [(38, 28), (36, 36), (30, 42), (34, 48), (42, 44)], # curving body
        ],
    },
    {
        'name': 'WO', 'script': 'HIRAGANA', 'concept': 'WO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(22, 32), (42, 32)],                               # middle bar
            [(36, 24), (32, 38), (28, 44), (34, 48), (42, 44)], # sweeping curve
        ],
    },
    # N
    {
        'name': 'N', 'script': 'HIRAGANA', 'concept': 'N',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(30, 20), (28, 30), (26, 40), (30, 48), (36, 44), (34, 36), (28, 30)], # large comma curving left
        ],
    },
]


KATAKANA_CHARS = [
    # ── KATAKANA (46 characters) ───────────────────────────────────
    # Vowels
    {
        'name': 'A', 'script': 'KATAKANA', 'concept': 'A',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal bar
            [(36, 20), (28, 48)],                               # diagonal
        ],
    },
    {
        'name': 'I', 'script': 'KATAKANA', 'concept': 'I',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(36, 20), (28, 34)],                               # left diagonal
            [(36, 20), (38, 48)],                               # right diagonal
        ],
    },
    {
        'name': 'U', 'script': 'KATAKANA', 'concept': 'U',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(32, 20), (32, 22)],                               # top tick
            [(22, 28), (42, 28)],                               # horizontal
            [(22, 28), (22, 46)],                               # left vertical
            [(42, 28), (42, 46)],                               # right vertical
        ],
    },
    {
        'name': 'E', 'script': 'KATAKANA', 'concept': 'E',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(32, 24), (32, 46)],                               # vertical
            [(22, 46), (42, 46)],                               # bottom bar
        ],
    },
    {
        'name': 'O', 'script': 'KATAKANA', 'concept': 'O',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],                               # horizontal
            [(34, 20), (34, 48)],                               # vertical
            [(34, 34), (22, 46)],                               # diagonal
        ],
    },
    # K-row
    {
        'name': 'KA', 'script': 'KATAKANA', 'concept': 'KA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(36, 20), (36, 48)],                               # vertical
            [(22, 26), (36, 26)],                               # horizontal arm
            [(36, 32), (22, 48)],                               # diagonal down-left
        ],
    },
    {
        'name': 'KI', 'script': 'KATAKANA', 'concept': 'KI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top bar
            [(22, 36), (42, 36)],                               # bottom bar
            [(36, 20), (28, 48)],                               # vertical/diagonal
        ],
    },
    {
        'name': 'KU', 'script': 'KATAKANA', 'concept': 'KU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 22), (22, 34)],                               # upper diagonal
            [(22, 34), (40, 48)],                               # lower diagonal
        ],
    },
    {
        'name': 'KE', 'script': 'KATAKANA', 'concept': 'KE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 42)],                               # left vertical
            [(24, 28), (42, 28)],                               # horizontal
            [(40, 22), (36, 48)],                               # right diagonal
        ],
    },
    {
        'name': 'KO', 'script': 'KATAKANA', 'concept': 'KO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(42, 24), (42, 46)],                               # right vertical
            [(22, 46), (42, 46)],                               # bottom bar
        ],
    },
    # S-row
    {
        'name': 'SA', 'script': 'KATAKANA', 'concept': 'SA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top bar
            [(22, 36), (42, 36)],                               # middle bar
            [(36, 22), (28, 48)],                               # diagonal
        ],
    },
    {
        'name': 'SHI', 'script': 'KATAKANA', 'concept': 'SHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (24, 26)],                               # upper dot
            [(22, 34), (24, 36)],                               # lower dot
            [(38, 26), (36, 36), (38, 44), (42, 48)],          # right curve
        ],
    },
    {
        'name': 'SU', 'script': 'KATAKANA', 'concept': 'SU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal
            [(38, 26), (22, 48)],                               # diagonal down-left
        ],
    },
    {
        'name': 'SE', 'script': 'KATAKANA', 'concept': 'SE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(34, 20), (34, 48)],                               # vertical
            [(22, 30), (44, 30)],                               # horizontal
            [(22, 30), (22, 44)],                               # left descender
        ],
    },
    {
        'name': 'SO', 'script': 'KATAKANA', 'concept': 'SO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (28, 24)],                               # left tick
            [(36, 24), (32, 36), (34, 46), (40, 48)],          # main curve
        ],
    },
    # T-row
    {
        'name': 'TA', 'script': 'KATAKANA', 'concept': 'TA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal
            [(36, 20), (28, 48)],                               # left diagonal
            [(36, 32), (42, 48)],                               # right diagonal
        ],
    },
    {
        'name': 'CHI', 'script': 'KATAKANA', 'concept': 'CHI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top bar
            [(32, 26), (22, 38), (26, 46), (36, 48), (42, 42)], # curved body
        ],
    },
    {
        'name': 'TSU', 'script': 'KATAKANA', 'concept': 'TSU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 22), (24, 24)],                               # left dot
            [(32, 22), (34, 24)],                               # right dot
            [(40, 24), (34, 36), (36, 46), (42, 48)],          # diagonal curve
        ],
    },
    {
        'name': 'TE', 'script': 'KATAKANA', 'concept': 'TE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 24), (44, 24)],                               # top bar
            [(22, 36), (42, 36)],                               # bottom bar (shorter)
            [(32, 36), (32, 48)],                               # descender
        ],
    },
    {
        'name': 'TO', 'script': 'KATAKANA', 'concept': 'TO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(28, 20), (28, 48)],                               # vertical
            [(28, 30), (42, 38)],                               # horizontal arm
        ],
    },
    # N-row
    {
        'name': 'NA', 'script': 'KATAKANA', 'concept': 'NA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal
            [(36, 20), (22, 48)],                               # diagonal
        ],
    },
    {
        'name': 'NI', 'script': 'KATAKANA', 'concept': 'NI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 28), (42, 28)],                               # top bar
            [(22, 44), (42, 44)],                               # bottom bar
        ],
    },
    {
        'name': 'NU', 'script': 'KATAKANA', 'concept': 'NU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal
            [(38, 26), (24, 44), (28, 48), (36, 44)],          # diagonal with hook
        ],
    },
    {
        'name': 'NE', 'script': 'KATAKANA', 'concept': 'NE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 20), (24, 48)],                               # left vertical
            [(24, 28), (42, 28)],                               # top horizontal
            [(24, 38), (42, 38)],                               # bottom horizontal
            [(42, 28), (42, 48)],                               # right vertical
        ],
    },
    {
        'name': 'NO', 'script': 'KATAKANA', 'concept': 'NO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 20), (24, 48)],                               # single diagonal
        ],
    },
    # H-row
    {
        'name': 'HA', 'script': 'KATAKANA', 'concept': 'HA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (36, 34)],                               # left diagonal
            [(40, 24), (28, 48)],                               # right diagonal crossing
        ],
    },
    {
        'name': 'HI', 'script': 'KATAKANA', 'concept': 'HI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # left vertical
            [(24, 26), (42, 30)],                               # upper connecting
            [(24, 42), (42, 38)],                               # lower connecting
            [(42, 30), (42, 38)],                               # right short vertical
        ],
    },
    {
        'name': 'FU', 'script': 'KATAKANA', 'concept': 'FU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(30, 24), (22, 48)],                               # left diagonal
        ],
    },
    {
        'name': 'HE', 'script': 'KATAKANA', 'concept': 'HE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(20, 38), (32, 26), (44, 38)],                    # chevron (same as hiragana)
        ],
    },
    {
        'name': 'HO', 'script': 'KATAKANA', 'concept': 'HO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(24, 20), (24, 48)],                               # left vertical
            [(24, 36), (42, 36)],                               # middle bar
            [(42, 24), (42, 48)],                               # right vertical
        ],
    },
    # M-row
    {
        'name': 'MA', 'script': 'KATAKANA', 'concept': 'MA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top bar
            [(22, 36), (42, 36)],                               # bottom bar
            [(38, 22), (26, 48)],                               # diagonal
        ],
    },
    {
        'name': 'MI', 'script': 'KATAKANA', 'concept': 'MI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 24), (40, 26)],                               # top tick
            [(24, 34), (40, 36)],                               # middle tick
            [(24, 44), (40, 46)],                               # bottom tick
        ],
    },
    {
        'name': 'MU', 'script': 'KATAKANA', 'concept': 'MU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 20), (22, 42), (32, 48), (42, 42)],          # angular body
            [(42, 20), (42, 42)],                               # right vertical
        ],
    },
    {
        'name': 'ME', 'script': 'KATAKANA', 'concept': 'ME',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(40, 20), (24, 48)],                               # left diagonal
            [(24, 30), (42, 40)],                               # crossing diagonal
        ],
    },
    {
        'name': 'MO', 'script': 'KATAKANA', 'concept': 'MO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top bar
            [(22, 36), (42, 36)],                               # middle bar
            [(32, 22), (32, 48)],                               # vertical
        ],
    },
    # Y-row
    {
        'name': 'YA', 'script': 'KATAKANA', 'concept': 'YA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # horizontal
            [(36, 20), (28, 48)],                               # left diagonal
            [(36, 30), (44, 48)],                               # right diagonal
        ],
    },
    {
        'name': 'YU', 'script': 'KATAKANA', 'concept': 'YU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(22, 24), (22, 46)],                               # left vertical
            [(22, 46), (42, 46)],                               # bottom bar
        ],
    },
    {
        'name': 'YO', 'script': 'KATAKANA', 'concept': 'YO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(22, 36), (42, 36)],                               # middle bar
            [(42, 24), (42, 48)],                               # right vertical
        ],
    },
    # R-row
    {
        'name': 'RA', 'script': 'KATAKANA', 'concept': 'RA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 26), (42, 26)],                               # top bar
            [(22, 26), (22, 48)],                               # left vertical
            [(22, 48), (42, 48)],                               # bottom bar
        ],
    },
    {
        'name': 'RI', 'script': 'KATAKANA', 'concept': 'RI',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(26, 22), (26, 44)],                               # left vertical
            [(38, 22), (38, 44)],                               # right vertical
        ],
    },
    {
        'name': 'RU', 'script': 'KATAKANA', 'concept': 'RU',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 22), (22, 42), (32, 48)],                    # left side
            [(42, 22), (42, 42), (32, 48)],                    # right side meeting
        ],
    },
    {
        'name': 'RE', 'script': 'KATAKANA', 'concept': 'RE',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],                               # vertical
            [(24, 22), (42, 28)],                               # diagonal arm
        ],
    },
    {
        'name': 'RO', 'script': 'KATAKANA', 'concept': 'RO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(22, 24), (22, 46)],                               # left vertical
            [(22, 46), (42, 46)],                               # bottom bar
        ],
    },
    # W-row
    {
        'name': 'WA', 'script': 'KATAKANA', 'concept': 'WA',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (24, 46)],                               # left vertical
            [(24, 26), (42, 26)],                               # top horizontal
            [(42, 26), (42, 36), (36, 46)],                    # right side curving
        ],
    },
    {
        'name': 'WO', 'script': 'KATAKANA', 'concept': 'WO',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(22, 24), (42, 24)],                               # top bar
            [(22, 34), (42, 34)],                               # middle bar
            [(36, 24), (28, 48)],                               # diagonal
        ],
    },
    # N
    {
        'name': 'N', 'script': 'KATAKANA', 'concept': 'N',
        'origin': 'HEIAN PERIOD ~800 AD',
        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,
        'strokes': [
            [(24, 22), (26, 24)],                               # upper dot
            [(36, 26), (32, 38), (36, 46), (42, 48)],          # main curve
        ],
    },
]


# ── Print for easy copy-paste ──────────────────────────────────────
if __name__ == '__main__':
    print("# ── HIRAGANA (" + str(len(HIRAGANA_CHARS)) + " characters) ──")
    for ch in HIRAGANA_CHARS:
        print("    {")
        print(f"        'name': '{ch['name']}', 'script': '{ch['script']}', 'concept': '{ch['concept']}',")
        print(f"        'origin': '{ch['origin']}',")
        print(f"        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,")
        print(f"        'strokes': [")
        for s in ch['strokes']:
            print(f"            {s},")
        print(f"        ],")
        print("    },")

    print()
    print("# ── KATAKANA (" + str(len(KATAKANA_CHARS)) + " characters) ──")
    for ch in KATAKANA_CHARS:
        print("    {")
        print(f"        'name': '{ch['name']}', 'script': '{ch['script']}', 'concept': '{ch['concept']}',")
        print(f"        'origin': '{ch['origin']}',")
        print(f"        'ink': _JAPANESE_INK, 'paper': _JAPANESE_PAPER,")
        print(f"        'strokes': [")
        for s in ch['strokes']:
            print(f"            {s},")
        print(f"        ],")
        print("    },")

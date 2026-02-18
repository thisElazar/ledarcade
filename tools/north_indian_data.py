"""
Generated stroke data for Gujarati (47), Gurmukhi (35), and Sinhala (50) characters.
Copy these into the CHARACTERS list in visuals/scripts.py.
"""

# ── Color constants ──────────────────────────────────────────────
_GUJARATI_INK = (160, 50, 20)
_GUJARATI_PAPER = (230, 222, 200)
_GURMUKHI_INK = (30, 40, 120)
_GURMUKHI_PAPER = (225, 225, 215)
_SINHALA_INK = (120, 40, 30)
_SINHALA_PAPER = (228, 225, 210)

# ── Gurmukhi headline bar (shared) ──────────────────────────────
_GM_HEAD = [(18, 22), (46, 22)]

# ══════════════════════════════════════════════════════════════════
#  GUJARATI  —  47 characters
#  No headline bar. Letters float freely (like Devanagari minus shirorekha).
# ══════════════════════════════════════════════════════════════════
GUJARATI_CHARS = [
    # ── Vowels (13) ──────────────────────────────────────────────
    {
        'name': 'A', 'script': 'GUJARATI', 'concept': 'A',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(30, 24), (30, 46)],                               # left vertical
            [(30, 24), (40, 24), (42, 28), (40, 32), (30, 34)], # top loop
            [(30, 34), (40, 38), (42, 44), (38, 48)],           # lower curve
        ],
    },
    {
        'name': 'Aa', 'script': 'GUJARATI', 'concept': 'AA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (26, 46)],                               # left vertical
            [(26, 24), (36, 24), (38, 28), (36, 32), (26, 34)], # top loop
            [(26, 34), (36, 38), (38, 44), (34, 48)],           # lower curve
            [(42, 24), (42, 46)],                                # right vertical stroke
        ],
    },
    {
        'name': 'I', 'script': 'GUJARATI', 'concept': 'I',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (36, 24), (38, 28), (34, 32), (28, 32)], # top loop
            [(28, 32), (28, 46)],                                # descender
        ],
    },
    {
        'name': 'Ii', 'script': 'GUJARATI', 'concept': 'II',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (34, 24), (36, 28), (32, 32), (26, 32)], # top loop
            [(26, 32), (26, 46)],                                # descender
            [(40, 24), (40, 36)],                                # right tick
        ],
    },
    {
        'name': 'U', 'script': 'GUJARATI', 'concept': 'U',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (26, 42), (30, 46), (36, 46), (40, 42)], # U-shape
            [(40, 42), (40, 24)],                                # right upstroke
        ],
    },
    {
        'name': 'Uu', 'script': 'GUJARATI', 'concept': 'UU',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (24, 42), (28, 46), (34, 46), (38, 42)], # U-shape
            [(38, 42), (38, 24)],                                # right upstroke
            [(42, 38), (44, 42), (42, 46)],                     # tail mark
        ],
    },
    {
        'name': 'E', 'script': 'GUJARATI', 'concept': 'E',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 30), (36, 24), (42, 28), (38, 34), (28, 36)], # top curve
            [(28, 36), (24, 42), (28, 48), (38, 46)],           # bottom curve
        ],
    },
    {
        'name': 'Ai', 'script': 'GUJARATI', 'concept': 'AI',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 30), (36, 24), (42, 28), (38, 34), (28, 36)], # top curve
            [(28, 36), (24, 42), (28, 48), (38, 46)],           # bottom curve
            [(36, 20), (40, 22)],                                # diacritic dot
        ],
    },
    {
        'name': 'O', 'script': 'GUJARATI', 'concept': 'O',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(30, 24), (30, 46)],                               # vertical
            [(30, 24), (40, 24), (42, 28), (40, 32), (30, 34)], # top loop
            [(30, 34), (40, 38), (42, 44), (38, 48)],           # lower curve
            [(28, 20), (32, 20), (34, 22)],                     # top mark
        ],
    },
    {
        'name': 'Au', 'script': 'GUJARATI', 'concept': 'AU',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(30, 24), (30, 46)],                               # vertical
            [(30, 24), (40, 24), (42, 28), (40, 32), (30, 34)], # top loop
            [(30, 34), (40, 38), (42, 44), (38, 48)],           # lower curve
            [(26, 20), (30, 20)],                                # left mark
            [(34, 20), (38, 20)],                                # right mark
        ],
    },
    {
        'name': 'Am', 'script': 'GUJARATI', 'concept': 'AM',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(30, 26), (30, 46)],                               # vertical
            [(30, 26), (40, 26), (42, 30), (40, 34), (30, 34)], # loop
            [(34, 20), (36, 22)],                                # anusvara dot
        ],
    },
    {
        'name': 'Ah', 'script': 'GUJARATI', 'concept': 'AH',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(30, 24), (30, 46)],                               # vertical
            [(30, 24), (40, 24), (42, 28), (40, 32), (30, 34)], # loop
            [(44, 28), (44, 32)],                                # visarga top dot
            [(44, 38), (44, 42)],                                # visarga bottom dot
        ],
    },
    {
        'name': 'Ri', 'script': 'GUJARATI', 'concept': 'RI',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 26), (36, 22), (40, 26), (36, 30), (28, 30)], # top loop
            [(28, 30), (24, 38), (28, 46), (36, 44), (40, 38)], # bottom curve
        ],
    },
    # ── Consonants (34) ──────────────────────────────────────────
    {
        'name': 'Ka', 'script': 'GUJARATI', 'concept': 'KA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 46)],                               # left vertical
            [(28, 24), (38, 24), (42, 28), (38, 32), (28, 32)], # top loop
        ],
    },
    {
        'name': 'Kha', 'script': 'GUJARATI', 'concept': 'KHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 46)],                               # left vertical
            [(28, 24), (38, 24), (42, 28), (38, 32), (28, 32)], # top loop
            [(28, 36), (36, 36), (40, 40), (36, 46)],           # lower loop
        ],
    },
    {
        'name': 'Ga', 'script': 'GUJARATI', 'concept': 'GA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (40, 24)],                               # top bar
            [(32, 24), (32, 34), (26, 40), (24, 46)],           # left curve down
            [(32, 34), (38, 40), (40, 46)],                     # right curve down
        ],
    },
    {
        'name': 'Gha', 'script': 'GUJARATI', 'concept': 'GHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(22, 24), (38, 24)],                               # top bar
            [(30, 24), (30, 34), (24, 40), (22, 46)],           # left down
            [(30, 34), (36, 40), (38, 46)],                     # right down
            [(42, 24), (42, 40), (40, 46)],                     # added stroke
        ],
    },
    {
        'name': 'Nga', 'script': 'GUJARATI', 'concept': 'NGA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (36, 24), (40, 28), (36, 32), (28, 32), (24, 36), (28, 40)],
            [(32, 40), (32, 48)],                               # tail
        ],
    },
    {
        'name': 'Cha', 'script': 'GUJARATI', 'concept': 'CHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (40, 24)],                               # top bar
            [(32, 24), (32, 46)],                                # vertical
            [(24, 34), (40, 34)],                                # mid bar
        ],
    },
    {
        'name': 'Chha', 'script': 'GUJARATI', 'concept': 'CHHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (40, 24)],                               # top bar
            [(32, 24), (32, 46)],                                # vertical
            [(24, 34), (40, 34)],                                # mid bar
            [(36, 40), (40, 44), (38, 48)],                     # foot curl
        ],
    },
    {
        'name': 'Ja', 'script': 'GUJARATI', 'concept': 'JA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 46)],                               # vertical
            [(28, 28), (38, 24), (42, 28), (38, 34), (28, 36)], # right loop
        ],
    },
    {
        'name': 'Jha', 'script': 'GUJARATI', 'concept': 'JHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (26, 46)],                               # vertical
            [(26, 28), (36, 24), (40, 28), (36, 34), (26, 36)], # right loop
            [(26, 40), (34, 38), (38, 42), (34, 46)],           # lower loop
        ],
    },
    {
        'name': 'Nya', 'script': 'GUJARATI', 'concept': 'NYA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 28), (32, 24), (40, 28), (36, 34), (28, 36), (24, 42), (28, 48)],
            [(36, 36), (40, 42), (38, 48)],                     # right tail
        ],
    },
    {
        'name': 'Ta_retro', 'script': 'GUJARATI', 'concept': 'TTA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (42, 24)],                               # top bar
            [(42, 24), (42, 36), (36, 40), (28, 38)],           # right hook
            [(28, 38), (24, 44), (28, 48), (36, 48)],           # bottom curve
        ],
    },
    {
        'name': 'Tha_retro', 'script': 'GUJARATI', 'concept': 'TTHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (42, 24)],                               # top bar
            [(42, 24), (42, 36), (36, 40), (28, 38)],           # right hook
            [(28, 38), (24, 44), (28, 48), (36, 48)],           # bottom curve
            [(32, 30), (34, 32)],                                # inner dot
        ],
    },
    {
        'name': 'Da_retro', 'script': 'GUJARATI', 'concept': 'DDA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (40, 24), (44, 30), (40, 36), (28, 36)], # top loop
            [(28, 36), (28, 48)],                                # descender
        ],
    },
    {
        'name': 'Dha_retro', 'script': 'GUJARATI', 'concept': 'DDHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (38, 24), (42, 30), (38, 36), (26, 36)], # top loop
            [(26, 36), (26, 48)],                                # descender
            [(42, 36), (44, 42), (42, 48)],                     # right tail
        ],
    },
    {
        'name': 'Na_retro', 'script': 'GUJARATI', 'concept': 'NNA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (42, 24)],                               # top bar
            [(32, 24), (32, 38)],                                # center stem
            [(24, 38), (32, 38), (40, 42), (36, 48), (28, 48)], # bottom bowl
        ],
    },
    {
        'name': 'Ta', 'script': 'GUJARATI', 'concept': 'TA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (40, 24), (44, 30), (40, 36), (24, 36)], # top loop
            [(24, 36), (24, 48)],                                # left descender
        ],
    },
    {
        'name': 'Tha', 'script': 'GUJARATI', 'concept': 'THA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 28), (38, 24), (42, 28), (38, 34), (26, 34)], # loop
            [(26, 24), (26, 46)],                                # left vertical
            [(26, 46), (38, 46)],                                # bottom bar
        ],
    },
    {
        'name': 'Da', 'script': 'GUJARATI', 'concept': 'DA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 34), (32, 24), (40, 28), (40, 38), (32, 42), (24, 40)],
            [(32, 42), (32, 48)],                                # tail
        ],
    },
    {
        'name': 'Dha', 'script': 'GUJARATI', 'concept': 'DHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(22, 34), (30, 24), (38, 28), (38, 38), (30, 42), (22, 40)],
            [(30, 42), (30, 48)],                                # tail
            [(42, 28), (44, 34), (42, 40)],                     # right hook
        ],
    },
    {
        'name': 'Na', 'script': 'GUJARATI', 'concept': 'NA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (26, 46)],                               # left vertical
            [(26, 24), (40, 24)],                                # top bar
            [(40, 24), (40, 36), (34, 40), (26, 38)],           # right curve
        ],
    },
    {
        'name': 'Pa', 'script': 'GUJARATI', 'concept': 'PA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 46)],                               # vertical
            [(28, 24), (40, 24)],                                # top bar
            [(28, 34), (40, 34)],                                # mid bar
        ],
    },
    {
        'name': 'Pha', 'script': 'GUJARATI', 'concept': 'PHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 46)],                               # vertical
            [(28, 24), (40, 24)],                                # top bar
            [(28, 34), (40, 34), (42, 40), (38, 46)],           # mid bar with curl
        ],
    },
    {
        'name': 'Ba', 'script': 'GUJARATI', 'concept': 'BA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (42, 24)],                               # top bar
            [(26, 24), (26, 46)],                                # left vertical
            [(42, 24), (42, 46)],                                # right vertical
            [(26, 46), (42, 46)],                                # bottom bar
        ],
    },
    {
        'name': 'Bha', 'script': 'GUJARATI', 'concept': 'BHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (40, 24)],                               # top bar
            [(24, 24), (24, 46)],                                # left vertical
            [(40, 24), (40, 46)],                                # right vertical
            [(24, 46), (40, 46)],                                # bottom bar
            [(40, 34), (44, 38), (42, 44)],                     # right hook
        ],
    },
    {
        'name': 'Ma', 'script': 'GUJARATI', 'concept': 'MA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 46)],                               # left vertical
            [(28, 24), (42, 24)],                                # top bar
            [(42, 24), (42, 34)],                                # right short vertical
            [(28, 34), (42, 34)],                                # mid bar
        ],
    },
    {
        'name': 'Ya', 'script': 'GUJARATI', 'concept': 'YA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 28), (32, 24), (40, 28), (40, 40), (32, 46), (24, 42)],
        ],
    },
    {
        'name': 'Ra', 'script': 'GUJARATI', 'concept': 'RA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (36, 24), (40, 28), (38, 34)],          # top hook
            [(38, 34), (32, 38), (28, 44), (30, 48)],           # descender curve
        ],
    },
    {
        'name': 'La', 'script': 'GUJARATI', 'concept': 'LA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 46)],                               # vertical
            [(28, 34), (38, 30), (42, 34), (38, 40), (28, 42)], # right loop
        ],
    },
    {
        'name': 'Va', 'script': 'GUJARATI', 'concept': 'VA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (40, 24)],                               # top bar
            [(26, 24), (26, 38), (32, 42), (40, 38), (40, 24)], # U-shape body
        ],
    },
    {
        'name': 'Sha', 'script': 'GUJARATI', 'concept': 'SHA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(24, 24), (24, 46)],                               # left vertical
            [(24, 24), (42, 34)],                                # diagonal right
            [(24, 34), (42, 24)],                                # diagonal cross
            [(42, 24), (42, 46)],                                # right vertical
        ],
    },
    {
        'name': 'Sha_retro', 'script': 'GUJARATI', 'concept': 'SSA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (26, 46)],                               # left vertical
            [(26, 24), (40, 24)],                                # top bar
            [(40, 24), (40, 36), (34, 40), (26, 38)],           # right hook
            [(34, 40), (38, 46), (42, 48)],                     # tail
        ],
    },
    {
        'name': 'Sa', 'script': 'GUJARATI', 'concept': 'SA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (38, 24), (42, 28), (38, 34), (28, 34)], # top loop
            [(28, 34), (22, 40), (28, 46), (38, 46), (42, 40)], # bottom loop
        ],
    },
    {
        'name': 'Ha', 'script': 'GUJARATI', 'concept': 'HA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(26, 24), (26, 46)],                               # left vertical
            [(26, 28), (36, 24), (42, 28), (42, 36)],           # top right curve
            [(42, 36), (36, 40), (26, 38)],                     # return curve
            [(32, 40), (32, 48)],                                # bottom tail
        ],
    },
    {
        'name': 'Lla', 'script': 'GUJARATI', 'concept': 'LLA',
        'origin': 'GUJARATI ~1600 AD',
        'ink': _GUJARATI_INK, 'paper': _GUJARATI_PAPER,
        'strokes': [
            [(28, 24), (28, 40)],                               # vertical
            [(28, 40), (24, 46), (28, 50), (36, 48), (40, 42)], # bottom loop
            [(28, 32), (38, 28), (42, 32), (38, 36), (28, 36)], # right loop
        ],
    },
]

# ══════════════════════════════════════════════════════════════════
#  GURMUKHI  —  35 characters
#  Has headline bar. Angular, clean, geometric. Created for Sikh scripture.
# ══════════════════════════════════════════════════════════════════
GURMUKHI_CHARS = [
    # ── Vowels (10) ──────────────────────────────────────────────
    {
        'name': 'A', 'script': 'GURMUKHI', 'concept': 'A',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # center vertical
            [(24, 32), (32, 32), (38, 36), (36, 42), (30, 46)], # left hook body
        ],
    },
    {
        'name': 'Aa', 'script': 'GURMUKHI', 'concept': 'AA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 46)],                                # left vertical
            [(28, 34), (36, 30), (40, 34), (36, 40), (28, 42)], # belly loop
            [(40, 22), (40, 46)],                                # right vertical
        ],
    },
    {
        'name': 'I', 'script': 'GURMUKHI', 'concept': 'I',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # center vertical
            [(26, 28), (32, 32), (38, 28)],                     # angular V above
        ],
    },
    {
        'name': 'Ii', 'script': 'GURMUKHI', 'concept': 'II',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # center vertical
            [(26, 28), (32, 32), (38, 28)],                     # angular V
            [(32, 46), (28, 50), (36, 50)],                     # bottom tick
        ],
    },
    {
        'name': 'U', 'script': 'GURMUKHI', 'concept': 'U',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(30, 22), (30, 40), (34, 46), (38, 40), (38, 22)], # U shape
        ],
    },
    {
        'name': 'Uu', 'script': 'GURMUKHI', 'concept': 'UU',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 40), (32, 46), (36, 40), (36, 22)], # U shape
            [(40, 38), (42, 44), (40, 48)],                     # tail mark
        ],
    },
    {
        'name': 'E', 'script': 'GURMUKHI', 'concept': 'E',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # vertical
            [(24, 30), (40, 30)],                                # cross bar
        ],
    },
    {
        'name': 'Ai', 'script': 'GURMUKHI', 'concept': 'AI',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # vertical
            [(24, 30), (40, 30)],                                # cross bar
            [(28, 18), (32, 20)],                                # top mark
        ],
    },
    {
        'name': 'O', 'script': 'GURMUKHI', 'concept': 'O',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # vertical
            [(24, 32), (32, 32), (38, 36), (36, 42), (30, 46)], # hook
            [(30, 18), (34, 18)],                                # top mark
        ],
    },
    {
        'name': 'Au', 'script': 'GURMUKHI', 'concept': 'AU',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # vertical
            [(24, 32), (32, 32), (38, 36), (36, 42), (30, 46)], # hook
            [(28, 18), (32, 18), (36, 18)],                     # double top mark
        ],
    },
    # ── Consonants (25) ──────────────────────────────────────────
    {
        'name': 'Sa', 'script': 'GURMUKHI', 'concept': 'SA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(24, 22), (24, 46)],                                # left vertical
            [(24, 34), (34, 30), (40, 34), (34, 40), (24, 42)], # belly
        ],
    },
    {
        'name': 'Ha', 'script': 'GURMUKHI', 'concept': 'HA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 46)],                                # left vertical
            [(40, 22), (40, 46)],                                # right vertical
            [(26, 34), (40, 34)],                                # cross bar
        ],
    },
    {
        'name': 'Ka', 'script': 'GURMUKHI', 'concept': 'KA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 46)],                                # vertical
            [(28, 28), (38, 26), (42, 30), (38, 36), (28, 36)], # right loop
        ],
    },
    {
        'name': 'Kha', 'script': 'GURMUKHI', 'concept': 'KHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 46)],                                # vertical
            [(26, 28), (36, 26), (40, 30), (36, 36), (26, 36)], # top loop
            [(26, 40), (34, 38), (38, 42), (34, 46)],           # bottom loop
        ],
    },
    {
        'name': 'Ga', 'script': 'GURMUKHI', 'concept': 'GA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(30, 22), (30, 38), (34, 44), (40, 46)],           # left curve down
            [(38, 22), (38, 34)],                                # right short vertical
        ],
    },
    {
        'name': 'Gha', 'script': 'GURMUKHI', 'concept': 'GHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 38), (32, 44), (38, 46)],           # left curve
            [(36, 22), (36, 34)],                                # right short vertical
            [(32, 48), (34, 50)],                                # dot below
        ],
    },
    {
        'name': 'Nga', 'script': 'GURMUKHI', 'concept': 'NGA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 40), (30, 46), (36, 46), (40, 40), (40, 22)],
        ],
    },
    {
        'name': 'Cha', 'script': 'GURMUKHI', 'concept': 'CHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # center vertical
            [(24, 34), (32, 38), (40, 34)],                     # angular V right
        ],
    },
    {
        'name': 'Chha', 'script': 'GURMUKHI', 'concept': 'CHHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # center vertical
            [(24, 34), (32, 38), (40, 34)],                     # angular V
            [(36, 42), (40, 46), (38, 50)],                     # foot curl
        ],
    },
    {
        'name': 'Ja', 'script': 'GURMUKHI', 'concept': 'JA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 46)],                                # left vertical
            [(28, 30), (36, 26), (42, 30), (42, 38), (36, 44), (28, 42)],
        ],
    },
    {
        'name': 'Jha', 'script': 'GURMUKHI', 'concept': 'JHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 46)],                                # left vertical
            [(26, 30), (34, 26), (40, 30), (40, 38), (34, 44), (26, 42)],
            [(34, 48), (36, 50)],                                # dot below
        ],
    },
    {
        'name': 'Nya', 'script': 'GURMUKHI', 'concept': 'NYA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 38), (32, 44), (40, 44)],           # left curve
            [(40, 22), (40, 44)],                                # right vertical
        ],
    },
    {
        'name': 'Ta_retro', 'script': 'GURMUKHI', 'concept': 'TTA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (32, 46)],                                # center vertical
            [(24, 28), (40, 28)],                                # upper cross bar
            [(24, 40), (40, 40)],                                # lower cross bar
        ],
    },
    {
        'name': 'Tha_retro', 'script': 'GURMUKHI', 'concept': 'TTHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 46)],                                # left vertical
            [(26, 28), (42, 28)],                                # upper cross bar
            [(26, 38), (36, 38), (40, 42), (36, 46)],           # lower bar with hook
        ],
    },
    {
        'name': 'Da_retro', 'script': 'GURMUKHI', 'concept': 'DDA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 42), (32, 46), (40, 44)],           # left vertical with foot
            [(28, 32), (38, 28), (42, 32), (38, 36), (28, 36)], # right loop
        ],
    },
    {
        'name': 'Dha_retro', 'script': 'GURMUKHI', 'concept': 'DDHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 42), (30, 46), (38, 44)],           # left vertical with foot
            [(26, 32), (36, 28), (40, 32), (36, 36), (26, 36)], # right loop
            [(34, 48), (36, 50)],                                # dot below
        ],
    },
    {
        'name': 'Na_retro', 'script': 'GURMUKHI', 'concept': 'NNA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 46)],                                # left vertical
            [(40, 22), (40, 46)],                                # right vertical
            [(28, 34), (34, 38), (40, 34)],                     # angular connector
        ],
    },
    {
        'name': 'Ta', 'script': 'GURMUKHI', 'concept': 'TA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 46)],                                # left vertical
            [(26, 30), (36, 26), (42, 30), (36, 36), (26, 36)], # loop
        ],
    },
    {
        'name': 'Tha', 'script': 'GURMUKHI', 'concept': 'THA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 46)],                                # vertical
            [(28, 28), (38, 26), (44, 30), (44, 42), (38, 46), (28, 44)],
        ],
    },
    {
        'name': 'Da', 'script': 'GURMUKHI', 'concept': 'DA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(32, 22), (24, 34), (24, 44), (32, 48), (40, 44), (40, 34), (32, 22)],
        ],
    },
    {
        'name': 'Dha', 'script': 'GURMUKHI', 'concept': 'DHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(30, 22), (22, 34), (22, 44), (30, 48), (38, 44), (38, 34), (30, 22)],
            [(42, 30), (44, 36), (42, 42)],                     # right mark
        ],
    },
    {
        'name': 'Na', 'script': 'GURMUKHI', 'concept': 'NA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 46)],                                # left vertical
            [(42, 22), (42, 46)],                                # right vertical
            [(26, 46), (42, 46)],                                # bottom bar
        ],
    },
    {
        'name': 'Pa', 'script': 'GURMUKHI', 'concept': 'PA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 46)],                                # vertical
            [(28, 26), (38, 24), (42, 28), (38, 34), (28, 34)], # top bump
            [(28, 40), (36, 38), (40, 42), (36, 46)],           # bottom bump
        ],
    },
    {
        'name': 'Pha', 'script': 'GURMUKHI', 'concept': 'PHA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(28, 22), (28, 46)],                                # vertical
            [(28, 28), (36, 24), (42, 28), (42, 40), (36, 46), (28, 42)],
        ],
    },
    {
        'name': 'Ba', 'script': 'GURMUKHI', 'concept': 'BA',
        'origin': 'GURU ANGAD 1539 AD',
        'ink': _GURMUKHI_INK, 'paper': _GURMUKHI_PAPER, 'thick': True,
        'strokes': [
            _GM_HEAD,                                            # headline
            [(26, 22), (26, 46)],                                # left vertical
            [(26, 34), (34, 30), (42, 34), (42, 42), (36, 46), (26, 46)],
        ],
    },
]

# ══════════════════════════════════════════════════════════════════
#  SINHALA  —  50 characters
#  Extremely rounded, curvy, loopy. One of the most distinctive scripts.
# ══════════════════════════════════════════════════════════════════
SINHALA_CHARS = [
    # ── Vowels (16) ──────────────────────────────────────────────
    {
        'name': 'A', 'script': 'SINHALA', 'concept': 'A',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 28), (22, 34), (26, 40), (34, 40), (38, 34), (34, 28), (26, 28)],
            [(34, 40), (38, 46), (34, 50)],                     # tail
        ],
    },
    {
        'name': 'Aa', 'script': 'SINHALA', 'concept': 'AA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(24, 28), (20, 34), (24, 40), (32, 40), (36, 34), (32, 28), (24, 28)],
            [(32, 40), (36, 46), (32, 50)],                     # tail
            [(40, 24), (42, 30), (40, 36)],                     # right mark
        ],
    },
    {
        'name': 'Ae', 'script': 'SINHALA', 'concept': 'AE',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 30), (24, 36), (28, 42), (36, 42), (40, 36), (36, 30), (28, 30)],
            [(22, 24), (28, 28)],                                # top left tick
        ],
    },
    {
        'name': 'Aee', 'script': 'SINHALA', 'concept': 'AEE',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 30), (24, 36), (28, 42), (36, 42), (40, 36), (36, 30), (28, 30)],
            [(22, 24), (28, 28)],                                # top left tick
            [(40, 24), (44, 28)],                                # top right tick
        ],
    },
    {
        'name': 'I', 'script': 'SINHALA', 'concept': 'I',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 24), (26, 30), (30, 36), (36, 36), (40, 30), (36, 24), (30, 24)],
            [(30, 36), (26, 42), (30, 48)],                     # bottom left curl
        ],
    },
    {
        'name': 'Ii', 'script': 'SINHALA', 'concept': 'II',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (24, 30), (28, 36), (34, 36), (38, 30), (34, 24), (28, 24)],
            [(28, 36), (24, 42), (28, 48)],                     # bottom curl
            [(40, 30), (44, 36), (40, 42)],                     # right loop
        ],
    },
    {
        'name': 'U', 'script': 'SINHALA', 'concept': 'U',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(24, 30), (28, 24), (36, 24), (40, 30), (36, 36), (28, 36), (24, 30)],
            [(32, 36), (32, 44), (28, 48)],                     # descender
        ],
    },
    {
        'name': 'Uu', 'script': 'SINHALA', 'concept': 'UU',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(22, 30), (26, 24), (34, 24), (38, 30), (34, 36), (26, 36), (22, 30)],
            [(30, 36), (30, 44), (26, 48)],                     # descender
            [(40, 36), (44, 42), (40, 48)],                     # right tail
        ],
    },
    {
        'name': 'E', 'script': 'SINHALA', 'concept': 'E',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(24, 38), (20, 44), (24, 48), (30, 48)],           # bottom left loop
        ],
    },
    {
        'name': 'Ee', 'script': 'SINHALA', 'concept': 'EE',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(24, 38), (20, 44), (24, 48), (30, 48)],           # bottom loop
            [(42, 28), (44, 32)],                                # right dot
        ],
    },
    {
        'name': 'Ai', 'script': 'SINHALA', 'concept': 'AI',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 28), (22, 34), (26, 40), (34, 40), (38, 34), (34, 28), (26, 28)],
            [(26, 40), (22, 46), (26, 50), (32, 50)],           # bottom curl
            [(38, 24), (42, 28), (38, 32)],                     # top right loop
        ],
    },
    {
        'name': 'O', 'script': 'SINHALA', 'concept': 'O',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 28), (24, 34), (28, 40), (36, 40), (40, 34), (36, 28), (28, 28)],
            [(28, 40), (24, 44), (28, 48)],                     # bottom left
            [(36, 40), (40, 44), (36, 48)],                     # bottom right
        ],
    },
    {
        'name': 'Oo', 'script': 'SINHALA', 'concept': 'OO',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 28), (22, 34), (26, 40), (34, 40), (38, 34), (34, 28), (26, 28)],
            [(26, 40), (22, 44), (26, 48)],                     # bottom left
            [(34, 40), (38, 44), (34, 48)],                     # bottom right
            [(40, 26), (44, 30), (40, 34)],                     # right mark
        ],
    },
    {
        'name': 'Au', 'script': 'SINHALA', 'concept': 'AU',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 28), (22, 34), (26, 40), (34, 40), (38, 34), (34, 28), (26, 28)],
            [(34, 40), (38, 46), (34, 50)],                     # tail
            [(20, 22), (26, 26)],                                # top left mark
            [(38, 22), (44, 26)],                                # top right mark
        ],
    },
    {
        'name': 'Am', 'script': 'SINHALA', 'concept': 'AM',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 28), (24, 34), (28, 40), (36, 40), (40, 34), (36, 28), (28, 28)],
            [(36, 40), (40, 46), (36, 50)],                     # tail
            [(32, 22), (34, 24)],                                # anusvara dot
        ],
    },
    {
        'name': 'Aha', 'script': 'SINHALA', 'concept': 'AHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 28), (24, 34), (28, 40), (36, 40), (40, 34), (36, 28), (28, 28)],
            [(36, 40), (40, 46), (36, 50)],                     # tail
            [(42, 30), (44, 34)],                                # visarga top
            [(42, 40), (44, 44)],                                # visarga bottom
        ],
    },
    # ── Consonants (34) ──────────────────────────────────────────
    {
        'name': 'Ka', 'script': 'SINHALA', 'concept': 'KA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 26), (22, 32), (26, 38), (34, 38), (38, 32), (34, 26), (26, 26)],
            [(34, 38), (40, 44), (36, 48), (30, 48)],           # tail loop
        ],
    },
    {
        'name': 'Kha', 'script': 'SINHALA', 'concept': 'KHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(24, 26), (20, 32), (24, 38), (32, 38), (36, 32), (32, 26), (24, 26)],
            [(32, 38), (38, 44), (34, 48), (28, 48)],           # tail loop
            [(40, 28), (44, 34), (40, 40)],                     # right stroke
        ],
    },
    {
        'name': 'Ga', 'script': 'SINHALA', 'concept': 'GA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 24), (26, 30), (30, 36), (38, 36), (42, 30), (38, 24), (30, 24)],
            [(26, 36), (22, 42), (26, 48), (34, 46)],           # left tail
        ],
    },
    {
        'name': 'Gha', 'script': 'SINHALA', 'concept': 'GHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (24, 30), (28, 36), (36, 36), (40, 30), (36, 24), (28, 24)],
            [(24, 36), (20, 42), (24, 48), (32, 46)],           # left tail
            [(40, 36), (44, 42), (40, 48)],                     # right tail
        ],
    },
    {
        'name': 'Nga', 'script': 'SINHALA', 'concept': 'NGA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 26), (26, 32), (30, 38), (38, 38), (42, 32), (38, 26), (30, 26)],
            [(30, 38), (26, 44), (30, 50), (38, 50), (42, 44), (38, 38)],
        ],
    },
    {
        'name': 'Cha', 'script': 'SINHALA', 'concept': 'CHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (24, 30), (28, 36), (34, 32), (38, 36), (42, 30), (38, 24)],
            [(28, 36), (24, 42), (28, 48), (34, 48)],           # bottom curl
        ],
    },
    {
        'name': 'Chha', 'script': 'SINHALA', 'concept': 'CHHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (26, 36), (32, 32), (36, 36), (40, 30), (36, 24)],
            [(26, 36), (22, 42), (26, 48), (32, 48)],           # bottom curl
            [(40, 36), (44, 40), (42, 46)],                     # right tail
        ],
    },
    {
        'name': 'Ja', 'script': 'SINHALA', 'concept': 'JA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(28, 38), (32, 44), (28, 50), (22, 48)],           # bottom left curl
        ],
    },
    {
        'name': 'Jha', 'script': 'SINHALA', 'concept': 'JHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 26), (22, 32), (26, 38), (34, 38), (38, 32), (34, 26), (26, 26)],
            [(26, 38), (30, 44), (26, 50), (20, 48)],           # bottom curl
            [(38, 38), (42, 44), (38, 50)],                     # right tail
        ],
    },
    {
        'name': 'Nya', 'script': 'SINHALA', 'concept': 'NYA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 26), (22, 30), (24, 36), (30, 36), (34, 30), (30, 26), (26, 26)],
            [(34, 30), (38, 26), (42, 30), (42, 36), (38, 40)], # right loop
            [(30, 36), (26, 42), (30, 48)],                     # descender
        ],
    },
    {
        'name': 'Ta_retro', 'script': 'SINHALA', 'concept': 'TTA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 24), (24, 30), (28, 38), (36, 38), (42, 30), (38, 24)],
            [(36, 38), (40, 44), (34, 48), (28, 44)],           # bottom loop
        ],
    },
    {
        'name': 'Tha_retro', 'script': 'SINHALA', 'concept': 'TTHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (22, 30), (26, 38), (34, 38), (40, 30), (36, 24)],
            [(34, 38), (38, 44), (32, 48), (26, 44)],           # bottom loop
            [(42, 28), (44, 34)],                                # right tick
        ],
    },
    {
        'name': 'Da_retro', 'script': 'SINHALA', 'concept': 'DDA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(32, 24), (26, 28), (24, 34), (28, 40), (36, 40), (40, 34), (38, 28), (32, 24)],
            [(28, 40), (24, 46), (30, 50)],                     # tail
        ],
    },
    {
        'name': 'Dha_retro', 'script': 'SINHALA', 'concept': 'DDHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 24), (24, 28), (22, 34), (26, 40), (34, 40), (38, 34), (36, 28), (30, 24)],
            [(26, 40), (22, 46), (28, 50)],                     # tail
            [(40, 34), (44, 40), (40, 46)],                     # right curl
        ],
    },
    {
        'name': 'Na_retro', 'script': 'SINHALA', 'concept': 'NNA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(28, 38), (24, 44), (28, 50), (36, 50), (40, 44), (36, 38)],
        ],
    },
    {
        'name': 'Ta', 'script': 'SINHALA', 'concept': 'TA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 28), (22, 34), (26, 40), (34, 40), (38, 34), (34, 28), (26, 28)],
            [(22, 24), (26, 28)],                                # top left approach
            [(38, 40), (42, 46), (38, 50)],                     # right tail
        ],
    },
    {
        'name': 'Tha', 'script': 'SINHALA', 'concept': 'THA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(20, 22), (28, 26)],                                # top approach
            [(36, 38), (40, 44), (44, 46)],                     # right tail
        ],
    },
    {
        'name': 'Da', 'script': 'SINHALA', 'concept': 'DA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 24), (24, 30), (28, 38), (36, 34), (40, 28), (36, 22), (30, 24)],
            [(28, 38), (24, 44), (28, 50), (34, 50)],           # bottom loop
        ],
    },
    {
        'name': 'Dha', 'script': 'SINHALA', 'concept': 'DHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (22, 30), (26, 38), (34, 34), (38, 28), (34, 22), (28, 24)],
            [(26, 38), (22, 44), (26, 50), (32, 50)],           # bottom loop
            [(40, 30), (44, 36), (40, 42)],                     # right mark
        ],
    },
    {
        'name': 'Na', 'script': 'SINHALA', 'concept': 'NA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(24, 28), (28, 24), (36, 24), (40, 28), (40, 36), (36, 40), (28, 40), (24, 36), (24, 28)],
            [(32, 40), (32, 48)],                                # descender
        ],
    },
    {
        'name': 'Pa', 'script': 'SINHALA', 'concept': 'PA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 26), (26, 32), (30, 38), (38, 38), (42, 32), (38, 26), (30, 26)],
            [(30, 38), (26, 44), (30, 48)],                     # left tail
            [(38, 38), (42, 44), (38, 48)],                     # right tail
        ],
    },
    {
        'name': 'Pha', 'script': 'SINHALA', 'concept': 'PHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(28, 38), (24, 44), (28, 48)],                     # left tail
            [(36, 38), (40, 44), (36, 48)],                     # right tail
            [(42, 28), (44, 32)],                                # right tick
        ],
    },
    {
        'name': 'Ba', 'script': 'SINHALA', 'concept': 'BA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(36, 38), (40, 44), (36, 50), (28, 50), (24, 44)], # bottom loop
        ],
    },
    {
        'name': 'Bha', 'script': 'SINHALA', 'concept': 'BHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 26), (22, 32), (26, 38), (34, 38), (38, 32), (34, 26), (26, 26)],
            [(34, 38), (38, 44), (34, 50), (26, 50), (22, 44)], # bottom loop
            [(40, 28), (44, 34), (40, 40)],                     # right curl
        ],
    },
    {
        'name': 'Ma', 'script': 'SINHALA', 'concept': 'MA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (24, 30), (28, 36), (36, 36), (40, 30), (36, 24), (28, 24)],
            [(28, 36), (24, 42), (28, 48), (36, 48), (40, 42), (36, 36)],
        ],
    },
    {
        'name': 'Ya', 'script': 'SINHALA', 'concept': 'YA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 28), (22, 34), (26, 40), (32, 36), (36, 40), (42, 34), (38, 28)],
            [(32, 40), (28, 46), (32, 50), (38, 48)],           # bottom curl
        ],
    },
    {
        'name': 'Ra', 'script': 'SINHALA', 'concept': 'RA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 24), (26, 30), (30, 36), (36, 30), (32, 24)], # small top loop
            [(30, 36), (26, 42), (30, 48), (38, 48), (42, 42)], # bottom curve
        ],
    },
    {
        'name': 'La', 'script': 'SINHALA', 'concept': 'LA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (24, 30), (28, 38), (36, 38), (40, 30), (36, 24)],
            [(28, 38), (24, 44), (28, 50), (36, 50), (40, 44)], # bottom loop
        ],
    },
    {
        'name': 'Va', 'script': 'SINHALA', 'concept': 'VA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(20, 22), (24, 26), (28, 26)],                     # approach stroke
            [(36, 38), (40, 42), (44, 44)],                     # exit stroke
        ],
    },
    {
        'name': 'Sha', 'script': 'SINHALA', 'concept': 'SHA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(26, 26), (22, 30), (24, 36), (30, 36), (34, 30), (30, 26), (26, 26)],
            [(34, 30), (40, 26), (44, 30), (40, 36), (34, 36)], # right loop
            [(30, 36), (26, 42), (30, 48), (36, 48)],           # tail
        ],
    },
    {
        'name': 'Sha_retro', 'script': 'SINHALA', 'concept': 'SSA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(24, 26), (20, 30), (22, 36), (28, 36), (32, 30), (28, 26), (24, 26)],
            [(32, 30), (38, 26), (42, 30), (38, 36), (32, 36)], # right loop
            [(28, 36), (24, 42), (28, 48), (34, 48)],           # tail
            [(40, 38), (42, 42)],                                # right dot
        ],
    },
    {
        'name': 'Sa', 'script': 'SINHALA', 'concept': 'SA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(30, 24), (26, 30), (30, 36), (38, 36), (42, 30), (38, 24), (30, 24)],
            [(30, 36), (34, 42), (30, 48), (24, 44)],           # bottom left curl
        ],
    },
    {
        'name': 'Ha', 'script': 'SINHALA', 'concept': 'HA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 26), (24, 32), (28, 38), (36, 38), (40, 32), (36, 26), (28, 26)],
            [(28, 38), (24, 44), (28, 50)],                     # left descender
            [(36, 38), (40, 44), (36, 50)],                     # right descender
        ],
    },
    {
        'name': 'Lla', 'script': 'SINHALA', 'concept': 'LLA',
        'origin': 'SINHALA ~300 BC',
        'ink': _SINHALA_INK, 'paper': _SINHALA_PAPER,
        'strokes': [
            [(28, 24), (24, 30), (28, 38), (36, 38), (40, 30), (36, 24), (28, 24)],
            [(28, 38), (24, 44), (28, 50), (36, 50), (40, 44), (36, 38)],
            [(20, 22), (24, 24)],                                # top left tick
        ],
    },
]


# ── Verification ─────────────────────────────────────────────────
if __name__ == '__main__':
    for name, chars in [('GUJARATI', GUJARATI_CHARS), ('GURMUKHI', GURMUKHI_CHARS), ('SINHALA', SINHALA_CHARS)]:
        print(f'{name}: {len(chars)} chars')
        for ch in chars:
            for si, stroke in enumerate(ch['strokes']):
                for x, y in stroke:
                    assert 8 <= x <= 56 and 14 <= y <= 56, f"OOB: {ch['name']} ({x},{y})"
    print('All OK')

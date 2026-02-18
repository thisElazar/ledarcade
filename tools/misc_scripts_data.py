"""
Generated stroke data for 6 additional writing systems:
  Latin (26), Braille (26), Baybayin (17), Vai (28), Linear B (20), Rongorongo (15)
Copy these into the CHARACTERS list in visuals/scripts.py.
"""

# ── Color constants ─────────────────────────────────────────────
_LATIN_INK = (30, 30, 80)
_LATIN_PAPER = (230, 228, 220)
_BRAILLE_INK = (40, 40, 40)
_BRAILLE_PAPER = (225, 225, 225)
_BAYBAYIN_INK = (80, 40, 20)
_BAYBAYIN_PAPER = (220, 210, 185)
_VAI_INK = (40, 30, 20)
_VAI_PAPER = (225, 215, 195)
_LINEAR_B_INK = (50, 40, 100)
_LINEAR_B_PAPER = (215, 210, 195)
_RONGO_INK = (60, 40, 25)
_RONGO_PAPER = (200, 185, 155)

# ── Helper for Braille dot positions ────────────────────────────
# Standard Braille cell: 2 columns × 3 rows
#   1 4
#   2 5
#   3 6
_BRL_LX = 26   # left column x
_BRL_RX = 38   # right column x
_BRL_R1 = 24   # row 1 y
_BRL_R2 = 34   # row 2 y
_BRL_R3 = 44   # row 3 y

_BRL_POS = {
    1: (_BRL_LX, _BRL_R1),
    2: (_BRL_LX, _BRL_R2),
    3: (_BRL_LX, _BRL_R3),
    4: (_BRL_RX, _BRL_R1),
    5: (_BRL_RX, _BRL_R2),
    6: (_BRL_RX, _BRL_R3),
}


def _brl_dot(x, y):
    """Return a stroke forming a small 3×3 square at (x, y)."""
    return [(x - 1, y - 1), (x + 1, y - 1), (x + 1, y + 1), (x - 1, y + 1), (x - 1, y - 1)]


def _brl_char(name, concept, dots):
    """Build a Braille character dict from a list of active dot numbers."""
    return {
        'name': name, 'script': 'BRAILLE', 'concept': concept,
        'origin': 'LOUIS BRAILLE 1824 AD',
        'ink': _BRAILLE_INK, 'paper': _BRAILLE_PAPER,
        'strokes': [_brl_dot(*_BRL_POS[d]) for d in sorted(dots)],
    }


# ═══════════════════════════════════════════════════════════════
# 1. LATIN  –  26 uppercase Roman capital letters
# ═══════════════════════════════════════════════════════════════
# Drawing zone: roughly x 20–44, y 22–48 (centered in paper area)
_LI = _LATIN_INK
_LP = _LATIN_PAPER
_LO = 'ROMAN ~700 BC'
_LS = 'LATIN'

LATIN_CHARS = [
    # A – two diagonals + crossbar
    {
        'name': 'A', 'script': _LS, 'concept': 'A',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 48), (32, 22), (42, 48)],         # outer V
            [(26, 38), (38, 38)],                     # crossbar
        ],
    },
    # B – vertical + two bumps
    {
        'name': 'B', 'script': _LS, 'concept': 'B',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],                                        # vertical
            [(22, 22), (36, 22), (40, 26), (40, 32), (36, 35), (22, 35)],  # top bump
            [(22, 35), (36, 35), (42, 38), (42, 44), (36, 48), (22, 48)],  # bottom bump
        ],
    },
    # C – open curve
    {
        'name': 'C', 'script': _LS, 'concept': 'C',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(42, 24), (36, 22), (28, 22), (22, 26), (20, 32), (20, 38),
             (22, 44), (28, 48), (36, 48), (42, 46)],
        ],
    },
    # D – vertical + curve
    {
        'name': 'D', 'script': _LS, 'concept': 'D',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],                                        # vertical
            [(22, 22), (34, 22), (42, 28), (44, 35), (42, 42), (34, 48), (22, 48)],  # curve
        ],
    },
    # E – vertical + 3 horizontals
    {
        'name': 'E', 'script': _LS, 'concept': 'E',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],         # vertical
            [(22, 22), (42, 22)],          # top bar
            [(22, 35), (38, 35)],          # middle bar
            [(22, 48), (42, 48)],          # bottom bar
        ],
    },
    # F – vertical + 2 horizontals
    {
        'name': 'F', 'script': _LS, 'concept': 'F',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],          # vertical
            [(22, 22), (42, 22)],          # top bar
            [(22, 35), (38, 35)],          # middle bar
        ],
    },
    # G – C-curve + horizontal inward bar
    {
        'name': 'G', 'script': _LS, 'concept': 'G',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(42, 24), (36, 22), (28, 22), (22, 26), (20, 32), (20, 38),
             (22, 44), (28, 48), (36, 48), (42, 44), (42, 36)],
            [(34, 36), (42, 36)],                                        # inward bar
        ],
    },
    # H – two verticals + crossbar
    {
        'name': 'H', 'script': _LS, 'concept': 'H',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],          # left vertical
            [(42, 22), (42, 48)],          # right vertical
            [(22, 35), (42, 35)],          # crossbar
        ],
    },
    # I – vertical + top/bottom serifs
    {
        'name': 'I', 'script': _LS, 'concept': 'I',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(28, 22), (36, 22)],          # top serif
            [(32, 22), (32, 48)],          # vertical
            [(28, 48), (36, 48)],          # bottom serif
        ],
    },
    # J – curve at bottom + vertical
    {
        'name': 'J', 'script': _LS, 'concept': 'J',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(28, 22), (38, 22)],          # top serif
            [(34, 22), (34, 42), (32, 46), (28, 48), (24, 46)],  # body + hook
        ],
    },
    # K – vertical + two diagonals
    {
        'name': 'K', 'script': _LS, 'concept': 'K',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],          # vertical
            [(42, 22), (22, 36)],          # upper diagonal
            [(26, 33), (42, 48)],          # lower diagonal
        ],
    },
    # L – vertical + bottom horizontal
    {
        'name': 'L', 'script': _LS, 'concept': 'L',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],          # vertical
            [(22, 48), (42, 48)],          # bottom bar
        ],
    },
    # M – two verticals + V in between
    {
        'name': 'M', 'script': _LS, 'concept': 'M',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(20, 48), (20, 22)],                     # left vertical
            [(20, 22), (32, 38)],                     # left diagonal
            [(32, 38), (44, 22)],                     # right diagonal
            [(44, 22), (44, 48)],                     # right vertical
        ],
    },
    # N – two verticals + diagonal
    {
        'name': 'N', 'script': _LS, 'concept': 'N',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 48), (22, 22)],          # left vertical
            [(22, 22), (42, 48)],          # diagonal
            [(42, 48), (42, 22)],          # right vertical
        ],
    },
    # O – oval
    {
        'name': 'O', 'script': _LS, 'concept': 'O',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(32, 22), (24, 24), (20, 30), (20, 40), (24, 46), (32, 48),
             (40, 46), (44, 40), (44, 30), (40, 24), (32, 22)],
        ],
    },
    # P – vertical + top bump
    {
        'name': 'P', 'script': _LS, 'concept': 'P',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],                                        # vertical
            [(22, 22), (36, 22), (42, 26), (42, 32), (36, 36), (22, 36)],  # bump
        ],
    },
    # Q – oval + small tail
    {
        'name': 'Q', 'script': _LS, 'concept': 'Q',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(32, 22), (24, 24), (20, 30), (20, 40), (24, 46), (32, 48),
             (40, 46), (44, 40), (44, 30), (40, 24), (32, 22)],          # oval
            [(36, 42), (44, 50)],                                        # tail
        ],
    },
    # R – vertical + top bump + leg
    {
        'name': 'R', 'script': _LS, 'concept': 'R',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 48)],                                        # vertical
            [(22, 22), (36, 22), (42, 26), (42, 32), (36, 36), (22, 36)],  # bump
            [(32, 36), (42, 48)],                                        # leg
        ],
    },
    # S – two curves making S shape
    {
        'name': 'S', 'script': _LS, 'concept': 'S',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(40, 24), (36, 22), (28, 22), (22, 24), (22, 30), (26, 34),
             (32, 36), (38, 38), (42, 42), (42, 46), (36, 48), (28, 48),
             (22, 46)],
        ],
    },
    # T – horizontal bar + vertical from center
    {
        'name': 'T', 'script': _LS, 'concept': 'T',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(20, 22), (44, 22)],          # top bar
            [(32, 22), (32, 48)],          # vertical
        ],
    },
    # U – two verticals connected by curve at bottom
    {
        'name': 'U', 'script': _LS, 'concept': 'U',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (22, 42), (26, 46), (32, 48), (38, 46), (42, 42), (42, 22)],
        ],
    },
    # V – two diagonals meeting at bottom
    {
        'name': 'V', 'script': _LS, 'concept': 'V',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(20, 22), (32, 48)],          # left diagonal
            [(32, 48), (44, 22)],          # right diagonal
        ],
    },
    # W – like two Vs
    {
        'name': 'W', 'script': _LS, 'concept': 'W',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(18, 22), (24, 48)],          # left-1
            [(24, 48), (32, 30)],          # left-2
            [(32, 30), (40, 48)],          # right-1
            [(40, 48), (46, 22)],          # right-2
        ],
    },
    # X – two crossing diagonals
    {
        'name': 'X', 'script': _LS, 'concept': 'X',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (42, 48)],          # backslash
            [(42, 22), (22, 48)],          # forward slash
        ],
    },
    # Y – two upper diagonals meeting + vertical down
    {
        'name': 'Y', 'script': _LS, 'concept': 'Y',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(20, 22), (32, 36)],          # left upper arm
            [(44, 22), (32, 36)],          # right upper arm
            [(32, 36), (32, 48)],          # vertical down
        ],
    },
    # Z – top bar + diagonal + bottom bar
    {
        'name': 'Z', 'script': _LS, 'concept': 'Z',
        'origin': _LO, 'ink': _LI, 'paper': _LP,
        'strokes': [
            [(22, 22), (42, 22)],          # top bar
            [(42, 22), (22, 48)],          # diagonal
            [(22, 48), (42, 48)],          # bottom bar
        ],
    },
]

# ═══════════════════════════════════════════════════════════════
# 2. BRAILLE  –  26 letters (tactile dot patterns)
# ═══════════════════════════════════════════════════════════════
# Cell positions:  1 4
#                  2 5
#                  3 6
BRAILLE_CHARS = [
    _brl_char('A', 'A', [1]),
    _brl_char('B', 'B', [1, 2]),
    _brl_char('C', 'C', [1, 4]),
    _brl_char('D', 'D', [1, 4, 5]),
    _brl_char('E', 'E', [1, 5]),
    _brl_char('F', 'F', [1, 2, 4]),
    _brl_char('G', 'G', [1, 2, 4, 5]),
    _brl_char('H', 'H', [1, 2, 5]),
    _brl_char('I', 'I', [2, 4]),
    _brl_char('J', 'J', [2, 4, 5]),
    _brl_char('K', 'K', [1, 3]),
    _brl_char('L', 'L', [1, 2, 3]),
    _brl_char('M', 'M', [1, 3, 4]),
    _brl_char('N', 'N', [1, 3, 4, 5]),
    _brl_char('O', 'O', [1, 3, 5]),
    _brl_char('P', 'P', [1, 2, 3, 4]),
    _brl_char('Q', 'Q', [1, 2, 3, 4, 5]),
    _brl_char('R', 'R', [1, 2, 3, 5]),
    _brl_char('S', 'S', [2, 3, 4]),
    _brl_char('T', 'T', [2, 3, 4, 5]),
    _brl_char('U', 'U', [1, 3, 6]),
    _brl_char('V', 'V', [1, 2, 3, 6]),
    _brl_char('W', 'W', [2, 4, 5, 6]),
    _brl_char('X', 'X', [1, 3, 4, 6]),
    _brl_char('Y', 'Y', [1, 3, 4, 5, 6]),
    _brl_char('Z', 'Z', [1, 3, 5, 6]),
]

# ═══════════════════════════════════════════════════════════════
# 3. BAYBAYIN  –  17 characters (pre-colonial Philippines)
# ═══════════════════════════════════════════════════════════════
_BI = _BAYBAYIN_INK
_BP = _BAYBAYIN_PAPER
_BO = 'PHILIPPINES ~1300 AD'
_BS = 'BAYBAYIN'

BAYBAYIN_CHARS = [
    # ── Vowels ──
    # A – a vertical with a loop on top-right
    {
        'name': 'A', 'script': _BS, 'concept': 'A (vowel)',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(32, 22), (32, 48)],                              # main vertical
            [(32, 26), (38, 24), (40, 28), (36, 32), (32, 30)],  # top loop
        ],
    },
    # I/E – two curves side by side
    {
        'name': 'I/E', 'script': _BS, 'concept': 'I / E (vowel)',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(24, 22), (22, 32), (26, 42), (28, 48)],         # left curve
            [(36, 22), (34, 32), (38, 42), (40, 48)],         # right curve
        ],
    },
    # O/U – a loop with tail going down
    {
        'name': 'O/U', 'script': _BS, 'concept': 'O / U (vowel)',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(28, 24), (22, 28), (24, 34), (32, 36), (40, 34), (42, 28), (36, 24), (28, 24)],
            [(32, 36), (32, 48)],                              # tail
        ],
    },
    # ── Consonants ──
    # Ba – vertical with two curves to the right
    {
        'name': 'BA', 'script': _BS, 'concept': 'BA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(24, 22), (24, 48)],                              # vertical
            [(24, 26), (34, 24), (38, 28), (34, 32), (24, 34)],  # upper bump
            [(24, 36), (34, 38), (36, 42), (32, 46), (24, 48)],  # lower bump
        ],
    },
    # Ka – angular stroke like a V with tail
    {
        'name': 'KA', 'script': _BS, 'concept': 'KA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(22, 22), (32, 36), (42, 22)],                   # V top
            [(32, 36), (32, 48)],                              # tail down
        ],
    },
    # Da/Ra – curvy S shape
    {
        'name': 'DA', 'script': _BS, 'concept': 'DA / RA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(22, 22), (26, 28), (36, 30), (40, 36), (36, 42), (26, 44), (22, 48)],
        ],
    },
    # Ga – vertical with loop at top
    {
        'name': 'GA', 'script': _BS, 'concept': 'GA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(32, 22), (26, 24), (24, 30), (28, 34), (36, 32), (38, 26), (32, 22)],
            [(32, 34), (30, 42), (32, 48)],                    # descender
        ],
    },
    # Ha – like an arch
    {
        'name': 'HA', 'script': _BS, 'concept': 'HA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(22, 48), (22, 30), (28, 22), (36, 22), (42, 30), (42, 48)],
        ],
    },
    # La – tall vertical with a hook
    {
        'name': 'LA', 'script': _BS, 'concept': 'LA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(28, 22), (28, 44), (32, 48), (38, 46)],         # vertical + hook
            [(28, 30), (36, 28), (40, 32)],                    # side tick
        ],
    },
    # Ma – like two mountains or W shape
    {
        'name': 'MA', 'script': _BS, 'concept': 'MA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(20, 48), (24, 28), (32, 40), (40, 28), (44, 48)],
        ],
    },
    # Na – curvy like a cursive n
    {
        'name': 'NA', 'script': _BS, 'concept': 'NA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(22, 44), (22, 26), (28, 22), (34, 26), (34, 44)],
            [(34, 44), (38, 48), (42, 46)],                    # tail
        ],
    },
    # Nga – complex character, like Na with extra loop
    {
        'name': 'NGA', 'script': _BS, 'concept': 'NGA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(22, 44), (22, 26), (28, 22), (34, 26), (34, 44)],  # Na base
            [(34, 28), (40, 24), (44, 28), (40, 34), (34, 32)],  # extra loop
        ],
    },
    # Pa – like a backwards J with hook
    {
        'name': 'PA', 'script': _BS, 'concept': 'PA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(38, 22), (38, 44), (34, 48), (28, 46)],         # main stroke
            [(38, 28), (30, 26), (26, 30), (28, 34), (38, 36)],  # loop
        ],
    },
    # Sa – flowing curve like a musical note
    {
        'name': 'SA', 'script': _BS, 'concept': 'SA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(24, 22), (32, 26), (38, 34), (32, 42), (24, 48)],  # main curve
            [(32, 26), (40, 22), (44, 26)],                       # top flourish
        ],
    },
    # Ta – angular zigzag
    {
        'name': 'TA', 'script': _BS, 'concept': 'TA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(22, 22), (42, 22)],                              # top bar
            [(32, 22), (26, 36), (38, 42), (32, 48)],         # zigzag body
        ],
    },
    # Wa – like a wide U with curls
    {
        'name': 'WA', 'script': _BS, 'concept': 'WA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(20, 26), (22, 22), (26, 24)],                   # left curl
            [(22, 24), (22, 40), (28, 48), (36, 48), (42, 40), (42, 24)],  # U body
            [(38, 24), (42, 22), (44, 26)],                    # right curl
        ],
    },
    # Ya – like a curved Y
    {
        'name': 'YA', 'script': _BS, 'concept': 'YA',
        'origin': _BO, 'ink': _BI, 'paper': _BP,
        'strokes': [
            [(22, 22), (30, 34)],                              # left arm
            [(42, 22), (34, 34)],                              # right arm
            [(32, 34), (28, 42), (32, 48), (38, 46)],         # descender with curl
        ],
    },
]

# ═══════════════════════════════════════════════════════════════
# 4. VAI  –  28 key syllables (indigenous West African syllabary)
# ═══════════════════════════════════════════════════════════════
_VI = _VAI_INK
_VPa = _VAI_PAPER
_VO = 'MƆMƆLU DUWALU BUKƐLƐ ~1833 AD'
_VS = 'VAI'

VAI_CHARS = [
    # Vowels
    # A – open triangular shape
    {
        'name': 'A', 'script': _VS, 'concept': 'A',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 48), (32, 22), (42, 48)],                   # triangle
            [(27, 36), (37, 36)],                              # crossbar
        ],
    },
    # E – like a backwards 3
    {
        'name': 'E', 'script': _VS, 'concept': 'E',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 22), (36, 22), (40, 26), (36, 34), (28, 36)],   # upper curve
            [(28, 36), (38, 38), (42, 44), (36, 48), (22, 48)],   # lower curve
        ],
    },
    # I – vertical with a small circle at top
    {
        'name': 'I', 'script': _VS, 'concept': 'I',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(32, 28), (32, 48)],                              # vertical
            [(30, 22), (34, 22), (34, 26), (30, 26), (30, 22)],  # head dot
        ],
    },
    # O – circle
    {
        'name': 'O', 'script': _VS, 'concept': 'O',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(32, 22), (24, 26), (20, 34), (24, 44), (32, 48),
             (40, 44), (44, 34), (40, 26), (32, 22)],
        ],
    },
    # U – horseshoe shape
    {
        'name': 'U', 'script': _VS, 'concept': 'U',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 22), (22, 40), (28, 48), (36, 48), (42, 40), (42, 22)],
        ],
    },
    # Ba – like a circle with a line through it
    {
        'name': 'BA', 'script': _VS, 'concept': 'BA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(26, 24), (22, 32), (26, 42), (34, 46), (42, 42), (44, 32), (40, 24), (32, 22), (26, 24)],
            [(20, 34), (44, 34)],                              # horizontal through
        ],
    },
    # Da – like a d with a long tail
    {
        'name': 'DA', 'script': _VS, 'concept': 'DA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(38, 22), (38, 48)],                              # vertical
            [(38, 28), (30, 26), (24, 30), (24, 38), (30, 42), (38, 40)],  # bowl
        ],
    },
    # Fa – like an f shape
    {
        'name': 'FA', 'script': _VS, 'concept': 'FA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(28, 22), (28, 48)],                              # vertical
            [(28, 22), (40, 22), (42, 28)],                    # top hook
            [(22, 34), (36, 34)],                              # crossbar
        ],
    },
    # Ga – like a gamma
    {
        'name': 'GA', 'script': _VS, 'concept': 'GA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 22), (42, 22)],                              # top bar
            [(32, 22), (28, 34), (30, 44), (36, 48)],         # descending curve
        ],
    },
    # Ha – like an arch with legs
    {
        'name': 'HA', 'script': _VS, 'concept': 'HA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 48), (22, 28), (32, 22), (42, 28), (42, 48)],   # arch
            [(32, 22), (32, 48)],                                   # center line
        ],
    },
    # Ja – angular J-like
    {
        'name': 'JA', 'script': _VS, 'concept': 'JA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 22), (42, 22)],                              # top bar
            [(36, 22), (36, 40), (30, 48), (22, 46)],         # descender + hook
        ],
    },
    # Ka – like a k shape
    {
        'name': 'KA', 'script': _VS, 'concept': 'KA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(24, 22), (24, 48)],                              # vertical
            [(40, 22), (24, 36)],                              # upper leg
            [(28, 34), (42, 48)],                              # lower leg
        ],
    },
    # La – like an L with a curve
    {
        'name': 'LA', 'script': _VS, 'concept': 'LA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(24, 22), (24, 48), (36, 48), (42, 44)],         # L + curve
        ],
    },
    # Ma – like an M
    {
        'name': 'MA', 'script': _VS, 'concept': 'MA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(20, 48), (20, 22), (32, 38), (44, 22), (44, 48)],
        ],
    },
    # Na – curvy n shape
    {
        'name': 'NA', 'script': _VS, 'concept': 'NA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 48), (22, 28), (28, 22), (36, 22), (42, 28), (42, 48)],
        ],
    },
    # Pa – like a P
    {
        'name': 'PA', 'script': _VS, 'concept': 'PA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(24, 22), (24, 48)],                              # vertical
            [(24, 22), (36, 22), (42, 28), (40, 34), (32, 36), (24, 34)],  # bump
        ],
    },
    # Ra – like a cursive r
    {
        'name': 'RA', 'script': _VS, 'concept': 'RA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(24, 22), (24, 48)],                              # vertical
            [(24, 22), (32, 22), (38, 26), (36, 30)],         # top curve
        ],
    },
    # Sa – like an S
    {
        'name': 'SA', 'script': _VS, 'concept': 'SA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(40, 24), (34, 22), (26, 22), (22, 26), (24, 32), (32, 36),
             (40, 40), (42, 46), (36, 48), (26, 48), (22, 46)],
        ],
    },
    # Ta – cross / plus shape
    {
        'name': 'TA', 'script': _VS, 'concept': 'TA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(20, 34), (44, 34)],                              # horizontal
            [(32, 22), (32, 48)],                              # vertical
        ],
    },
    # Wa – wavy line
    {
        'name': 'WA', 'script': _VS, 'concept': 'WA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(20, 34), (26, 26), (32, 34), (38, 26), (44, 34)],   # wave top
            [(32, 34), (32, 48)],                                   # tail
        ],
    },
    # Ya – like a Y
    {
        'name': 'YA', 'script': _VS, 'concept': 'YA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 22), (32, 36)],                              # left arm
            [(42, 22), (32, 36)],                              # right arm
            [(32, 36), (32, 48)],                              # stem
        ],
    },
    # Za – zigzag shape
    {
        'name': 'ZA', 'script': _VS, 'concept': 'ZA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 22), (42, 22), (22, 48), (42, 48)],         # zigzag Z
        ],
    },
    # Mba – M-like with a bump
    {
        'name': 'MBA', 'script': _VS, 'concept': 'MBA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(20, 48), (20, 22), (28, 38), (36, 22), (44, 38)],   # M shape
            [(44, 38), (44, 48)],                                   # right leg
        ],
    },
    # Nda – arch + vertical
    {
        'name': 'NDA', 'script': _VS, 'concept': 'NDA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 48), (22, 28), (32, 22), (42, 28), (42, 48)],   # arch shape
            [(22, 48), (42, 48)],                                   # base bar
        ],
    },
    # Nga – circle on top of vertical
    {
        'name': 'NGA', 'script': _VS, 'concept': 'NGA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(28, 22), (24, 26), (28, 30), (36, 30), (40, 26), (36, 22), (28, 22)],  # head circle
            [(32, 30), (32, 48)],                              # stem
        ],
    },
    # Gba – like G with bar
    {
        'name': 'GBA', 'script': _VS, 'concept': 'GBA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(42, 24), (36, 22), (26, 22), (22, 28), (22, 40), (26, 48), (36, 48), (42, 42)],
            [(30, 36), (42, 36)],                              # inward bar
        ],
    },
    # Kpa – K-like with loop
    {
        'name': 'KPA', 'script': _VS, 'concept': 'KPA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(24, 22), (24, 48)],                              # vertical
            [(42, 22), (24, 36)],                              # upper arm
            [(28, 34), (42, 48)],                              # lower arm
            [(34, 26), (40, 24), (42, 28), (38, 30)],         # small loop
        ],
    },
    # Nya – curvy n with tail
    {
        'name': 'NYA', 'script': _VS, 'concept': 'NYA',
        'origin': _VO, 'ink': _VI, 'paper': _VPa,
        'strokes': [
            [(22, 48), (22, 28), (28, 22), (36, 22), (42, 28), (42, 42)],  # arch
            [(42, 42), (38, 48), (32, 50)],                                  # tail curl
        ],
    },
]

# ═══════════════════════════════════════════════════════════════
# 5. LINEAR B  –  20 key syllabic signs (Mycenaean Greek)
# ═══════════════════════════════════════════════════════════════
_LBI = _LINEAR_B_INK
_LBP = _LINEAR_B_PAPER
_LBO = 'MYCENAE ~1450 BC'
_LBs = 'LINEAR_B'

LINEAR_B_CHARS = [
    # A (AB 08) – cross / asterisk like shape
    {
        'name': 'A', 'script': _LBs, 'concept': 'A',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 22), (32, 48)],                              # vertical
            [(20, 35), (44, 35)],                              # horizontal
            [(24, 24), (40, 46)],                              # diagonal
        ],
    },
    # E (AB 38) – arrow pointing right
    {
        'name': 'E', 'script': _LBs, 'concept': 'E',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(20, 35), (44, 35)],                              # horizontal shaft
            [(34, 24), (44, 35), (34, 46)],                    # arrowhead
        ],
    },
    # I (AB 28) – vertical with ticks
    {
        'name': 'I', 'script': _LBs, 'concept': 'I',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 22), (32, 48)],                              # vertical
            [(24, 28), (32, 28)],                              # tick left
            [(24, 42), (32, 42)],                              # tick left lower
        ],
    },
    # O (AB 61) – diamond shape
    {
        'name': 'O', 'script': _LBs, 'concept': 'O',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 22), (44, 35), (32, 48), (20, 35), (32, 22)],   # diamond
        ],
    },
    # U (AB 10) – gate / pi shape
    {
        'name': 'U', 'script': _LBs, 'concept': 'U',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(22, 22), (42, 22)],                              # top bar
            [(22, 22), (22, 48)],                              # left leg
            [(42, 22), (42, 48)],                              # right leg
        ],
    },
    # Da (AB 01) – stick figure sitting
    {
        'name': 'DA', 'script': _LBs, 'concept': 'DA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 22), (32, 40)],                              # body
            [(22, 48), (32, 40), (42, 48)],                    # legs
            [(24, 30), (40, 30)],                              # arms
        ],
    },
    # Ka (AB 77) – trident
    {
        'name': 'KA', 'script': _LBs, 'concept': 'KA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 22), (32, 48)],                              # center prong
            [(22, 22), (22, 34)],                              # left prong
            [(42, 22), (42, 34)],                              # right prong
            [(22, 34), (42, 34)],                              # crossbar
        ],
    },
    # Ma (AB 80) – double cross
    {
        'name': 'MA', 'script': _LBs, 'concept': 'MA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(20, 22), (44, 48)],                              # diagonal 1
            [(44, 22), (20, 48)],                              # diagonal 2
            [(20, 35), (44, 35)],                              # horizontal
        ],
    },
    # Na (AB 06) – upside-down T with arms
    {
        'name': 'NA', 'script': _LBs, 'concept': 'NA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 22), (32, 48)],                              # vertical
            [(20, 48), (44, 48)],                              # base bar
            [(22, 30), (42, 30)],                              # arms
        ],
    },
    # Pa (AB 03) – eye shape
    {
        'name': 'PA', 'script': _LBs, 'concept': 'PA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(20, 35), (32, 22), (44, 35), (32, 48), (20, 35)],   # diamond/eye
            [(20, 35), (44, 35)],                                   # horizontal pupil
        ],
    },
    # Ra (AB 60) – branching Y
    {
        'name': 'RA', 'script': _LBs, 'concept': 'RA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 48), (32, 34)],                              # stem
            [(32, 34), (22, 22)],                              # left branch
            [(32, 34), (42, 22)],                              # right branch
        ],
    },
    # Sa (AB 31) – angular S / zigzag
    {
        'name': 'SA', 'script': _LBs, 'concept': 'SA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(22, 22), (42, 22), (22, 35), (42, 48)],         # zigzag
        ],
    },
    # Ta (AB 59) – cross in a box
    {
        'name': 'TA', 'script': _LBs, 'concept': 'TA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(22, 22), (42, 22), (42, 48), (22, 48), (22, 22)],  # box
            [(22, 22), (42, 48)],                                  # diagonal
        ],
    },
    # Wa (AB 54) – W-shape
    {
        'name': 'WA', 'script': _LBs, 'concept': 'WA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(20, 22), (26, 48), (32, 30), (38, 48), (44, 22)],
        ],
    },
    # Ja (AB 57) – pronged fork
    {
        'name': 'JA', 'script': _LBs, 'concept': 'JA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 48), (32, 28)],                              # handle
            [(22, 22), (32, 28)],                              # left tine
            [(42, 22), (32, 28)],                              # right tine
        ],
    },
    # Qa (AB 16) – hourglass
    {
        'name': 'QA', 'script': _LBs, 'concept': 'QA',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(22, 22), (42, 22)],                              # top bar
            [(22, 22), (42, 48)],                              # cross 1
            [(42, 22), (22, 48)],                              # cross 2
            [(22, 48), (42, 48)],                              # bottom bar
        ],
    },
    # Ro (AB 02) – circle with stem
    {
        'name': 'RO', 'script': _LBs, 'concept': 'RO',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(28, 22), (22, 28), (22, 36), (28, 40), (36, 40), (42, 36), (42, 28), (36, 22), (28, 22)],
            [(32, 40), (32, 48)],                              # stem
        ],
    },
    # Ko (AB 70) – triangle with line
    {
        'name': 'KO', 'script': _LBs, 'concept': 'KO',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(32, 22), (20, 48), (44, 48), (32, 22)],         # triangle
            [(26, 35), (38, 35)],                              # inner bar
        ],
    },
    # No (AB 52) – T shape with feet
    {
        'name': 'NO', 'script': _LBs, 'concept': 'NO',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(20, 22), (44, 22)],                              # top bar
            [(32, 22), (32, 48)],                              # vertical
            [(24, 48), (40, 48)],                              # foot bar
        ],
    },
    # To (AB 05) – double triangle / bowtie
    {
        'name': 'TO', 'script': _LBs, 'concept': 'TO',
        'origin': _LBO, 'ink': _LBI, 'paper': _LBP, 'thick': True,
        'strokes': [
            [(20, 22), (44, 35), (20, 48)],                   # left triangle
            [(44, 22), (20, 35), (44, 48)],                    # right triangle
        ],
    },
]

# ═══════════════════════════════════════════════════════════════
# 6. RONGORONGO  –  15 key glyphs (Easter Island, undeciphered)
# ═══════════════════════════════════════════════════════════════
_RI = _RONGO_INK
_RPa = _RONGO_PAPER
_RO = 'RAPA NUI ~1700 AD'
_RS = 'RONGORONGO'

RONGORONGO_CHARS = [
    # BIRDMAN – iconic birdman figure (tangata manu)
    {
        'name': 'BIRDMAN', 'script': _RS, 'concept': 'BIRDMAN',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(28, 22), (24, 24), (24, 28), (28, 30), (36, 30), (40, 28), (40, 24), (36, 22), (28, 22)],  # head
            [(32, 30), (32, 42)],                              # body
            [(22, 36), (32, 32), (42, 36)],                    # wings
            [(28, 42), (24, 48)],                              # left leg
            [(36, 42), (40, 48)],                              # right leg
            [(40, 24), (46, 22)],                              # beak
        ],
    },
    # FISH – stylized fish
    {
        'name': 'FISH', 'script': _RS, 'concept': 'FISH',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(20, 35), (28, 28), (38, 28), (44, 32), (44, 38), (38, 42), (28, 42), (20, 35)],  # body
            [(44, 32), (46, 26), (44, 35), (46, 44), (44, 38)],  # tail
            [(30, 34), (32, 36)],                              # eye
        ],
    },
    # TURTLE – sea turtle from above
    {
        'name': 'TURTLE', 'script': _RS, 'concept': 'TURTLE',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(26, 28), (22, 34), (26, 42), (38, 42), (42, 34), (38, 28), (26, 28)],  # shell
            [(32, 28), (32, 22)],                              # head
            [(22, 30), (18, 26)],                              # front-left flipper
            [(42, 30), (46, 26)],                              # front-right flipper
            [(24, 42), (20, 48)],                              # back-left flipper
            [(40, 42), (44, 48)],                              # back-right flipper
        ],
    },
    # FRIGATE BIRD – soaring bird shape
    {
        'name': 'FRIGATE_BIRD', 'script': _RS, 'concept': 'FRIGATE BIRD',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(18, 30), (24, 26), (32, 24), (40, 26), (46, 30)],   # wings spread
            [(32, 24), (32, 44)],                              # body
            [(30, 44), (32, 48), (34, 44)],                    # tail fork
            [(32, 24), (36, 22), (38, 24)],                    # head + beak
        ],
    },
    # SEATED FIGURE – person sitting cross-legged
    {
        'name': 'SEATED_FIGURE', 'script': _RS, 'concept': 'SEATED FIGURE',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(30, 22), (34, 22), (34, 26), (30, 26), (30, 22)],   # head
            [(32, 26), (32, 40)],                              # torso
            [(24, 32), (32, 34), (40, 32)],                    # arms
            [(32, 40), (22, 48), (42, 48), (32, 40)],         # crossed legs
        ],
    },
    # STANDING FIGURE – upright person with raised arms
    {
        'name': 'STANDING_FIGURE', 'script': _RS, 'concept': 'STANDING FIGURE',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(30, 22), (34, 22), (34, 26), (30, 26), (30, 22)],   # head
            [(32, 26), (32, 42)],                              # torso
            [(32, 30), (22, 22)],                              # left arm up
            [(32, 30), (42, 22)],                              # right arm up
            [(32, 42), (26, 50)],                              # left leg
            [(32, 42), (38, 50)],                              # right leg
        ],
    },
    # CRESCENT – crescent moon shape
    {
        'name': 'CRESCENT', 'script': _RS, 'concept': 'CRESCENT',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(36, 22), (26, 26), (22, 34), (26, 44), (36, 48)],   # outer curve
            [(36, 22), (32, 28), (30, 34), (32, 42), (36, 48)],   # inner curve
        ],
    },
    # VULVA – fertility symbol, oval with line
    {
        'name': 'VULVA', 'script': _RS, 'concept': 'FERTILITY',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(32, 22), (24, 28), (22, 36), (26, 44), (32, 48),
             (38, 44), (42, 36), (40, 28), (32, 22)],             # oval
            [(32, 24), (32, 46)],                                   # center line
        ],
    },
    # PLANT – stylized growing plant / tree
    {
        'name': 'PLANT', 'script': _RS, 'concept': 'PLANT',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(32, 50), (32, 22)],                              # stem
            [(32, 28), (22, 22)],                              # left branch top
            [(32, 28), (42, 22)],                              # right branch top
            [(32, 36), (24, 30)],                              # left branch mid
            [(32, 36), (40, 30)],                              # right branch mid
        ],
    },
    # EAR – stylized ear shape
    {
        'name': 'EAR', 'script': _RS, 'concept': 'EAR / HEARING',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(36, 22), (28, 24), (24, 30), (24, 40), (28, 46), (36, 48)],  # outer ear
            [(36, 28), (30, 30), (28, 36), (30, 40), (36, 42)],             # inner ear
            [(36, 36), (42, 36)],                                             # canal
        ],
    },
    # HAND – open palm with fingers
    {
        'name': 'HAND', 'script': _RS, 'concept': 'HAND',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(22, 36), (42, 36), (42, 48), (22, 48), (22, 36)],   # palm
            [(24, 36), (22, 24)],                                   # thumb
            [(28, 36), (28, 22)],                                   # index
            [(32, 36), (32, 20)],                                   # middle
            [(36, 36), (36, 22)],                                   # ring
            [(40, 36), (42, 26)],                                   # pinky
        ],
    },
    # DOUBLE HOOK – interlocking hooks / spirals
    {
        'name': 'DOUBLE_HOOK', 'script': _RS, 'concept': 'DOUBLE HOOK',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(22, 22), (22, 36), (32, 36), (32, 28), (26, 28)],   # left hook
            [(42, 48), (42, 34), (32, 34), (32, 42), (38, 42)],   # right hook (inverted)
        ],
    },
    # PADDLE – ceremonial paddle / oar shape
    {
        'name': 'PADDLE', 'script': _RS, 'concept': 'PADDLE / OAR',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(32, 48), (32, 32)],                              # handle
            [(32, 32), (24, 28), (22, 22), (32, 20), (42, 22), (40, 28), (32, 32)],  # blade
        ],
    },
    # SUN – radiant circle
    {
        'name': 'SUN', 'script': _RS, 'concept': 'SUN',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(28, 30), (24, 34), (28, 40), (36, 40), (40, 34), (36, 30), (28, 30)],  # center circle
            [(32, 30), (32, 22)],                              # ray up
            [(32, 40), (32, 48)],                              # ray down
            [(24, 34), (18, 34)],                              # ray left
            [(40, 34), (46, 34)],                              # ray right
        ],
    },
    # MOAI – iconic Easter Island head
    {
        'name': 'MOAI', 'script': _RS, 'concept': 'MOAI / ANCESTOR',
        'origin': _RO, 'ink': _RI, 'paper': _RPa, 'thick': True,
        'strokes': [
            [(26, 20), (38, 20), (40, 24), (40, 44), (36, 48), (28, 48), (24, 44), (24, 24), (26, 20)],  # head outline
            [(28, 30), (30, 30)],                              # left eye
            [(34, 30), (36, 30)],                              # right eye
            [(26, 36), (24, 38), (26, 40), (38, 40), (40, 38), (38, 36)],  # nose + brow ridge
            [(30, 44), (34, 44)],                              # mouth
        ],
    },
]

# ── Verification ────────────────────────────────────────────────
if __name__ == '__main__':
    all_sets = [('LATIN', LATIN_CHARS), ('BRAILLE', BRAILLE_CHARS), ('BAYBAYIN', BAYBAYIN_CHARS),
                ('VAI', VAI_CHARS), ('LINEAR_B', LINEAR_B_CHARS), ('RONGORONGO', RONGORONGO_CHARS)]
    for name, chars in all_sets:
        print(f'{name}: {len(chars)} chars')
        for ch in chars:
            for si, stroke in enumerate(ch['strokes']):
                for x, y in stroke:
                    assert 8 <= x <= 56 and 14 <= y <= 56, f"OOB: {ch['name']} stroke {si} ({x},{y})"
    print('All OK')

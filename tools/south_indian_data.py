"""
Generated stroke data for South Indian scripts: Telugu, Kannada, Malayalam.
Copy these into the CHARACTERS list in visuals/scripts.py.

Stroke zone: x=18-46, y=20-50 within paper area x=10-54, y=14-56.
"""

# ── Color constants ──────────────────────────────────────────────────────────

_TELUGU_INK = (30, 60, 130)
_TELUGU_PAPER = (230, 225, 210)

_KANNADA_INK = (140, 40, 20)
_KANNADA_PAPER = (228, 222, 205)

_MALAYALAM_INK = (20, 50, 20)
_MALAYALAM_PAPER = (225, 225, 210)

# ═══════════════════════════════════════════════════════════════════════════════
#  TELUGU  (~80M speakers, Andhra Pradesh / Telangana)
#  Very rounded, curvy letterforms with loops and hooks.
# ═══════════════════════════════════════════════════════════════════════════════

TELUGU_CHARS = [
    # ── Vowels (14) ──────────────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'TELUGU', 'concept': 'A',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(28, 22), (24, 28), (22, 35), (24, 42), (30, 46), (36, 42), (38, 35), (36, 28), (28, 22)],
            [(38, 35), (42, 30), (44, 24)],
        ],
    },
    {
        'name': 'Aa', 'script': 'TELUGU', 'concept': 'AA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(26, 22), (22, 28), (20, 35), (22, 42), (28, 46), (34, 42), (36, 35), (34, 28), (26, 22)],
            [(36, 35), (40, 30), (42, 24)],
            [(42, 24), (44, 30), (44, 38), (42, 44)],
        ],
    },
    {
        'name': 'I', 'script': 'TELUGU', 'concept': 'I',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 24), (22, 30), (24, 36), (30, 38), (36, 36), (38, 30), (36, 24), (30, 22), (24, 24)],
            [(30, 38), (28, 44), (30, 48), (34, 46)],
        ],
    },
    {
        'name': 'Ii', 'script': 'TELUGU', 'concept': 'II',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 24), (22, 30), (24, 36), (30, 38), (36, 36), (38, 30), (36, 24), (30, 22), (24, 24)],
            [(30, 38), (28, 44), (30, 48), (34, 46)],
            [(38, 22), (42, 26), (40, 32)],
        ],
    },
    {
        'name': 'U', 'script': 'TELUGU', 'concept': 'U',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 28), (26, 22), (32, 22), (36, 28), (34, 34), (28, 36), (24, 34), (22, 28)],
            [(28, 36), (30, 42), (34, 46), (38, 44)],
        ],
    },
    {
        'name': 'Uu', 'script': 'TELUGU', 'concept': 'UU',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 28), (26, 22), (32, 22), (36, 28), (34, 34), (28, 36), (24, 34), (22, 28)],
            [(28, 36), (30, 42), (34, 48), (40, 46), (42, 40)],
        ],
    },
    {
        'name': 'E', 'script': 'TELUGU', 'concept': 'E',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 34), (24, 26), (30, 22), (36, 26), (38, 34), (34, 40), (28, 42), (24, 38)],
            [(34, 40), (38, 46), (42, 48)],
        ],
    },
    {
        'name': 'Ee', 'script': 'TELUGU', 'concept': 'EE',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 34), (24, 26), (30, 22), (36, 26), (38, 34), (34, 40), (28, 42), (24, 38)],
            [(34, 40), (38, 46), (42, 48)],
            [(40, 22), (44, 28), (42, 34)],
        ],
    },
    {
        'name': 'Ai', 'script': 'TELUGU', 'concept': 'AI',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 34), (24, 26), (30, 22), (36, 26), (38, 34), (34, 40), (28, 42)],
            [(28, 42), (32, 48), (38, 48), (42, 44)],
            [(24, 20), (20, 24)],
        ],
    },
    {
        'name': 'O', 'script': 'TELUGU', 'concept': 'O',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (20, 36), (24, 42), (30, 44), (36, 42), (38, 36), (36, 28), (28, 22)],
            [(30, 44), (32, 48), (36, 50)],
        ],
    },
    {
        'name': 'Oo', 'script': 'TELUGU', 'concept': 'OO',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (20, 36), (24, 42), (30, 44), (36, 42), (38, 36), (36, 28), (28, 22)],
            [(30, 44), (32, 48), (36, 50)],
            [(40, 22), (44, 28), (42, 36)],
        ],
    },
    {
        'name': 'Au', 'script': 'TELUGU', 'concept': 'AU',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (30, 40), (36, 38), (38, 30), (34, 24), (26, 24)],
            [(30, 40), (28, 46), (32, 50), (38, 48)],
            [(40, 22), (44, 26), (44, 34), (40, 38)],
        ],
    },
    {
        'name': 'Am', 'script': 'TELUGU', 'concept': 'AM',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(28, 24), (24, 30), (26, 38), (32, 40), (38, 36), (36, 28), (28, 24)],
            [(34, 20), (38, 20)],
        ],
    },
    {
        'name': 'Aha', 'script': 'TELUGU', 'concept': 'AHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(26, 24), (22, 32), (26, 40), (34, 42), (40, 38), (42, 30), (38, 24), (26, 24)],
            [(34, 42), (32, 48), (36, 50)],
        ],
    },
    # ── Consonants (36) ──────────────────────────────────────────────────────
    {
        'name': 'Ka', 'script': 'TELUGU', 'concept': 'KA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 22), (20, 30), (22, 38), (28, 42), (34, 40), (38, 34), (36, 26), (30, 22), (24, 22)],
            [(28, 42), (26, 48), (30, 50), (36, 48)],
        ],
    },
    {
        'name': 'Kha', 'script': 'TELUGU', 'concept': 'KHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 22), (20, 30), (22, 38), (28, 40), (34, 38), (36, 30), (32, 24), (24, 22)],
            [(34, 38), (38, 44), (42, 48)],
            [(42, 22), (44, 28), (42, 34)],
        ],
    },
    {
        'name': 'Ga', 'script': 'TELUGU', 'concept': 'GA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(32, 22), (26, 24), (22, 30), (24, 38), (30, 42), (36, 40), (40, 34)],
            [(40, 34), (42, 28), (40, 22), (36, 20)],
            [(30, 42), (28, 48), (32, 50)],
        ],
    },
    {
        'name': 'Gha', 'script': 'TELUGU', 'concept': 'GHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(30, 22), (24, 26), (20, 34), (24, 42), (32, 44), (38, 40), (40, 32), (36, 26), (30, 22)],
            [(32, 44), (30, 48), (34, 50)],
            [(40, 32), (44, 28), (44, 22)],
        ],
    },
    {
        'name': 'Nga', 'script': 'TELUGU', 'concept': 'NGA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 30), (26, 22), (34, 22), (38, 30), (34, 38), (26, 38), (22, 30)],
            [(30, 38), (30, 46), (34, 50)],
        ],
    },
    {
        'name': 'Cha', 'script': 'TELUGU', 'concept': 'CHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 28), (24, 22), (32, 20), (38, 24), (40, 32), (36, 38), (28, 40), (22, 36)],
            [(28, 40), (30, 46), (36, 50), (40, 46)],
        ],
    },
    {
        'name': 'Chha', 'script': 'TELUGU', 'concept': 'CHHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 28), (24, 22), (32, 20), (38, 24), (40, 32), (36, 38), (28, 38)],
            [(28, 38), (26, 44), (30, 48), (36, 46)],
            [(40, 32), (44, 36), (44, 42)],
        ],
    },
    {
        'name': 'Ja', 'script': 'TELUGU', 'concept': 'JA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 26), (26, 20), (34, 20), (38, 26), (36, 34), (30, 38)],
            [(30, 38), (24, 36), (20, 30)],
            [(30, 38), (32, 44), (28, 50)],
        ],
    },
    {
        'name': 'Jha', 'script': 'TELUGU', 'concept': 'JHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 24), (28, 20), (36, 22), (40, 28), (38, 36), (30, 40), (24, 36), (22, 28)],
            [(30, 40), (34, 46), (40, 48)],
        ],
    },
    {
        'name': 'Nya', 'script': 'TELUGU', 'concept': 'NYA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 30), (24, 22), (32, 22), (36, 30), (32, 36), (24, 36), (20, 30)],
            [(36, 30), (42, 26), (44, 32), (40, 38)],
            [(30, 36), (28, 44), (32, 48)],
        ],
    },
    {
        'name': 'Ta_retro', 'script': 'TELUGU', 'concept': 'TA_RETRO',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 22), (20, 30), (24, 38), (32, 40), (38, 36), (40, 28), (36, 22), (28, 20)],
            [(32, 40), (34, 46), (30, 50)],
        ],
    },
    {
        'name': 'Tha_retro', 'script': 'TELUGU', 'concept': 'THA_RETRO',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(26, 22), (20, 28), (22, 36), (28, 40), (36, 38), (40, 30), (36, 24), (26, 22)],
            [(28, 40), (26, 46), (30, 50), (36, 48)],
        ],
    },
    {
        'name': 'Da_retro', 'script': 'TELUGU', 'concept': 'DA_RETRO',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(30, 22), (24, 26), (22, 34), (26, 42), (34, 44), (40, 40), (42, 32), (38, 24), (30, 22)],
            [(34, 44), (32, 50)],
        ],
    },
    {
        'name': 'Dha_retro', 'script': 'TELUGU', 'concept': 'DHA_RETRO',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (20, 36), (24, 42), (32, 44), (38, 40), (40, 32), (36, 24), (28, 22)],
            [(32, 44), (30, 50)],
            [(42, 22), (44, 30)],
        ],
    },
    {
        'name': 'Na_retro', 'script': 'TELUGU', 'concept': 'NA_RETRO',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 26), (28, 20), (36, 22), (40, 30), (36, 38), (28, 40), (22, 34)],
            [(28, 40), (30, 48), (36, 50), (40, 46)],
        ],
    },
    {
        'name': 'Ta', 'script': 'TELUGU', 'concept': 'TA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 30), (26, 22), (34, 22), (40, 28), (38, 36), (30, 40), (24, 36), (20, 30)],
            [(30, 40), (32, 46), (28, 50)],
        ],
    },
    {
        'name': 'Tha', 'script': 'TELUGU', 'concept': 'THA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 28), (28, 22), (36, 22), (42, 28), (40, 36), (32, 40), (24, 38), (22, 28)],
            [(32, 40), (34, 46), (38, 50)],
        ],
    },
    {
        'name': 'Da', 'script': 'TELUGU', 'concept': 'DA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(32, 20), (24, 24), (20, 32), (24, 40), (32, 42), (40, 38), (42, 30), (38, 22), (32, 20)],
            [(32, 42), (30, 48), (34, 50)],
        ],
    },
    {
        'name': 'Dha', 'script': 'TELUGU', 'concept': 'DHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(30, 20), (22, 26), (20, 34), (24, 42), (34, 44), (42, 38), (44, 30), (40, 22), (30, 20)],
            [(34, 44), (32, 50)],
        ],
    },
    {
        'name': 'Na', 'script': 'TELUGU', 'concept': 'NA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 24), (20, 32), (22, 40), (28, 44), (36, 42), (40, 36), (38, 28), (32, 22), (24, 24)],
            [(28, 44), (26, 50)],
        ],
    },
    {
        'name': 'Pa', 'script': 'TELUGU', 'concept': 'PA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 26), (28, 20), (36, 22), (40, 30), (36, 38), (28, 38)],
            [(28, 38), (22, 34), (20, 28)],
            [(30, 38), (30, 46), (34, 50)],
        ],
    },
    {
        'name': 'Pha', 'script': 'TELUGU', 'concept': 'PHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 24), (20, 32), (24, 40), (32, 42), (38, 38), (40, 30), (36, 22), (28, 20), (24, 24)],
            [(32, 42), (36, 48), (42, 48)],
        ],
    },
    {
        'name': 'Ba', 'script': 'TELUGU', 'concept': 'BA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(30, 22), (22, 26), (20, 34), (24, 40), (32, 42), (38, 38), (40, 30), (36, 22), (30, 22)],
            [(24, 40), (22, 46), (26, 50)],
        ],
    },
    {
        'name': 'Bha', 'script': 'TELUGU', 'concept': 'BHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 36), (28, 42), (36, 42), (40, 36), (40, 28), (34, 22), (28, 22)],
            [(28, 42), (26, 48), (30, 50)],
            [(40, 28), (44, 24)],
        ],
    },
    {
        'name': 'Ma', 'script': 'TELUGU', 'concept': 'MA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 32), (26, 24), (34, 22), (40, 28), (38, 36), (30, 40), (22, 38), (20, 32)],
            [(30, 40), (34, 46), (30, 50)],
        ],
    },
    {
        'name': 'Ya', 'script': 'TELUGU', 'concept': 'YA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 26), (26, 20), (34, 22), (38, 28)],
            [(38, 28), (36, 36), (30, 42), (24, 40), (20, 34)],
            [(30, 42), (34, 48), (40, 48)],
        ],
    },
    {
        'name': 'Ra', 'script': 'TELUGU', 'concept': 'RA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 24), (28, 20), (36, 22), (40, 30), (36, 38), (28, 40), (22, 36), (22, 24)],
            [(28, 40), (32, 46), (28, 50)],
        ],
    },
    {
        'name': 'La', 'script': 'TELUGU', 'concept': 'LA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(26, 20), (20, 28), (22, 36), (30, 40), (38, 36), (40, 28), (34, 22), (26, 20)],
            [(30, 40), (28, 48)],
        ],
    },
    {
        'name': 'Va', 'script': 'TELUGU', 'concept': 'VA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(22, 30), (28, 22), (36, 22), (42, 28), (40, 36), (34, 42), (26, 40), (22, 34)],
            [(34, 42), (38, 48), (42, 46)],
        ],
    },
    {
        'name': 'Sha', 'script': 'TELUGU', 'concept': 'SHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 28), (26, 22), (34, 20), (40, 26), (42, 34)],
            [(42, 34), (38, 40), (30, 42), (24, 38), (20, 32)],
            [(30, 42), (32, 48)],
        ],
    },
    {
        'name': 'Sha_retro', 'script': 'TELUGU', 'concept': 'SHA_RETRO',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 24), (20, 32), (24, 40), (32, 42), (40, 38), (42, 30), (38, 22), (30, 20), (24, 24)],
            [(32, 42), (30, 48), (34, 50)],
        ],
    },
    {
        'name': 'Sa', 'script': 'TELUGU', 'concept': 'SA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 30), (24, 22), (34, 20), (40, 26), (38, 34), (30, 38), (24, 34), (20, 30)],
            [(30, 38), (34, 44), (30, 50)],
        ],
    },
    {
        'name': 'Ha', 'script': 'TELUGU', 'concept': 'HA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (20, 36), (26, 42), (34, 42), (40, 36), (42, 28), (36, 22), (28, 22)],
            [(30, 42), (30, 48)],
        ],
    },
    {
        'name': 'Lla', 'script': 'TELUGU', 'concept': 'LLA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 22), (20, 30), (22, 38), (30, 42), (38, 38), (42, 30), (38, 22), (30, 20), (24, 22)],
            [(30, 42), (32, 48), (28, 50)],
        ],
    },
    {
        'name': 'Ksha', 'script': 'TELUGU', 'concept': 'KSHA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(20, 28), (24, 22), (30, 22), (34, 28), (30, 34), (24, 34), (20, 28)],
            [(34, 28), (40, 24), (44, 28), (42, 36), (36, 38)],
            [(30, 38), (30, 46), (34, 50)],
        ],
    },
    {
        'name': 'Rra', 'script': 'TELUGU', 'concept': 'RRA',
        'origin': 'TELUGU ~1100 AD',
        'ink': _TELUGU_INK, 'paper': _TELUGU_PAPER,
        'strokes': [
            [(24, 24), (20, 32), (24, 40), (32, 44), (40, 40), (44, 32), (40, 24), (32, 20), (24, 24)],
            [(32, 44), (30, 50)],
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
#  KANNADA  (~45M speakers, Karnataka)
#  Rounded shapes with characteristic head-marks and vertical strokes.
# ═══════════════════════════════════════════════════════════════════════════════

KANNADA_CHARS = [
    # ── Vowels (14) ──────────────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'KANNADA', 'concept': 'A',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 44)],
            [(22, 22), (34, 22), (40, 28), (40, 36), (34, 42), (22, 44)],
        ],
    },
    {
        'name': 'Aa', 'script': 'KANNADA', 'concept': 'AA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(20, 22), (20, 44)],
            [(20, 22), (32, 22), (38, 28), (38, 36), (32, 42), (20, 44)],
            [(38, 28), (44, 24), (44, 36), (38, 40)],
        ],
    },
    {
        'name': 'I', 'script': 'KANNADA', 'concept': 'I',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (22, 30), (26, 38), (32, 40), (38, 36), (40, 28), (36, 22), (28, 20)],
            [(32, 40), (34, 46), (30, 50)],
        ],
    },
    {
        'name': 'Ii', 'script': 'KANNADA', 'concept': 'II',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (22, 30), (26, 38), (32, 40), (38, 36), (40, 28), (36, 22), (28, 20)],
            [(32, 40), (34, 46), (30, 50)],
            [(42, 22), (44, 28)],
        ],
    },
    {
        'name': 'U', 'script': 'KANNADA', 'concept': 'U',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 24), (22, 32), (26, 40), (34, 42), (40, 38), (42, 30), (38, 22), (30, 20), (24, 24)],
        ],
    },
    {
        'name': 'Uu', 'script': 'KANNADA', 'concept': 'UU',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 24), (22, 32), (26, 40), (34, 42), (40, 38), (42, 30), (38, 22), (30, 20), (24, 24)],
            [(34, 42), (36, 48), (32, 50)],
        ],
    },
    {
        'name': 'E', 'script': 'KANNADA', 'concept': 'E',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(20, 22), (20, 42)],
            [(20, 22), (30, 22), (36, 26), (36, 32), (30, 36), (20, 36)],
            [(36, 32), (42, 34), (44, 40)],
        ],
    },
    {
        'name': 'Ee', 'script': 'KANNADA', 'concept': 'EE',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(20, 22), (20, 42)],
            [(20, 22), (30, 22), (36, 26), (36, 32), (30, 36), (20, 36)],
            [(36, 32), (42, 34), (44, 40), (42, 46)],
        ],
    },
    {
        'name': 'Ai', 'script': 'KANNADA', 'concept': 'AI',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(20, 24), (20, 44)],
            [(20, 24), (28, 22), (34, 26), (34, 34), (28, 38), (20, 38)],
            [(34, 26), (40, 22), (44, 26), (42, 34)],
        ],
    },
    {
        'name': 'O', 'script': 'KANNADA', 'concept': 'O',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 44)],
            [(22, 22), (32, 22), (38, 28), (38, 36), (32, 42), (22, 44)],
            [(30, 20), (34, 20)],
        ],
    },
    {
        'name': 'Oo', 'script': 'KANNADA', 'concept': 'OO',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 44)],
            [(22, 22), (32, 22), (38, 28), (38, 36), (32, 42), (22, 44)],
            [(28, 20), (34, 20), (38, 20)],
        ],
    },
    {
        'name': 'Au', 'script': 'KANNADA', 'concept': 'AU',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 24), (22, 44)],
            [(22, 24), (32, 24), (38, 30), (38, 38), (32, 42), (22, 44)],
            [(38, 30), (44, 28), (44, 38), (40, 44)],
        ],
    },
    {
        'name': 'Am', 'script': 'KANNADA', 'concept': 'AM',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 42)],
            [(22, 22), (32, 22), (38, 28), (38, 36), (32, 42), (22, 42)],
            [(30, 20), (32, 20)],
        ],
    },
    {
        'name': 'Aha', 'script': 'KANNADA', 'concept': 'AHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 24), (22, 46)],
            [(22, 24), (34, 24), (40, 30), (40, 38), (34, 44), (22, 46)],
        ],
    },
    # ── Consonants (36) ──────────────────────────────────────────────────────
    {
        'name': 'Ka', 'script': 'KANNADA', 'concept': 'KA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 46)],
            [(22, 28), (30, 22), (38, 24), (42, 30), (38, 36), (30, 38), (22, 36)],
            [(30, 38), (34, 44), (30, 50)],
        ],
    },
    {
        'name': 'Kha', 'script': 'KANNADA', 'concept': 'KHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 44)],
            [(22, 28), (30, 22), (38, 26), (40, 34), (36, 40), (28, 42)],
            [(40, 34), (44, 38), (44, 44)],
        ],
    },
    {
        'name': 'Ga', 'script': 'KANNADA', 'concept': 'GA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 22), (34, 22), (40, 28), (38, 36), (30, 40), (24, 38)],
        ],
    },
    {
        'name': 'Gha', 'script': 'KANNADA', 'concept': 'GHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 46)],
            [(22, 22), (32, 22), (40, 28), (38, 38), (30, 42), (22, 40)],
            [(40, 28), (44, 24), (46, 30)],
        ],
    },
    {
        'name': 'Nga', 'script': 'KANNADA', 'concept': 'NGA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 26), (28, 20), (36, 22), (40, 30), (36, 38), (28, 40), (22, 34)],
            [(28, 40), (32, 46), (28, 50)],
        ],
    },
    {
        'name': 'Cha', 'script': 'KANNADA', 'concept': 'CHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 30), (32, 24), (38, 28), (40, 36), (36, 42), (28, 44), (24, 40)],
        ],
    },
    {
        'name': 'Chha', 'script': 'KANNADA', 'concept': 'CHHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 46)],
            [(22, 28), (30, 22), (38, 26), (40, 34), (34, 40), (22, 42)],
            [(40, 34), (44, 40), (42, 46)],
        ],
    },
    {
        'name': 'Ja', 'script': 'KANNADA', 'concept': 'JA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(20, 22), (20, 46)],
            [(20, 26), (28, 20), (36, 24), (38, 32), (34, 38), (26, 40), (20, 36)],
            [(34, 38), (38, 44), (36, 50)],
        ],
    },
    {
        'name': 'Jha', 'script': 'KANNADA', 'concept': 'JHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 26), (32, 22), (40, 28), (40, 38), (34, 44), (22, 44)],
        ],
    },
    {
        'name': 'Nya', 'script': 'KANNADA', 'concept': 'NYA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 46)],
            [(24, 28), (32, 22), (40, 26), (42, 34), (38, 40), (28, 42)],
            [(38, 40), (42, 46), (40, 50)],
        ],
    },
    {
        'name': 'Ta_retro', 'script': 'KANNADA', 'concept': 'TA_RETRO',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 28), (30, 22), (38, 26), (38, 36), (30, 42), (22, 40)],
        ],
    },
    {
        'name': 'Tha_retro', 'script': 'KANNADA', 'concept': 'THA_RETRO',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 46)],
            [(24, 26), (32, 20), (40, 24), (42, 32), (38, 40), (28, 44), (24, 40)],
        ],
    },
    {
        'name': 'Da_retro', 'script': 'KANNADA', 'concept': 'DA_RETRO',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 24), (22, 48)],
            [(22, 30), (30, 24), (38, 28), (40, 36), (36, 42), (26, 44)],
            [(36, 42), (40, 48)],
        ],
    },
    {
        'name': 'Dha_retro', 'script': 'KANNADA', 'concept': 'DHA_RETRO',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 28), (32, 22), (40, 26), (42, 34), (38, 42), (28, 44)],
        ],
    },
    {
        'name': 'Na_retro', 'script': 'KANNADA', 'concept': 'NA_RETRO',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 46)],
            [(22, 28), (30, 22), (38, 28), (38, 38), (30, 44), (22, 42)],
            [(30, 44), (34, 48)],
        ],
    },
    {
        'name': 'Ta', 'script': 'KANNADA', 'concept': 'TA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 28), (34, 22), (42, 28), (40, 38), (32, 44), (24, 42)],
        ],
    },
    {
        'name': 'Tha', 'script': 'KANNADA', 'concept': 'THA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 26), (32, 20), (42, 26), (42, 38), (34, 44), (22, 44)],
        ],
    },
    {
        'name': 'Da', 'script': 'KANNADA', 'concept': 'DA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 46)],
            [(24, 26), (34, 22), (40, 28), (38, 36), (30, 40), (24, 38)],
            [(30, 40), (36, 44), (34, 50)],
        ],
    },
    {
        'name': 'Dha', 'script': 'KANNADA', 'concept': 'DHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 26), (30, 20), (38, 24), (40, 34), (36, 42), (26, 44)],
            [(40, 34), (44, 40)],
        ],
    },
    {
        'name': 'Na', 'script': 'KANNADA', 'concept': 'NA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 28), (32, 22), (40, 26), (42, 34), (38, 42), (28, 46), (24, 42)],
        ],
    },
    {
        'name': 'Pa', 'script': 'KANNADA', 'concept': 'PA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 46)],
            [(22, 22), (36, 22), (42, 28), (42, 36), (36, 42), (22, 44)],
        ],
    },
    {
        'name': 'Pha', 'script': 'KANNADA', 'concept': 'PHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 24), (34, 22), (42, 28), (42, 38), (34, 44), (22, 44)],
            [(42, 28), (46, 24)],
        ],
    },
    {
        'name': 'Ba', 'script': 'KANNADA', 'concept': 'BA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 26), (34, 22), (40, 28), (40, 38), (34, 44), (24, 44)],
        ],
    },
    {
        'name': 'Bha', 'script': 'KANNADA', 'concept': 'BHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 26), (32, 20), (40, 26), (42, 36), (36, 44), (22, 44)],
            [(42, 36), (44, 42)],
        ],
    },
    {
        'name': 'Ma', 'script': 'KANNADA', 'concept': 'MA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 46)],
            [(24, 28), (32, 22), (38, 26), (40, 34), (36, 42), (28, 46)],
        ],
    },
    {
        'name': 'Ya', 'script': 'KANNADA', 'concept': 'YA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 24), (30, 20), (38, 24), (40, 32), (36, 40), (28, 44), (22, 40)],
            [(28, 44), (32, 48), (28, 50)],
        ],
    },
    {
        'name': 'Ra', 'script': 'KANNADA', 'concept': 'RA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 30), (32, 24), (38, 28), (36, 36), (28, 40), (24, 38)],
        ],
    },
    {
        'name': 'La', 'script': 'KANNADA', 'concept': 'LA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 28), (30, 22), (38, 26), (40, 34), (36, 42), (26, 46)],
        ],
    },
    {
        'name': 'Va', 'script': 'KANNADA', 'concept': 'VA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 46)],
            [(24, 26), (34, 22), (42, 28), (42, 36), (36, 44), (24, 46)],
        ],
    },
    {
        'name': 'Sha', 'script': 'KANNADA', 'concept': 'SHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 26), (30, 20), (38, 24), (40, 32)],
            [(40, 32), (38, 40), (30, 44), (22, 42)],
        ],
    },
    {
        'name': 'Sha_retro', 'script': 'KANNADA', 'concept': 'SHA_RETRO',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 26), (32, 20), (40, 26), (42, 34), (38, 42), (28, 46)],
        ],
    },
    {
        'name': 'Sa', 'script': 'KANNADA', 'concept': 'SA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 46)],
            [(22, 22), (34, 22), (40, 28), (40, 36), (34, 42), (22, 42)],
            [(28, 42), (28, 48)],
        ],
    },
    {
        'name': 'Ha', 'script': 'KANNADA', 'concept': 'HA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(22, 22), (22, 48)],
            [(22, 28), (34, 22), (42, 28), (42, 38), (34, 46), (22, 48)],
        ],
    },
    {
        'name': 'Lla', 'script': 'KANNADA', 'concept': 'LLA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 28), (34, 22), (40, 28), (40, 38), (34, 44), (24, 44)],
            [(34, 44), (38, 50)],
        ],
    },
    {
        'name': 'Ksha', 'script': 'KANNADA', 'concept': 'KSHA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(20, 22), (20, 46)],
            [(20, 26), (28, 20), (34, 24), (34, 32), (28, 36), (20, 34)],
            [(34, 24), (40, 22), (44, 28), (42, 36), (36, 40)],
        ],
    },
    {
        'name': 'Rra', 'script': 'KANNADA', 'concept': 'RRA',
        'origin': 'KANNADA ~1000 AD',
        'ink': _KANNADA_INK, 'paper': _KANNADA_PAPER,
        'strokes': [
            [(24, 22), (24, 48)],
            [(24, 26), (32, 20), (40, 24), (42, 34), (38, 44), (28, 48)],
        ],
    },
]

# ═══════════════════════════════════════════════════════════════════════════════
#  MALAYALAM  (~38M speakers, Kerala)
#  Extremely rounded — almost all letters based on circles and curves.
# ═══════════════════════════════════════════════════════════════════════════════

MALAYALAM_CHARS = [
    # ── Vowels (14) ──────────────────────────────────────────────────────────
    {
        'name': 'A', 'script': 'MALAYALAM', 'concept': 'A',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(30, 22), (24, 26), (22, 34), (26, 42), (34, 44), (40, 40), (42, 32), (38, 24), (30, 22)],
            [(34, 44), (32, 50)],
        ],
    },
    {
        'name': 'Aa', 'script': 'MALAYALAM', 'concept': 'AA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 36), (28, 42), (34, 42), (38, 36), (38, 28), (32, 22), (28, 22)],
            [(38, 28), (44, 26), (44, 38), (40, 44)],
        ],
    },
    {
        'name': 'I', 'script': 'MALAYALAM', 'concept': 'I',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 22), (22, 28), (24, 36), (30, 40), (36, 36), (38, 28), (34, 22), (26, 22)],
            [(30, 40), (28, 48)],
        ],
    },
    {
        'name': 'Ii', 'script': 'MALAYALAM', 'concept': 'II',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 22), (22, 28), (24, 36), (30, 40), (36, 36), (38, 28), (34, 22), (26, 22)],
            [(30, 40), (28, 48)],
            [(40, 22), (44, 26), (42, 32)],
        ],
    },
    {
        'name': 'U', 'script': 'MALAYALAM', 'concept': 'U',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (32, 42), (40, 38), (42, 30), (38, 22), (30, 20), (26, 24)],
        ],
    },
    {
        'name': 'Uu', 'script': 'MALAYALAM', 'concept': 'UU',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (32, 42), (40, 38), (42, 30), (38, 22), (30, 20), (26, 24)],
            [(32, 42), (30, 48), (34, 50)],
        ],
    },
    {
        'name': 'E', 'script': 'MALAYALAM', 'concept': 'E',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(22, 30), (26, 22), (34, 22), (40, 28), (38, 36), (30, 40), (24, 36), (22, 30)],
            [(30, 40), (34, 46), (30, 50)],
        ],
    },
    {
        'name': 'Ee', 'script': 'MALAYALAM', 'concept': 'EE',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(22, 30), (26, 22), (34, 22), (40, 28), (38, 36), (30, 40), (24, 36), (22, 30)],
            [(30, 40), (34, 46), (30, 50)],
            [(42, 22), (44, 28)],
        ],
    },
    {
        'name': 'Ai', 'script': 'MALAYALAM', 'concept': 'AI',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(24, 28), (28, 22), (36, 22), (40, 28), (38, 36), (30, 40), (24, 36), (22, 30)],
            [(30, 40), (32, 46), (28, 50)],
            [(20, 22), (22, 20)],
        ],
    },
    {
        'name': 'O', 'script': 'MALAYALAM', 'concept': 'O',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 24), (22, 30), (22, 38), (28, 44), (36, 44), (42, 38), (42, 30), (36, 24), (28, 24)],
        ],
    },
    {
        'name': 'Oo', 'script': 'MALAYALAM', 'concept': 'OO',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 24), (22, 30), (22, 38), (28, 44), (36, 44), (42, 38), (42, 30), (36, 24), (28, 24)],
            [(42, 30), (46, 28), (46, 36)],
        ],
    },
    {
        'name': 'Au', 'script': 'MALAYALAM', 'concept': 'AU',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (30, 42), (38, 40), (42, 32), (38, 24), (30, 22), (26, 24)],
            [(42, 32), (46, 36), (44, 44)],
        ],
    },
    {
        'name': 'Am', 'script': 'MALAYALAM', 'concept': 'AM',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 24), (22, 30), (24, 38), (32, 42), (40, 38), (42, 30), (36, 24), (28, 24)],
            [(34, 20), (36, 20)],
        ],
    },
    {
        'name': 'Aha', 'script': 'MALAYALAM', 'concept': 'AHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (36, 44), (42, 38), (42, 28), (36, 22), (28, 22)],
            [(32, 44), (32, 50)],
        ],
    },
    # ── Consonants (36) ──────────────────────────────────────────────────────
    {
        'name': 'Ka', 'script': 'MALAYALAM', 'concept': 'KA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (24, 36), (30, 40), (36, 36), (38, 28), (34, 22), (28, 22)],
            [(30, 40), (28, 46), (32, 50), (38, 48)],
        ],
    },
    {
        'name': 'Kha', 'script': 'MALAYALAM', 'concept': 'KHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 22), (20, 28), (22, 36), (28, 40), (36, 38), (38, 30), (34, 22), (26, 22)],
            [(28, 40), (26, 46), (30, 50)],
            [(38, 30), (42, 26), (44, 32)],
        ],
    },
    {
        'name': 'Ga', 'script': 'MALAYALAM', 'concept': 'GA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(30, 22), (24, 26), (22, 34), (26, 42), (34, 44), (40, 40), (42, 32), (38, 24), (30, 22)],
            [(26, 42), (24, 48), (28, 50)],
        ],
    },
    {
        'name': 'Gha', 'script': 'MALAYALAM', 'concept': 'GHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (36, 42), (40, 36), (40, 26), (34, 22), (28, 22)],
            [(28, 44), (30, 50)],
            [(40, 26), (44, 22)],
        ],
    },
    {
        'name': 'Nga', 'script': 'MALAYALAM', 'concept': 'NGA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(24, 28), (28, 22), (36, 22), (40, 28), (38, 36), (30, 40), (24, 36), (22, 28)],
            [(30, 40), (32, 46), (36, 50)],
        ],
    },
    {
        'name': 'Cha', 'script': 'MALAYALAM', 'concept': 'CHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(22, 30), (26, 22), (34, 22), (40, 28), (40, 36), (34, 42), (26, 42), (22, 36), (22, 30)],
            [(34, 42), (36, 48)],
        ],
    },
    {
        'name': 'Chha', 'script': 'MALAYALAM', 'concept': 'CHHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(22, 30), (26, 22), (34, 22), (40, 28), (40, 36), (34, 42), (26, 42), (22, 36)],
            [(34, 42), (38, 48), (42, 46)],
        ],
    },
    {
        'name': 'Ja', 'script': 'MALAYALAM', 'concept': 'JA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (32, 42), (38, 38), (40, 30), (36, 24), (26, 24)],
            [(32, 42), (30, 48)],
        ],
    },
    {
        'name': 'Jha', 'script': 'MALAYALAM', 'concept': 'JHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 22), (20, 30), (22, 38), (30, 42), (38, 38), (42, 30), (38, 22), (30, 20), (26, 22)],
            [(30, 42), (34, 48), (40, 48)],
        ],
    },
    {
        'name': 'Nya', 'script': 'MALAYALAM', 'concept': 'NYA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(22, 28), (26, 22), (34, 22), (38, 28), (36, 34), (28, 36), (22, 32)],
            [(36, 34), (42, 32), (44, 38), (40, 44)],
            [(30, 36), (28, 44), (32, 48)],
        ],
    },
    {
        'name': 'Ta_retro', 'script': 'MALAYALAM', 'concept': 'TA_RETRO',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (36, 44), (42, 38), (42, 28), (36, 22), (28, 22)],
            [(28, 44), (26, 50)],
        ],
    },
    {
        'name': 'Tha_retro', 'script': 'MALAYALAM', 'concept': 'THA_RETRO',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 22), (20, 30), (22, 38), (30, 44), (38, 40), (42, 32), (38, 24), (30, 20), (26, 22)],
            [(30, 44), (28, 50)],
        ],
    },
    {
        'name': 'Da_retro', 'script': 'MALAYALAM', 'concept': 'DA_RETRO',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(30, 22), (24, 26), (20, 34), (24, 42), (32, 46), (40, 42), (44, 34), (40, 26), (32, 22)],
            [(32, 46), (30, 50)],
        ],
    },
    {
        'name': 'Dha_retro', 'script': 'MALAYALAM', 'concept': 'DHA_RETRO',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (20, 36), (24, 44), (32, 46), (40, 42), (44, 34), (40, 26), (34, 22), (28, 22)],
            [(32, 46), (34, 50)],
        ],
    },
    {
        'name': 'Na_retro', 'script': 'MALAYALAM', 'concept': 'NA_RETRO',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (30, 42), (38, 40), (42, 32), (40, 24), (32, 20), (26, 24)],
            [(30, 42), (28, 48), (32, 50)],
        ],
    },
    {
        'name': 'Ta', 'script': 'MALAYALAM', 'concept': 'TA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(24, 26), (28, 20), (36, 20), (42, 26), (42, 36), (36, 42), (28, 42), (24, 36), (24, 26)],
            [(32, 42), (32, 48)],
        ],
    },
    {
        'name': 'Tha', 'script': 'MALAYALAM', 'concept': 'THA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 32), (26, 40), (34, 44), (42, 40), (44, 32), (40, 24), (32, 20), (26, 24)],
            [(34, 44), (32, 50)],
        ],
    },
    {
        'name': 'Da', 'script': 'MALAYALAM', 'concept': 'DA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(30, 22), (24, 26), (22, 34), (26, 42), (34, 44), (40, 40), (42, 32), (38, 24), (30, 22)],
            [(34, 44), (38, 48), (42, 46)],
        ],
    },
    {
        'name': 'Dha', 'script': 'MALAYALAM', 'concept': 'DHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (38, 46), (44, 40), (44, 30), (38, 22), (28, 22)],
            [(28, 44), (26, 50)],
        ],
    },
    {
        'name': 'Na', 'script': 'MALAYALAM', 'concept': 'NA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (30, 42), (38, 40), (42, 32), (40, 24), (32, 20), (26, 24)],
            [(30, 42), (32, 48)],
        ],
    },
    {
        'name': 'Pa', 'script': 'MALAYALAM', 'concept': 'PA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (24, 36), (30, 40), (38, 38), (42, 30), (38, 22), (28, 22)],
            [(30, 40), (28, 46), (32, 50)],
        ],
    },
    {
        'name': 'Pha', 'script': 'MALAYALAM', 'concept': 'PHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 22), (20, 30), (22, 38), (30, 44), (38, 40), (42, 32), (38, 24), (30, 20), (26, 22)],
            [(30, 44), (34, 50), (40, 48)],
        ],
    },
    {
        'name': 'Ba', 'script': 'MALAYALAM', 'concept': 'BA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (36, 44), (42, 38), (42, 28), (36, 22), (28, 22)],
            [(28, 44), (26, 50)],
        ],
    },
    {
        'name': 'Bha', 'script': 'MALAYALAM', 'concept': 'BHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (36, 42), (40, 36), (40, 26), (34, 22), (28, 22)],
            [(28, 44), (30, 50)],
            [(40, 26), (44, 22)],
        ],
    },
    {
        'name': 'Ma', 'script': 'MALAYALAM', 'concept': 'MA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(30, 22), (24, 26), (20, 34), (24, 42), (32, 46), (40, 42), (44, 34), (40, 26), (34, 22), (30, 22)],
        ],
    },
    {
        'name': 'Ya', 'script': 'MALAYALAM', 'concept': 'YA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(24, 26), (28, 20), (36, 20), (42, 26), (40, 34), (34, 40), (26, 40), (22, 34)],
            [(34, 40), (36, 46), (32, 50)],
        ],
    },
    {
        'name': 'Ra', 'script': 'MALAYALAM', 'concept': 'RA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (30, 42), (38, 40), (42, 32), (38, 24), (30, 20), (26, 24)],
            [(30, 42), (28, 48)],
        ],
    },
    {
        'name': 'La', 'script': 'MALAYALAM', 'concept': 'LA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (36, 44), (42, 38), (42, 28), (36, 22), (28, 22)],
            [(32, 44), (30, 50)],
        ],
    },
    {
        'name': 'Va', 'script': 'MALAYALAM', 'concept': 'VA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(24, 26), (28, 20), (36, 20), (42, 26), (42, 36), (36, 42), (28, 42), (22, 36), (22, 28)],
            [(36, 42), (40, 48)],
        ],
    },
    {
        'name': 'Sha', 'script': 'MALAYALAM', 'concept': 'SHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(22, 28), (26, 22), (34, 22), (40, 28), (38, 36), (30, 40), (24, 36), (22, 28)],
            [(30, 40), (34, 46), (38, 50)],
        ],
    },
    {
        'name': 'Sha_retro', 'script': 'MALAYALAM', 'concept': 'SHA_RETRO',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 36), (28, 42), (36, 42), (42, 36), (42, 28), (36, 22), (28, 22)],
            [(28, 42), (26, 48), (30, 50)],
        ],
    },
    {
        'name': 'Sa', 'script': 'MALAYALAM', 'concept': 'SA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(24, 26), (28, 20), (36, 20), (42, 26), (40, 34), (34, 40), (26, 40), (22, 34), (24, 26)],
            [(34, 40), (36, 46), (32, 50)],
        ],
    },
    {
        'name': 'Ha', 'script': 'MALAYALAM', 'concept': 'HA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (20, 36), (24, 44), (32, 46), (40, 42), (44, 34), (42, 26), (36, 22), (28, 22)],
            [(32, 46), (30, 50)],
        ],
    },
    {
        'name': 'Lla', 'script': 'MALAYALAM', 'concept': 'LLA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(26, 24), (22, 30), (24, 38), (30, 42), (38, 40), (42, 32), (40, 24), (32, 20), (26, 24)],
            [(30, 42), (28, 48), (32, 50), (36, 48)],
        ],
    },
    {
        'name': 'Zha', 'script': 'MALAYALAM', 'concept': 'ZHA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(24, 26), (28, 20), (36, 20), (42, 26), (40, 34), (34, 40), (26, 42), (22, 36)],
            [(34, 40), (38, 46), (34, 50)],
        ],
    },
    {
        'name': 'Rra', 'script': 'MALAYALAM', 'concept': 'RRA',
        'origin': 'MALAYALAM ~830 AD',
        'ink': _MALAYALAM_INK, 'paper': _MALAYALAM_PAPER,
        'strokes': [
            [(28, 22), (22, 28), (22, 38), (28, 44), (36, 44), (42, 38), (42, 28), (36, 22), (28, 22)],
            [(36, 44), (40, 48), (36, 50)],
        ],
    },
]

# ── Verification ─────────────────────────────────────────────────────────────

if __name__ == '__main__':
    for name, chars in [('TELUGU', TELUGU_CHARS), ('KANNADA', KANNADA_CHARS), ('MALAYALAM', MALAYALAM_CHARS)]:
        print(f'{name}: {len(chars)} chars')
        for ch in chars:
            for si, stroke in enumerate(ch['strokes']):
                for x, y in stroke:
                    assert 8 <= x <= 56 and 14 <= y <= 56, f"OOB: {ch['name']} ({x},{y})"
    print('All OK')

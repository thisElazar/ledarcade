"""Pasta Shapes - Pixel art pasta reference on 64x64 LED matrix.

Each of 20 pasta shapes gets a small pixel art illustration in the top half,
with name, Italian meaning, region, and sauce pairings as reference text below.
"""

from . import Visual

# ── Families ────────────────────────────────────────────────────────
FAMILIES = ["LONG", "TUBE", "SHAPED", "FILLED", "SHEET"]
FAMILY_COLORS = [
    (220, 180, 80),    # LONG = golden wheat
    (200, 150, 60),    # TUBE = warm amber
    (200, 120, 60),    # SHAPED = terracotta
    (230, 200, 80),    # FILLED = egg yellow
    (220, 200, 160),   # SHEET = cream
]

HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)

# Pasta color palette
_B = (230, 200, 120)   # base
_L = (245, 225, 160)   # light / highlight
_S = (180, 150, 80)    # shadow
_D = (140, 110, 60)    # dark / ridges
_F = (180, 100, 60)    # filling
_  = None               # transparent

# ── Sprite data (each ~20×16, recognizable at pixel scale) ─────────

_SPAGHETTI = [
    [_,_,_,_,_L,_,_,_L,_,_,_,_L,_,_,_L,_,_,_,_L,_],
    [_,_,_,_,_B,_,_,_B,_,_,_,_B,_,_,_B,_,_,_,_B,_],
    [_,_,_,_,_B,_,_,_B,_,_,_,_B,_,_,_B,_,_,_,_B,_],
    [_,_,_,_,_B,_,_,_,_B,_,_B,_,_,_,_B,_,_,_B,_],
    [_,_,_,_,_B,_,_,_,_B,_,_B,_,_,_,_B,_,_,_B,_],
    [_,_,_,_,_S,_,_,_,_B,_,_B,_,_,_,_S,_,_,_B,_],
    [_,_,_,_,_S,_,_,_B,_,_,_,_B,_,_,_S,_,_,_,_B,_],
    [_,_,_,_,_B,_,_,_B,_,_,_,_B,_,_,_B,_,_,_,_B,_],
    [_,_,_,_,_B,_,_,_B,_,_,_,_B,_,_,_B,_,_,_,_B,_],
    [_,_,_,_,_B,_,_,_,_B,_,_B,_,_,_,_B,_,_,_B,_],
    [_,_,_,_,_S,_,_,_,_B,_,_S,_,_,_,_B,_,_,_S,_],
    [_,_,_,_,_B,_,_,_B,_,_,_,_B,_,_,_B,_,_,_,_B,_],
    [_,_,_,_,_B,_,_,_B,_,_,_,_B,_,_,_B,_,_,_,_B,_],
    [_,_,_,_,_S,_,_,_S,_,_,_,_S,_,_,_S,_,_,_,_S,_],
]

_LINGUINE = [
    [_,_,_,_L,_L,_,_,_L,_L,_,_,_L,_L,_,_,_L,_L,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_B,_S,_,_,_B,_S,_,_,_B,_S,_,_,_B,_S,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_S,_B,_,_,_S,_B,_,_,_S,_B,_,_,_S,_B,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_,_B,_B,_,_],
    [_,_,_,_S,_S,_,_,_S,_S,_,_,_S,_S,_,_,_S,_S,_,_],
]

_BUCATINI = [
    [_,_,_,_L,_L,_L,_,_,_,_L,_L,_L,_,_,_,_L,_L,_L,_,_],
    [_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_],
    [_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_],
    [_,_,_,_B,_L,_S,_,_,_,_B,_L,_S,_,_,_,_B,_L,_S,_,_],
    [_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_],
    [_,_,_,_S,_L,_B,_,_,_,_S,_L,_B,_,_,_,_S,_L,_B,_,_],
    [_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_],
    [_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_],
    [_,_,_,_B,_L,_S,_,_,_,_B,_L,_S,_,_,_,_B,_L,_S,_,_],
    [_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_],
    [_,_,_,_S,_L,_B,_,_,_,_S,_L,_B,_,_,_,_S,_L,_B,_,_],
    [_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_,_,_B,_L,_B,_,_],
    [_,_,_,_S,_S,_S,_,_,_,_S,_S,_S,_,_,_,_S,_S,_S,_,_],
]

_CAPELLINI = [
    [_,_,_S,_,_S,_,_S,_,_S,_,_S,_,_S,_,_S,_,_S,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_S,_,_B,_,_S,_,_B,_,_S,_,_B,_,_S,_,_B,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_B,_,_S,_,_B,_,_S,_,_B,_,_S,_,_B,_,_S,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_S,_,_B,_,_S,_,_B,_,_S,_,_B,_,_S,_,_B,_,_],
    [_,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_B,_,_],
    [_,_,_S,_,_S,_,_S,_,_S,_,_S,_,_S,_,_S,_,_S,_,_],
]

_FETTUCCINE = [
    [_,_,_,_L,_L,_L,_L,_,_,_L,_L,_L,_L,_,_,_L,_L,_L,_L,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_B,_B,_S,_S,_,_,_B,_B,_S,_S,_,_,_B,_B,_S,_S,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_],
    [_,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_,_,_B,_B,_B,_S,_],
    [_,_,_,_S,_S,_S,_D,_,_,_S,_S,_S,_D,_,_,_S,_S,_S,_D,_],
]

_PAPPARDELLE = [
    [_,_,_L,_L,_L,_L,_L,_L,_,_,_L,_L,_L,_L,_L,_L,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_S,_B,_B,_B,_B,_S,_,_,_S,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_S,_S,_,_,_B,_B,_B,_B,_S,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_S,_B,_B,_B,_B,_S,_,_,_S,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_B,_B,_B,_B,_B,_S,_,_,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_S,_S,_S,_S,_S,_D,_,_,_S,_S,_S,_S,_S,_D,_,_,_,_],
]

_PENNE = [
    [_,_,_,_,_,_,_,_,_,_L,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_L,_B,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_L,_B,_B,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_B,_B,_S,_,_,_,_,_L,_,_,_,_,_],
    [_,_,_,_,_,_,_,_B,_B,_S,_,_,_,_L,_B,_,_,_,_,_],
    [_,_,_L,_,_,_,_,_B,_B,_S,_,_,_L,_B,_B,_,_,_,_,_],
    [_,_L,_B,_,_,_,_,_S,_B,_S,_,_,_B,_B,_S,_,_,_,_,_],
    [_,_B,_B,_B,_,_,_,_S,_B,_S,_,_,_B,_B,_S,_,_,_,_,_],
    [_,_B,_B,_S,_,_,_,_S,_B,_D,_,_,_B,_B,_S,_,_,_,_,_],
    [_,_B,_B,_S,_,_,_,_,_S,_D,_,_,_S,_B,_S,_,_,_,_,_],
    [_,_S,_B,_S,_,_,_,_,_D,_,_,_,_S,_B,_D,_,_,_,_,_],
    [_,_S,_B,_D,_,_,_,_,_,_,_,_,_,_S,_D,_,_,_,_,_],
    [_,_,_S,_D,_,_,_,_,_,_,_,_,_,_,_D,_,_,_,_,_],
    [_,_,_,_D,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
]

_RIGATONI = [
    [_,_,_,_,_L,_L,_L,_L,_L,_,_,_,_L,_L,_L,_L,_L,_,_,_],
    [_,_,_,_,_B,_B,_B,_B,_S,_,_,_,_B,_B,_B,_B,_S,_,_,_],
    [_,_,_,_,_D,_D,_D,_D,_D,_,_,_,_D,_D,_D,_D,_D,_,_,_],
    [_,_,_,_,_B,_B,_B,_B,_S,_,_,_,_B,_B,_B,_B,_S,_,_,_],
    [_,_,_,_,_D,_D,_D,_D,_D,_,_,_,_D,_D,_D,_D,_D,_,_,_],
    [_,_,_,_,_B,_B,_B,_B,_S,_,_,_,_B,_B,_B,_B,_S,_,_,_],
    [_,_,_,_,_D,_D,_D,_D,_D,_,_,_,_D,_D,_D,_D,_D,_,_,_],
    [_,_,_,_,_B,_B,_B,_B,_S,_,_,_,_B,_B,_B,_B,_S,_,_,_],
    [_,_,_,_,_D,_D,_D,_D,_D,_,_,_,_D,_D,_D,_D,_D,_,_,_],
    [_,_,_,_,_B,_B,_B,_B,_S,_,_,_,_B,_B,_B,_B,_S,_,_,_],
    [_,_,_,_,_S,_S,_S,_S,_D,_,_,_,_S,_S,_S,_S,_D,_,_,_],
]

_PACCHERI = [
    [_,_,_,_L,_L,_L,_L,_L,_L,_,_,_L,_L,_L,_L,_L,_L,_,_,_],
    [_,_,_,_B,_B,_L,_L,_B,_S,_,_,_B,_B,_L,_L,_B,_S,_,_,_],
    [_,_,_,_B,_B,_L,_L,_B,_S,_,_,_B,_B,_L,_L,_B,_S,_,_,_],
    [_,_,_,_B,_B,_L,_L,_B,_S,_,_,_B,_B,_L,_L,_B,_S,_,_,_],
    [_,_,_,_B,_B,_L,_B,_B,_S,_,_,_B,_B,_L,_B,_B,_S,_,_,_],
    [_,_,_,_B,_S,_L,_B,_B,_S,_,_,_B,_S,_L,_B,_B,_S,_,_,_],
    [_,_,_,_B,_B,_L,_L,_B,_S,_,_,_B,_B,_L,_L,_B,_S,_,_,_],
    [_,_,_,_B,_B,_L,_L,_B,_S,_,_,_B,_B,_L,_L,_B,_S,_,_,_],
    [_,_,_,_B,_B,_L,_L,_B,_S,_,_,_B,_B,_L,_L,_B,_S,_,_,_],
    [_,_,_,_S,_S,_S,_S,_S,_D,_,_,_S,_S,_S,_S,_S,_D,_,_,_],
]

_MACARONI = [
    [_,_,_,_,_,_L,_L,_,_,_,_,_,_L,_L,_,_,_,_,_L,_L],
    [_,_,_,_,_L,_B,_B,_L,_,_,_,_L,_B,_B,_L,_,_,_L,_B,_B],
    [_,_,_,_,_B,_L,_B,_S,_,_,_,_B,_L,_B,_S,_,_,_B,_L,_B],
    [_,_,_,_,_B,_L,_,_S,_,_,_,_B,_L,_,_S,_,_,_B,_L,_],
    [_,_,_,_,_B,_L,_,_,_,_,_,_B,_L,_,_,_,_,_B,_L,_],
    [_,_,_,_,_B,_L,_,_,_,_,_,_B,_L,_,_,_,_,_B,_L,_],
    [_,_,_,_,_B,_L,_,_,_,_,_,_B,_L,_,_,_,_,_B,_L,_],
    [_,_,_,_,_S,_B,_,_,_,_,_,_S,_B,_,_,_,_,_S,_B,_],
    [_,_,_,_,_,_S,_B,_,_,_,_,_,_S,_B,_,_,_,_,_S,_B],
    [_,_,_,_,_,_,_S,_B,_,_,_,_,_,_S,_B,_,_,_,_,_S],
    [_,_,_,_,_,_,_S,_S,_,_,_,_,_,_S,_S,_,_,_,_,_S],
]

_FUSILLI = [
    [_,_,_,_,_,_,_L,_L,_,_,_,_,_,_L,_L,_,_,_,_,_],
    [_,_,_,_,_,_L,_B,_B,_L,_,_,_,_L,_B,_B,_L,_,_,_,_],
    [_,_,_,_,_B,_B,_,_,_B,_S,_,_B,_B,_,_,_B,_S,_,_,_],
    [_,_,_,_,_S,_B,_,_,_B,_S,_,_S,_B,_,_,_B,_S,_,_,_],
    [_,_,_,_,_,_S,_B,_B,_S,_,_,_,_S,_B,_B,_S,_,_,_,_],
    [_,_,_,_,_,_,_S,_S,_,_,_,_,_,_S,_S,_,_,_,_,_],
    [_,_,_,_,_,_L,_B,_B,_L,_,_,_,_L,_B,_B,_L,_,_,_,_],
    [_,_,_,_,_B,_B,_,_,_B,_S,_,_B,_B,_,_,_B,_S,_,_,_],
    [_,_,_,_,_S,_B,_,_,_B,_S,_,_S,_B,_,_,_B,_S,_,_,_],
    [_,_,_,_,_,_S,_B,_B,_S,_,_,_,_S,_B,_B,_S,_,_,_,_],
    [_,_,_,_,_,_,_S,_S,_,_,_,_,_,_S,_S,_,_,_,_,_],
    [_,_,_,_,_,_L,_B,_B,_L,_,_,_,_L,_B,_B,_L,_,_,_,_],
    [_,_,_,_,_B,_B,_,_,_B,_S,_,_B,_B,_,_,_B,_S,_,_,_],
    [_,_,_,_,_S,_S,_,_,_S,_D,_,_S,_S,_,_,_S,_D,_,_,_],
]

_FARFALLE = [
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_L,_L,_L,_,_,_,_,_,_,_,_,_,_L,_L,_L,_,_,_],
    [_,_L,_B,_B,_B,_L,_,_,_,_,_,_,_L,_B,_B,_B,_L,_,_,_],
    [_,_B,_B,_B,_B,_B,_L,_,_,_,_,_L,_B,_B,_B,_B,_B,_,_,_],
    [_,_B,_B,_B,_B,_B,_B,_S,_B,_S,_B,_B,_B,_B,_B,_B,_B,_,_,_],
    [_,_B,_B,_B,_B,_B,_B,_D,_S,_D,_B,_B,_B,_B,_B,_B,_B,_,_,_],
    [_,_S,_B,_B,_B,_B,_B,_S,_B,_S,_B,_B,_B,_B,_B,_S,_,_,_,_],
    [_,_,_S,_B,_B,_B,_S,_,_,_,_,_,_S,_B,_B,_B,_S,_,_,_],
    [_,_,_,_S,_S,_S,_,_,_,_,_,_,_,_,_S,_S,_S,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
]

_ORECCHIETTE = [
    [_,_,_,_,_,_L,_L,_,_,_,_,_L,_L,_,_,_,_L,_L,_,_],
    [_,_,_,_,_L,_B,_B,_L,_,_,_L,_B,_B,_L,_,_L,_B,_B,_L,_],
    [_,_,_,_,_B,_S,_B,_B,_,_,_B,_S,_B,_B,_,_B,_S,_B,_B,_],
    [_,_,_,_,_B,_B,_S,_B,_,_,_B,_B,_S,_B,_,_B,_B,_S,_B,_],
    [_,_,_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_,_S,_B,_B,_S,_],
    [_,_,_,_,_,_S,_S,_,_,_,_,_S,_S,_,_,_,_S,_S,_,_],
]

_CONCHIGLIE = [
    [_,_,_,_,_,_L,_L,_L,_,_,_,_,_,_L,_L,_L,_,_,_,_],
    [_,_,_,_,_L,_B,_B,_B,_L,_,_,_,_L,_B,_B,_B,_L,_,_,_],
    [_,_,_,_,_B,_D,_B,_D,_B,_,_,_,_B,_D,_B,_D,_B,_,_,_],
    [_,_,_,_,_B,_B,_D,_B,_B,_S,_,_,_B,_B,_D,_B,_B,_S,_,_],
    [_,_,_,_,_B,_D,_B,_D,_B,_S,_,_,_B,_D,_B,_D,_B,_S,_,_],
    [_,_,_,_,_S,_B,_D,_B,_B,_S,_,_,_S,_B,_D,_B,_B,_S,_,_],
    [_,_,_,_,_,_S,_B,_B,_S,_,_,_,_,_S,_B,_B,_S,_,_,_],
    [_,_,_,_,_,_,_S,_S,_,_,_,_,_,_,_S,_S,_,_,_,_],
]

_CAVATAPPI = [
    [_,_,_,_,_,_,_L,_L,_L,_,_,_,_,_L,_L,_L,_,_,_,_],
    [_,_,_,_,_,_L,_B,_L,_B,_S,_,_,_L,_B,_L,_B,_S,_,_,_],
    [_,_,_,_,_,_B,_B,_L,_B,_S,_,_,_B,_B,_L,_B,_S,_,_,_],
    [_,_,_,_,_,_,_S,_B,_S,_,_,_,_,_S,_B,_S,_,_,_,_],
    [_,_,_,_,_,_L,_B,_L,_B,_S,_,_,_L,_B,_L,_B,_S,_,_,_],
    [_,_,_,_,_,_B,_B,_L,_B,_S,_,_,_B,_B,_L,_B,_S,_,_,_],
    [_,_,_,_,_,_,_S,_B,_S,_,_,_,_,_S,_B,_S,_,_,_,_],
    [_,_,_,_,_,_L,_B,_L,_B,_S,_,_,_L,_B,_L,_B,_S,_,_,_],
    [_,_,_,_,_,_B,_B,_L,_B,_S,_,_,_B,_B,_L,_B,_S,_,_,_],
    [_,_,_,_,_,_,_S,_S,_D,_,_,_,_,_S,_S,_D,_,_,_,_],
]

_STROZZAPRETI = [
    [_,_,_,_L,_L,_,_,_,_,_L,_L,_,_,_,_,_L,_L,_,_,_],
    [_,_,_,_B,_B,_L,_,_,_,_B,_B,_L,_,_,_,_B,_B,_L,_,_],
    [_,_,_,_B,_S,_B,_,_,_,_B,_S,_B,_,_,_,_B,_S,_B,_,_],
    [_,_,_,_,_B,_B,_S,_,_,_,_B,_B,_S,_,_,_,_B,_B,_S,_],
    [_,_,_,_,_B,_S,_B,_,_,_,_B,_S,_B,_,_,_,_B,_S,_B,_],
    [_,_,_,_,_S,_B,_B,_,_,_,_S,_B,_B,_,_,_,_S,_B,_B,_],
    [_,_,_,_B,_B,_S,_,_,_,_B,_B,_S,_,_,_,_B,_B,_S,_,_],
    [_,_,_,_B,_S,_B,_,_,_,_B,_S,_B,_,_,_,_B,_S,_B,_,_],
    [_,_,_,_,_B,_B,_S,_,_,_,_B,_B,_S,_,_,_,_B,_B,_S,_],
    [_,_,_,_,_S,_S,_D,_,_,_,_S,_S,_D,_,_,_,_S,_S,_D,_],
]

_RAVIOLI = [
    [_,_,_,_,_D,_D,_D,_D,_D,_D,_,_,_D,_D,_D,_D,_D,_D,_,_],
    [_,_,_,_D,_L,_L,_L,_L,_L,_D,_,_D,_L,_L,_L,_L,_L,_D,_,_],
    [_,_,_,_D,_B,_B,_B,_B,_B,_S,_,_D,_B,_B,_B,_B,_B,_S,_,_],
    [_,_,_,_D,_B,_F,_F,_F,_B,_S,_,_D,_B,_F,_F,_F,_B,_S,_,_],
    [_,_,_,_D,_B,_F,_F,_F,_B,_S,_,_D,_B,_F,_F,_F,_B,_S,_,_],
    [_,_,_,_D,_B,_F,_F,_F,_B,_S,_,_D,_B,_F,_F,_F,_B,_S,_,_],
    [_,_,_,_D,_B,_B,_B,_B,_B,_S,_,_D,_B,_B,_B,_B,_B,_S,_,_],
    [_,_,_,_D,_S,_S,_S,_S,_S,_D,_,_D,_S,_S,_S,_S,_S,_D,_,_],
    [_,_,_,_,_D,_D,_D,_D,_D,_D,_,_,_D,_D,_D,_D,_D,_D,_,_],
]

_TORTELLINI = [
    [_,_,_,_,_,_L,_L,_L,_,_,_,_,_,_L,_L,_L,_,_,_,_],
    [_,_,_,_,_L,_B,_B,_B,_L,_,_,_,_L,_B,_B,_B,_L,_,_,_],
    [_,_,_,_,_B,_B,_F,_B,_B,_S,_,_,_B,_B,_F,_B,_B,_S,_,_],
    [_,_,_,_S,_B,_F,_F,_B,_B,_S,_,_S,_B,_F,_F,_B,_B,_S,_],
    [_,_,_,_S,_B,_B,_B,_B,_S,_,_,_S,_B,_B,_B,_B,_S,_,_,_],
    [_,_,_,_,_S,_S,_B,_B,_B,_L,_,_,_S,_S,_B,_B,_B,_L,_,_],
    [_,_,_,_,_,_,_S,_B,_B,_S,_,_,_,_,_S,_B,_B,_S,_,_,_],
    [_,_,_,_,_,_,_,_S,_S,_,_,_,_,_,_,_S,_S,_,_,_],
]

_AGNOLOTTI = [
    [_,_,_D,_D,_D,_D,_,_,_D,_D,_D,_D,_,_,_D,_D,_D,_D,_,_],
    [_,_,_D,_L,_L,_D,_,_,_D,_L,_L,_D,_,_,_D,_L,_L,_D,_,_],
    [_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_,_],
    [_,_,_S,_B,_F,_S,_,_,_S,_B,_F,_S,_,_,_S,_B,_F,_S,_,_],
    [_,_,_S,_B,_F,_S,_,_,_S,_B,_F,_S,_,_,_S,_B,_F,_S,_,_],
    [_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_,_,_S,_B,_B,_S,_,_],
    [_,_,_D,_S,_S,_D,_,_,_D,_S,_S,_D,_,_,_D,_S,_S,_D,_,_],
    [_,_,_,_D,_D,_,_,_,_,_D,_D,_,_,_,_,_D,_D,_,_,_],
]

_LASAGNA = [
    [_,_,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_,_],
    [_,_,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_S,_,_],
    [_,_,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_,_],
    [_,_,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_,_],
    [_,_,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_S,_,_],
    [_,_,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_,_],
    [_,_,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_,_],
    [_,_,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_B,_S,_,_],
    [_,_,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_F,_,_],
    [_,_,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_L,_,_],
    [_,_,_S,_S,_S,_S,_S,_S,_S,_S,_S,_S,_S,_S,_S,_S,_S,_D,_,_],
]

# ── Pasta data ──────────────────────────────────────────────────────
PASTAS = [
    # ── LONG (family 0) ──────────────────────────────────
    {'name': 'SPAGHETTI', 'family': 0, 'num': 1,
     'meaning': 'LITTLE STRINGS',
     'region': 'CAMPANIA',
     'sauces': 'CARBONARA / AGLIO E OLIO / POMODORO / ALLE VONGOLE',
     'sprite': _SPAGHETTI},
    {'name': 'LINGUINE', 'family': 0, 'num': 2,
     'meaning': 'LITTLE TONGUES',
     'region': 'LIGURIA',
     'sauces': 'PESTO / CLAM SAUCE / SEAFOOD / AGLIO E OLIO',
     'sprite': _LINGUINE},
    {'name': 'BUCATINI', 'family': 0, 'num': 3,
     'meaning': 'LITTLE HOLES',
     'region': 'LAZIO',
     'sauces': "AMATRICIANA / CACIO E PEPE / CARBONARA",
     'sprite': _BUCATINI},
    {'name': 'CAPELLINI', 'family': 0, 'num': 4,
     'meaning': 'THIN HAIR',
     'region': 'CAMPANIA',
     'sauces': 'LIGHT TOMATO / OLIVE OIL / BROTH / LEMON BUTTER',
     'sprite': _CAPELLINI},
    {'name': 'FETTUCCINE', 'family': 0, 'num': 5,
     'meaning': 'LITTLE RIBBONS',
     'region': 'LAZIO',
     'sauces': 'ALFREDO / RAGU / CREAM SAUCE / PORCINI',
     'sprite': _FETTUCCINE},
    {'name': 'PAPPARDELLE', 'family': 0, 'num': 6,
     'meaning': 'TO GOBBLE UP',
     'region': 'TUSCANY',
     'sauces': 'WILD BOAR RAGU / BOLOGNESE / MUSHROOM / DUCK',
     'sprite': _PAPPARDELLE},

    # ── TUBE (family 1) ──────────────────────────────────
    {'name': 'PENNE', 'family': 1, 'num': 7,
     'meaning': 'QUILLS / PENS',
     'region': 'LIGURIA',
     'sauces': 'ARRABBIATA / VODKA / PESTO / NORMA',
     'sprite': _PENNE},
    {'name': 'RIGATONI', 'family': 1, 'num': 8,
     'meaning': 'RIDGED ONES',
     'region': 'LAZIO',
     'sauces': 'RAGU / PAJATA / AMATRICIANA / CACIO E PEPE',
     'sprite': _RIGATONI},
    {'name': 'PACCHERI', 'family': 1, 'num': 9,
     'meaning': 'OPEN-HAND SLAPS',
     'region': 'CAMPANIA',
     'sauces': 'SEAFOOD / RAGU / STUFFED / SORRENTINA',
     'sprite': _PACCHERI},
    {'name': 'MACARONI', 'family': 1, 'num': 10,
     'meaning': 'BLESSED DOUGH',
     'region': 'CAMPANIA',
     'sauces': 'CHEESE SAUCE / BAKED / TOMATO / CREAM',
     'sprite': _MACARONI},

    # ── SHAPED (family 2) ────────────────────────────────
    {'name': 'FUSILLI', 'family': 2, 'num': 11,
     'meaning': 'LITTLE SPINDLES',
     'region': 'CAMPANIA',
     'sauces': 'PESTO / RAGU / CREAM / PRIMAVERA',
     'sprite': _FUSILLI},
    {'name': 'FARFALLE', 'family': 2, 'num': 12,
     'meaning': 'BUTTERFLIES',
     'region': 'EMILIA-ROMAGNA',
     'sauces': 'SALMON / PESTO / CREAM / PRIMAVERA',
     'sprite': _FARFALLE},
    {'name': 'ORECCHIETTE', 'family': 2, 'num': 13,
     'meaning': 'LITTLE EARS',
     'region': 'PUGLIA',
     'sauces': 'BROCCOLI RABE / SAUSAGE / TOMATO / ANCHOVY',
     'sprite': _ORECCHIETTE},
    {'name': 'CONCHIGLIE', 'family': 2, 'num': 14,
     'meaning': 'SEASHELLS',
     'region': 'CAMPANIA',
     'sauces': 'RAGU / CREAM / PESTO / BAKED WITH CHEESE',
     'sprite': _CONCHIGLIE},
    {'name': 'CAVATAPPI', 'family': 2, 'num': 15,
     'meaning': 'CORKSCREWS',
     'region': 'SOUTHERN ITALY',
     'sauces': 'MAC & CHEESE / RAGU / PESTO / ARRABBIATA',
     'sprite': _CAVATAPPI},
    {'name': 'STROZZAPRETI', 'family': 2, 'num': 16,
     'meaning': 'PRIEST STRANGLERS',
     'region': 'EMILIA-ROMAGNA',
     'sauces': 'RAGU / PORCINI / SAGE BUTTER / TOMATO BASIL',
     'sprite': _STROZZAPRETI},

    # ── FILLED (family 3) ────────────────────────────────
    {'name': 'RAVIOLI', 'family': 3, 'num': 17,
     'meaning': 'LITTLE TURNIPS',
     'region': 'LIGURIA',
     'sauces': 'SAGE BUTTER / MARINARA / CREAM / BROWN BUTTER',
     'sprite': _RAVIOLI},
    {'name': 'TORTELLINI', 'family': 3, 'num': 18,
     'meaning': 'LITTLE CAKES',
     'region': 'EMILIA-ROMAGNA',
     'sauces': 'BROTH / CREAM / RAGU / SAGE BUTTER',
     'sprite': _TORTELLINI},
    {'name': 'AGNOLOTTI', 'family': 3, 'num': 19,
     'meaning': 'PRIESTS CAPS',
     'region': 'PIEDMONT',
     'sauces': 'BUTTER / ROAST JUS / SAGE / PAN DRIPPINGS',
     'sprite': _AGNOLOTTI},

    # ── SHEET (family 4) ─────────────────────────────────
    {'name': 'LASAGNA', 'family': 4, 'num': 20,
     'meaning': 'COOKING POT',
     'region': 'EMILIA-ROMAGNA',
     'sauces': 'BOLOGNESE / BECHAMEL / RICOTTA / PESTO',
     'sprite': _LASAGNA},
]

# Build per-family index
_FAMILY_PASTAS = [[] for _ in range(len(FAMILIES))]
for _i, _p in enumerate(PASTAS):
    _FAMILY_PASTAS[_p['family']].append(_i)


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


class Pasta(Visual):
    name = "PASTA"
    description = "Pasta shapes reference"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout Y positions
    NAME_Y = 1
    SEP1_Y = 7
    SPRITE_TOP = 8
    SPRITE_BOTTOM = 29
    SEP2_Y = 30
    MEANING_Y = 32
    SEP3_Y = 38
    SAUCE_Y = 40
    SEP4_Y = 46
    REGION_Y = 48
    FOOT_SEP_Y = 57
    FOOT_Y = 59

    def reset(self):
        self.time = 0.0
        self.pasta_idx = 0
        self._name_scroll_x = 0.0
        self._meaning_scroll_x = 0.0
        self._sauce_scroll_x = 0.0
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0
        self._switch_flash = 0.0

    def _current(self):
        return PASTAS[self.pasta_idx % len(PASTAS)]

    def _step_pasta(self, direction):
        self.pasta_idx = (self.pasta_idx + direction) % len(PASTAS)
        self._name_scroll_x = 0.0
        self._meaning_scroll_x = 0.0
        self._sauce_scroll_x = 0.0
        self._switch_flash = 0.15

    def _jump_family(self, direction):
        cur = self._current()['family']
        target = (cur + direction) % len(FAMILIES)
        if _FAMILY_PASTAS[target]:
            self.pasta_idx = _FAMILY_PASTAS[target][0]
        self._name_scroll_x = 0.0
        self._meaning_scroll_x = 0.0
        self._sauce_scroll_x = 0.0
        self._switch_flash = 0.15

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left_pressed:
            self._step_pasta(-1)
            self._scroll_dir = -1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True
        elif input_state.right_pressed:
            self._step_pasta(1)
            self._scroll_dir = 1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True

        if not input_state.left and not input_state.right:
            self._scroll_dir = 0

        if input_state.up_pressed:
            self._jump_family(-1)
            consumed = True
        elif input_state.down_pressed:
            self._jump_family(1)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._name_scroll_x = 0.0
            self._meaning_scroll_x = 0.0
            self._sauce_scroll_x = 0.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if self._scroll_dir != 0:
            self._scroll_hold += dt
            if self._scroll_hold >= self.SCROLL_DELAY:
                self._scroll_accum += dt
                while self._scroll_accum >= self.SCROLL_RATE:
                    self._scroll_accum -= self.SCROLL_RATE
                    self._step_pasta(self._scroll_dir)

        if self._switch_flash > 0:
            self._switch_flash = max(0.0, self._switch_flash - dt)

        pasta = self._current()
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, pasta['name'], 48, dt, 18)
        self._meaning_scroll_x = self._advance_scroll(
            self._meaning_scroll_x, pasta['meaning'], 60, dt, 16)
        self._sauce_scroll_x = self._advance_scroll(
            self._sauce_scroll_x, pasta['sauces'], 60, dt, 16)

    def _advance_scroll(self, scroll_x, text, avail_px, dt, speed):
        text_px = len(text) * 4
        if text_px > avail_px:
            scroll_x += dt * speed
            total = self.SCROLL_LEAD_IN + text_px + 20
            if scroll_x >= total:
                scroll_x -= total
        return scroll_x

    def draw(self):
        d = self.display
        d.clear()

        pasta = self._current()
        fam = pasta['family']
        fam_color = FAMILY_COLORS[fam]

        # ── Header: num + name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(pasta['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(fam_color, 0.6))

        name_start_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_start_x, self.NAME_Y,
                                  pasta['name'], fam_color,
                                  self._name_scroll_x, 63 - name_start_x)

        # ── Sep 1 ──
        self._draw_sep(d, self.SEP1_Y)

        # ── Pixel art sprite (centered in sprite area) ──
        sprite = pasta['sprite']
        sprite_h = len(sprite)
        sprite_w = max(len(row) for row in sprite) if sprite else 0
        area_h = self.SPRITE_BOTTOM - self.SPRITE_TOP + 1
        offset_y = self.SPRITE_TOP + (area_h - sprite_h) // 2
        offset_x = (64 - sprite_w) // 2
        for sy, row in enumerate(sprite):
            for sx, color in enumerate(row):
                if color:
                    px = offset_x + sx
                    py = offset_y + sy
                    if 0 <= px < 64 and self.SPRITE_TOP <= py <= self.SPRITE_BOTTOM:
                        d.set_pixel(px, py, color)

        # ── Sep 2 ──
        self._draw_sep(d, self.SEP2_Y)

        # ── Meaning (scrolling, dimmed) ──
        meaning_color = _dim(fam_color, 0.5)
        self._draw_scrolling_text(d, 2, self.MEANING_Y,
                                  pasta['meaning'], meaning_color,
                                  self._meaning_scroll_x, 60)

        # ── Sep 3 ──
        self._draw_sep(d, self.SEP3_Y)

        # ── Sauce pairings (scrolling) ──
        self._draw_scrolling_text(d, 2, self.SAUCE_Y,
                                  pasta['sauces'], TEXT_DIM,
                                  self._sauce_scroll_x, 60)

        # ── Sep 4 ──
        self._draw_sep(d, self.SEP4_Y)

        # ── Region + family name (centered, dimmed) ──
        region_fam = f'{pasta["region"]}  {FAMILIES[fam]}'
        region_color = _dim(fam_color, 0.35)
        region_px = len(region_fam) * 4
        region_x = max(1, (64 - region_px) // 2)
        d.draw_text_small(region_x, self.REGION_Y, region_fam, region_color)

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)

        pos_str = f'{self.pasta_idx + 1}/{len(PASTAS)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)

        fam_list = _FAMILY_PASTAS[fam]
        fam_pos = fam_list.index(self.pasta_idx) + 1 if self.pasta_idx in fam_list else 1
        fam_str = f'{fam_pos}/{len(fam_list)}'
        fam_str_px = len(fam_str) * 4
        d.draw_text_small(63 - fam_str_px, self.FOOT_Y, fam_str, fam_color)

    def _draw_scrolling_text(self, d, start_x, y, text, color, scroll_x, avail_px):
        text_px = len(text) * 4
        if text_px <= avail_px:
            x = start_x + (avail_px - text_px) // 2
            d.draw_text_small(x, y, text, color)
        else:
            lead = self.SCROLL_LEAD_IN
            total = lead + text_px + 20
            sx = int(scroll_x) % total
            end_x = start_x + avail_px
            for cx in range(start_x, min(end_x, 63)):
                px = sx + (cx - start_x) - lead
                if px < 0:
                    continue
                char_idx = px // 4
                col = px % 4
                if col < 3 and 0 <= char_idx < len(text):
                    ch = text[char_idx]
                    self._draw_char_col(d, cx, y, ch, col, color)

    def _draw_sep(self, d, y):
        for x in range(64):
            d.set_pixel(x, y, SEP_COLOR)

    def _draw_char_col(self, d, x, y, ch, col, color):
        glyph = _FONT.get(ch.upper())
        if glyph is None or col >= 3:
            return
        for row_idx, row in enumerate(glyph):
            if row[col] == '1':
                d.set_pixel(x, y + row_idx, color)


_FONT = {
    'A': ['010', '101', '111', '101', '101'],
    'B': ['110', '101', '110', '101', '110'],
    'C': ['011', '100', '100', '100', '011'],
    'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'],
    'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'],
    'H': ['101', '101', '111', '101', '101'],
    'I': ['111', '010', '010', '010', '111'],
    'J': ['001', '001', '001', '101', '010'],
    'K': ['101', '110', '100', '110', '101'],
    'L': ['100', '100', '100', '100', '111'],
    'M': ['101', '111', '111', '101', '101'],
    'N': ['101', '111', '111', '111', '101'],
    'O': ['010', '101', '101', '101', '010'],
    'P': ['110', '101', '110', '100', '100'],
    'Q': ['010', '101', '101', '110', '011'],
    'R': ['110', '101', '110', '101', '101'],
    'S': ['011', '100', '010', '001', '110'],
    'T': ['111', '010', '010', '010', '010'],
    'U': ['101', '101', '101', '101', '011'],
    'V': ['101', '101', '101', '010', '010'],
    'W': ['101', '101', '111', '111', '101'],
    'X': ['101', '101', '010', '101', '101'],
    'Y': ['101', '101', '010', '010', '010'],
    'Z': ['111', '001', '010', '100', '111'],
    ' ': ['000', '000', '000', '000', '000'],
    '-': ['000', '000', '111', '000', '000'],
    '+': ['000', '010', '111', '010', '000'],
    ':': ['000', '010', '000', '010', '000'],
    '/': ['001', '001', '010', '100', '100'],
    '(': ['010', '100', '100', '100', '010'],
    ')': ['010', '001', '001', '001', '010'],
    '&': ['010', '101', '010', '101', '011'],
    "'": ['010', '010', '000', '000', '000'],
    '0': ['111', '101', '101', '101', '111'],
    '1': ['010', '110', '010', '010', '111'],
    '2': ['110', '001', '010', '100', '111'],
    '3': ['110', '001', '010', '001', '110'],
    '4': ['101', '101', '111', '001', '001'],
    '5': ['111', '100', '110', '001', '110'],
    '6': ['011', '100', '110', '101', '010'],
    '7': ['111', '001', '010', '010', '010'],
    '8': ['010', '101', '010', '101', '010'],
    '9': ['010', '101', '011', '001', '110'],
}

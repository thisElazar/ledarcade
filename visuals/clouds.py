"""Clouds - Cloud type reference chart on 64x64 LED matrix.

Educational display showing 13 cloud classifications by altitude and type,
with pixel-art cloud shapes. Two modes: altitude chart view and detail view.
"""

import math
from . import Visual

# ── Color shortcuts ────────────────────────────────────────────────
_ = None  # transparent

# Cloud body colors by altitude
_HW = (255, 255, 255)   # high white
_HB = (200, 220, 255)   # high ice blue
_HL = (180, 200, 240)   # high light
_MW = (230, 230, 240)   # mid white
_MG = (190, 190, 210)   # mid gray
_LG = (150, 150, 170)   # low gray
_LD = (110, 110, 130)   # low dark gray
_NK = (80, 70, 100)     # nimbus dark
_NP = (90, 70, 120)     # nimbus purple
_CB = (70, 60, 100)     # cumulonimbus base dark
_RN = (100, 140, 220)   # rain blue
_AN = (200, 210, 230)   # anvil light

# ── Altitude bands ─────────────────────────────────────────────────
BANDS = ["HIGH", "MID", "LOW", "VERT"]
BAND_COLORS = [
    (180, 200, 255),  # HIGH = ice blue
    (200, 200, 220),  # MID = silver
    (150, 150, 170),  # LOW = gray
    (220, 180, 100),  # VERT = amber
]

HEADER_BG = (10, 15, 30)
TEXT_DIM = (80, 90, 120)
SEP_COLOR = (30, 40, 65)

# ── Sky gradient colors (top to bottom) ────────────────────────────
SKY_TOP = (8, 12, 40)
SKY_BOT = (40, 60, 110)

# ── Pixel-art sprites ──────────────────────────────────────────────

# Cirrus: thin wispy diagonal streaks
_CIRRUS = [
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_HW,_HB,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_HW,_HB,_HL,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_HB,_HW,_HL,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_HB,_HL,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_HW,_HB,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_HB,_HW,_HL,_,_,_,_],
    [_,_,_HW,_HB,_HL,_,_,_,_HB,_HW,_HL,_,_,_,_,_,_,_,_,_],
    [_HB,_HL,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
]

# Cirrocumulus: small white patches / ripples
_CIRROCUMULUS = [
    [_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_,_],
]

# Cirrostratus: thin sheet / haze
_CIRROSTRATUS = [
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_HL,_HL,_HB,_HB,_HB,_HL,_HL,_HB,_HB,_HL,_HL,_HB,_HB,_HB,_HL,_HL,_HB,_,_],
    [_HL,_HB,_HB,_HW,_HW,_HW,_HB,_HB,_HW,_HW,_HB,_HB,_HW,_HW,_HW,_HB,_HB,_HW,_HL,_],
    [_,_HL,_HB,_HB,_HW,_HW,_HB,_HW,_HW,_HB,_HB,_HW,_HW,_HB,_HW,_HW,_HB,_HL,_,_],
    [_,_,_HL,_HL,_HB,_HB,_HL,_HB,_HB,_HL,_HL,_HB,_HB,_HL,_HB,_HB,_HL,_,_,_],
    [_,_,_,_,_HL,_HL,_,_HL,_HL,_,_,_HL,_HL,_,_HL,_HL,_,_,_,_],
]

# Altostratus: gray/blue sheet
_ALTOSTRATUS = [
    [_,_,_MG,_MG,_MW,_MW,_MW,_MG,_MG,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_MG,_MG,_,_],
    [_MG,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MG,_],
    [_MW,_MW,_MW,_MG,_MW,_MW,_MG,_MW,_MW,_MG,_MW,_MW,_MW,_MG,_MW,_MW,_MG,_MW,_MW,_],
    [_MG,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MG,_],
    [_,_,_MG,_MG,_MW,_MW,_MW,_MG,_MG,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_MG,_MG,_,_],
]

# Altocumulus: white/gray rounded patches
_ALTOCUMULUS = [
    [_,_,_,_MW,_MW,_,_,_,_,_MW,_MW,_,_,_,_,_MW,_MW,_,_,_],
    [_,_,_MW,_MW,_MW,_MW,_,_,_MW,_MW,_MW,_MW,_,_,_MW,_MW,_MW,_MW,_,_],
    [_,_MW,_MW,_MG,_MG,_MW,_,_MW,_MW,_MG,_MG,_MW,_,_MW,_MW,_MG,_MG,_MW,_,_],
    [_,_,_MG,_MG,_MG,_MG,_,_,_MG,_MG,_MG,_MG,_,_,_MG,_MG,_MG,_MG,_,_],
    [_,_,_,_MG,_MG,_,_,_,_,_MG,_MG,_,_,_,_,_MG,_MG,_,_,_],
]

# Stratus: uniform gray layer
_STRATUS = [
    [_,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_],
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG],
    [_,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_],
]

# Stratocumulus: lumpy gray/white layer
_STRATOCUMULUS = [
    [_,_,_,_LG,_MW,_MW,_LG,_,_,_LG,_MW,_MW,_LG,_,_,_LG,_MW,_LG,_,_],
    [_,_LG,_MW,_MW,_MW,_MW,_MW,_LG,_LG,_MW,_MW,_MW,_MW,_LG,_LG,_MW,_MW,_MW,_LG,_],
    [_LG,_MW,_MW,_LG,_LG,_MW,_MW,_MW,_MW,_MW,_LG,_LG,_MW,_MW,_MW,_MW,_LG,_MW,_MW,_LG],
    [_LG,_LG,_LG,_LD,_LD,_LG,_LG,_LG,_LG,_LG,_LD,_LD,_LG,_LG,_LG,_LG,_LD,_LG,_LG,_LG],
    [_,_LD,_LD,_LD,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_],
]

# Nimbostratus: thick dark band with rain lines
_NIMBOSTRATUS = [
    [_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK],
    [_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK],
    [_NP,_NK,_NK,_NK,_NP,_NK,_NK,_NK,_NK,_NP,_NK,_NK,_NK,_NP,_NK,_NK,_NK,_NK,_NP,_NK],
    [_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK],
    [_,_RN,_,_,_,_RN,_,_,_RN,_,_,_,_RN,_,_,_RN,_,_,_,_RN],
    [_,_,_,_RN,_,_,_RN,_,_,_,_RN,_,_,_,_,_,_RN,_,_,_],
    [_,_,_,_,_,_,_,_,_,_RN,_,_,_RN,_,_,_,_,_,_RN,_],
    [_,_RN,_,_,_,_,_,_RN,_,_,_,_,_,_,_RN,_,_,_,_,_],
]

# Cumulus: classic puffy cotton ball
_CUMULUS = [
    [_,_,_,_,_,_,_,_HW,_HW,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_,_,_],
    [_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_],
    [_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_],
    [_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_],
    [_,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_,_,_,_,_],
    [_,_,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_,_,_,_,_,_],
]

# Cumulonimbus: tall tower with anvil top
_CUMULONIMBUS = [
    [_,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_],
    [_,_,_AN,_AN,_AN,_AN,_HW,_HW,_HW,_HW,_HW,_HW,_AN,_AN,_AN,_AN,_AN,_,_,_],
    [_,_,_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_],
    [_,_,_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_],
    [_,_,_,_,_MW,_MW,_HW,_HW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_,_,_],
    [_,_,_,_,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_,_,_,_,_,_,_],
    [_,_,_,_,_MG,_MG,_MW,_MW,_MW,_MW,_MW,_MG,_MG,_,_,_,_,_,_,_],
    [_,_,_,_,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_,_,_,_,_,_,_],
    [_,_,_,_,_LG,_LG,_MG,_MG,_MG,_MG,_MG,_LG,_LG,_,_,_,_,_,_,_],
    [_,_,_,_,_NK,_NK,_CB,_CB,_CB,_CB,_CB,_NK,_NK,_,_,_,_,_,_,_],
    [_,_,_,_,_CB,_NP,_NK,_NK,_NK,_NK,_NK,_NP,_CB,_,_,_,_,_,_,_],
    [_,_,_RN,_,_,_,_RN,_,_,_RN,_,_,_,_RN,_,_,_,_RN,_,_],
    [_,_,_,_,_RN,_,_,_,_RN,_,_,_RN,_,_,_,_RN,_,_,_,_],
]

# Lenticular: smooth lens/disc shape
_LENTICULAR = [
    [_,_,_,_,_,_,_,_,_MW,_MW,_MW,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_MW,_MW,_HW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_,_,_],
    [_,_,_,_MW,_MW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_,_],
    [_,_,_MW,_MW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_],
    [_,_,_,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_MG,_MG,_MW,_MW,_,_,_,_,_,_],
    [_,_,_,_,_,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_,_,_,_,_,_,_,_],
]

# Mammatus: pouch-like bulges underneath
_MAMMATUS = [
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LD,_LD,_LG,_,_LG,_LD,_LD,_LG,_,_LG,_LD,_LD,_LG,_,_LG,_LD,_LD,_LG,_],
    [_,_LD,_LD,_,_,_,_LD,_LD,_,_,_,_LD,_LD,_,_,_,_LD,_LD,_,_],
    [_,_,_NK,_,_,_,_,_NK,_,_,_,_,_NK,_,_,_,_,_NK,_,_],
]

# Fog: low stratus at ground level
_FOG = [
    [_,_,_,_LG,_LG,_LG,_LG,_,_,_LG,_LG,_LG,_,_,_LG,_LG,_LG,_LG,_,_],
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD],
    [_,_LD,_LD,_,_,_LD,_LD,_,_,_LD,_LD,_,_,_LD,_LD,_,_,_LD,_LD,_],
    [_,_,_LD,_,_,_,_LD,_,_,_,_LD,_,_,_,_LD,_,_,_,_LD,_],
]


# ── Lightning flash color ─────────────────────────────────────────
_LF = (255, 255, 180)  # lightning flash yellow-white

# ── Animation frames (2-3 per cloud) ─────────────────────────────

# Cumulonimbus frame 2: lightning flash in base
_CUMULONIMBUS_2 = [
    [_,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_AN,_],
    [_,_,_AN,_AN,_AN,_AN,_HW,_HW,_HW,_HW,_HW,_HW,_AN,_AN,_AN,_AN,_AN,_,_,_],
    [_,_,_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_],
    [_,_,_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_],
    [_,_,_,_,_MW,_MW,_HW,_HW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_,_,_],
    [_,_,_,_,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_MW,_,_,_,_,_,_,_],
    [_,_,_,_,_MG,_MG,_MW,_MW,_MW,_MW,_MW,_MG,_MG,_,_,_,_,_,_,_],
    [_,_,_,_,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_,_,_,_,_,_,_],
    [_,_,_,_,_LG,_LG,_MG,_MG,_MG,_MG,_MG,_LG,_LG,_,_,_,_,_,_,_],
    [_,_,_,_,_NK,_NK,_LF,_CB,_LF,_CB,_LF,_NK,_NK,_,_,_,_,_,_,_],
    [_,_,_,_,_CB,_NP,_NK,_LF,_NK,_LF,_NK,_NP,_CB,_,_,_,_,_,_,_],
    [_,_,_RN,_,_,_,_RN,_,_LF,_RN,_,_,_,_RN,_,_,_,_RN,_,_],
    [_,_,_,_,_RN,_,_,_,_RN,_,_,_RN,_,_,_,_RN,_,_,_,_],
]

# Cirrus frame 2: wisps extend/curl
_CIRRUS_2 = [
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_HW,_HB,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_HW,_HB,_HL,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_HB,_HW,_HL,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_HB,_HL,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_HW,_HB,_HL,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_HB,_HW,_HL,_,_,_,_,_],
    [_,_HW,_HB,_HL,_,_,_,_HB,_HW,_HL,_,_,_,_,_,_,_,_,_,_],
    [_HL,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
]

# Cirrocumulus frame 2: ripple offset
_CIRROCUMULUS_2 = [
    [_,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_HW,_,_,_HB,_,_,_],
]

# Cirrostratus frame 2: brightness shimmer
_HB2 = (210, 230, 255)  # slightly brighter ice
_CIRROSTRATUS_2 = [
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
    [_,_HL,_HL,_HB2,_HB2,_HB2,_HL,_HL,_HB,_HB,_HL,_HL,_HB2,_HB2,_HB2,_HL,_HL,_HB,_,_],
    [_HL,_HB2,_HB2,_HW,_HW,_HW,_HB2,_HB2,_HW,_HW,_HB,_HB,_HW,_HW,_HW,_HB2,_HB2,_HW,_HL,_],
    [_,_HL,_HB,_HB,_HW,_HW,_HB2,_HW,_HW,_HB,_HB,_HW,_HW,_HB2,_HW,_HW,_HB,_HL,_,_],
    [_,_,_HL,_HL,_HB,_HB,_HL,_HB2,_HB2,_HL,_HL,_HB,_HB,_HL,_HB2,_HB2,_HL,_,_,_],
    [_,_,_,_,_HL,_HL,_,_HL,_HL,_,_,_HL,_HL,_,_HL,_HL,_,_,_,_],
]

# Altostratus frame 2: brightness undulation
_MW2 = (240, 240, 250)  # brighter mid white
_ALTOSTRATUS_2 = [
    [_,_,_MG,_MG,_MW2,_MW2,_MW2,_MG,_MG,_MW,_MW,_MG,_MG,_MW2,_MW2,_MW2,_MG,_MG,_,_],
    [_MG,_MW2,_MW2,_MW2,_MW2,_MW2,_MW,_MW,_MW,_MW,_MW,_MW,_MW2,_MW2,_MW2,_MW2,_MW2,_MW,_MG,_],
    [_MW2,_MW2,_MW2,_MG,_MW2,_MW,_MG,_MW,_MW,_MG,_MW,_MW2,_MW2,_MG,_MW2,_MW,_MG,_MW,_MW,_],
    [_MG,_MW,_MW,_MW,_MW,_MW,_MW2,_MW2,_MW2,_MW2,_MW2,_MW,_MW,_MW,_MW,_MW,_MW2,_MW2,_MG,_],
    [_,_,_MG,_MG,_MW,_MW,_MW2,_MG,_MG,_MW2,_MW2,_MG,_MG,_MW,_MW,_MW2,_MG,_MG,_,_],
]

# Altocumulus frame 2: patches drift apart
_ALTOCUMULUS_2 = [
    [_,_,_,_MW,_MW,_,_,_,_,_,_MW,_MW,_,_,_,_MW,_MW,_,_,_],
    [_,_,_MW,_MW,_MW,_MW,_,_,_,_MW,_MW,_MW,_MW,_,_MW,_MW,_MW,_MW,_,_],
    [_,_MW,_MW,_MG,_MG,_MW,_,_,_MW,_MW,_MG,_MG,_MW,_,_MW,_MW,_MG,_MG,_MW,_],
    [_,_,_MG,_MG,_MG,_MG,_,_,_,_MG,_MG,_MG,_MG,_,_,_MG,_MG,_MG,_MG,_],
    [_,_,_,_MG,_MG,_,_,_,_,_,_MG,_MG,_,_,_,_,_MG,_MG,_,_],
]

# Cumulus frame 2: top billows up (extra top pixels)
_CUMULUS_2 = [
    [_,_,_,_,_,_,_,_HW,_HW,_HW,_,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_,_,_],
    [_,_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_,_],
    [_,_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_,_],
    [_,_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_,_],
    [_,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_,_,_,_,_],
    [_,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_,_,_,_,_],
    [_,_,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_,_,_,_,_,_],
]

# Mammatus frame 2: pouches sag further
_MAMMATUS_2 = [
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LD,_LD,_LG,_,_LG,_LD,_LD,_LG,_,_LG,_LD,_LD,_LG,_,_LG,_LD,_LD,_LG,_],
    [_,_LD,_LD,_,_,_,_LD,_LD,_,_,_,_LD,_LD,_,_,_,_LD,_LD,_,_],
    [_,_LD,_NK,_LD,_,_,_LD,_NK,_LD,_,_,_LD,_NK,_LD,_,_,_LD,_NK,_LD,_],
    [_,_,_NK,_,_,_,_,_NK,_,_,_,_,_NK,_,_,_,_,_NK,_,_],
]

# Nimbostratus frame 2: rain streaks shift
_NIMBOSTRATUS_2 = [
    [_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK],
    [_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK,_NP,_NK,_NK],
    [_NP,_NK,_NK,_NK,_NP,_NK,_NK,_NK,_NK,_NP,_NK,_NK,_NK,_NP,_NK,_NK,_NK,_NK,_NP,_NK],
    [_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK,_NK],
    [_,_,_,_RN,_,_,_RN,_,_,_,_RN,_,_,_,_,_,_RN,_,_,_],
    [_,_RN,_,_,_,_,_,_,_RN,_,_,_,_RN,_,_,_RN,_,_,_,_RN],
    [_,_,_,_,_RN,_,_,_,_,_,_,_RN,_,_,_RN,_,_,_,_,_],
    [_,_,_,_,_,_RN,_,_,_RN,_,_,_,_,_RN,_,_,_RN,_,_],
]

# Stratocumulus frame 2: lumps morph (alternate shading)
_STRATOCUMULUS_2 = [
    [_,_,_LG,_MW,_MW,_MW,_,_,_,_LG,_MW,_MW,_LG,_,_,_LG,_MW,_MW,_,_],
    [_,_LG,_MW,_MW,_MW,_MW,_MW,_LG,_LG,_MW,_MW,_MW,_MW,_LG,_LG,_MW,_MW,_MW,_LG,_],
    [_LG,_MW,_LG,_MW,_MW,_LG,_MW,_MW,_MW,_MW,_MW,_LG,_MW,_MW,_MW,_LG,_MW,_MW,_MW,_LG],
    [_LG,_LG,_LD,_LG,_LG,_LD,_LG,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LG],
    [_,_LD,_LD,_LD,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_],
]

# Stratus frame 2: drizzle drops appear below
_STRATUS_2 = [
    [_,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_],
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG],
    [_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG,_LG,_LG,_LD,_LG],
    [_,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_,_,_LD,_LD,_LD,_],
    [_,_,_RN,_,_,_,_,_,_RN,_,_,_,_,_RN,_,_,_,_RN,_,_],
]

# Fog frame 2: edge wisps fade (lighter edges)
_FG2 = (130, 130, 150)  # faded fog
_FOG_2 = [
    [_,_,_,_FG2,_LG,_LG,_FG2,_,_,_FG2,_LG,_FG2,_,_,_FG2,_LG,_LG,_FG2,_,_],
    [_FG2,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_LG,_FG2],
    [_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD,_LD,_LG,_LG,_LD],
    [_,_LD,_LD,_,_,_LD,_LD,_,_,_LD,_LD,_,_,_LD,_LD,_,_,_LD,_LD,_],
    [_,_,_FG2,_,_,_,_FG2,_,_,_,_FG2,_,_,_,_FG2,_,_,_,_FG2,_],
]

# Lenticular frame 2: shifted up 1 row (vertical oscillation)
_LENTICULAR_2 = [
    [_,_,_,_,_,_,_MW,_MW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_,_,_],
    [_,_,_,_MW,_MW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_,_],
    [_,_,_MW,_MW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_HW,_MW,_MW,_,_,_,_,_],
    [_,_,_,_MW,_MW,_MG,_MG,_MW,_MW,_MW,_MG,_MG,_MW,_MW,_,_,_,_,_,_],
    [_,_,_,_,_,_MG,_MG,_MG,_MG,_MG,_MG,_MG,_,_,_,_,_,_,_,_],
    [_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_,_],
]

# ── Animation frame lists ────────────────────────────────────────
_FRAMES = {
    'CUMULONIMBUS': [_CUMULONIMBUS, _CUMULONIMBUS, _CUMULONIMBUS_2],
    'CIRRUS':       [_CIRRUS, _CIRRUS_2],
    'CIRROCUMULUS':  [_CIRROCUMULUS, _CIRROCUMULUS_2],
    'CIRROSTRATUS':  [_CIRROSTRATUS, _CIRROSTRATUS_2],
    'LENTICULAR':   [_LENTICULAR, _LENTICULAR_2],
    'ALTOSTRATUS':  [_ALTOSTRATUS, _ALTOSTRATUS_2],
    'ALTOCUMULUS':  [_ALTOCUMULUS, _ALTOCUMULUS_2],
    'CUMULUS':      [_CUMULUS, _CUMULUS_2],
    'MAMMATUS':     [_MAMMATUS, _MAMMATUS_2],
    'NIMBOSTRATUS': [_NIMBOSTRATUS, _NIMBOSTRATUS_2],
    'STRATOCUMULUS': [_STRATOCUMULUS, _STRATOCUMULUS_2],
    'STRATUS':      [_STRATUS, _STRATUS_2],
    'FOG':          [_FOG, _FOG_2],
}

ANIM_PERIOD = 0.8  # seconds per frame

# ── Cloud data (ordered by descending max altitude) ───────────────
CLOUDS = [
    # ── 60,000 ft — towering ──────────────────────────
    {'name': 'CUMULONIMBUS', 'abbr': 'Cb', 'band': 3, 'num': 1,
     'alt': '2000-60000 FT',
     'desc': 'TOWERING THUNDERSTORM CLOUD / ANVIL TOP / LIGHTNING HAIL TORNADOES',
     'precip': 'STORM',
     'chart_y': 4,
     'sprite': _CUMULONIMBUS},

    # ── HIGH (band 0) — 40,000 ft ─────────────────────
    {'name': 'CIRRUS', 'abbr': 'Ci', 'band': 0, 'num': 2,
     'alt': '20000-40000 FT',
     'desc': 'THIN WISPY STREAKS OF ICE CRYSTALS / MARES TAILS / FAIR WEATHER',
     'precip': 'NONE',
     'chart_y': 4,
     'sprite': _CIRRUS},
    {'name': 'CIRROCUMULUS', 'abbr': 'Cc', 'band': 0, 'num': 3,
     'alt': '20000-40000 FT',
     'desc': 'SMALL WHITE PATCHES AND RIPPLES / MACKEREL SKY / ICE CRYSTALS',
     'precip': 'NONE',
     'chart_y': 8,
     'sprite': _CIRROCUMULUS},
    {'name': 'CIRROSTRATUS', 'abbr': 'Cs', 'band': 0, 'num': 4,
     'alt': '20000-40000 FT',
     'desc': 'THIN SHEET / SUN AND MOON HALOS / APPROACHING WARM FRONT',
     'precip': 'NONE',
     'chart_y': 13,
     'sprite': _CIRROSTRATUS},

    # ── 40,000 ft — mountain wave ─────────────────────
    {'name': 'LENTICULAR', 'abbr': 'Lc', 'band': 3, 'num': 5,
     'alt': '6500-40000 FT',
     'desc': 'LENS OR UFO SHAPED / FORMS NEAR MOUNTAINS / STANDING WAVE CLOUD',
     'precip': 'NONE',
     'chart_y': 21,
     'sprite': _LENTICULAR},

    # ── MID (band 1) — 20,000 ft ──────────────────────
    {'name': 'ALTOSTRATUS', 'abbr': 'As', 'band': 1, 'num': 6,
     'alt': '6500-20000 FT',
     'desc': 'GRAY-BLUE SHEET / SUN DIMLY VISIBLE / RAIN OR SNOW COMING',
     'precip': 'RAIN',
     'chart_y': 21,
     'sprite': _ALTOSTRATUS},
    {'name': 'ALTOCUMULUS', 'abbr': 'Ac', 'band': 1, 'num': 7,
     'alt': '6500-20000 FT',
     'desc': 'WHITE-GRAY PATCHES / ROUNDED MASSES / FAIR BUT MAY PRECEDE STORMS',
     'precip': 'NONE',
     'chart_y': 27,
     'sprite': _ALTOCUMULUS},

    # ── 20,000 ft — vertical development ──────────────
    {'name': 'CUMULUS', 'abbr': 'Cu', 'band': 3, 'num': 8,
     'alt': '2000-20000 FT',
     'desc': 'PUFFY WHITE FAIR WEATHER CLOUDS / FLAT BASES / COTTON BALLS',
     'precip': 'NONE',
     'chart_y': 36,
     'sprite': _CUMULUS},
    {'name': 'MAMMATUS', 'abbr': 'Ma', 'band': 3, 'num': 9,
     'alt': '6500-20000 FT',
     'desc': 'POUCH-LIKE BULGES UNDERNEATH / SEVERE WEATHER INDICATOR',
     'precip': 'NONE',
     'chart_y': 27,
     'sprite': _MAMMATUS},

    # ── LOW (band 2) — 10,000 ft and below ────────────
    {'name': 'NIMBOSTRATUS', 'abbr': 'Ns', 'band': 2, 'num': 10,
     'alt': 'SURFACE-10000 FT',
     'desc': 'THICK DARK GRAY / CONTINUOUS RAIN OR SNOW / NO VISIBLE SUN',
     'precip': 'RAIN/SNOW',
     'chart_y': 48,
     'sprite': _NIMBOSTRATUS},
    {'name': 'STRATOCUMULUS', 'abbr': 'Sc', 'band': 2, 'num': 11,
     'alt': 'SURFACE-6500 FT',
     'desc': 'LUMPY GRAY-WHITE LAYER / MOST COMMON CLOUD TYPE ON EARTH',
     'precip': 'DRIZZLE',
     'chart_y': 42,
     'sprite': _STRATOCUMULUS},
    {'name': 'STRATUS', 'abbr': 'St', 'band': 2, 'num': 12,
     'alt': 'SURFACE-6500 FT',
     'desc': 'UNIFORM GRAY LAYER / DRIZZLE / OVERCAST DAYS / FOG THAT LIFTS',
     'precip': 'DRIZZLE',
     'chart_y': 36,
     'sprite': _STRATUS},

    # ── Surface ───────────────────────────────────────
    {'name': 'FOG', 'abbr': 'Fg', 'band': 3, 'num': 13,
     'alt': 'SURFACE',
     'desc': 'STRATUS AT GROUND LEVEL / VISIBILITY BELOW 1 KM / DEW POINT MET',
     'precip': 'MIST',
     'chart_y': 55,
     'sprite': _FOG},
]

# Build per-band index
_BAND_CLOUDS = [[] for _ in range(len(BANDS))]
for _i, _c in enumerate(CLOUDS):
    _BAND_CLOUDS[_c['band']].append(_i)

# Precipitation icons (small symbols)
PRECIP_COLORS = {
    'NONE': (80, 100, 80),
    'DRIZZLE': (100, 140, 200),
    'RAIN': (80, 120, 220),
    'RAIN/SNOW': (140, 140, 220),
    'SNOW': (200, 200, 240),
    'STORM': (200, 100, 255),
    'MIST': (140, 140, 160),
}


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def _lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB colors."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


class Clouds(Visual):
    name = "CLOUDS"
    description = "Cloud type reference"
    category = "nature"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Detail view layout Y positions
    NAME_Y = 1
    SEP1_Y = 7
    ABBR_Y = 9
    SEP2_Y = 15
    SPRITE_TOP = 16
    SPRITE_BOTTOM = 37
    SEP3_Y = 38
    ALT_Y = 40
    SEP4_Y = 46
    DESC_Y = 48
    FOOT_SEP_Y = 57
    FOOT_Y = 59

    # Wind speeds per altitude band (px/sec at 1x time)
    # Realistic ratios: jet stream ~6x, mid ~3x, low ~1x, vert ~2x
    WIND_SPEEDS = [8.0, 4.0, 1.5, 2.5]  # HIGH, MID, LOW, VERT

    # Time speed presets
    TIME_SPEEDS = [0.25, 0.5, 1.0, 2.0, 4.0]
    TIME_LABELS = ['1/4X', '1/2X', '1X', '2X', '4X']

    def reset(self):
        self.time = 0.0
        self.idx = 0
        self.mode = 0  # 0 = sky, 1 = detail
        self._name_scroll_x = 0.0
        self._desc_scroll_x = 0.0
        self.overlay_timer = 2.0
        self._wind_time = 0.0       # accumulated wind time
        self._speed_idx = 2         # index into TIME_SPEEDS (default 1x)
        self._anim_timer = 0.0      # animation frame timer
        self._anim_frame = 0        # current animation frame index

    def _current(self):
        return CLOUDS[self.idx % len(CLOUDS)]

    def _step(self, direction):
        self.idx = (self.idx + direction) % len(CLOUDS)
        self._name_scroll_x = 0.0
        self._desc_scroll_x = 0.0
        self.overlay_timer = 1.5

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: toggle sky/detail
        if input_state.action_l or input_state.action_r:
            self.mode = 1 - self.mode
            self._name_scroll_x = 0.0
            self._desc_scroll_x = 0.0
            self.overlay_timer = 0.0
            consumed = True

        # Up/Down: cycle through cloud list
        if input_state.up_pressed:
            self._step(-1)
            consumed = True
        elif input_state.down_pressed:
            self._step(1)
            consumed = True

        # Left/Right: adjust time speed
        if input_state.left_pressed:
            self._speed_idx = max(0, self._speed_idx - 1)
            self.overlay_timer = 1.2
            consumed = True
        elif input_state.right_pressed:
            self._speed_idx = min(len(self.TIME_SPEEDS) - 1, self._speed_idx + 1)
            self.overlay_timer = 1.2
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self._wind_time += dt * self.TIME_SPEEDS[self._speed_idx]

        # Advance animation frame
        self._anim_timer += dt
        if self._anim_timer >= ANIM_PERIOD:
            self._anim_timer -= ANIM_PERIOD
            self._anim_frame += 1

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        c = self._current()
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, c['name'], 48, dt, 18)
        self._desc_scroll_x = self._advance_scroll(
            self._desc_scroll_x, c['desc'], 60, dt, 16)

    def _advance_scroll(self, scroll_x, text, avail_px, dt, speed):
        text_px = len(text) * 4
        if text_px > avail_px:
            scroll_x += dt * speed
            total = self.SCROLL_LEAD_IN + text_px + 20
            if scroll_x >= total:
                scroll_x -= total
        return scroll_x

    def draw(self):
        if self.mode == 0:
            self._draw_chart()
        else:
            self._draw_detail()

    # ── Sky View (drifting clouds) ──────────────────────────────────

    # Base x-offsets so clouds start spread across the sky
    _CLOUD_OFFSETS = [0, 15, 40, 55, 25, 50, 10, 35, 60, 5, 45, 20, 30]

    def _draw_chart(self):
        d = self.display
        d.clear()

        # Sky gradient background
        for y in range(57):
            t = y / 56.0
            bg = _lerp_color(SKY_TOP, SKY_BOT, t)
            for x in range(64):
                d.set_pixel(x, y, bg)

        # Highlight active altitude band
        selected = self._current()
        band = selected['band']
        band_color = BAND_COLORS[band]
        # Band Y ranges: HIGH 0-17, MID 19-33, LOW 35-56
        _BAND_RANGES = {0: (0, 17), 1: (19, 33), 2: (35, 56)}
        if band in _BAND_RANGES:
            by0, by1 = _BAND_RANGES[band]
        else:
            # VERT: highlight around the cloud's chart_y ± sprite height
            sprite = selected['sprite']
            sh = len(sprite) if sprite else 6
            by0 = max(0, selected['chart_y'] - 1)
            by1 = min(56, selected['chart_y'] + sh + 1)
        glow = 0.15
        for y in range(by0, by1 + 1):
            for x in range(64):
                r, g, b = d.get_pixel(x, y)
                r = min(255, int(r + band_color[0] * glow))
                g = min(255, int(g + band_color[1] * glow))
                b = min(255, int(b + band_color[2] * glow))
                d.set_pixel(x, y, (r, g, b))

        # Dashed altitude separator lines
        for sep_y in [18, 34]:
            for x in range(0, 64, 4):
                d.set_pixel(x, sep_y, _dim(SEP_COLOR, 0.4))
                if x + 1 < 64:
                    d.set_pixel(x + 1, sep_y, _dim(SEP_COLOR, 0.4))

        # Draw each cloud drifting across the sky
        for ci, cloud in enumerate(CLOUDS):
            cb = cloud['band']
            chart_y = cloud['chart_y']

            # Compute drift position: base offset + wind * time, wrap at 64+sprite_w
            sp = cloud['sprite']
            sprite_w = max(len(row) for row in sp) if sp else 8
            wrap = 64 + sprite_w + 10  # total wrap distance
            wind = self.WIND_SPEEDS[cb]
            base = self._CLOUD_OFFSETS[ci % len(self._CLOUD_OFFSETS)]
            drift_x = int(base + self._wind_time * wind) % wrap - sprite_w - 5

            is_selected = (ci == self.idx)
            self._draw_sky_sprite(d, drift_x, chart_y, cloud, is_selected)

        # Bottom info bar
        d.draw_rect(0, 57, 64, 7, HEADER_BG)
        self._draw_sep(d, 57)

        name = selected['name']
        abbr = selected['abbr']

        label = f'{name} ({abbr})'
        label_px = len(label) * 4
        label_x = max(1, (64 - label_px) // 2)
        d.draw_text_small(label_x, 59, label, band_color)

        # Speed indicator (top-right)
        speed_label = self.TIME_LABELS[self._speed_idx]
        spd_px = len(speed_label) * 4
        d.draw_text_small(63 - spd_px, 1, speed_label, (80, 100, 80))

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            if self.overlay_timer > 0.8:
                # Just changed cloud — show cloud name
                oc = (int(band_color[0] * alpha),
                      int(band_color[1] * alpha),
                      int(band_color[2] * alpha))
                d.draw_text_small(2, 1, name, oc)
            else:
                # Speed change overlay
                oc = (int(120 * alpha), int(160 * alpha), int(120 * alpha))
                d.draw_text_small(2, 1, speed_label, oc)

    def _get_sprite(self, cloud):
        """Get the current animation frame for a cloud."""
        frames = _FRAMES.get(cloud['name'])
        if frames:
            return frames[self._anim_frame % len(frames)]
        return cloud['sprite']

    def _draw_sky_sprite(self, d, sx, sy, cloud, selected):
        """Draw a cloud sprite at (sx, sy) on the sky, clipped to sky region."""
        sprite = self._get_sprite(cloud)
        sprite_h = len(sprite)
        sprite_w = max(len(row) for row in sprite) if sprite else 0

        # Dim factor for non-selected clouds
        dim_f = 1.0 if selected else 0.45

        for row_idx, row in enumerate(sprite):
            py = sy + row_idx
            if py < 0 or py >= 57:
                continue
            for col_idx, color in enumerate(row):
                if color is None:
                    continue
                px = sx + col_idx
                if px < 0 or px >= 64:
                    continue
                if dim_f < 1.0:
                    color = _dim(color, dim_f)
                d.set_pixel(px, py, color)

        # Selection indicator: bright dot below sprite center
        if selected:
            blink = 0.6 + 0.4 * math.sin(self.time * 4)
            cx = sx + sprite_w // 2
            iy = sy + sprite_h + 1
            if 0 <= cx < 64 and 0 <= iy < 57:
                ind = (int(255 * blink), int(255 * blink), int(100 * blink))
                d.set_pixel(cx, iy, ind)

    # ── Detail View ────────────────────────────────────────────────

    def _draw_detail(self):
        d = self.display
        d.clear()

        cloud = self._current()
        band = cloud['band']
        band_color = BAND_COLORS[band]

        # ── Header: name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(cloud['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(band_color, 0.6))

        name_start_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_start_x, self.NAME_Y,
                                  cloud['name'], band_color,
                                  self._name_scroll_x, 63 - name_start_x)

        # ── Sep 1 ──
        self._draw_sep(d, self.SEP1_Y)

        # ── Abbreviation + precipitation ──
        abbr_str = f'({cloud["abbr"]})'
        precip = cloud['precip']
        info_str = f'{abbr_str}  {precip}'
        info_color = _dim(band_color, 0.5)
        precip_color = PRECIP_COLORS.get(precip, TEXT_DIM)

        # Draw abbreviation
        d.draw_text_small(2, self.ABBR_Y, abbr_str, info_color)
        # Draw precipitation right-aligned
        precip_px = len(precip) * 4
        d.draw_text_small(62 - precip_px, self.ABBR_Y, precip, precip_color)

        # ── Sep 2 ──
        self._draw_sep(d, self.SEP2_Y)

        # ── Pixel art sprite (centered in sprite area) ──
        sprite = self._get_sprite(cloud)
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

        # ── Sep 3 ──
        self._draw_sep(d, self.SEP3_Y)

        # ── Altitude range (centered) ──
        alt = cloud['alt']
        alt_color = _dim(band_color, 0.5)
        alt_px = len(alt) * 4
        alt_x = max(1, (64 - alt_px) // 2)
        d.draw_text_small(alt_x, self.ALT_Y, alt, alt_color)

        # ── Sep 4 ──
        self._draw_sep(d, self.SEP4_Y)

        # ── Description (scrolling) ──
        self._draw_scrolling_text(d, 2, self.DESC_Y,
                                  cloud['desc'], TEXT_DIM,
                                  self._desc_scroll_x, 60)

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)

        pos_str = f'{self.idx + 1}/{len(CLOUDS)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)

        band_list = _BAND_CLOUDS[band]
        band_pos = band_list.index(self.idx) + 1 if self.idx in band_list else 1
        band_str = f'{BANDS[band]}'
        band_str_px = len(band_str) * 4
        d.draw_text_small(63 - band_str_px, self.FOOT_Y, band_str, band_color)

    # ── Shared drawing helpers ─────────────────────────────────────

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
    '.': ['000', '000', '000', '000', '010'],
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

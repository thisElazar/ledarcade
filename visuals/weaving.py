"""
WEAVING — World textile traditions on 64x64 LED matrix.
========================================================
Top-down view of fabric showing how warp and weft threads interlace.
Weft rows animate in one at a time, building the pattern from top to bottom.
46 weave structures spanning 7000 years and every inhabited continent,
paired with 18 color palettes from global textile traditions.

Controls:
  Left/Right - Adjust weaving speed
  Up/Down    - Cycle color palette
  Action     - Next weave technique
"""

import math
from . import Visual

# ---------------------------------------------------------------------------
# Thread geometry — each logical thread is THREAD_PX pixels square
# 64 / 4 = 16 threads across and down
# ---------------------------------------------------------------------------
THREAD_PX = 4
GRID = 64 // THREAD_PX  # 16

# ---------------------------------------------------------------------------
# Speed control
# ---------------------------------------------------------------------------
SPEEDS = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
SPEED_LABELS = ['.5X', '.75X', '1X', '1.5X', '2X', '3X']
DEFAULT_SPEED_IDX = 2
BASE_ROWS_PER_SEC = 3.0

# ---------------------------------------------------------------------------
# Helper: tile a small draft to fill the grid
# ---------------------------------------------------------------------------
def _tile(draft, cols, rows):
    ph = len(draft)
    pw = len(draft[0])
    return [[draft[r % ph][c % pw] for c in range(cols)] for r in range(rows)]


# ═══════════════════════════════════════════════════════════════════
# WEAVE DRAFTS — True = warp on top, False = weft on top
# Organized by cultural origin / historical period
# ═══════════════════════════════════════════════════════════════════

# ── Foundational (universal, Neolithic onward) ────────────────────

# Plain/Tabby: oldest known weave, every culture on Earth
_PLAIN = [
    [True, False],
    [False, True],
]

# Basket 2/2: doubled plain weave, universal
_BASKET = [
    [True, True, False, False],
    [True, True, False, False],
    [False, False, True, True],
    [False, False, True, True],
]

# Rib: weft-dominant horizontal ridges
_RIB = [
    [True, False, True, False],
    [False, False, False, False],
    [True, False, True, False],
    [False, False, False, False],
]

# ── European traditions ───────────────────────────────────────────

# Twill 2/2: diagonal lines, widespread since Bronze Age
_TWILL = [
    [True, True, False, False],
    [False, True, True, False],
    [False, False, True, True],
    [True, False, False, True],
]

# Twill 3/1: denim/jean weave, Nimes France
_DENIM = [
    [True, True, True, False],
    [False, True, True, True],
    [True, False, True, True],
    [True, True, False, True],
]

# Herringbone: Roman roads, British tweeds
_HERRINGBONE = [
    [True, True, False, False, False, False, True, True],
    [False, True, True, False, False, True, True, False],
    [False, False, True, True, True, True, False, False],
    [True, False, False, True, True, False, False, True],
]

# Houndstooth: Scottish Borders, 1800s
_HOUNDSTOOTH = [
    [True,  True,  False, False, True,  True,  False, False],
    [True,  True,  False, False, True,  True,  False, False],
    [False, False, True,  True,  False, False, True,  True],
    [False, False, True,  True,  False, False, True,  True],
    [True,  True,  True,  True,  False, False, False, False],
    [True,  True,  True,  True,  False, False, False, False],
    [False, False, False, False, True,  True,  True,  True],
    [False, False, False, False, True,  True,  True,  True],
]

# Satin 5-shaft: long floats, developed in China, refined in Europe
_SATIN = [
    [True, False, False, False, False],
    [False, False, True, False, False],
    [False, False, False, False, True],
    [False, True, False, False, False],
    [False, False, False, True, False],
]

# Waffle/Honeycomb: European kitchen textiles, raised grid
_WAFFLE = [
    [True,  True,  True,  True,  True,  True],
    [True,  False, False, False, False, True],
    [True,  False, True,  True,  False, True],
    [True,  False, True,  True,  False, True],
    [True,  False, False, False, False, True],
    [True,  True,  True,  True,  True,  True],
]

# Huck lace: European lace weaving, open/closed float pattern
_HUCK = [
    [True,  False, True,  False, True,  False],
    [True,  True,  True,  True,  True,  True],
    [False, True,  False, True,  False, True],
    [True,  True,  True,  True,  True,  True],
]

# M's and O's: European, alternating blocks of texture
_MS_AND_OS = [
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  False, True,  True,  False, True,  False],
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  False, True,  True,  False, True,  False],
    [False, True,  False, True,  True,  False, True,  False],
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  False, True,  True,  False, True,  False],
    [True,  False, True,  False, False, True,  False, True],
]

# ── Scandinavian traditions ───────────────────────────────────────

# Diamond twill: Norse/Viking, Celtic textiles
_DIAMOND = [
    [False, False, True,  False, False, False, True,  False],
    [False, True,  False, False, False, True,  False, False],
    [True,  False, False, False, True,  False, False, False],
    [False, True,  False, False, False, True,  False, False],
    [False, False, True,  False, False, False, True,  False],
    [False, False, False, True,  False, False, False, True],
]

# Bird's Eye: Scandinavian folk weaving, small diamond dots
_BIRDS_EYE = [
    [True,  False, True,  False],
    [False, False, False, True],
    [True,  False, True,  False],
    [False, True,  False, False],
]

# Goose Eye: larger diamond twill variant, Nordic
_GOOSE_EYE = [
    [True,  True,  False, False, False, False, True,  True,  False, False],
    [True,  False, False, False, False, True,  True,  False, False, False],
    [False, False, False, False, True,  True,  False, False, False, False],
    [False, False, False, True,  True,  False, False, False, False, True],
    [False, False, True,  True,  False, False, False, False, True,  True],
    [False, True,  True,  False, False, False, False, True,  True,  False],
    [False, False, True,  True,  False, False, False, False, True,  True],
    [False, False, False, True,  True,  False, False, False, False, True],
    [False, False, False, False, True,  True,  False, False, False, False],
    [True,  False, False, False, False, True,  True,  False, False, False],
]

# Rosepath: Swedish classic, undulating diagonal
_ROSEPATH = [
    [True,  False, False, False, True,  False, False, False],
    [False, True,  False, False, False, False, False, True],
    [False, False, True,  False, False, False, True,  False],
    [False, False, False, True,  False, True,  False, False],
    [False, False, True,  False, False, False, True,  False],
    [False, True,  False, False, False, False, False, True],
]

# Monk's Belt: Scandinavian, bold blocks with plain borders
_MONKS_BELT = [
    [True,  False, True,  False, True,  False, True,  False],
    [False, False, False, False, False, False, False, False],
    [True,  False, False, False, False, False, False, False],
    [False, False, False, False, False, False, False, False],
    [True,  False, False, False, False, False, False, False],
    [False, False, False, False, False, False, False, False],
    [True,  False, False, False, False, False, False, False],
    [False, False, False, False, False, False, False, False],
]

# ── Colonial American ─────────────────────────────────────────────

# Overshot: American colonial, "Star of Bethlehem" style
_OVERSHOT = [
    [True,  True,  True,  True,  False, False, False, False],
    [True,  True,  True,  False, False, False, False, True],
    [True,  True,  False, False, False, False, True,  True],
    [True,  False, False, False, False, True,  True,  True],
    [False, False, False, False, True,  True,  True,  True],
    [False, False, False, True,  True,  True,  True,  False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  True,  True,  True,  False, False, False],
]

# Summer & Winter: American colonial, two-block pattern
_SUMMER_WINTER = [
    [True,  False, True,  False, True,  True,  True,  True],
    [False, True,  False, True,  False, False, False, False],
    [True,  False, True,  False, True,  True,  True,  True],
    [False, True,  False, True,  False, False, False, False],
    [True,  True,  True,  True,  True,  False, True,  False],
    [False, False, False, False, False, True,  False, True],
    [True,  True,  True,  True,  True,  False, True,  False],
    [False, False, False, False, False, True,  False, True],
]

# ── African traditions ────────────────────────────────────────────

# Kente: Ashanti/Ewe, Ghana — bold geometric blocks on strip looms
_KENTE = [
    [True,  True,  True,  True,  False, False, False, False],
    [True,  True,  True,  True,  False, False, False, False],
    [True,  True,  True,  True,  False, False, False, False],
    [True,  True,  True,  True,  False, False, False, False],
    [False, False, False, False, True,  True,  True,  True],
    [False, False, False, False, True,  True,  True,  True],
    [False, False, False, False, True,  True,  True,  True],
    [False, False, False, False, True,  True,  True,  True],
]

# Kuba: Bakuba people, Congo — raffia cut-pile, stepped diagonals
_KUBA = [
    [True,  True,  False, False, False, True,  True,  False],
    [True,  False, False, False, True,  True,  False, False],
    [False, False, False, True,  True,  False, False, False],
    [False, False, True,  True,  False, False, False, True],
    [False, True,  True,  False, False, False, True,  True],
    [True,  True,  False, False, False, True,  True,  False],
    [True,  False, False, False, True,  True,  False, False],
    [False, False, False, True,  True,  False, False, False],
]

# Mudcloth (Bogolan): Bambara people, Mali — geometric resist-dyed
_MUDCLOTH = [
    [True,  True,  True,  True,  True,  True,  True,  True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  True,  True,  True,  True,  True,  True,  True],
    [True,  True,  True,  True,  True,  True,  True,  True],
    [False, False, True,  True,  False, False, True,  True],
    [False, False, True,  True,  False, False, True,  True],
    [True,  True,  True,  True,  True,  True,  True,  True],
]

# Adire: Yoruba people, Nigeria — resist-dyed indigo, bold geometry
_ADIRE = [
    [True,  True,  False, False, True,  True,  False, False],
    [True,  False, False, True,  True,  False, False, True],
    [False, False, True,  True,  False, False, True,  True],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  True,  False, False, True,  True,  False, False],
    [True,  False, False, True,  True,  False, False, True],
    [False, False, True,  True,  False, False, True,  True],
    [False, True,  True,  False, False, True,  True,  False],
]

# Aso-oke: Yoruba people, Nigeria — prestige strip-woven cloth
_ASO_OKE = [
    [True,  True,  True,  False, True,  True,  True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  True,  False, True,  True,  True,  False],
    [False, False, False, True,  False, False, False, True],
    [True,  True,  True,  False, True,  True,  True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  True,  False, True,  True,  True,  False],
    [False, False, False, True,  False, False, False, True],
]

# Ethiopian Tibeb: decorative border pattern on netela/shemma cloth
_TIBEB = [
    [True,  False, True,  False, True,  False, True,  False],
    [True,  True,  True,  True,  True,  True,  True,  True],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  False, False, True,  True,  False, False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  True,  True,  True,  True,  True,  True],
    [True,  False, True,  False, True,  False, True,  False],
    [False, False, True,  True,  False, False, True,  True],
]

# Shoowa: Kuba subgroup, Congo — embroidered raffia, interlocking geometry
_SHOOWA = [
    [True,  True,  True,  False, False, True,  True,  True],
    [True,  False, True,  False, False, True,  False, True],
    [True,  True,  True,  False, False, True,  True,  True],
    [False, False, False, True,  True,  False, False, False],
    [False, False, False, True,  True,  False, False, False],
    [True,  True,  True,  False, False, True,  True,  True],
    [True,  False, True,  False, False, True,  False, True],
    [True,  True,  True,  False, False, True,  True,  True],
]

# Berber/Amazigh: Morocco/North Africa — bold diamond motifs
_BERBER = [
    [False, False, False, True,  False, False, False, True],
    [False, False, True,  False, True,  False, True,  False],
    [False, True,  False, False, False, True,  False, False],
    [True,  False, False, False, False, False, True,  False],
    [False, True,  False, False, False, True,  False, False],
    [False, False, True,  False, True,  False, True,  False],
    [False, False, False, True,  False, False, False, True],
    [False, False, True,  False, True,  False, True,  False],
]

# Akwete: Igbo people, Nigeria — complex supplementary weft patterns
_AKWETE = [
    [True,  False, True,  True,  False, True,  False, True],
    [False, True,  False, False, True,  False, True,  False],
    [True,  True,  False, True,  True,  False, True,  True],
    [False, False, True,  False, False, True,  False, False],
    [True,  False, True,  True,  False, True,  False, True],
    [True,  True,  False, False, True,  False, True,  True],
    [False, False, True,  True,  False, True,  False, False],
    [True,  False, False, False, True,  False, False, True],
]

# Manjak: Guinea-Bissau / Senegal — strip-woven pano d'obra
_MANJAK = [
    [True,  True,  False, False, True,  True,  False, False],
    [True,  True,  False, False, True,  True,  False, False],
    [False, False, True,  True,  False, False, True,  True],
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  False, False, True,  True,  False, False],
    [False, False, True,  True,  False, False, True,  True],
    [False, False, True,  True,  False, False, True,  True],
]

# ── American Indigenous ───────────────────────────────────────────

# Navajo: Dine people, American Southwest — stepped diamonds, zigzags
_NAVAJO = [
    [False, False, False, True,  True,  False, False, False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  True,  False, False, False, False, True,  True],
    [True,  True,  False, False, False, False, True,  True],
    [False, True,  True,  False, False, True,  True,  False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, False, False, True,  True,  False, False, False],
]

# Andean: Inca/Quechua, Peru/Bolivia — backstrap loom geometric
_ANDEAN = [
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  True,  True,  True,  True,  True,  False],
    [True,  True,  False, True,  True,  False, True,  True],
    [False, True,  True,  True,  True,  True,  True,  False],
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  False, True,  True,  False, True,  False],
    [True,  True,  True,  False, False, True,  True,  True],
    [False, True,  False, True,  True,  False, True,  False],
]

# Mayan: Guatemala — bright backstrap brocade, horizontal bands
_MAYAN = [
    [True,  True,  True,  True,  True,  True,  True,  True],
    [False, True,  False, True,  False, True,  False, True],
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  True,  True,  True,  True,  True,  True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  True,  True,  True,  True,  True,  True,  True],
    [False, False, True,  True,  False, False, True,  True],
]

# Chimayo: New Mexico — Spanish colonial + Pueblo influence
_CHIMAYO = [
    [True,  False, False, True,  True,  False, False, True],
    [False, True,  True,  True,  True,  True,  True,  False],
    [False, True,  False, False, False, False, True,  False],
    [True,  True,  False, True,  True,  False, True,  True],
    [True,  True,  False, True,  True,  False, True,  True],
    [False, True,  False, False, False, False, True,  False],
    [False, True,  True,  True,  True,  True,  True,  False],
    [True,  False, False, True,  True,  False, False, True],
]

# Zapotec: Oaxaca, Mexico — Mitla step-fret (grecas) geometric
_ZAPOTEC = [
    [True,  True,  True,  True,  False, False, False, False],
    [True,  False, False, False, False, False, False, False],
    [True,  False, True,  True,  True,  True,  False, False],
    [True,  False, True,  False, False, False, False, False],
    [False, False, True,  False, True,  True,  True,  True],
    [False, False, True,  False, True,  False, False, True],
    [False, False, False, False, True,  False, False, True],
    [False, False, False, False, True,  True,  True,  True],
]

# Mapuche: Chile/Argentina — bold backstrap geometric
_MAPUCHE = [
    [True,  False, False, False, False, False, False, True],
    [True,  True,  False, False, False, False, True,  True],
    [False, True,  True,  False, False, True,  True,  False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  True,  False, False, False, False, True,  True],
    [True,  False, False, False, False, False, False, True],
]

# Salish: Coast Salish, Pacific NW — mountain goat wool, bold geometry
_SALISH = [
    [True,  True,  True,  True,  True,  True,  True,  True],
    [True,  False, False, False, False, False, False, True],
    [True,  False, True,  False, False, True,  False, True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  False, True,  False, False, True,  False, True],
    [True,  False, False, False, False, False, False, True],
    [True,  True,  True,  True,  True,  True,  True,  True],
]

# Hopi: Arizona — cotton ceremonial textiles, terraced patterns
_HOPI = [
    [True,  True,  True,  True,  True,  True,  True,  True],
    [False, True,  True,  True,  True,  True,  True,  False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, False, False, True,  True,  False, False, False],
    [False, False, False, True,  True,  False, False, False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  True,  True,  True,  True,  True,  False],
    [True,  True,  True,  True,  True,  True,  True,  True],
]

# ── Asian traditions ──────────────────────────────────────────────

# Silk damask: China — tone-on-tone, satin/twill contrast
_DAMASK = [
    [True,  True,  True,  True,  False, False, False, False],
    [True,  True,  True,  False, False, False, False, True],
    [True,  True,  False, False, False, False, True,  True],
    [True,  False, False, False, False, True,  True,  True],
    [False, False, False, True,  True,  True,  True,  False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  True,  True,  True,  False, False, False],
    [True,  True,  True,  True,  False, False, False, False],
]

# Kasuri/Ikat: Japan — offset resist-dyed warp, blurred-edge look
_KASURI = [
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  False, False, True,  True,  False, False],
    [False, False, True,  True,  False, False, True,  True],
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [False, False, True,  True,  False, False, True,  True],
    [True,  True,  False, False, True,  True,  False, False],
]

# Patola: Gujarat, India — double ikat, interlocking geometry
_PATOLA = [
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  False, True,  True,  True,  True,  False, True],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  False, True,  True,  True,  True,  False, True],
    [False, True,  False, True,  False, True,  False, True],
]

# Jamdani: Bangladesh/Bengal — supplementary weft muslin, floral geometry
_JAMDANI = [
    [True,  True,  False, True,  True,  False, True,  True],
    [True,  False, False, False, False, False, False, True],
    [False, False, True,  False, False, True,  False, False],
    [True,  False, False, True,  True,  False, False, True],
    [True,  False, False, True,  True,  False, False, True],
    [False, False, True,  False, False, True,  False, False],
    [True,  False, False, False, False, False, False, True],
    [True,  True,  False, True,  True,  False, True,  True],
]

# Songket: Malaysia/Indonesia — gold thread supplementary weft brocade
_SONGKET = [
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  True,  True,  False, True,  True,  True],
    [True,  True,  False, True,  True,  True,  False, True],
    [False, True,  True,  True,  False, True,  True,  True],
    [True,  False, True,  False, True,  False, True,  False],
    [True,  True,  False, True,  True,  True,  False, True],
    [False, True,  True,  True,  False, True,  True,  True],
    [True,  True,  False, True,  True,  True,  False, True],
]

# Thai Mudmee: Isan/NE Thailand — silk ikat, flowing organic shapes
_MUDMEE = [
    [True,  True,  False, False, True,  True,  False, False],
    [True,  False, False, True,  False, False, True,  True],
    [False, False, True,  True,  False, True,  True,  False],
    [False, True,  True,  False, True,  True,  False, False],
    [True,  True,  False, False, True,  True,  False, False],
    [False, False, True,  True,  False, False, True,  True],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  True,  False, False, True,  True,  False, False],
]

# T'nalak: T'boli people, Philippines — abaca fiber, dream-woven patterns
_TNALAK = [
    [True,  True,  True,  False, False, True,  True,  True],
    [True,  True,  False, True,  True,  False, True,  True],
    [True,  False, False, False, False, False, False, True],
    [False, True,  False, True,  True,  False, True,  False],
    [False, True,  False, True,  True,  False, True,  False],
    [True,  False, False, False, False, False, False, True],
    [True,  True,  False, True,  True,  False, True,  True],
    [True,  True,  True,  False, False, True,  True,  True],
]

# Hmong: Laos/Vietnam/China — story cloth, bold angular geometry
_HMONG = [
    [True,  False, False, False, True,  False, False, False],
    [True,  True,  False, True,  True,  True,  False, True],
    [False, True,  False, True,  False, True,  False, True],
    [False, True,  True,  True,  False, True,  True,  True],
    [False, True,  True,  True,  False, True,  True,  True],
    [False, True,  False, True,  False, True,  False, True],
    [True,  True,  False, True,  True,  True,  False, True],
    [True,  False, False, False, True,  False, False, False],
]

# Nishijin: Kyoto, Japan — complex figured silk, chrysanthemum motifs
_NISHIJIN = [
    [False, True,  False, False, False, False, True,  False],
    [True,  True,  True,  False, False, True,  True,  True],
    [False, True,  False, True,  True,  False, True,  False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  False, True,  True,  False, True,  False],
    [True,  True,  True,  False, False, True,  True,  True],
    [False, True,  False, False, False, False, True,  False],
]

# Dhaka: Nepal — fine geometric topi cloth, tiny repeating motifs
_DHAKA = [
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, False, False, True,  False, False],
    [True,  False, True,  False, True,  False, True,  False],
    [False, False, False, True,  False, False, False, True],
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, False, False, True,  False, False],
    [True,  False, True,  False, True,  False, True,  False],
    [False, False, False, True,  False, False, False, True],
]

# Li brocade: Li people, Hainan, China — UNESCO heritage, nature motifs
_LI = [
    [True,  False, False, True,  True,  False, False, True],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  True,  False, False, False, False, True,  True],
    [True,  False, False, True,  True,  False, False, True],
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  True,  False, False, False, False, True,  True],
    [False, False, False, True,  True,  False, False, False],
]

# Khmer Hol: Cambodia — silk ikat, temple-inspired geometry
_KHMER = [
    [True,  True,  False, False, False, False, True,  True],
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  True,  False, False, True,  True,  False],
    [False, False, False, True,  True,  False, False, False],
    [False, False, False, True,  True,  False, False, False],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  False, True,  False, False, True,  False, True],
    [True,  True,  False, False, False, False, True,  True],
]

# ── Middle Eastern / Central Asian traditions ─────────────────────

# Kilim: Turkey/Persia — slit tapestry, interlocking diagonal
_KILIM = [
    [True,  True,  True,  False, False, False, True,  True],
    [True,  True,  False, False, False, True,  True,  True],
    [True,  False, False, False, True,  True,  True,  False],
    [False, False, False, True,  True,  True,  False, False],
    [False, False, True,  True,  True,  False, False, False],
    [False, True,  True,  True,  False, False, False, True],
    [True,  True,  True,  False, False, False, True,  True],
    [True,  True,  False, False, False, True,  True,  True],
]

# Sumak: Caucasus — weft-wrapping technique, bold geometric
_SUMAK = [
    [True,  False, False, True,  True,  False, False, True],
    [False, True,  True,  False, False, True,  True,  False],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  False, False, True,  True,  False, False, True],
    [True,  True,  False, False, False, False, True,  True],
    [False, False, True,  True,  True,  True,  False, False],
    [False, False, True,  True,  True,  True,  False, False],
    [True,  True,  False, False, False, False, True,  True],
]

# Sadu: Bedouin, Arabian Peninsula — tent divider, bold stripes + geometry
_SADU = [
    [True,  True,  True,  True,  True,  True,  True,  True],
    [False, False, False, False, False, False, False, False],
    [True,  False, True,  False, True,  False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  False, True,  False, True,  False, True,  False],
    [False, False, False, False, False, False, False, False],
    [True,  True,  True,  True,  True,  True,  True,  True],
    [True,  True,  True,  True,  True,  True,  True,  True],
]

# Baluch: Afghanistan/Iran/Pakistan — dark tribal geometric
_BALUCH = [
    [True,  False, True,  True,  True,  True,  False, True],
    [False, True,  False, False, False, False, True,  False],
    [True,  False, True,  False, False, True,  False, True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  False, False, False, False, True,  False],
    [True,  False, True,  True,  True,  True,  False, True],
]

# Jajim: Iran — striped flat-weave, warp-faced bands
_JAJIM = [
    [True,  True,  False, False, True,  True,  False, False],
    [True,  True,  False, False, True,  True,  False, False],
    [True,  True,  False, False, True,  True,  False, False],
    [False, False, True,  True,  False, False, True,  True],
    [False, False, True,  True,  False, False, True,  True],
    [False, False, True,  True,  False, False, True,  True],
    [True,  False, True,  False, True,  False, True,  False],
    [True,  False, True,  False, True,  False, True,  False],
]

# Cicim: Turkey — supplementary weft embroidery on flat-weave
_CICIM = [
    [True,  True,  True,  False, False, True,  True,  True],
    [True,  True,  False, True,  True,  False, True,  True],
    [True,  False, True,  False, False, True,  False, True],
    [False, True,  False, True,  True,  False, True,  False],
    [False, True,  False, True,  True,  False, True,  False],
    [True,  False, True,  False, False, True,  False, True],
    [True,  True,  False, True,  True,  False, True,  True],
    [True,  True,  True,  False, False, True,  True,  True],
]

# Suzani: Uzbekistan/Central Asia — embroidered cosmic medallions
_SUZANI = [
    [False, False, True,  True,  True,  True,  False, False],
    [False, True,  True,  False, False, True,  True,  False],
    [True,  True,  False, False, False, False, True,  True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  False, False, True,  True,  False, False, True],
    [True,  True,  False, False, False, False, True,  True],
    [False, True,  True,  False, False, True,  True,  False],
    [False, False, True,  True,  True,  True,  False, False],
]

# ── Oceanian traditions ───────────────────────────────────────────

# Maori Taniko: New Zealand — finger-woven border, stepped triangles
_TANIKO = [
    [True,  False, False, False, False, False, False, False],
    [True,  True,  False, False, False, False, False, False],
    [True,  True,  True,  False, False, False, False, False],
    [True,  True,  True,  True,  False, False, False, False],
    [False, False, False, False, True,  True,  True,  True],
    [False, False, False, False, False, True,  True,  True],
    [False, False, False, False, False, False, True,  True],
    [False, False, False, False, False, False, False, True],
]

# Tongan Ngatu: Tonga/Polynesia — bark cloth, bold geometric kupesi
_NGATU = [
    [True,  True,  True,  True,  False, False, False, False],
    [True,  False, False, True,  False, True,  True,  False],
    [True,  False, False, True,  False, True,  True,  False],
    [True,  True,  True,  True,  False, False, False, False],
    [False, False, False, False, True,  True,  True,  True],
    [False, True,  True,  False, True,  False, False, True],
    [False, True,  True,  False, True,  False, False, True],
    [False, False, False, False, True,  True,  True,  True],
]


# ═══════════════════════════════════════════════════════════════════
# Weave registry — name, origin, draft
# ═══════════════════════════════════════════════════════════════════

WEAVES = [
    # Foundational                                                          pal: NATURAL=0
    {'name': 'PLAIN',          'origin': 'UNIVERSAL 7000 BCE', 'draft': _PLAIN,       'pal': 0},
    {'name': 'BASKET',         'origin': 'UNIVERSAL',          'draft': _BASKET,      'pal': 0},
    {'name': 'RIB',            'origin': 'UNIVERSAL',          'draft': _RIB,         'pal': 0},
    # European
    {'name': 'TWILL',          'origin': 'EUROPE / ASIA',      'draft': _TWILL,       'pal': 0},  # NATURAL
    {'name': 'DENIM',          'origin': 'NIMES, FRANCE',      'draft': _DENIM,       'pal': 1},  # INDIGO
    {'name': 'HERRINGBONE',    'origin': 'ROME / BRITAIN',     'draft': _HERRINGBONE, 'pal': 3},  # TARTAN
    {'name': 'HOUNDSTOOTH',    'origin': 'SCOTLAND',           'draft': _HOUNDSTOOTH, 'pal': 3},  # TARTAN
    {'name': 'SATIN',          'origin': 'CHINA VIA SILK ROAD','draft': _SATIN,       'pal': 5},  # SILK
    {'name': 'WAFFLE',         'origin': 'EUROPE',             'draft': _WAFFLE,      'pal': 0},  # NATURAL
    {'name': 'HUCK LACE',      'origin': 'EUROPE',             'draft': _HUCK,        'pal': 0},  # NATURAL
    {"name": "M'S AND O'S",    'origin': 'EUROPE',             'draft': _MS_AND_OS,   'pal': 9},  # NORDIC
    # Scandinavian
    {'name': 'DIAMOND TWILL',  'origin': 'NORSE / CELTIC',     'draft': _DIAMOND,     'pal': 9},  # NORDIC
    {"name": "BIRD'S EYE",     'origin': 'SCANDINAVIA',        'draft': _BIRDS_EYE,   'pal': 9},  # NORDIC
    {'name': 'GOOSE EYE',      'origin': 'NORDIC',             'draft': _GOOSE_EYE,   'pal': 9},  # NORDIC
    {'name': 'ROSEPATH',       'origin': 'SWEDEN',             'draft': _ROSEPATH,    'pal': 9},  # NORDIC
    {"name": "MONK'S BELT",    'origin': 'SCANDINAVIA',        'draft': _MONKS_BELT,  'pal': 9},  # NORDIC
    # Colonial American
    {'name': 'OVERSHOT',       'origin': 'COLONIAL AMERICA',   'draft': _OVERSHOT,    'pal': 0},  # NATURAL
    {'name': 'SUMMER+WINTER',  'origin': 'COLONIAL AMERICA',   'draft': _SUMMER_WINTER,'pal': 1}, # INDIGO
    # African
    {'name': 'KENTE',          'origin': 'ASHANTI, GHANA',     'draft': _KENTE,       'pal': 2},  # KENTE GOLD
    {'name': 'KUBA',           'origin': 'BAKUBA, CONGO',      'draft': _KUBA,        'pal': 11}, # KUBA RAFFIA
    {'name': 'MUDCLOTH',       'origin': 'BAMBARA, MALI',      'draft': _MUDCLOTH,    'pal': 6},  # MUDCLOTH
    {'name': 'ADIRE',          'origin': 'YORUBA, NIGERIA',    'draft': _ADIRE,       'pal': 1},  # INDIGO
    {'name': 'ASO-OKE',        'origin': 'YORUBA, NIGERIA',    'draft': _ASO_OKE,     'pal': 2},  # KENTE GOLD
    {'name': 'TIBEB',          'origin': 'ETHIOPIA',           'draft': _TIBEB,       'pal': 12}, # ETHIOPIAN
    {'name': 'SHOOWA',         'origin': 'KUBA, CONGO',        'draft': _SHOOWA,      'pal': 11}, # KUBA RAFFIA
    {'name': 'BERBER',         'origin': 'AMAZIGH, N. AFRICA', 'draft': _BERBER,      'pal': 17}, # BERBER
    {'name': 'AKWETE',         'origin': 'IGBO, NIGERIA',      'draft': _AKWETE,      'pal': 1},  # INDIGO
    {'name': 'MANJAK',         'origin': 'GUINEA-BISSAU',      'draft': _MANJAK,      'pal': 1},  # INDIGO
    # American Indigenous
    {'name': 'NAVAJO',         'origin': 'DINE, SW USA',       'draft': _NAVAJO,      'pal': 4},  # NAVAJO RED
    {'name': 'ANDEAN',         'origin': 'INCA, PERU',         'draft': _ANDEAN,      'pal': 7},  # ANDEAN
    {'name': 'MAYAN',          'origin': 'GUATEMALA',          'draft': _MAYAN,       'pal': 10}, # MAYAN
    {'name': 'CHIMAYO',        'origin': 'NEW MEXICO',         'draft': _CHIMAYO,     'pal': 4},  # NAVAJO RED
    {'name': 'ZAPOTEC',        'origin': 'OAXACA, MEXICO',     'draft': _ZAPOTEC,     'pal': 4},  # NAVAJO RED
    {'name': 'MAPUCHE',        'origin': 'CHILE / ARGENTINA',  'draft': _MAPUCHE,     'pal': 7},  # ANDEAN
    {'name': 'SALISH',         'origin': 'PACIFIC NW, USA',    'draft': _SALISH,      'pal': 0},  # NATURAL
    {'name': 'HOPI',           'origin': 'ARIZONA, USA',       'draft': _HOPI,        'pal': 0},  # NATURAL
    # Asian
    {'name': 'DAMASK',         'origin': 'CHINA',              'draft': _DAMASK,      'pal': 5},  # SILK
    {'name': 'KASURI',         'origin': 'JAPAN',              'draft': _KASURI,      'pal': 1},  # INDIGO
    {'name': 'PATOLA',         'origin': 'GUJARAT, INDIA',     'draft': _PATOLA,      'pal': 16}, # PATOLA
    {'name': 'JAMDANI',        'origin': 'BANGLADESH',         'draft': _JAMDANI,     'pal': 0},  # NATURAL
    {'name': 'SONGKET',        'origin': 'MALAYSIA',           'draft': _SONGKET,     'pal': 13}, # THAI SILK
    {'name': 'MUDMEE',         'origin': 'ISAN, THAILAND',     'draft': _MUDMEE,      'pal': 13}, # THAI SILK
    {"name": "T'NALAK",        'origin': "T'BOLI, PHILIPPINES",'draft': _TNALAK,      'pal': 6},  # MUDCLOTH
    {'name': 'HMONG',          'origin': 'LAOS / VIETNAM',     'draft': _HMONG,       'pal': 15}, # HMONG
    {'name': 'NISHIJIN',       'origin': 'KYOTO, JAPAN',       'draft': _NISHIJIN,    'pal': 5},  # SILK
    {'name': 'DHAKA',          'origin': 'NEPAL',              'draft': _DHAKA,       'pal': 16}, # PATOLA
    {'name': 'LI BROCADE',     'origin': 'HAINAN, CHINA',      'draft': _LI,          'pal': 8},  # IKAT
    {'name': 'KHMER HOL',      'origin': 'CAMBODIA',           'draft': _KHMER,       'pal': 13}, # THAI SILK
    # Middle Eastern / Central Asian
    {'name': 'KILIM',          'origin': 'TURKEY / PERSIA',    'draft': _KILIM,       'pal': 8},  # IKAT
    {'name': 'SUMAK',          'origin': 'CAUCASUS',           'draft': _SUMAK,       'pal': 8},  # IKAT
    {'name': 'SADU',           'origin': 'BEDOUIN, ARABIA',    'draft': _SADU,        'pal': 14}, # SADU
    {'name': 'BALUCH',         'origin': 'AFGHANISTAN',        'draft': _BALUCH,      'pal': 14}, # SADU
    {'name': 'JAJIM',          'origin': 'IRAN',               'draft': _JAJIM,       'pal': 8},  # IKAT
    {'name': 'CICIM',          'origin': 'TURKEY',             'draft': _CICIM,       'pal': 8},  # IKAT
    {'name': 'SUZANI',         'origin': 'UZBEKISTAN',         'draft': _SUZANI,      'pal': 7},  # ANDEAN
    # Oceanian
    {'name': 'TANIKO',         'origin': 'MAORI, NZ',          'draft': _TANIKO,      'pal': 14}, # SADU
    {'name': 'NGATU',          'origin': 'TONGA / POLYNESIA',  'draft': _NGATU,       'pal': 11}, # KUBA RAFFIA
]


# ═══════════════════════════════════════════════════════════════════
# COLOR PALETTES — global textile traditions
# ═══════════════════════════════════════════════════════════════════

PALETTES = [
    {
        'name': 'NATURAL',
        'origin': 'UNDYED FIBER',
        'warp': (200, 180, 140),
        'weft': (160, 130, 80),
        'gap':  (90, 75, 50),
    },
    {
        'name': 'INDIGO',
        'origin': 'JAPAN / W. AFRICA',
        'warp': (220, 215, 195),
        'weft': (35, 45, 110),
        'gap':  (18, 22, 55),
    },
    {
        'name': 'KENTE GOLD',
        'origin': 'GHANA',
        'warp': (220, 180, 30),
        'weft': (170, 35, 25),
        'gap':  (75, 55, 12),
    },
    {
        'name': 'TARTAN',
        'origin': 'SCOTLAND',
        'warp': (25, 50, 120),
        'weft': (155, 25, 25),
        'gap':  (15, 18, 38),
    },
    {
        'name': 'NAVAJO RED',
        'origin': 'AMERICAN SW',
        'warp': (185, 75, 35),
        'weft': (55, 35, 30),
        'gap':  (45, 28, 18),
    },
    {
        'name': 'SILK',
        'origin': 'CHINA',
        'warp': (195, 165, 195),
        'weft': (130, 175, 155),
        'gap':  (65, 70, 75),
    },
    {
        'name': 'MUDCLOTH',
        'origin': 'MALI',
        'warp': (200, 185, 150),
        'weft': (60, 45, 30),
        'gap':  (35, 28, 18),
    },
    {
        'name': 'ANDEAN',
        'origin': 'PERU / BOLIVIA',
        'warp': (180, 30, 40),
        'weft': (210, 170, 30),
        'gap':  (70, 25, 18),
    },
    {
        'name': 'IKAT',
        'origin': 'INDONESIA',
        'warp': (35, 40, 100),
        'weft': (170, 70, 35),
        'gap':  (20, 22, 45),
    },
    {
        'name': 'NORDIC',
        'origin': 'SCANDINAVIA',
        'warp': (210, 205, 190),
        'weft': (50, 70, 130),
        'gap':  (65, 65, 75),
    },
    {
        'name': 'MAYAN',
        'origin': 'GUATEMALA',
        'warp': (190, 30, 100),
        'weft': (30, 160, 150),
        'gap':  (55, 25, 45),
    },
    {
        'name': 'KUBA RAFFIA',
        'origin': 'CONGO',
        'warp': (190, 165, 110),
        'weft': (70, 50, 30),
        'gap':  (50, 42, 28),
    },
    {
        'name': 'ETHIOPIAN',
        'origin': 'ETHIOPIA',
        'warp': (230, 225, 210),
        'weft': (180, 50, 40),
        'gap':  (100, 95, 85),
    },
    {
        'name': 'THAI SILK',
        'origin': 'THAILAND',
        'warp': (140, 45, 130),
        'weft': (200, 165, 40),
        'gap':  (55, 25, 50),
    },
    {
        'name': 'SADU',
        'origin': 'ARABIAN PENINSULA',
        'warp': (30, 25, 20),
        'weft': (190, 50, 30),
        'gap':  (15, 12, 10),
    },
    {
        'name': 'HMONG',
        'origin': 'SE ASIA',
        'warp': (25, 25, 30),
        'weft': (40, 110, 200),
        'gap':  (12, 12, 15),
    },
    {
        'name': 'PATOLA',
        'origin': 'INDIA',
        'warp': (170, 25, 30),
        'weft': (225, 210, 180),
        'gap':  (65, 15, 15),
    },
    {
        'name': 'BERBER',
        'origin': 'NORTH AFRICA',
        'warp': (210, 195, 160),
        'weft': (160, 110, 50),
        'gap':  (80, 70, 48),
    },
]


# ═══════════════════════════════════════════════════════════════════
# Visual class
# ═══════════════════════════════════════════════════════════════════

class Weaving(Visual):
    name = "WEAVING"
    description = "World textile traditions"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self.weave_idx = 0
        self.palette_idx = 0
        self.speed_idx = DEFAULT_SPEED_IDX
        self.row_timer = 0.0
        self.revealed_rows = 0
        self.overlay_timer = 0.0
        self._build_fabric()

    def _build_fabric(self, set_palette=True):
        w = WEAVES[self.weave_idx]
        self.fabric = _tile(w['draft'], GRID, GRID)
        self.revealed_rows = 0
        self.row_timer = 0.0
        if set_palette:
            self.palette_idx = w.get('pal', 0)

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: speed control
        if input_state.left_pressed:
            self.speed_idx = max(0, self.speed_idx - 1)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.speed_idx = min(len(SPEEDS) - 1, self.speed_idx + 1)
            self.overlay_timer = 2.0
            consumed = True

        # Up/Down: palette
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True

        # Action: next weave technique
        if input_state.action_l or input_state.action_r:
            self.weave_idx = (self.weave_idx + 1) % len(WEAVES)
            self._build_fabric()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        speed = SPEEDS[self.speed_idx]
        if self.revealed_rows < GRID:
            self.row_timer += dt * BASE_ROWS_PER_SEC * speed
            while self.row_timer >= 1.0 and self.revealed_rows < GRID:
                self.row_timer -= 1.0
                self.revealed_rows += 1
        else:
            # Pause then auto-advance
            self.row_timer += dt * speed
            if self.row_timer > 2.5:
                self.weave_idx = (self.weave_idx + 1) % len(WEAVES)
                self._build_fabric()

    def draw(self):
        d = self.display
        d.clear()

        pal = PALETTES[self.palette_idx]
        warp_c = pal['warp']
        weft_c = pal['weft']
        gap_c = pal['gap']

        # ── Draw fabric ──
        for row in range(self.revealed_rows):
            for col in range(GRID):
                warp_on_top = self.fabric[row][col]
                top_c = warp_c if warp_on_top else weft_c
                shade = 1.0 if warp_on_top else 0.85

                px = col * THREAD_PX
                py = row * THREAD_PX

                for dy in range(THREAD_PX):
                    for dx in range(THREAD_PX):
                        if dx == THREAD_PX - 1 or dy == THREAD_PX - 1:
                            d.set_pixel(px + dx, py + dy, gap_c)
                        else:
                            if dx == 0 and dy == 0:
                                hi = min(1.15, shade + 0.15)
                                c = (min(255, int(top_c[0] * hi)),
                                     min(255, int(top_c[1] * hi)),
                                     min(255, int(top_c[2] * hi)))
                            else:
                                c = (int(top_c[0] * shade),
                                     int(top_c[1] * shade),
                                     int(top_c[2] * shade))
                            d.set_pixel(px + dx, py + dy, c)

        # ── Shuttle on current weaving row ──
        if self.revealed_rows < GRID:
            sy = self.revealed_rows * THREAD_PX
            frac = self.row_timer % 1.0
            sx = int(frac * 60) + 2
            for dx in range(3):
                for dy in range(2):
                    nx, ny = sx + dx, sy + dy
                    if 0 <= nx < 64 and 0 <= ny < 64:
                        d.set_pixel(nx, ny, (255, 240, 200))

        # ── Weave name + origin (top) ──
        w = WEAVES[self.weave_idx]
        d.draw_text_small(2, 1, w['name'], (180, 180, 180))
        d.draw_text_small(2, 7, w['origin'], (110, 110, 110))

        # ── Palette name (bottom) ──
        d.draw_text_small(2, 59, pal['name'], (120, 120, 120))

        # ── Speed overlay ──
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 30, 'SPEED ' + SPEED_LABELS[self.speed_idx], c)

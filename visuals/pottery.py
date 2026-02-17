"""
Pottery
=======
World ceramic traditions rendered as top-down plates/bowls (concentric
circular decoration) and side-view vessels (silhouette with row-by-row
decoration).

Controls:
  Up/Down    - Cycle traditions
  Left/Right - Cycle vessels within current tradition
  Action     - Next vessel (any tradition)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE

# ═══════════════════════════════════════════════════════════════════
# Constants
# ═══════════════════════════════════════════════════════════════════

CX, CY = 32, 34          # center for top-down plates (shifted down for labels)
SIDE_Y0 = 14             # top of side-view vessel area
SIDE_ROWS = 38           # side-view vessel height
BASE_ROWS_PER_SEC = 3.0  # decoration reveal speed (rings or rows)
HOLD_TIME = 2.5          # seconds to hold before auto-advance


# ═══════════════════════════════════════════════════════════════════
# Helpers -- side-view silhouettes
# ═══════════════════════════════════════════════════════════════════

def _lerp_widths(pairs, total):
    """Linearly interpolate between (row_count, half_width) waypoints."""
    out = []
    for i in range(len(pairs) - 1):
        n, w0 = pairs[i]
        _, w1 = pairs[i + 1]
        for t in range(n):
            f = t / max(1, n - 1) if n > 1 else 0.0
            out.append(round(w0 + (w1 - w0) * f))
    out.append(pairs[-1][1])
    while len(out) < total:
        out.append(out[-1])
    return out[:total]


def _sym(cx, half_widths):
    """Return list of (xl, xr) tuples centered at cx."""
    return [(cx - hw, cx + hw) for hw in half_widths]


# ═══════════════════════════════════════════════════════════════════
# Tile patterns -- small grids for decoration
# ═══════════════════════════════════════════════════════════════════

PAT_MEANDER = [
    [1, 1, 1, 1, 0, 0, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1],
    [0, 0, 1, 0, 0, 1, 0, 0],
]

PAT_WAVE = [
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 1],
]

PAT_FLORAL = [
    [0, 0, 1, 1, 0, 0, 0, 0],
    [0, 1, 1, 1, 1, 0, 0, 0],
    [1, 1, 0, 0, 1, 1, 0, 0],
    [0, 1, 1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0, 0, 0],
]

PAT_DIAMOND = [
    [0, 0, 1, 0, 0, 0],
    [0, 1, 0, 1, 0, 0],
    [1, 0, 0, 0, 1, 0],
    [0, 1, 0, 1, 0, 0],
    [0, 0, 1, 0, 0, 0],
]

PAT_ZIGZAG = [
    [1, 0, 0, 0, 0, 0],
    [1, 1, 0, 0, 0, 0],
    [0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 0],
    [0, 0, 0, 0, 1, 1],
    [0, 0, 0, 1, 1, 0],
    [0, 0, 1, 1, 0, 0],
    [0, 1, 1, 0, 0, 0],
    [1, 1, 0, 0, 0, 0],
]

PAT_DOTS = [
    [0, 0, 0, 0],
    [0, 1, 0, 0],
    [0, 0, 0, 0],
    [0, 0, 0, 1],
]

PAT_STRIPE_H = [
    [1, 1, 1, 1],
    [0, 0, 0, 0],
    [1, 1, 1, 1],
    [0, 0, 0, 0],
]

PAT_CORD = [
    [1, 0, 1, 0, 0, 1],
    [0, 1, 0, 0, 1, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0],
]

PAT_STEP = [
    [1, 1, 1, 0, 0, 0],
    [1, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0],
    [0, 0, 0, 0, 1, 1],
    [0, 0, 0, 0, 1, 1],
]

PAT_TRIANGLE = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

PAT_CROSS = [
    [0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0],
    [1, 1, 1, 1, 1, 1],
    [1, 1, 1, 1, 1, 1],
    [0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0],
]

PAT_HOOK = [
    [1, 1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0],
    [0, 1, 1, 1, 0, 0],
    [0, 0, 0, 1, 0, 0],
    [0, 0, 0, 1, 1, 1],
    [0, 0, 0, 0, 0, 1],
]


# ═══════════════════════════════════════════════════════════════════
# Side-view silhouette builders
# ═══════════════════════════════════════════════════════════════════

def _amphora():
    hw = _lerp_widths([
        (3, 6), (3, 4), (2, 3), (5, 14), (12, 15),
        (6, 13), (4, 8), (3, 7),
    ], SIDE_ROWS)
    sil = _sym(CX, hw)
    for i in range(8, min(20, SIDE_ROWS)):
        xl, xr = sil[i]
        sil[i] = (xl - 3, xr + 3)
    return sil


def _ming_vase():
    hw = _lerp_widths([
        (2, 5), (2, 4), (3, 3), (5, 13), (10, 15),
        (8, 14), (5, 10), (3, 7),
    ], SIDE_ROWS)
    return _sym(CX, hw)


def _canopic_jar():
    hw = _lerp_widths([
        (4, 9), (2, 7), (2, 4), (3, 5), (10, 12),
        (10, 12), (4, 9), (3, 7),
    ], SIDE_ROWS)
    return _sym(CX, hw)


def _zulu_pot():
    hw = _lerp_widths([
        (3, 5), (4, 8), (8, 16), (10, 16),
        (6, 12), (4, 6), (3, 5),
    ], SIDE_ROWS)
    return _sym(CX, hw)


def _jomon_vessel():
    hw = _lerp_widths([
        (3, 12), (2, 8), (2, 5), (4, 7), (10, 14),
        (8, 13), (4, 8), (3, 7),
    ], SIDE_ROWS)
    return _sym(CX, hw)


def _raku_bowl():
    hw = _lerp_widths([
        (4, 18), (10, 20), (10, 20), (6, 16),
        (3, 5), (4, 6),
    ], SIDE_ROWS)
    return _sym(CX, hw)


def _yixing_teapot():
    hw = _lerp_widths([
        (3, 4), (2, 3), (3, 5), (10, 14), (10, 14),
        (6, 10), (3, 6),
    ], SIDE_ROWS)
    sil = _sym(CX, hw)
    for i in range(10, min(20, SIDE_ROWS)):
        xl, xr = sil[i]
        sil[i] = (xl - 5, xr + 3)
    return sil


def _persian_ewer():
    hw = _lerp_widths([
        (2, 5), (3, 3), (3, 3), (6, 12), (10, 13),
        (6, 10), (3, 7),
    ], SIDE_ROWS)
    sil = _sym(CX, hw)
    for i in range(min(6, SIDE_ROWS)):
        xl, xr = sil[i]
        sil[i] = (xl, xr + 5)
    return sil


# ═══════════════════════════════════════════════════════════════════
# Top-down plate decoration helpers
# ═══════════════════════════════════════════════════════════════════

def _ring_pixels(cx, cy, r):
    """Return set of (x,y) on a circle outline at radius r."""
    pts = set()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            d2 = dx * dx + dy * dy
            if abs(d2 - r * r) < r * 2:
                pts.add((cx + dx, cy + dy))
    return pts


def _filled_circle_pixels(cx, cy, r):
    """Return set of (x,y) inside circle of radius r."""
    pts = set()
    for dy in range(-r, r + 1):
        for dx in range(-r, r + 1):
            if dx * dx + dy * dy <= r * r:
                pts.add((cx + dx, cy + dy))
    return pts


def _polar_deco(cx, cy, r, n, offset=0.0):
    """Return n evenly spaced pixel positions around radius r."""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n + offset
        px = int(round(cx + r * math.cos(a)))
        py = int(round(cy + r * math.sin(a)))
        pts.append((px, py))
    return pts


def _sector_pixels(cx, cy, r_inner, r_outer, a_start, a_end):
    """Return pixels in an arc sector between two radii and angle range."""
    pts = []
    for dy in range(-(r_outer + 1), r_outer + 2):
        for dx in range(-(r_outer + 1), r_outer + 2):
            d2 = dx * dx + dy * dy
            if r_inner * r_inner <= d2 <= r_outer * r_outer:
                a = math.atan2(dy, dx)
                if a < 0:
                    a += 2 * math.pi
                if a_start <= a <= a_end or (a_start > a_end and (a >= a_start or a <= a_end)):
                    pts.append((cx + dx, cy + dy))
    return pts


# ═══════════════════════════════════════════════════════════════════
# Top-down plate decoration functions
# Each returns a list of "rings" (from center outward).
# Each ring is a list of (x, y, color) pixels for that ring layer.
# ═══════════════════════════════════════════════════════════════════

def _deco_greek_kylix(cx, cy):
    """Red-figure kylix: terracotta ground, black meander border, central figure."""
    terra = (180, 100, 50)
    black = (30, 25, 20)
    dark_red = (140, 60, 30)
    rings = []
    # Ring 0: center medallion r=0-8
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 8):
        r0.append((px, py, terra))
    # Small cross figure in center
    for d in range(-3, 4):
        r0.append((cx + d, cy, black))
        r0.append((cx, cy + d, black))
    rings.append(r0)
    # Ring 1: inner border r=9-10
    r1 = []
    for r in range(9, 11):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, black))
    rings.append(r1)
    # Ring 2: meander band r=11-16
    r2 = []
    for r in range(11, 17):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            idx = int((a + math.pi) / (2 * math.pi) * 24) % 24
            row = (r - 11) % 4
            if PAT_MEANDER[row][idx % len(PAT_MEANDER[row])]:
                r2.append((px, py, black))
            else:
                r2.append((px, py, terra))
    rings.append(r2)
    # Ring 3: body fill r=17-22
    r3 = []
    for r in range(17, 23):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, terra))
    rings.append(r3)
    # Ring 4: outer border r=23-24
    r4 = []
    for r in range(23, 25):
        for px, py in _ring_pixels(cx, cy, r):
            r4.append((px, py, black))
    rings.append(r4)
    # Ring 5: rim r=25-26
    r5 = []
    for r in range(25, 27):
        for px, py in _ring_pixels(cx, cy, r):
            r5.append((px, py, dark_red))
    rings.append(r5)
    return rings


def _deco_ming_plate(cx, cy):
    """Ming blue-and-white plate: central flower, concentric blue bands."""
    white = (220, 220, 230)
    blue = (40, 60, 160)
    lt_blue = (80, 110, 200)
    rings = []
    # Center medallion
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 6):
        r0.append((px, py, white))
    # Flower: 6-petal
    for pt in _polar_deco(cx, cy, 4, 6):
        r0.append((pt[0], pt[1], blue))
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r0.append((pt[0] + dx, pt[1] + dy, blue))
    r0.append((cx, cy, blue))
    rings.append(r0)
    # Inner ring
    r1 = []
    for r in range(7, 10):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, blue if r == 8 else lt_blue))
    rings.append(r1)
    # Decoration band with floral repeats
    r2 = []
    for r in range(10, 17):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            idx = int((a + math.pi) / (2 * math.pi) * 32) % 32
            row = (r - 10) % len(PAT_FLORAL)
            if PAT_FLORAL[row][idx % len(PAT_FLORAL[row])]:
                r2.append((px, py, blue))
            else:
                r2.append((px, py, white))
    rings.append(r2)
    # Outer field
    r3 = []
    for r in range(17, 23):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, white))
    rings.append(r3)
    # Rim bands
    r4 = []
    for r in range(23, 27):
        for px, py in _ring_pixels(cx, cy, r):
            r4.append((px, py, blue if r in (24, 25) else lt_blue))
    rings.append(r4)
    return rings


def _deco_iznik_plate(cx, cy):
    """Iznik plate: tulip/geometric in blue, red, turquoise on white."""
    white = (225, 225, 230)
    blue = (30, 70, 170)
    red = (190, 50, 40)
    turq = (40, 160, 160)
    rings = []
    # Center rosette
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 5):
        r0.append((px, py, turq))
    for pt in _polar_deco(cx, cy, 3, 8):
        r0.append((pt[0], pt[1], red))
    r0.append((cx, cy, blue))
    rings.append(r0)
    # Inner border
    r1 = []
    for r in range(6, 9):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, blue))
    rings.append(r1)
    # Tulip zone: alternating color motifs
    r2 = []
    for r in range(9, 18):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            sector = int((a + math.pi) / (2 * math.pi) * 8) % 8
            if sector % 2 == 0:
                r2.append((px, py, red if (r - 9) % 3 == 0 else white))
            else:
                r2.append((px, py, turq if (r - 9) % 3 == 0 else white))
    rings.append(r2)
    # Outer border
    r3 = []
    for r in range(18, 21):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, blue))
    rings.append(r3)
    # White field + rim
    r4 = []
    for r in range(21, 27):
        for px, py in _ring_pixels(cx, cy, r):
            r4.append((px, py, white if r < 25 else blue))
    rings.append(r4)
    return rings


def _deco_talavera_plate(cx, cy):
    """Talavera majolica: blue floral on white."""
    white = (225, 225, 230)
    blue = (45, 75, 165)
    yellow = (200, 180, 60)
    rings = []
    # Center flower
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 4):
        r0.append((px, py, yellow))
    for pt in _polar_deco(cx, cy, 3, 6):
        r0.append((pt[0], pt[1], blue))
    rings.append(r0)
    # Inner ring
    r1 = []
    for r in range(5, 8):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, blue if r == 6 else white))
    rings.append(r1)
    # Floral band
    r2 = []
    for r in range(8, 16):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            idx = int((a + math.pi) / (2 * math.pi) * 24) % 24
            row = (r - 8) % len(PAT_FLORAL)
            if PAT_FLORAL[row][idx % len(PAT_FLORAL[row])]:
                r2.append((px, py, blue))
            else:
                r2.append((px, py, white))
    rings.append(r2)
    # Outer white
    r3 = []
    for r in range(16, 22):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, white))
    rings.append(r3)
    # Blue rim
    r4 = []
    for r in range(22, 27):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            idx = int((a + math.pi) / (2 * math.pi) * 16) % 16
            if idx % 4 == 0:
                r4.append((px, py, yellow))
            else:
                r4.append((px, py, blue))
    rings.append(r4)
    return rings


def _deco_hopi_bowl(cx, cy):
    """Hopi bowl: black-on-cream, bold geometric asymmetric design."""
    cream = (210, 190, 150)
    black = (35, 30, 25)
    rings = []
    # Center
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 6):
        r0.append((px, py, cream))
    # Asymmetric spiral in center
    for i in range(20):
        a = i * 0.4
        r = i * 0.3
        px = int(round(cx + r * math.cos(a)))
        py = int(round(cy + r * math.sin(a)))
        r0.append((px, py, black))
    rings.append(r0)
    # Step pattern band
    r1 = []
    for r in range(7, 10):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, black))
    rings.append(r1)
    # Geometric zone: step/hook pattern
    r2 = []
    for r in range(10, 20):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            idx = int((a + math.pi) / (2 * math.pi) * 24) % 24
            row = (r - 10) % len(PAT_STEP)
            if PAT_STEP[row][idx % len(PAT_STEP[row])]:
                r2.append((px, py, black))
            else:
                r2.append((px, py, cream))
    rings.append(r2)
    # Outer cream
    r3 = []
    for r in range(20, 24):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, cream))
    rings.append(r3)
    # Rim
    r4 = []
    for r in range(24, 27):
        for px, py in _ring_pixels(cx, cy, r):
            r4.append((px, py, black if r == 25 else cream))
    rings.append(r4)
    return rings


def _deco_delft_plate(cx, cy):
    """Delft plate: blue on white, central windmill motif."""
    white = (225, 225, 235)
    blue = (35, 65, 155)
    lt_blue = (100, 130, 200)
    rings = []
    # Center: windmill abstraction (cross + triangle)
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 7):
        r0.append((px, py, white))
    # Windmill sails (X shape)
    for d in range(-5, 6):
        r0.append((cx + d, cy + d, blue))
        r0.append((cx + d, cy - d, blue))
    # Body
    for dy in range(-2, 3):
        for dx in range(-1, 2):
            r0.append((cx + dx, cy + dy, blue))
    rings.append(r0)
    # Inner border
    r1 = []
    for r in range(8, 11):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, blue if r == 9 else lt_blue))
    rings.append(r1)
    # Floral garland zone
    r2 = []
    for r in range(11, 19):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            idx = int((a + math.pi) / (2 * math.pi) * 20) % 20
            row = (r - 11) % len(PAT_FLORAL)
            if PAT_FLORAL[row][idx % len(PAT_FLORAL[row])]:
                r2.append((px, py, blue))
            else:
                r2.append((px, py, white))
    rings.append(r2)
    # Outer white
    r3 = []
    for r in range(19, 23):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, white))
    rings.append(r3)
    # Rim
    r4 = []
    for r in range(23, 27):
        for px, py in _ring_pixels(cx, cy, r):
            r4.append((px, py, blue if r in (24, 25) else lt_blue))
    rings.append(r4)
    return rings


def _deco_imari_plate(cx, cy):
    """Imari plate: red, blue, gold in radiating sectors."""
    white = (225, 220, 215)
    red = (180, 40, 30)
    blue = (30, 50, 150)
    gold = (200, 170, 50)
    rings = []
    # Center medallion
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 6):
        r0.append((px, py, blue))
    for pt in _polar_deco(cx, cy, 3, 6):
        r0.append((pt[0], pt[1], gold))
    r0.append((cx, cy, gold))
    rings.append(r0)
    # Divider ring
    r1 = []
    for r in range(7, 9):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, gold))
    rings.append(r1)
    # Sector zone: alternating red/blue/white panels
    r2 = []
    for r in range(9, 20):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            sector = int((a + math.pi) / (2 * math.pi) * 6) % 6
            if sector % 3 == 0:
                r2.append((px, py, red))
            elif sector % 3 == 1:
                r2.append((px, py, blue))
            else:
                r2.append((px, py, white))
    rings.append(r2)
    # Gold divider
    r3 = []
    for r in range(20, 22):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, gold))
    rings.append(r3)
    # Rim
    r4 = []
    for r in range(22, 27):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            sector = int((a + math.pi) / (2 * math.pi) * 12) % 12
            if sector % 2 == 0:
                r4.append((px, py, red))
            else:
                r4.append((px, py, blue))
    rings.append(r4)
    return rings


def _deco_celadon_bowl(cx, cy):
    """Celadon bowl: subtle jade green with crackle pattern."""
    jade = (75, 130, 85)
    lt_jade = (95, 155, 105)
    dk_jade = (55, 100, 65)
    crack = (110, 170, 120)
    rings = []
    # Center
    r0 = []
    for px, py in _filled_circle_pixels(cx, cy, 8):
        r0.append((px, py, jade))
    rings.append(r0)
    # Subtle carved pattern zone
    r1 = []
    for r in range(9, 12):
        for px, py in _ring_pixels(cx, cy, r):
            r1.append((px, py, lt_jade))
    rings.append(r1)
    # Body with crackle
    r2 = []
    for r in range(12, 21):
        for px, py in _ring_pixels(cx, cy, r):
            a = math.atan2(py - cy, px - cx)
            idx = int((a + math.pi) / (2 * math.pi) * 30) % 30
            # Crackle lines at irregular intervals
            if idx in (3, 7, 12, 18, 23, 27) and (r + idx) % 3 == 0:
                r2.append((px, py, crack))
            else:
                r2.append((px, py, jade))
    rings.append(r2)
    # Inner rim
    r3 = []
    for r in range(21, 24):
        for px, py in _ring_pixels(cx, cy, r):
            r3.append((px, py, lt_jade))
    rings.append(r3)
    # Outer rim
    r4 = []
    for r in range(24, 27):
        for px, py in _ring_pixels(cx, cy, r):
            r4.append((px, py, dk_jade))
    rings.append(r4)
    return rings


# ═══════════════════════════════════════════════════════════════════
# Vessel data
# ═══════════════════════════════════════════════════════════════════

VESSELS = [
    # ── Top-down plates and bowls ──
    {
        'name': 'GREEK KYLIX',
        'origin': 'GREECE  500 BC',
        'tradition': 'GREEK',
        'view': 'top',
        'deco_fn': _deco_greek_kylix,
    },
    {
        'name': 'MING PLATE',
        'origin': 'CHINA  1400',
        'tradition': 'CHINESE',
        'view': 'top',
        'deco_fn': _deco_ming_plate,
    },
    {
        'name': 'IZNIK PLATE',
        'origin': 'TURKEY  1550',
        'tradition': 'ISLAMIC',
        'view': 'top',
        'deco_fn': _deco_iznik_plate,
    },
    {
        'name': 'TALAVERA PLATE',
        'origin': 'MEXICO  1600',
        'tradition': 'MEXICAN',
        'view': 'top',
        'deco_fn': _deco_talavera_plate,
    },
    {
        'name': 'HOPI BOWL',
        'origin': 'SW AMERICA  1000',
        'tradition': 'PUEBLO',
        'view': 'top',
        'deco_fn': _deco_hopi_bowl,
    },
    {
        'name': 'DELFT PLATE',
        'origin': 'NETHERLANDS 1650',
        'tradition': 'EUROPEAN',
        'view': 'top',
        'deco_fn': _deco_delft_plate,
    },
    {
        'name': 'IMARI PLATE',
        'origin': 'JAPAN  1700',
        'tradition': 'JAPANESE',
        'view': 'top',
        'deco_fn': _deco_imari_plate,
    },
    {
        'name': 'CELADON BOWL',
        'origin': 'KOREA  1100',
        'tradition': 'KOREAN',
        'view': 'top',
        'deco_fn': _deco_celadon_bowl,
    },
    # ── Side-view vessels ──
    {
        'name': 'AMPHORA',
        'origin': 'GREECE  500 BC',
        'tradition': 'GREEK',
        'view': 'side',
        'body_color': (180, 100, 50),
        'deco_color': (30, 25, 20),
        'silhouette': _amphora(),
        'pattern': PAT_MEANDER,
    },
    {
        'name': 'MING VASE',
        'origin': 'CHINA  1400',
        'tradition': 'CHINESE',
        'view': 'side',
        'body_color': (220, 220, 230),
        'deco_color': (40, 60, 160),
        'silhouette': _ming_vase(),
        'pattern': PAT_FLORAL,
    },
    {
        'name': 'CANOPIC JAR',
        'origin': 'EGYPT  1300 BC',
        'tradition': 'EGYPTIAN',
        'view': 'side',
        'body_color': (190, 170, 130),
        'deco_color': (200, 170, 80),
        'silhouette': _canopic_jar(),
        'pattern': PAT_STRIPE_H,
    },
    {
        'name': 'ZULU BEER POT',
        'origin': 'SOUTH AFRICA',
        'tradition': 'AFRICAN',
        'view': 'side',
        'body_color': (50, 35, 25),
        'deco_color': (130, 90, 50),
        'silhouette': _zulu_pot(),
        'pattern': PAT_TRIANGLE,
    },
    {
        'name': 'JOMON VESSEL',
        'origin': 'JAPAN  3000 BC',
        'tradition': 'JAPANESE',
        'view': 'side',
        'body_color': (140, 100, 60),
        'deco_color': (90, 65, 35),
        'silhouette': _jomon_vessel(),
        'pattern': PAT_CORD,
    },
    {
        'name': 'RAKU BOWL',
        'origin': 'JAPAN  1580',
        'tradition': 'JAPANESE',
        'view': 'side',
        'body_color': (40, 35, 30),
        'deco_color': (160, 100, 60),
        'silhouette': _raku_bowl(),
        'pattern': PAT_DOTS,
    },
    {
        'name': 'YIXING TEAPOT',
        'origin': 'CHINA  1500',
        'tradition': 'CHINESE',
        'view': 'side',
        'body_color': (120, 50, 30),
        'deco_color': (80, 35, 20),
        'silhouette': _yixing_teapot(),
        'pattern': PAT_CROSS,
    },
    {
        'name': 'PERSIAN EWER',
        'origin': 'IRAN  1200',
        'tradition': 'ISLAMIC',
        'view': 'side',
        'body_color': (210, 200, 170),
        'deco_color': (60, 160, 170),
        'silhouette': _persian_ewer(),
        'pattern': PAT_DIAMOND,
    },
]

# Build tradition ordering
TRADITIONS = []
_seen = set()
for _v in VESSELS:
    t = _v['tradition']
    if t not in _seen:
        TRADITIONS.append(t)
        _seen.add(t)

# Pre-build top-down decoration rings (computed once)
for _v in VESSELS:
    if _v['view'] == 'top':
        _v['_rings'] = _v['deco_fn'](CX, CY)
        _v['_total_rings'] = len(_v['_rings'])


# ═══════════════════════════════════════════════════════════════════
# Visual class
# ═══════════════════════════════════════════════════════════════════

class Pottery(Visual):
    name = "POTTERY"
    description = "World ceramic traditions"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self.vessel_idx = 0
        self.tradition_idx = 0
        self.revealed = 0       # rings (top-down) or rows (side)
        self.reveal_timer = 0.0
        self.hold_timer = 0.0
        self.overlay_timer = 0.0
        self._input_cooldown = 0.0

    # ── navigation helpers ──

    def _vessels_for_tradition(self, trad):
        return [i for i, v in enumerate(VESSELS) if v['tradition'] == trad]

    def _set_vessel(self, idx):
        self.vessel_idx = idx % len(VESSELS)
        self.tradition_idx = TRADITIONS.index(VESSELS[self.vessel_idx]['tradition'])
        self.revealed = 0
        self.reveal_timer = 0.0
        self.hold_timer = 0.0
        self.overlay_timer = 2.0

    def _advance(self, delta=1):
        self._set_vessel(self.vessel_idx + delta)

    def _cycle_tradition(self, delta):
        self.tradition_idx = (self.tradition_idx + delta) % len(TRADITIONS)
        trad = TRADITIONS[self.tradition_idx]
        indices = self._vessels_for_tradition(trad)
        self._set_vessel(indices[0])

    def _cycle_within_tradition(self, delta):
        trad = TRADITIONS[self.tradition_idx]
        indices = self._vessels_for_tradition(trad)
        if not indices:
            return
        try:
            pos = indices.index(self.vessel_idx)
        except ValueError:
            pos = 0
        pos = (pos + delta) % len(indices)
        self._set_vessel(indices[pos])

    def _total_steps(self, vessel):
        if vessel['view'] == 'top':
            return vessel['_total_rings']
        return len(vessel['silhouette'])

    # ── input ──

    def handle_input(self, input_state) -> bool:
        if self._input_cooldown > 0:
            return False
        consumed = False
        if input_state.up_pressed:
            self._cycle_tradition(-1)
            consumed = True
        if input_state.down_pressed:
            self._cycle_tradition(1)
            consumed = True
        if input_state.left_pressed:
            self._cycle_within_tradition(-1)
            consumed = True
        if input_state.right_pressed:
            self._cycle_within_tradition(1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._advance()
            consumed = True
        if consumed:
            self._input_cooldown = 0.15
        return consumed

    # ── update ──

    def update(self, dt: float):
        self.time += dt
        if self._input_cooldown > 0:
            self._input_cooldown -= dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        vessel = VESSELS[self.vessel_idx]
        total = self._total_steps(vessel)

        if self.revealed < total:
            self.reveal_timer += dt * BASE_ROWS_PER_SEC
            while self.reveal_timer >= 1.0 and self.revealed < total:
                self.reveal_timer -= 1.0
                self.revealed += 1
        else:
            self.hold_timer += dt
            if self.hold_timer >= HOLD_TIME:
                self._advance()

    # ── draw ──

    def _draw_top_down(self, d, vessel):
        """Draw a top-down plate/bowl with concentric ring reveal."""
        rings = vessel['_rings']
        for ring_i in range(min(self.revealed, len(rings))):
            for px, py, color in rings[ring_i]:
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, color)

        # Shimmer on the currently revealing ring
        if self.revealed < len(rings):
            ring = rings[self.revealed]
            frac = self.reveal_timer % 1.0
            n_show = int(frac * len(ring))
            for i in range(n_show):
                px, py, color = ring[i]
                bright = (
                    min(255, color[0] + 60),
                    min(255, color[1] + 60),
                    min(255, color[2] + 60),
                )
                if 0 <= px < 64 and 0 <= py < 64:
                    d.set_pixel(px, py, bright)

    def _draw_side_view(self, d, vessel):
        """Draw a side-view vessel with row-by-row decoration reveal."""
        sil = vessel['silhouette']
        body = vessel['body_color']
        deco = vessel['deco_color']
        pat = vessel['pattern']
        ph = len(pat)
        pw = len(pat[0])

        for row_i, (xl, xr) in enumerate(sil):
            y = SIDE_Y0 + row_i
            if y < 0 or y >= 64:
                continue
            for x in range(max(0, xl), min(64, xr + 1)):
                if row_i < self.revealed and pat[row_i % ph][x % pw]:
                    d.set_pixel(x, y, deco)
                else:
                    d.set_pixel(x, y, body)

        # Cursor on the decorating row
        if self.revealed < len(sil):
            cy = SIDE_Y0 + self.revealed
            if 0 <= cy < 64:
                xl, xr = sil[self.revealed]
                frac = self.reveal_timer % 1.0
                sx = xl + int(frac * max(1, xr - xl))
                bright = (
                    min(255, deco[0] + 80),
                    min(255, deco[1] + 80),
                    min(255, deco[2] + 80),
                )
                for dx in range(-1, 2):
                    px = sx + dx
                    if 0 <= px < 64:
                        d.set_pixel(px, cy, bright)

    def draw(self):
        d = self.display
        d.clear()

        vessel = VESSELS[self.vessel_idx]

        # Draw vessel
        if vessel['view'] == 'top':
            self._draw_top_down(d, vessel)
        else:
            self._draw_side_view(d, vessel)

        # Name and origin at top
        d.draw_text_small(2, 1, vessel['name'], (200, 200, 200))
        d.draw_text_small(2, 7, vessel['origin'], (110, 110, 110))

        # Tradition at bottom
        trad = vessel['tradition']
        d.draw_text_small(2, 59, trad, (100, 100, 100))

        # Overlay for navigation feedback
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(220 * alpha), int(220 * alpha), int(220 * alpha))
            d.draw_text_small(2, 30, vessel['name'], oc)

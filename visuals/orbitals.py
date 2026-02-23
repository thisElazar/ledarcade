"""
Orbitals - Quantum Probability Density Clouds
==============================================
Hydrogen-like atomic orbital shapes (s/p/d/f), molecular bonding
(sigma/pi), hybridization (sp/sp2/sp3), and delocalization (benzene,
metallic).  Data-driven architecture: scene table + generic wavefunction
renderer + group-based browsing.

Controls:
  Up/Down    - Cycle through groups
  Left/Right - Browse scenes in current group
  Both btns  - Toggle auto-cycle on/off
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ── Groups: (key, display_name, color) ──────────────────────────────

GROUPS = [
    ('s',       'S ORBITALS',   (100, 180, 255)),
    ('p',       'P ORBITALS',   (80, 255, 180)),
    ('d',       'D ORBITALS',   (255, 200, 80)),
    ('f',       'F ORBITALS',   (255, 120, 200)),
    ('sigma',   'SIGMA BONDS',  (180, 220, 255)),
    ('pi',      'PI BONDS',     (180, 255, 200)),
    ('hybrid',  'HYBRID',       (255, 230, 140)),
    ('delocal', 'DELOCALIZED',  (220, 180, 255)),
]

# ── Scene data ──────────────────────────────────────────────────────
# Each scene dict has:
#   name, desc, groups, type
#   For atomic: n, l, ml, plane (default 'xz')
#   For bonding: left, right, separation, mode ('bonding'/'antibonding')
#   For hybrid: mix ('sp','sp2','sp3')
#   For delocal: system ('benzene','metallic')
#   Optional: annotation (extra label), r_max override

SCENES = [
    # ── S orbitals ───────────────────────────────────────────────────
    {'name': '1S', 'desc': 'GROUND STATE',
     'groups': ['s'], 'type': 'atomic', 'n': 1, 'l': 0, 'ml': 0},
    {'name': '2S', 'desc': '1 RADIAL NODE',
     'groups': ['s'], 'type': 'atomic', 'n': 2, 'l': 0, 'ml': 0},
    {'name': '3S', 'desc': '2 RADIAL NODES',
     'groups': ['s'], 'type': 'atomic', 'n': 3, 'l': 0, 'ml': 0},

    # ── P orbitals ───────────────────────────────────────────────────
    {'name': '2PZ', 'desc': 'DUMBBELL Z',
     'groups': ['p'], 'type': 'atomic', 'n': 2, 'l': 1, 'ml': 0, 'plane': 'xz'},
    {'name': '2PX', 'desc': 'DUMBBELL X',
     'groups': ['p'], 'type': 'atomic', 'n': 2, 'l': 1, 'ml': 1, 'plane': 'xz'},
    {'name': '2PY', 'desc': 'DUMBBELL Y',
     'groups': ['p'], 'type': 'atomic', 'n': 2, 'l': 1, 'ml': -1, 'plane': 'yz'},
    {'name': '3PZ', 'desc': 'PZ + NODE',
     'groups': ['p'], 'type': 'atomic', 'n': 3, 'l': 1, 'ml': 0, 'plane': 'xz'},
    {'name': '3PX', 'desc': 'PX + NODE',
     'groups': ['p'], 'type': 'atomic', 'n': 3, 'l': 1, 'ml': 1, 'plane': 'xz'},

    # ── D orbitals ───────────────────────────────────────────────────
    {'name': '3DZ2', 'desc': 'DONUT + LOBES',
     'groups': ['d'], 'type': 'atomic', 'n': 3, 'l': 2, 'ml': 0, 'plane': 'xz'},
    {'name': '3DXZ', 'desc': 'CLOVERLEAF XZ',
     'groups': ['d'], 'type': 'atomic', 'n': 3, 'l': 2, 'ml': 1, 'plane': 'xz'},
    {'name': '3DX2-Y2', 'desc': 'CLOVERLEAF XY',
     'groups': ['d'], 'type': 'atomic', 'n': 3, 'l': 2, 'ml': 2, 'plane': 'xy'},
    {'name': '3DXY', 'desc': 'CLOVERLEAF 45',
     'groups': ['d'], 'type': 'atomic', 'n': 3, 'l': 2, 'ml': -2, 'plane': 'xy'},
    {'name': '3DYZ', 'desc': 'CLOVERLEAF YZ',
     'groups': ['d'], 'type': 'atomic', 'n': 3, 'l': 2, 'ml': -1, 'plane': 'yz'},

    # ── F orbitals ───────────────────────────────────────────────────
    {'name': '4FZ3', 'desc': '3 NODAL CONES',
     'groups': ['f'], 'type': 'atomic', 'n': 4, 'l': 3, 'ml': 0, 'plane': 'xz'},
    {'name': '4FXZ2', 'desc': 'XZ PLANE LOBES',
     'groups': ['f'], 'type': 'atomic', 'n': 4, 'l': 3, 'ml': 1, 'plane': 'xz'},
    {'name': '4FYZ2', 'desc': 'YZ PLANE LOBES',
     'groups': ['f'], 'type': 'atomic', 'n': 4, 'l': 3, 'ml': -1, 'plane': 'yz'},
    {'name': '4FXYZ', 'desc': '8 CUBIC LOBES',
     'groups': ['f'], 'type': 'atomic', 'n': 4, 'l': 3, 'ml': -2, 'plane': 'xz'},
    {'name': '4FZ(X2-Y2)', 'desc': '6 LOBES',
     'groups': ['f'], 'type': 'atomic', 'n': 4, 'l': 3, 'ml': 2, 'plane': 'xz'},
    {'name': '4FX(X2-3Y2)', 'desc': 'HEXAGONAL X',
     'groups': ['f'], 'type': 'atomic', 'n': 4, 'l': 3, 'ml': 3, 'plane': 'xy'},
    {'name': '4FY(3X2-Y2)', 'desc': 'HEXAGONAL Y',
     'groups': ['f'], 'type': 'atomic', 'n': 4, 'l': 3, 'ml': -3, 'plane': 'xy'},

    # ── Sigma bonds ──────────────────────────────────────────────────
    {'name': 'SIGMA BOND', 'desc': 'H2 BONDING',
     'groups': ['sigma'], 'type': 'bonding',
     'left': {'n': 1, 'l': 0, 'ml': 0}, 'right': {'n': 1, 'l': 0, 'ml': 0},
     'separation': 1.4, 'mode': 'bonding'},
    {'name': 'SIGMA STAR', 'desc': 'H2 ANTIBONDING',
     'groups': ['sigma'], 'type': 'bonding',
     'left': {'n': 1, 'l': 0, 'ml': 0}, 'right': {'n': 1, 'l': 0, 'ml': 0},
     'separation': 1.4, 'mode': 'antibonding'},
    {'name': 'SP3-SP3', 'desc': 'C-C SIGMA',
     'groups': ['sigma'], 'type': 'bonding',
     'left': {'n': 2, 'l': 0, 'ml': 0}, 'right': {'n': 2, 'l': 0, 'ml': 0},
     'separation': 2.6, 'mode': 'bonding'},
    {'name': 'HE2', 'desc': 'BOND ORDER 0',
     'groups': ['sigma'], 'type': 'bonding',
     'left': {'n': 1, 'l': 0, 'ml': 0}, 'right': {'n': 1, 'l': 0, 'ml': 0},
     'separation': 1.4, 'mode': 'he2', 'annotation': 'BOND ORDER 0'},

    # ── Pi bonds ─────────────────────────────────────────────────────
    {'name': 'PI BOND', 'desc': 'SIDE-ON OVERLAP',
     'groups': ['pi'], 'type': 'bonding',
     'left': {'n': 2, 'l': 1, 'ml': 0}, 'right': {'n': 2, 'l': 1, 'ml': 0},
     'separation': 2.4, 'mode': 'bonding', 'bond_axis': 'x'},
    {'name': 'PI STAR', 'desc': 'ANTIBONDING PI',
     'groups': ['pi'], 'type': 'bonding',
     'left': {'n': 2, 'l': 1, 'ml': 0}, 'right': {'n': 2, 'l': 1, 'ml': 0},
     'separation': 2.4, 'mode': 'antibonding', 'bond_axis': 'x'},
    {'name': 'O2 PI', 'desc': 'PARAMAGNETIC!',
     'groups': ['pi'], 'type': 'bonding',
     'left': {'n': 2, 'l': 1, 'ml': 0}, 'right': {'n': 2, 'l': 1, 'ml': 0},
     'separation': 2.2, 'mode': 'bonding', 'bond_axis': 'x',
     'annotation': 'PARAMAGNETIC!'},

    # ── Hybrid orbitals ──────────────────────────────────────────────
    {'name': 'SP', 'desc': 'LINEAR 180',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp'},
    {'name': 'SP2', 'desc': 'TRIGONAL 120',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp2'},
    {'name': 'SP3', 'desc': 'TETRAHEDRAL 109',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp3'},
    {'name': 'SP3D', 'desc': 'TRIG BIPYRAMID',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp3d'},
    {'name': 'SP3D2', 'desc': 'OCTAHEDRAL 90',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp3d2'},
    {'name': 'CO2', 'desc': 'SP LINEAR',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp_co2'},
    {'name': 'BF3', 'desc': 'SP2 PLANAR',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp2_bef3'},
    {'name': 'NH3', 'desc': 'SP3 + LONE PAIR',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp3_nh3'},
    {'name': 'H2O', 'desc': 'SP3 + 2 LONE PR',
     'groups': ['hybrid'], 'type': 'hybrid', 'mix': 'sp3_h2o'},

    # ── Delocalized ──────────────────────────────────────────────────
    {'name': 'BENZENE PI', 'desc': 'AROMATIC RING',
     'groups': ['delocal'], 'type': 'delocal', 'system': 'benzene'},
    {'name': 'METAL BAND', 'desc': 'ELECTRON SEA',
     'groups': ['delocal'], 'type': 'delocal', 'system': 'metallic'},
]


# ── Wavefunction math ───────────────────────────────────────────────
# Hydrogen-like radial × angular, hard-coded polynomials.
# We work in atomic units where a0 = 1.

def _radial(n, l, r):
    """Radial wavefunction R(n,l,r) (un-normalized — we normalize visually)."""
    rho = r / n  # scaled radius
    if n == 1 and l == 0:
        return math.exp(-rho)
    if n == 2 and l == 0:
        return (2.0 - r) * math.exp(-rho)
    if n == 2 and l == 1:
        return r * math.exp(-rho)
    if n == 3 and l == 0:
        return (27.0 - 18.0 * r + 2.0 * r * r) * math.exp(-rho)
    if n == 3 and l == 1:
        return r * (6.0 - r) * math.exp(-rho)
    if n == 3 and l == 2:
        return r * r * math.exp(-rho)
    if n == 4 and l == 0:
        return (192.0 - 144.0 * r + 24.0 * r * r - r * r * r) * math.exp(-rho)
    if n == 4 and l == 1:
        return r * (80.0 - 20.0 * r + r * r) * math.exp(-rho)
    if n == 4 and l == 2:
        return r * r * (12.0 - r) * math.exp(-rho)
    if n == 4 and l == 3:
        return r * r * r * math.exp(-rho)
    return 0.0


def _angular(l, ml, x, y, z, r):
    """Real spherical harmonic Y(l,ml) given Cartesian coords + radius.
    Returns signed value for phase coloring."""
    if r < 1e-12:
        return 1.0 if l == 0 else 0.0

    # l = 0: s
    if l == 0:
        return 1.0

    # l = 1: p orbitals
    if l == 1:
        if ml == 0:    # pz: cos(theta) = z/r
            return z / r
        if ml == 1:    # px: sin(theta)cos(phi) = x/r
            return x / r
        if ml == -1:   # py: sin(theta)sin(phi) = y/r
            return y / r

    # l = 2: d orbitals
    if l == 2:
        rr = r * r
        if ml == 0:    # dz2: (3z^2 - r^2) / r^2
            return (3.0 * z * z - rr) / rr
        if ml == 1:    # dxz: xz / r^2
            return x * z / rr
        if ml == -1:   # dyz: yz / r^2
            return y * z / rr
        if ml == 2:    # dx2-y2: (x^2 - y^2) / r^2
            return (x * x - y * y) / rr
        if ml == -2:   # dxy: xy / r^2
            return x * y / rr

    # l = 3: f orbitals
    if l == 3:
        rr = r * r
        r3 = rr * r
        if ml == 0:    # fz3: z(5z^2 - 3r^2) / r^3
            return z * (5.0 * z * z - 3.0 * rr) / r3
        if ml == 1:    # fxz2: x(5z^2 - r^2) / r^3
            return x * (5.0 * z * z - rr) / r3
        if ml == -1:   # fyz2: y(5z^2 - r^2) / r^3
            return y * (5.0 * z * z - rr) / r3
        if ml == 2:    # fz(x2-y2): z(x^2 - y^2) / r^3
            return z * (x * x - y * y) / r3
        if ml == -2:   # fxyz: xyz / r^3
            return x * y * z / r3
        if ml == 3:    # fx(x2-3y2): x(x^2 - 3y^2) / r^3
            return x * (x * x - 3.0 * y * y) / r3
        if ml == -3:   # fy(3x2-y2): y(3x^2 - y^2) / r^3
            return y * (3.0 * x * x - y * y) / r3

    return 0.0


def _psi_atomic(n, l, ml, px, py, plane='xz'):
    """Evaluate wavefunction at pixel coords (px, py) on given plane.
    Returns signed float. px maps to first axis, py maps to second (screen-up = +z)."""
    # Map pixel coords to 3D Cartesian based on plane slice
    if plane == 'xz':
        x, y, z = px, 0.0, -py  # screen-up = +z
    elif plane == 'yz':
        x, y, z = 0.0, px, -py
    elif plane == 'xy':
        x, y, z = px, -py, 0.0  # z=0 slice
    else:
        x, y, z = px, 0.0, -py

    r = math.sqrt(x * x + y * y + z * z)
    R = _radial(n, l, r)
    Y = _angular(l, ml, x, y, z, r)
    return R * Y


def _auto_rmax(n, l):
    """Choose a display radius that captures most of the density."""
    # Rough rule: outermost peak ≈ n^2, but we want some space beyond
    base = {
        (1, 0): 5.0,
        (2, 0): 12.0, (2, 1): 10.0,
        (3, 0): 22.0, (3, 1): 20.0, (3, 2): 16.0,
        (4, 0): 36.0, (4, 1): 32.0, (4, 2): 28.0, (4, 3): 22.0,
    }
    return base.get((n, l), n * n * 3.0)


# ── Grid computation ────────────────────────────────────────────────

# Display area: full 64×64 panel — labels overlay on top
DISP_W = 64
DISP_H = 64

# Phase colors: positive → blue, negative → red
COLOR_POS = (60, 140, 255)   # blue
COLOR_NEG = (255, 60, 80)    # red


def _compute_atomic_grid(scene):
    """Compute 64×48 signed-float grid for an atomic orbital."""
    n, l, ml = scene['n'], scene['l'], scene['ml']
    plane = scene.get('plane', 'xz')
    r_max = scene.get('r_max', _auto_rmax(n, l))

    grid = []
    half = DISP_H / 2.0  # square mapping: same scale both axes
    for py in range(DISP_H):
        row = []
        cy = (py - half + 0.5) / half * r_max
        for px in range(DISP_W):
            cx = (px - DISP_W / 2.0 + 0.5) / half * r_max
            row.append(_psi_atomic(n, l, ml, cx, cy, plane))
        grid.append(row)
    return grid


def _compute_bonding_grid(scene):
    """Compute grid for a two-center bonding/antibonding scene.
    Returns (grid, meta) where meta has r_max, bond_axis, sep."""
    left = scene['left']
    right = scene['right']
    sep = scene['separation']
    mode = scene['mode']
    bond_axis = scene.get('bond_axis', 'z')

    n1, l1, ml1 = left['n'], left['l'], left['ml']
    n2, l2, ml2 = right['n'], right['l'], right['ml']

    r_max1 = _auto_rmax(n1, l1)
    r_max2 = _auto_rmax(n2, l2)
    r_max = max(r_max1, r_max2) + sep

    sign = 1.0 if mode in ('bonding', 'he2') else -1.0

    half = DISP_H / 2.0
    grid = []
    for py in range(DISP_H):
        row = []
        cy = (py - half + 0.5) / half * r_max
        for px in range(DISP_W):
            cx = (px - DISP_W / 2.0 + 0.5) / half * r_max

            if bond_axis == 'x':
                psi1 = _psi_atomic(n1, l1, ml1, cx + sep / 2, cy, 'xz')
                psi2 = _psi_atomic(n2, l2, ml2, cx - sep / 2, cy, 'xz')
            else:
                psi1 = _psi_atomic(n1, l1, ml1, cx, cy + sep / 2, 'xz')
                psi2 = _psi_atomic(n2, l2, ml2, cx, cy - sep / 2, 'xz')

            row.append(psi1 + sign * psi2)
        grid.append(row)

    meta = {'r_max': r_max, 'bond_axis': bond_axis, 'sep': sep}
    return grid, meta


def _compute_hybrid_grid(scene):
    """Compute multi-channel grid for hybrid orbitals. Returns list of (grid, color)."""
    mix = scene['mix']

    # Hybrid orbital directions and colors (subdued for LED readability)
    if mix == 'sp':
        directions = [
            (1.0, 0.0, 1.0, (0, 140, 180)),     # +z: cyan
            (1.0, 0.0, -1.0, (180, 140, 0)),     # -z: amber
        ]
    elif mix == 'sp2':
        s3 = math.sqrt(3.0)
        directions = [
            (1.0, 1.0, 0.0, (0, 140, 180)),            # cyan
            (1.0, -0.5, s3 / 2.0, (180, 140, 0)),      # amber
            (1.0, -0.5, -s3 / 2.0, (0, 180, 90)),      # green
        ]
    elif mix == 'sp3':
        directions = [
            (1.0, 1.0, 1.0, (0, 140, 180)),        # cyan
            (1.0, -1.0, -1.0, (180, 140, 0)),      # amber
            (1.0, 1.0, -1.0, (0, 180, 90)),        # green
            (1.0, -1.0, 1.0, (180, 90, 20)),       # orange
        ]
    elif mix == 'sp3d':
        # Trigonal bipyramidal: 3 equatorial (120 deg) + 2 axial
        s3 = math.sqrt(3.0)
        directions = [
            (1.0, 1.0, 0.0, (0, 140, 180)),            # eq 1: cyan
            (1.0, -0.5, s3 / 2.0, (180, 140, 0)),      # eq 2: amber
            (1.0, -0.5, -s3 / 2.0, (0, 180, 90)),      # eq 3: green
            (1.0, 0.0, 1.0, (180, 90, 20)),             # axial +z: orange
            (1.0, 0.0, -1.0, (140, 60, 160)),           # axial -z: purple
        ]
    elif mix == 'sp3d2':
        # Octahedral: 6 directions along ±x, ±y, ±z
        directions = [
            (1.0, 1.0, 0.0, (0, 140, 180)),        # +x: cyan
            (1.0, -1.0, 0.0, (180, 140, 0)),       # -x: amber
            (1.0, 0.0, 1.0, (0, 180, 90)),         # +z: green
            (1.0, 0.0, -1.0, (180, 90, 20)),       # -z: orange
            (1.0, 0.7, 0.7, (140, 60, 160)),       # +y proj: purple
            (1.0, -0.7, -0.7, (160, 120, 140)),    # -y proj: mauve
        ]
    elif mix == 'sp2_bef3':
        # BF3: sp2 but viewed with B center + 3 equivalent lobes
        s3 = math.sqrt(3.0)
        directions = [
            (1.0, 0.0, 1.0, (0, 140, 180)),
            (1.0, s3 / 2.0, -0.5, (180, 140, 0)),
            (1.0, -s3 / 2.0, -0.5, (0, 180, 90)),
        ]
    elif mix == 'sp_co2':
        # CO2-style: two sp hybrids along x-axis + leftover p orbitals shown dimly
        directions = [
            (1.0, 1.0, 0.0, (0, 140, 180)),
            (1.0, -1.0, 0.0, (180, 140, 0)),
        ]
    elif mix == 'sp3_nh3':
        # NH3: sp3 tetrahedral, lone pair up, 3 N-H bonds down
        directions = [
            (1.0, 0.0, 1.0, (80, 80, 140)),             # lone pair: dim blue
            (1.0, 0.943, -0.333, (0, 140, 180)),        # N-H: cyan
            (1.0, -0.471, -0.333, (180, 140, 0)),       # N-H: amber (left-back)
            (1.0, -0.471, -0.333, (0, 180, 90)),        # N-H: green (right-back)
        ]
        # Spread the two back bonds apart in the y-component (out of xz plane)
        # so they're distinct in the 2D projection
        directions[2] = (1.0, -0.816, -0.333, (180, 140, 0))
        directions[3] = (1.0, -0.127, -0.333, (0, 180, 90))
    elif mix == 'sp3_h2o':
        # H2O: sp3 with two lone pairs + two bond pairs
        directions = [
            (1.0, 0.6, 0.8, (80, 80, 140)),        # lone pair 1: dim blue
            (1.0, -0.6, 0.8, (80, 80, 140)),       # lone pair 2: dim blue
            (1.0, 0.6, -0.8, (0, 140, 180)),       # O-H bond: cyan
            (1.0, -0.6, -0.8, (180, 140, 0)),      # O-H bond: amber
        ]
    else:  # fallback to sp3
        directions = [
            (1.0, 1.0, 1.0, (0, 140, 180)),
            (1.0, -1.0, -1.0, (180, 140, 0)),
            (1.0, 1.0, -1.0, (0, 180, 90)),
            (1.0, -1.0, 1.0, (180, 90, 20)),
        ]

    r_max = 12.0
    channels = []

    for s_coeff, px_dir, pz_dir, color in directions:
        # Normalize direction
        mag = math.sqrt(px_dir * px_dir + pz_dir * pz_dir)
        if mag > 0:
            px_dir /= mag
            pz_dir /= mag

        half = DISP_H / 2.0
        grid = []
        for py in range(DISP_H):
            row = []
            cy = (py - half + 0.5) / half * r_max
            for px_coord in range(DISP_W):
                cx = (px_coord - DISP_W / 2.0 + 0.5) / half * r_max

                r = math.sqrt(cx * cx + cy * cy)
                # s component: R(2,0) × Y(0,0)
                s_part = _radial(2, 0, r) * 1.0
                # p component: R(2,1) × direction dot
                # project (cx, -cy) onto direction (px_dir, pz_dir) for angular part
                proj = (cx * px_dir + (-cy) * pz_dir) / (r + 1e-12)
                p_part = _radial(2, 1, r) * proj

                # Mix: hybrid = (s + sqrt(N-1)*p) / sqrt(N)
                n_hybrids = len(directions)
                psi = (s_part + math.sqrt(n_hybrids - 1) * p_part) / math.sqrt(n_hybrids)
                row.append(psi)
            grid.append(row)
        channels.append((grid, color))

    return channels


def _compute_delocal_grid(scene):
    """Compute grid for delocalized systems.
    Returns (grid, meta) where meta has centers, r_max."""
    system = scene['system']

    if system == 'benzene':
        r_hex = 5.0
        r_max = 14.0
        centers = []
        for i in range(6):
            angle = i * math.pi / 3.0
            centers.append((r_hex * math.cos(angle), r_hex * math.sin(angle)))

        half = DISP_H / 2.0
        grid = []
        for py in range(DISP_H):
            row = []
            cy = (py - half + 0.5) / half * r_max
            for px in range(DISP_W):
                cx = (px - DISP_W / 2.0 + 0.5) / half * r_max
                total = 0.0
                for (ax, az) in centers:
                    dx = cx - ax
                    dz = (-cy) - az
                    r = math.sqrt(dx * dx + dz * dz)
                    total += _radial(2, 1, r) * math.exp(-r * 0.3)
                row.append(total)
            grid.append(row)
        return grid, {'centers': centers, 'r_max': r_max}

    else:  # metallic
        r_max = 24.0
        n_atoms = 8
        spacing = 4.0
        start_x = -(n_atoms - 1) * spacing / 2.0
        centers = [(start_x + i * spacing, 0.0) for i in range(n_atoms)]

        half = DISP_H / 2.0
        grid = []
        for py in range(DISP_H):
            row = []
            cy = (py - half + 0.5) / half * r_max
            for px in range(DISP_W):
                cx = (px - DISP_W / 2.0 + 0.5) / half * r_max
                total = 0.0
                for (ax, az) in centers:
                    dx = cx - ax
                    dz = (-cy) - az
                    r = math.sqrt(dx * dx + dz * dz)
                    total += _radial(2, 0, r)
                row.append(total)
            grid.append(row)
        return grid, {'centers': centers, 'r_max': r_max}


# ── Build group indices ─────────────────────────────────────────────

def _build_group_indices():
    """Build mapping from group key to list of SCENES indices."""
    groups = {}
    for i, sc in enumerate(SCENES):
        for g in sc['groups']:
            groups.setdefault(g, []).append(i)
    return groups


# ── Orbitals visual class ───────────────────────────────────────────

class Orbitals(Visual):
    name = "ORBITALS"
    description = "Quantum probability density clouds"
    category = "science_micro"

    _saved_group_idx = None
    _saved_scene_pos = None
    _saved_render_mode = 0

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()

        if Orbitals._saved_group_idx is not None:
            self.group_idx = Orbitals._saved_group_idx
            self.scene_pos = Orbitals._saved_scene_pos
        else:
            self.group_idx = 0
            self.scene_pos = 0

        self.auto_cycle = False
        self.cycle_timer = 0.0
        self.cycle_duration = 10.0
        self.overlay_timer = 2.5  # Show initial group name
        self.label_timer = 0.0
        # Render mode: 0=dots, 1=heatmap, 2=combined
        self.render_mode = Orbitals._saved_render_mode
        self._mode_names = ['PROBABILITY', 'DENSITY', 'COMBINED']
        self._mode_timer = 0.0  # overlay for mode name
        self._prev_up = False
        self._prev_down = False
        self._prev_left = False
        self._prev_right = False

        # Cached rendering data
        self._grid = None
        self._grid_meta = None
        self._hybrid_channels = None
        self._scene_type = None
        self._prepare_scene()

    def _current_scene_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_scene_index(self):
        scene_list = self._current_scene_list()
        if not scene_list:
            return 0
        return scene_list[self.scene_pos % len(scene_list)]

    def _current_scene(self):
        return SCENES[self._current_scene_index()]

    def _prepare_scene(self):
        """Pre-compute grids, probability sampler, and dot pool."""
        scene = self._current_scene()
        self._scene_type = scene['type']
        self._grid_meta = None
        self._grid = None
        self._grid_max = 1.0
        self._hybrid_channels = None
        self._channel_maxes = None
        self.label_timer = 0.0

        if scene['type'] == 'atomic':
            grid = _compute_atomic_grid(scene)
            self._stash_grid(grid)
            self._build_sampler_single(grid)
        elif scene['type'] == 'bonding':
            grid, self._grid_meta = _compute_bonding_grid(scene)
            self._stash_grid(grid)
            self._build_sampler_single(grid)
        elif scene['type'] == 'hybrid':
            channels = _compute_hybrid_grid(scene)
            self._stash_hybrid(channels)
            self._build_sampler_hybrid(channels)
        elif scene['type'] == 'delocal':
            grid, self._grid_meta = _compute_delocal_grid(scene)
            self._stash_grid(grid)
            self._build_sampler_single(grid)
        else:
            self._sample_table = []
            self._sample_cum = []

        # Reset dot pool
        self._dots = []
        self._dot_target = 600
        self._spawn_dots(self._dot_target)

        Orbitals._saved_group_idx = self.group_idx
        Orbitals._saved_scene_pos = self.scene_pos

    def _stash_grid(self, grid):
        """Keep grid + max for heatmap rendering."""
        self._grid = grid
        gmax = 0.0
        for row in grid:
            for v in row:
                av = abs(v)
                if av > gmax:
                    gmax = av
        self._grid_max = gmax if gmax > 1e-20 else 1.0

    def _stash_hybrid(self, channels):
        """Keep hybrid channel grids + maxes for heatmap rendering."""
        self._hybrid_channels = channels
        self._channel_maxes = []
        for grid, color in channels:
            mx = 0.0
            for row in grid:
                for v in row:
                    av = abs(v)
                    if av > mx:
                        mx = av
            self._channel_maxes.append(mx if mx > 1e-20 else 1.0)

    def _build_sampler_single(self, grid):
        """Build weighted sampling table from a single signed-psi grid.
        Each entry: (px, py, color)."""
        gamma_s = 0.5  # sampling gamma — controls spread of dots
        table = []     # (px, py, color, weight)
        cum = []       # cumulative weights for binary search

        gmax = 0.0
        for row in grid:
            for v in row:
                av = abs(v)
                if av > gmax:
                    gmax = av
        if gmax < 1e-20:
            self._sample_table = []
            self._sample_cum = []
            self._sample_total = 0.0
            return

        running = 0.0
        for py in range(DISP_H):
            row = grid[py]
            for px in range(DISP_W):
                psi = row[px]
                val = abs(psi) / gmax
                if val < 0.01:
                    continue
                w = pow(val, gamma_s)
                color = COLOR_POS if psi >= 0 else COLOR_NEG
                table.append((px, py, color))
                running += w
                cum.append(running)

        self._sample_table = table
        self._sample_cum = cum
        self._sample_total = running

    def _build_sampler_hybrid(self, channels):
        """Build weighted sampling table from multiple hybrid channels.
        Dots get their channel's color."""
        gamma_s = 0.5
        table = []
        cum = []

        # Find per-channel max
        channel_maxes = []
        for grid, color in channels:
            mx = 0.0
            for row in grid:
                for v in row:
                    av = abs(v)
                    if av > mx:
                        mx = av
            channel_maxes.append(mx if mx > 1e-20 else 1.0)

        running = 0.0
        for ch_idx, (grid, color) in enumerate(channels):
            ch_max = channel_maxes[ch_idx]
            for py in range(DISP_H):
                row = grid[py]
                for px in range(DISP_W):
                    psi = row[px]
                    val = abs(psi) / ch_max
                    if val < 0.01:
                        continue
                    w = pow(val, gamma_s)
                    table.append((px, py, color))
                    running += w
                    cum.append(running)

        self._sample_table = table
        self._sample_cum = cum
        self._sample_total = running

    def _sample_one(self):
        """Sample one (px, py, color) from the probability table."""
        if not self._sample_table:
            return None
        r = random.random() * self._sample_total
        # Binary search in cumulative array
        lo, hi = 0, len(self._sample_cum) - 1
        while lo < hi:
            mid = (lo + hi) >> 1
            if self._sample_cum[mid] < r:
                lo = mid + 1
            else:
                hi = mid
        return self._sample_table[lo]

    def _spawn_dots(self, count):
        """Spawn count new dots into the pool."""
        if not self._sample_table:
            return
        for _ in range(count):
            sample = self._sample_one()
            if sample is None:
                continue
            px, py, color = sample
            lifetime = 0.6 + random.random() * 1.0  # 0.6–1.6s
            self._dots.append([px, py, color, self.time, lifetime])

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Edge detection for directions
        up_edge = input_state.up and not self._prev_up
        down_edge = input_state.down and not self._prev_down
        left_edge = input_state.left and not self._prev_left
        right_edge = input_state.right and not self._prev_right

        # Up/Down: cycle groups
        if up_edge:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.scene_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_scene()
            consumed = True
        elif down_edge:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.scene_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            self._prepare_scene()
            consumed = True

        # Left/Right: cycle scenes within group
        if left_edge:
            scene_list = self._current_scene_list()
            if scene_list:
                self.scene_pos = (self.scene_pos - 1) % len(scene_list)
            self.cycle_timer = 0.0
            self._prepare_scene()
            consumed = True
        elif right_edge:
            scene_list = self._current_scene_list()
            if scene_list:
                self.scene_pos = (self.scene_pos + 1) % len(scene_list)
            self.cycle_timer = 0.0
            self._prepare_scene()
            consumed = True

        # Action button (either/both): cycle render mode
        action = input_state.action_l or input_state.action_r
        if action:
            self.render_mode = (self.render_mode + 1) % 3
            Orbitals._saved_render_mode = self.render_mode
            self._mode_timer = 2.0
            consumed = True
        self._prev_up = input_state.up
        self._prev_down = input_state.down
        self._prev_left = input_state.left
        self._prev_right = input_state.right

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self._mode_timer > 0:
            self._mode_timer = max(0.0, self._mode_timer - dt)

        # Cull expired dots and spawn replacements
        now = self.time
        self._dots = [d for d in self._dots if now - d[3] < d[4]]
        deficit = self._dot_target - len(self._dots)
        if deficit > 0:
            self._spawn_dots(deficit)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                scene_list = self._current_scene_list()
                if scene_list:
                    self.scene_pos = (self.scene_pos + 1) % len(scene_list)
                self._prepare_scene()

    def draw(self):
        self.display.clear(Colors.BLACK)
        scene = self._current_scene()

        # Delocal skeleton goes underneath everything
        if self._scene_type == 'delocal':
            self._draw_delocal_skeleton(scene)

        # Render based on mode
        if self.render_mode == 0:
            self._draw_dots()
        elif self.render_mode == 1:
            self._draw_heatmap()
        else:  # combined
            self._draw_heatmap(dim=0.35)
            self._draw_dots()

        # Nucleus markers for bonding scenes
        if self._scene_type == 'bonding':
            self._draw_nuclei(scene)

        # Labels overlay
        self._draw_labels(scene)

        # Group overlay at top
        if self.overlay_timer > 0:
            _, gname, gcolor = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(gcolor[0] * alpha), int(gcolor[1] * alpha),
                  int(gcolor[2] * alpha))
            self.display.draw_text_small(2, 2, gname, oc)

        # Mode name overlay (bottom-right, fades)
        if self._mode_timer > 0:
            alpha = min(1.0, self._mode_timer / 0.4)
            mc = (int(180 * alpha), int(180 * alpha), int(180 * alpha))
            name = self._mode_names[self.render_mode]
            x = DISP_W - len(name) * 4 - 1
            self.display.draw_text_small(x, 2, name, mc)

    def _draw_dots(self):
        """Draw Monte Carlo probability dots with fade envelope."""
        now = self.time
        fade_in = 0.1
        fade_out = 0.25
        for dot in self._dots:
            px, py, color, birth, lifetime = dot
            age = now - birth
            remaining = lifetime - age
            if age < fade_in:
                alpha = age / fade_in
            elif remaining < fade_out:
                alpha = remaining / fade_out
            else:
                alpha = 1.0
            c = (int(color[0] * alpha),
                 int(color[1] * alpha),
                 int(color[2] * alpha))
            self.display.set_pixel(px, py, c)

    def _draw_heatmap(self, dim=1.0):
        """Draw smooth density heatmap from cached grid."""
        gamma = 0.45
        if self._scene_type == 'hybrid' and self._hybrid_channels is not None:
            self._draw_heatmap_hybrid(gamma, dim)
            return
        grid = self._grid
        if grid is None:
            return
        gmax = self._grid_max
        for py in range(DISP_H):
            row = grid[py]
            for px in range(DISP_W):
                psi = row[px]
                if abs(psi) < gmax * 0.005:
                    continue
                val = abs(psi) / gmax
                bright = min(1.0, pow(val, gamma)) * dim
                if psi >= 0:
                    c = (int(COLOR_POS[0] * bright),
                         int(COLOR_POS[1] * bright),
                         int(COLOR_POS[2] * bright))
                else:
                    c = (int(COLOR_NEG[0] * bright),
                         int(COLOR_NEG[1] * bright),
                         int(COLOR_NEG[2] * bright))
                self.display.set_pixel(px, py, c)

    def _draw_heatmap_hybrid(self, gamma, dim):
        """Draw multi-colored hybrid heatmap additively."""
        buf = [[(0.0, 0.0, 0.0) for _ in range(DISP_W)] for _ in range(DISP_H)]
        for ch_idx, (grid, color) in enumerate(self._hybrid_channels):
            ch_max = self._channel_maxes[ch_idx]
            for py in range(DISP_H):
                row = grid[py]
                for px in range(DISP_W):
                    psi = row[px]
                    val = abs(psi) / ch_max
                    if val < 0.005:
                        continue
                    bright = pow(val, gamma) * dim
                    r, g, b = buf[py][px]
                    buf[py][px] = (r + color[0] * bright,
                                   g + color[1] * bright,
                                   b + color[2] * bright)
        for py in range(DISP_H):
            for px in range(DISP_W):
                r, g, b = buf[py][px]
                if r + g + b < 2.0:
                    continue
                c = (min(255, int(r)), min(255, int(g)), min(255, int(b)))
                self.display.set_pixel(px, py, c)

    def _draw_delocal_skeleton(self, scene):
        """Draw faint skeleton lines for delocalized systems."""
        meta = self._grid_meta or {}
        if scene.get('system') == 'benzene' and 'centers' in meta:
            centers = meta['centers']
            r_max = meta['r_max']
            skel_color = (30, 45, 30)
            half = DISP_H / 2.0
            pts = []
            for (ax, az) in centers:
                sx = int(DISP_W / 2.0 + ax / r_max * half)
                sy = int(half - az / r_max * half)
                pts.append((sx, sy))
            for i in range(6):
                x1, y1 = pts[i]
                x2, y2 = pts[(i + 1) % 6]
                self.display.draw_line(x1, y1, x2, y2, skel_color)

    def _draw_nuclei(self, scene):
        """Draw small nucleus markers for bonding scenes."""
        meta = self._grid_meta or {}
        sep = meta.get('sep', scene['separation'])
        bond_axis = meta.get('bond_axis', scene.get('bond_axis', 'z'))
        r_max = meta.get('r_max', 10.0)
        half = DISP_H / 2.0

        nuc_color = (255, 255, 255)

        if bond_axis == 'x':
            for sign in (-1, 1):
                phys_x = sign * sep / 2.0
                sx = int(DISP_W / 2.0 + phys_x / r_max * half)
                sy = DISP_H // 2
                self.display.set_pixel(sx, sy, nuc_color)
                self.display.set_pixel(sx - 1, sy, nuc_color)
                self.display.set_pixel(sx + 1, sy, nuc_color)
                self.display.set_pixel(sx, sy - 1, nuc_color)
                self.display.set_pixel(sx, sy + 1, nuc_color)
        else:
            for sign in (-1, 1):
                phys_z = sign * sep / 2.0
                sx = DISP_W // 2
                sy = int(half - phys_z / r_max * half)
                self.display.set_pixel(sx, sy, nuc_color)
                self.display.set_pixel(sx - 1, sy, nuc_color)
                self.display.set_pixel(sx + 1, sy, nuc_color)
                self.display.set_pixel(sx, sy - 1, nuc_color)
                self.display.set_pixel(sx, sy + 1, nuc_color)

    def _draw_labels(self, scene):
        """Draw cycling labels overlaid at the bottom of the density."""
        phase = int(self.label_timer / 5.0) % 3
        y_label = 58  # bottom of 64px display

        if phase == 0:
            self.display.draw_text_small(2, y_label, scene['name'], Colors.WHITE)
        elif phase == 1:
            self.display.draw_text_small(2, y_label, scene['desc'], (200, 200, 200))
        else:
            if scene['type'] == 'atomic':
                qn = 'N=%d L=%d ML=%d' % (scene['n'], scene['l'], scene['ml'])
                self.display.draw_text_small(2, y_label, qn, (160, 160, 220))
            elif scene['type'] == 'bonding':
                self.display.draw_text_small(2, y_label,
                                             scene.get('annotation', scene['mode'].upper()),
                                             (220, 200, 160))
            elif scene['type'] == 'hybrid':
                self.display.draw_text_small(2, y_label, scene['mix'].upper(),
                                             (220, 220, 160))
            elif scene['type'] == 'delocal':
                self.display.draw_text_small(2, y_label,
                                             scene.get('system', '').upper(),
                                             (200, 160, 220))

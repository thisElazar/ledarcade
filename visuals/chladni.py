"""
Chladni Plates – Vibrating Plate Nodal Patterns
================================================
Sand settles at nodal lines on a vibrating plate,
revealing standing wave patterns.

Six plate geometries, each with its own physics:
  Square    — Ritz antisymmetric: cos(nπx)cos(mπy) − cos(mπx)cos(nπy)
  Circle    — Bessel functions J_m(k·r)·cos(mθ)
  Rectangle — 3:2 aspect Ritz formula
  Hexagon   — three-axis plane-wave superposition at 120° intervals
  Triangle  — barycentric eigenmodes on equilateral triangle
  Annular   — radial sin modes on a ring with angular cos(mθ)

Controls:
  Left/Right (held) - Sweep frequency continuously
  Up/Down (pressed) - Cycle plate shape
  Action            - Scatter sand
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

SHAPES = [
    ('SQUARE', 'square'),
    ('CIRCLE', 'circle'),
    ('RECTANGLE', 'rect'),
    ('HEXAGON', 'hex'),
    ('TRIANGLE', 'tri'),
    ('ANNULAR', 'ring'),
]

# Sand color palette — slight per-pixel variation for texture
SAND_COLORS = [
    (220, 190, 130),
    (240, 210, 150),
    (200, 170, 110),
    (230, 200, 140),
    (250, 220, 160),
]

PLATE_COLOR = (15, 12, 10)

DRAW_SIZE = 48
DRAW_OFFSET_X = (GRID_SIZE - DRAW_SIZE) // 2
DRAW_OFFSET_Y = 8

# Gaussian width controlling sand line thickness in amplitude space
LINE_SIGMA = 0.10

# ── Geometry constants ────────────────────────────────────────────
_S3 = math.sqrt(3)
_S3_2 = _S3 / 2.0

# Hexagon (flat-top, circumradius)
_HEX_R = 0.49
_HEX_HALF_H = _HEX_R * _S3_2   # half-height
_HEX_EDGE = _S3_2 * _HEX_R     # for angled-facet test

# Equilateral triangle (apex up, circumradius)
_TRI_R = 0.49
_TRI_V1 = (0.5, 0.5 - _TRI_R)                          # top
_TRI_V2 = (0.5 - _TRI_R * _S3_2, 0.5 + _TRI_R * 0.5)  # bottom-left
_TRI_V3 = (0.5 + _TRI_R * _S3_2, 0.5 + _TRI_R * 0.5)  # bottom-right
_TRI_DENOM = ((_TRI_V2[1] - _TRI_V3[1]) * (_TRI_V1[0] - _TRI_V3[0])
              + (_TRI_V3[0] - _TRI_V2[0]) * (_TRI_V1[1] - _TRI_V3[1]))
# Precompute coefficients for barycentric lambda calc
_TRI_A1 = _TRI_V2[1] - _TRI_V3[1]
_TRI_B1 = _TRI_V3[0] - _TRI_V2[0]
_TRI_A2 = _TRI_V3[1] - _TRI_V1[1]
_TRI_B2 = _TRI_V1[0] - _TRI_V3[0]
_TRI_INV_D = 1.0 / _TRI_DENOM

# Annular plate (ring) — radii in the r ∈ [0,1] space used by circle
_RING_INNER = 0.30
_RING_SPAN = 1.0 - _RING_INNER    # width of ring
_RING_INNER2 = (_RING_INNER * 0.5) ** 2  # squared inner radius in (cx,cy) space


class Chladni(Visual):
    name = "CHLADNI"
    description = "Vibrating plate nodal patterns"
    category = "science_bench"

    # Square/rect modes sorted by ascending frequency f ∝ (n² + m²).
    # For a ~20 cm square brass plate, f ≈ 28·(n² + m²) Hz.
    FREQ_CONST = 28.0
    MODES = [
        (1, 2),  #  140 Hz   n²+m²=  5
        (1, 3),  #  280 Hz   n²+m²= 10
        (2, 3),  #  364 Hz   n²+m²= 13
        (1, 4),  #  476 Hz   n²+m²= 17
        (2, 4),  #  560 Hz   n²+m²= 20
        (3, 4),  #  700 Hz   n²+m²= 25
        (1, 5),  #  728 Hz   n²+m²= 26
        (2, 5),  #  812 Hz   n²+m²= 29
        (3, 5),  #  952 Hz   n²+m²= 34
        (4, 5),  # 1148 Hz   n²+m²= 41
        (3, 7),  # 1624 Hz   n²+m²= 58
        (5, 6),  # 1708 Hz   n²+m²= 61
        (4, 7),  # 1820 Hz   n²+m²= 65
        (6, 7),  # 2380 Hz   n²+m²= 85
        (5, 8),  # 2492 Hz   n²+m²= 89
        (6, 8),  # 2800 Hz   n²+m²=100
        (5, 9),  # 2968 Hz   n²+m²=106
        (7, 8),  # 3164 Hz   n²+m²=113
        (6, 9),  # 3276 Hz   n²+m²=117
        (7, 9),  # 3640 Hz   n²+m²=130
        (8, 9),  # 4060 Hz   n²+m²=145
        (7,10),  # 4172 Hz   n²+m²=149
        (9,10),  # 5068 Hz   n²+m²=181
    ]

    # Zeros of J_m(x) — Abramowitz & Stegun Table 9.5
    _J_ZEROS = [
        [2.4048, 5.5201, 8.6537, 11.7915, 14.9309],   # J_0
        [3.8317, 7.0156, 10.1735, 13.3237, 16.4706],   # J_1
        [5.1356, 8.4172, 11.6198, 14.7960],             # J_2
        [6.3802, 9.7610, 13.0152],                       # J_3
        [7.5883, 11.0647, 14.3725],                      # J_4
        [8.7715, 12.3386],                                # J_5
        [9.9361, 13.5893],                                # J_6
        [11.0864],                                        # J_7
    ]

    @staticmethod
    def _bessel_j(n, x):
        """Bessel function J_n(x) via convergent power series."""
        half_x = x * 0.5
        if abs(half_x) < 1e-12:
            return 1.0 if n == 0 else 0.0
        # First term: (x/2)^n / n!
        term = 1.0
        for i in range(1, n + 1):
            term *= half_x / i
        total = term
        hx2 = -(half_x * half_x)
        for k in range(1, 20):
            term *= hx2 / (k * (n + k))
            total += term
            if abs(term) < abs(total) * 1e-12:
                break
        return total

    def _j_zero(self, order, idx):
        """idx-th zero (1-indexed) of J_{order}. McMahon asymptotic fallback."""
        if order < len(self._J_ZEROS) and idx <= len(self._J_ZEROS[order]):
            return self._J_ZEROS[order][idx - 1]
        # McMahon expansion for large arguments
        return math.pi * (idx + order * 0.5 - 0.25)

    # ── lifecycle ─────────────────────────────────────────────────

    def reset(self):
        self.time = 0.0
        self.shape_idx = 0
        self.frequency = 2.5
        self.label_timer = 0.0
        self.overlay_timer = 0.0
        self.settle = 1.0  # 0 = just scattered, 1 = settled

        self._init_texture()

    def _init_texture(self):
        """Per-pixel sand colour, grain, and scatter displacement field."""
        self.grain = [[random.uniform(0.8, 1.0)
                       for _ in range(DRAW_SIZE)] for _ in range(DRAW_SIZE)]
        self.pix_color = [[random.choice(SAND_COLORS)
                           for _ in range(DRAW_SIZE)] for _ in range(DRAW_SIZE)]
        self.disp_x = [[random.uniform(-0.3, 0.3)
                        for _ in range(DRAW_SIZE)] for _ in range(DRAW_SIZE)]
        self.disp_y = [[random.uniform(-0.3, 0.3)
                        for _ in range(DRAW_SIZE)] for _ in range(DRAW_SIZE)]

    # ── physics ───────────────────────────────────────────────────

    def _chladni_amp(self, x, y, n, m, shape):
        """Chladni amplitude at normalised (x, y) ∈ [0, 1]²."""
        if shape == 'circle':
            cx, cy = x - 0.5, y - 0.5
            r = math.sqrt(cx * cx + cy * cy) * 2.0  # r ∈ [0, 1]
            if r > 1.0:
                return 1.0
            theta = math.atan2(cy, cx)
            ang = min(n, m)
            rad = max(n, m) - ang + 1
            k = self._j_zero(ang, rad)
            return self._bessel_j(ang, k * r) * math.cos(ang * theta)

        if shape == 'rect':
            return (math.cos(n * math.pi * x) * math.cos(m * math.pi * y * 1.5)
                    - math.cos(m * math.pi * x) * math.cos(n * math.pi * y * 1.5))

        if shape == 'hex':
            cx, cy = x - 0.5, y - 0.5
            # Three axis projections at 120° intervals
            d1 = cx
            d2 = -0.5 * cx + _S3_2 * cy
            d3 = -0.5 * cx - _S3_2 * cy
            s = 3.0  # density scale
            return (math.cos(n * math.pi * d1 * s) * math.cos(m * math.pi * d2 * s)
                    - math.cos(m * math.pi * d1 * s) * math.cos(n * math.pi * d3 * s))

        if shape == 'tri':
            # Barycentric coordinates on equilateral triangle
            px, py = x - _TRI_V3[0], y - _TRI_V3[1]
            l1 = (_TRI_A1 * px + _TRI_B1 * py) * _TRI_INV_D
            l2 = (_TRI_A2 * px + _TRI_B2 * py) * _TRI_INV_D
            _sin = math.sin
            _pi = math.pi
            return (_sin(n * _pi * l1) * _sin(m * _pi * l2)
                    - _sin(m * _pi * l1) * _sin(n * _pi * l2))

        if shape == 'ring':
            cx, cy = x - 0.5, y - 0.5
            r = math.sqrt(cx * cx + cy * cy) * 2.0
            if r < _RING_INNER or r > 1.0:
                return 1.0
            theta = math.atan2(cy, cx)
            ring_r = (r - _RING_INNER) / _RING_SPAN
            return math.sin(n * math.pi * ring_r) * math.cos(m * theta)

        # Square — classic Chladni (Ritz antisymmetric combination)
        return (math.cos(n * math.pi * x) * math.cos(m * math.pi * y)
                - math.cos(m * math.pi * x) * math.cos(n * math.pi * y))

    def _mode_hz(self, n, m, shape):
        """Approximate resonant frequency in Hz."""
        if shape == 'circle':
            ang = min(n, m)
            rad = max(n, m) - ang + 1
            k = self._j_zero(ang, rad)
            return 2.85 * k * k
        if shape == 'rect':
            return self.FREQ_CONST * (n * n + m * m * 2.25)
        if shape == 'hex':
            # Hexagonal eigenvalues ∝ n² + nm + m²
            return self.FREQ_CONST * (n * n + n * m + m * m) * 0.8
        if shape == 'tri':
            return self.FREQ_CONST * (n * n + n * m + m * m)
        if shape == 'ring':
            # Radial modes spaced more tightly due to narrower domain
            return self.FREQ_CONST * (n * n * 4 + m * m)
        return self.FREQ_CONST * (n * n + m * m)

    # ── input ─────────────────────────────────────────────────────

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left:
            self.frequency = max(0.0, self.frequency - 0.04)
            consumed = True
        if input_state.right:
            self.frequency += 0.04
            consumed = True
        if input_state.up_pressed:
            self.shape_idx = (self.shape_idx - 1) % len(SHAPES)
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.shape_idx = (self.shape_idx + 1) % len(SHAPES)
            self.overlay_timer = 2.5
            consumed = True
        if input_state.action_l or input_state.action_r:
            self._scatter()
            consumed = True
        return consumed

    def _scatter(self):
        """Randomise displacement field and restart settle animation."""
        self.settle = 0.0
        for py in range(DRAW_SIZE):
            for px in range(DRAW_SIZE):
                self.disp_x[py][px] = random.uniform(-0.3, 0.3)
                self.disp_y[py][px] = random.uniform(-0.3, 0.3)
                self.grain[py][px] = random.uniform(0.8, 1.0)

    # ── update / draw ─────────────────────────────────────────────

    def update(self, dt: float):
        self.time += dt
        self.label_timer += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.settle < 1.0:
            self.settle = min(1.0, self.settle + dt * 0.4)  # ~2.5 s to settle

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        shape_name, shape_key = SHAPES[self.shape_idx]

        # Resolve current mode blend once for the whole frame
        idx = self.frequency
        i = int(idx) % len(self.MODES)
        j = (i + 1) % len(self.MODES)
        blend = idx - int(idx)
        n1, m1 = self.MODES[i]
        n2, m2 = self.MODES[j]
        inv_blend = 1.0 - blend
        hz = (self._mode_hz(n1, m1, shape_key) * inv_blend
              + self._mode_hz(n2, m2, shape_key) * blend)

        # Scatter animation state
        disp_amt = (1.0 - self.settle) ** 2          # ease-in settle
        sigma = LINE_SIGMA + 0.25 * disp_amt         # wide → narrow
        inv_2s2 = 1.0 / (2.0 * sigma * sigma)

        # Local refs for hot loop
        _amp = self._chladni_amp
        _exp = math.exp
        DS1 = float(DRAW_SIZE - 1)

        for py in range(DRAW_SIZE):
            sy = DRAW_OFFSET_Y + py
            ny_base = py / DS1
            dy_row = self.disp_y[py]
            dx_row = self.disp_x[py]
            g_row = self.grain[py]
            c_row = self.pix_color[py]

            for px in range(DRAW_SIZE):
                nx_base = px / DS1

                # Plate boundary check
                if shape_key == 'circle':
                    cx = nx_base - 0.5
                    cy = ny_base - 0.5
                    if cx * cx + cy * cy > 0.25:
                        continue
                elif shape_key == 'hex':
                    ax = abs(nx_base - 0.5)
                    ay = abs(ny_base - 0.5)
                    if ax > _HEX_R or ay > _HEX_HALF_H or _S3_2 * ax + 0.5 * ay > _HEX_EDGE:
                        continue
                elif shape_key == 'tri':
                    tpx = nx_base - _TRI_V3[0]
                    tpy = ny_base - _TRI_V3[1]
                    tl1 = (_TRI_A1 * tpx + _TRI_B1 * tpy) * _TRI_INV_D
                    tl2 = (_TRI_A2 * tpx + _TRI_B2 * tpy) * _TRI_INV_D
                    if tl1 < 0 or tl2 < 0 or tl1 + tl2 > 1.0:
                        continue
                elif shape_key == 'ring':
                    cx = nx_base - 0.5
                    cy = ny_base - 0.5
                    r2 = cx * cx + cy * cy
                    if r2 > 0.25 or r2 < _RING_INNER2:
                        continue

                # Apply scatter displacement
                if disp_amt > 0.001:
                    nx = max(0.0, min(1.0, nx_base + dx_row[px] * disp_amt))
                    ny = max(0.0, min(1.0, ny_base + dy_row[px] * disp_amt))
                else:
                    nx, ny = nx_base, ny_base

                # Blended amplitude between adjacent modes
                a1 = _amp(nx, ny, n1, m1, shape_key)
                a2 = _amp(nx, ny, n2, m2, shape_key)
                amp = abs(a1 * inv_blend + a2 * blend)

                # Sand brightness: Gaussian peak at nodal lines (amp ≈ 0)
                bri = _exp(-amp * amp * inv_2s2) * g_row[px]

                sx = DRAW_OFFSET_X + px
                if bri > 0.02:
                    sc = c_row[px]
                    d.set_pixel(sx, sy, (int(sc[0] * bri),
                                         int(sc[1] * bri),
                                         int(sc[2] * bri)))
                else:
                    d.set_pixel(sx, sy, PLATE_COLOR)

        # ── HUD ───────────────────────────────────────────────────
        d.draw_text_small(2, 2, f"{int(hz)} HZ", (220, 190, 130))

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            oc = (int(220 * alpha), int(190 * alpha), int(130 * alpha))
            d.draw_text_small(2, 58, shape_name, oc)
        else:
            phase = int(self.label_timer / 4) % 2
            label = f"MODE {n1}.{m1}" if phase == 0 else shape_name
            d.draw_text_small(2, 58, label, Colors.WHITE)

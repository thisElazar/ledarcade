"""
Chladni Plates – Vibrating Plate Nodal Patterns
================================================
Sand settles at nodal lines on a vibrating plate,
revealing standing wave patterns.

Square plate uses the classic Ritz approximation:
  cos(nπx)cos(mπy) − cos(mπx)cos(nπy)
Circular plate uses Bessel functions J_m(k·r)·cos(mθ).

Controls:
  Left/Right (held) - Sweep frequency continuously
  Up/Down (pressed) - Cycle plate shape (square, circle, rectangle)
  Action            - Scatter sand
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

SHAPES = [
    ('SQUARE', 'square'),
    ('CIRCLE', 'circle'),
    ('RECTANGLE', 'rect'),
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


class Chladni(Visual):
    name = "CHLADNI"
    description = "Vibrating plate nodal patterns"
    category = "science_bench"

    # Square/rect modes sorted by ascending frequency f ∝ (n² + m²).
    # For a ~20 cm square brass plate, f ≈ 28·(n² + m²) Hz.
    FREQ_CONST = 28.0
    MODES = [
        (1, 2),  #  140 Hz   n²+m²= 5
        (1, 3),  #  280 Hz   n²+m²=10
        (2, 3),  #  364 Hz   n²+m²=13
        (1, 4),  #  476 Hz   n²+m²=17
        (2, 4),  #  560 Hz   n²+m²=20
        (3, 4),  #  700 Hz   n²+m²=25
        (1, 5),  #  728 Hz   n²+m²=26
        (2, 5),  #  812 Hz   n²+m²=29
        (3, 5),  #  952 Hz   n²+m²=34
        (4, 5),  # 1148 Hz   n²+m²=41
        (3, 7),  # 1624 Hz   n²+m²=58
        (5, 6),  # 1708 Hz   n²+m²=61
        (4, 7),  # 1820 Hz   n²+m²=65
        (6, 7),  # 2380 Hz   n²+m²=85
        (5, 8),  # 2492 Hz   n²+m²=89
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
            # Map mode numbers to circular: angular order + radial index
            ang = min(n, m)
            rad = max(n, m) - ang + 1
            k = self._j_zero(ang, rad)
            return self._bessel_j(ang, k * r) * math.cos(ang * theta)

        if shape == 'rect':
            # 3:2 aspect ratio rectangle
            return (math.cos(n * math.pi * x) * math.cos(m * math.pi * y * 1.5)
                    - math.cos(m * math.pi * x) * math.cos(n * math.pi * y * 1.5))

        # Square — classic Chladni (Ritz antisymmetric combination)
        return (math.cos(n * math.pi * x) * math.cos(m * math.pi * y)
                - math.cos(m * math.pi * x) * math.cos(n * math.pi * y))

    def _mode_hz(self, n, m, shape):
        """Approximate resonant frequency in Hz."""
        if shape == 'circle':
            ang = min(n, m)
            rad = max(n, m) - ang + 1
            k = self._j_zero(ang, rad)
            # Scaled so lowest mode ≈ 140 Hz (matching square plate range)
            return 2.85 * k * k
        if shape == 'rect':
            # f ∝ (n/a)² + (m/b)² with 3:2 aspect
            return self.FREQ_CONST * (n * n + m * m * 2.25)
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

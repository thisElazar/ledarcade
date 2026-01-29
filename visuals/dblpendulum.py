"""
Double Pendulum
===============
Classic chaotic double pendulum filling the full display.
Traces the path of the lower bob, creating beautiful patterns.

Controls:
  Up/Down    - Cycle color palette
  Left/Right - Adjust trail length
  Button     - Randomize starting angles
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


PALETTES = [
    # Fire
    [(255, 60, 0), (255, 160, 0), (255, 255, 40), (255, 80, 0)],
    # Cyan-Magenta
    [(0, 255, 255), (255, 0, 255), (100, 200, 255), (200, 100, 255)],
    # Green
    [(0, 255, 80), (80, 255, 0), (0, 200, 120), (160, 255, 40)],
    # Blue-White
    [(60, 100, 255), (120, 160, 255), (200, 220, 255), (80, 130, 255)],
    # Rainbow cycle
    [(255, 0, 0), (255, 255, 0), (0, 255, 0), (0, 200, 255)],
    # Gold
    [(255, 200, 50), (255, 160, 20), (200, 140, 10), (255, 220, 100)],
]

# Physics constants
G = 9.81
SCALE = 13.0       # Pixels per meter
BOB2_RADIUS = 3    # Lower bob draw radius


class DblPendulum(Visual):
    name = "DBL PENDULUM"
    description = "Chaotic double pendulum"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Arm lengths (in sim units)
        self.L1 = 1.0
        self.L2 = 1.0

        # Masses
        self.m1 = 1.0
        self.m2 = 1.0

        # Initial angles (from vertical) and angular velocities
        self.a1 = math.pi * 0.75 + random.uniform(-0.3, 0.3)
        self.a2 = math.pi * 0.5 + random.uniform(-0.3, 0.3)
        self.w1 = 0.0
        self.w2 = 0.0

        # Pivot: position so full downward extension just above screen bottom
        self.pivot_x = GRID_SIZE // 2
        self.pivot_y = int(GRID_SIZE - 2 - BOB2_RADIUS - SCALE * (self.L1 + self.L2))

        # Trail
        self.trail = []
        self.max_trail = 600

        # Palette
        self.palette_idx = random.randint(0, len(PALETTES) - 1)

    def handle_input(self, input_state):
        consumed = False
        # Up/Down: cycle palette (visual)
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True
        elif input_state.down_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        # Left/Right: adjust trail length (time)
        if input_state.right_pressed:
            self.max_trail = min(1200, self.max_trail + 100)
            consumed = True
        elif input_state.left_pressed:
            self.max_trail = max(100, self.max_trail - 100)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.a1 = random.uniform(0.5, math.pi * 1.5)
            self.a2 = random.uniform(0.5, math.pi * 1.5)
            self.w1 = 0.0
            self.w2 = 0.0
            self.trail.clear()
            consumed = True
        return consumed

    def _derivatives(self, a1, a2, w1, w2):
        """Compute angular accelerations for the double pendulum."""
        m1, m2, L1, L2 = self.m1, self.m2, self.L1, self.L2
        da = a1 - a2
        sin_da = math.sin(da)
        cos_da = math.cos(da)
        M = m1 + m2

        denom = 2 * M - m2 * (1 + math.cos(2 * da))
        if abs(denom) < 1e-10:
            denom = 1e-10

        alpha1 = (-G * M * math.sin(a1)
                   - m2 * G * math.sin(a1 - 2 * a2)
                   - 2 * m2 * sin_da * (w2 * w2 * L2 + w1 * w1 * L1 * cos_da)
                   ) / (L1 * denom)

        alpha2 = (2 * sin_da * (w1 * w1 * L1 * M
                   + G * M * math.cos(a1)
                   + w2 * w2 * L2 * m2 * cos_da)
                   ) / (L2 * denom)

        return alpha1, alpha2

    def update(self, dt):
        self.time += dt

        # RK4 integration with sub-steps for stability
        steps = 10
        h = dt / steps
        for _ in range(steps):
            a1, a2, w1, w2 = self.a1, self.a2, self.w1, self.w2

            # k1
            dw1_1, dw2_1 = self._derivatives(a1, a2, w1, w2)
            da1_1, da2_1 = w1, w2

            # k2
            dw1_2, dw2_2 = self._derivatives(
                a1 + da1_1 * h / 2, a2 + da2_1 * h / 2,
                w1 + dw1_1 * h / 2, w2 + dw2_1 * h / 2)
            da1_2 = w1 + dw1_1 * h / 2
            da2_2 = w2 + dw2_1 * h / 2

            # k3
            dw1_3, dw2_3 = self._derivatives(
                a1 + da1_2 * h / 2, a2 + da2_2 * h / 2,
                w1 + dw1_2 * h / 2, w2 + dw2_2 * h / 2)
            da1_3 = w1 + dw1_2 * h / 2
            da2_3 = w2 + dw2_2 * h / 2

            # k4
            dw1_4, dw2_4 = self._derivatives(
                a1 + da1_3 * h, a2 + da2_3 * h,
                w1 + dw1_3 * h, w2 + dw2_3 * h)
            da1_4 = w1 + dw1_3 * h
            da2_4 = w2 + dw2_3 * h

            self.a1 += h * (da1_1 + 2 * da1_2 + 2 * da1_3 + da1_4) / 6
            self.a2 += h * (da2_1 + 2 * da2_2 + 2 * da2_3 + da2_4) / 6
            self.w1 += h * (dw1_1 + 2 * dw1_2 + 2 * dw1_3 + dw1_4) / 6
            self.w2 += h * (dw2_1 + 2 * dw2_2 + 2 * dw2_3 + dw2_4) / 6

        # Compute bob positions
        x1 = self.pivot_x + SCALE * self.L1 * math.sin(self.a1)
        y1 = self.pivot_y + SCALE * self.L1 * math.cos(self.a1)
        x2 = x1 + SCALE * self.L2 * math.sin(self.a2)
        y2 = y1 + SCALE * self.L2 * math.cos(self.a2)

        # Record trail point
        self.trail.append((int(round(x2)), int(round(y2))))
        if len(self.trail) > self.max_trail:
            self.trail.pop(0)

    def _trail_color(self, idx, total):
        """Get trail color: fades from dim to bright along the trail."""
        palette = PALETTES[self.palette_idx]
        t = idx / max(1, total - 1)
        pi = t * (len(palette) - 1)
        lo = int(pi)
        hi = min(lo + 1, len(palette) - 1)
        f = pi - lo
        c0 = palette[lo]
        c1 = palette[hi]

        r = c0[0] + (c1[0] - c0[0]) * f
        g = c0[1] + (c1[1] - c0[1]) * f
        b = c0[2] + (c1[2] - c0[2]) * f

        brightness = 0.15 + 0.85 * t
        return (int(r * brightness), int(g * brightness), int(b * brightness))

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw trail
        total = len(self.trail)
        for i, (tx, ty) in enumerate(self.trail):
            if 0 <= tx < GRID_SIZE and 0 <= ty < GRID_SIZE:
                color = self._trail_color(i, total)
                self.display.set_pixel(tx, ty, color)

        # Compute current bob positions
        x1 = self.pivot_x + SCALE * self.L1 * math.sin(self.a1)
        y1 = self.pivot_y + SCALE * self.L1 * math.cos(self.a1)
        x2 = x1 + SCALE * self.L2 * math.sin(self.a2)
        y2 = y1 + SCALE * self.L2 * math.cos(self.a2)

        ix1, iy1 = int(round(x1)), int(round(y1))
        ix2, iy2 = int(round(x2)), int(round(y2))

        # Draw arms
        self.display.draw_line(self.pivot_x, self.pivot_y, ix1, iy1, (160, 160, 170))
        self.display.draw_line(ix1, iy1, ix2, iy2, (160, 160, 170))

        # Draw pivot
        self.display.set_pixel(self.pivot_x, self.pivot_y, Colors.WHITE)

        # Draw bob 1 (smaller)
        self.display.draw_circle(ix1, iy1, 2, (200, 200, 210), filled=True)

        # Draw bob 2 (larger, bright)
        palette = PALETTES[self.palette_idx]
        self.display.draw_circle(ix2, iy2, BOB2_RADIUS, palette[0], filled=True)
        if 0 <= ix2 - 1 < GRID_SIZE and 0 <= iy2 - 1 < GRID_SIZE:
            self.display.set_pixel(ix2 - 1, iy2 - 1, Colors.WHITE)

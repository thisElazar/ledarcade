"""
SPIROGRAPH - Hypotrochoid and epitrochoid curves
==================================================
12 presets of parametric curves drawn progressively
with rainbow coloring along the curve length.

Controls:
  Up/Down    - Cycle preset
  Left/Right - Drawing speed
  Button     - Toggle mechanism view
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


def _hsv(h, s, v):
    c = v * s
    x = c * (1 - abs((h * 6) % 2 - 1))
    m = v - c
    if h < 1/6:   r, g, b = c, x, 0
    elif h < 2/6: r, g, b = x, c, 0
    elif h < 3/6: r, g, b = 0, c, x
    elif h < 4/6: r, g, b = 0, x, c
    elif h < 5/6: r, g, b = x, 0, c
    else:          r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


# Presets: (name, R, r, d, is_epi)
# hypotrochoid: x=(R-r)cos(t)+d*cos((R-r)/r*t)
# epitrochoid:  x=(R+r)cos(t)-d*cos((R+r)/r*t)
PRESETS = [
    ('ASTROID',      4, 1, 1, False),
    ('DELTOID',      3, 1, 1, False),
    ('CARDIOID',     1, 1, 1, True),
    ('NEPHROID',     2, 1, 1, True),
    ('3-PETAL',      3, 1, 0.5, False),
    ('5-STAR',       5, 3, 3, False),
    ('ROSE 4',       4, 1, 0.8, False),
    ('ROSE 7',       7, 4, 4, False),
    ('SPIRALING',    5, 2, 1.5, False),
    ('RANUNCULOID',  5, 1, 1, True),
    ('TREFOIL',      3, 2, 1.5, False),
    ('LACE',         7, 3, 2, False),
]


def _compute_max_extent(R, r, d, is_epi):
    """Compute max distance from origin for scaling."""
    max_r = 0
    steps = 1000
    for i in range(steps):
        t = i / steps * 2 * math.pi * 20
        if is_epi:
            x = (R + r) * math.cos(t) - d * math.cos((R + r) / r * t)
            y = (R + r) * math.sin(t) - d * math.sin((R + r) / r * t)
        else:
            x = (R - r) * math.cos(t) + d * math.cos((R - r) / r * t)
            y = (R - r) * math.sin(t) - d * math.sin((R - r) / r * t)
        dist = math.sqrt(x * x + y * y)
        if dist > max_r:
            max_r = dist
    return max_r if max_r > 0 else 1


def _curve_period(R, r):
    """Number of full rotations of t for the curve to close."""
    from math import gcd
    # Curve closes after lcm(R_int, r_int) / R_int full rotations
    # Use integer approximation
    ri = int(round(r * 100))
    Ri = int(round(R * 100))
    if ri == 0:
        return 2 * math.pi
    g = gcd(ri, Ri)
    lcm = ri * Ri // g
    periods = lcm // Ri
    return periods * 2 * math.pi


class Spirograph(Visual):
    name = "SPIROGRAPH"
    description = "Hypotrochoid curves"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.preset_idx = 0
        self.overlay_timer = 0.0
        self.draw_speed = 1.0
        self.show_mechanism = False
        self._t = 0.0
        self._trail = []
        self._complete = False
        self._hold_timer = 0.0
        self._setup_preset()

    def _setup_preset(self):
        name, R, r, d, is_epi = PRESETS[self.preset_idx]
        self._R = R
        self._r = r
        self._d = d
        self._is_epi = is_epi
        self._max_extent = _compute_max_extent(R, r, d, is_epi)
        self._scale = 28.0 / self._max_extent if self._max_extent > 0 else 1
        self._period = _curve_period(R, r)
        self._t = 0.0
        self._trail = []
        self._complete = False
        self._hold_timer = 0.0

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.preset_idx = (self.preset_idx - 1) % len(PRESETS)
            self._setup_preset()
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.preset_idx = (self.preset_idx + 1) % len(PRESETS)
            self._setup_preset()
            self.overlay_timer = 2.0
            consumed = True
        if input_state.left:
            self.draw_speed = max(0.2, self.draw_speed - 0.1)
            consumed = True
        if input_state.right:
            self.draw_speed = min(5.0, self.draw_speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.show_mechanism = not self.show_mechanism
            consumed = True
        return consumed

    def _curve_point(self, t):
        R, r, d = self._R, self._r, self._d
        if self._is_epi:
            x = (R + r) * math.cos(t) - d * math.cos((R + r) / r * t)
            y = (R + r) * math.sin(t) - d * math.sin((R + r) / r * t)
        else:
            x = (R - r) * math.cos(t) + d * math.cos((R - r) / r * t)
            y = (R - r) * math.sin(t) - d * math.sin((R - r) / r * t)
        return x, y

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if not self._complete:
            # Advance parameter
            speed = self.draw_speed * 3.0
            steps = max(1, int(speed * 50 * dt))
            step_size = speed * dt / steps
            for _ in range(steps):
                if self._t >= self._period:
                    self._complete = True
                    break
                self._t += step_size
                x, y = self._curve_point(self._t)
                sx = int(32 + x * self._scale)
                sy = int(32 - y * self._scale)
                self._trail.append((sx, sy, self._t))
        else:
            # Hold timer for auto-advance
            self._hold_timer += dt
            if self._hold_timer >= 3.0:
                self.preset_idx = (self.preset_idx + 1) % len(PRESETS)
                self._setup_preset()
                self.overlay_timer = 2.0

    def draw(self):
        d = self.display
        d.clear()

        # Draw trail with rainbow hue along length
        period = self._period if self._period > 0 else 1
        for i, (sx, sy, t) in enumerate(self._trail):
            if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                hue = (t / period) % 1.0
                color = _hsv(hue, 1.0, 1.0)
                d.set_pixel(sx, sy, color)

        # Draw mechanism if enabled
        if self.show_mechanism and self._trail:
            self._draw_mechanism(d)

        # Label
        name = PRESETS[self.preset_idx][0]
        d.draw_text_small(2, 58, name, Colors.WHITE)

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, name, c)

    def _draw_mechanism(self, d):
        """Draw the rolling circle and pen point."""
        t = self._t
        R, r = self._R, self._r
        s = self._scale
        cx, cy = 32, 32

        # Outer/fixed circle
        outer_r = R * s if not self._is_epi else R * s
        self._draw_circle_outline(d, cx, cy, int(outer_r), (40, 40, 60))

        # Rolling circle center
        if self._is_epi:
            rc_x = (R + r) * math.cos(t)
            rc_y = (R + r) * math.sin(t)
        else:
            rc_x = (R - r) * math.cos(t)
            rc_y = (R - r) * math.sin(t)
        rcx = int(cx + rc_x * s)
        rcy = int(cy - rc_y * s)
        self._draw_circle_outline(d, rcx, rcy, int(r * s), (60, 60, 80))

        # Pen point
        px, py = self._curve_point(t)
        ppx = int(cx + px * s)
        ppy = int(cy - py * s)
        # Line from rolling center to pen
        d.draw_line(rcx, rcy, ppx, ppy, (100, 100, 120))
        # Pen dot
        if 0 <= ppx < GRID_SIZE and 0 <= ppy < GRID_SIZE:
            d.set_pixel(ppx, ppy, (255, 255, 255))

    def _draw_circle_outline(self, d, cx, cy, r, color):
        """Draw circle outline."""
        steps = max(16, r * 4)
        for i in range(steps):
            angle = 2 * math.pi * i / steps
            px = int(cx + r * math.cos(angle))
            py = int(cy + r * math.sin(angle))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, color)

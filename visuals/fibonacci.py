"""
FIBONACCI - Golden ratio patterns
===================================
Three modes: Fibonacci spiral rectangles, sunflower phyllotaxis,
and scrolling sequence with ratio convergence.

Controls:
  Up/Down    - Cycle mode
  Left/Right - Adjust speed
  Button     - Reset animation
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


# Fibonacci sequence
_FIB = [1, 1]
while len(_FIB) < 40:
    _FIB.append(_FIB[-1] + _FIB[-2])

PHI = (1 + math.sqrt(5)) / 2
GOLDEN_ANGLE = 137.508  # degrees

MODE_NAMES = ['SPIRAL', 'SUNFLOWER', 'SEQUENCE']

# Rectangle colors
RECT_COLORS = [
    (255, 80, 80), (255, 180, 50), (255, 255, 60),
    (80, 255, 80), (60, 200, 255), (100, 100, 255),
    (200, 80, 255), (255, 100, 200),
]


class Fibonacci(Visual):
    name = "FIBONACCI"
    description = "Golden ratio patterns"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.mode = 0
        self.build_progress = 0.0
        self.speed = 1.0
        self.overlay_timer = 0.0
        self._seq_scroll = 0.0
        self._precompute_spiral()

    def _precompute_spiral(self):
        """Precompute Fibonacci rectangle positions for spiral mode."""
        fibs = [1, 1, 2, 3, 5, 8, 13, 21]
        self._rects = []
        directions = [(1, 0), (0, -1), (-1, 0), (0, 1)]
        for i, f in enumerate(fibs):
            d = directions[i % 4]
            if i == 0:
                rx, ry = 0, 0
            else:
                prev = self._rects[-1]
                prx, pry, prf = prev['x'], prev['y'], prev['f']
                if d == (1, 0):
                    rx = prx + prf
                    ry = pry + prf - f
                elif d == (0, -1):
                    rx = prx
                    ry = pry - f
                elif d == (-1, 0):
                    rx = prx - f
                    ry = pry
                elif d == (0, 1):
                    rx = prx - f + prf
                    ry = pry + prf
            self._rects.append({'x': rx, 'y': ry, 'f': f, 'dir': i % 4})

        # Center and scale to fit display
        if self._rects:
            min_x = min(r['x'] for r in self._rects)
            max_x = max(r['x'] + r['f'] for r in self._rects)
            min_y = min(r['y'] for r in self._rects)
            max_y = max(r['y'] + r['f'] for r in self._rects)
            span = max(max_x - min_x, max_y - min_y)
            self._spiral_scale = (GRID_SIZE - 4) / span if span > 0 else 1
            self._spiral_ox = -min_x * self._spiral_scale + (GRID_SIZE - (max_x - min_x) * self._spiral_scale) / 2
            self._spiral_oy = -min_y * self._spiral_scale + (GRID_SIZE - (max_y - min_y) * self._spiral_scale) / 2

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.mode = (self.mode - 1) % len(MODE_NAMES)
            self.build_progress = 0.0
            self._seq_scroll = 0.0
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.mode = (self.mode + 1) % len(MODE_NAMES)
            self.build_progress = 0.0
            self._seq_scroll = 0.0
            self.overlay_timer = 2.0
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.build_progress = 0.0
            self._seq_scroll = 0.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        if self.mode == 0:
            self.build_progress = min(len(self._rects), self.build_progress + self.speed * dt)
        elif self.mode == 1:
            self.build_progress = min(500, self.build_progress + self.speed * 60 * dt)
        else:
            self._seq_scroll += self.speed * 0.3 * dt

    def draw(self):
        d = self.display
        d.clear()
        if self.mode == 0:
            self._draw_spiral(d)
        elif self.mode == 1:
            self._draw_sunflower(d)
        else:
            self._draw_sequence(d)

        d.draw_text_small(2, 58, MODE_NAMES[self.mode], Colors.WHITE)

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, MODE_NAMES[self.mode], c)

    def _draw_spiral(self, d):
        count = int(self.build_progress)
        s = self._spiral_scale
        ox, oy = self._spiral_ox, self._spiral_oy
        for i in range(min(count, len(self._rects))):
            r = self._rects[i]
            rx = int(r['x'] * s + ox)
            ry = int(r['y'] * s + oy)
            rf = max(1, int(r['f'] * s))
            color = RECT_COLORS[i % len(RECT_COLORS)]
            dim = tuple(max(20, c // 3) for c in color)
            d.draw_rect(rx, ry, rf, rf, dim)
            d.draw_rect(rx, ry, rf, rf, color, filled=False)
            self._draw_arc(d, r, rx, ry, rf, color)

    def _draw_arc(self, d, r, rx, ry, rf, color):
        """Draw quarter-circle arc inside rectangle."""
        dir_idx = r['dir']
        if dir_idx == 0:
            cx, cy = rx, ry + rf
            a0, a1 = -math.pi / 2, 0
        elif dir_idx == 1:
            cx, cy = rx, ry
            a0, a1 = 0, math.pi / 2
        elif dir_idx == 2:
            cx, cy = rx + rf, ry
            a0, a1 = math.pi / 2, math.pi
        else:
            cx, cy = rx + rf, ry + rf
            a0, a1 = math.pi, 3 * math.pi / 2
        radius = rf
        steps = max(8, rf * 2)
        for j in range(steps):
            t = a0 + (a1 - a0) * j / steps
            px = int(cx + radius * math.cos(t))
            py = int(cy + radius * math.sin(t))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                d.set_pixel(px, py, color)

    def _draw_sunflower(self, d):
        count = int(self.build_progress)
        cx, cy = 32, 30
        c_scale = 1.7
        for n in range(1, count + 1):
            angle = math.radians(n * GOLDEN_ANGLE)
            radius = c_scale * math.sqrt(n)
            px = int(cx + radius * math.cos(angle))
            py = int(cy + radius * math.sin(angle))
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                hue = (n / 100.0) % 1.0
                d.set_pixel(px, py, _hsv(hue, 0.9, 1.0))

    def _draw_sequence(self, d):
        """Show Fibonacci numbers with F(n)/F(n-1) ratio converging to phi.

        Layout per row: "F(n) = value  ratio"
        Rows scroll slowly to reveal the full sequence.
        """
        row_h = 7  # 5px glyph + 2px gap
        visible_rows = (GRID_SIZE - 12) // row_h  # room for header + label
        scroll_idx = int(self._seq_scroll)

        # Header
        d.draw_text_small(2, 1, "N  FIB  RATIO", (140, 140, 100))

        for row in range(visible_rows):
            i = scroll_idx + row
            if i < 0 or i >= len(_FIB):
                continue
            y = 9 + row * row_h
            if y + 5 > GRID_SIZE - 6:
                break

            # Index
            idx_str = f"{i + 1:>2}"
            d.draw_text_small(0, y, idx_str, (100, 100, 100))

            # Value (truncate long numbers)
            val = _FIB[i]
            if val > 99999:
                val_str = f"{val:.0e}"[:5]
            else:
                val_str = str(val)
            hue = (i / 12.0) % 1.0
            d.draw_text_small(10, y, val_str, _hsv(hue, 0.8, 1.0))

            # Ratio F(n)/F(n-1)
            if i > 0:
                ratio = _FIB[i] / _FIB[i - 1]
                ratio_str = f"{ratio:.3f}"
                # Color: closer to phi = brighter gold
                err = abs(ratio - PHI)
                if err < 0.001:
                    rc = (255, 220, 80)
                elif err < 0.05:
                    rc = (200, 180, 60)
                else:
                    rc = (120, 120, 80)
                d.draw_text_small(38, y, ratio_str, rc)

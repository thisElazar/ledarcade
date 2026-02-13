"""
FRACTALS - Interactive Fractal Explorer
========================================
Five classic fractals: Mandelbrot, Julia, Sierpinski Triangle,
Koch Snowflake, and Fractal Tree with animated depth and palettes.
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE

# ---------------------------------------------------------------------------
# Palette LUTs (64-entry color tables)
# ---------------------------------------------------------------------------

def _make_lut(fn):
    return [fn(i / 63.0) for i in range(64)]

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
    return (int((r+m)*255), int((g+m)*255), int((b+m)*255))

PALETTES = [
    ('RAINBOW', _make_lut(lambda t: _hsv(t, 1.0, 1.0))),
    ('FIRE',    _make_lut(lambda t: (min(255, int(t*510)),
                                      int(max(0, t-0.4)*425),
                                      int(max(0, t-0.7)*850)))),
    ('ICE',     _make_lut(lambda t: (int(t*100),
                                      int(80+t*175),
                                      int(150+t*105)))),
    ('NEON',    _make_lut(lambda t: _hsv((t*0.6+0.75) % 1.0, 1.0, 0.5+0.5*t))),
    ('GRAY',    _make_lut(lambda t: (int(t*255), int(t*255), int(t*255)))),
]

FRACTAL_NAMES = ['MANDELBROT', 'JULIA', 'SIERPINSKI', 'KOCH', 'TREE']

# Julia set interesting c values
JULIA_C = [
    (-0.7, 0.27015),
    (-0.8, 0.156),
    (0.355, 0.355),
    (-0.4, 0.6),
    (0.285, 0.01),
]

MAX_ITER = 64


class Fractals(Visual):
    name = "FRACTALS"
    description = "Interactive fractal explorer"
    category = "science"

    def reset(self):
        self.time = 0.0
        self.fractal_idx = 0
        self.palette_idx = 0
        self.overlay_timer = 0.0
        self.julia_c_idx = 0
        # Cached iteration grids
        self._grid = None
        self._dirty = True
        # Animated fractals
        self._anim_depth = 0.0
        self._tree_wind = 0.0
        self._compute()

    def _compute(self):
        """Compute fractal data (only for Mandelbrot/Julia)."""
        if self.fractal_idx == 0:
            self._compute_mandelbrot()
        elif self.fractal_idx == 1:
            self._compute_julia()
        self._dirty = False

    def _compute_mandelbrot(self):
        grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for py in range(GRID_SIZE):
            for px in range(GRID_SIZE):
                x0 = (px / GRID_SIZE) * 2.5 - 2.0
                y0 = (py / GRID_SIZE) * 2.5 - 1.25
                x, y = 0.0, 0.0
                it = 0
                while x*x + y*y <= 4 and it < MAX_ITER:
                    x, y = x*x - y*y + x0, 2*x*y + y0
                    it += 1
                grid[py][px] = it
        self._grid = grid

    def _compute_julia(self):
        cr, ci = JULIA_C[self.julia_c_idx % len(JULIA_C)]
        grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for py in range(GRID_SIZE):
            for px in range(GRID_SIZE):
                x = (px / GRID_SIZE) * 3.0 - 1.5
                y = (py / GRID_SIZE) * 3.0 - 1.5
                it = 0
                while x*x + y*y <= 4 and it < MAX_ITER:
                    x, y = x*x - y*y + cr, 2*x*y + ci
                    it += 1
                grid[py][px] = it
        self._grid = grid

    def handle_input(self, input_state):
        consumed = False
        if input_state.left_pressed:
            self.fractal_idx = (self.fractal_idx - 1) % len(FRACTAL_NAMES)
            self._dirty = True
            self._anim_depth = 0.0
            consumed = True
        if input_state.right_pressed:
            self.fractal_idx = (self.fractal_idx + 1) % len(FRACTAL_NAMES)
            self._dirty = True
            self._anim_depth = 0.0
            consumed = True
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            if self.fractal_idx == 1:
                self.julia_c_idx = (self.julia_c_idx + 1) % len(JULIA_C)
                self._dirty = True
            elif self.fractal_idx >= 2:
                self._anim_depth = 0.0
            else:
                self._dirty = True
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self._dirty and self.fractal_idx <= 1:
            self._compute()

        # Animate depth for geometric fractals
        if self.fractal_idx == 2:  # Sierpinski
            self._anim_depth = min(7, self._anim_depth + dt * 0.5)
        elif self.fractal_idx == 3:  # Koch
            self._anim_depth = min(5, self._anim_depth + dt * 0.5)
        elif self.fractal_idx == 4:  # Tree
            self._anim_depth = min(9, self._anim_depth + dt * 0.5)
            self._tree_wind = self.time

    def draw(self):
        d = self.display
        d.clear()
        pal_name, lut = PALETTES[self.palette_idx]

        if self.fractal_idx == 0 or self.fractal_idx == 1:
            self._draw_iteration_grid(d, lut)
        elif self.fractal_idx == 2:
            self._draw_sierpinski(d, lut)
        elif self.fractal_idx == 3:
            self._draw_koch(d, lut)
        elif self.fractal_idx == 4:
            self._draw_tree(d, lut)

        # Label
        label = FRACTAL_NAMES[self.fractal_idx]
        d.draw_text_small(2, 58, label, Colors.WHITE)

        # Palette overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, pal_name, c)

    def _draw_iteration_grid(self, d, lut):
        if not self._grid:
            return
        offset = int(self.time * 5) % 64
        for py in range(GRID_SIZE):
            for px in range(GRID_SIZE):
                it = self._grid[py][px]
                if it >= MAX_ITER:
                    d.set_pixel(px, py, (0, 0, 0))
                else:
                    idx = (it + offset) % 64
                    d.set_pixel(px, py, lut[idx])

    def _draw_sierpinski(self, d, lut):
        depth = int(self._anim_depth)
        if depth < 1:
            return
        color = lut[32]
        self._sierpinski_recurse(d, 32, 4, 4, 60, 60, 60, depth, color, lut)

    def _sierpinski_recurse(self, d, x1, y1, x2, y2, x3, y3, depth, color, lut):
        if depth == 0:
            d.draw_line(x1, y1, x2, y2, color)
            d.draw_line(x2, y2, x3, y3, color)
            d.draw_line(x3, y3, x1, y1, color)
            return
        mx1 = (x1 + x2) // 2
        my1 = (y1 + y2) // 2
        mx2 = (x2 + x3) // 2
        my2 = (y2 + y3) // 2
        mx3 = (x3 + x1) // 2
        my3 = (y3 + y1) // 2
        c = lut[min(63, depth * 9)]
        self._sierpinski_recurse(d, x1, y1, mx1, my1, mx3, my3, depth-1, c, lut)
        self._sierpinski_recurse(d, mx1, my1, x2, y2, mx2, my2, depth-1, c, lut)
        self._sierpinski_recurse(d, mx3, my3, mx2, my2, x3, y3, depth-1, c, lut)

    def _draw_koch(self, d, lut):
        depth = int(self._anim_depth)
        if depth < 1:
            depth = 1
        # Start with equilateral triangle
        cx, cy = 32, 34
        r = 28
        pts = []
        for i in range(3):
            a = math.pi * 2 * i / 3 - math.pi / 2
            pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))

        # Build Koch curve for each side
        for i in range(3):
            x1, y1 = pts[i]
            x2, y2 = pts[(i + 1) % 3]
            segments = self._koch_segments(x1, y1, x2, y2, depth)
            c = lut[min(63, 20 + i * 15)]
            for j in range(len(segments) - 1):
                ax, ay = segments[j]
                bx, by = segments[j + 1]
                d.draw_line(int(ax), int(ay), int(bx), int(by), c)

    def _koch_segments(self, x1, y1, x2, y2, depth):
        if depth == 0:
            return [(x1, y1), (x2, y2)]
        dx = x2 - x1
        dy = y2 - y1
        ax = x1 + dx / 3
        ay = y1 + dy / 3
        bx = x1 + dx * 2 / 3
        by = y1 + dy * 2 / 3
        # Peak of equilateral triangle
        px = (x1 + x2) / 2 + (y1 - y2) * math.sqrt(3) / 6
        py = (y1 + y2) / 2 + (x2 - x1) * math.sqrt(3) / 6
        s1 = self._koch_segments(x1, y1, ax, ay, depth - 1)
        s2 = self._koch_segments(ax, ay, px, py, depth - 1)
        s3 = self._koch_segments(px, py, bx, by, depth - 1)
        s4 = self._koch_segments(bx, by, x2, y2, depth - 1)
        return s1 + s2[1:] + s3[1:] + s4[1:]

    def _draw_tree(self, d, lut):
        depth = int(self._anim_depth)
        if depth < 1:
            return
        # Trunk starts at bottom center
        self._tree_branch(d, 32, 60, -math.pi / 2, 18, depth, lut)

    def _tree_branch(self, d, x, y, angle, length, depth, lut):
        if depth == 0 or length < 1:
            return
        ex = x + length * math.cos(angle)
        ey = y + length * math.sin(angle)
        ci = min(63, max(0, 63 - depth * 7))
        c = lut[ci]
        d.draw_line(int(x), int(y), int(ex), int(ey), c)
        # Branch with wind sway
        sway = math.sin(self._tree_wind * 0.5 + depth * 0.3) * 0.15
        spread = 0.45 + sway
        new_len = length * 0.7
        self._tree_branch(d, ex, ey, angle - spread, new_len, depth - 1, lut)
        self._tree_branch(d, ex, ey, angle + spread, new_len, depth - 1, lut)

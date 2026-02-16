"""
TESSELLATIONS - Mathematical tilings
======================================
Six tiling patterns: triangles, squares, hexagons,
Cairo pentagons, Penrose rhombuses, and herringbone.

Controls:
  Up/Down    - Cycle palette
  Left/Right - Adjust scroll speed
  Button     - Cycle tiling pattern
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


MODE_NAMES = ['TRIANGLES', 'SQUARES', 'HEXAGONS', 'CAIRO', 'PENROSE', 'HERRINGBONE']

PALETTE_NAMES = ['WARM', 'COOL', 'EARTH', 'NEON', 'PASTEL', 'MONO']

PALETTES = [
    # Warm
    [(200, 80, 60), (220, 150, 50), (180, 120, 80), (240, 100, 70), (200, 180, 60), (160, 90, 50)],
    # Cool
    [(60, 100, 200), (80, 180, 180), (100, 140, 220), (50, 160, 200), (120, 100, 200), (70, 200, 160)],
    # Earth
    [(140, 100, 60), (100, 130, 70), (170, 140, 80), (120, 90, 50), (90, 120, 80), (160, 120, 70)],
    # Neon
    [(255, 50, 100), (50, 255, 150), (100, 50, 255), (255, 200, 50), (50, 200, 255), (255, 100, 255)],
    # Pastel
    [(220, 180, 180), (180, 220, 180), (180, 180, 220), (220, 220, 180), (180, 220, 220), (220, 180, 220)],
    # Monochrome
    [(60, 60, 60), (100, 100, 100), (140, 140, 140), (180, 180, 180), (80, 80, 80), (120, 120, 120)],
]


class Tessellations(Visual):
    name = "TESSELLATIONS"
    description = "Mathematical tilings"
    category = "math"

    def reset(self):
        self.time = 0.0
        self.mode = 0
        self.palette_idx = 0
        self.overlay_timer = 0.0
        self.scroll_speed = 8.0
        self.scroll_x = 0.0
        self.scroll_y = 0.0
        self._penrose_grid = None
        self._build_penrose()

    def _build_penrose(self):
        """Pre-rasterize Penrose-like tiling via de Bruijn's multigrid method."""
        grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for py in range(GRID_SIZE):
            for px in range(GRID_SIZE):
                val = 0
                for k in range(5):
                    angle = k * math.pi / 5
                    proj = (px - 32) * math.cos(angle) + (py - 32) * math.sin(angle)
                    val += int(math.floor(proj / 8.0 + 0.5)) * (k + 1)
                grid[py][px] = abs(val) % 6
        self._penrose_grid = grid

    def handle_input(self, input_state):
        consumed = False
        # Up/Down cycle palette (colors)
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            self.overlay_timer = 2.0
            consumed = True
        # Left/Right adjust scroll speed
        if input_state.left:
            self.scroll_speed = max(-20, self.scroll_speed - 1)
            consumed = True
        if input_state.right:
            self.scroll_speed = min(20, self.scroll_speed + 1)
            consumed = True
        # Button cycles tiling pattern
        if input_state.action_l or input_state.action_r:
            self.mode = (self.mode + 1) % len(MODE_NAMES)
            self.overlay_timer = 2.0
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)
        self.scroll_x += self.scroll_speed * dt
        self.scroll_y += self.scroll_speed * 0.7 * dt

    def draw(self):
        d = self.display
        pal = PALETTES[self.palette_idx]
        ox = int(self.scroll_x) % 256
        oy = int(self.scroll_y) % 256

        for py in range(GRID_SIZE):
            for px in range(GRID_SIZE):
                wx = px + ox
                wy = py + oy
                tile = self._get_tile(wx, wy)
                d.set_pixel(px, py, pal[tile % len(pal)])

        # Label
        d.draw_text_small(2, 58, MODE_NAMES[self.mode], Colors.WHITE)

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, MODE_NAMES[self.mode], c)
            d.draw_text_small(2, 9, PALETTE_NAMES[self.palette_idx],
                              (int(160 * alpha), int(160 * alpha), int(160 * alpha)))

    def _get_tile(self, wx, wy):
        if self.mode == 0:
            return self._tile_triangles(wx, wy)
        elif self.mode == 1:
            return self._tile_squares(wx, wy)
        elif self.mode == 2:
            return self._tile_hexagons(wx, wy)
        elif self.mode == 3:
            return self._tile_cairo(wx, wy)
        elif self.mode == 4:
            return self._tile_penrose(wx, wy)
        else:
            return self._tile_herringbone(wx, wy)

    def _tile_triangles(self, wx, wy):
        side = 12
        h = int(side * 0.866)
        row = wy // h
        offset = (side // 2) * (row % 2)
        col = (wx + offset) // side
        local_y = wy % h
        local_x = (wx + offset) % side
        if local_y < h * local_x / side:
            return (row * 2 + col) % 6
        else:
            return (row * 2 + col + 1) % 6

    def _tile_squares(self, wx, wy):
        side = 10
        col = wx // side
        row = wy // side
        return (col + row) % len(PALETTES[0])

    def _tile_hexagons(self, wx, wy):
        size = 8.0
        q = (2.0 / 3 * wx) / size
        r = (-1.0 / 3 * wx + math.sqrt(3) / 3 * wy) / size
        x = q
        z = r
        y = -x - z
        rx = round(x)
        ry = round(y)
        rz = round(z)
        x_diff = abs(rx - x)
        y_diff = abs(ry - y)
        z_diff = abs(rz - z)
        if x_diff > y_diff and x_diff > z_diff:
            rx = -ry - rz
        elif y_diff > z_diff:
            ry = -rx - rz
        return (abs(rx * 3 + ry * 7 + rz * 11)) % 6

    def _tile_cairo(self, wx, wy):
        cell = 14
        cx = wx % cell
        cy = wy % cell
        col = wx // cell
        row = wy // cell
        half = cell // 2
        if cx < half:
            if cy < half:
                sub = 0
            else:
                sub = 1
        else:
            if cy < half:
                sub = 2
            else:
                sub = 3
        lx = cx % half
        ly = cy % half
        if lx + ly > half:
            sub = (sub + 2) % 4
        return (col * 4 + row * 5 + sub) % 6

    def _tile_penrose(self, wx, wy):
        px = wx % GRID_SIZE
        py = wy % GRID_SIZE
        if self._penrose_grid:
            return self._penrose_grid[py][px]
        return 0

    def _tile_herringbone(self, wx, wy):
        brick_w = 12
        brick_h = 4
        cell_w = brick_w
        cell_h = brick_h * 2
        cx = wx % cell_w
        cy = wy % cell_h
        col = wx // cell_w
        row = wy // cell_h
        if cy < brick_h:
            sub = cx // (brick_w // 2)
            return (col * 2 + row * 3 + sub) % 6
        else:
            shifted_x = (wx + brick_w // 2) % cell_w
            sub = shifted_x // (brick_w // 2)
            return (col * 2 + row * 3 + sub + 3) % 6

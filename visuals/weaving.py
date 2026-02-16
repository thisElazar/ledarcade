"""
WEAVING — Classic textile weave structures on 64x64 LED matrix.
================================================================
Top-down view of fabric showing how warp and weft threads interlace.
Weft rows animate in one at a time, building the pattern from top to bottom,
then restart with a new weave or palette.

Weave structures: Plain, Twill 2/2, Herringbone, Basket, Satin,
Houndstooth, Diamond Twill, Waffle.

Controls:
  Up/Down    - Cycle weave pattern
  Left/Right - Cycle color palette
  Action     - Restart weave animation
"""

import math
from . import Visual

# ---------------------------------------------------------------------------
# Thread size — each logical thread is THREAD_PX pixels wide/tall
# 64 / 4 = 16 threads across and down
# ---------------------------------------------------------------------------
THREAD_PX = 4
GRID = 64 // THREAD_PX  # 16 threads

# ---------------------------------------------------------------------------
# Weave drafts — each is a 2D pattern of True/False
# True = warp on top, False = weft on top
# Pattern tiles across the grid.
# ---------------------------------------------------------------------------

def _tile(draft, cols, rows):
    """Tile a small draft pattern to fill cols x rows."""
    ph = len(draft)
    pw = len(draft[0])
    return [[draft[r % ph][c % pw] for c in range(cols)] for r in range(rows)]


# Plain weave: 1/1 alternating
_PLAIN = [
    [True, False],
    [False, True],
]

# Twill 2/2: diagonal lines
_TWILL = [
    [True, True, False, False],
    [False, True, True, False],
    [False, False, True, True],
    [True, False, False, True],
]

# Herringbone: twill that reverses direction
_HERRINGBONE = [
    [True, True, False, False, False, False, True, True],
    [False, True, True, False, False, True, True, False],
    [False, False, True, True, True, True, False, False],
    [True, False, False, True, True, False, False, True],
]

# Basket weave: 2/2 blocks
_BASKET = [
    [True, True, False, False],
    [True, True, False, False],
    [False, False, True, True],
    [False, False, True, True],
]

# Satin 5-shaft: long floats, minimal interlacing
_SATIN = [
    [True, False, False, False, False],
    [False, False, True, False, False],
    [False, False, False, False, True],
    [False, True, False, False, False],
    [False, False, False, True, False],
]

# Houndstooth: classic 4x4 pattern
_HOUNDSTOOTH = [
    [True, True, False, False, True, True, False, False],
    [True, True, False, False, True, True, False, False],
    [False, False, True, True, False, False, True, True],
    [False, False, True, True, False, False, True, True],
    [True, True, True, True, False, False, False, False],
    [True, True, True, True, False, False, False, False],
    [False, False, False, False, True, True, True, True],
    [False, False, False, False, True, True, True, True],
]

# Diamond twill: concentric diamond shapes
_DIAMOND = [
    [True,  False, False, False, True,  False, False, False],
    [False, True,  False, True,  False, True,  False, True],
    [False, False, True,  False, False, False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
    [True,  False, False, False, True,  False, False, False],
    [False, True,  False, True,  False, True,  False, True],
    [False, False, True,  False, False, False, True,  False],
    [False, True,  False, True,  False, True,  False, True],
]

# Waffle weave: raised grid pattern
_WAFFLE = [
    [True,  True,  True,  True,  True,  True],
    [True,  False, False, False, False, True],
    [True,  False, True,  True,  False, True],
    [True,  False, True,  True,  False, True],
    [True,  False, False, False, False, True],
    [True,  True,  True,  True,  True,  True],
]

WEAVES = [
    {'name': 'PLAIN',       'draft': _PLAIN},
    {'name': 'TWILL',       'draft': _TWILL},
    {'name': 'HERRINGBONE', 'draft': _HERRINGBONE},
    {'name': 'BASKET',      'draft': _BASKET},
    {'name': 'SATIN',       'draft': _SATIN},
    {'name': 'HOUNDSTOOTH', 'draft': _HOUNDSTOOTH},
    {'name': 'DIAMOND',     'draft': _DIAMOND},
    {'name': 'WAFFLE',      'draft': _WAFFLE},
]

# ---------------------------------------------------------------------------
# Color palettes — (warp_color, weft_color, bg_tint)
# ---------------------------------------------------------------------------
PALETTES = [
    {
        'name': 'NATURAL',
        'warp': (200, 180, 140),
        'weft': (160, 130, 80),
        'gap':  (90, 75, 50),
    },
    {
        'name': 'INDIGO',
        'warp': (220, 215, 195),
        'weft': (40, 50, 120),
        'gap':  (20, 25, 60),
    },
    {
        'name': 'KENTE',
        'warp': (220, 180, 30),
        'weft': (180, 40, 30),
        'gap':  (80, 60, 15),
    },
    {
        'name': 'TARTAN',
        'warp': (30, 60, 130),
        'weft': (160, 30, 30),
        'gap':  (20, 20, 40),
    },
    {
        'name': 'NAVAJO',
        'warp': (190, 80, 40),
        'weft': (60, 40, 35),
        'gap':  (50, 30, 20),
    },
    {
        'name': 'SILK',
        'warp': (200, 170, 200),
        'weft': (140, 180, 160),
        'gap':  (70, 75, 80),
    },
]

# ---------------------------------------------------------------------------
# Weaving speed
# ---------------------------------------------------------------------------
ROWS_PER_SEC = 3.0  # weft rows revealed per second


class Weaving(Visual):
    name = "WEAVING"
    description = "Classic textile weave structures"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self.weave_idx = 0
        self.palette_idx = 0
        self.row_timer = 0.0
        self.revealed_rows = 0
        self._build_fabric()

    def _build_fabric(self):
        """Tile current weave draft to fill the grid."""
        w = WEAVES[self.weave_idx]
        self.fabric = _tile(w['draft'], GRID, GRID)
        self.revealed_rows = 0
        self.row_timer = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.weave_idx = (self.weave_idx - 1) % len(WEAVES)
            self._build_fabric()
            consumed = True
        if input_state.down_pressed:
            self.weave_idx = (self.weave_idx + 1) % len(WEAVES)
            self._build_fabric()
            consumed = True

        if input_state.left_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.right_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._build_fabric()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        if self.revealed_rows < GRID:
            self.row_timer += dt * ROWS_PER_SEC
            while self.row_timer >= 1.0 and self.revealed_rows < GRID:
                self.row_timer -= 1.0
                self.revealed_rows += 1
        else:
            # Pause 2s then auto-advance to next weave
            self.row_timer += dt
            if self.row_timer > 2.0:
                self.weave_idx = (self.weave_idx + 1) % len(WEAVES)
                self._build_fabric()

    def draw(self):
        d = self.display
        d.clear()

        pal = PALETTES[self.palette_idx]
        warp_c = pal['warp']
        weft_c = pal['weft']
        gap_c = pal['gap']

        # Draw revealed rows of fabric
        for row in range(self.revealed_rows):
            for col in range(GRID):
                warp_on_top = self.fabric[row][col]

                # Top color is what's visible
                top_c = warp_c if warp_on_top else weft_c

                # Add subtle shading for depth — warp-on-top is slightly raised
                if warp_on_top:
                    shade = 1.0
                else:
                    shade = 0.85

                px = col * THREAD_PX
                py = row * THREAD_PX

                # Fill thread block
                for dy in range(THREAD_PX):
                    for dx in range(THREAD_PX):
                        # Gap between threads (1px border on right/bottom)
                        if dx == THREAD_PX - 1 or dy == THREAD_PX - 1:
                            d.set_pixel(px + dx, py + dy, gap_c)
                        else:
                            # Slight highlight on top-left pixel
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

        # Draw "shuttle" on the row currently being woven
        if self.revealed_rows < GRID:
            shuttle_row = self.revealed_rows
            sy = shuttle_row * THREAD_PX
            # Shuttle position oscillates across the width
            frac = (self.row_timer % 1.0)
            sx = int(frac * 60) + 2
            # Small shuttle marker
            for dx in range(3):
                for dy in range(2):
                    nx = sx + dx
                    ny = sy + dy
                    if 0 <= nx < 64 and 0 <= ny < 64:
                        d.set_pixel(nx, ny, (255, 240, 200))

        # Weave name at top
        name = WEAVES[self.weave_idx]['name']
        d.draw_text_small(2, 1, name, (180, 180, 180))

        # Palette name at bottom
        pal_name = PALETTES[self.palette_idx]['name']
        d.draw_text_small(2, 59, pal_name, (120, 120, 120))

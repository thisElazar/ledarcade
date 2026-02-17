"""
KNITTING — World knitting traditions on 64x64 LED matrix.
==========================================================
Stitch charts rendered as pixel grids, 4x4px per stitch = 16x16 stitches.
Each pattern is a small grid of 0/1 values that tiles to fill 16x16,
representing two-color stranded knitting. Rows animate in top to bottom
with a needle indicator on the active row.

Controls:
  Left/Right - Adjust knitting speed
  Up/Down    - Cycle color palette
  Action     - Next stitch pattern
"""

from . import Visual

# ---------------------------------------------------------------------------
# Stitch geometry — each logical stitch is STITCH_PX pixels square
# 64 / 4 = 16 stitches across and down
# ---------------------------------------------------------------------------
STITCH_PX = 4
GRID = 64 // STITCH_PX  # 16

# ---------------------------------------------------------------------------
# Speed control
# ---------------------------------------------------------------------------
SPEEDS = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0]
SPEED_LABELS = ['.5X', '.75X', '1X', '1.5X', '2X', '3X']
DEFAULT_SPEED_IDX = 2
BASE_ROWS_PER_SEC = 3.0

# ---------------------------------------------------------------------------
# Helper: tile a small chart to fill the grid
# ---------------------------------------------------------------------------
def _tile(chart, cols, rows):
    ph = len(chart)
    pw = len(chart[0])
    return [[chart[r % ph][c % pw] for c in range(cols)] for r in range(rows)]


# ===================================================================
# STITCH CHARTS — 0 = background color, 1 = foreground color
# Organized by knitting tradition
# ===================================================================

# -- Basic stitches (universal) ------------------------------------

_STOCKINETTE = [
    [0],
]

_GARTER = [
    [0],
    [1],
]

_SEED = [
    [0, 1],
    [1, 0],
]

_RIBBING = [
    [0, 0, 1, 1],
]

# -- Fair Isle (Scotland, Shetland) --------------------------------

_FAIR_ISLE_OXO = [
    [0, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 0],
    [0, 1, 0, 1, 0, 1],
    [1, 1, 1, 1, 1, 1],
    [1, 0, 1, 0, 1, 0],
    [0, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 0],
    [1, 1, 1, 1, 1, 1],
]

_FAIR_ISLE_PEERIE = [
    [1, 0, 0, 1, 0, 0],
    [0, 1, 1, 0, 1, 1],
    [0, 1, 1, 0, 1, 1],
    [1, 0, 0, 1, 0, 0],
]

_FAIR_ISLE_STAR = [
    [0, 0, 0, 1, 0, 0, 0, 1],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# -- Aran (Ireland) ------------------------------------------------

_ARAN_CABLE = [
    [0, 0, 1, 1, 0, 0, 1, 1],
    [0, 0, 1, 1, 0, 0, 1, 1],
    [0, 1, 1, 0, 0, 1, 1, 0],
    [1, 1, 0, 0, 1, 1, 0, 0],
    [1, 1, 0, 0, 1, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 1, 0],
    [0, 0, 1, 1, 0, 0, 1, 1],
    [0, 0, 1, 1, 0, 0, 1, 1],
]

_ARAN_DIAMOND = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# -- Nordic / Scandinavian -----------------------------------------

_NORDIC_STAR = [
    [0, 0, 0, 1, 1, 0, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 1, 0, 0, 1, 1, 0],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [0, 1, 1, 0, 0, 1, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 0, 1, 1, 0, 0, 0],
]

_NORDIC_SNOWFLAKE = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 1, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 1, 0, 1, 0, 1, 0, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
]

# -- Selburose (Norway) -------------------------------------------

_SELBUROSE = [
    [0, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 1, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 1, 0],
    [0, 1, 0, 1, 1, 1, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1],
    [0, 1, 0, 1, 1, 1, 0, 1],
    [0, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 0, 1, 1, 1, 0, 0],
]

# -- Lopapeysa (Iceland) ------------------------------------------

_LOPAPEYSA = [
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [1, 0, 1, 0, 0, 1, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
]

# -- Sashiko (Japan) -----------------------------------------------

_SASHIKO_ASANOHA = [
    [0, 0, 0, 1, 0, 0, 0, 1],
    [0, 0, 1, 0, 1, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 1],
    [0, 0, 1, 0, 1, 0, 1, 0],
]

_SASHIKO_SEIGAIHA = [
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 1, 0, 0, 1, 0, 1],
]

# -- Argyle (Scotland) --------------------------------------------

_ARGYLE = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 1, 1, 1, 1, 1, 0, 0],
    [1, 1, 1, 1, 1, 1, 1, 0],
    [0, 1, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# -- Bavarian twisted stitch (Germany) ----------------------------

_BAVARIAN = [
    [1, 0, 0, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [1, 0, 0, 0, 0, 0, 1, 0],
    [0, 0, 0, 0, 0, 0, 0, 1],
]

# -- Latvian patterns ---------------------------------------------

_LATVIAN_BRAID = [
    [1, 0, 1, 0, 1, 0, 1, 0],
    [0, 1, 0, 1, 0, 1, 0, 1],
    [1, 1, 0, 0, 1, 1, 0, 0],
    [0, 0, 1, 1, 0, 0, 1, 1],
    [0, 1, 0, 1, 0, 1, 0, 1],
    [1, 0, 1, 0, 1, 0, 1, 0],
    [0, 0, 1, 1, 0, 0, 1, 1],
    [1, 1, 0, 0, 1, 1, 0, 0],
]

_LATVIAN_SUN = [
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 1, 1, 1, 1, 0, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
]

# -- Estonian lace -------------------------------------------------

_ESTONIAN_LILY = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 1, 0, 0, 0],
    [0, 1, 0, 0, 0, 1, 0, 0],
    [0, 1, 0, 1, 0, 1, 0, 0],
    [1, 0, 1, 0, 1, 0, 1, 0],
    [1, 0, 0, 1, 0, 0, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]

# -- Cowichan (Pacific NW) ----------------------------------------

_COWICHAN = [
    [1, 1, 1, 0, 0, 1, 1, 1],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [0, 0, 1, 1, 1, 1, 0, 0],
    [1, 0, 0, 1, 1, 0, 0, 1],
    [1, 1, 0, 0, 0, 0, 1, 1],
    [1, 1, 1, 0, 0, 1, 1, 1],
]

# -- Additional Fair Isle ------------------------------------------

_FAIR_ISLE_ANCHOR = [
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0],
    [0, 1, 0, 1, 0, 1, 0, 0],
    [0, 0, 1, 1, 1, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
    [0, 0, 0, 0, 0, 0, 0, 0],
]


# ===================================================================
# Pattern registry — name, origin, chart, default palette index
# ===================================================================

PATTERNS = [
    # Basic
    {'name': 'STOCKINETTE',   'origin': 'UNIVERSAL',        'chart': _STOCKINETTE,     'pal': 0},
    {'name': 'GARTER',        'origin': 'UNIVERSAL',        'chart': _GARTER,          'pal': 0},
    {'name': 'SEED STITCH',   'origin': 'UNIVERSAL',        'chart': _SEED,            'pal': 0},
    {'name': '2X2 RIBBING',   'origin': 'UNIVERSAL',        'chart': _RIBBING,         'pal': 0},
    # Fair Isle
    {'name': 'FAIR ISLE OXO', 'origin': 'SHETLAND',         'chart': _FAIR_ISLE_OXO,   'pal': 1},
    {'name': 'FAIR ISLE PEERIE','origin':'SHETLAND',         'chart': _FAIR_ISLE_PEERIE,'pal': 1},
    {'name': 'FAIR ISLE STAR','origin': 'SHETLAND',         'chart': _FAIR_ISLE_STAR,  'pal': 1},
    {'name': 'FAIR ISLE ANCHOR','origin':'SCOTLAND',         'chart': _FAIR_ISLE_ANCHOR,'pal': 1},
    # Aran
    {'name': 'ARAN CABLE',   'origin': 'IRELAND',           'chart': _ARAN_CABLE,      'pal': 4},
    {'name': 'ARAN DIAMOND', 'origin': 'IRELAND',           'chart': _ARAN_DIAMOND,    'pal': 4},
    # Nordic
    {'name': 'NORDIC STAR',  'origin': 'SCANDINAVIA',       'chart': _NORDIC_STAR,     'pal': 2},
    {'name': 'SNOWFLAKE',    'origin': 'SCANDINAVIA',       'chart': _NORDIC_SNOWFLAKE,'pal': 2},
    {'name': 'SELBUROSE',    'origin': 'NORWAY',            'chart': _SELBUROSE,       'pal': 2},
    {'name': 'LOPAPEYSA',    'origin': 'ICELAND',           'chart': _LOPAPEYSA,       'pal': 6},
    # Japanese
    {'name': 'SASHIKO ASANOHA','origin':'JAPAN',             'chart': _SASHIKO_ASANOHA, 'pal': 3},
    {'name': 'SASHIKO WAVE', 'origin': 'JAPAN',             'chart': _SASHIKO_SEIGAIHA,'pal': 3},
    # Argyle
    {'name': 'ARGYLE',       'origin': 'SCOTLAND',          'chart': _ARGYLE,          'pal': 1},
    # Bavarian
    {'name': 'BAVARIAN TWIST','origin':'BAVARIA, GERMANY',  'chart': _BAVARIAN,        'pal': 7},
    # Baltic
    {'name': 'LATVIAN BRAID','origin': 'LATVIA',            'chart': _LATVIAN_BRAID,   'pal': 2},
    {'name': 'LATVIAN SUN',  'origin': 'LATVIA',            'chart': _LATVIAN_SUN,     'pal': 2},
    {'name': 'ESTONIAN LILY','origin': 'ESTONIA',           'chart': _ESTONIAN_LILY,   'pal': 9},
    # Pacific NW
    {'name': 'COWICHAN',     'origin': 'PACIFIC NW',        'chart': _COWICHAN,        'pal': 8},
    # Additional Nordic
    {'name': 'NORDIC BORDER','origin': 'SCANDINAVIA',       'chart': _LATVIAN_BRAID,   'pal': 5},
    {'name': 'ICELANDIC YOKE','origin':'ICELAND',           'chart': _LOPAPEYSA,       'pal': 6},
]


# ===================================================================
# COLOR PALETTES — two-color knitting traditions
# Each has bg (background/main), fg (foreground/contrast), gap
# ===================================================================

PALETTES = [
    {
        'name': 'NATURAL WOOL',
        'bg':  (220, 210, 180),
        'fg':  (140, 110, 70),
        'gap': (90, 75, 50),
    },
    {
        'name': 'FAIR ISLE RED',
        'bg':  (220, 210, 180),
        'fg':  (180, 40, 30),
        'gap': (90, 75, 50),
    },
    {
        'name': 'NORDIC BLUE',
        'bg':  (220, 220, 230),
        'fg':  (30, 50, 120),
        'gap': (65, 65, 75),
    },
    {
        'name': 'SASHIKO INDIGO',
        'bg':  (220, 210, 190),
        'fg':  (35, 45, 100),
        'gap': (60, 58, 65),
    },
    {
        'name': 'ARAN CREAM',
        'bg':  (215, 205, 175),
        'fg':  (170, 155, 120),
        'gap': (85, 78, 60),
    },
    {
        'name': 'HIGHLAND GREEN',
        'bg':  (210, 205, 180),
        'fg':  (40, 100, 50),
        'gap': (60, 68, 55),
    },
    {
        'name': 'ICELANDIC GRAY',
        'bg':  (200, 195, 185),
        'fg':  (60, 55, 50),
        'gap': (55, 52, 48),
    },
    {
        'name': 'BAVARIAN BLUE',
        'bg':  (220, 215, 220),
        'fg':  (30, 60, 160),
        'gap': (65, 62, 75),
    },
    {
        'name': 'COWICHAN EARTH',
        'bg':  (210, 195, 160),
        'fg':  (70, 50, 30),
        'gap': (58, 50, 35),
    },
    {
        'name': 'ESTONIAN ROSE',
        'bg':  (225, 215, 210),
        'fg':  (170, 50, 70),
        'gap': (80, 68, 65),
    },
]


# ===================================================================
# Visual class
# ===================================================================

class Knitting(Visual):
    name = "KNITTING"
    description = "World knitting traditions"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self.pattern_idx = 0
        self.palette_idx = 0
        self.speed_idx = DEFAULT_SPEED_IDX
        self.row_timer = 0.0
        self.revealed_rows = 0
        self.overlay_timer = 0.0
        self._input_cooldown = 0.0
        self._build_chart()

    def _build_chart(self, set_palette=True):
        p = PATTERNS[self.pattern_idx]
        self.chart = _tile(p['chart'], GRID, GRID)
        self.revealed_rows = 0
        self.row_timer = 0.0
        if set_palette:
            self.palette_idx = p.get('pal', 0)

    def handle_input(self, input_state) -> bool:
        if self._input_cooldown > 0:
            return False
        consumed = False

        # Left/Right: speed control
        if input_state.left_pressed:
            self.speed_idx = max(0, self.speed_idx - 1)
            self.overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.speed_idx = min(len(SPEEDS) - 1, self.speed_idx + 1)
            self.overlay_timer = 2.0
            consumed = True

        # Up/Down: palette
        if input_state.up_pressed:
            self.palette_idx = (self.palette_idx - 1) % len(PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_idx = (self.palette_idx + 1) % len(PALETTES)
            consumed = True

        # Action: next stitch pattern
        if input_state.action_l or input_state.action_r:
            self.pattern_idx = (self.pattern_idx + 1) % len(PATTERNS)
            self._build_chart()
            consumed = True

        if consumed:
            self._input_cooldown = 0.15
        return consumed

    def update(self, dt: float):
        self.time += dt
        if self._input_cooldown > 0:
            self._input_cooldown -= dt
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        speed = SPEEDS[self.speed_idx]
        if self.revealed_rows < GRID:
            self.row_timer += dt * BASE_ROWS_PER_SEC * speed
            while self.row_timer >= 1.0 and self.revealed_rows < GRID:
                self.row_timer -= 1.0
                self.revealed_rows += 1
        else:
            # Pause then auto-advance
            self.row_timer += dt * speed
            if self.row_timer > 2.5:
                self.pattern_idx = (self.pattern_idx + 1) % len(PATTERNS)
                self._build_chart()

    def draw(self):
        d = self.display
        d.clear()

        pal = PALETTES[self.palette_idx]
        bg_c = pal['bg']
        fg_c = pal['fg']
        gap_c = pal['gap']

        # -- V-stitch shading lookup for 3x3 interior --
        # Row 0: V-arms top (bright . shadow . bright)
        # Row 1: V-arms mid  (mid . shadow . mid)
        # Row 2: V-bottom    (shadow . bright . shadow)
        _V = {(0,0): 1.2, (0,1): 0.65, (0,2): 1.2,
              (1,0): 1.0, (1,1): 0.65, (1,2): 1.0,
              (2,0): 0.65, (2,1): 1.2, (2,2): 0.65}

        # -- Draw stitch chart (bottom-up, like real knitting) --
        for row_idx in range(self.revealed_rows):
            row = GRID - 1 - row_idx  # count up from bottom
            for col in range(GRID):
                val = self.chart[row][col]
                base_c = fg_c if val else bg_c

                px = col * STITCH_PX
                py = row * STITCH_PX

                for dy in range(STITCH_PX):
                    for dx in range(STITCH_PX):
                        if dx == STITCH_PX - 1 or dy == STITCH_PX - 1:
                            d.set_pixel(px + dx, py + dy, gap_c)
                        else:
                            m = _V[(dy, dx)]
                            c = (min(255, int(base_c[0] * m)),
                                 min(255, int(base_c[1] * m)),
                                 min(255, int(base_c[2] * m)))
                            d.set_pixel(px + dx, py + dy, c)

        # -- Yarn carry line + needle on active row --
        if self.revealed_rows < GRID:
            active_row = GRID - 1 - self.revealed_rows
            ny = active_row * STITCH_PX
            # Yarn strand across active row
            yarn_c = fg_c if (self.revealed_rows % 2 == 0) else bg_c
            for x in range(64):
                if 0 <= ny < 64:
                    d.set_pixel(x, ny, yarn_c)
            # Needle tip — alternates direction each row
            frac = self.row_timer % 1.0
            going_right = (self.revealed_rows % 2 == 0)
            nx = int(frac * 62) if going_right else 62 - int(frac * 62)
            for dy2 in range(3):
                yy = ny + dy2
                if 0 <= yy < 64:
                    if 0 <= nx < 64:
                        d.set_pixel(nx, yy, (255, 250, 240))
                    if 0 <= nx + 1 < 64:
                        d.set_pixel(nx + 1, yy, (200, 195, 185))

        # -- Pattern name + origin (top) --
        p = PATTERNS[self.pattern_idx]
        d.draw_text_small(2, 1, p['name'], (180, 180, 180))
        d.draw_text_small(2, 7, p['origin'], (110, 110, 110))

        # -- Palette name (bottom) --
        d.draw_text_small(2, 59, pal['name'], (120, 120, 120))

        # -- Speed overlay --
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 30, 'SPEED ' + SPEED_LABELS[self.speed_idx], c)

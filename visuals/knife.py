"""Knife Cuts - Animated knife cut reference on 64x64 LED matrix.

Each cut shows a flipbook-style animation of the technique happening on a
cutting board, then holds on the finished product.  Below: dimensions,
description, and best-use pairings.

Nine cuts across three families: Strips, Dice, Special.
"""

from . import Visual

# ── Color palette ──────────────────────────────────────────────────
# Cutting board (warm wood)
_BW = (160, 120, 60)     # board base
_BD = (135, 100, 48)     # board dark grain
_BL = (185, 145, 85)     # board light grain

# Carrot
_CO = (240, 140, 40)     # carrot orange
_CL = (255, 180, 70)     # carrot highlight
_CD = (200, 105, 25)     # carrot shadow
_CG = (75, 155, 50)      # carrot green
_CK = (55, 120, 35)      # carrot dark green

# Potato
_PO = (210, 190, 130)    # base
_PL = (230, 215, 165)    # highlight
_PD = (170, 150, 95)     # shadow
_PI = (240, 230, 190)    # interior

# Basil
_BA = (60, 150, 45)      # base green
_BH = (85, 180, 65)      # highlight
_BS = (40, 110, 30)      # shadow

# Scallion
_SG = (70, 160, 50)      # green part
_SL = (100, 190, 80)     # green highlight
_SW = (230, 230, 220)    # white part
_SC = (200, 200, 185)    # white shadow

# Garlic
_GA = (240, 230, 180)    # base
_GL = (250, 245, 215)    # highlight
_GD = (200, 190, 140)    # shadow

# Onion
_OB = (220, 180, 100)    # base/skin
_OL = (240, 205, 130)    # highlight
_OD = (180, 145, 70)     # shadow
_OI = (235, 230, 220)    # interior white

# Knife
_KS = (195, 200, 210)    # steel
_KL = (220, 225, 235)    # steel highlight
_KD = (145, 150, 160)    # steel edge
_KH = (65, 48, 32)       # handle dark
_KB = (90, 68, 48)       # handle light

# UI
HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)
LABEL_DIM = (70, 70, 90)

# ── Families (for future cuts) ─────────────────────────────────────
FAMILIES = ["STRIPS", "DICE", "SPECIAL"]
FAMILY_COLORS = [
    (200, 160, 60),     # STRIPS = golden
    (180, 120, 60),     # DICE = amber
    (100, 180, 120),    # SPECIAL = green
]

# ── Cut data ───────────────────────────────────────────────────────
CUTS = [
    # ── STRIPS family (0) ──
    {'name': 'JULIENNE', 'family': 0, 'num': 1,
     'size': '1/8 x 1/8 x 2 IN',
     'desc': 'THIN MATCHSTICKS',
     'use': 'CARROTS / PEPPERS / ZUCCHINI / STIR-FRY / GARNISH / SALADS',
     'labels': ['WHOLE', 'SPLIT', 'PLANKS', 'CUT', 'JULIENNE'],
     'n_frames': 5,
     'hold': [1.8, 1.2, 1.2, 1.2, 2.8]},
    {'name': 'BATONNET', 'family': 0, 'num': 2,
     'size': '1/4 x 1/4 x 2 IN',
     'desc': 'THICK STICKS',
     'use': 'CRUDITE / FRIES / CARROTS / CELERY / DIPPING',
     'labels': ['WHOLE', 'PLANKS', 'CUT', 'BATONNET'],
     'n_frames': 4,
     'hold': [1.8, 1.2, 1.2, 2.8]},
    {'name': 'CHIFFONADE', 'family': 0, 'num': 3,
     'size': 'VERY THIN RIBBONS',
     'desc': 'ROLLED LEAF STRIPS',
     'use': 'BASIL / MINT / SPINACH / GARNISH / SOUPS / PASTA',
     'labels': ['STACK', 'ROLL', 'SLICE', 'CHIFFONADE'],
     'n_frames': 4,
     'hold': [1.5, 1.2, 1.2, 2.8]},
    # ── DICE family (1) ──
    {'name': 'BRUNOISE', 'family': 1, 'num': 4,
     'size': '1/8 x 1/8 x 1/8 IN',
     'desc': 'TINY FINE DICE',
     'use': 'CARROTS / CELERY / ONION / SAUCES / CONSOMME / GARNISH',
     'labels': ['STICKS', 'GATHER', 'CUT', 'BRUNOISE'],
     'n_frames': 4,
     'hold': [1.5, 1.2, 1.2, 2.8]},
    {'name': 'SMALL DICE', 'family': 1, 'num': 5,
     'size': '1/4 x 1/4 x 1/4 IN',
     'desc': 'UNIFORM CUBES',
     'use': 'POTATOES / SOUPS / STUFFING / MIREPOIX / SALSA',
     'labels': ['WHOLE', 'PLANKS', 'CUT', 'SMALL DICE'],
     'n_frames': 4,
     'hold': [1.8, 1.2, 1.2, 2.8]},
    # ── SPECIAL family (2) ──
    {'name': 'MINCE', 'family': 2, 'num': 6,
     'size': '1/16 IN OR LESS',
     'desc': 'VERY FINE PIECES',
     'use': 'GARLIC / SHALLOTS / HERBS / GINGER / SAUCES / MARINADES',
     'labels': ['CLOVE', 'SLICE', 'ROCK CHOP', 'MINCE'],
     'n_frames': 4,
     'hold': [1.5, 1.2, 1.2, 2.8]},
    {'name': 'BIAS CUT', 'family': 2, 'num': 7,
     'size': 'DIAGONAL SLICES',
     'desc': 'ANGLED OVALS',
     'use': 'SCALLIONS / CARROTS / CELERY / STIR-FRY / PRESENTATION',
     'labels': ['WHOLE', 'ANGLE', 'SLICE', 'BIAS CUT'],
     'n_frames': 4,
     'hold': [1.5, 1.2, 1.2, 2.8]},
    {'name': 'OBLIQUE', 'family': 2, 'num': 8,
     'size': 'IRREGULAR ANGLES',
     'desc': 'ROLL-CUT PIECES',
     'use': 'CARROTS / PARSNIPS / BRAISING / STEWS / ROASTING',
     'labels': ['WHOLE', 'CUT', 'ROLL', 'OBLIQUE'],
     'n_frames': 4,
     'hold': [1.5, 1.2, 1.2, 2.8]},
    {'name': 'CHOP', 'family': 2, 'num': 9,
     'size': '1/4 TO 3/4 IN',
     'desc': 'ROUGH IRREGULAR',
     'use': 'ONIONS / TOMATOES / HERBS / SOUPS / STEWS / CHILI',
     'labels': ['HALF', 'CUTS', 'CROSS', 'CHOP'],
     'n_frames': 4,
     'hold': [1.5, 1.2, 1.2, 2.8]},
]

# Build per-family index
_FAMILY_CUTS = [[] for _ in range(len(FAMILIES))]
for _i, _c in enumerate(CUTS):
    _FAMILY_CUTS[_c['family']].append(_i)


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


class Knife(Visual):
    name = "KNIFE CUTS"
    description = "Knife cut reference"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout
    NAME_Y = 1
    SEP1_Y = 7
    ANIM_TOP = 8
    ANIM_BOT = 33
    SEP2_Y = 34
    SIZE_Y = 36
    SEP3_Y = 42
    USE_Y = 44
    SEP4_Y = 50
    FAM_Y = 52
    FOOT_SEP_Y = 57
    FOOT_Y = 59

    # Board position within animation area
    BOARD_Y = 30       # top of board (4px tall: 30-33)
    SURFACE_Y = 29     # where things rest (just above board)

    def reset(self):
        self.time = 0.0
        self.cut_idx = 0
        self.frame = 0
        self.frame_timer = 0.0
        self._name_scroll_x = 0.0
        self._size_scroll_x = 0.0
        self._use_scroll_x = 0.0
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0

    def _current(self):
        return CUTS[self.cut_idx % len(CUTS)]

    def _step(self, direction):
        self.cut_idx = (self.cut_idx + direction) % len(CUTS)
        self._name_scroll_x = 0.0
        self._size_scroll_x = 0.0
        self._use_scroll_x = 0.0
        self.frame = 0
        self.frame_timer = 0.0

    def _jump_family(self, direction):
        cur = self._current()['family']
        target = (cur + direction) % len(FAMILIES)
        if _FAMILY_CUTS[target]:
            self.cut_idx = _FAMILY_CUTS[target][0]
        self._name_scroll_x = 0.0
        self._size_scroll_x = 0.0
        self._use_scroll_x = 0.0
        self.frame = 0
        self.frame_timer = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left_pressed:
            self._step(-1)
            self._scroll_dir = -1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True
        elif input_state.right_pressed:
            self._step(1)
            self._scroll_dir = 1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True

        if not input_state.left and not input_state.right:
            self._scroll_dir = 0

        if input_state.up_pressed:
            self._jump_family(-1)
            consumed = True
        elif input_state.down_pressed:
            self._jump_family(1)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._name_scroll_x = 0.0
            self._size_scroll_x = 0.0
            self._use_scroll_x = 0.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Auto-scroll nav
        if self._scroll_dir != 0:
            self._scroll_hold += dt
            if self._scroll_hold >= self.SCROLL_DELAY:
                self._scroll_accum += dt
                while self._scroll_accum >= self.SCROLL_RATE:
                    self._scroll_accum -= self.SCROLL_RATE
                    self._step(self._scroll_dir)

        cut = self._current()

        # Advance animation frame
        self.frame_timer += dt
        hold = cut['hold'][self.frame]
        if self.frame_timer >= hold:
            self.frame_timer -= hold
            self.frame = (self.frame + 1) % cut['n_frames']

        # Scroll text
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, cut['name'], 48, dt, 18)
        size_text = f"{cut['size']}  {cut['desc']}"
        self._size_scroll_x = self._advance_scroll(
            self._size_scroll_x, size_text, 60, dt, 16)
        self._use_scroll_x = self._advance_scroll(
            self._use_scroll_x, cut['use'], 60, dt, 16)

    def _advance_scroll(self, scroll_x, text, avail_px, dt, speed):
        text_px = len(text) * 4
        if text_px > avail_px:
            scroll_x += dt * speed
            total = self.SCROLL_LEAD_IN + text_px + 20
            if scroll_x >= total:
                scroll_x -= total
        return scroll_x

    # ── Main draw ──────────────────────────────────────────────────

    def draw(self):
        d = self.display
        d.clear()

        cut = self._current()
        fam = cut['family']
        fam_color = FAMILY_COLORS[fam]

        # ── Header ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(cut['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(fam_color, 0.6))
        name_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_x, self.NAME_Y,
                                  cut['name'], fam_color,
                                  self._name_scroll_x, 63 - name_x)
        self._draw_sep(d, self.SEP1_Y)

        # ── Animation ──
        self._draw_animation(d, cut)
        self._draw_sep(d, self.SEP2_Y)

        # ── Size + description (scrolling) ──
        size_text = f"{cut['size']}  {cut['desc']}"
        self._draw_scrolling_text(d, 2, self.SIZE_Y,
                                  size_text, _dim(fam_color, 0.5),
                                  self._size_scroll_x, 60)
        self._draw_sep(d, self.SEP3_Y)

        # ── Use (scrolling) ──
        self._draw_scrolling_text(d, 2, self.USE_Y,
                                  cut['use'], TEXT_DIM,
                                  self._use_scroll_x, 60)
        self._draw_sep(d, self.SEP4_Y)

        # ── Family name ──
        fam_name = FAMILIES[fam]
        fam_px = len(fam_name) * 4
        d.draw_text_small((64 - fam_px) // 2, self.FAM_Y,
                          fam_name, _dim(fam_color, 0.35))

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)
        pos_str = f'{self.cut_idx + 1}/{len(CUTS)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)
        fam_list = _FAMILY_CUTS[fam]
        fam_pos = fam_list.index(self.cut_idx) + 1 if self.cut_idx in fam_list else 1
        fam_str = f'{fam_pos}/{len(fam_list)}'
        fam_str_px = len(fam_str) * 4
        d.draw_text_small(63 - fam_str_px, self.FOOT_Y, fam_str, fam_color)

    # ── Animation drawing ──────────────────────────────────────────

    def _draw_animation(self, d, cut):
        frame = self.frame

        # Board (always present)
        self._draw_board(d)

        # Step label (dimmed, top of anim area)
        label = cut['labels'][frame]
        label_px = len(label) * 4
        d.draw_text_small((64 - label_px) // 2, self.ANIM_TOP + 1,
                          label, LABEL_DIM)

        # Frame content
        dispatch = {
            'JULIENNE': self._draw_julienne,
            'BATONNET': self._draw_batonnet,
            'CHIFFONADE': self._draw_chiffonade,
            'BRUNOISE': self._draw_brunoise,
            'SMALL DICE': self._draw_small_dice,
            'MINCE': self._draw_mince,
            'BIAS CUT': self._draw_bias,
            'OBLIQUE': self._draw_oblique,
            'CHOP': self._draw_chop,
        }
        fn = dispatch.get(cut['name'])
        if fn:
            fn(d, frame)

    def _draw_board(self, d):
        """Wooden cutting board across the bottom of the animation area."""
        for y in range(self.BOARD_Y, self.BOARD_Y + 4):
            for x in range(6, 58):
                seed = x * 7 + y * 3
                if seed % 11 == 0:
                    d.set_pixel(x, y, _BL)
                elif seed % 13 == 0:
                    d.set_pixel(x, y, _BD)
                else:
                    d.set_pixel(x, y, _BW)

    def _draw_knife(self, d, cx, top_y, blade_h=8):
        """Draw a vertical chef's knife blade at cx, handle on top."""
        # Handle (3px tall)
        for y in range(top_y, top_y + 3):
            d.set_pixel(cx - 1, y, _KH)
            d.set_pixel(cx,     y, _KB)
            d.set_pixel(cx + 1, y, _KH)
        # Bolster
        by = top_y + 3
        d.set_pixel(cx - 1, by, _KD)
        d.set_pixel(cx,     by, _KS)
        d.set_pixel(cx + 1, by, _KD)
        # Blade
        for y in range(top_y + 4, top_y + 4 + blade_h - 1):
            d.set_pixel(cx - 1, y, _KS)
            d.set_pixel(cx,     y, _KL)
            d.set_pixel(cx + 1, y, _KS)
        # Edge
        ey = top_y + 3 + blade_h
        d.set_pixel(cx - 1, ey, _KD)
        d.set_pixel(cx,     ey, _KD)
        d.set_pixel(cx + 1, ey, _KD)

    def _draw_knife_diagonal(self, d, tip_x, tip_y, length=10):
        """Draw a knife angled ~45° from bottom-left tip to upper-right handle."""
        # Blade from tip upward-right
        for i in range(length):
            x = tip_x + i
            y = tip_y - i
            d.set_pixel(x - 1, y, _KS)
            d.set_pixel(x,     y, _KL)
            d.set_pixel(x,     y - 1, _KS)
        # Edge at tip
        d.set_pixel(tip_x - 1, tip_y + 1, _KD)
        d.set_pixel(tip_x,     tip_y + 1, _KD)
        # Bolster
        bx = tip_x + length
        by = tip_y - length
        d.set_pixel(bx, by, _KD)
        d.set_pixel(bx + 1, by, _KD)
        d.set_pixel(bx, by - 1, _KD)
        # Handle (continues diagonal)
        for i in range(1, 4):
            x = bx + i
            y = by - i
            d.set_pixel(x, y, _KH)
            d.set_pixel(x + 1, y, _KB)
            d.set_pixel(x, y - 1, _KH)

    # ── Julienne frames ────────────────────────────────────────────

    def _draw_julienne(self, d, frame):
        s = self.SURFACE_Y  # y where things rest on the board

        if frame == 0:
            # Whole carrot on board
            self._draw_carrot_whole(d, 14, s)

        elif frame == 1:
            # Split lengthwise — two halves with gap, knife to the side
            self._draw_carrot_half(d, 14, s - 4, highlight_top=True)
            self._draw_carrot_half(d, 14, s - 1, highlight_top=False)
            self._draw_knife(d, 46, s - 15, blade_h=8)

        elif frame == 2:
            # Sliced into thin planks — 5 flat strips stacked with gaps
            for i in range(5):
                self._draw_plank(d, 14, s - 7 + i * 2, 28)

        elif frame == 3:
            # Planks stacked on right being cut crosswise, sticks on left
            # Stacked planks (seen from the end — short vertical block)
            for i in range(5):
                self._draw_plank(d, 35, s - 7 + i * 2, 12)
            # Finished matchsticks on the left
            self._draw_matchsticks(d, 10, s - 8)
            # Knife between
            self._draw_knife(d, 32, s - 15, blade_h=8)

        elif frame == 4:
            # Finished julienne — long thin matchsticks across the board
            self._draw_matchsticks_full(d, 10, s - 9)

    def _draw_carrot_whole(self, d, sx, surf_y):
        """Whole carrot, side view, thick end left, tapering right."""
        length = 30
        for i in range(length):
            t = i / length
            h = max(1, round(4.5 * (1 - t * 0.85)))
            top = surf_y - h + 1
            for dy in range(h):
                if dy == 0 and h > 1:
                    c = _CL
                elif dy == h - 1 and h > 2:
                    c = _CD
                else:
                    c = _CO
                d.set_pixel(sx + i, top + dy, c)
        # Green leafy top at thick end
        d.set_pixel(sx - 1, surf_y - 4, _CG)
        d.set_pixel(sx - 2, surf_y - 5, _CG)
        d.set_pixel(sx,     surf_y - 5, _CG)
        d.set_pixel(sx - 1, surf_y - 6, _CK)
        d.set_pixel(sx + 1, surf_y - 5, _CK)
        d.set_pixel(sx - 3, surf_y - 6, _CK)

    def _draw_carrot_half(self, d, sx, y, highlight_top=True):
        """One lengthwise half of a carrot (1-2px tall, tapering)."""
        length = 28
        for i in range(length):
            t = i / length
            h = max(1, round(2.2 * (1 - t * 0.75)))
            for dy in range(h):
                if highlight_top:
                    c = _CL if dy == 0 else _CO
                else:
                    c = _CO if dy == 0 else _CD
                d.set_pixel(sx + i, y + dy, c)

    def _draw_plank(self, d, sx, y, length):
        """Single thin plank, 1px tall with highlight variation."""
        for i in range(length):
            t = i / length
            if t > 0.93:
                c = _CD
            elif i % 8 == 0:
                c = _CL
            else:
                c = _CO
            d.set_pixel(sx + i, y, c)

    def _draw_matchsticks(self, d, sx, sy):
        """Draw a half-portion of julienne matchsticks (for the CUT frame).
        Each stick is 5-7px long, 1px tall — clearly elongated."""
        # Hand-placed sticks for a natural scattered look
        sticks = [
            # (x_off, y_off, length, shade)  shade: 0=base, 1=light, 2=dark
            (0, 0, 6, 1),  (8, 0, 5, 0),
            (1, 2, 7, 0),  (10, 2, 6, 2),
            (0, 4, 5, 0),  (7, 4, 6, 1),
            (2, 6, 6, 2),  (9, 6, 5, 0),
            (0, 8, 7, 0),  (8, 8, 6, 1),
        ]
        shades = [_CO, _CL, _CD]
        for xo, yo, length, shade in sticks:
            c = shades[shade]
            for i in range(length):
                d.set_pixel(sx + xo + i, sy + yo, c)

    def _draw_matchsticks_full(self, d, sx, sy):
        """Draw the full finished julienne — long thin sticks spread wide.
        The 2-inch matchstick shape should be clearly visible."""
        sticks = [
            # (x_off, y_off, length, shade)
            (0, 0, 7, 1),  (9, 0, 6, 0),  (17, 0, 7, 0),  (26, 1, 6, 2),
            (2, 2, 6, 0),  (10, 2, 7, 2), (19, 2, 6, 1),  (27, 2, 5, 0),
            (0, 4, 7, 0),  (8, 4, 6, 1),  (16, 3, 7, 0),  (25, 4, 7, 0),
            (1, 6, 6, 2),  (9, 6, 7, 0),  (18, 6, 6, 0),  (26, 6, 6, 1),
            (0, 8, 7, 1),  (8, 8, 6, 0),  (16, 8, 7, 2),  (25, 8, 7, 0),
            (2, 10, 6, 0), (10, 10, 7, 1),(19, 10, 6, 0), (27, 10, 5, 2),
        ]
        shades = [_CO, _CL, _CD]
        for xo, yo, length, shade in sticks:
            c = shades[shade]
            for i in range(length):
                d.set_pixel(sx + xo + i, sy + yo, c)

    # ── Shared drawing helpers ────────────────────────────────────

    def _draw_thick_plank(self, d, sx, y, length, colors):
        """2px-tall plank with highlight/base/shadow colors."""
        base, light, dark = colors
        for i in range(length):
            t = i / length
            if t > 0.93:
                d.set_pixel(sx + i, y, dark)
                d.set_pixel(sx + i, y + 1, dark)
            elif i % 8 == 0:
                d.set_pixel(sx + i, y, light)
                d.set_pixel(sx + i, y + 1, base)
            else:
                d.set_pixel(sx + i, y, light)
                d.set_pixel(sx + i, y + 1, base)

    def _draw_sticks(self, d, sx, sy, sticks, colors):
        """Generic stick renderer. sticks = [(xo, yo, length, shade_idx), ...]"""
        for xo, yo, length, shade in sticks:
            c = colors[shade % len(colors)]
            for i in range(length):
                d.set_pixel(sx + xo + i, sy + yo, c)

    def _draw_thick_sticks(self, d, sx, sy, sticks, colors):
        """2px-wide stick renderer. sticks = [(xo, yo, length, shade_idx), ...]"""
        for xo, yo, length, shade in sticks:
            c = colors[shade % len(colors)]
            for i in range(length):
                d.set_pixel(sx + xo + i, sy + yo, c)
                d.set_pixel(sx + xo + i, sy + yo + 1, _dim(c, 0.75))

    def _draw_cubes(self, d, sx, sy, cubes, size, colors):
        """Generic cube scatter. cubes = [(xo, yo, shade_idx), ...]"""
        for xo, yo, shade in cubes:
            base = colors[shade % len(colors)]
            hi = colors[1] if len(colors) > 1 else base
            for dx in range(size):
                for dy in range(size):
                    c = hi if (dx == 0 and dy == 0) else base
                    d.set_pixel(sx + xo + dx, sy + yo + dy, c)

    def _draw_dots(self, d, sx, sy, dots, colors):
        """Fine dot scatter. dots = [(xo, yo, shade_idx), ...]"""
        for xo, yo, shade in dots:
            d.set_pixel(sx + xo, sy + yo, colors[shade % len(colors)])

    # ── Batonnet frames ──────────────────────────────────────────

    def _draw_batonnet(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            self._draw_carrot_whole(d, 14, s)

        elif frame == 1:
            # Thick planks (2px tall each)
            for i in range(3):
                self._draw_thick_plank(d, 14, s - 6 + i * 3, 28,
                                       (_CO, _CL, _CD))

        elif frame == 2:
            # Planks on right, thick sticks on left, knife between
            for i in range(3):
                self._draw_thick_plank(d, 35, s - 6 + i * 3, 14,
                                       (_CO, _CL, _CD))
            sticks = [
                (0, 0, 8, 1), (10, 0, 7, 0),
                (1, 3, 8, 0), (11, 3, 7, 2),
                (0, 6, 7, 0), (9, 6, 8, 1),
            ]
            self._draw_thick_sticks(d, 10, s - 8, sticks, [_CO, _CL, _CD])
            self._draw_knife(d, 32, s - 15, blade_h=8)

        elif frame == 3:
            # Result: thick sticks spread across
            sticks = [
                (0, 0, 8, 1),  (10, 0, 7, 0), (19, 0, 8, 0), (29, 1, 7, 2),
                (1, 3, 7, 0),  (10, 3, 8, 2), (20, 3, 7, 1), (29, 3, 6, 0),
                (0, 6, 8, 0),  (10, 6, 7, 1), (19, 6, 8, 0), (28, 7, 7, 0),
                (2, 9, 7, 2),  (11, 9, 8, 0), (21, 9, 7, 0), (30, 9, 6, 1),
            ]
            self._draw_thick_sticks(d, 10, s - 10, sticks, [_CO, _CL, _CD])

    # ── Chiffonade frames ────────────────────────────────────────

    def _draw_chiffonade(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            # Stacked basil leaves (3 overlapping ovals)
            for leaf_i in range(3):
                cy = s - 4 + leaf_i * 2
                cx = 32
                shade = [_BH, _BA, _BS][leaf_i]
                for dx in range(-8, 9):
                    w = max(0, 3 - abs(dx) // 3)
                    for dy in range(-w, w + 1):
                        c = _BH if dy == -w else shade
                        d.set_pixel(cx + dx, cy + dy, c)

        elif frame == 1:
            # Rolled tube
            cx, cy = 32, s - 3
            for dx in range(-10, 11):
                for dy in range(-2, 3):
                    dist = abs(dy)
                    if dist == 2:
                        c = _BS
                    elif dist == 0 and abs(dx) < 8:
                        c = _BH
                    else:
                        c = _BA
                    d.set_pixel(cx + dx, cy + dy, c)

        elif frame == 2:
            # Knife cutting across the roll
            cx, cy = 32, s - 3
            for dx in range(-10, 11):
                for dy in range(-2, 3):
                    dist = abs(dy)
                    c = _BS if dist == 2 else _BA
                    d.set_pixel(cx + dx, cy + dy, c)
            self._draw_knife(d, 36, s - 15, blade_h=8)

        elif frame == 3:
            # Thin curly ribbons scattered
            ribbons = [
                (10, -8, 7), (20, -7, 5), (30, -8, 6), (40, -7, 7),
                (12, -5, 6), (22, -4, 7), (32, -5, 5), (42, -4, 6),
                (9, -2, 5),  (19, -1, 6), (29, -2, 7), (39, -1, 5),
                (14, 1, 6),  (24, 0, 5),  (34, 1, 6),  (44, 0, 5),
            ]
            for rx, ry, rlen in ribbons:
                shade = _BH if (rx + ry) % 3 == 0 else _BA
                for i in range(rlen):
                    wave = 1 if (i % 3 == 1) else 0
                    d.set_pixel(rx + i, s + ry + wave, shade)
                    if i % 2 == 0:
                        d.set_pixel(rx + i, s + ry + wave - 1, _BS)

    # ── Brunoise frames ──────────────────────────────────────────

    def _draw_brunoise(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            # Julienne sticks gathered
            sticks = [
                (0, 0, 6, 1), (8, 0, 5, 0),
                (1, 2, 7, 0), (10, 2, 6, 2),
                (0, 4, 5, 0), (7, 4, 6, 1),
                (2, 6, 6, 2), (9, 6, 5, 0),
            ]
            self._draw_sticks(d, 20, s - 8, sticks, [_CO, _CL, _CD])

        elif frame == 1:
            # Tight bundle pushed together
            sticks = [
                (0, 0, 6, 1), (7, 0, 6, 0),
                (0, 1, 7, 0), (7, 1, 6, 2),
                (0, 2, 6, 0), (7, 2, 6, 1),
                (0, 3, 6, 2), (7, 3, 6, 0),
                (0, 4, 7, 0), (7, 4, 6, 1),
                (0, 5, 6, 0), (7, 5, 6, 2),
            ]
            self._draw_sticks(d, 24, s - 7, sticks, [_CO, _CL, _CD])

        elif frame == 2:
            # Knife cutting crosswise across bundle
            sticks = [
                (0, 0, 6, 1), (7, 0, 6, 0),
                (0, 1, 7, 0), (7, 1, 6, 2),
                (0, 2, 6, 0), (7, 2, 6, 1),
                (0, 3, 6, 2), (7, 3, 6, 0),
            ]
            self._draw_sticks(d, 30, s - 6, sticks, [_CO, _CL, _CD])
            # Some dots on left
            dots = [
                (0, 0, 0), (2, 1, 1), (4, 0, 2), (1, 3, 0), (3, 2, 1),
                (5, 3, 0), (0, 4, 2), (2, 5, 0), (4, 4, 1), (6, 5, 0),
            ]
            self._draw_dots(d, 14, s - 6, dots, [_CO, _CL, _CD])
            self._draw_knife(d, 27, s - 15, blade_h=8)

        elif frame == 3:
            # Tiny 1px dots scattered like confetti
            dots = [
                (0, 0, 0), (3, 1, 1), (6, 0, 2), (9, 1, 0), (12, 0, 1),
                (15, 1, 0), (18, 0, 2), (21, 1, 0), (24, 0, 1), (27, 1, 0),
                (1, 3, 1), (4, 2, 0), (7, 3, 2), (10, 2, 0), (13, 3, 1),
                (16, 2, 0), (19, 3, 2), (22, 2, 1), (25, 3, 0), (28, 2, 0),
                (2, 5, 0), (5, 4, 1), (8, 5, 0), (11, 4, 2), (14, 5, 0),
                (17, 4, 1), (20, 5, 0), (23, 4, 0), (26, 5, 2), (29, 4, 1),
                (0, 7, 2), (3, 6, 0), (6, 7, 1), (9, 6, 0), (12, 7, 0),
                (15, 6, 2), (18, 7, 0), (21, 6, 1), (24, 7, 0), (27, 6, 0),
                (1, 9, 0), (4, 8, 1), (7, 9, 2), (10, 8, 0), (13, 9, 1),
                (16, 8, 0), (19, 9, 0), (22, 8, 2), (25, 9, 0), (28, 8, 1),
            ]
            self._draw_dots(d, 10, s - 10, dots, [_CO, _CL, _CD])

    # ── Small Dice frames ────────────────────────────────────────

    def _draw_small_dice(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            # Whole potato (rounded rectangle)
            cx, cy = 32, s - 4
            for dx in range(-12, 13):
                h = 4 if abs(dx) < 10 else (3 if abs(dx) < 12 else 2)
                for dy in range(-h, h + 1):
                    if dy == -h:
                        c = _PL
                    elif dy == h:
                        c = _PD
                    else:
                        c = _PO if abs(dx) < 8 else _PD
                    d.set_pixel(cx + dx, cy + dy, c)

        elif frame == 1:
            # Thick planks
            for i in range(4):
                self._draw_thick_plank(d, 14, s - 8 + i * 3, 24,
                                       (_PO, _PL, _PD))

        elif frame == 2:
            # Cutting planks into cubes
            for i in range(3):
                self._draw_thick_plank(d, 34, s - 6 + i * 3, 14,
                                       (_PO, _PL, _PD))
            cubes = [
                (0, 0, 0), (3, 0, 1), (6, 0, 0), (9, 0, 2),
                (0, 3, 1), (3, 3, 0), (6, 3, 2), (9, 3, 0),
                (0, 6, 0), (3, 6, 2), (6, 6, 0), (9, 6, 1),
            ]
            self._draw_cubes(d, 14, s - 8, cubes, 2, [_PO, _PL, _PD])
            self._draw_knife(d, 31, s - 15, blade_h=8)

        elif frame == 3:
            # 2x2 cubes scattered
            cubes = [
                (0, 0, 0), (4, 0, 1), (8, 0, 2),  (12, 0, 0), (16, 0, 1),
                (20, 0, 0), (24, 0, 2), (28, 0, 0), (32, 0, 1),
                (1, 3, 1), (5, 3, 0), (9, 3, 0),  (13, 3, 2), (17, 3, 0),
                (21, 3, 1), (25, 3, 0), (29, 3, 2), (33, 3, 0),
                (0, 6, 0), (4, 6, 2), (8, 6, 1),  (12, 6, 0), (16, 6, 0),
                (20, 6, 2), (24, 6, 0), (28, 6, 1), (32, 6, 0),
                (2, 9, 2), (6, 9, 0), (10, 9, 1), (14, 9, 0), (18, 9, 2),
                (22, 9, 0), (26, 9, 1), (30, 9, 0),
            ]
            self._draw_cubes(d, 8, s - 10, cubes, 2, [_PO, _PL, _PD])

    # ── Mince frames ─────────────────────────────────────────────

    def _draw_mince(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            # Garlic clove (teardrop shape)
            cx, cy = 32, s - 4
            for dx in range(-5, 6):
                # Teardrop: wider at bottom, pointed at top
                w = max(0, 4 - abs(dx))
                top = -w - (2 if abs(dx) < 3 else 0)
                for dy in range(top, w + 1):
                    if dy == top:
                        c = _GL
                    elif dy == w:
                        c = _GD
                    else:
                        c = _GA
                    d.set_pixel(cx + dx, cy + dy, c)

        elif frame == 1:
            # Thin slices fanned out
            for i in range(6):
                x = 18 + i * 5
                for dy in range(-3, 4):
                    c = _GL if dy == -3 else (_GD if dy == 3 else _GA)
                    d.set_pixel(x, s - 4 + dy, c)
                    d.set_pixel(x + 1, s - 4 + dy, c)

        elif frame == 2:
            # Rock chop — knife with motion lines
            # Chopped bits below
            dots = [
                (0, 0, 0), (2, 1, 1), (5, 0, 2), (7, 1, 0), (10, 0, 1),
                (1, 3, 0), (3, 2, 2), (6, 3, 0), (8, 2, 1), (11, 3, 0),
            ]
            self._draw_dots(d, 22, s - 5, dots, [_GA, _GL, _GD])
            self._draw_knife(d, 32, s - 15, blade_h=8)
            # Motion lines (rocking)
            d.set_pixel(28, s - 10, _KD)
            d.set_pixel(36, s - 10, _KD)
            d.set_pixel(27, s - 9, _KD)
            d.set_pixel(37, s - 9, _KD)

        elif frame == 3:
            # Very fine dots, almost paste
            dots = []
            seed = 17
            for i in range(70):
                seed = (seed * 31 + 7) % 997
                xo = seed % 36
                yo = (seed // 36) % 12
                shade = seed % 3
                dots.append((xo, yo, shade))
            self._draw_dots(d, 10, s - 11, dots, [_GA, _GL, _GD])

    # ── Bias Cut frames ──────────────────────────────────────────

    def _draw_bias(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            # Scallion on board — green tube → white base
            for i in range(36):
                t = i / 36
                if t < 0.7:
                    top_c, bot_c = _SL, _SG
                else:
                    top_c, bot_c = _SW, _SC
                for dy in range(-2, 3):
                    c = top_c if dy < 0 else (bot_c if dy > 0 else
                         (_SL if t < 0.7 else _SW))
                    d.set_pixel(14 + i, s - 3 + dy, c)

        elif frame == 1:
            # Knife at diagonal angle
            for i in range(36):
                t = i / 36
                if t < 0.7:
                    top_c, bot_c = _SL, _SG
                else:
                    top_c, bot_c = _SW, _SC
                for dy in range(-2, 3):
                    c = top_c if dy < 0 else bot_c
                    d.set_pixel(14 + i, s - 3 + dy, c)
            # Diagonal knife matching the bias angle
            self._draw_knife_diagonal(d, 33, s - 1, length=9)

        elif frame == 2:
            # Several diagonal cuts — each segment is a slanted parallelogram
            for seg in range(5):
                sx_off = 12 + seg * 8
                is_green = seg < 3
                shade = _SG if is_green else _SC
                hi = _SL if is_green else _SW
                for dy in range(-2, 3):
                    # Shift x by dy to create diagonal slant
                    slant = -dy  # top-right to bottom-left diagonal
                    for i in range(5):
                        c = hi if dy < 0 else shade
                        d.set_pixel(sx_off + i + slant, s - 3 + dy, c)
            # Diagonal knife matching the bias angle
            self._draw_knife_diagonal(d, 46, s - 1, length=9)

        elif frame == 3:
            # Elongated diagonal ovals/diamonds
            ovals = [
                (10, -7, True), (18, -6, True), (26, -8, True),
                (34, -7, False), (42, -6, False),
                (12, -3, True), (20, -2, True), (28, -4, False),
                (36, -3, True), (44, -2, False),
                (9, 1, True),  (17, 0, False), (25, 1, True),
                (33, 0, True),  (41, 1, False),
            ]
            for ox, oy, is_green in ovals:
                base = _SG if is_green else _SC
                hi = _SL if is_green else _SW
                # Diamond shape: 4px wide, 2px tall
                d.set_pixel(ox + 1, s + oy, hi)
                d.set_pixel(ox + 2, s + oy, hi)
                d.set_pixel(ox, s + oy + 1, base)
                d.set_pixel(ox + 1, s + oy + 1, base)
                d.set_pixel(ox + 2, s + oy + 1, base)
                d.set_pixel(ox + 3, s + oy + 1, base)
                d.set_pixel(ox + 1, s + oy + 2, base)
                d.set_pixel(ox + 2, s + oy + 2, base)

    # ── Oblique frames ───────────────────────────────────────────

    def _draw_oblique(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            self._draw_carrot_whole(d, 14, s)

        elif frame == 1:
            # Diagonal cut showing angle
            length = 24
            for i in range(length):
                t = i / length
                h = max(1, round(4 * (1 - t * 0.8)))
                top = s - h + 1
                for dy in range(h):
                    c = _CL if dy == 0 else (_CD if dy == h - 1 else _CO)
                    d.set_pixel(14 + i, top + dy, c)
            # Cut line (diagonal)
            for j in range(5):
                d.set_pixel(28 + j, s - 5 + j, _KD)
            self._draw_knife(d, 32, s - 15, blade_h=8)

        elif frame == 2:
            # Rolled 90°, next cut
            length = 18
            for i in range(length):
                t = i / length
                h = max(1, round(3.5 * (1 - t * 0.7)))
                top = s - h + 1
                for dy in range(h):
                    c = _CL if dy == 0 else _CO
                    d.set_pixel(18 + i, top + dy, c)
            # One triangular piece to the left
            for dx in range(5):
                for dy in range(max(1, 3 - dx)):
                    c = _CO if dy > 0 else _CL
                    d.set_pixel(10 + dx, s - 2 + dy, c)
            self._draw_knife(d, 24, s - 15, blade_h=8)

        elif frame == 3:
            # Angular irregular triangular pieces scattered
            pieces = [
                (10, -8), (18, -7), (26, -9), (34, -8), (42, -7),
                (12, -4), (20, -3), (28, -5), (36, -4), (44, -3),
                (9, 0),   (17, -1), (25, 0),  (33, -1), (41, 0),
            ]
            for px, py in pieces:
                # Small triangle 3-4px
                shade = _CL if (px + py) % 3 == 0 else _CO
                dark = _CD
                d.set_pixel(px, s + py, shade)
                d.set_pixel(px + 1, s + py, shade)
                d.set_pixel(px + 2, s + py, dark)
                d.set_pixel(px, s + py + 1, dark)
                d.set_pixel(px + 1, s + py + 1, shade)
                d.set_pixel(px, s + py + 2, dark)

    # ── Chop frames ──────────────────────────────────────────────

    def _draw_chop(self, d, frame):
        s = self.SURFACE_Y

        if frame == 0:
            # Halved onion showing cross-section layers — larger dome
            self._draw_onion_dome(d, 32, s - 2)

        elif frame == 1:
            # Horizontal + vertical score cuts visible
            self._draw_onion_scored(d, 32, s - 2)

        elif frame == 2:
            # Knife cutting across
            self._draw_onion_scored(d, 32, s - 2)
            self._draw_knife(d, 40, s - 15, blade_h=8)

        elif frame == 3:
            # Rough irregular varied-size pieces
            pieces = [
                # (x, y, w, h, shade) — varied sizes for rough chop
                (8, -9, 3, 2, 0),  (14, -8, 2, 3, 1), (19, -9, 4, 2, 0),
                (26, -8, 2, 2, 2), (31, -9, 3, 3, 1), (37, -8, 2, 2, 0),
                (42, -9, 3, 2, 0), (10, -5, 2, 2, 1), (16, -4, 3, 3, 0),
                (22, -5, 4, 2, 2), (29, -4, 2, 3, 0), (35, -5, 3, 2, 1),
                (41, -4, 2, 2, 0), (9, -1, 3, 2, 0),  (15, 0, 2, 2, 1),
                (20, -1, 3, 3, 2), (27, 0, 4, 2, 0),  (34, -1, 2, 2, 0),
                (40, 0, 3, 2, 1),
            ]
            colors = [_OI, _OB, _OD]
            for px, py, w, h, shade in pieces:
                c = colors[shade]
                hi = _OL if shade == 0 else c
                for dx in range(w):
                    for dy in range(h):
                        pc = hi if (dx == 0 and dy == 0) else c
                        d.set_pixel(px + dx, s + py + dy, pc)

    # ── Onion helpers ──────────────────────────────────────────────

    def _draw_onion_dome(self, d, cx, cy):
        """Larger halved onion dome with concentric layer arcs."""
        # Concentric rings — outer to inner so inner overwrites
        for ring in range(6, 0, -1):
            color = _OI if ring % 2 == 0 else _OB
            half_w = ring * 2 + 1
            for dx in range(-half_w, half_w + 1):
                h = max(0, ring + 1 - (abs(dx) * (ring + 1)) // (half_w + 1))
                for dy in range(-h, 1):
                    d.set_pixel(cx + dx, cy + dy, color)
        # Skin outline on top
        for dx in range(-13, 14):
            h = max(0, 7 - (abs(dx) * 7) // 14)
            d.set_pixel(cx + dx, cy - h, _OD)
        # Flat bottom
        for dx in range(-12, 13):
            d.set_pixel(cx + dx, cy + 1, _OI)

    def _draw_onion_scored(self, d, cx, cy):
        """Larger onion dome with score-cut grid lines."""
        for dx in range(-12, 13):
            h = max(0, 7 - (abs(dx) * 7) // 14)
            for dy in range(-h, 2):
                if dy % 3 == 0 or dx % 4 == 0:
                    c = _OD
                else:
                    c = _OI if (dx + dy) % 2 == 0 else _OB
                d.set_pixel(cx + dx, cy + dy, c)

    # ── Text helpers (shared pattern) ──────────────────────────────

    def _draw_scrolling_text(self, d, start_x, y, text, color, scroll_x, avail_px):
        text_px = len(text) * 4
        if text_px <= avail_px:
            x = start_x + (avail_px - text_px) // 2
            d.draw_text_small(x, y, text, color)
        else:
            lead = self.SCROLL_LEAD_IN
            total = lead + text_px + 20
            sx = int(scroll_x) % total
            end_x = start_x + avail_px
            for cx in range(start_x, min(end_x, 63)):
                px = sx + (cx - start_x) - lead
                if px < 0:
                    continue
                char_idx = px // 4
                col = px % 4
                if col < 3 and 0 <= char_idx < len(text):
                    ch = text[char_idx]
                    self._draw_char_col(d, cx, y, ch, col, color)

    def _draw_sep(self, d, y):
        for x in range(64):
            d.set_pixel(x, y, SEP_COLOR)

    def _draw_char_col(self, d, x, y, ch, col, color):
        glyph = _FONT.get(ch.upper())
        if glyph is None or col >= 3:
            return
        for row_idx, row in enumerate(glyph):
            if row[col] == '1':
                d.set_pixel(x, y + row_idx, color)


_FONT = {
    'A': ['010', '101', '111', '101', '101'],
    'B': ['110', '101', '110', '101', '110'],
    'C': ['011', '100', '100', '100', '011'],
    'D': ['110', '101', '101', '101', '110'],
    'E': ['111', '100', '110', '100', '111'],
    'F': ['111', '100', '110', '100', '100'],
    'G': ['011', '100', '101', '101', '011'],
    'H': ['101', '101', '111', '101', '101'],
    'I': ['111', '010', '010', '010', '111'],
    'J': ['001', '001', '001', '101', '010'],
    'K': ['101', '110', '100', '110', '101'],
    'L': ['100', '100', '100', '100', '111'],
    'M': ['101', '111', '111', '101', '101'],
    'N': ['101', '111', '111', '111', '101'],
    'O': ['010', '101', '101', '101', '010'],
    'P': ['110', '101', '110', '100', '100'],
    'Q': ['010', '101', '101', '110', '011'],
    'R': ['110', '101', '110', '101', '101'],
    'S': ['011', '100', '010', '001', '110'],
    'T': ['111', '010', '010', '010', '010'],
    'U': ['101', '101', '101', '101', '011'],
    'V': ['101', '101', '101', '010', '010'],
    'W': ['101', '101', '111', '111', '101'],
    'X': ['101', '101', '010', '101', '101'],
    'Y': ['101', '101', '010', '010', '010'],
    'Z': ['111', '001', '010', '100', '111'],
    ' ': ['000', '000', '000', '000', '000'],
    '-': ['000', '000', '111', '000', '000'],
    '+': ['000', '010', '111', '010', '000'],
    ':': ['000', '010', '000', '010', '000'],
    '/': ['001', '001', '010', '100', '100'],
    '(': ['010', '100', '100', '100', '010'],
    ')': ['010', '001', '001', '001', '010'],
    '&': ['010', '101', '010', '101', '011'],
    "'": ['010', '010', '000', '000', '000'],
    '.': ['000', '000', '000', '000', '010'],
    '0': ['111', '101', '101', '101', '111'],
    '1': ['010', '110', '010', '010', '111'],
    '2': ['110', '001', '010', '100', '111'],
    '3': ['110', '001', '010', '001', '110'],
    '4': ['101', '101', '111', '001', '001'],
    '5': ['111', '100', '110', '001', '110'],
    '6': ['011', '100', '110', '101', '010'],
    '7': ['111', '001', '010', '010', '010'],
    '8': ['010', '101', '010', '101', '010'],
    '9': ['010', '101', '011', '001', '110'],
}

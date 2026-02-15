"""Baking - Ratios and formulas reference on 64x64 LED matrix.

Each entry shows baker's percentages or weight ratios with proportional
ingredient bars scaled relative to the largest component.
"""

from . import Visual

# ── Families ────────────────────────────────────────────────────────
FAMILIES = ["BREAD", "PIZZA", "PASTRY", "QUICK"]
FAMILY_COLORS = [
    (180, 140, 80),    # BREAD = warm brown
    (220, 80, 40),     # PIZZA = red-orange
    (220, 190, 100),   # PASTRY = butter gold
    (140, 180, 100),   # QUICK = soft green
]

HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)

# ── Baking data ─────────────────────────────────────────────────────
RECIPES = [
    # BREAD (family 0)
    {'name': 'STANDARD BREAD', 'family': 0, 'num': 1,
     'ratio': '100 FLOUR  62 WATER  2 SALT  1 YEAST',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('WATER', 62, (80, 140, 255)),
              ('SALT', 2, (240, 240, 240)),
              ('YEAST', 1, (200, 180, 80))],
     'note': 'BASIC SANDWICH BREAD  60-65% HYDRATION'},
    {'name': 'BAGEL', 'family': 0, 'num': 2,
     'ratio': '100 FLOUR  55 WATER  2 SALT  1 YEAST  2 MALT',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('WATER', 55, (80, 140, 255)),
              ('SALT', 2, (240, 240, 240)),
              ('YEAST', 1, (200, 180, 80)),
              ('MALT', 2, (180, 120, 40))],
     'note': 'LOW HYDRATION  DENSE CHEWY  BOIL THEN BAKE'},
    {'name': 'CIABATTA', 'family': 0, 'num': 3,
     'ratio': '100 FLOUR  68 WATER  2 SALT  1 YEAST',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('WATER', 68, (80, 140, 255)),
              ('SALT', 2, (240, 240, 240)),
              ('YEAST', 1, (200, 180, 80))],
     'note': 'HIGH HYDRATION  OPEN CRUMB  WET STICKY DOUGH'},
    {'name': 'FOCACCIA', 'family': 0, 'num': 4,
     'ratio': '100 FLOUR  80 WATER  5 OIL  2 SALT  1 YEAST',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('WATER', 80, (80, 140, 255)),
              ('OIL', 5, (180, 200, 60)),
              ('SALT', 2, (240, 240, 240)),
              ('YEAST', 1, (200, 180, 80))],
     'note': 'VERY HIGH HYDRATION  DIMPLE  GENEROUS OIL'},

    # PIZZA (family 1)
    {'name': 'NEAPOLITAN', 'family': 1, 'num': 5,
     'ratio': '100 FLOUR  60 WATER  3 SALT  0.2 YEAST',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('WATER', 60, (80, 140, 255)),
              ('SALT', 3, (240, 240, 240)),
              ('YEAST', 1, (200, 180, 80))],
     'note': 'LONG FERMENT 24-72H  900F OVEN  90 SEC BAKE'},
    {'name': 'NEW YORK', 'family': 1, 'num': 6,
     'ratio': '100 FLOUR  65 WATER  3 SALT  1 YEAST  3 OIL  2 SUGAR',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('WATER', 65, (80, 140, 255)),
              ('OIL', 3, (180, 200, 60)),
              ('SUGAR', 2, (240, 200, 200)),
              ('SALT', 3, (240, 240, 240)),
              ('YEAST', 1, (200, 180, 80))],
     'note': 'FOLDABLE THIN CRUST  OIL + SUGAR FOR BROWNING'},
    {'name': 'DETROIT', 'family': 1, 'num': 7,
     'ratio': '100 FLOUR  65 WATER  3 SALT  1 YEAST  4 OIL',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('WATER', 65, (80, 140, 255)),
              ('OIL', 4, (180, 200, 60)),
              ('SALT', 3, (240, 240, 240)),
              ('YEAST', 1, (200, 180, 80))],
     'note': 'THICK PAN STYLE  CRISPY CHEESE EDGE  BRICK CHEESE'},

    # PASTRY (family 2)
    {'name': 'POUND CAKE', 'family': 2, 'num': 8,
     'ratio': '1 FLOUR  1 BUTTER  1 SUGAR  1 EGG',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('BUTTR', 100, (240, 220, 100)),
              ('SUGAR', 100, (240, 200, 200)),
              ('EGG', 100, (240, 200, 80))],
     'note': 'EQUAL PARTS BY WEIGHT  CREAM BUTTER + SUGAR'},
    {'name': 'PIE DOUGH', 'family': 2, 'num': 9,
     'ratio': '3 FLOUR  2 FAT  1 WATER',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('FAT', 67, (240, 220, 100)),
              ('WATER', 33, (80, 140, 255))],
     'note': 'KEEP COLD  VISIBLE FAT PIECES  FLAKY LAYERS'},
    {'name': 'COOKIE DOUGH', 'family': 2, 'num': 10,
     'ratio': '3 FLOUR  2 FAT  1 SUGAR',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('FAT', 67, (240, 220, 100)),
              ('SUGAR', 33, (240, 200, 200))],
     'note': 'CREAM FAT + SUGAR  ADD EGGS  FOLD IN FLOUR'},

    # QUICK (family 3)
    {'name': 'MUFFINS', 'family': 3, 'num': 11,
     'ratio': '2 FLOUR  2 LIQUID  1 EGG  1 FAT',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('LIQID', 100, (80, 140, 255)),
              ('EGG', 50, (240, 200, 80)),
              ('FAT', 50, (240, 220, 100))],
     'note': 'MIX WET + DRY SEPARATELY  FOLD GENTLY  LUMPY OK'},
    {'name': 'BISCUITS', 'family': 3, 'num': 12,
     'ratio': '3 FLOUR  2 LIQUID  1 FAT',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('LIQID', 67, (80, 140, 255)),
              ('FAT', 33, (240, 220, 100))],
     'note': 'CUT COLD FAT INTO FLOUR  PAT + FOLD  DO NOT TWIST'},
    {'name': 'PANCAKES', 'family': 3, 'num': 13,
     'ratio': '2 FLOUR  2 LIQUID  1 EGG  0.5 FAT',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('LIQID', 100, (80, 140, 255)),
              ('EGG', 50, (240, 200, 80)),
              ('FAT', 25, (240, 220, 100))],
     'note': 'THIN BATTER  REST 5 MIN  BUBBLES = FLIP TIME'},
    {'name': 'CREPES', 'family': 3, 'num': 14,
     'ratio': '1 FLOUR  1 EGG  1 MILK',
     'bars': [('FLOUR', 100, (220, 180, 120)),
              ('EGG', 100, (240, 200, 80)),
              ('MILK', 100, (80, 140, 255))],
     'note': 'VERY THIN BATTER  REST 1 HR  SWIRL PAN'},
]

# Build per-family index
_FAMILY_RECIPES = [[] for _ in range(len(FAMILIES))]
for _i, _r in enumerate(RECIPES):
    _FAMILY_RECIPES[_r['family']].append(_i)


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


class Baking(Visual):
    name = "BAKING"
    description = "Baking ratios and formulas"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout Y positions
    NAME_Y = 1
    SEP1_Y = 7
    RATIO_Y = 9
    SEP2_Y = 15
    BARS_Y = 17      # ingredient bars start
    BAR_H = 5        # height per bar row
    BAR_GAP = 1      # gap between bars
    SEP3_Y = 51
    NOTE_Y = 53
    FOOT_SEP_Y = 57
    FOOT_Y = 59

    def reset(self):
        self.time = 0.0
        self.idx = 0
        self._name_scroll_x = 0.0
        self._ratio_scroll_x = 0.0
        self._note_scroll_x = 0.0
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0
        self._switch_flash = 0.0

    def _current(self):
        return RECIPES[self.idx % len(RECIPES)]

    def _step(self, direction):
        self.idx = (self.idx + direction) % len(RECIPES)
        self._name_scroll_x = 0.0
        self._ratio_scroll_x = 0.0
        self._note_scroll_x = 0.0
        self._switch_flash = 0.15

    def _jump_family(self, direction):
        cur = self._current()['family']
        target = (cur + direction) % len(FAMILIES)
        if _FAMILY_RECIPES[target]:
            self.idx = _FAMILY_RECIPES[target][0]
        self._name_scroll_x = 0.0
        self._ratio_scroll_x = 0.0
        self._note_scroll_x = 0.0
        self._switch_flash = 0.15

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
            self._ratio_scroll_x = 0.0
            self._note_scroll_x = 0.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if self._scroll_dir != 0:
            self._scroll_hold += dt
            if self._scroll_hold >= self.SCROLL_DELAY:
                self._scroll_accum += dt
                while self._scroll_accum >= self.SCROLL_RATE:
                    self._scroll_accum -= self.SCROLL_RATE
                    self._step(self._scroll_dir)

        if self._switch_flash > 0:
            self._switch_flash = max(0.0, self._switch_flash - dt)

        r = self._current()
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, r['name'], 48, dt, 18)
        self._ratio_scroll_x = self._advance_scroll(
            self._ratio_scroll_x, r['ratio'], 60, dt, 16)
        self._note_scroll_x = self._advance_scroll(
            self._note_scroll_x, r['note'], 60, dt, 16)

    def _advance_scroll(self, scroll_x, text, avail_px, dt, speed):
        text_px = len(text) * 4
        if text_px > avail_px:
            scroll_x += dt * speed
            total = self.SCROLL_LEAD_IN + text_px + 20
            if scroll_x >= total:
                scroll_x -= total
        return scroll_x

    def draw(self):
        d = self.display
        d.clear()

        r = self._current()
        fam = r['family']
        fam_color = FAMILY_COLORS[fam]

        # ── Header: recipe name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(r['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(fam_color, 0.6))

        name_start_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_start_x, self.NAME_Y,
                                  r['name'], fam_color,
                                  self._name_scroll_x, 63 - name_start_x)

        # ── Sep 1 ──
        self._draw_sep(d, self.SEP1_Y)

        # ── Ratio text (scrolling) ──
        self._draw_scrolling_text(d, 2, self.RATIO_Y,
                                  r['ratio'], (180, 180, 200),
                                  self._ratio_scroll_x, 60)

        # ── Sep 2 ──
        self._draw_sep(d, self.SEP2_Y)

        # ── Ingredient bars ──
        bars = r['bars']
        max_val = max(b[1] for b in bars) if bars else 1
        max_bar_w = 38  # max pixel width for widest bar
        label_w = 22    # 5 chars * 4px + 2px pad

        for i, (label, val, color) in enumerate(bars):
            y = self.BARS_Y + i * (self.BAR_H + self.BAR_GAP)
            if y + self.BAR_H > self.SEP3_Y:
                break

            # Label (5 chars max)
            d.draw_text_small(1, y, label[:5], _dim(color, 0.6))

            # Proportional bar
            bar_w = int(val / max_val * max_bar_w) if max_val > 0 else 0
            bar_w = max(bar_w, 1)  # at least 1px
            bar_y = y + 1  # center 3px bar in 5px row
            bar_h = 3

            for bx in range(label_w, label_w + bar_w):
                for by in range(bar_y, bar_y + bar_h):
                    d.set_pixel(bx, by, color)

        # ── Sep 3 ──
        self._draw_sep(d, self.SEP3_Y)

        # ── Note text (scrolling) ──
        self._draw_scrolling_text(d, 2, self.NOTE_Y,
                                  r['note'], TEXT_DIM,
                                  self._note_scroll_x, 60)

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)

        pos_str = f'{self.idx + 1}/{len(RECIPES)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)

        # Family position right-aligned
        fam_list = _FAMILY_RECIPES[fam]
        fam_pos = fam_list.index(self.idx) + 1 if self.idx in fam_list else 1
        fam_str = f'{fam_pos}/{len(fam_list)}'
        fam_str_px = len(fam_str) * 4
        d.draw_text_small(63 - fam_str_px, self.FOOT_Y, fam_str, fam_color)

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

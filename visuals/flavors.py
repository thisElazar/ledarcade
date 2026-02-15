"""Flavors - Regional cuisine flavor profiles on 64x64 LED matrix.

Each cuisine shows key ingredients and 5 flavor intensity bars
(sweet, sour, salty, spicy, umami) on a 0-5 scale.
"""

from . import Visual

# ── Regions ─────────────────────────────────────────────────────────
REGIONS = ["EAST ASIA", "SE ASIA", "SOUTH ASIA", "AMERICAS", "EUROPE", "MIDEAST"]
REGION_COLORS = [
    (220, 60, 60),     # EAST ASIA = red
    (60, 200, 120),    # SE ASIA = green
    (240, 160, 40),    # SOUTH ASIA = saffron
    (80, 160, 220),    # AMERICAS = blue
    (180, 140, 200),   # EUROPE = lavender
    (200, 160, 60),    # MIDEAST = amber
]

HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)

# Bar label names and colors
BAR_LABELS = ['SWT', 'SOR', 'SLT', 'SPC', 'UMA']
BAR_COLORS = [
    (255, 160, 40),    # SWEET = warm orange
    (100, 220, 60),    # SOUR = bright green
    (220, 220, 240),   # SALTY = white
    (255, 60, 40),     # SPICY = red
    (160, 80, 255),    # UMAMI = purple
]

# ── Cuisine data ────────────────────────────────────────────────────
#                                              SWT SOR SLT SPC UMA
CUISINES = [
    # EAST ASIA (region 0)
    {'name': 'JAPANESE', 'region': 0, 'num': 1,
     'ingredients': 'SOY + MISO + MIRIN + DASHI + SESAME + GINGER + WASABI',
     'bars': [2, 2, 4, 1, 5]},
    {'name': 'CHINESE', 'region': 0, 'num': 2,
     'ingredients': 'SOY + SESAME OIL + GINGER + GARLIC + FIVE-SPICE + HOISIN + CHILI OIL',
     'bars': [2, 2, 4, 3, 4]},
    {'name': 'KOREAN', 'region': 0, 'num': 3,
     'ingredients': 'GOCHUJANG + GOCHUGARU + SESAME + SOY + GARLIC + GINGER + KIMCHI',
     'bars': [2, 1, 4, 5, 4]},

    # SE ASIA (region 1)
    {'name': 'THAI', 'region': 1, 'num': 4,
     'ingredients': 'LEMONGRASS + FISH SAUCE + LIME + COCONUT + CHILI + BASIL',
     'bars': [4, 4, 4, 4, 3]},
    {'name': 'VIETNAMESE', 'region': 1, 'num': 5,
     'ingredients': 'FISH SAUCE + LIME + HERBS + CHILI + RICE NOODLES + LEMONGRASS',
     'bars': [3, 4, 4, 2, 4]},

    # SOUTH ASIA (region 2)
    {'name': 'INDIAN', 'region': 2, 'num': 6,
     'ingredients': 'TURMERIC + CUMIN + CORIANDER + GARAM MASALA + GINGER + GARLIC + YOGURT',
     'bars': [2, 2, 3, 4, 3]},

    # AMERICAS (region 3)
    {'name': 'MEXICAN', 'region': 3, 'num': 7,
     'ingredients': 'CUMIN + CHILI + LIME + CILANTRO + GARLIC + OREGANO + AVOCADO',
     'bars': [1, 3, 2, 4, 2]},
    {'name': 'CARIBBEAN', 'region': 3, 'num': 8,
     'ingredients': 'ALLSPICE + SCOTCH BONNET + NUTMEG + CINNAMON + RUM + COCONUT + LIME',
     'bars': [3, 2, 2, 4, 1]},

    # EUROPE (region 4)
    {'name': 'FRENCH', 'region': 4, 'num': 9,
     'ingredients': 'BUTTER + SHALLOTS + THYME + TARRAGON + CREAM + WINE + MUSHROOMS',
     'bars': [1, 2, 2, 0, 4]},
    {'name': 'ITALIAN', 'region': 4, 'num': 10,
     'ingredients': 'GARLIC + BASIL + OREGANO + EVOO + TOMATOES + PARMESAN + LEMON',
     'bars': [1, 3, 3, 1, 4]},
    {'name': 'SPANISH', 'region': 4, 'num': 11,
     'ingredients': 'EVOO + SAFFRON + SMOKED PAPRIKA + GARLIC + SHERRY VINEGAR + ALMONDS',
     'bars': [1, 2, 3, 2, 3]},

    # MIDEAST (region 5)
    {'name': 'MIDDLE EASTERN', 'region': 5, 'num': 12,
     'ingredients': 'SUMAC + ZAATAR + CUMIN + TAHINI + POMEGRANATE + YOGURT + MINT',
     'bars': [3, 3, 2, 2, 2]},
    {'name': 'MOROCCAN', 'region': 5, 'num': 13,
     'ingredients': 'RAS EL HANOUT + HARISSA + PRESERVED LEMON + SAFFRON + HONEY + ALMONDS',
     'bars': [3, 2, 2, 3, 1]},
]

# Build per-region index
_REGION_CUISINES = [[] for _ in range(len(REGIONS))]
for _i, _c in enumerate(CUISINES):
    _REGION_CUISINES[_c['region']].append(_i)


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


class Flavors(Visual):
    name = "FLAVORS"
    description = "Regional flavor profiles"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout Y positions
    NAME_Y = 1
    SEP1_Y = 7
    INGR_Y = 9
    SEP2_Y = 15
    BAR_START_Y = 17   # first bar row
    BAR_SPACING = 6    # 5px text row + 1px gap
    SEP3_Y = 47
    REGION_Y = 49
    FOOT_SEP_Y = 57
    FOOT_Y = 59

    def reset(self):
        self.time = 0.0
        self.idx = 0
        self._name_scroll_x = 0.0
        self._ingr_scroll_x = 0.0
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0
        self._switch_flash = 0.0

    def _current(self):
        return CUISINES[self.idx % len(CUISINES)]

    def _step(self, direction):
        self.idx = (self.idx + direction) % len(CUISINES)
        self._name_scroll_x = 0.0
        self._ingr_scroll_x = 0.0
        self._switch_flash = 0.15

    def _jump_region(self, direction):
        cur = self._current()['region']
        target = (cur + direction) % len(REGIONS)
        if _REGION_CUISINES[target]:
            self.idx = _REGION_CUISINES[target][0]
        self._name_scroll_x = 0.0
        self._ingr_scroll_x = 0.0
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
            self._jump_region(-1)
            consumed = True
        elif input_state.down_pressed:
            self._jump_region(1)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._name_scroll_x = 0.0
            self._ingr_scroll_x = 0.0
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

        c = self._current()
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, c['name'], 48, dt, 18)
        self._ingr_scroll_x = self._advance_scroll(
            self._ingr_scroll_x, c['ingredients'], 60, dt, 16)

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

        c = self._current()
        region = c['region']
        region_color = REGION_COLORS[region]

        # ── Header: cuisine name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(c['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(region_color, 0.6))

        name_start_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_start_x, self.NAME_Y,
                                  c['name'], region_color,
                                  self._name_scroll_x, 63 - name_start_x)

        # ── Sep 1 ──
        self._draw_sep(d, self.SEP1_Y)

        # ── Ingredients (scrolling) ──
        self._draw_scrolling_text(d, 2, self.INGR_Y,
                                  c['ingredients'], (180, 180, 200),
                                  self._ingr_scroll_x, 60)

        # ── Sep 2 ──
        self._draw_sep(d, self.SEP2_Y)

        # ── Flavor bars ──
        bars = c['bars']
        for i in range(5):
            y = self.BAR_START_Y + i * self.BAR_SPACING
            label = BAR_LABELS[i]
            bar_color = BAR_COLORS[i]
            level = bars[i]

            # Label (3 chars at x=1)
            d.draw_text_small(1, y, label, _dim(bar_color, 0.6))

            # Bar area: x=15 to x=60, level 0-5, each unit = 9px
            bar_x = 15
            bar_y = y + 1  # center 3px bar in 5px text row
            bar_h = 3

            # Draw dim dots for empty positions
            for dot in range(5):
                dot_x = bar_x + dot * 9 + 4
                d.set_pixel(dot_x, bar_y + 1, _dim(bar_color, 0.15))

            # Draw filled bar
            if level > 0:
                fill_w = level * 9
                for bx in range(bar_x, bar_x + fill_w):
                    for by in range(bar_y, bar_y + bar_h):
                        d.set_pixel(bx, by, bar_color)

        # ── Sep 3 ──
        self._draw_sep(d, self.SEP3_Y)

        # ── Region name (centered, dimmed) ──
        region_name = REGIONS[region]
        region_name_px = len(region_name) * 4
        region_x = (64 - region_name_px) // 2
        d.draw_text_small(region_x, self.REGION_Y, region_name, _dim(region_color, 0.35))

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)

        pos_str = f'{self.idx + 1}/{len(CUISINES)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)

        # Region position right-aligned
        reg_list = _REGION_CUISINES[region]
        reg_pos = reg_list.index(self.idx) + 1 if self.idx in reg_list else 1
        reg_str = f'{reg_pos}/{len(reg_list)}'
        reg_str_px = len(reg_str) * 4
        d.draw_text_small(63 - reg_str_px, self.FOOT_Y, reg_str, region_color)

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

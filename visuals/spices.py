"""Spices - Famous spice blend recipes from around the world on 64x64 LED matrix.

Each blend shows: name, origin, meaning, component spices (the actual recipe),
and what dishes to use it on. Complements Flavors (macro cuisine profiles) with
the micro view — what's actually *in* ras el hanout, garam masala, etc.
"""

from . import Visual

# ── Regions ────────────────────────────────────────────────────────
REGIONS = ["N. AFRICA", "MIDDLE EAST", "SOUTH ASIA", "EAST ASIA", "AMERICAS", "EUROPE"]
REGION_COLORS = [
    (200, 120, 50),    # N. AFRICA = burnt orange
    (200, 160, 60),    # MIDDLE EAST = amber
    (240, 160, 40),    # SOUTH ASIA = saffron
    (220, 60, 60),     # EAST ASIA = red
    (80, 180, 100),    # AMERICAS = green
    (140, 130, 200),   # EUROPE = lavender
]

HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)
PLUS_COLOR = (180, 180, 200)

# ── Blend data ─────────────────────────────────────────────────────
BLENDS = [
    # ── N. AFRICA (region 0) ─────────────────────────────
    {'name': 'RAS EL HANOUT', 'region': 0, 'num': 1,
     'origin': 'MOROCCO',
     'meaning': 'HEAD OF THE SHOP',
     'components': 'CUMIN + CORIANDER + CINNAMON + PAPRIKA + TURMERIC + GINGER + CARDAMOM + CLOVE + NUTMEG + BLACK PEPPER + ROSE PETALS',
     'use': 'TAGINES / COUSCOUS / ROAST LAMB / MERGUEZ'},
    {'name': 'HARISSA', 'region': 0, 'num': 2,
     'origin': 'TUNISIA',
     'meaning': 'TO CRUSH',
     'components': 'DRIED CHILES + CARAWAY + CORIANDER + CUMIN + GARLIC + OLIVE OIL + SMOKED PAPRIKA',
     'use': 'COUSCOUS / MERGUEZ / SHAKSHUKA / EGGS'},
    {'name': 'DUKKAH', 'region': 0, 'num': 3,
     'origin': 'EGYPT',
     'meaning': 'TO POUND',
     'components': 'HAZELNUTS + SESAME + CORIANDER + CUMIN + BLACK PEPPER + SALT',
     'use': 'BREAD + OLIVE OIL / SALADS / CRUSTED FISH'},
    {'name': 'BERBERE', 'region': 0, 'num': 4,
     'origin': 'ETHIOPIA',
     'meaning': 'HOT',
     'components': 'CHILI + FENUGREEK + CORIANDER + CARDAMOM + BLACK PEPPER + ALLSPICE + CLOVE + GINGER + CINNAMON',
     'use': 'DORO WAT / STEWS / LENTILS / KITFO'},

    # ── MIDDLE EAST (region 1) ───────────────────────────
    {'name': "ZA'ATAR", 'region': 1, 'num': 5,
     'origin': 'LEVANT',
     'meaning': 'WILD THYME',
     'components': 'THYME + SUMAC + SESAME + OREGANO + MARJORAM + SALT',
     'use': 'FLATBREAD / LABNEH / EGGS / ROAST VEG'},
    {'name': 'BAHARAT', 'region': 1, 'num': 6,
     'origin': 'ARABIA',
     'meaning': 'SPICES',
     'components': 'BLACK PEPPER + CORIANDER + CINNAMON + CLOVE + CUMIN + CARDAMOM + NUTMEG + PAPRIKA',
     'use': 'RICE / GRILLED MEAT / STEWS / KIBBEH'},
    {'name': 'ADVIEH', 'region': 1, 'num': 7,
     'origin': 'PERSIA',
     'meaning': 'SPICE',
     'components': 'CINNAMON + CARDAMOM + CUMIN + ROSE PETALS + TURMERIC + NUTMEG',
     'use': 'RICE / STEWS / SWEETS / JEWELED RICE'},

    # ── SOUTH ASIA (region 2) ────────────────────────────
    {'name': 'GARAM MASALA', 'region': 2, 'num': 8,
     'origin': 'NORTH INDIA',
     'meaning': 'HOT SPICE',
     'components': 'CUMIN + CORIANDER + CARDAMOM + CINNAMON + CLOVE + BLACK PEPPER + NUTMEG',
     'use': 'CURRIES / DAL / FINISHING SPICE'},
    {'name': 'CHAAT MASALA', 'region': 2, 'num': 9,
     'origin': 'INDIA',
     'meaning': 'TO LICK',
     'components': 'AMCHUR + CUMIN + BLACK SALT + CORIANDER + GINGER + CHILI + ASAFOETIDA',
     'use': 'FRUIT / SNACKS / CHAAT / RAITA'},
    {'name': 'PANCH PHORON', 'region': 2, 'num': 10,
     'origin': 'BENGAL',
     'meaning': 'FIVE SPICES',
     'components': 'FENUGREEK + NIGELLA + CUMIN + MUSTARD SEED + FENNEL  (EQUAL PARTS  WHOLE SEEDS)',
     'use': 'DAL / VEGETABLES / PICKLES / FISH'},
    {'name': 'MADRAS CURRY', 'region': 2, 'num': 11,
     'origin': 'SOUTH INDIA',
     'meaning': 'CURRY BLEND',
     'components': 'CORIANDER + CUMIN + TURMERIC + CHILI + MUSTARD + FENUGREEK + BLACK PEPPER',
     'use': 'CURRIES / VINDALOO / RICE / LENTILS'},

    # ── EAST ASIA (region 3) ─────────────────────────────
    {'name': 'FIVE-SPICE', 'region': 3, 'num': 12,
     'origin': 'CHINA',
     'meaning': 'FIVE FRAGRANCE',
     'components': 'STAR ANISE + CLOVE + CINNAMON + SICHUAN PEPPER + FENNEL',
     'use': 'ROAST DUCK / PORK BELLY / STIR-FRY'},
    {'name': 'SHICHIMI', 'region': 3, 'num': 13,
     'origin': 'JAPAN',
     'meaning': 'SEVEN FLAVOR CHILI',
     'components': 'CHILI + SANSHO PEPPER + ORANGE PEEL + SESAME + HEMP SEED + NORI + GINGER',
     'use': 'UDON / RAMEN / YAKITORI / RICE'},
    {'name': 'FURIKAKE', 'region': 3, 'num': 14,
     'origin': 'JAPAN',
     'meaning': 'SPRINKLE OVER',
     'components': 'NORI + SESAME + BONITO FLAKES + SALT + SUGAR',
     'use': 'RICE / ONIGIRI / POPCORN / EGGS'},

    # ── AMERICAS (region 4) ──────────────────────────────
    {'name': 'CHILI POWDER', 'region': 4, 'num': 15,
     'origin': 'TEXAS / MEXICO',
     'meaning': 'CHILE BLEND',
     'components': 'ANCHO CHILI + CUMIN + GARLIC + OREGANO + PAPRIKA + CAYENNE',
     'use': 'CHILI CON CARNE / TACOS / BEANS'},
    {'name': 'JERK SEASONING', 'region': 4, 'num': 16,
     'origin': 'JAMAICA',
     'meaning': 'JERKED MEAT',
     'components': 'ALLSPICE + SCOTCH BONNET + THYME + GARLIC + GINGER + NUTMEG + CINNAMON + BLACK PEPPER',
     'use': 'CHICKEN / PORK / FISH / SHRIMP'},
    {'name': 'ADOBO', 'region': 4, 'num': 17,
     'origin': 'LATIN AMERICA',
     'meaning': 'MARINADE',
     'components': 'GARLIC + OREGANO + BLACK PEPPER + TURMERIC + ONION + CUMIN + SALT',
     'use': 'RICE / BEANS / MEAT / EVERYTHING'},
    {'name': 'TAJIN', 'region': 4, 'num': 18,
     'origin': 'MEXICO',
     'meaning': 'CHILE-LIME SALT',
     'components': 'CHILI PEPPER + DEHYDRATED LIME + SALT',
     'use': 'FRUIT / CORN / MANGO / RIM DRINKS'},

    # ── EUROPE (region 5) ────────────────────────────────
    {'name': 'HERBES DE PROVENCE', 'region': 5, 'num': 19,
     'origin': 'FRANCE',
     'meaning': 'HERBS OF PROVENCE',
     'components': 'THYME + ROSEMARY + OREGANO + SAVORY + MARJORAM + LAVENDER',
     'use': 'GRILLED MEAT / RATATOUILLE / BREAD'},
    {'name': 'QUATRE EPICES', 'region': 5, 'num': 20,
     'origin': 'FRANCE',
     'meaning': 'FOUR SPICES',
     'components': 'WHITE PEPPER + NUTMEG + CLOVE + GINGER',
     'use': 'PATE / CHARCUTERIE / STEWS / TERRINES'},
]

# Build per-region index
_REGION_BLENDS = [[] for _ in range(len(REGIONS))]
for _i, _b in enumerate(BLENDS):
    _REGION_BLENDS[_b['region']].append(_i)


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


class Spices(Visual):
    name = "SPICES"
    description = "Spice blend recipes"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout Y positions
    NAME_Y = 1       # blend name
    SEP1_Y = 7       # separator after name
    ORIGIN_Y = 10    # country of origin (centered)
    SEP2_Y = 16      # separator
    COMP_Y = 19      # components / recipe (scrolling)
    SEP3_Y = 26      # separator
    MEAN_LBL_Y = 29  # meaning label
    MEAN_Y = 36      # meaning text (scrolling)
    SEP4_Y = 43      # separator
    USE_Y = 46        # use / dishes (scrolling)
    FOOT_SEP_Y = 57  # footer separator
    FOOT_Y = 59      # footer text

    def reset(self):
        self.time = 0.0
        self.idx = 0
        self._name_scroll_x = 0.0
        self._comp_scroll_x = 0.0
        self._mean_scroll_x = 0.0
        self._use_scroll_x = 0.0
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0
        self._switch_flash = 0.0

    def _current(self):
        return BLENDS[self.idx % len(BLENDS)]

    def _step(self, direction):
        self.idx = (self.idx + direction) % len(BLENDS)
        self._name_scroll_x = 0.0
        self._comp_scroll_x = 0.0
        self._mean_scroll_x = 0.0
        self._use_scroll_x = 0.0
        self._switch_flash = 0.15

    def _jump_region(self, direction):
        cur = self._current()['region']
        target = (cur + direction) % len(REGIONS)
        if _REGION_BLENDS[target]:
            self.idx = _REGION_BLENDS[target][0]
        self._name_scroll_x = 0.0
        self._comp_scroll_x = 0.0
        self._mean_scroll_x = 0.0
        self._use_scroll_x = 0.0
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
            self._comp_scroll_x = 0.0
            self._mean_scroll_x = 0.0
            self._use_scroll_x = 0.0
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

        b = self._current()
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, b['name'], 48, dt, 18)
        self._comp_scroll_x = self._advance_scroll(
            self._comp_scroll_x, b['components'], 60, dt, 16)
        self._mean_scroll_x = self._advance_scroll(
            self._mean_scroll_x, b['meaning'], 48, dt, 16)
        self._use_scroll_x = self._advance_scroll(
            self._use_scroll_x, b['use'], 60, dt, 16)

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

        b = self._current()
        region = b['region']
        region_color = REGION_COLORS[region]

        # ── Header: blend name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(b['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(region_color, 0.6))

        name_start_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_start_x, self.NAME_Y,
                                  b['name'], region_color,
                                  self._name_scroll_x, 63 - name_start_x)

        # ── Sep 1 ──
        self._draw_sep(d, self.SEP1_Y)

        # ── Origin (centered, dimmed) ──
        origin = b['origin']
        origin_color = _dim(region_color, 0.5)
        origin_px = len(origin) * 4
        origin_x = max(1, (64 - origin_px) // 2)
        d.draw_text_small(origin_x, self.ORIGIN_Y, origin, origin_color)

        # ── Sep 2 ──
        self._draw_sep(d, self.SEP2_Y)

        # ── Components / recipe (scrolling, bright) ──
        self._draw_scrolling_text(d, 2, self.COMP_Y,
                                  b['components'], PLUS_COLOR,
                                  self._comp_scroll_x, 60)

        # ── Sep 3 ──
        self._draw_sep(d, self.SEP3_Y)

        # ── Meaning label + text ──
        mean_label_color = _dim(region_color, 0.3)
        d.draw_text_small(1, self.MEAN_LBL_Y, 'MEANS', mean_label_color)
        self._draw_scrolling_text(d, 2, self.MEAN_Y,
                                  b['meaning'], _dim(region_color, 0.5),
                                  self._mean_scroll_x, 60)

        # ── Sep 4 ──
        self._draw_sep(d, self.SEP4_Y)

        # ── Use / dishes (scrolling) ──
        self._draw_scrolling_text(d, 2, self.USE_Y,
                                  b['use'], TEXT_DIM,
                                  self._use_scroll_x, 60)

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)

        pos_str = f'{self.idx + 1}/{len(BLENDS)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)

        # Region position right-aligned
        reg_name = REGIONS[region]
        reg_list = _REGION_BLENDS[region]
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

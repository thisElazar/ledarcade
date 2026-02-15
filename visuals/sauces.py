"""Sauces - Mother + Delta culinary sauce reference on 64x64 LED matrix.

Each sauce shows: where it comes from (parent) + what you add (delta) = this sauce.
Daughters show their mother, world sauces show their country of origin.
"""

from . import Visual

# ── Families ────────────────────────────────────────────────────────
FAMILIES = ["MOTHER", "BECHAMEL", "VELOUTE", "ESPAGNOLE", "HOLLANDAISE", "TOMATO", "WORLD"]
FAMILY_COLORS = [
    (220, 180, 50),    # MOTHER = gold
    (240, 230, 200),   # BECHAMEL = cream
    (200, 180, 100),   # VELOUTE = pale gold
    (140, 90, 50),     # ESPAGNOLE = brown
    (255, 210, 50),    # HOLLANDAISE = bright gold
    (220, 50, 40),     # TOMATO = red
    (60, 180, 80),     # WORLD = green
]

HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
PLUS_COLOR = (180, 180, 200)
SEP_COLOR = (50, 50, 70)

# ── Sauce data: parent + delta model ──────────────────────────────
SAUCES = [
    # ── MOTHERS (family 0) ─────────────────────────────────
    {'name': 'BECHAMEL', 'family': 0, 'num': 1,
     'parent': 'MOTHER SAUCE',
     'add': 'BUTTER + FLOUR (2 MIN) + MILK + NUTMEG',
     'serve': 'CREAM SAUCES  GRATINS  LASAGNA'},
    {'name': 'VELOUTE', 'family': 0, 'num': 2,
     'parent': 'MOTHER SAUCE',
     'add': 'BUTTER + FLOUR (5 MIN) + CHICKEN OR FISH STOCK',
     'serve': 'SUPREME  ALLEMANDE  BERCY'},
    {'name': 'ESPAGNOLE', 'family': 0, 'num': 3,
     'parent': 'MOTHER SAUCE',
     'add': 'BUTTER + FLOUR (8 MIN) + BROWN STOCK + TOMATO + ONION CARROT CELERY',
     'serve': 'DEMI-GLACE  BORDELAISE  CHASSEUR'},
    {'name': 'HOLLANDAISE', 'family': 0, 'num': 4,
     'parent': 'MOTHER SAUCE',
     'add': 'EGG YOLKS + MELTED BUTTER + LEMON  WHISK OVER STEAM',
     'serve': 'EGGS BENEDICT  ASPARAGUS  FISH'},
    {'name': 'TOMATO', 'family': 0, 'num': 5,
     'parent': 'MOTHER SAUCE',
     'add': 'TOMATOES + ONION + GARLIC + OLIVE OIL + BASIL',
     'serve': 'PASTA  PIZZA  BRAISES'},

    # ── BECHAMEL DAUGHTERS (family 1) ──────────────────────
    {'name': 'MORNAY', 'family': 1, 'num': 6,
     'parent': 'BECHAMEL',
     'add': '+ GRUYERE + PARMESAN',
     'serve': 'GRATINS  MAC & CHEESE  CROQUE MONSIEUR'},
    {'name': 'SOUBISE', 'family': 1, 'num': 7,
     'parent': 'BECHAMEL',
     'add': '+ PUREED ONION + BUTTER',
     'serve': 'EGGS  VEAL  ROAST CHICKEN'},
    {'name': 'NANTUA', 'family': 1, 'num': 8,
     'parent': 'BECHAMEL',
     'add': '+ CRAYFISH + BUTTER + CREAM',
     'serve': 'QUENELLES  FISH  SHELLFISH'},
    {'name': 'CREAM SAUCE', 'family': 1, 'num': 9,
     'parent': 'BECHAMEL',
     'add': '+ HEAVY CREAM',
     'serve': 'VEGETABLES  CHICKEN  PASTA'},

    # ── VELOUTE DAUGHTERS (family 2) ───────────────────────
    {'name': 'SUPREME', 'family': 2, 'num': 10,
     'parent': 'CHICKEN VELOUTE',
     'add': '+ CREAM + BUTTER + LEMON',
     'serve': 'POULTRY  RICE  VOL-AU-VENT'},
    {'name': 'ALLEMANDE', 'family': 2, 'num': 11,
     'parent': 'VEAL VELOUTE',
     'add': '+ EGG YOLK + LEMON + CREAM  THICKENS OFF HEAT',
     'serve': 'VEAL  VEGETABLES  POACHED EGGS'},
    {'name': 'BERCY', 'family': 2, 'num': 12,
     'parent': 'FISH VELOUTE',
     'add': '+ SHALLOTS + WHITE WINE + PARSLEY',
     'serve': 'POACHED FISH  SOLE  TURBOT'},
    {'name': 'NORMANDY', 'family': 2, 'num': 13,
     'parent': 'FISH VELOUTE',
     'add': '+ MUSHROOMS + WHITE WINE + CREAM',
     'serve': 'SOLE  SHELLFISH  BAKED FISH'},

    # ── ESPAGNOLE DAUGHTERS (family 3) ─────────────────────
    {'name': 'DEMI-GLACE', 'family': 3, 'num': 14,
     'parent': 'ESPAGNOLE',
     'add': '+ BROWN STOCK  SIMMER AND REDUCE BY HALF',
     'serve': 'BASE FOR ALL BROWN SAUCES'},
    {'name': 'BORDELAISE', 'family': 3, 'num': 15,
     'parent': 'DEMI-GLACE',
     'add': '+ RED WINE (BORDEAUX) + SHALLOTS + BONE MARROW',
     'serve': 'STEAK  BEEF TENDERLOIN  LAMB'},
    {'name': 'CHASSEUR', 'family': 3, 'num': 16,
     'parent': 'DEMI-GLACE',
     'add': '+ MUSHROOMS + WHITE WINE + TOMATO',
     'serve': 'CHICKEN  VEAL  RABBIT'},
    {'name': 'ROBERT', 'family': 3, 'num': 17,
     'parent': 'DEMI-GLACE',
     'add': '+ ONIONS + WHITE WINE + DIJON',
     'serve': 'PORK CHOPS  GRILLED MEAT'},
    {'name': 'MADEIRA', 'family': 3, 'num': 18,
     'parent': 'DEMI-GLACE',
     'add': '+ MADEIRA WINE',
     'serve': 'BEEF TENDERLOIN  HAM  MUSHROOMS'},

    # ── HOLLANDAISE DAUGHTERS (family 4) ───────────────────
    {'name': 'BEARNAISE', 'family': 4, 'num': 19,
     'parent': 'HOLLANDAISE',
     'add': '+ TARRAGON + SHALLOT + WHITE WINE VINEGAR  REDUCE FIRST',
     'serve': 'STEAK  GRILLED FISH  EGGS'},
    {'name': 'CHORON', 'family': 4, 'num': 20,
     'parent': 'BEARNAISE',
     'add': '+ TOMATO PUREE',
     'serve': 'FISH  EGGS  GRILLED MEAT'},
    {'name': 'MALTAISE', 'family': 4, 'num': 21,
     'parent': 'HOLLANDAISE',
     'add': '+ BLOOD ORANGE JUICE + ZEST',
     'serve': 'ASPARAGUS  STEAMED VEGETABLES'},
    {'name': 'MOUSSELINE', 'family': 4, 'num': 22,
     'parent': 'HOLLANDAISE',
     'add': '+ WHIPPED CREAM  GENTLY FOLD IN',
     'serve': 'ASPARAGUS  FISH  SOUFFLES'},

    # ── TOMATO DAUGHTERS (family 5) ────────────────────────
    {'name': 'MARINARA', 'family': 5, 'num': 23,
     'parent': 'TOMATO',
     'add': '+ GARLIC + OREGANO + BASIL',
     'serve': 'PASTA  PIZZA  DIPPING'},
    {'name': 'BOLOGNESE', 'family': 5, 'num': 24,
     'parent': 'TOMATO',
     'add': '+ GROUND MEAT + ONION CARROT CELERY + WINE + MILK  SLOW SIMMER',
     'serve': 'TAGLIATELLE  LASAGNA  PAPPARDELLE'},
    {'name': 'CREOLE', 'family': 5, 'num': 25,
     'parent': 'TOMATO',
     'add': '+ ONION + CELERY + BELL PEPPER + CAYENNE',
     'serve': 'SHRIMP  RICE  JAMBALAYA'},
    {'name': 'PUTTANESCA', 'family': 5, 'num': 26,
     'parent': 'TOMATO',
     'add': '+ CAPERS + OLIVES + ANCHOVIES + CHILI',
     'serve': 'SPAGHETTI  LINGUINE'},

    # ── WORLD SAUCES (family 6) ────────────────────────────
    {'name': 'CHIMICHURRI', 'family': 6, 'num': 27,
     'parent': 'ARGENTINA',
     'add': 'PARSLEY + GARLIC + OREGANO + VINEGAR + OIL',
     'serve': 'GRILLED STEAK  SAUSAGES'},
    {'name': 'PESTO', 'family': 6, 'num': 28,
     'parent': 'GENOA  ITALY',
     'add': 'BASIL + PINE NUTS + GARLIC + PARMESAN + OIL',
     'serve': 'PASTA  BRUSCHETTA  SANDWICHES'},
    {'name': 'TERIYAKI', 'family': 6, 'num': 29,
     'parent': 'JAPAN',
     'add': 'SOY + SAKE + MIRIN + SUGAR + GINGER',
     'serve': 'CHICKEN  SALMON  RICE BOWLS'},
    {'name': 'MOLE POBLANO', 'family': 6, 'num': 30,
     'parent': 'PUEBLA  MEXICO',
     'add': 'DRIED CHILES (ANCHO MULATO PASILLA) + CHOCOLATE + ALMONDS + SESAME + SPICES',
     'serve': 'TURKEY  ENCHILADAS  TAMALES'},
    {'name': 'TIKKA MASALA', 'family': 6, 'num': 31,
     'parent': 'INDIA / UK',
     'add': 'ONION + GINGER + GARLIC + CUMIN CORIANDER TURMERIC + TOMATO + CREAM',
     'serve': 'CHICKEN  NAAN  RICE'},
    {'name': 'NUOC CHAM', 'family': 6, 'num': 32,
     'parent': 'VIETNAM',
     'add': 'FISH SAUCE + LIME + SUGAR + GARLIC + CHILI',
     'serve': 'SPRING ROLLS  NOODLES  RICE'},
    {'name': 'PONZU', 'family': 6, 'num': 33,
     'parent': 'JAPAN',
     'add': 'SOY + CITRUS (YUZU) + MIRIN + DRIED FISH + KELP  STEEP OVERNIGHT',
     'serve': 'DIPPING  SASHIMI  TATAKI'},
    {'name': 'AGLIO E OLIO', 'family': 6, 'num': 34,
     'parent': 'NAPLES  ITALY',
     'add': 'OLIVE OIL + THIN-SLICED GARLIC + CHILI FLAKES + STARCHY PASTA WATER',
     'serve': 'SPAGHETTI  LINGUINE'},
    {'name': 'SALSA VERDE', 'family': 6, 'num': 35,
     'parent': 'MEXICO',
     'add': 'ROASTED TOMATILLOS + SERRANO PEPPER + ONION + CILANTRO + LIME',
     'serve': 'ENCHILADAS  TACOS  CHILAQUILES'},
    {'name': 'GREEN CHUTNEY', 'family': 6, 'num': 36,
     'parent': 'INDIA',
     'add': 'CILANTRO + MINT + GREEN CHILES + LEMON + CUMIN',
     'serve': 'SAMOSAS  CHAAT  KEBABS'},
    {'name': 'THAI PEANUT', 'family': 6, 'num': 37,
     'parent': 'THAILAND',
     'add': 'PEANUT BUTTER + SOY + LIME + CHILI + COCONUT',
     'serve': 'SATAY  NOODLES  SPRING ROLLS'},
    {'name': 'RAITA', 'family': 6, 'num': 38,
     'parent': 'INDIA',
     'add': 'YOGURT + CUCUMBER + TOASTED CUMIN + MINT',
     'serve': 'BIRYANI  CURRIES  KEBABS'},
]

# Build per-family index
_FAMILY_SAUCES = [[] for _ in range(len(FAMILIES))]
for _i, _s in enumerate(SAUCES):
    _FAMILY_SAUCES[_s['family']].append(_i)


def _dim(color, factor=0.4):
    """Return a dimmed version of a color."""
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


class Sauces(Visual):
    name = "SAUCES"
    description = "Culinary sauce reference"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12

    # Layout Y positions
    NAME_Y = 1       # sauce name
    SEP1_Y = 7       # separator after name
    PARENT_Y = 10    # parent/origin line
    ARROW_Y = 17     # small down-arrow
    ADD_Y = 20       # delta / what you add
    SEP2_Y = 27      # separator
    SERVE_LBL_Y = 30 # "SERVE" label
    SERVE_Y = 37     # serve text
    SEP3_Y = 44      # separator
    FAM_Y = 47       # family name (small, centered)
    FOOT_SEP_Y = 57  # footer separator
    FOOT_Y = 59      # footer text

    def reset(self):
        self.time = 0.0
        self.sauce_idx = 0
        self._name_scroll_x = 0.0
        self._add_scroll_x = 0.0
        self._serve_scroll_x = 0.0
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0
        self._switch_flash = 0.0  # brief flash on sauce change

    def _current(self):
        return SAUCES[self.sauce_idx % len(SAUCES)]

    def _step_sauce(self, direction):
        self.sauce_idx = (self.sauce_idx + direction) % len(SAUCES)
        self._name_scroll_x = 0.0
        self._add_scroll_x = 0.0
        self._serve_scroll_x = 0.0
        self._switch_flash = 0.15

    def _jump_family(self, direction):
        """Jump to next/prev family."""
        cur = self._current()['family']
        target = (cur + direction) % len(FAMILIES)
        if _FAMILY_SAUCES[target]:
            self.sauce_idx = _FAMILY_SAUCES[target][0]
        self._name_scroll_x = 0.0
        self._add_scroll_x = 0.0
        self._serve_scroll_x = 0.0
        self._switch_flash = 0.15

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: cycle through sauces one at a time (with auto-scroll on hold)
        if input_state.left_pressed:
            self._step_sauce(-1)
            self._scroll_dir = -1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True
        elif input_state.right_pressed:
            self._step_sauce(1)
            self._scroll_dir = 1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True

        if not input_state.left and not input_state.right:
            self._scroll_dir = 0

        # Up/Down: jump between families
        if input_state.up_pressed:
            self._jump_family(-1)
            consumed = True
        elif input_state.down_pressed:
            self._jump_family(1)
            consumed = True

        # Either action button: reset scrolling to start
        if input_state.action_l or input_state.action_r:
            self._name_scroll_x = 0.0
            self._add_scroll_x = 0.0
            self._serve_scroll_x = 0.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Auto-scroll when left/right held
        if self._scroll_dir != 0:
            self._scroll_hold += dt
            if self._scroll_hold >= self.SCROLL_DELAY:
                self._scroll_accum += dt
                while self._scroll_accum >= self.SCROLL_RATE:
                    self._scroll_accum -= self.SCROLL_RATE
                    self._step_sauce(self._scroll_dir)

        # Decay switch flash
        if self._switch_flash > 0:
            self._switch_flash = max(0.0, self._switch_flash - dt)

        sauce = self._current()

        # Scroll name if long
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, sauce['name'], 48, dt, 18)

        # Scroll add/delta line
        self._add_scroll_x = self._advance_scroll(
            self._add_scroll_x, sauce['add'], 60, dt, 16)

        # Scroll serve line
        self._serve_scroll_x = self._advance_scroll(
            self._serve_scroll_x, sauce['serve'], 60, dt, 16)

    SCROLL_LEAD_IN = 30  # px of empty space before text starts scrolling

    def _advance_scroll(self, scroll_x, text, avail_px, dt, speed):
        """Advance scroll position if text is wider than available pixels."""
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

        sauce = self._current()
        fam = sauce['family']
        fam_color = FAMILY_COLORS[fam]

        # ── Header: sauce name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(sauce['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(fam_color, 0.6))

        name_start_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_start_x, self.NAME_Y,
                                  sauce['name'], fam_color,
                                  self._name_scroll_x, 63 - name_start_x)

        # ── Sep 1 ──
        self._draw_sep(d, self.SEP1_Y)

        # ── Parent line (dimmed) ──
        parent = sauce['parent']
        parent_color = _dim(fam_color, 0.5)
        parent_px = len(parent) * 4
        if parent_px <= 62:
            x = (64 - parent_px) // 2
            d.draw_text_small(x, self.PARENT_Y, parent, parent_color)
        else:
            d.draw_text_small(1, self.PARENT_Y, parent, parent_color)

        # ── Down-arrow showing transformation ──
        arrow_color = _dim(fam_color, 0.35)
        d.set_pixel(30, self.ARROW_Y, arrow_color)
        d.set_pixel(31, self.ARROW_Y, arrow_color)
        d.set_pixel(32, self.ARROW_Y, arrow_color)
        d.set_pixel(31, self.ARROW_Y + 1, arrow_color)

        # ── Delta / what you add (bright) ──
        self._draw_scrolling_text(d, 2, self.ADD_Y,
                                  sauce['add'], PLUS_COLOR,
                                  self._add_scroll_x, 60)

        # ── Sep 2 ──
        self._draw_sep(d, self.SEP2_Y)

        # ── "SERVE" label + serve text ──
        serve_label_color = _dim(fam_color, 0.3)
        d.draw_text_small(1, self.SERVE_LBL_Y, 'SERVE', serve_label_color)
        self._draw_scrolling_text(d, 2, self.SERVE_Y,
                                  sauce['serve'], TEXT_DIM,
                                  self._serve_scroll_x, 60)

        # ── Sep 3 ──
        self._draw_sep(d, self.SEP3_Y)

        # ── Family name (small, centered, dimmed) ──
        fam_name = FAMILIES[fam]
        fam_name_px = len(fam_name) * 4
        fam_x = (64 - fam_name_px) // 2
        d.draw_text_small(fam_x, self.FAM_Y, fam_name, _dim(fam_color, 0.35))

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)

        pos_str = f'{self.sauce_idx + 1}/{len(SAUCES)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)

        # Family position right-aligned
        fam_list = _FAMILY_SAUCES[fam]
        fam_pos = fam_list.index(self.sauce_idx) + 1 if self.sauce_idx in fam_list else 1
        fam_str = f'{fam_pos}/{len(fam_list)}'
        fam_str_px = len(fam_str) * 4
        d.draw_text_small(63 - fam_str_px, self.FOOT_Y, fam_str, fam_color)

    def _draw_scrolling_text(self, d, start_x, y, text, color, scroll_x, avail_px):
        """Draw text that scrolls if wider than avail_px, otherwise centered."""
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
        """Draw a single column of a 3x5 character."""
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

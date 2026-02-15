"""Butcher Cuts - Pixel art butcher's cut charts on 64x64 LED matrix.

Four animals (Beef, Pork, Lamb, Chicken) with primal cut regions shown as
colored zones on pixel-art silhouettes.  Up/Down cycles animals, Left/Right
cycles primal cuts (highlighting the region), action button toggles between
primal name and retail cuts / cooking info.
"""

from . import Visual

# ── UI colors ──────────────────────────────────────────────────────
HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)
HIGHLIGHT_COLOR = (255, 255, 255)

# ── Animal accent colors ──────────────────────────────────────────
ANIMAL_COLORS = [
    (200, 60, 60),     # BEEF = red
    (220, 150, 80),    # PORK = amber
    (180, 200, 140),   # LAMB = sage green
    (240, 200, 80),    # CHICKEN = golden
]

# ── Silhouette building ──────────────────────────────────────────
# Each silhouette is defined as a list of (y, x_start, x_end) spans.
# Each cut region maps cut-index -> set of (x,y) pixel coordinates.
# Silhouettes are drawn offset from (ox, oy) at draw time.

def _spans_to_pixels(spans):
    """Convert [(y, x0, x1), ...] to set of (x,y)."""
    pix = set()
    for y, x0, x1 in spans:
        for x in range(x0, x1 + 1):
            pix.add((x, y))
    return pix

# ── BEEF silhouette (side profile, ~48x26, facing right) ─────────
# Constructed as row-spans: (row, x_start, x_end) relative to origin
_BEEF_SPANS = [
    # Head / face (rows 0-6)
    (0, 40, 44),
    (1, 38, 46),
    (2, 37, 47),
    (3, 36, 47),
    (4, 35, 47), (4, 0, 2),   # horn
    (5, 35, 47),
    (6, 36, 46),
    # Neck / chuck area (rows 7-9)
    (7, 30, 45),
    (8, 27, 44),
    (9, 24, 43),
    # Main body (rows 10-17)
    (10, 4, 42),
    (11, 3, 42),
    (12, 2, 42),
    (13, 2, 42),
    (14, 2, 42),
    (15, 2, 42),
    (16, 3, 42),
    (17, 4, 41),
    # Belly / underside (rows 18-20)
    (18, 5, 40),
    (19, 6, 39),
    (20, 7, 38),
    # Legs (rows 21-25)
    (21, 7, 12), (21, 33, 38),
    (22, 7, 11), (22, 34, 38),
    (23, 7, 11), (23, 34, 37),
    (24, 7, 10), (24, 35, 37),
    (25, 7, 10), (25, 35, 37),
]

# Beef cut regions (pixel coordinate sets, relative to silhouette origin)
def _beef_regions():
    # Define x-ranges for each primal at body rows
    regions = {}
    # Chuck: x 24-33, y 7-17
    r = set()
    for y in range(7, 18):
        for x in range(24, 34):
            r.add((x, y))
    # Add head/neck area
    for y in range(0, 7):
        for sp in _BEEF_SPANS:
            if sp[0] == y:
                for x in range(sp[1], sp[2] + 1):
                    r.add((x, y))
    regions['CHUCK'] = r

    # Rib: x 18-24, y 10-17
    r = set()
    for y in range(10, 18):
        for x in range(18, 24):
            r.add((x, y))
    regions['RIB'] = r

    # Short Loin: x 13-18, y 10-17
    r = set()
    for y in range(10, 18):
        for x in range(13, 18):
            r.add((x, y))
    regions['SHORT LOIN'] = r

    # Sirloin: x 8-13, y 10-17
    r = set()
    for y in range(10, 18):
        for x in range(8, 13):
            r.add((x, y))
    regions['SIRLOIN'] = r

    # Round: x 2-8, y 10-17 plus rear leg
    r = set()
    for y in range(10, 18):
        for x in range(2, 8):
            r.add((x, y))
    for y in range(18, 26):
        for x in range(7, 13):
            r.add((x, y))
    regions['ROUND'] = r

    # Brisket: x 30-42, y 18-20 plus front lower
    r = set()
    for y in range(17, 21):
        for x in range(30, 41):
            r.add((x, y))
    regions['BRISKET'] = r

    # Plate: x 18-30, y 18-20
    r = set()
    for y in range(18, 21):
        for x in range(18, 30):
            r.add((x, y))
    regions['PLATE'] = r

    # Flank: x 8-18, y 18-20
    r = set()
    for y in range(18, 21):
        for x in range(8, 18):
            r.add((x, y))
    regions['FLANK'] = r

    # Shank: front and rear legs
    r = set()
    for y in range(21, 26):
        for x in range(33, 39):
            r.add((x, y))
    for y in range(21, 26):
        for x in range(7, 13):
            # rear shank already in round, only add non-overlapping
            pass
    regions['SHANK'] = r

    # Also add body top row pixels to chuck
    for y in [7, 8, 9]:
        for sp in _BEEF_SPANS:
            if sp[0] == y:
                for x in range(sp[1], min(sp[2] + 1, 45)):
                    if x >= 34:
                        regions['CHUCK'].add((x, y))

    return regions

_BEEF_REGIONS = _beef_regions()

# ── PORK silhouette (side profile, ~46x22) ───────────────────────
_PORK_SPANS = [
    # Ears (rows 0-2)
    (0, 40, 42),
    (1, 39, 43),
    (2, 38, 44),
    # Head (rows 3-7)
    (3, 36, 46),
    (4, 35, 47),
    (5, 35, 47),
    (6, 36, 47),
    (7, 37, 46),
    # Neck + body (rows 8-16)
    (8, 4, 45),
    (9, 3, 44),
    (10, 2, 43),
    (11, 2, 42),
    (12, 2, 42),
    (13, 2, 42),
    (14, 3, 42),
    (15, 4, 41),
    (16, 5, 40),
    # Belly (rows 17-19)
    (17, 6, 39),
    (18, 7, 38),
    (19, 8, 37),
    # Legs (rows 20-24)
    (20, 8, 13), (20, 32, 37),
    (21, 8, 12), (21, 33, 37),
    (22, 8, 12), (22, 33, 36),
    (23, 9, 12), (23, 34, 36),
    (24, 9, 11), (24, 34, 36),
]

def _pork_regions():
    regions = {}
    # Shoulder/Butt: x 30-47, y 3-14 (front quarter including head)
    r = set()
    for y in range(0, 15):
        for sp in _PORK_SPANS:
            if sp[0] == y:
                for x in range(max(sp[1], 30), sp[2] + 1):
                    r.add((x, y))
    regions['SHOULDER'] = r

    # Loin: x 12-30, y 8-14 (top of body)
    r = set()
    for y in range(8, 15):
        for x in range(12, 30):
            r.add((x, y))
    regions['LOIN'] = r

    # Belly: x 12-30, y 15-19
    r = set()
    for y in range(15, 20):
        for x in range(8, 30):
            r.add((x, y))
    regions['BELLY'] = r

    # Leg/Ham: x 2-12, y 8-19 plus rear leg
    r = set()
    for y in range(8, 20):
        for x in range(2, 12):
            r.add((x, y))
    for y in range(20, 25):
        for x in range(8, 14):
            r.add((x, y))
    regions['LEG/HAM'] = r

    # Spare Ribs: x 20-30, y 15-19
    r = set()
    for y in range(15, 20):
        for x in range(30, 40):
            r.add((x, y))
    regions['SPARE RIBS'] = r

    # Hock: front and rear lower legs
    r = set()
    for y in range(20, 25):
        for x in range(32, 38):
            r.add((x, y))
    regions['HOCK'] = r

    return regions

_PORK_REGIONS = _pork_regions()

# ── LAMB silhouette (side profile, ~44x22) ───────────────────────
_LAMB_SPANS = [
    # Head (rows 0-6)
    (0, 40, 43),
    (1, 38, 44),
    (2, 37, 45),
    (3, 36, 45),
    (4, 36, 44),
    (5, 37, 44),
    (6, 38, 43),
    # Neck + body (rows 7-15)
    (7, 6, 42),
    (8, 4, 41),
    (9, 3, 40),
    (10, 2, 40),
    (11, 2, 40),
    (12, 2, 40),
    (13, 3, 40),
    (14, 4, 39),
    (15, 5, 38),
    # Underside (rows 16-18)
    (16, 6, 37),
    (17, 7, 36),
    (18, 8, 35),
    # Legs (rows 19-24)
    (19, 8, 12), (19, 30, 35),
    (20, 8, 11), (20, 31, 35),
    (21, 8, 11), (21, 31, 34),
    (22, 8, 10), (22, 32, 34),
    (23, 8, 10), (23, 32, 34),
    (24, 9, 10), (24, 33, 34),
]

def _lamb_regions():
    regions = {}
    # Shoulder: x 28-45, y 0-14
    r = set()
    for y in range(0, 15):
        for sp in _LAMB_SPANS:
            if sp[0] == y:
                for x in range(max(sp[1], 28), sp[2] + 1):
                    r.add((x, y))
    regions['SHOULDER'] = r

    # Rack: x 18-28, y 7-14
    r = set()
    for y in range(7, 15):
        for x in range(18, 28):
            r.add((x, y))
    regions['RACK'] = r

    # Loin: x 10-18, y 7-14
    r = set()
    for y in range(7, 15):
        for x in range(10, 18):
            r.add((x, y))
    regions['LOIN'] = r

    # Leg: x 2-10, y 7-18 plus rear leg
    r = set()
    for y in range(7, 19):
        for x in range(2, 10):
            r.add((x, y))
    for y in range(19, 25):
        for x in range(8, 13):
            r.add((x, y))
    regions['LEG'] = r

    # Breast: x 10-28, y 15-18
    r = set()
    for y in range(15, 19):
        for x in range(10, 36):
            r.add((x, y))
    regions['BREAST'] = r

    # Shank: front and rear lower legs
    r = set()
    for y in range(19, 25):
        for x in range(30, 36):
            r.add((x, y))
    regions['SHANK'] = r

    return regions

_LAMB_REGIONS = _lamb_regions()

# ── CHICKEN silhouette (front view, ~38x26) ──────────────────────
_CHICKEN_SPANS = [
    # Comb (rows 0-1)
    (0, 18, 20),
    (1, 17, 21),
    # Head (rows 2-4)
    (2, 16, 22),
    (3, 15, 23),
    (4, 16, 22),
    # Neck (rows 5-6)
    (5, 17, 21),
    (6, 16, 22),
    # Body / breast (rows 7-17)
    (7, 10, 28),
    (8, 8, 30),
    (9, 7, 31),
    (10, 6, 32),
    (11, 5, 33),
    (12, 5, 33),
    (13, 5, 33),
    (14, 6, 32),
    (15, 7, 31),
    (16, 8, 30),
    (17, 10, 28),
    # Wings (stick out from body at rows 10-15)
    (10, 2, 5), (10, 33, 36),
    (11, 1, 4), (11, 34, 37),
    (12, 0, 3), (12, 35, 38),
    (13, 0, 3), (13, 35, 38),
    (14, 1, 4), (14, 34, 37),
    (15, 2, 5), (15, 33, 36),
    # Lower body (rows 18-19)
    (18, 12, 26),
    (19, 14, 24),
    # Legs (rows 20-25)
    (20, 12, 16), (20, 22, 26),
    (21, 13, 15), (21, 23, 25),
    (22, 13, 15), (22, 23, 25),
    (23, 12, 16), (23, 22, 26),
    (24, 11, 13), (24, 25, 27), (24, 15, 16), (24, 22, 23),
    (25, 11, 13), (25, 25, 27),
]

def _chicken_regions():
    regions = {}
    # Breast: center body rows 7-17
    r = set()
    for y in range(7, 18):
        for x in range(10, 29):
            r.add((x, y))
    regions['BREAST'] = r

    # Thigh: rows 18-22 inner leg area
    r = set()
    for y in range(18, 23):
        for x in range(12, 27):
            r.add((x, y))
    regions['THIGH'] = r

    # Drumstick: lower legs rows 23-25
    r = set()
    for y in range(23, 26):
        for x in range(11, 17):
            r.add((x, y))
        for x in range(22, 28):
            r.add((x, y))
    regions['DRUMSTICK'] = r

    # Wing: outer wing portions
    r = set()
    for y in range(10, 16):
        for x in range(0, 6):
            r.add((x, y))
        for x in range(33, 39):
            r.add((x, y))
    regions['WING'] = r

    # Tenderloin: small strip inside breast area
    r = set()
    for y in range(9, 16):
        for x in range(17, 22):
            r.add((x, y))
    regions['TENDERLOIN'] = r

    # Back: upper body behind breast
    r = set()
    for y in range(7, 10):
        for x in range(10, 29):
            r.add((x, y))
    regions['BACK'] = r

    # Oyster: two small spots near the thigh/back junction
    r = set()
    for y in range(17, 19):
        for x in range(10, 14):
            r.add((x, y))
        for x in range(24, 28):
            r.add((x, y))
    regions['OYSTER'] = r

    return regions

_CHICKEN_REGIONS = _chicken_regions()

# ── Cut colors (distinct per region index) ────────────────────────
CUT_COLORS = [
    (200, 80, 80),     # 0 warm red
    (80, 160, 200),    # 1 sky blue
    (200, 180, 60),    # 2 gold
    (120, 200, 120),   # 3 green
    (200, 120, 200),   # 4 magenta
    (255, 140, 60),    # 5 orange
    (100, 200, 200),   # 6 teal
    (180, 140, 100),   # 7 tan
    (160, 100, 200),   # 8 purple
    (200, 200, 200),   # 9 light gray
]

# ── Animal data ───────────────────────────────────────────────────
ANIMALS = [
    {
        'name': 'BEEF',
        'color': ANIMAL_COLORS[0],
        'spans': _BEEF_SPANS,
        'regions': _BEEF_REGIONS,
        'silhouette_w': 48,
        'cuts': [
            {'name': 'CHUCK', 'retail': 'CHUCK ROAST / GROUND BEEF / FLAT IRON'},
            {'name': 'RIB', 'retail': 'RIBEYE / PRIME RIB / BACK RIBS'},
            {'name': 'SHORT LOIN', 'retail': 'T-BONE / PORTERHOUSE / NY STRIP'},
            {'name': 'SIRLOIN', 'retail': 'TOP SIRLOIN / TRI-TIP / SIRLOIN CAP'},
            {'name': 'ROUND', 'retail': 'RUMP ROAST / EYE OF ROUND / BOTTOM ROUND'},
            {'name': 'BRISKET', 'retail': 'WHOLE BRISKET / FLAT / POINT'},
            {'name': 'PLATE', 'retail': 'SHORT RIBS / SKIRT STEAK / HANGER'},
            {'name': 'FLANK', 'retail': 'FLANK STEAK / LONDON BROIL'},
            {'name': 'SHANK', 'retail': 'OSSO BUCO / SOUP BONES'},
        ],
    },
    {
        'name': 'PORK',
        'color': ANIMAL_COLORS[1],
        'spans': _PORK_SPANS,
        'regions': _PORK_REGIONS,
        'silhouette_w': 48,
        'cuts': [
            {'name': 'SHOULDER', 'retail': 'PULLED PORK / BOSTON BUTT / PICNIC'},
            {'name': 'LOIN', 'retail': 'PORK CHOP / TENDERLOIN / BABY BACK RIBS'},
            {'name': 'BELLY', 'retail': 'BACON / PANCETTA / PORK BELLY'},
            {'name': 'LEG/HAM', 'retail': 'HAM / PROSCIUTTO / GAMMON'},
            {'name': 'SPARE RIBS', 'retail': 'ST. LOUIS RIBS / RIB TIPS'},
            {'name': 'HOCK', 'retail': 'HAM HOCK / TROTTERS'},
        ],
    },
    {
        'name': 'LAMB',
        'color': ANIMAL_COLORS[2],
        'spans': _LAMB_SPANS,
        'regions': _LAMB_REGIONS,
        'silhouette_w': 46,
        'cuts': [
            {'name': 'SHOULDER', 'retail': 'SHOULDER ROAST / BLADE CHOP / STEW MEAT'},
            {'name': 'RACK', 'retail': 'RACK OF LAMB / LAMB CHOPS / CROWN ROAST'},
            {'name': 'LOIN', 'retail': 'LOIN CHOP / SADDLE / NOISETTE'},
            {'name': 'LEG', 'retail': 'LEG OF LAMB / BONELESS LEG / SHANK END'},
            {'name': 'BREAST', 'retail': 'BREAST / RIBLETS / DENVER RIBS'},
            {'name': 'SHANK', 'retail': 'BRAISED SHANK / OSSO BUCO'},
        ],
    },
    {
        'name': 'CHICKEN',
        'color': ANIMAL_COLORS[3],
        'spans': _CHICKEN_SPANS,
        'regions': _CHICKEN_REGIONS,
        'silhouette_w': 39,
        'cuts': [
            {'name': 'BREAST', 'retail': 'WHOLE BREAST / SPLIT BREAST / CUTLET'},
            {'name': 'THIGH', 'retail': 'BONE-IN THIGH / BONELESS THIGH'},
            {'name': 'DRUMSTICK', 'retail': 'DRUMSTICK / LEG QUARTER'},
            {'name': 'WING', 'retail': 'WHOLE WING / WINGETTE / DRUMETTE'},
            {'name': 'TENDERLOIN', 'retail': 'TENDERLOIN / TENDER / STRIP'},
            {'name': 'BACK', 'retail': 'BACK / STOCK BONES / CARCASS'},
            {'name': 'OYSTER', 'retail': 'OYSTER (HIDDEN GEM ON BACK)'},
        ],
    },
]


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def _blend(c1, c2, t):
    """Blend c1 toward c2 by factor t (0=c1, 1=c2)."""
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


class Butcher(Visual):
    name = "BUTCHER"
    description = "Butcher cut charts"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout Y positions
    NAME_Y = 1
    SEP1_Y = 7
    SILHOUETTE_TOP = 8
    SILHOUETTE_BOT = 39
    SEP2_Y = 40
    CUT_Y = 42
    SEP3_Y = 48
    RETAIL_Y = 50
    FOOT_SEP_Y = 57
    FOOT_Y = 59

    def reset(self):
        self.time = 0.0
        self.animal_idx = 0
        self.cut_idx = 0
        self._cut_scroll_x = 0.0
        self._retail_scroll_x = 0.0
        self._blink_timer = 0.0

    def _animal(self):
        return ANIMALS[self.animal_idx % len(ANIMALS)]

    def _cut(self):
        a = self._animal()
        return a['cuts'][self.cut_idx % len(a['cuts'])]

    def _reset_scrolls(self):
        self._cut_scroll_x = 0.0
        self._retail_scroll_x = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.animal_idx = (self.animal_idx - 1) % len(ANIMALS)
            self.cut_idx = 0
            self._reset_scrolls()
            consumed = True
        elif input_state.down_pressed:
            self.animal_idx = (self.animal_idx + 1) % len(ANIMALS)
            self.cut_idx = 0
            self._reset_scrolls()
            consumed = True

        if input_state.left_pressed:
            a = self._animal()
            self.cut_idx = (self.cut_idx - 1) % len(a['cuts'])
            self._reset_scrolls()
            consumed = True
        elif input_state.right_pressed:
            a = self._animal()
            self.cut_idx = (self.cut_idx + 1) % len(a['cuts'])
            self._reset_scrolls()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self._blink_timer += dt

        cut = self._cut()
        self._cut_scroll_x = self._advance_scroll(
            self._cut_scroll_x, cut['name'], 60, dt, 18)
        self._retail_scroll_x = self._advance_scroll(
            self._retail_scroll_x, cut['retail'], 60, dt, 16)

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

        animal = self._animal()
        cut = self._cut()
        accent = animal['color']

        # ── Header: animal name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        d.draw_text_small(2, self.NAME_Y, animal['name'], accent)

        # Animal position indicator (right-aligned)
        pos_str = f'{self.animal_idx + 1}/{len(ANIMALS)}'
        pos_px = len(pos_str) * 4
        d.draw_text_small(63 - pos_px, self.NAME_Y, pos_str, _dim(accent, 0.5))

        self._draw_sep(d, self.SEP1_Y)

        # ── Silhouette with cut regions ──
        self._draw_silhouette(d, animal, cut)

        self._draw_sep(d, self.SEP2_Y)

        # ── Cut name (scrolling) ──
        cut_color = CUT_COLORS[self.cut_idx % len(CUT_COLORS)]
        self._draw_scrolling_text(d, 2, self.CUT_Y,
                                  cut['name'], cut_color,
                                  self._cut_scroll_x, 60)

        self._draw_sep(d, self.SEP3_Y)

        # ── Retail cuts ──
        self._draw_scrolling_text(d, 2, self.RETAIL_Y,
                                  cut['retail'], TEXT_DIM,
                                  self._retail_scroll_x, 60)

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)
        cut_pos = f'{self.cut_idx + 1}/{len(animal["cuts"])}'
        d.draw_text_small(1, self.FOOT_Y, cut_pos, TEXT_DIM)

        # Right side: animal name dim
        aname = animal['name']
        aname_px = len(aname) * 4
        d.draw_text_small(63 - aname_px, self.FOOT_Y, aname, _dim(accent, 0.35))

    def _draw_silhouette(self, d, animal, cut):
        """Draw the animal silhouette with colored cut regions."""
        spans = animal['spans']
        regions = animal['regions']
        cuts = animal['cuts']
        current_cut_name = cut['name']

        # Build full pixel set from spans
        all_pixels = _spans_to_pixels(spans)

        # Compute bounding box for centering
        if all_pixels:
            min_x = min(p[0] for p in all_pixels)
            max_x = max(p[0] for p in all_pixels)
            min_y = min(p[1] for p in all_pixels)
            max_y = max(p[1] for p in all_pixels)
        else:
            return

        sil_w = max_x - min_x + 1
        sil_h = max_y - min_y + 1
        area_h = self.SILHOUETTE_BOT - self.SILHOUETTE_TOP + 1
        ox = (64 - sil_w) // 2 - min_x
        oy = self.SILHOUETTE_TOP + (area_h - sil_h) // 2 - min_y

        # Determine blink state for selected cut
        blink_on = (int(self._blink_timer * 4) % 2) == 0

        # Build a mapping: for each pixel, which cut does it belong to?
        # (first match wins for overlapping regions)
        pixel_cut_map = {}
        for ci, c in enumerate(cuts):
            cname = c['name']
            if cname in regions:
                for px in regions[cname]:
                    if px not in pixel_cut_map:
                        pixel_cut_map[px] = ci

        # Base silhouette color (dim)
        base_color = _dim(animal['color'], 0.2)

        for (px, py) in all_pixels:
            sx = px + ox
            sy = py + oy
            if sx < 0 or sx >= 64 or sy < self.SILHOUETTE_TOP or sy > self.SILHOUETTE_BOT:
                continue

            if (px, py) in pixel_cut_map:
                ci = pixel_cut_map[(px, py)]
                cut_color = CUT_COLORS[ci % len(CUT_COLORS)]
                cname = cuts[ci]['name']

                if cname == current_cut_name:
                    # Selected cut: bright or blink to highlight
                    if blink_on:
                        color = cut_color
                    else:
                        color = _dim(cut_color, 0.6)
                else:
                    # Other cuts: dimmed version of their color
                    color = _dim(cut_color, 0.3)
            else:
                color = base_color

            d.set_pixel(sx, sy, color)

    # ── Text helpers ──────────────────────────────────────────────

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

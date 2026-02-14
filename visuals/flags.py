"""
FLAGS OF THE WORLD - National Flag Display
============================================
120+ country flags rendered at 48x32, grouped by continent.
Pattern rendering system with shared methods for common layouts.
"""

import math
import random
from . import Visual, Display, Colors

# Flag canvas: 48x32 at offset (8, 10)
FW, FH = 48, 32
FX, FY = 8, 10

# ---------------------------------------------------------------------------
# Pattern types
# ---------------------------------------------------------------------------
HSTRIPES = 'h'  # horizontal stripes
VSTRIPES = 'v'  # vertical stripes
CROSS = '+'
NORDIC = 'n'
DISC = 'o'
TRIANGLE = 't'
CUSTOM = 'c'

# ---------------------------------------------------------------------------
# Flag data: (name, continent, pattern, params)
# For hstripes/vstripes: params = list of colors
# For cross: params = (bg, cross_color, width)
# For nordic: params = (bg, cross_color, [outline_color])
# For disc: params = (bg, disc_color, radius)
# For triangle: params = (bg, tri_color)
# For custom: params = draw function name
# ---------------------------------------------------------------------------

# Color shortcuts
W = (255, 255, 255)
BK = (0, 0, 0)
R = (220, 30, 30)
B = (0, 50, 160)
G = (0, 140, 60)
Y = (255, 210, 0)
O = (255, 140, 0)
LB = (0, 120, 200)
DB = (0, 30, 100)
DG = (0, 100, 40)
DR = (180, 20, 20)
SKY = (80, 160, 220)
MAR = (128, 0, 0)
NAV = (0, 0, 80)

FLAGS = [
    # ===== AFRICA =====
    ('ALGERIA',       'AFRICA', CUSTOM, '_algeria'),
    ('CAMEROON',      'AFRICA', VSTRIPES, [G, R, Y]),
    ('CHAD',          'AFRICA', VSTRIPES, [B, Y, R]),
    ('EGYPT',         'AFRICA', HSTRIPES, [R, W, BK]),
    ('ETHIOPIA',      'AFRICA', HSTRIPES, [G, Y, R]),
    ('GHANA',         'AFRICA', HSTRIPES, [R, Y, G]),
    ('IVORY COAST',   'AFRICA', VSTRIPES, [O, W, G]),
    ('KENYA',         'AFRICA', CUSTOM, '_kenya'),
    ('LIBYA',         'AFRICA', HSTRIPES, [R, BK, G]),
    ('MADAGASCAR',    'AFRICA', CUSTOM, '_madagascar'),
    ('MALI',          'AFRICA', VSTRIPES, [G, Y, R]),
    ('MOROCCO',       'AFRICA', CUSTOM, '_morocco'),
    ('MOZAMBIQUE',    'AFRICA', CUSTOM, '_mozambique'),
    ('NIGER',         'AFRICA', HSTRIPES, [O, W, G]),
    ('NIGERIA',       'AFRICA', VSTRIPES, [G, W, G]),
    ('SENEGAL',       'AFRICA', VSTRIPES, [G, Y, R]),
    ('SOUTH AFRICA',  'AFRICA', CUSTOM, '_safrica'),
    ('TANZANIA',      'AFRICA', CUSTOM, '_tanzania'),
    ('TUNISIA',       'AFRICA', CUSTOM, '_tunisia'),
    ('UGANDA',        'AFRICA', HSTRIPES, [BK, Y, R, BK, Y, R]),

    # ===== AMERICAS =====
    ('ARGENTINA',     'AMERICAS', HSTRIPES, [LB, W, LB]),
    ('BAHAMAS',       'AMERICAS', CUSTOM, '_bahamas'),
    ('BOLIVIA',       'AMERICAS', HSTRIPES, [R, Y, G]),
    ('BRAZIL',        'AMERICAS', CUSTOM, '_brazil'),
    ('CANADA',        'AMERICAS', CUSTOM, '_canada'),
    ('CHILE',         'AMERICAS', CUSTOM, '_chile'),
    ('COLOMBIA',      'AMERICAS', CUSTOM, '_colombia'),
    ('COSTA RICA',    'AMERICAS', CUSTOM, '_costarica'),
    ('CUBA',          'AMERICAS', CUSTOM, '_cuba'),
    ('DOM. REPUBLIC', 'AMERICAS', CUSTOM, '_dominican'),
    ('ECUADOR',       'AMERICAS', CUSTOM, '_colombia'),
    ('EL SALVADOR',   'AMERICAS', HSTRIPES, [B, W, B]),
    ('GUATEMALA',     'AMERICAS', VSTRIPES, [LB, W, LB]),
    ('HAITI',         'AMERICAS', HSTRIPES, [B, R]),
    ('HONDURAS',      'AMERICAS', HSTRIPES, [B, W, B]),
    ('JAMAICA',       'AMERICAS', CUSTOM, '_jamaica'),
    ('MEXICO',        'AMERICAS', CUSTOM, '_mexico'),
    ('NICARAGUA',     'AMERICAS', HSTRIPES, [B, W, B]),
    ('PANAMA',        'AMERICAS', CUSTOM, '_panama'),
    ('PARAGUAY',      'AMERICAS', HSTRIPES, [R, W, B]),
    ('PERU',          'AMERICAS', VSTRIPES, [R, W, R]),
    ('TRINIDAD',      'AMERICAS', CUSTOM, '_trinidad'),
    ('URUGUAY',       'AMERICAS', HSTRIPES, [W, B, W, B, W, B, W, B, W]),
    ('USA',           'AMERICAS', CUSTOM, '_usa'),
    ('VENEZUELA',     'AMERICAS', HSTRIPES, [Y, B, R]),

    # ===== ASIA =====
    ('BANGLADESH',    'ASIA', DISC, (DG, R, 9)),
    ('CAMBODIA',      'ASIA', HSTRIPES, [B, R, B]),
    ('CHINA',         'ASIA', CUSTOM, '_china'),
    ('INDIA',         'ASIA', CUSTOM, '_india'),
    ('INDONESIA',     'ASIA', HSTRIPES, [R, W]),
    ('IRAN',          'ASIA', HSTRIPES, [G, W, R]),
    ('IRAQ',          'ASIA', HSTRIPES, [R, W, BK]),
    ('ISRAEL',        'ASIA', CUSTOM, '_israel'),
    ('JAPAN',         'ASIA', DISC, (W, R, 8)),
    ('JORDAN',        'ASIA', CUSTOM, '_jordan'),
    ('KUWAIT',        'ASIA', CUSTOM, '_kuwait'),
    ('LAOS',          'ASIA', CUSTOM, '_laos'),
    ('LEBANON',       'ASIA', CUSTOM, '_lebanon'),
    ('MALAYSIA',      'ASIA', CUSTOM, '_malaysia'),
    ('MONGOLIA',      'ASIA', VSTRIPES, [R, B, R]),
    ('MYANMAR',       'ASIA', HSTRIPES, [Y, G, R]),
    ('NEPAL',         'ASIA', CUSTOM, '_nepal'),
    ('NORTH KOREA',   'ASIA', CUSTOM, '_nkorea'),
    ('PAKISTAN',       'ASIA', CUSTOM, '_pakistan'),
    ('PALESTINE',     'ASIA', CUSTOM, '_palestine'),
    ('PHILIPPINES',   'ASIA', CUSTOM, '_philippines'),
    ('QATAR',         'ASIA', CUSTOM, '_qatar'),
    ('SAUDI ARABIA',  'ASIA', CUSTOM, '_saudi'),
    ('SINGAPORE',     'ASIA', HSTRIPES, [R, W]),
    ('SOUTH KOREA',   'ASIA', CUSTOM, '_skorea'),
    ('SRI LANKA',     'ASIA', CUSTOM, '_srilanka'),
    ('THAILAND',      'ASIA', HSTRIPES, [R, W, B, B, W, R]),
    ('TURKEY',        'ASIA', CUSTOM, '_turkey'),
    ('UAE',           'ASIA', CUSTOM, '_uae'),
    ('UZBEKISTAN',    'ASIA', HSTRIPES, [B, W, G]),
    ('VIETNAM',       'ASIA', CUSTOM, '_vietnam'),

    # ===== EUROPE =====
    ('ALBANIA',       'EUROPE', CUSTOM, '_albania'),
    ('AUSTRIA',       'EUROPE', HSTRIPES, [R, W, R]),
    ('BELGIUM',       'EUROPE', VSTRIPES, [BK, Y, R]),
    ('BULGARIA',      'EUROPE', HSTRIPES, [W, G, R]),
    ('CROATIA',       'EUROPE', HSTRIPES, [R, W, B]),
    ('CZECH REPUBLIC','EUROPE', TRIANGLE, [(W, R), B]),
    ('DENMARK',       'EUROPE', NORDIC, [R, W]),
    ('ESTONIA',       'EUROPE', HSTRIPES, [B, BK, W]),
    ('FINLAND',       'EUROPE', NORDIC, [W, B]),
    ('FRANCE',        'EUROPE', VSTRIPES, [B, W, R]),
    ('GERMANY',       'EUROPE', HSTRIPES, [BK, R, Y]),
    ('GREECE',        'EUROPE', CUSTOM, '_greece'),
    ('HUNGARY',       'EUROPE', HSTRIPES, [R, W, G]),
    ('ICELAND',       'EUROPE', NORDIC, [B, R, W]),
    ('IRELAND',       'EUROPE', VSTRIPES, [G, W, O]),
    ('ITALY',         'EUROPE', VSTRIPES, [G, W, R]),
    ('LATVIA',        'EUROPE', HSTRIPES, [MAR, W, MAR]),
    ('LITHUANIA',     'EUROPE', HSTRIPES, [Y, G, R]),
    ('LUXEMBOURG',    'EUROPE', HSTRIPES, [R, W, LB]),
    ('MALTA',         'EUROPE', VSTRIPES, [W, R]),
    ('MONACO',        'EUROPE', HSTRIPES, [R, W]),
    ('NETHERLANDS',   'EUROPE', HSTRIPES, [R, W, B]),
    ('NORWAY',        'EUROPE', NORDIC, [R, (0, 32, 91), W]),
    ('POLAND',        'EUROPE', HSTRIPES, [W, R]),
    ('PORTUGAL',      'EUROPE', CUSTOM, '_portugal'),
    ('ROMANIA',       'EUROPE', VSTRIPES, [B, Y, R]),
    ('RUSSIA',        'EUROPE', HSTRIPES, [W, B, R]),
    ('SERBIA',        'EUROPE', HSTRIPES, [R, B, W]),
    ('SLOVAKIA',      'EUROPE', HSTRIPES, [W, B, R]),
    ('SLOVENIA',      'EUROPE', HSTRIPES, [W, B, R]),
    ('SPAIN',         'EUROPE', CUSTOM, '_spain'),
    ('SWEDEN',        'EUROPE', NORDIC, [(0, 100, 170), Y]),
    ('SWITZERLAND',   'EUROPE', CUSTOM, '_swiss'),
    ('UK',            'EUROPE', CUSTOM, '_uk'),
    ('UKRAINE',       'EUROPE', HSTRIPES, [B, Y]),

    # ===== OCEANIA =====
    ('AUSTRALIA',     'OCEANIA', CUSTOM, '_australia'),
    ('FIJI',          'OCEANIA', CUSTOM, '_fiji'),
    ('MARSHALL IS.',  'OCEANIA', CUSTOM, '_marshall'),
    ('MICRONESIA',    'OCEANIA', CUSTOM, '_micronesia'),
    ('NAURU',         'OCEANIA', CUSTOM, '_nauru'),
    ('NEW ZEALAND',   'OCEANIA', CUSTOM, '_nzealand'),
    ('PALAU',         'OCEANIA', DISC, (LB, Y, 8)),
    ('PAPUA N.G.',    'OCEANIA', CUSTOM, '_png'),
    ('SAMOA',         'OCEANIA', CUSTOM, '_samoa'),
    ('SOLOMON IS.',   'OCEANIA', CUSTOM, '_solomon'),
    ('TONGA',         'OCEANIA', CUSTOM, '_tonga'),
    ('VANUATU',       'OCEANIA', CUSTOM, '_vanuatu'),
]

# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------
GROUPS = [
    ('ALL',      'ALL COUNTRIES'),
    ('AFRICA',   'AFRICA'),
    ('AMERICAS', 'AMERICAS'),
    ('ASIA',     'ASIA'),
    ('EUROPE',   'EUROPE'),
    ('OCEANIA',  'OCEANIA'),
]


def _build_group_indices():
    all_sorted = sorted(range(len(FLAGS)), key=lambda i: FLAGS[i][0])
    indices = {'ALL': all_sorted}
    for key in ['AFRICA', 'AMERICAS', 'ASIA', 'EUROPE', 'OCEANIA']:
        indices[key] = [i for i, f in enumerate(FLAGS) if f[1] == key]
    return indices


class Flags(Visual):
    name = "FLAGS"
    description = "Flags of the world"
    category = "household"

    def reset(self):
        self.time = 0.0
        self.group_indices = _build_group_indices()
        self.group_idx = 0
        self.flag_pos = 0
        self.auto_cycle = True
        self.cycle_timer = 0.0
        self.cycle_duration = 5.0
        self.overlay_timer = 0.0
        self.scroll_offset = 0.0

    def _current_list(self):
        key = GROUPS[self.group_idx][0]
        return self.group_indices.get(key, [])

    def _current_flag(self):
        lst = self._current_list()
        if not lst:
            return FLAGS[0]
        return FLAGS[lst[self.flag_pos % len(lst)]]

    def handle_input(self, input_state):
        consumed = False
        if input_state.up_pressed:
            self.group_idx = (self.group_idx - 1) % len(GROUPS)
            self.flag_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            self.group_idx = (self.group_idx + 1) % len(GROUPS)
            self.flag_pos = 0
            self.cycle_timer = 0.0
            self.overlay_timer = 2.5
            consumed = True
        if input_state.left_pressed:
            lst = self._current_list()
            if lst:
                self.flag_pos = (self.flag_pos - 1) % len(lst)
            self.cycle_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.right_pressed:
            lst = self._current_list()
            if lst:
                self.flag_pos = (self.flag_pos + 1) % len(lst)
            self.cycle_timer = 0.0
            self.scroll_offset = 0.0
            consumed = True
        if input_state.action_l or input_state.action_r:
            self.auto_cycle = not self.auto_cycle
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.scroll_offset += dt * 20
        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        if self.auto_cycle:
            self.cycle_timer += dt
            if self.cycle_timer >= self.cycle_duration:
                self.cycle_timer = 0.0
                lst = self._current_list()
                if lst:
                    self.flag_pos = (self.flag_pos + 1) % len(lst)
                self.scroll_offset = 0.0

    def draw(self):
        d = self.display
        d.clear()

        flag = self._current_flag()
        name, continent, pattern, params = flag

        # Draw flag
        if pattern == HSTRIPES:
            self._draw_hstripes(d, params)
        elif pattern == VSTRIPES:
            self._draw_vstripes(d, params)
        elif pattern == NORDIC:
            self._draw_nordic(d, params)
        elif pattern == DISC:
            self._draw_disc(d, params)
        elif pattern == TRIANGLE:
            self._draw_triangle(d, params)
        elif pattern == CUSTOM:
            fn = getattr(self, params, None)
            if fn:
                fn(d)
            else:
                self._draw_hstripes(d, [W, W, W])

        # Flag border
        d.draw_rect(FX - 1, FY - 1, FW + 2, FH + 2, (40, 40, 40), filled=False)

        # Country name at bottom
        label = name
        max_chars = 14
        if len(label) > max_chars:
            padded = label + "    " + label
            total_w = len(label + "    ") * 4
            offset = int(self.scroll_offset) % total_w
            d.draw_text_small(2 - offset, 46, padded, Colors.WHITE)
        else:
            d.draw_text_small(2, 46, label, Colors.WHITE)

        # Group overlay
        if self.overlay_timer > 0:
            _, gname = GROUPS[self.group_idx]
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(200 * alpha), int(200 * alpha), int(200 * alpha))
            d.draw_text_small(2, 2, gname, c)

    # -----------------------------------------------------------------------
    # Pattern renderers
    # -----------------------------------------------------------------------

    def _draw_hstripes(self, d, colors):
        n = len(colors)
        for i, c in enumerate(colors):
            y0 = FY + i * FH // n
            y1 = FY + (i + 1) * FH // n
            for y in range(y0, y1):
                for x in range(FX, FX + FW):
                    d.set_pixel(x, y, c)

    def _draw_vstripes(self, d, colors):
        n = len(colors)
        for i, c in enumerate(colors):
            x0 = FX + i * FW // n
            x1 = FX + (i + 1) * FW // n
            for y in range(FY, FY + FH):
                for x in range(x0, x1):
                    d.set_pixel(x, y, c)

    def _draw_nordic(self, d, params):
        bg = params[0]
        cross_c = params[1]
        outline_c = params[2] if len(params) > 2 else None
        # Fill background
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, bg)
        # Cross position: offset left
        cx = FX + FW // 3
        cy = FY + FH // 2
        cw = 3  # cross arm width
        # Outline first if present
        if outline_c:
            for y in range(FY, FY + FH):
                for x in range(cx - cw, cx + cw + 1):
                    d.set_pixel(x, y, outline_c)
            for x in range(FX, FX + FW):
                for y in range(cy - cw, cy + cw + 1):
                    d.set_pixel(x, y, outline_c)
        # Cross
        hw = 1 if outline_c else cw
        for y in range(FY, FY + FH):
            for x in range(cx - hw, cx + hw + 1):
                d.set_pixel(x, y, cross_c)
        for x in range(FX, FX + FW):
            for y in range(cy - hw, cy + hw + 1):
                d.set_pixel(x, y, cross_c)

    def _draw_disc(self, d, params):
        bg, disc_c, radius = params
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, bg)
        cx = FX + FW // 2
        cy = FY + FH // 2
        d.draw_circle(cx, cy, radius, disc_c, filled=True)

    def _draw_triangle(self, d, params):
        stripe_colors, tri_c = params
        # Two horizontal stripes
        half = FH // 2
        for y in range(FY, FY + half):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, stripe_colors[0])
        for y in range(FY + half, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, stripe_colors[1])
        # Left triangle
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * FW / FH * 0.8)
            for x in range(min(w, FW)):
                d.set_pixel(FX + x, FY + y, tri_c)

    # -----------------------------------------------------------------------
    # Helpers
    # -----------------------------------------------------------------------

    def _star(self, d, x, y, c, size=3):
        """Draw a small star cross: size 3 = 5px cross, size 5 = bigger."""
        d.set_pixel(x, y, c)
        for i in range(1, size // 2 + 1):
            d.set_pixel(x - i, y, c)
            d.set_pixel(x + i, y, c)
            d.set_pixel(x, y - i, c)
            d.set_pixel(x, y + i, c)

    # -----------------------------------------------------------------------
    # Custom flag drawing methods
    # -----------------------------------------------------------------------

    def _usa(self, d):
        # 13 stripes
        for i in range(13):
            c = R if i % 2 == 0 else W
            y0 = FY + i * FH // 13
            y1 = FY + (i + 1) * FH // 13
            for y in range(y0, y1):
                for x in range(FX, FX + FW):
                    d.set_pixel(x, y, c)
        # Blue canton
        cw, ch = 21, 20
        for y in range(FY, FY + ch):
            for x in range(FX, FX + cw):
                d.set_pixel(x, y, NAV)
        # 50 stars: 5 rows of 6 + 4 rows of 5 (staggered)
        for row in range(9):
            sy = FY + 2 + row * 2
            if row % 2 == 0:  # 6-star rows
                for col in range(6):
                    d.set_pixel(FX + 2 + col * 3, sy, W)
            else:  # 5-star rows (offset)
                for col in range(5):
                    d.set_pixel(FX + 4 + col * 3, sy, W)

    def _uk(self, d):
        # Blue background
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, (0, 36, 125))
        # White diagonals (St Andrew + St Patrick base)
        for i in range(-FH, FW + FH):
            x1 = FX + i
            y1 = FY + int(i * FH / FW)
            x2 = FX + FW - 1 - i
            for dx in range(-1, 2):
                if 0 <= x1 + dx - FX < FW and 0 <= y1 - FY < FH:
                    d.set_pixel(x1 + dx, y1, W)
                if 0 <= x2 + dx - FX < FW and 0 <= y1 - FY < FH:
                    d.set_pixel(x2 + dx, y1, W)
        # Red diagonals (narrower)
        for i in range(-FH, FW + FH):
            x1 = FX + i
            y1 = FY + int(i * FH / FW)
            x2 = FX + FW - 1 - i
            if 0 <= x1 - FX < FW and 0 <= y1 - FY < FH:
                d.set_pixel(x1, y1, R)
            if 0 <= x2 - FX < FW and 0 <= y1 - FY < FH:
                d.set_pixel(x2, y1, R)
        # White cross
        cx = FX + FW // 2
        cy = FY + FH // 2
        for y in range(FY, FY + FH):
            for dx in range(-2, 3):
                d.set_pixel(cx + dx, y, W)
        for x in range(FX, FX + FW):
            for dy in range(-2, 3):
                d.set_pixel(x, cy + dy, W)
        # Red cross
        for y in range(FY, FY + FH):
            for dx in range(-1, 2):
                d.set_pixel(cx + dx, y, R)
        for x in range(FX, FX + FW):
            for dy in range(-1, 2):
                d.set_pixel(x, cy + dy, R)

    def _spain(self, d):
        # Red-yellow-red (1:2:1)
        q = FH // 4
        for y in range(FY, FY + q):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        for y in range(FY + q, FY + 3 * q):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, Y)
        for y in range(FY + 3 * q, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)

    def _swiss(self, d):
        # Red background with white cross
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        cx, cy = FX + FW // 2, FY + FH // 2
        # Vertical bar
        for y in range(cy - 8, cy + 9):
            for x in range(cx - 2, cx + 3):
                d.set_pixel(x, y, W)
        # Horizontal bar
        for x in range(cx - 8, cx + 9):
            for y in range(cy - 2, cy + 3):
                d.set_pixel(x, y, W)

    def _greece(self, d):
        # 9 stripes blue/white
        for i in range(9):
            c = B if i % 2 == 0 else W
            y0 = FY + i * FH // 9
            y1 = FY + (i + 1) * FH // 9
            for y in range(y0, y1):
                for x in range(FX, FX + FW):
                    d.set_pixel(x, y, c)
        # Blue canton with white cross
        cw, ch = 18, 18
        for y in range(FY, FY + ch):
            for x in range(FX, FX + cw):
                d.set_pixel(x, y, B)
        ccx = FX + cw // 2
        ccy = FY + ch // 2
        for y in range(FY, FY + ch):
            d.set_pixel(ccx, y, W)
        for x in range(FX, FX + cw):
            d.set_pixel(x, ccy, W)

    def _portugal(self, d):
        # Green left, red right (2:3)
        split = FX + FW * 2 // 5
        for y in range(FY, FY + FH):
            for x in range(FX, split):
                d.set_pixel(x, y, G)
            for x in range(split, FX + FW):
                d.set_pixel(x, y, R)
        # Yellow circle at split
        d.draw_circle(split, FY + FH // 2, 5, Y, filled=True)

    def _canada(self, d):
        # Red-white-red vertical bands (1:2:1)
        q = FW // 4
        for y in range(FY, FY + FH):
            for x in range(FX, FX + q):
                d.set_pixel(x, y, R)
            for x in range(FX + q, FX + 3 * q):
                d.set_pixel(x, y, W)
            for x in range(FX + 3 * q, FX + FW):
                d.set_pixel(x, y, R)
        # Maple leaf with pointed lobes
        cx, cy = FX + FW // 2, FY + FH // 2
        leaf = [
            #        top point
                     (0, -8),
            (-1, -7), (0, -7), (1, -7),
            #        upper side lobes
            (-4, -5), (-3, -5), (-2, -5), (-1, -5), (0, -5), (1, -5), (2, -5), (3, -5), (4, -5),
                      (-3, -4),(-2, -4), (-1, -4), (0, -4), (1, -4), (2, -4), (3, -4),
            (-6, -3), (-5, -3),(-2, -3), (-1, -3), (0, -3), (1, -3), (2, -3), (5, -3), (6, -3),
                               (-1, -2), (0, -2), (1, -2),
            #        lower side lobes
            (-7, -1), (-6, -1), (-5, -1), (-4, -1), (-3, -1), (-2, -1), (-1, -1),
            (0, -1),
            (1, -1), (2, -1), (3, -1), (4, -1), (5, -1), (6, -1), (7, -1),
                      (-5, 0), (-4, 0), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0), (4, 0), (5, 0),
                               (-3, 1), (-2, 1), (-1, 1), (0, 1), (1, 1), (2, 1), (3, 1),
                               (-3, 2), (-2, 2), (-1, 2), (0, 2), (1, 2), (2, 2), (3, 2),
            #        base notches
            (-4, 3), (-3, 3),          (-1, 3), (0, 3), (1, 3),          (3, 3), (4, 3),
            (-5, 4), (-4, 4),                   (0, 4),                  (4, 4), (5, 4),
            #        stem
                                                 (0, 5),
                                        (-1, 6), (0, 6), (1, 6),
        ]
        for dx, dy in leaf:
            d.set_pixel(cx + dx, cy + dy, R)

    def _brazil(self, d):
        # Green background
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, G)
        # Yellow diamond
        cx, cy = FX + FW // 2, FY + FH // 2
        for dy in range(-12, 13):
            w = int((1 - abs(dy) / 12.0) * 20)
            for dx in range(-w, w + 1):
                d.set_pixel(cx + dx, cy + dy, Y)
        # Blue circle
        d.draw_circle(cx, cy, 7, B, filled=True)

    def _china(self, d):
        # Red background
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        # Large yellow star
        d.set_pixel(FX + 8, FY + 6, Y)
        d.set_pixel(FX + 7, FY + 7, Y)
        d.set_pixel(FX + 8, FY + 7, Y)
        d.set_pixel(FX + 9, FY + 7, Y)
        d.set_pixel(FX + 8, FY + 8, Y)
        # Small stars
        for pos in [(14, 4), (16, 6), (16, 9), (14, 11)]:
            d.set_pixel(FX + pos[0], FY + pos[1], Y)

    def _skorea(self, d):
        # White background
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, W)
        # Red/blue yin-yang circle
        cx, cy = FX + FW // 2, FY + FH // 2
        for dy in range(-7, 8):
            for dx in range(-7, 8):
                if dx * dx + dy * dy <= 49:
                    if dy < 0 or (dy == 0 and dx >= 0):
                        d.set_pixel(cx + dx, cy + dy, R)
                    else:
                        d.set_pixel(cx + dx, cy + dy, B)
        # Trigrams (simplified as short lines in corners)
        for i in range(3):
            d.draw_line(FX + 3, FY + 3 + i * 3, FX + 9, FY + 3 + i * 3, BK)
        for i in range(3):
            d.draw_line(FX + FW - 10, FY + FH - 4 - i * 3,
                        FX + FW - 4, FY + FH - 4 - i * 3, BK)

    def _india(self, d):
        self._draw_hstripes(d, [O, W, G])
        # Blue chakra wheel in center
        cx, cy = FX + FW // 2, FY + FH // 2
        d.draw_circle(cx, cy, 4, B, filled=False)
        d.set_pixel(cx, cy, B)

    def _vietnam(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        cx, cy = FX + FW // 2, FY + FH // 2
        # Yellow star
        for dy in range(-5, 6):
            w = max(0, 5 - abs(dy))
            for dx in range(-w, w + 1):
                d.set_pixel(cx + dx, cy + dy, Y)

    def _turkey(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        # White crescent + star
        cx = FX + FW // 2 - 4
        cy = FY + FH // 2
        d.draw_circle(cx, cy, 8, W, filled=True)
        d.draw_circle(cx + 3, cy, 6, R, filled=True)  # cutout
        # Star
        d.set_pixel(cx + 10, cy, W)
        d.set_pixel(cx + 9, cy - 1, W)
        d.set_pixel(cx + 9, cy + 1, W)
        d.set_pixel(cx + 11, cy - 1, W)
        d.set_pixel(cx + 11, cy + 1, W)

    def _israel(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, W)
        # Blue stripes
        for y in range(FY + 3, FY + 6):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, B)
        for y in range(FY + FH - 6, FY + FH - 3):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, B)
        # Star of David — two overlapping triangle outlines
        cx, cy = FX + FW // 2, FY + FH // 2
        s = 6  # half-height
        # Upward triangle: apex at top, base at cy + s//2
        d.draw_line(cx, cy - s, cx - s, cy + s // 2, B)
        d.draw_line(cx, cy - s, cx + s, cy + s // 2, B)
        d.draw_line(cx - s, cy + s // 2, cx + s, cy + s // 2, B)
        # Downward triangle: apex at bottom, base at cy - s//2
        d.draw_line(cx, cy + s, cx - s, cy - s // 2, B)
        d.draw_line(cx, cy + s, cx + s, cy - s // 2, B)
        d.draw_line(cx - s, cy - s // 2, cx + s, cy - s // 2, B)

    def _cuba(self, d):
        # 5 stripes blue/white
        for i in range(5):
            c = B if i % 2 == 0 else W
            y0 = FY + i * FH // 5
            y1 = FY + (i + 1) * FH // 5
            for y in range(y0, y1):
                for x in range(FX, FX + FW):
                    d.set_pixel(x, y, c)
        # Red triangle
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * 0.7)
            for x in range(min(w + 2, FW)):
                d.set_pixel(FX + x, FY + y, R)
        # White star
        self._star(d, FX + 6, FY + FH // 2, W)

    def _chile(self, d):
        half = FH // 2
        # White top, red bottom
        for y in range(FY, FY + half):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, W)
        for y in range(FY + half, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        # Blue canton
        sq = min(half, FW // 3)
        for y in range(FY, FY + half):
            for x in range(FX, FX + sq):
                d.set_pixel(x, y, B)
        self._star(d, FX + sq // 2, FY + half // 2, W)

    def _colombia(self, d):
        # Yellow (half), blue (quarter), red (quarter)
        h1 = FH // 2
        h2 = FH * 3 // 4
        for y in range(FY, FY + h1):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, Y)
        for y in range(FY + h1, FY + h2):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, B)
        for y in range(FY + h2, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)

    def _mexico(self, d):
        # Green-white-red vertical stripes
        self._draw_vstripes(d, [G, W, R])
        # Coat of arms: eagle on cactus in center white stripe
        cx, cy = FX + FW // 2, FY + FH // 2
        # Cactus (green vertical with pads)
        for dy in range(2, 8):
            d.set_pixel(cx, cy + dy, DG)
        d.set_pixel(cx - 1, cy + 4, DG)
        d.set_pixel(cx + 1, cy + 5, DG)
        # Eagle body (brown/dark)
        BR = (120, 70, 20)
        for dx in range(-3, 4):
            d.set_pixel(cx + dx, cy, BR)
        for dx in range(-2, 3):
            d.set_pixel(cx + dx, cy - 1, BR)
            d.set_pixel(cx + dx, cy + 1, BR)
        for dx in range(-1, 2):
            d.set_pixel(cx + dx, cy - 2, BR)
        # Wings spread
        for dx in range(3, 7):
            d.set_pixel(cx - dx, cy - 1, BR)
            d.set_pixel(cx + dx, cy - 1, BR)
            d.set_pixel(cx - dx, cy - 2, BR)
            d.set_pixel(cx + dx, cy - 2, BR)
        d.set_pixel(cx - 7, cy - 2, BR)
        d.set_pixel(cx + 7, cy - 2, BR)
        d.set_pixel(cx - 7, cy - 3, BR)
        d.set_pixel(cx + 7, cy - 3, BR)
        # Head
        d.set_pixel(cx, cy - 3, BR)
        d.set_pixel(cx, cy - 4, BR)
        # Snake (green, in beak)
        d.set_pixel(cx + 1, cy - 3, G)
        d.set_pixel(cx + 2, cy - 4, G)

    def _jamaica(self, d):
        # Green background with gold X
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, G)
        # Black triangles top/bottom
        for y in range(FH // 2):
            w = int(y * FW / FH)
            for x in range(FX + FW // 2 - w, FX + FW // 2 + w + 1):
                if FY + y < FY + FH:
                    d.set_pixel(x, FY + y, BK)
                    d.set_pixel(x, FY + FH - 1 - y, BK)
        # Gold X diagonals
        d.draw_line(FX, FY, FX + FW - 1, FY + FH - 1, Y)
        d.draw_line(FX, FY + FH - 1, FX + FW - 1, FY, Y)

    def _safrica(self, d):
        # 5 stripes with Y-shape
        h = FH // 3
        for y in range(FY, FY + h):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        for y in range(FY + h, FY + 2*h):
            for x in range(FX, FX + FW): d.set_pixel(x, y, W)
        for y in range(FY + 2*h, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, B)
        # Green Y
        cy = FY + FH // 2
        for x in range(FX, FX + FW // 3):
            span = int((FH // 2) * (1 - x / (FW // 3 + 1)))
            for dy in range(-span, span + 1):
                d.set_pixel(x, cy + dy, G)
        for x in range(FX + FW // 3, FX + FW):
            d.set_pixel(x, cy, G)
            d.set_pixel(x, cy - 1, G)

    def _kenya(self, d):
        self._draw_hstripes(d, [BK, R, G])
        # White separators
        for x in range(FX, FX + FW):
            d.set_pixel(x, FY + FH // 3, W)
            d.set_pixel(x, FY + 2 * FH // 3, W)
        # Shield (simplified)
        cx = FX + FW // 2
        cy = FY + FH // 2
        d.draw_circle(cx, cy, 3, R, filled=True)
        d.set_pixel(cx, cy, BK)

    def _tanzania(self, d):
        # Green upper-left, blue lower-right, black diagonal
        for y in range(FY, FY + FH):
            split = FX + int((y - FY) * FW / FH)
            for x in range(FX, split):
                d.set_pixel(x, y, G)
            for x in range(split, FX + FW):
                d.set_pixel(x, y, B)
        # Black diagonal stripe
        for y in range(FY, FY + FH):
            cx = FX + int((y - FY) * FW / FH)
            for dx in range(-2, 3):
                d.set_pixel(cx + dx, y, BK)
        # Yellow outlines
        for y in range(FY, FY + FH):
            cx = FX + int((y - FY) * FW / FH)
            d.set_pixel(cx - 3, y, Y)
            d.set_pixel(cx + 3, y, Y)

    def _morocco(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        cx, cy = FX + FW // 2, FY + FH // 2
        d.draw_circle(cx, cy, 5, G, filled=False)

    def _tunisia(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, R)
        cx, cy = FX + FW // 2, FY + FH // 2
        d.draw_circle(cx, cy, 7, W, filled=True)
        d.draw_circle(cx, cy, 5, R, filled=True)
        d.draw_circle(cx + 2, cy, 4, W, filled=True)
        d.draw_circle(cx + 2, cy, 4, R, filled=True)

    def _algeria(self, d):
        # Green left, white right
        half = FX + FW // 2
        for y in range(FY, FY + FH):
            for x in range(FX, half):
                d.set_pixel(x, y, G)
            for x in range(half, FX + FW):
                d.set_pixel(x, y, W)
        # Red crescent + star
        cx, cy = half, FY + FH // 2
        d.draw_circle(cx, cy, 6, R, filled=True)
        d.draw_circle(cx + 2, cy, 5, W if True else G, filled=True)

    def _philippines(self, d):
        # Blue top, red bottom
        half = FY + FH // 2
        for y in range(FY, half):
            for x in range(FX, FX + FW): d.set_pixel(x, y, B)
        for y in range(half, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        # White triangle
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * 0.6)
            for x in range(min(w + 2, FW)):
                d.set_pixel(FX + x, FY + y, W)
        # Yellow sun
        self._star(d, FX + 6, FY + FH // 2, Y)

    def _malaysia(self, d):
        # 14 stripes red/white
        for i in range(14):
            c = R if i % 2 == 0 else W
            y0 = FY + i * FH // 14
            y1 = FY + (i + 1) * FH // 14
            for y in range(y0, y1):
                for x in range(FX, FX + FW):
                    d.set_pixel(x, y, c)
        # Blue canton
        for y in range(FY, FY + FH // 2):
            for x in range(FX, FX + FW // 2):
                d.set_pixel(x, y, DB)
        # Crescent + star
        cx = FX + FW // 4
        cy = FY + FH // 4
        d.draw_circle(cx, cy, 4, Y, filled=True)
        d.draw_circle(cx + 1, cy, 3, DB, filled=True)

    def _saudi(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, G)
        # Stylized calligraphy (pixel-art suggestion of Arabic script)
        # Main script line with vertical strokes (alifs/lams)
        for x in range(FX + 6, FX + 42):
            d.set_pixel(x, FY + 14, W)  # baseline
        # Vertical strokes (tall letters)
        for vx in [8, 14, 20, 28, 34, 40]:
            for dy in range(-5, 0):
                d.set_pixel(FX + vx, FY + 14 + dy, W)
        # Connecting curves / dots above
        for px in [11, 17, 24, 31, 37]:
            d.set_pixel(FX + px, FY + 7, W)
        # Sub-baseline curves (letter tails)
        for px in [12, 25, 38]:
            d.set_pixel(FX + px, FY + 15, W)
            d.set_pixel(FX + px + 1, FY + 16, W)
        # Sword — blade with handle
        d.draw_line(FX + 8, FY + 23, FX + 40, FY + 23, W)
        d.set_pixel(FX + 7, FY + 22, W)  # handle guard
        d.set_pixel(FX + 7, FY + 24, W)
        d.set_pixel(FX + 6, FY + 23, W)  # grip

    def _uae(self, d):
        # Red vertical band + 3 horizontal stripes
        vw = FW // 4
        for y in range(FY, FY + FH):
            for x in range(FX, FX + vw):
                d.set_pixel(x, y, R)
        h = FH // 3
        colors = [G, W, BK]
        for i, c in enumerate(colors):
            for y in range(FY + i * h, FY + (i + 1) * h):
                for x in range(FX + vw, FX + FW):
                    d.set_pixel(x, y, c)

    def _pakistan(self, d):
        # Green with white left band
        vw = FW // 4
        for y in range(FY, FY + FH):
            for x in range(FX, FX + vw):
                d.set_pixel(x, y, W)
            for x in range(FX + vw, FX + FW):
                d.set_pixel(x, y, DG)
        # White crescent + star
        cx = FX + FW * 5 // 8
        cy = FY + FH // 2
        d.draw_circle(cx, cy, 6, W, filled=True)
        d.draw_circle(cx + 2, cy, 5, DG, filled=True)

    def _srilanka(self, d):
        # Green/orange stripes on left, maroon on right
        for y in range(FY, FY + FH // 2):
            for x in range(FX, FX + FW // 4): d.set_pixel(x, y, G)
        for y in range(FY + FH // 2, FY + FH):
            for x in range(FX, FX + FW // 4): d.set_pixel(x, y, O)
        for y in range(FY, FY + FH):
            for x in range(FX + FW // 4, FX + FW):
                d.set_pixel(x, y, MAR)
        # Lion (simplified)
        cx = FX + FW * 5 // 8
        cy = FY + FH // 2
        d.draw_rect(cx - 3, cy - 4, 6, 8, Y)

    def _nepal(self, d):
        # Unique non-rectangular flag - draw as two triangles
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW):
                d.set_pixel(x, y, (20, 20, 40))  # dark bg
        # Two stacked triangles (pennants)
        for y in range(FH * 2 // 3):
            w = int((FH * 2 // 3 - y) * FW * 0.6 / (FH * 2 // 3))
            for x in range(min(w, FW)):
                d.set_pixel(FX + x, FY + y, (200, 20, 40))
        for y in range(FH):
            w = int((FH - y) * FW * 0.6 / FH)
            for x in range(min(w, FW)):
                d.set_pixel(FX + x, FY + y, (200, 20, 40))
        # Blue borders
        for y in range(FH):
            w = int((FH - y) * FW * 0.6 / FH)
            if w > 0 and w < FW:
                d.set_pixel(FX + w, FY + y, B)

    def _laos(self, d):
        h = FH // 4
        for y in range(FY, FY + h):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        for y in range(FY + h, FY + 3*h):
            for x in range(FX, FX + FW): d.set_pixel(x, y, B)
        for y in range(FY + 3*h, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        cx, cy = FX + FW // 2, FY + FH // 2
        d.draw_circle(cx, cy, 5, W, filled=True)

    def _nkorea(self, d):
        self._draw_hstripes(d, [B, R, B])
        # White separators
        for x in range(FX, FX + FW):
            d.set_pixel(x, FY + FH // 3, W)
            d.set_pixel(x, FY + 2 * FH // 3, W)
        # Red circle with star
        cx, cy = FX + FW // 3, FY + FH // 2
        d.draw_circle(cx, cy, 6, W, filled=True)
        d.draw_circle(cx, cy, 5, R, filled=True)

    def _palestine(self, d):
        self._draw_hstripes(d, [BK, W, G])
        # Red triangle on hoist side
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * 0.6)
            for x in range(min(w + 2, FW)):
                d.set_pixel(FX + x, FY + y, R)

    def _jordan(self, d):
        self._draw_hstripes(d, [BK, W, G])
        # Red triangle
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * 0.6)
            for x in range(min(w + 2, FW)):
                d.set_pixel(FX + x, FY + y, R)

    def _lebanon(self, d):
        h = FH // 4
        for y in range(FY, FY + h):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        for y in range(FY + h, FY + 3*h):
            for x in range(FX, FX + FW): d.set_pixel(x, y, W)
        for y in range(FY + 3*h, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        # Cedar tree (simplified)
        cx = FX + FW // 2
        for dy in range(-5, 5):
            w = max(0, 5 - abs(dy))
            for dx in range(-w, w + 1):
                d.set_pixel(cx + dx, FY + FH // 2 + dy - 2, G)

    def _qatar(self, d):
        # White left, maroon right with zigzag
        split = FX + FW // 3
        for y in range(FY, FY + FH):
            for x in range(FX, split):
                d.set_pixel(x, y, W)
            for x in range(split, FX + FW):
                d.set_pixel(x, y, MAR)

    def _kuwait(self, d):
        self._draw_hstripes(d, [G, W, R])
        # Black trapezoid on left
        for y in range(FH):
            w = int(FW * 0.2 * (1 - abs(y - FH // 2) / (FH // 2 + 1) * 0.5))
            for x in range(max(1, w)):
                d.set_pixel(FX + x, FY + y, BK)

    def _trinidad(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        # Black diagonal stripe
        d.draw_line(FX + 8, FY, FX + FW, FY + FH - 8, BK)
        d.draw_line(FX + 6, FY, FX + FW, FY + FH - 6, BK)
        d.draw_line(FX + 10, FY, FX + FW, FY + FH - 10, BK)
        # White outlines
        d.draw_line(FX + 5, FY, FX + FW, FY + FH - 5, W)
        d.draw_line(FX + 11, FY, FX + FW, FY + FH - 11, W)

    def _bahamas(self, d):
        self._draw_hstripes(d, [LB, Y, LB])
        # Black triangle
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * 0.6)
            for x in range(min(w + 2, FW)):
                d.set_pixel(FX + x, FY + y, BK)

    def _dominican(self, d):
        # Quartered blue/red with white cross
        half_w = FW // 2
        half_h = FH // 2
        for y in range(FY, FY + half_h):
            for x in range(FX, FX + half_w): d.set_pixel(x, y, B)
            for x in range(FX + half_w, FX + FW): d.set_pixel(x, y, R)
        for y in range(FY + half_h, FY + FH):
            for x in range(FX, FX + half_w): d.set_pixel(x, y, R)
            for x in range(FX + half_w, FX + FW): d.set_pixel(x, y, B)
        # White cross
        cx, cy = FX + half_w, FY + half_h
        for y in range(FY, FY + FH): d.set_pixel(cx, y, W)
        for x in range(FX, FX + FW): d.set_pixel(x, cy, W)

    def _costarica(self, d):
        # Blue-white-red-white-blue (1:1:2:1:1)
        h = FH // 6
        colors = [B, W, R, R, W, B]
        for i, c in enumerate(colors):
            for y in range(FY + i * h, FY + (i + 1) * h):
                for x in range(FX, FX + FW): d.set_pixel(x, y, c)

    def _panama(self, d):
        # Quartered white/red/blue with stars
        hw, hh = FW // 2, FH // 2
        for y in range(FY, FY + hh):
            for x in range(FX, FX + hw): d.set_pixel(x, y, W)
            for x in range(FX + hw, FX + FW): d.set_pixel(x, y, R)
        for y in range(FY + hh, FY + FH):
            for x in range(FX, FX + hw): d.set_pixel(x, y, B)
            for x in range(FX + hw, FX + FW): d.set_pixel(x, y, W)
        self._star(d, FX + hw // 2, FY + hh // 2, B)
        self._star(d, FX + hw + hw // 2, FY + hh + hh // 2, R)

    def _madagascar(self, d):
        vw = FW // 3
        for y in range(FY, FY + FH):
            for x in range(FX, FX + vw): d.set_pixel(x, y, W)
        for y in range(FY, FY + FH // 2):
            for x in range(FX + vw, FX + FW): d.set_pixel(x, y, R)
        for y in range(FY + FH // 2, FY + FH):
            for x in range(FX + vw, FX + FW): d.set_pixel(x, y, G)

    def _mozambique(self, d):
        self._draw_hstripes(d, [G, BK, Y])
        # White separators
        for x in range(FX, FX + FW):
            d.set_pixel(x, FY + FH // 3, W)
            d.set_pixel(x, FY + 2 * FH // 3, W)
        # Red triangle
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * 0.5)
            for x in range(min(w + 2, FW)):
                d.set_pixel(FX + x, FY + y, R)

    def _australia(self, d):
        # Blue background
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, B)
        # Union Jack canton (simplified)
        for y in range(FY, FY + FH // 2):
            for x in range(FX, FX + FW // 2):
                d.set_pixel(x, y, NAV)
        cx, cy = FX + FW // 4, FY + FH // 4
        for y in range(FY, FY + FH // 2):
            d.set_pixel(cx, y, R)
        for x in range(FX, FX + FW // 2):
            d.set_pixel(x, cy, R)
        # Southern Cross stars
        for pos in [(38, 10), (42, 16), (38, 24), (34, 18), (40, 20)]:
            self._star(d, FX + pos[0] - 8, FY + pos[1], W)

    def _nzealand(self, d):
        # Blue background
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, B)
        # Union Jack canton
        for y in range(FY, FY + FH // 2):
            for x in range(FX, FX + FW // 2):
                d.set_pixel(x, y, NAV)
        cx, cy = FX + FW // 4, FY + FH // 4
        for y in range(FY, FY + FH // 2): d.set_pixel(cx, y, R)
        for x in range(FX, FX + FW // 2): d.set_pixel(x, cy, R)
        # 4 red stars
        for pos in [(38, 8), (42, 14), (40, 22), (36, 18)]:
            self._star(d, FX + pos[0] - 8, FY + pos[1], R)

    def _fiji(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, LB)
        # Union Jack canton
        for y in range(FY, FY + FH // 2):
            for x in range(FX, FX + FW // 3):
                d.set_pixel(x, y, NAV)
        # Shield
        cx = FX + FW * 2 // 3
        cy = FY + FH // 2
        d.draw_rect(cx - 4, cy - 5, 8, 10, W)
        d.draw_line(cx, cy - 5, cx, cy + 4, R)
        d.draw_line(cx - 4, cy, cx + 3, cy, R)

    def _png(self, d):
        # Diagonally split: red upper-right, black lower-left
        for y in range(FY, FY + FH):
            split = FX + int((y - FY) * FW / FH)
            for x in range(FX, split): d.set_pixel(x, y, BK)
            for x in range(split, FX + FW): d.set_pixel(x, y, R)
        # Stars on black side (Southern Cross)
        for pos in [(8, 18), (5, 22), (10, 26), (7, 14)]:
            self._star(d, FX + pos[0], FY + pos[1], W)
        # Bird on red side
        d.set_pixel(FX + 32, FY + 10, Y)
        d.set_pixel(FX + 33, FY + 11, Y)

    def _tonga(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        # White canton with red cross
        for y in range(FY, FY + FH // 2):
            for x in range(FX, FX + FW // 3): d.set_pixel(x, y, W)
        cx, cy = FX + FW // 6, FY + FH // 4
        for y in range(FY + 2, FY + FH // 2 - 2): d.set_pixel(cx, y, R)
        for x in range(FX + 2, FX + FW // 3 - 2): d.set_pixel(x, cy, R)

    def _samoa(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        # Blue canton
        for y in range(FY, FY + FH * 2 // 3):
            for x in range(FX, FX + FW // 2): d.set_pixel(x, y, B)
        # Stars (Southern Cross)
        for pos in [(8, 4), (14, 8), (10, 14), (6, 10)]:
            self._star(d, FX + pos[0], FY + pos[1], W)

    def _solomon(self, d):
        # Diagonally split: blue upper, green lower
        for y in range(FY, FY + FH):
            split = FX + int((y - FY) * FW / FH)
            for x in range(FX, split): d.set_pixel(x, y, B)
            for x in range(split, FX + FW): d.set_pixel(x, y, G)
        # Yellow diagonal stripe
        for y in range(FY, FY + FH):
            cx = FX + int((y - FY) * FW / FH)
            d.set_pixel(cx, y, Y)
            d.set_pixel(cx - 1, y, Y)

    def _vanuatu(self, d):
        half = FH // 2
        for y in range(FY, FY + half):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        for y in range(FY + half, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, G)
        # Black triangle on left
        for y in range(FH):
            w = int((FH // 2 - abs(y - FH // 2)) * 0.5)
            for x in range(min(w + 2, FW)):
                d.set_pixel(FX + x, FY + y, BK)
        # Yellow Y
        d.set_pixel(FX + 2, FY + FH // 2, Y)
        d.draw_line(FX, FY + 4, FX + FW // 4, FY + FH // 2, Y)
        d.draw_line(FX, FY + FH - 4, FX + FW // 4, FY + FH // 2, Y)

    def _marshall(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, B)
        # Orange/white diagonal stripes
        d.draw_line(FX, FY + FH * 2 // 3, FX + FW - 1, FY + 2, O)
        d.draw_line(FX, FY + FH * 3 // 4, FX + FW - 1, FY + 4, W)
        # Star
        self._star(d, FX + 6, FY + 6, W)

    def _micronesia(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, LB)
        # 4 white stars in diamond
        cx, cy = FX + FW // 2, FY + FH // 2
        self._star(d, cx, cy - 8, W)
        self._star(d, cx, cy + 8, W)
        self._star(d, cx - 10, cy, W)
        self._star(d, cx + 10, cy, W)

    def _nauru(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, B)
        # Yellow horizontal stripe
        cy = FY + FH // 2
        for x in range(FX, FX + FW):
            d.set_pixel(x, cy, Y)
            d.set_pixel(x, cy + 1, Y)
        # White star below
        self._star(d, FX + FW // 3, FY + FH * 2 // 3, W)

    def _albania(self, d):
        for y in range(FY, FY + FH):
            for x in range(FX, FX + FW): d.set_pixel(x, y, R)
        # Black eagle (simplified)
        cx, cy = FX + FW // 2, FY + FH // 2
        d.set_pixel(cx, cy - 4, BK)
        d.set_pixel(cx - 1, cy - 3, BK)
        d.set_pixel(cx + 1, cy - 3, BK)
        for dx in range(-4, 5):
            d.set_pixel(cx + dx, cy, BK)
        d.set_pixel(cx - 3, cy + 1, BK)
        d.set_pixel(cx + 3, cy + 1, BK)
        d.set_pixel(cx - 2, cy + 2, BK)
        d.set_pixel(cx + 2, cy + 2, BK)

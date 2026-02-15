"""Pantry - Building blocks of cooking on 64x64 LED matrix.

Aromatics, roux, stocks, and herb bundles with ratio blocks
showing component proportions as colored squares.
"""

from . import Visual

# ── Families ────────────────────────────────────────────────────────
FAMILIES = ["AROMATICS", "ROUX", "STOCKS", "HERBS"]
FAMILY_COLORS = [
    (200, 160, 60),    # AROMATICS = warm amber
    (180, 150, 80),    # ROUX = butter gold
    (160, 100, 50),    # STOCKS = deep brown
    (80, 160, 80),     # HERBS = forest green
]

HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)

# ── Pantry data ─────────────────────────────────────────────────────
ITEMS = [
    # AROMATICS (family 0)
    {'name': 'MIREPOIX', 'family': 0, 'num': 1,
     'parts': [('ONION', 2, (220, 180, 100)), ('CARROT', 1, (240, 140, 40)), ('CELERY', 1, (140, 200, 80))],
     'method': 'DICE FINE  SWEAT IN BUTTER  NO BROWNING',
     'use': 'STOCKS  SOUPS  BRAISES  SAUCES'},
    {'name': 'WHITE MIREPOIX', 'family': 0, 'num': 2,
     'parts': [('ONION', 2, (220, 200, 160)), ('PARSNIP', 1, (240, 230, 180)), ('CELERY', 1, (180, 220, 160))],
     'method': 'SWEAT IN BUTTER  KEEP WHITE  NO COLOR',
     'use': 'WHITE STOCKS  CREAM SOUPS  VELOUTE'},
    {'name': 'HOLY TRINITY', 'family': 0, 'num': 3,
     'parts': [('ONION', 2, (220, 180, 100)), ('CELERY', 1, (140, 200, 80)), ('PEPPER', 1, (60, 160, 60))],
     'method': 'DICE MEDIUM  SAUTE IN OIL UNTIL SOFT',
     'use': 'GUMBO  JAMBALAYA  ETOUFFEE'},
    {'name': 'SOFFRITTO', 'family': 0, 'num': 4,
     'parts': [('ONION', 1, (220, 180, 100)), ('CARROT', 1, (240, 140, 40)), ('CELERY', 1, (140, 200, 80))],
     'method': 'MINCE FINE  SLOW COOK IN EVOO UNTIL SWEET',
     'use': 'RAGU  RISOTTO  MINESTRONE'},
    {'name': 'SOFRITO', 'family': 0, 'num': 5,
     'parts': [('ONION', 1, (220, 180, 100)), ('GARLIC', 1, (240, 230, 180)), ('TOMATO', 1, (220, 60, 40)), ('PEPPER', 1, (60, 160, 60))],
     'method': 'SAUTE ONION + GARLIC  ADD TOMATO + PEPPER',
     'use': 'PAELLA  BEANS  STEWS  RICE'},

    # ROUX (family 1)
    {'name': 'WHITE ROUX', 'family': 1, 'num': 6,
     'parts': [('BUTTER', 1, (240, 220, 100)), ('FLOUR', 1, (220, 180, 120))],
     'method': 'MELT BUTTER  ADD FLOUR  COOK 2-3 MIN  NO COLOR',
     'use': 'BECHAMEL  CREAM SOUPS  GRATINS'},
    {'name': 'BLOND ROUX', 'family': 1, 'num': 7,
     'parts': [('BUTTER', 1, (240, 220, 100)), ('FLOUR', 1, (200, 180, 120))],
     'method': 'COOK 4-5 MIN TO PALE GOLD  SLIGHT NUTTY AROMA',
     'use': 'VELOUTE  LIGHT SAUCES'},
    {'name': 'BROWN ROUX', 'family': 1, 'num': 8,
     'parts': [('FAT', 1, (180, 140, 60)), ('FLOUR', 1, (140, 100, 50))],
     'method': 'COOK 6-15 MIN  MED-DARK BROWN  NUTTY TOASTY',
     'use': 'ESPAGNOLE  GUMBO  BROWN SAUCES'},

    # STOCKS (family 2)
    {'name': 'CHICKEN STOCK', 'family': 2, 'num': 9,
     'parts': [('BONES', 3, (220, 200, 160)), ('WATER', 5, (80, 140, 255)), ('MIRPX', 1, (200, 160, 80))],
     'method': 'RAW BONES + COLD WATER  NEVER BOIL  SKIM  3-4 HRS',
     'use': 'SOUPS  SAUCES  RISOTTO  BRAISES'},
    {'name': 'BROWN BEEF', 'family': 2, 'num': 10,
     'parts': [('BONES', 3, (160, 100, 50)), ('WATER', 5, (80, 140, 255)), ('MIRPX', 1, (200, 160, 80))],
     'method': 'ROAST BONES 425F  DEGLAZE PAN  SIMMER 8-12 HRS',
     'use': 'DEMI-GLACE  BROWN SAUCES  BRAISES'},
    {'name': 'FISH FUMET', 'family': 2, 'num': 11,
     'parts': [('BONES', 2, (200, 200, 220)), ('WATER', 3, (80, 140, 255)), ('WINE', 1, (220, 220, 160))],
     'method': 'LEAN WHITE FISH ONLY  SWEAT + WINE  30-45 MIN MAX',
     'use': 'FISH SAUCES  POACHING  RISOTTO'},
    {'name': 'VEGETABLE', 'family': 2, 'num': 12,
     'parts': [('ONION', 1, (220, 180, 100)), ('CARROT', 1, (240, 140, 40)), ('CELERY', 1, (140, 200, 80)), ('LEEK', 1, (160, 200, 120))],
     'method': 'NO BRASSICAS  SWEAT IN BUTTER  30-45 MIN ONLY',
     'use': 'VEGETARIAN SOUPS  GRAINS  SAUCES'},

    # HERBS (family 3)
    {'name': 'BOUQUET GARNI', 'family': 3, 'num': 13,
     'parts': [('PARSLY', 2, (100, 180, 60)), ('THYME', 1, (140, 160, 100)), ('BAY', 1, (80, 120, 60))],
     'method': 'TIE WITH TWINE  SIMMER IN LIQUID  REMOVE BEFORE SERVE',
     'use': 'STOCKS  BRAISES  SOUPS  STEWS'},
    {'name': "SACHET D'EPICES", 'family': 3, 'num': 14,
     'parts': [('PARSLY', 1, (100, 180, 60)), ('THYME', 1, (140, 160, 100)), ('BAY', 1, (80, 120, 60)), ('PPPRCN', 1, (60, 60, 60))],
     'method': 'WRAP IN CHEESECLOTH  TIE CLOSED  HOLDS LOOSE SPICES',
     'use': 'STOCKS  SOUPS  SAUCES  CONSOMME'},
]

# Build per-family index
_FAMILY_ITEMS = [[] for _ in range(len(FAMILIES))]
for _i, _item in enumerate(ITEMS):
    _FAMILY_ITEMS[_item['family']].append(_i)


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


class Pantry(Visual):
    name = "PANTRY"
    description = "Cooking building blocks"
    category = "cooking"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout Y positions
    NAME_Y = 1
    SEP1_Y = 7
    BLOCKS_Y = 9      # ratio blocks start
    BLOCKS_H = 8      # block height
    LEGEND_Y = 19     # colored legend line (dots + names)
    SEP2_Y = 25
    METHOD_Y = 27
    SEP3_Y = 33
    USE_LBL_Y = 35
    USE_Y = 37
    SEP4_Y = 43
    FAM_Y = 47
    FOOT_SEP_Y = 57
    FOOT_Y = 59

    def reset(self):
        self.time = 0.0
        self.idx = 0
        self._name_scroll_x = 0.0
        self._legend_scroll_x = 0.0
        self._method_scroll_x = 0.0
        self._use_scroll_x = 0.0
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0
        self._switch_flash = 0.0

    def _current(self):
        return ITEMS[self.idx % len(ITEMS)]

    def _step(self, direction):
        self.idx = (self.idx + direction) % len(ITEMS)
        self._name_scroll_x = 0.0
        self._legend_scroll_x = 0.0
        self._method_scroll_x = 0.0
        self._use_scroll_x = 0.0
        self._switch_flash = 0.15

    def _jump_family(self, direction):
        cur = self._current()['family']
        target = (cur + direction) % len(FAMILIES)
        if _FAMILY_ITEMS[target]:
            self.idx = _FAMILY_ITEMS[target][0]
        self._name_scroll_x = 0.0
        self._legend_scroll_x = 0.0
        self._method_scroll_x = 0.0
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
            self._jump_family(-1)
            consumed = True
        elif input_state.down_pressed:
            self._jump_family(1)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._name_scroll_x = 0.0
            self._legend_scroll_x = 0.0
            self._method_scroll_x = 0.0
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

        item = self._current()
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, item['name'], 48, dt, 18)

        # Legend: build text for width calculation
        legend_text = self._build_legend_text(item['parts'])
        self._legend_scroll_x = self._advance_scroll(
            self._legend_scroll_x, legend_text, 60, dt, 14)

        self._method_scroll_x = self._advance_scroll(
            self._method_scroll_x, item['method'], 60, dt, 16)
        self._use_scroll_x = self._advance_scroll(
            self._use_scroll_x, item['use'], 60, dt, 16)

    def _advance_scroll(self, scroll_x, text, avail_px, dt, speed):
        text_px = len(text) * 4
        if text_px > avail_px:
            scroll_x += dt * speed
            total = self.SCROLL_LEAD_IN + text_px + 20
            if scroll_x >= total:
                scroll_x -= total
        return scroll_x

    @staticmethod
    def _build_legend_text(parts):
        """Build a flat string for scroll-width calculation."""
        # Format: "@ NAME 2  @ NAME 1" — @ is a placeholder for the color dot
        segs = []
        for name, count, _color in parts:
            segs.append(f'  {name} {count}')
        return '  '.join(segs)

    def _build_legend_segments(self, parts):
        """Build list of (text, color) for multi-color legend drawing."""
        segments = []
        for i, (name, count, color) in enumerate(parts):
            if i > 0:
                segments.append(('  ', TEXT_DIM))   # spacer
            # Dot char will be drawn as a filled square in _draw_legend
            segments.append(('\x00', color))        # sentinel for color swatch
            segments.append((f'{name} {count}', color))
        return segments

    def draw(self):
        d = self.display
        d.clear()

        item = self._current()
        fam = item['family']
        fam_color = FAMILY_COLORS[fam]

        # ── Header: item name ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(item['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(fam_color, 0.6))

        name_start_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_start_x, self.NAME_Y,
                                  item['name'], fam_color,
                                  self._name_scroll_x, 63 - name_start_x)

        # ── Sep 1 ──
        self._draw_sep(d, self.SEP1_Y)

        # ── Ratio blocks (clean, no labels) ──
        parts = item['parts']
        total_parts = sum(p[1] for p in parts)
        block_area_w = 60
        block_h = self.BLOCKS_H
        block_x = 2
        gap = 1  # 1px gap between blocks

        if total_parts > 0:
            # Calculate widths, accounting for gaps
            num_gaps = len(parts) - 1
            usable_w = block_area_w - num_gaps * gap
            widths = []
            for _name, count, _color in parts:
                widths.append(max(2, int(count / total_parts * usable_w)))
            # Distribute rounding error to largest block
            diff = usable_w - sum(widths)
            if diff != 0:
                largest = widths.index(max(widths))
                widths[largest] += diff

            for i, ((_name, _count, color), w) in enumerate(zip(parts, widths)):
                # Filled block interior
                for bx in range(block_x + 1, min(block_x + w - 1, 63)):
                    for by in range(self.BLOCKS_Y + 1, self.BLOCKS_Y + block_h - 1):
                        d.set_pixel(bx, by, color)
                # Dimmer border
                border = _dim(color, 0.5)
                for bx in range(block_x, min(block_x + w, 63)):
                    d.set_pixel(bx, self.BLOCKS_Y, border)
                    d.set_pixel(bx, self.BLOCKS_Y + block_h - 1, border)
                for by in range(self.BLOCKS_Y, self.BLOCKS_Y + block_h):
                    d.set_pixel(block_x, by, border)
                    d.set_pixel(min(block_x + w - 1, 62), by, border)

                block_x += w + gap

        # ── Legend line (colored dots + names, scrolls if needed) ──
        self._draw_legend(d, 2, self.LEGEND_Y, parts, self._legend_scroll_x, 60)

        # ── Sep 2 ──
        self._draw_sep(d, self.SEP2_Y)

        # ── Method (scrolling) ──
        self._draw_scrolling_text(d, 2, self.METHOD_Y,
                                  item['method'], (180, 180, 200),
                                  self._method_scroll_x, 60)

        # ── Sep 3 ──
        self._draw_sep(d, self.SEP3_Y)

        # ── "USE" label + use text ──
        use_label_color = _dim(fam_color, 0.3)
        d.draw_text_small(1, self.USE_LBL_Y, 'USE', use_label_color)
        self._draw_scrolling_text(d, 2, self.USE_Y,
                                  item['use'], TEXT_DIM,
                                  self._use_scroll_x, 60)

        # ── Sep 4 ──
        self._draw_sep(d, self.SEP4_Y)

        # ── Family name (centered, dimmed) ──
        fam_name = FAMILIES[fam]
        fam_name_px = len(fam_name) * 4
        fam_x = (64 - fam_name_px) // 2
        d.draw_text_small(fam_x, self.FAM_Y, fam_name, _dim(fam_color, 0.35))

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)

        pos_str = f'{self.idx + 1}/{len(ITEMS)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)

        # Family position right-aligned
        fam_list = _FAMILY_ITEMS[fam]
        fam_pos = fam_list.index(self.idx) + 1 if self.idx in fam_list else 1
        fam_str = f'{fam_pos}/{len(fam_list)}'
        fam_str_px = len(fam_str) * 4
        d.draw_text_small(63 - fam_str_px, self.FOOT_Y, fam_str, fam_color)

    def _draw_legend(self, d, start_x, y, parts, scroll_x, avail_px):
        """Draw multi-colored legend: ■NAME N  ■NAME N ..."""
        # Build flat character list with per-char colors
        chars = []  # list of (char, color)  — '\x00' = 3x3 swatch
        for i, (name, count, color) in enumerate(parts):
            if i > 0:
                chars.append((' ', TEXT_DIM))
                chars.append((' ', TEXT_DIM))
            # Color swatch (occupies one 4px char slot)
            chars.append(('\x00', color))
            for ch in f'{name} {count}':
                chars.append((ch, color))

        text_px = len(chars) * 4
        if text_px <= avail_px:
            # Static: draw centered
            x = start_x + (avail_px - text_px) // 2
            for ch, color in chars:
                if ch == '\x00':
                    # Draw 3x3 filled swatch
                    for sx in range(3):
                        for sy in range(3):
                            d.set_pixel(x + sx, y + 1 + sy, color)
                else:
                    self._draw_char_col(d, x, y, ch, 0, color)
                    self._draw_char_col(d, x + 1, y, ch, 1, color)
                    self._draw_char_col(d, x + 2, y, ch, 2, color)
                x += 4
        else:
            # Scrolling
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
                if 0 <= char_idx < len(chars):
                    ch, color = chars[char_idx]
                    if ch == '\x00':
                        # Swatch: draw if in the 3x3 area
                        if col < 3:
                            for sy in range(3):
                                d.set_pixel(cx, y + 1 + sy, color)
                    elif col < 3:
                        self._draw_char_col(d, cx, y, ch, col, color)

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

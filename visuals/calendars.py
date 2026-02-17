"""
CALENDARS - Calendar Systems of the World
==========================================
Displays 8 historic calendar systems with unique visual representations.
Mayan dot-bar numerals, Islamic crescent phases, Chinese zodiac pixel art,
Hebrew Star of David, Gregorian month grid, Egyptian seasons, French
Republican decimal clock, and Ethiopian 13-month calendar.

Controls:
  Left/Right - Cycle calendar systems
  Action     - Next calendar
"""

import math
from . import Visual, Colors

# ---------------------------------------------------------------------------
# Calendar data
# ---------------------------------------------------------------------------
CALENDARS = [
    {'name': 'MAYAN',       'origin': 'MESOAMERICA 3114 BCE', 'color': (160, 140, 60)},
    {'name': 'ISLAMIC',     'origin': 'ARABIA 622 CE',        'color': (40, 160, 80)},
    {'name': 'CHINESE',     'origin': 'CHINA 2637 BCE',       'color': (200, 50, 40)},
    {'name': 'HEBREW',      'origin': 'MESOPOTAMIA 3761 BCE', 'color': (60, 100, 200)},
    {'name': 'GREGORIAN',   'origin': 'EUROPE 1582 CE',       'color': (180, 180, 200)},
    {'name': 'EGYPTIAN',    'origin': 'EGYPT 3000 BCE',       'color': (200, 170, 80)},
    {'name': 'FRENCH REP.', 'origin': 'FRANCE 1793 CE',       'color': (50, 80, 200)},
    {'name': 'ETHIOPIAN',   'origin': 'ETHIOPIA 8 CE',        'color': (60, 160, 60)},
]

NUM_CALENDARS = len(CALENDARS)

# Islamic months
ISLAMIC_MONTHS = [
    'MUHARRAM', 'SAFAR', 'RABI AL-AWWAL', 'RABI AL-THANI',
    'JUMADA AL-ULA', 'JUMADA AL-THANI', 'RAJAB', 'SHABAN',
    'RAMADAN', 'SHAWWAL', 'DHU AL-QADAH', 'DHU AL-HIJJAH',
]

# Chinese zodiac animals
ZODIAC_ANIMALS = [
    'RAT', 'OX', 'TIGER', 'RABBIT', 'DRAGON', 'SNAKE',
    'HORSE', 'GOAT', 'MONKEY', 'ROOSTER', 'DOG', 'PIG',
]

# Simple 12x12 pixel art bitmaps for each zodiac (1 = filled pixel)
# Each is a list of 12 rows, each row a 12-bit integer
ZODIAC_SPRITES = {
    'RAT': [
        0b000110011000,
        0b001001100100,
        0b010000000010,
        0b010011110010,
        0b100100001001,
        0b100100001001,
        0b100011110001,
        0b010000000010,
        0b001000000100,
        0b000111111000,
        0b000010010000,
        0b000010010000,
    ],
    'OX': [
        0b010000000010,
        0b011000000110,
        0b001111111100,
        0b001000000100,
        0b001011101100,
        0b001000000100,
        0b001111111100,
        0b000100001000,
        0b000100001000,
        0b000111111000,
        0b000100001000,
        0b000110011000,
    ],
    'TIGER': [
        0b011000000110,
        0b010100001010,
        0b001111111100,
        0b001010010100,
        0b001111111100,
        0b001000000100,
        0b011111111110,
        0b001000000100,
        0b001111111100,
        0b000100001000,
        0b000100001000,
        0b000110011000,
    ],
    'RABBIT': [
        0b000100010000,
        0b001100011000,
        0b001100011000,
        0b000111110000,
        0b000100010000,
        0b000111110000,
        0b001111111000,
        0b000111110000,
        0b000011100000,
        0b000001000000,
        0b000011100000,
        0b000010100000,
    ],
    'DRAGON': [
        0b001110000000,
        0b011011100000,
        0b010001111100,
        0b110001000010,
        0b100111000010,
        0b100100000100,
        0b011000001000,
        0b001111110000,
        0b000100000000,
        0b000111100000,
        0b000010010000,
        0b000010010000,
    ],
    'SNAKE': [
        0b000000000000,
        0b011111100000,
        0b100000010000,
        0b011100010000,
        0b000010010000,
        0b000010010000,
        0b000001100000,
        0b000001100000,
        0b000010010000,
        0b000100001000,
        0b001000000100,
        0b000111111000,
    ],
    'HORSE': [
        0b000111000000,
        0b001000100000,
        0b010000010000,
        0b010000010000,
        0b010000111110,
        0b001111000010,
        0b000010000010,
        0b000010000010,
        0b000010000010,
        0b000010000010,
        0b000011000110,
        0b000001000100,
    ],
    'GOAT': [
        0b010000010000,
        0b011000110000,
        0b001111100000,
        0b001000100000,
        0b001111100000,
        0b000100011100,
        0b000111111000,
        0b000100001000,
        0b000100001000,
        0b000100001000,
        0b000110011000,
        0b000100001000,
    ],
    'MONKEY': [
        0b000111110000,
        0b001000001000,
        0b010010100100,
        0b010000000100,
        0b010001000100,
        0b001011101000,
        0b000111110000,
        0b001001001000,
        0b000111110000,
        0b000010000000,
        0b000011100000,
        0b000100010000,
    ],
    'ROOSTER': [
        0b000011000000,
        0b000111000000,
        0b000100000000,
        0b001111100000,
        0b010100010000,
        0b010111110000,
        0b010100010000,
        0b001111100000,
        0b000100000000,
        0b000111100000,
        0b000010010000,
        0b000110011000,
    ],
    'DOG': [
        0b011000000000,
        0b010100000000,
        0b001111111000,
        0b001000001000,
        0b001010101000,
        0b001000001000,
        0b001011101000,
        0b001111111000,
        0b000100001000,
        0b000100001000,
        0b000100001000,
        0b000110011000,
    ],
    'PIG': [
        0b000000000000,
        0b001111111100,
        0b010000000010,
        0b010011110010,
        0b010010010010,
        0b010011110010,
        0b010000000010,
        0b001111111100,
        0b000100001000,
        0b000100001000,
        0b000110011000,
        0b000100001000,
    ],
}

# Hebrew months
HEBREW_MONTHS = [
    'TISHREI', 'CHESHVAN', 'KISLEV', 'TEVET',
    'SHEVAT', 'ADAR', 'NISAN', 'IYYAR',
    'SIVAN', 'TAMMUZ', 'AV', 'ELUL',
]

# French Republican months
FRENCH_MONTHS = [
    'VENDEMIAIRE', 'BRUMAIRE', 'FRIMAIRE',
    'NIVOSE', 'PLUVIOSE', 'VENTOSE',
    'GERMINAL', 'FLOREAL', 'PRAIRIAL',
    'MESSIDOR', 'THERMIDOR', 'FRUCTIDOR',
]

# Egyptian seasons
EGYPTIAN_SEASONS = [
    {'name': 'AKHET',  'meaning': 'FLOOD',   'color': (60, 100, 200)},
    {'name': 'PERET',  'meaning': 'GROWING', 'color': (60, 180, 60)},
    {'name': 'SHEMU',  'meaning': 'HARVEST', 'color': (220, 180, 60)},
]

# Ethiopian months
ETHIOPIAN_MONTHS = [
    'MESKEREM', 'TIKIMT', 'HIDAR', 'TAHSAS',
    'TIR', 'YEKATIT', 'MEGABIT', 'MIAZIA',
    'GINBOT', 'SENE', 'HAMLE', 'NEHASE', 'PAGUME',
]

# Mayan Long Count: an interesting date (13.0.0.0.0 = creation date)
# We'll animate 9.16.4.1.0 as a sample (interesting nonzero digits)
MAYAN_LONG_COUNT = [0, 1, 4, 16, 9]  # kin, uinal, tun, katun, baktun (bottom to top)

CYCLE_ANIM = 4.0   # seconds for animation phase
CYCLE_HOLD = 2.0   # seconds to hold after animation
CYCLE_TOTAL = CYCLE_ANIM + CYCLE_HOLD


class Calendars(Visual):
    name = "CALENDARS"
    description = "Calendar systems of the world"
    category = "culture"

    def reset(self):
        self.time = 0.0
        self.index = 0
        self.anim_timer = 0.0
        self.auto_advance = True
        self.overlay_timer = 0.0
        self.overlay_text = ""
        self._input_cooldown = 0.0

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self, input_state):
        if self._input_cooldown > 0:
            return False
        consumed = False

        if input_state.right_pressed:
            self._go(1)
            consumed = True
        if input_state.left_pressed:
            self._go(-1)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._go(1)
            consumed = True

        if consumed:
            self._input_cooldown = 0.15
        return consumed

    def _go(self, delta):
        self.index = (self.index + delta) % NUM_CALENDARS
        self.anim_timer = 0.0

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt):
        self.time += dt
        if self._input_cooldown > 0:
            self._input_cooldown -= dt
        self.anim_timer += dt

        if self.overlay_timer > 0:
            self.overlay_timer = max(0.0, self.overlay_timer - dt)

        # Auto-advance after cycle completes
        if self.auto_advance and self.anim_timer >= CYCLE_TOTAL:
            self.index = (self.index + 1) % NUM_CALENDARS
            self.anim_timer = 0.0

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self):
        d = self.display
        d.clear()

        cal = CALENDARS[self.index]
        progress = min(1.0, self.anim_timer / CYCLE_ANIM)

        # Header: calendar name
        d.draw_text_small(2, 1, cal['name'], cal['color'])

        # Origin line
        d.draw_text_small(2, 7, cal['origin'], (90, 90, 90))

        # Dispatch to specific draw method
        draw_fn = [
            self._draw_mayan, self._draw_islamic, self._draw_chinese,
            self._draw_hebrew, self._draw_gregorian, self._draw_egyptian,
            self._draw_french, self._draw_ethiopian,
        ][self.index]
        draw_fn(d, progress)

        # Position indicator dots at y=59
        for i in range(NUM_CALENDARS):
            ix = 32 - (NUM_CALENDARS * 3) // 2 + i * 3
            if i == self.index:
                d.set_pixel(ix, 60, (200, 200, 200))
                d.set_pixel(ix + 1, 60, (200, 200, 200))
            else:
                d.set_pixel(ix, 60, (50, 50, 50))

        # Overlay
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(220 * alpha), int(220 * alpha), int(220 * alpha))
            ow = len(self.overlay_text) * 4
            ox = max(0, (64 - ow) // 2)
            d.draw_text_small(ox, 40, self.overlay_text, c)

    # ------------------------------------------------------------------
    # MAYAN - Dot-bar vigesimal notation
    # ------------------------------------------------------------------
    def _draw_mayan(self, d, progress):
        bg = (30, 35, 25)
        stone = (100, 140, 80)
        stone_dim = (60, 85, 50)

        # Fill background area
        d.draw_rect(0, 14, 64, 42, bg, filled=True)

        # How many places to reveal based on progress
        num_places = len(MAYAN_LONG_COUNT)
        places_shown = min(num_places, int(progress * num_places) + 1)
        sub_progress = (progress * num_places) % 1.0 if progress < 1.0 else 1.0

        # Draw from bottom (kin) to top (baktun)
        for i in range(places_shown):
            val = MAYAN_LONG_COUNT[i]
            # y position: bottom-up, each place gets ~9px
            py = 48 - i * 9
            cx = 32  # center x

            if i == places_shown - 1 and progress < 1.0:
                # Animating this place
                self._draw_mayan_numeral(d, cx, py, val, sub_progress, stone)
            else:
                self._draw_mayan_numeral(d, cx, py, val, 1.0, stone)

            # Place label on the right
            labels = ['KIN', 'UINAL', 'TUN', 'KATUN', "B'AKTUN"]
            if i < len(labels):
                d.draw_text_small(44, py - 2, labels[i], stone_dim)

    def _draw_mayan_numeral(self, d, cx, y, value, progress, color):
        """Draw a single Mayan numeral (0-19) at center cx, baseline y."""
        if value == 0:
            # Shell glyph: small oval outline
            if progress > 0.3:
                d.draw_circle(cx, y - 2, 3, color, filled=False)
                d.set_pixel(cx, y - 2, color)
            return

        bars = value // 5
        dots = value % 5

        # Dots on top, bars on bottom
        bar_y = y
        total_bars = int(bars * progress) if progress < 1.0 else bars
        total_dots = int(dots * min(1.0, progress * 2)) if progress < 1.0 else dots

        # Draw bars (each 10px wide, 2px tall)
        for b in range(total_bars):
            by = bar_y - b * 4
            d.draw_rect(cx - 5, by, 10, 2, color, filled=True)

        # Draw dots above bars
        dot_y = bar_y - total_bars * 4 - 1 if total_bars > 0 else bar_y - 1
        dot_spacing = 4
        dot_start_x = cx - ((total_dots - 1) * dot_spacing) // 2
        for dd in range(total_dots):
            dx = dot_start_x + dd * dot_spacing
            d.draw_circle(dx, dot_y, 1, color, filled=True)

    # ------------------------------------------------------------------
    # ISLAMIC - Crescent moon phases
    # ------------------------------------------------------------------
    def _draw_islamic(self, d, progress):
        green = (40, 160, 80)
        gold = (200, 180, 60)
        dark = (10, 25, 15)

        # Crescent animation: phase cycles over time
        phase = (self.time * 0.15) % 1.0  # slow wax/wane cycle
        cx, cy = 32, 32
        r = 12

        # Draw the moon: filled circle then subtract with offset circle
        # Phase 0 = new, 0.5 = full, 1.0 = new again
        # Offset determines crescent thickness
        if phase < 0.5:
            # Waxing: crescent grows
            t = phase * 2.0  # 0 to 1
        else:
            # Waning: crescent shrinks
            t = (1.0 - phase) * 2.0  # 1 to 0

        # Draw filled moon circle
        for py in range(cy - r - 1, cy + r + 2):
            for px in range(cx - r - 1, cx + r + 2):
                dx = px - cx
                dy = py - cy
                if dx * dx + dy * dy <= r * r:
                    # Check if inside the "shadow" circle
                    offset = int((1.0 - t) * r * 1.5) - r // 3
                    sdx = px - (cx + offset)
                    sdy = py - cy
                    shadow_r = r - 1
                    if sdx * sdx + sdy * sdy > shadow_r * shadow_r:
                        # Visible part of moon
                        bright = 0.4 + 0.6 * progress
                        c = (int(gold[0] * bright), int(gold[1] * bright), int(gold[2] * bright))
                        d.set_pixel(px, py, c)

        # Star accent near crescent
        if progress > 0.5:
            sx, sy = cx + 10, cy - 8
            d.set_pixel(sx, sy, gold)
            d.set_pixel(sx - 1, sy, (gold[0] // 2, gold[1] // 2, gold[2] // 2))
            d.set_pixel(sx + 1, sy, (gold[0] // 2, gold[1] // 2, gold[2] // 2))
            d.set_pixel(sx, sy - 1, (gold[0] // 2, gold[1] // 2, gold[2] // 2))
            d.set_pixel(sx, sy + 1, (gold[0] // 2, gold[1] // 2, gold[2] // 2))

        # Month name
        month_idx = int(self.time * 0.3) % 12
        name = ISLAMIC_MONTHS[month_idx]
        # Truncate if too long
        if len(name) > 15:
            name = name[:15]
        d.draw_text_small(2, 50, name, green)

    # ------------------------------------------------------------------
    # CHINESE - Zodiac animal pixel art
    # ------------------------------------------------------------------
    def _draw_chinese(self, d, progress):
        red = (200, 50, 40)
        gold = (220, 190, 60)

        animal_idx = int(self.time * 0.12) % 12
        animal_name = ZODIAC_ANIMALS[animal_idx]
        sprite = ZODIAC_SPRITES[animal_name]

        # Fade in based on progress
        bright = progress

        # Draw sprite centered
        sx = (64 - 12) // 2
        sy = 18

        for row_i, row in enumerate(sprite):
            for col in range(12):
                if row & (1 << (11 - col)):
                    c = (int(gold[0] * bright), int(gold[1] * bright), int(gold[2] * bright))
                    d.set_pixel(sx + col, sy + row_i, c)

        # Frame around sprite
        if progress > 0.3:
            frame_c = (int(red[0] * 0.5), int(red[1] * 0.5), int(red[2] * 0.5))
            d.draw_rect(sx - 2, sy - 2, 16, 16, frame_c, filled=False)

        # Animal name and year
        d.draw_text_small(2, 34, animal_name, red)
        cycle_num = 4721 + animal_idx  # approximate Chinese year
        d.draw_text_small(2, 40, "YEAR %d" % cycle_num, (160, 140, 50))

        # Decorative corner dots
        if progress > 0.6:
            for corner in [(sx - 3, sy - 3), (sx + 13, sy - 3),
                           (sx - 3, sy + 13), (sx + 13, sy + 13)]:
                d.set_pixel(corner[0], corner[1], red)

    # ------------------------------------------------------------------
    # HEBREW - Star of David + month
    # ------------------------------------------------------------------
    def _draw_hebrew(self, d, progress):
        blue = (60, 100, 200)
        white = (220, 220, 230)

        cx, cy = 32, 30
        r = 10

        # Star of David: two overlapping triangles
        # Triangle 1: point up
        # Triangle 2: point down
        pts_up = self._triangle_points(cx, cy, r, pointing_up=True)
        pts_down = self._triangle_points(cx, cy, r, pointing_up=False)

        # Progressively draw the star
        if progress > 0.1:
            alpha = min(1.0, (progress - 0.1) / 0.4)
            c = (int(blue[0] * alpha), int(blue[1] * alpha), int(blue[2] * alpha))
            self._draw_triangle(d, pts_up, c)
        if progress > 0.4:
            alpha = min(1.0, (progress - 0.4) / 0.4)
            c = (int(white[0] * alpha), int(white[1] * alpha), int(white[2] * alpha))
            self._draw_triangle(d, pts_down, c)

        # Month name
        month_idx = int(self.time * 0.25) % 12
        d.draw_text_small(2, 46, HEBREW_MONTHS[month_idx], blue)

        # Lunar phase dots
        if progress > 0.7:
            phase_dots = int((self.time * 0.5) % 8)
            for i in range(8):
                px = 20 + i * 3
                if i <= phase_dots:
                    d.set_pixel(px, 52, white)
                else:
                    d.set_pixel(px, 52, (40, 40, 50))

    def _triangle_points(self, cx, cy, r, pointing_up):
        """Return 3 vertices of an equilateral triangle."""
        if pointing_up:
            angles = [-math.pi / 2, math.pi / 6, 5 * math.pi / 6]
        else:
            angles = [math.pi / 2, -math.pi / 6, -5 * math.pi / 6]
        return [(int(cx + r * math.cos(a)), int(cy + r * math.sin(a))) for a in angles]

    def _draw_triangle(self, d, pts, color):
        """Draw triangle outline from 3 points."""
        for i in range(3):
            x0, y0 = pts[i]
            x1, y1 = pts[(i + 1) % 3]
            d.draw_line(x0, y0, x1, y1, color)

    # ------------------------------------------------------------------
    # GREGORIAN - Standard month grid
    # ------------------------------------------------------------------
    def _draw_gregorian(self, d, progress):
        white = (180, 180, 200)
        dim = (70, 70, 90)
        highlight = (100, 160, 255)

        # Day-of-week header
        days = "SMTWTFS"
        for i, ch in enumerate(days):
            dx = 5 + i * 8
            d.draw_text_small(dx, 15, ch, dim)

        # Grid of days (show February as example, 28 days, starts on Saturday)
        start_dow = 6  # Saturday
        num_days = 28
        today = 16  # "today"

        days_shown = int(num_days * progress)
        for day in range(1, days_shown + 1):
            cell = (day - 1) + start_dow
            col = cell % 7
            row = cell // 7
            px = 5 + col * 8
            py = 21 + row * 7

            if day == today:
                # Highlight box
                d.draw_rect(px - 1, py - 1, 7, 7, highlight, filled=False)
                d.draw_text_small(px, py, str(day), highlight)
            else:
                d.draw_text_small(px, py, str(day), white)

        # Month/year label
        if progress > 0.2:
            d.draw_text_small(2, 50, "FEBRUARY 2026", dim)

    # ------------------------------------------------------------------
    # EGYPTIAN - Three seasons with icons
    # ------------------------------------------------------------------
    def _draw_egyptian(self, d, progress):
        gold = (200, 170, 80)
        sand = (160, 140, 70)

        season_idx = int(self.time * 0.2) % 3
        season = EGYPTIAN_SEASONS[season_idx]
        sc = season['color']

        # Season name and meaning
        d.draw_text_small(2, 15, season['name'], sc)
        d.draw_text_small(2, 21, season['meaning'], sand)

        # Draw season icon in center area
        cx, cy = 32, 36

        if season_idx == 0:
            # AKHET - flood: wavy water lines
            num_waves = int(4 * progress)
            for w in range(num_waves):
                wy = cy - 4 + w * 4
                for px in range(10, 54):
                    wave_y = wy + int(2 * math.sin((px + self.time * 20) * 0.3))
                    bright = 0.5 + 0.5 * math.sin((px + self.time * 15) * 0.2)
                    c = (int(sc[0] * bright), int(sc[1] * bright), int(sc[2] * bright))
                    if 14 <= wave_y <= 52:
                        d.set_pixel(px, wave_y, c)

        elif season_idx == 1:
            # PERET - growing: sprouting plant
            if progress > 0.2:
                # Stem
                stem_h = int(16 * min(1.0, (progress - 0.2) / 0.4))
                for sy in range(stem_h):
                    d.set_pixel(cx, cy + 8 - sy, sc)
            if progress > 0.5:
                # Leaves
                leaf_prog = min(1.0, (progress - 0.5) / 0.3)
                leaf_w = int(5 * leaf_prog)
                leaf_y = cy - 2
                for lx in range(1, leaf_w + 1):
                    d.set_pixel(cx - lx, leaf_y + lx // 2, sc)
                    d.set_pixel(cx + lx, leaf_y + lx // 2, sc)
            if progress > 0.7:
                # Top sprout
                d.set_pixel(cx - 1, cy - 8, sc)
                d.set_pixel(cx, cy - 9, sc)
                d.set_pixel(cx + 1, cy - 8, sc)

        else:
            # SHEMU - harvest: wheat/sun
            if progress > 0.1:
                # Sun circle
                sun_r = int(6 * min(1.0, progress / 0.6))
                d.draw_circle(cx, cy, sun_r, sc, filled=True)
            if progress > 0.5:
                # Sun rays
                num_rays = int(8 * min(1.0, (progress - 0.5) / 0.3))
                for i in range(num_rays):
                    angle = i * math.pi / 4
                    rx = int(cx + 9 * math.cos(angle))
                    ry = int(cy + 9 * math.sin(angle))
                    d.draw_line(cx + int(7 * math.cos(angle)),
                                cy + int(7 * math.sin(angle)),
                                rx, ry, gold)

        # Month count: 12 x 30 + 5
        d.draw_text_small(2, 50, "12x30 + 5 DAYS", sand)

    # ------------------------------------------------------------------
    # FRENCH REPUBLICAN - Decimal clock
    # ------------------------------------------------------------------
    def _draw_french(self, d, progress):
        blue = (50, 80, 200)
        white = (200, 200, 220)
        red = (200, 50, 50)

        cx, cy = 32, 33
        r = 14

        # Clock face outline
        if progress > 0.1:
            d.draw_circle(cx, cy, r, blue, filled=False)

        # 10 hour markers
        if progress > 0.2:
            markers_shown = int(10 * min(1.0, (progress - 0.2) / 0.4))
            for i in range(markers_shown):
                angle = i * math.pi * 2 / 10 - math.pi / 2
                mx = int(cx + (r - 2) * math.cos(angle))
                my = int(cy + (r - 2) * math.sin(angle))
                d.set_pixel(mx, my, white)
                # Outer tick
                ox = int(cx + (r + 1) * math.cos(angle))
                oy = int(cy + (r + 1) * math.sin(angle))
                d.set_pixel(ox, oy, blue)

        # Hour hand (decimal time: 10 hours in a day)
        if progress > 0.5:
            dec_hour = (self.time * 0.05) % 10
            h_angle = dec_hour * math.pi * 2 / 10 - math.pi / 2
            hx = int(cx + 8 * math.cos(h_angle))
            hy = int(cy + 8 * math.sin(h_angle))
            d.draw_line(cx, cy, hx, hy, white)

        # Minute hand
        if progress > 0.6:
            dec_min = (self.time * 0.5) % 100
            m_angle = dec_min * math.pi * 2 / 100 - math.pi / 2
            mx = int(cx + 11 * math.cos(m_angle))
            my = int(cy + 11 * math.sin(m_angle))
            d.draw_line(cx, cy, mx, my, red)

        # Center dot
        if progress > 0.5:
            d.set_pixel(cx, cy, white)

        # Month name
        month_idx = int(self.time * 0.15) % 12
        name = FRENCH_MONTHS[month_idx]
        if len(name) > 15:
            name = name[:15]
        d.draw_text_small(2, 52, name, blue)

        # Tricolor accent at top
        if progress > 0.8:
            for i in range(3):
                colors = [blue, white, red]
                d.set_pixel(30 + i * 2, 16, colors[i])

    # ------------------------------------------------------------------
    # ETHIOPIAN - 13-month calendar
    # ------------------------------------------------------------------
    def _draw_ethiopian(self, d, progress):
        green = (60, 160, 60)
        gold = (200, 180, 60)
        dim = (50, 80, 50)

        # Draw 13 month blocks in a grid: 4 cols x 4 rows (last row has 1)
        months_shown = int(13 * progress)

        for i in range(months_shown):
            col = i % 4
            row = i // 4
            bx = 4 + col * 15
            by = 16 + row * 10

            is_pagume = (i == 12)

            if is_pagume:
                # Special highlight for 13th month
                d.draw_rect(bx, by, 13, 8, gold, filled=False)
                d.draw_text_small(bx + 1, by + 1, "P", gold)
                d.draw_text_small(bx + 1, by + 1, "13", gold)
            else:
                month_c = green if (i % 2 == 0) else dim
                d.draw_rect(bx, by, 13, 8, month_c, filled=False)
                # Month number
                d.draw_text_small(bx + 2, by + 2, str(i + 1), month_c)

        # Current month name
        m_idx = int(self.time * 0.2) % 13
        name = ETHIOPIAN_MONTHS[m_idx]
        if len(name) > 15:
            name = name[:15]

        c = gold if m_idx == 12 else green
        d.draw_text_small(2, 52, name, c)

        # Days note
        if progress > 0.8:
            note = "5 EXTRA" if m_idx == 12 else "30 DAYS"
            d.draw_text_small(36, 52, note, dim)

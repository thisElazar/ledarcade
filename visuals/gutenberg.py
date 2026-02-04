"""
Gutenberg Press
===============
Front view of a screw press with inking roller, sliding type bed,
and visible printed pages. The handle swings dramatically during press.

5-phase cycle: ink roller sweeps type -> bed slides in -> screw turns /
platen descends with handle swing -> impression flash -> platen rises /
bed slides out with printed page.

Controls:
  Left/Right - Adjust press speed (6 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---
OAK_COLOR = (100, 65, 25)
OAK_DARK = (70, 45, 15)
OAK_LIGHT = (130, 85, 35)
OAK_EDGE = (60, 40, 12)

IRON_COLOR = (140, 140, 150)
IRON_DARK = (100, 100, 110)
IRON_BRIGHT = (180, 180, 190)

SCREW_COLOR = (160, 160, 170)
SCREW_THREAD = (120, 120, 130)
SCREW_HIGHLIGHT = (200, 200, 210)

HANDLE_COLOR = (170, 140, 50)
HANDLE_BRIGHT = (210, 180, 70)
HANDLE_KNOB = (220, 190, 80)

PLATEN_COLOR = (160, 160, 170)
PLATEN_DARK = (120, 120, 130)

BED_COLOR = (80, 55, 25)
BED_DARK = (55, 38, 18)
TYPE_BLOCK = (50, 50, 55)
TYPE_BRIGHT = (80, 80, 90)
INK_COLOR = (20, 20, 30)

ROLLER_COLOR = (40, 40, 50)
ROLLER_BRIGHT = (60, 60, 75)
INK_WET = (10, 10, 20)

RAIL_COLOR = (110, 110, 120)

PAPER_COLOR = (220, 210, 190)
PAPER_SHADOW = (190, 180, 160)
PRINTED_INK = (30, 25, 15)

IMPRESSION_FLASH = (255, 255, 220)

HUD_COLOR = (160, 160, 170)

# --- Layout ---
LEFT_POST_X = 8
RIGHT_POST_X = 52
POST_WIDTH = 4
POST_TOP = 6
POST_BOTTOM = 52

CROSSBEAM_Y = 6
CROSSBEAM_HEIGHT = 4

SCREW_CX = 32
SCREW_WIDTH = 4
SCREW_TOP = CROSSBEAM_Y + CROSSBEAM_HEIGHT
SCREW_PITCH = 6

HANDLE_Y = CROSSBEAM_Y + 1
HANDLE_HALF = 16

PLATEN_WIDTH = 32
PLATEN_HEIGHT = 3
PLATEN_HOME_Y = 18
PLATEN_DOWN_Y = 36

RAIL_Y = 40
BED_WIDTH = 30
BED_HEIGHT = 4
BED_HOME_X = -BED_WIDTH
BED_IN_X = SCREW_CX - BED_WIDTH // 2

# Inking roller
ROLLER_R = 2

# Paper output area
PAPER_Y = 46
PAPER_LEFT = LEFT_POST_X + POST_WIDTH + 1
PAPER_RIGHT = RIGHT_POST_X - 1

# Speed
SPEED_CPMS = [2, 4, 8, 12, 18, 24]

# 5 phases
PHASE_INK = 0
PHASE_BED_IN = 1
PHASE_PRESS = 2
PHASE_IMPRESS = 3
PHASE_RISE_OUT = 4

PHASE_FRACS = [0.12, 0.13, 0.30, 0.08, 0.37]

# Text lines to "print" (cycle through)
PRINT_LINES = [
    [1, 1, 0, 1, 1, 1, 0, 1, 0, 1, 1, 0, 1],
    [1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
    [0, 1, 1, 1, 0, 1, 0, 1, 1, 1, 0, 1, 0],
]


class GutenbergPress(Visual):
    name = "GUTENBERG"
    description = "Printing press"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3
        self.cycle_phase = 0.0
        self.screw_angle = 0.0
        self.platen_y = PLATEN_HOME_Y
        self.bed_x = BED_HOME_X
        self.impression_flash = 0.0
        self.handle_swing = 0.0  # -1 to 1 (left to right swing)
        self.roller_x = 0.0  # inking roller position (0..1 across bed)
        self.print_count = 0
        self.last_cycle_id = 0
        self.printed_pages = []  # list of page line patterns

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        cpm = SPEED_CPMS[self.speed_level - 1]
        cycle_period = 60.0 / cpm
        phase_speed = 1.0 / cycle_period

        self.cycle_phase += phase_speed * dt
        cycle_id = int(self.cycle_phase)
        if cycle_id != self.last_cycle_id:
            self.last_cycle_id = cycle_id
            self.print_count += 1
            # Store the page pattern
            pattern = PRINT_LINES[self.print_count % len(PRINT_LINES)]
            self.printed_pages.append(pattern)
            if len(self.printed_pages) > 5:
                self.printed_pages = self.printed_pages[-5:]

        frac = self.cycle_phase - int(self.cycle_phase)

        # Determine sub-phase
        cumulative = 0.0
        phase = 0
        local_t = 0.0
        for i, pf in enumerate(PHASE_FRACS):
            if frac < cumulative + pf:
                phase = i
                local_t = (frac - cumulative) / pf
                break
            cumulative += pf
        else:
            phase = len(PHASE_FRACS) - 1
            local_t = 1.0

        eased = 0.5 - 0.5 * math.cos(math.pi * local_t)

        if phase == PHASE_INK:
            # Inking roller sweeps across bed (bed is off-screen)
            self.roller_x = eased
            self.bed_x = BED_HOME_X
            self.platen_y = PLATEN_HOME_Y
            self.handle_swing = 0.0
            self.impression_flash = 0.0

        elif phase == PHASE_BED_IN:
            self.roller_x = -1.0  # hidden
            self.bed_x = BED_HOME_X + (BED_IN_X - BED_HOME_X) * eased
            self.platen_y = PLATEN_HOME_Y
            self.handle_swing = 0.0

        elif phase == PHASE_PRESS:
            self.bed_x = BED_IN_X
            self.platen_y = PLATEN_HOME_Y + (PLATEN_DOWN_Y - PLATEN_HOME_Y) * eased
            # Handle swings from right to left during press
            self.handle_swing = 1.0 - 2.0 * eased
            # Screw rotates
            self.screw_angle += dt * cpm * 0.8
            if local_t > 0.92:
                self.impression_flash = (local_t - 0.92) / 0.08

        elif phase == PHASE_IMPRESS:
            self.bed_x = BED_IN_X
            self.platen_y = PLATEN_DOWN_Y
            self.impression_flash = 1.0 - eased
            self.handle_swing = -1.0

        elif phase == PHASE_RISE_OUT:
            self.impression_flash = 0.0
            if local_t < 0.45:
                # Platen rises, handle swings back
                rise_t = local_t / 0.45
                rise_e = 0.5 - 0.5 * math.cos(math.pi * rise_t)
                self.platen_y = PLATEN_DOWN_Y + (PLATEN_HOME_Y - PLATEN_DOWN_Y) * rise_e
                self.bed_x = BED_IN_X
                self.handle_swing = -1.0 + rise_e
                self.screw_angle -= dt * cpm * 0.8
            else:
                # Bed slides out
                out_t = (local_t - 0.45) / 0.55
                out_e = 0.5 - 0.5 * math.cos(math.pi * out_t)
                self.platen_y = PLATEN_HOME_Y
                self.bed_x = BED_IN_X + (BED_HOME_X - BED_IN_X) * out_e
                self.handle_swing = 0.0

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        self._draw_frame(d)
        self._draw_rails(d)
        self._draw_bed(d)
        self._draw_screw(d)
        self._draw_platen(d)
        self._draw_handle(d)
        self._draw_roller(d)
        self._draw_impression(d)
        self._draw_pages(d)
        self._draw_hud(d)

    def _draw_frame(self, d):
        # Left post
        d.draw_rect(LEFT_POST_X, POST_TOP, POST_WIDTH, POST_BOTTOM - POST_TOP, OAK_COLOR)
        d.draw_line(LEFT_POST_X, POST_TOP, LEFT_POST_X, POST_BOTTOM - 1, OAK_LIGHT)
        d.draw_line(LEFT_POST_X + POST_WIDTH - 1, POST_TOP,
                     LEFT_POST_X + POST_WIDTH - 1, POST_BOTTOM - 1, OAK_DARK)

        # Right post
        d.draw_rect(RIGHT_POST_X, POST_TOP, POST_WIDTH, POST_BOTTOM - POST_TOP, OAK_COLOR)
        d.draw_line(RIGHT_POST_X, POST_TOP, RIGHT_POST_X, POST_BOTTOM - 1, OAK_LIGHT)
        d.draw_line(RIGHT_POST_X + POST_WIDTH - 1, POST_TOP,
                     RIGHT_POST_X + POST_WIDTH - 1, POST_BOTTOM - 1, OAK_DARK)

        # Crossbeam
        beam_l = LEFT_POST_X
        beam_r = RIGHT_POST_X + POST_WIDTH
        d.draw_rect(beam_l, CROSSBEAM_Y, beam_r - beam_l, CROSSBEAM_HEIGHT, OAK_COLOR)
        d.draw_line(beam_l, CROSSBEAM_Y, beam_r - 1, CROSSBEAM_Y, OAK_LIGHT)
        d.draw_line(beam_l, CROSSBEAM_Y + CROSSBEAM_HEIGHT - 1,
                     beam_r - 1, CROSSBEAM_Y + CROSSBEAM_HEIGHT - 1, OAK_DARK)

        # Base
        d.draw_rect(LEFT_POST_X - 2, POST_BOTTOM, RIGHT_POST_X + POST_WIDTH - LEFT_POST_X + 4,
                     3, OAK_COLOR)
        d.draw_line(LEFT_POST_X - 2, POST_BOTTOM, RIGHT_POST_X + POST_WIDTH + 1,
                     POST_BOTTOM, OAK_LIGHT)

    def _draw_screw(self, d):
        sl = SCREW_CX - SCREW_WIDTH // 2
        sr = SCREW_CX + SCREW_WIDTH // 2
        sb = int(self.platen_y)

        thread_off = (self.screw_angle / (2.0 * math.pi)) * SCREW_PITCH

        for y in range(SCREW_TOP, sb):
            for x in range(sl, sr + 1):
                stripe = (y + thread_off + (x - sl) * 1.5) % SCREW_PITCH
                if x == sl or x == sr:
                    d.set_pixel(x, y, IRON_DARK)
                elif stripe < SCREW_PITCH * 0.4:
                    d.set_pixel(x, y, SCREW_THREAD)
                else:
                    d.set_pixel(x, y, SCREW_COLOR)
        for y in range(SCREW_TOP, sb):
            d.set_pixel(SCREW_CX, y, SCREW_HIGHLIGHT)

    def _draw_platen(self, d):
        py = int(self.platen_y)
        pl = SCREW_CX - PLATEN_WIDTH // 2
        pr = SCREW_CX + PLATEN_WIDTH // 2
        d.draw_rect(pl, py, PLATEN_WIDTH, PLATEN_HEIGHT, PLATEN_COLOR)
        d.draw_line(pl, py, pr - 1, py, IRON_BRIGHT)
        d.draw_line(pl, py + PLATEN_HEIGHT - 1, pr - 1, py + PLATEN_HEIGHT - 1, PLATEN_DARK)
        # Guide brackets
        d.draw_line(pl, py + 1, LEFT_POST_X + POST_WIDTH, py + 1, IRON_DARK)
        d.draw_line(pr, py + 1, RIGHT_POST_X - 1, py + 1, IRON_DARK)

    def _draw_handle(self, d):
        # Handle swings left/right: swing = -1 (full left) to +1 (full right)
        offset = self.handle_swing * HANDLE_HALF * 0.6

        hy = HANDLE_Y
        hl = int(SCREW_CX - HANDLE_HALF + offset)
        hr = int(SCREW_CX + HANDLE_HALF + offset)
        hl = max(1, hl)
        hr = min(62, hr)

        d.draw_line(hl, hy, hr, hy, HANDLE_COLOR)
        d.draw_line(hl, hy + 1, hr, hy + 1, HANDLE_BRIGHT)

        # Knobs
        for dy in range(2):
            d.set_pixel(hl - 1, hy + dy, HANDLE_KNOB)
            d.set_pixel(hr + 1, hy + dy, HANDLE_KNOB)

        # Hub
        d.set_pixel(SCREW_CX, hy, IRON_BRIGHT)

    def _draw_rails(self, d):
        rl = LEFT_POST_X + POST_WIDTH
        rr = RIGHT_POST_X - 1
        d.draw_line(rl, RAIL_Y, rr, RAIL_Y, RAIL_COLOR)
        d.draw_line(rl, RAIL_Y + BED_HEIGHT + 1, rr, RAIL_Y + BED_HEIGHT + 1, RAIL_COLOR)

    def _draw_bed(self, d):
        bx = int(self.bed_x)
        by = RAIL_Y + 1

        if bx + BED_WIDTH <= 0 or bx >= GRID_SIZE:
            return

        dl = max(0, bx)
        dr = min(GRID_SIZE - 1, bx + BED_WIDTH - 1)

        d.draw_rect(dl, by, dr - dl + 1, BED_HEIGHT, BED_COLOR)
        d.draw_line(dl, by, dr, by, BED_DARK)

        # Type blocks
        for tx in range(bx + 2, bx + BED_WIDTH - 2, 2):
            if 0 <= tx < GRID_SIZE and tx + 1 < GRID_SIZE:
                for ty in range(by + 1, by + BED_HEIGHT - 1):
                    d.set_pixel(tx, ty, TYPE_BLOCK)
                    d.set_pixel(tx + 1, ty, TYPE_BRIGHT)

        # Ink on top of type blocks
        for ix in range(dl + 1, dr):
            if (ix + int(self.time * 3)) % 2 == 0:
                d.set_pixel(ix, by + 1, INK_COLOR)

    def _draw_roller(self, d):
        """Draw inking roller sweeping across the bed."""
        if self.roller_x < 0:
            return
        # Roller position: centered off-screen at bed's home position
        # roller_x: 0..1 maps across bed width
        rx = int(BED_HOME_X + 2 + self.roller_x * (BED_WIDTH - 4))
        ry = RAIL_Y  # on top of the bed

        if rx < 0 or rx >= GRID_SIZE:
            return

        # Roller circle
        for dy in range(-ROLLER_R, ROLLER_R + 1):
            for dx in range(-ROLLER_R, ROLLER_R + 1):
                if dx * dx + dy * dy <= ROLLER_R * ROLLER_R:
                    px = rx + dx
                    py = ry + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        d.set_pixel(px, py, ROLLER_COLOR if dy < 0 else ROLLER_BRIGHT)

        # Ink trail behind roller
        trail_end = max(0, rx - 6)
        for tx in range(trail_end, rx):
            if 0 <= tx < GRID_SIZE:
                d.set_pixel(tx, ry + 1, INK_WET)

    def _draw_impression(self, d):
        if self.impression_flash <= 0.01:
            return

        b = self.impression_flash
        fr = int(IMPRESSION_FLASH[0] * b)
        fg = int(IMPRESSION_FLASH[1] * b)
        fb = int(IMPRESSION_FLASH[2] * b)

        # Wide flash across the impression zone
        flash_y = int(self.platen_y) + PLATEN_HEIGHT
        bed_cx = int(self.bed_x) + BED_WIDTH // 2
        for dx in range(-12, 13):
            fx = bed_cx + dx
            if 0 <= fx < GRID_SIZE:
                fade = 1.0 - abs(dx) / 13.0
                r = min(255, int(fr * fade))
                g = min(255, int(fg * fade))
                b2 = min(255, int(fb * fade))
                d.set_pixel(fx, flash_y, (r, g, b2))
                if flash_y + 1 < GRID_SIZE:
                    d.set_pixel(fx, flash_y + 1, (r // 2, g // 2, b2 // 2))
                if flash_y - 1 >= 0:
                    d.set_pixel(fx, flash_y - 1, (r // 3, g // 3, b2 // 3))

    def _draw_pages(self, d):
        """Draw printed pages stacking up in the output area."""
        if not self.printed_pages:
            return

        for i, pattern in enumerate(self.printed_pages[-3:]):
            py = PAPER_Y + i * 3
            if py + 2 >= GRID_SIZE:
                break
            offset = i

            # Paper sheet
            pl = PAPER_LEFT + offset
            pr = PAPER_RIGHT - offset
            d.draw_line(pl, py, pr, py, PAPER_COLOR)
            d.draw_line(pl, py + 1, pr, py + 1, PAPER_SHADOW)

            # Printed text marks on the page
            for j, has_ink in enumerate(pattern):
                tx = pl + 2 + j * 2
                if has_ink and tx < pr:
                    d.set_pixel(tx, py, PRINTED_INK)
                    if tx + 1 < pr:
                        d.set_pixel(tx + 1, py, PRINTED_INK)

        # Page counter
        d.draw_text_small(2, 58, f"PG {self.print_count}", HUD_COLOR)

    def _draw_hud(self, d):
        ppm = SPEED_CPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{ppm} PPM", HUD_COLOR)

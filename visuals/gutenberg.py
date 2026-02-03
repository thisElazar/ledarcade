"""
Gutenberg Press
===============
Front view of a screw press. A central screw with visible thread lines
drives a platen up and down. The type bed slides in on rails for each
impression cycle.

4-phase cycle: bed rolls in -> screw turns / platen descends ->
impression flash -> platen rises -> bed rolls out.

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
HANDLE_KNOB = (200, 170, 60)

PLATEN_COLOR = (160, 160, 170)
PLATEN_DARK = (120, 120, 130)

BED_COLOR = (80, 55, 25)
BED_DARK = (55, 38, 18)
TYPE_BLOCK = (50, 50, 55)
TYPE_BRIGHT = (80, 80, 90)
INK_COLOR = (20, 20, 25)

RAIL_COLOR = (110, 110, 120)

PAPER_COLOR = (220, 210, 190)
PAPER_PRINTED = (40, 30, 20)

IMPRESSION_FLASH = (255, 255, 220)

HUD_COLOR = (160, 160, 170)

# --- Layout Constants ---
LEFT_POST_X = 10
RIGHT_POST_X = 50
POST_WIDTH = 4
POST_TOP = 6
POST_BOTTOM = 54

CROSSBEAM_Y = 6
CROSSBEAM_HEIGHT = 4

SCREW_CX = 32
SCREW_WIDTH = 4
SCREW_TOP = CROSSBEAM_Y + CROSSBEAM_HEIGHT
SCREW_PITCH = 6  # pixels per full thread revolution

HANDLE_Y = CROSSBEAM_Y + 1
HANDLE_HALF = 14  # half-width of handle bar

PLATEN_WIDTH = 30
PLATEN_HEIGHT = 4
PLATEN_HOME_Y = 18  # top position
PLATEN_DOWN_Y = 38  # bottom position (impression)

RAIL_Y = 43
BED_WIDTH = 28
BED_HEIGHT = 5
BED_HOME_X = -BED_WIDTH  # off-screen left when retracted
BED_IN_X = SCREW_CX - BED_WIDTH // 2  # centered under platen

PAPER_STACK_Y = 48
PAPER_STACK_LEFT = LEFT_POST_X + POST_WIDTH + 2
PAPER_STACK_RIGHT = RIGHT_POST_X - 2

# Speed levels: cycles per minute
SPEED_CPMS = [2, 4, 8, 12, 18, 24]

# Phase durations (fractions of one full cycle)
PHASE_BED_IN = 0  # bed rolls in
PHASE_PRESS = 1   # screw turns, platen descends
PHASE_IMPRESS = 2  # impression flash
PHASE_RISE = 3    # platen rises, bed rolls out

PHASE_FRACS = [0.20, 0.30, 0.10, 0.40]  # must sum to 1.0


class GutenbergPress(Visual):
    name = "GUTENBERG"
    description = "Printing press"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3  # 1-6
        self.cycle_phase = 0.0  # 0.0 to 1.0 within current cycle
        self.screw_angle = 0.0  # continuous rotation angle
        self.platen_y = PLATEN_HOME_Y
        self.bed_x = BED_HOME_X
        self.impression_flash = 0.0
        self.handle_angle = 0.0
        self.print_count = 0
        self.last_cycle_id = 0

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
        phase_speed = 1.0 / cycle_period  # phase units per second

        self.cycle_phase += phase_speed * dt
        cycle_id = int(self.cycle_phase)
        if cycle_id != self.last_cycle_id:
            self.last_cycle_id = cycle_id
            self.print_count += 1

        frac = self.cycle_phase - int(self.cycle_phase)  # 0.0 to 1.0

        # Determine which sub-phase we're in
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

        # Smooth easing
        eased = 0.5 - 0.5 * math.cos(math.pi * local_t)

        if phase == PHASE_BED_IN:
            # Bed slides in from left
            self.bed_x = BED_HOME_X + (BED_IN_X - BED_HOME_X) * eased
            self.platen_y = PLATEN_HOME_Y
            self.screw_angle = self.handle_angle  # no rotation

        elif phase == PHASE_PRESS:
            # Platen descends, screw rotates
            self.bed_x = BED_IN_X
            self.platen_y = PLATEN_HOME_Y + (PLATEN_DOWN_Y - PLATEN_HOME_Y) * eased
            # Screw rotates during press
            self.screw_angle = self.handle_angle + eased * 4.0 * math.pi
            self.handle_angle = self.screw_angle
            if local_t > 0.9:
                self.impression_flash = (local_t - 0.9) / 0.1

        elif phase == PHASE_IMPRESS:
            # Hold at bottom, flash
            self.bed_x = BED_IN_X
            self.platen_y = PLATEN_DOWN_Y
            self.impression_flash = 1.0 - eased

        elif phase == PHASE_RISE:
            # Platen rises, then bed slides out
            self.impression_flash = 0.0
            if local_t < 0.5:
                # First half: platen rises
                rise_t = local_t / 0.5
                rise_eased = 0.5 - 0.5 * math.cos(math.pi * rise_t)
                self.platen_y = PLATEN_DOWN_Y + (PLATEN_HOME_Y - PLATEN_DOWN_Y) * rise_eased
                self.bed_x = BED_IN_X
                # Screw rotates back
                self.screw_angle = self.handle_angle - rise_eased * 4.0 * math.pi
            else:
                # Second half: bed slides out
                out_t = (local_t - 0.5) / 0.5
                out_eased = 0.5 - 0.5 * math.cos(math.pi * out_t)
                self.platen_y = PLATEN_HOME_Y
                self.bed_x = BED_IN_X + (BED_HOME_X - BED_IN_X) * out_eased

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        self._draw_frame(d)
        self._draw_rails(d)
        self._draw_bed(d)
        self._draw_paper_stack(d)
        self._draw_screw(d)
        self._draw_platen(d)
        self._draw_handle(d)
        self._draw_impression(d)
        self._draw_hud(d)

    def _draw_frame(self, d):
        """Draw the oak frame: two posts and crossbeam."""
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
        beam_left = LEFT_POST_X
        beam_right = RIGHT_POST_X + POST_WIDTH
        d.draw_rect(beam_left, CROSSBEAM_Y, beam_right - beam_left,
                     CROSSBEAM_HEIGHT, OAK_COLOR)
        d.draw_line(beam_left, CROSSBEAM_Y, beam_right - 1, CROSSBEAM_Y, OAK_LIGHT)
        d.draw_line(beam_left, CROSSBEAM_Y + CROSSBEAM_HEIGHT - 1,
                     beam_right - 1, CROSSBEAM_Y + CROSSBEAM_HEIGHT - 1, OAK_DARK)

        # Base
        d.draw_rect(LEFT_POST_X - 2, POST_BOTTOM, RIGHT_POST_X + POST_WIDTH - LEFT_POST_X + 4,
                     3, OAK_COLOR)
        d.draw_line(LEFT_POST_X - 2, POST_BOTTOM, RIGHT_POST_X + POST_WIDTH + 1,
                     POST_BOTTOM, OAK_LIGHT)

    def _draw_screw(self, d):
        """Draw the central screw with rotating thread pattern."""
        screw_left = SCREW_CX - SCREW_WIDTH // 2
        screw_right = SCREW_CX + SCREW_WIDTH // 2
        screw_bot = int(self.platen_y)

        # Thread offset from rotation
        thread_offset = (self.screw_angle / (2.0 * math.pi)) * SCREW_PITCH

        for y in range(SCREW_TOP, screw_bot):
            for x in range(screw_left, screw_right + 1):
                # Diagonal stripe pattern for thread illusion
                stripe = (y + thread_offset + (x - screw_left) * 1.5) % SCREW_PITCH
                if x == screw_left or x == screw_right:
                    d.set_pixel(x, y, IRON_DARK)
                elif stripe < SCREW_PITCH * 0.4:
                    d.set_pixel(x, y, SCREW_THREAD)
                else:
                    d.set_pixel(x, y, SCREW_COLOR)

        # Center highlight
        for y in range(SCREW_TOP, screw_bot):
            d.set_pixel(SCREW_CX, y, SCREW_HIGHLIGHT)

    def _draw_platen(self, d):
        """Draw the pressing platen."""
        py = int(self.platen_y)
        platen_left = SCREW_CX - PLATEN_WIDTH // 2
        platen_right = SCREW_CX + PLATEN_WIDTH // 2

        d.draw_rect(platen_left, py, PLATEN_WIDTH, PLATEN_HEIGHT, PLATEN_COLOR)
        # Top highlight
        d.draw_line(platen_left, py, platen_right - 1, py, IRON_BRIGHT)
        # Bottom edge
        d.draw_line(platen_left, py + PLATEN_HEIGHT - 1,
                     platen_right - 1, py + PLATEN_HEIGHT - 1, PLATEN_DARK)
        # Side brackets connecting to posts
        d.draw_line(platen_left, py + 1, LEFT_POST_X + POST_WIDTH, py + 1, IRON_DARK)
        d.draw_line(platen_right, py + 1, RIGHT_POST_X - 1, py + 1, IRON_DARK)

    def _draw_handle(self, d):
        """Draw the horizontal press handle at the top."""
        # Handle rotates with screw (shown as horizontal bar that shifts)
        handle_offset = math.sin(self.screw_angle) * 3  # subtle oscillation

        hy = HANDLE_Y
        h_left = int(SCREW_CX - HANDLE_HALF + handle_offset)
        h_right = int(SCREW_CX + HANDLE_HALF + handle_offset)

        # Clamp to screen
        h_left = max(1, h_left)
        h_right = min(62, h_right)

        d.draw_line(h_left, hy, h_right, hy, HANDLE_COLOR)
        d.draw_line(h_left, hy + 1, h_right, hy + 1, HANDLE_BRIGHT)

        # Handle knobs at ends
        d.set_pixel(h_left - 1, hy, HANDLE_KNOB)
        d.set_pixel(h_left - 1, hy + 1, HANDLE_KNOB)
        d.set_pixel(h_right + 1, hy, HANDLE_KNOB)
        d.set_pixel(h_right + 1, hy + 1, HANDLE_KNOB)

        # Central hub where handle meets screw
        d.set_pixel(SCREW_CX, hy, IRON_BRIGHT)
        d.set_pixel(SCREW_CX - 1, hy, IRON_COLOR)
        d.set_pixel(SCREW_CX + 1, hy, IRON_COLOR)

    def _draw_rails(self, d):
        """Draw the bed rails."""
        rail_left = LEFT_POST_X + POST_WIDTH
        rail_right = RIGHT_POST_X - 1
        d.draw_line(rail_left, RAIL_Y, rail_right, RAIL_Y, RAIL_COLOR)
        d.draw_line(rail_left, RAIL_Y + BED_HEIGHT + 1, rail_right,
                     RAIL_Y + BED_HEIGHT + 1, RAIL_COLOR)

    def _draw_bed(self, d):
        """Draw the sliding type bed with type blocks."""
        bx = int(self.bed_x)
        by = RAIL_Y + 1

        # Bed base
        if bx + BED_WIDTH > 0 and bx < GRID_SIZE:
            draw_left = max(0, bx)
            draw_right = min(GRID_SIZE - 1, bx + BED_WIDTH - 1)

            d.draw_rect(draw_left, by, draw_right - draw_left + 1, BED_HEIGHT, BED_COLOR)
            d.draw_line(draw_left, by, draw_right, by, BED_DARK)

            # Type blocks on the bed (small raised rectangles)
            for tx in range(bx + 2, bx + BED_WIDTH - 2, 3):
                if 0 <= tx < GRID_SIZE and tx + 1 < GRID_SIZE:
                    for ty in range(by + 1, by + BED_HEIGHT - 1):
                        d.set_pixel(tx, ty, TYPE_BLOCK)
                        d.set_pixel(tx + 1, ty, TYPE_BRIGHT)

            # Ink on top of type
            ink_y = by + 1
            for ix in range(draw_left + 1, draw_right):
                if (ix + int(self.time * 2)) % 3 == 0:
                    d.set_pixel(ix, ink_y, INK_COLOR)

    def _draw_paper_stack(self, d):
        """Draw a small paper stack below the press area."""
        stack_left = PAPER_STACK_LEFT
        stack_right = PAPER_STACK_RIGHT

        # Multiple sheets slightly offset
        for i in range(min(3, self.print_count + 1)):
            py = PAPER_STACK_Y + i * 2
            if py >= GRID_SIZE:
                break
            offset = i
            d.draw_line(stack_left + offset, py,
                         stack_right - offset, py, PAPER_COLOR)
            # Printed text marks
            if i < self.print_count:
                for tx in range(stack_left + offset + 2, stack_right - offset - 1, 4):
                    d.set_pixel(tx, py, PAPER_PRINTED)
                    if tx + 1 < stack_right - offset:
                        d.set_pixel(tx + 1, py, PAPER_PRINTED)

    def _draw_impression(self, d):
        """Draw impression flash when platen presses."""
        if self.impression_flash <= 0.01:
            return

        bright = self.impression_flash
        fr = int(IMPRESSION_FLASH[0] * bright)
        fg = int(IMPRESSION_FLASH[1] * bright)
        fb = int(IMPRESSION_FLASH[2] * bright)
        flash = (min(255, fr), min(255, fg), min(255, fb))

        # Flash across the impression zone
        flash_y = int(self.platen_y) + PLATEN_HEIGHT
        bed_center = int(self.bed_x) + BED_WIDTH // 2
        for dx in range(-8, 9):
            fx = bed_center + dx
            if 0 <= fx < GRID_SIZE:
                fade = 1.0 - abs(dx) / 9.0
                r = int(fr * fade)
                g = int(fg * fade)
                b = int(fb * fade)
                d.set_pixel(fx, flash_y, (min(255, r), min(255, g), min(255, b)))
                if flash_y + 1 < GRID_SIZE:
                    r2 = int(r * 0.5)
                    g2 = int(g * 0.5)
                    b2 = int(b * 0.5)
                    d.set_pixel(fx, flash_y + 1, (r2, g2, b2))

    def _draw_hud(self, d):
        """Draw speed indicator."""
        cpm = SPEED_CPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{cpm} CPM", HUD_COLOR)

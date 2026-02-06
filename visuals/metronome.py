"""
Metronome
=========
Classic mechanical metronome with swinging arm and adjustable BPM.

Controls:
  Left/Right - Adjust BPM by 1
  Up/Down    - Adjust BPM by 10
  Button     - Cycle time signature (2, 3, 4, 5)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Colors
WOOD_DARK = (100, 60, 20)
WOOD_MID = (140, 85, 30)
WOOD_LIGHT = (170, 110, 50)
METAL_ARM = (200, 200, 210)
METAL_WEIGHT = (180, 180, 190)
WEIGHT_HIGHLIGHT = (220, 220, 230)
FLASH_COLOR = (255, 255, 200)
BPM_COLOR = (220, 200, 160)
BEAT_ON = (255, 20, 20)
BEAT_DIM = (60, 10, 10)
BEAT_TEXT = (255, 60, 60)


class Metronome(Visual):
    name = "METRONOME"
    description = "Mechanical metronome"
    category = "music"

    # Layout
    PIVOT_X = 32
    PIVOT_Y = 48
    ARM_LENGTH = 40
    MAX_ANGLE = 0.45  # radians (~26 degrees)

    # Body trapezoid
    BODY_TOP = 22
    BODY_BOT = 60
    BODY_TOP_HALF = 10   # half-width at top
    BODY_BOT_HALF = 16   # half-width at bottom

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.bpm = 120
        self.beat_phase = 0.0
        self.last_beat_id = 0
        self.flash_timer = 0.0
        self.time_sig = 4        # beats per measure
        self.beat_in_measure = 1  # 1-based current beat
        self.beat_flash = 0.0     # red blink decay timer

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.bpm = min(240, self.bpm + 1)
            consumed = True
        elif input_state.left_pressed:
            self.bpm = max(20, self.bpm - 1)
            consumed = True
        if input_state.up_pressed:
            self.bpm = min(240, self.bpm + 10)
            consumed = True
        elif input_state.down_pressed:
            self.bpm = max(20, self.bpm - 10)
            consumed = True
        if input_state.action_l or input_state.action_r:
            # Cycle time signature: 2 -> 3 -> 4 -> 5 -> 2
            self.time_sig = (self.time_sig - 1) % 4 + 2
            self.beat_in_measure = 1
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Advance beat phase
        self.beat_phase += (self.bpm / 60.0) * dt

        # Detect beat (integer crossing)
        beat_id = int(self.beat_phase)
        if beat_id != self.last_beat_id:
            self.flash_timer = 0.1
            self.beat_flash = 0.15
            self.last_beat_id = beat_id
            # Advance beat counter
            self.beat_in_measure = self.beat_in_measure % self.time_sig + 1

        # Decay timers
        if self.flash_timer > 0:
            self.flash_timer = max(0.0, self.flash_timer - dt)
        if self.beat_flash > 0:
            self.beat_flash = max(0.0, self.beat_flash - dt)

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # -- Draw wooden body (trapezoid) --
        cx = self.PIVOT_X
        for y in range(self.BODY_TOP, self.BODY_BOT + 1):
            t = (y - self.BODY_TOP) / max(1, self.BODY_BOT - self.BODY_TOP)
            half_w = self.BODY_TOP_HALF + t * (self.BODY_BOT_HALF - self.BODY_TOP_HALF)
            x0 = int(cx - half_w)
            x1 = int(cx + half_w)

            for x in range(x0, x1 + 1):
                dist_from_center = abs(x - cx) / max(1, half_w)
                if dist_from_center < 0.4:
                    color = WOOD_LIGHT
                elif dist_from_center < 0.7:
                    color = WOOD_MID
                else:
                    color = WOOD_DARK
                d.set_pixel(x, y, color)

        # Body outline (top edge highlight)
        hw_top = self.BODY_TOP_HALF
        d.draw_line(cx - hw_top, self.BODY_TOP, cx + hw_top, self.BODY_TOP, WOOD_LIGHT)

        # -- Compute arm angle --
        angle = self.MAX_ANGLE * math.cos(self.beat_phase * math.pi)

        # Arm tip position (arm extends upward from pivot)
        tip_x = self.PIVOT_X + self.ARM_LENGTH * math.sin(angle)
        tip_y = self.PIVOT_Y - self.ARM_LENGTH * math.cos(angle)

        # -- Draw arm --
        d.draw_line(self.PIVOT_X, self.PIVOT_Y, int(round(tip_x)), int(round(tip_y)), METAL_ARM)

        # -- Draw weight on arm --
        # Higher BPM = weight closer to pivot (lower on arm visually)
        weight_t = 0.85 - (self.bpm - 20) / (240 - 20) * 0.60
        wx = self.PIVOT_X + (tip_x - self.PIVOT_X) * weight_t
        wy = self.PIVOT_Y + (tip_y - self.PIVOT_Y) * weight_t
        iwx, iwy = int(round(wx)), int(round(wy))

        # Weight: 3x5 rectangle centered on the arm
        for dy in range(-2, 3):
            for dx in range(-1, 2):
                px = iwx + dx
                py = iwy + dy
                if dx == -1 and dy == -2:
                    d.set_pixel(px, py, WEIGHT_HIGHLIGHT)
                else:
                    d.set_pixel(px, py, METAL_WEIGHT)

        # -- Pivot dot --
        d.set_pixel(self.PIVOT_X, self.PIVOT_Y, METAL_ARM)
        d.set_pixel(self.PIVOT_X - 1, self.PIVOT_Y, METAL_ARM)
        d.set_pixel(self.PIVOT_X + 1, self.PIVOT_Y, METAL_ARM)

        # -- Beat flash at arm tip --
        if self.flash_timer > 0:
            brightness = self.flash_timer / 0.1
            r = int(FLASH_COLOR[0] * brightness)
            g = int(FLASH_COLOR[1] * brightness)
            b = int(FLASH_COLOR[2] * brightness)
            flash = (r, g, b)
            itx, ity = int(round(tip_x)), int(round(tip_y))
            d.set_pixel(itx, ity, flash)
            d.set_pixel(itx - 1, ity, flash)
            d.set_pixel(itx + 1, ity, flash)
            d.set_pixel(itx, ity - 1, flash)
            d.set_pixel(itx, ity + 1, flash)

        # -- Red beat indicator (right side) --
        # Column of dots, one per beat in measure, current beat bright red
        ind_x = 58  # right side of screen
        ind_top = 24
        ind_spacing = 8
        for i in range(self.time_sig):
            iy = ind_top + i * ind_spacing
            if i + 1 == self.beat_in_measure and self.beat_flash > 0:
                # Active beat — bright red, fading
                bright = self.beat_flash / 0.15
                cr = int(BEAT_ON[0] * bright + BEAT_DIM[0] * (1 - bright))
                cg = int(BEAT_ON[1] * bright + BEAT_DIM[1] * (1 - bright))
                cb = int(BEAT_ON[2] * bright + BEAT_DIM[2] * (1 - bright))
                c = (cr, cg, cb)
                # 3x3 bright dot
                for dy in range(-1, 2):
                    for dx in range(-1, 2):
                        d.set_pixel(ind_x + dx, iy + dy, c)
            else:
                # Inactive beat — dim dot
                d.set_pixel(ind_x, iy, BEAT_DIM)
                d.set_pixel(ind_x - 1, iy, BEAT_DIM)
                d.set_pixel(ind_x + 1, iy, BEAT_DIM)
                d.set_pixel(ind_x, iy - 1, BEAT_DIM)
                d.set_pixel(ind_x, iy + 1, BEAT_DIM)

        # -- Beat counter number --
        d.draw_text_small(55, 56, str(self.beat_in_measure), BEAT_TEXT)

        # -- BPM and time signature text --
        bpm_str = f"{self.bpm} BPM"
        d.draw_text_small(2, 2, bpm_str, BPM_COLOR)
        sig_str = f"{self.time_sig}:4"
        d.draw_text_small(2, 9, sig_str, BPM_COLOR)

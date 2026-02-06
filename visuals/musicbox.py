"""
Music Box
=========
Side-view brass cylinder with pins rotating past a steel comb. Tines
extend LEFT from the comb spine toward the cylinder. Pins pluck tines
at the contact point (rightmost cylinder edge) with a flash and ±1px
vibration that decays.

Controls:
  Left/Right - Adjust tempo (6 levels)
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---
CYLINDER_COLOR = (180, 150, 50)
CYLINDER_DARK = (130, 110, 35)
CYLINDER_EDGE = (100, 85, 25)
PIN_COLOR = (255, 230, 120)
PIN_DIM = (200, 175, 70)

COMB_SPINE = (160, 160, 170)
COMB_DARK = (120, 120, 130)
TINE_COLOR = (180, 180, 190)
TINE_BRIGHT = (220, 220, 230)
TINE_BASE = (140, 140, 150)

PLUCK_FLASH = (255, 255, 200)

BOX_COLOR = (100, 65, 25)
BOX_DARK = (70, 45, 15)
BOX_LIGHT = (130, 85, 35)
BOX_EDGE = (60, 40, 12)

LID_COLOR = (120, 80, 30)
LID_HIGHLIGHT = (150, 100, 40)

HUD_COLOR = (160, 160, 170)

# --- Layout ---
CYLINDER_CX = 16
CYLINDER_CY = 32
CYLINDER_R = 10

# Comb: spine on right, tines extend LEFT toward cylinder
COMB_SPINE_X = 46
TINE_TIP_X = CYLINDER_CX + CYLINDER_R + 1  # tine tips touch cylinder edge
NUM_TINES = 12
TINE_TOP = CYLINDER_CY - NUM_TINES // 2 + 1

# Pin grid
PIN_ROWS = 12
PIN_COLS = 16

# Box housing
BOX_TOP = CYLINDER_CY + CYLINDER_R + 3
BOX_LEFT = 2
BOX_RIGHT = 60

# Lid
LID_Y = CYLINDER_CY - CYLINDER_R - 6
LID_LEFT = 1
LID_RIGHT = 61

SPEED_BPMS = [30, 60, 90, 120, 160, 200]

# Pin pattern (sparse melody)
PIN_PATTERN = [
    [1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0],
    [0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    [0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0],
    [0, 1, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1],
    [1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0],
    [0, 0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 0, 0],
    [0, 1, 0, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0, 1, 0, 0],
    [0, 0, 0, 1, 0, 0, 0, 0, 0, 1, 0, 0, 1, 0, 0, 1],
]


class MusicBox(Visual):
    name = "MUSIC BOX"
    description = "Cylinder music box"
    category = "music"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3
        self.cylinder_angle = 0.0
        self.tine_energy = [0.0] * NUM_TINES
        self.tine_phase = [0.0] * NUM_TINES
        self.last_col = -1

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

        bpm = SPEED_BPMS[self.speed_level - 1]
        beats_per_sec = bpm / 60.0
        rads_per_sec = (beats_per_sec / PIN_COLS) * 2.0 * math.pi

        self.cylinder_angle += rads_per_sec * dt

        # Which column is at the contact point (rightmost edge)?
        # Pin at col_angle = pi/2 is at x = cx + r (rightmost).
        # col_angle = (col/PIN_COLS)*2pi - cylinder_angle
        # Setting col_angle = pi/2:
        #   col = (cylinder_angle + pi/2) * PIN_COLS / (2*pi)
        contact_frac = ((self.cylinder_angle + math.pi / 2) / (2.0 * math.pi)) * PIN_COLS
        current_col = int(contact_frac) % PIN_COLS

        if current_col != self.last_col:
            self.last_col = current_col
            for row in range(PIN_ROWS):
                if PIN_PATTERN[row][current_col]:
                    self.tine_energy[row] = 1.0
                    self.tine_phase[row] = 0.0

        # Decay tine vibrations
        for i in range(NUM_TINES):
            if self.tine_energy[i] > 0:
                self.tine_energy[i] *= (1.0 - 4.0 * dt)
                if self.tine_energy[i] < 0.02:
                    self.tine_energy[i] = 0.0
                self.tine_phase[i] += dt * 25.0

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        self._draw_box(d)
        self._draw_lid(d)
        self._draw_cylinder(d)
        self._draw_comb(d)
        self._draw_hud(d)

    def _draw_box(self, d):
        d.draw_rect(BOX_LEFT, BOX_TOP, BOX_RIGHT - BOX_LEFT, GRID_SIZE - BOX_TOP, BOX_COLOR)
        d.draw_line(BOX_LEFT, BOX_TOP, BOX_RIGHT - 1, BOX_TOP, BOX_LIGHT)
        d.draw_line(BOX_LEFT, BOX_TOP, BOX_LEFT, 63, BOX_EDGE)
        d.draw_line(BOX_RIGHT - 1, BOX_TOP, BOX_RIGHT - 1, 63, BOX_EDGE)
        d.draw_line(BOX_LEFT + 1, BOX_TOP - 1, BOX_RIGHT - 2, BOX_TOP - 1, BOX_DARK)

    def _draw_lid(self, d):
        d.draw_line(LID_LEFT, LID_Y, LID_RIGHT, LID_Y, LID_COLOR)
        d.draw_line(LID_LEFT, LID_Y + 1, LID_RIGHT, LID_Y + 1, LID_HIGHLIGHT)
        d.draw_line(LID_LEFT, LID_Y, BOX_LEFT, CYLINDER_CY - CYLINDER_R - 2, LID_COLOR)
        d.draw_line(LID_RIGHT, LID_Y, BOX_RIGHT - 1, CYLINDER_CY - CYLINDER_R - 2, LID_COLOR)

    def _draw_cylinder(self, d):
        cx, cy, r = CYLINDER_CX, CYLINDER_CY, CYLINDER_R

        # Cylinder body
        for py in range(cy - r, cy + r + 1):
            if py < 0 or py >= GRID_SIZE:
                continue
            dy = py - cy
            dx_max_sq = r * r - dy * dy
            if dx_max_sq < 0:
                continue
            dx_max = math.sqrt(dx_max_sq)

            for px in range(int(cx - dx_max), int(cx + dx_max) + 1):
                if px < 0 or px >= GRID_SIZE:
                    continue
                dist = math.sqrt((px - cx) ** 2 + dy ** 2)
                if dist > r:
                    continue
                if dist > r - 1.2:
                    d.set_pixel(px, py, CYLINDER_EDGE)
                elif dist > r - 2.5:
                    d.set_pixel(px, py, CYLINDER_DARK)
                else:
                    d.set_pixel(px, py, CYLINDER_COLOR)

        # Pins on visible face
        for col in range(PIN_COLS):
            # Pin angle: col_angle = 0 at top, pi/2 at right (contact)
            col_angle = (col / PIN_COLS) * 2.0 * math.pi - self.cylinder_angle
            col_angle = col_angle % (2.0 * math.pi)
            if col_angle > math.pi:
                col_angle -= 2.0 * math.pi

            # Only draw front-facing pins
            if abs(col_angle) > math.pi * 0.48:
                continue

            pin_x = cx + int(round(r * math.sin(col_angle)))
            facing = math.cos(col_angle)
            if facing < 0.1:
                continue
            color = PIN_COLOR if facing > 0.5 else PIN_DIM

            for row in range(PIN_ROWS):
                if not PIN_PATTERN[row][col]:
                    continue
                pin_y = TINE_TOP + row
                if 0 <= pin_x < GRID_SIZE and 0 <= pin_y < GRID_SIZE:
                    d.set_pixel(pin_x, pin_y, color)

        # Axle ends
        d.set_pixel(cx - r - 1, cy, COMB_SPINE)
        d.set_pixel(cx + r + 1, cy, COMB_SPINE)

    def _draw_comb(self, d):
        """Draw comb: spine on right, tines extending LEFT toward cylinder."""
        # Spine (vertical bar on right side)
        spine_top = TINE_TOP - 2
        spine_bot = TINE_TOP + NUM_TINES + 1
        d.draw_line(COMB_SPINE_X, spine_top, COMB_SPINE_X, spine_bot, COMB_SPINE)
        d.draw_line(COMB_SPINE_X + 1, spine_top, COMB_SPINE_X + 1, spine_bot, COMB_DARK)

        for i in range(NUM_TINES):
            tine_y = TINE_TOP + i
            energy = self.tine_energy[i]

            # Vibration offset
            dy_offset = 0
            if energy > 0.02:
                dy_offset = int(round(energy * math.sin(self.tine_phase[i])))

            # All tines same length — tips align at contact point
            tine_len = COMB_SPINE_X - TINE_TIP_X
            tine_start_x = COMB_SPINE_X - 1  # just left of spine

            for tx_offset in range(tine_len):
                tx = tine_start_x - tx_offset
                # Vibration increases toward the tip (left end)
                tip_frac = tx_offset / max(1, tine_len)
                vy = tine_y + int(round(dy_offset * tip_frac))

                if 0 <= tx < GRID_SIZE and 0 <= vy < GRID_SIZE:
                    if energy > 0.5:
                        d.set_pixel(tx, vy, TINE_BRIGHT)
                    elif energy > 0.1:
                        d.set_pixel(tx, vy, TINE_COLOR)
                    else:
                        d.set_pixel(tx, vy, TINE_BASE)

            # Pluck flash at tine tip (left end, near cylinder)
            if energy > 0.7:
                bright = (energy - 0.7) / 0.3
                fr = int(PLUCK_FLASH[0] * bright)
                fg = int(PLUCK_FLASH[1] * bright)
                fb = int(PLUCK_FLASH[2] * bright)
                flash = (min(255, fr), min(255, fg), min(255, fb))
                tip_x = tine_start_x - tine_len + 1
                d.set_pixel(tip_x, tine_y, flash)
                d.set_pixel(tip_x + 1, tine_y, flash)

    def _draw_hud(self, d):
        bpm = SPEED_BPMS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"{bpm} BPM", HUD_COLOR)

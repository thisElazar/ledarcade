"""
Music Box
=========
Looking down into a cylinder music box. The brass cylinder turns toward the
steel comb; each pin that comes round to the comb plucks one tooth, which
flashes and rings down.

The pins are a real tune - Scott Joplin's "The Entertainer", converted note
for note from a public-domain Mutopia Project score by tools/build_music_box.py.
As in a real box, the comb is cut for the tune: one tooth for each of the 55
pitches the piece uses, long bass teeth on the left, short treble on the right.

Regions:
  y=0-4:   Title of the tune, alternating with its composer
  y=8-33:  Cylinder; pins ride down its face toward the comb
  y=34+:   Comb; tooth tips meet the cylinder, roots run diagonally

Controls:
  Left/Right - Adjust tempo (6 levels)
"""

import math
from bisect import bisect_left, bisect_right

from . import Visual, Display, Colors, GRID_SIZE
from .musicbox_data import TITLE, COMPOSER, BPM, TICKS_PER_BEAT, COMB, PINS


# --- Color Palette ---
CYLINDER_COLOR = (150, 118, 36)
CYLINDER_EDGE = (50, 38, 10)
PIN_COLOR = (255, 240, 170)

TOOTH_LIGHT = (150, 150, 162)
TOOTH_DARK = (104, 104, 116)
COMB_PLATE = (78, 78, 90)
COMB_SCREW = (30, 30, 36)
PLUCK_FLASH = (255, 255, 200)

BOX_COLOR = (100, 65, 25)
BOX_DARK = (34, 22, 8)
AXLE_COLOR = (160, 160, 170)

HUD_COLOR = (160, 160, 170)

# --- Layout ---
NUM_TEETH = len(COMB)
COMB_LEFT = (GRID_SIZE - NUM_TEETH) // 2   # one pixel per tooth, centred

CYLINDER_TOP = 8
CYLINDER_BOTTOM = 33
CYLINDER_R = (CYLINDER_BOTTOM - CYLINDER_TOP + 1) / 2.0
CYLINDER_CY = (CYLINDER_TOP + CYLINDER_BOTTOM) / 2.0

TOOTH_TIP = CYLINDER_BOTTOM + 1
TOOTH_LONG = 20      # bass tooth length
TOOTH_SHORT = 7      # treble tooth length
PLATE_BOTTOM = 58

BOX_TOP = 6

# The cylinder turns at one speed for the whole tune. A real one would carry
# the tune in a single turn; at this size that would smear the pins together,
# so this one turns faster and the tune takes many turns.
TURN_SPEED = 0.55   # radians per second at the tune's own tempo
TEMPO_SCALES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

TITLE_SECONDS = 4.0    # header alternates title / composer this often
TEMPO_SECONDS = 2.0    # header shows the tempo this long after a change
TAIL_SECONDS = 3.0     # silence after the last note, before it starts over

PIN_STARTS = [p[0] for p in PINS]
TUNE_END = PINS[-1][0]
# Ticks of music per radian of cylinder, and how much of it is on view
TICKS_PER_RADIAN = BPM / 60.0 * TICKS_PER_BEAT / TURN_SPEED
VISIBLE_TICKS = math.pi * TICKS_PER_RADIAN

# Brass shading per cylinder row: bright along the top of the curve
CYLINDER_ROWS = []
for _y in range(CYLINDER_TOP, CYLINDER_BOTTOM + 1):
    _lit = math.sqrt(max(0.0, 1.0 - ((_y - CYLINDER_CY) / CYLINDER_R) ** 2))
    CYLINDER_ROWS.append(tuple(
        int(e + (c - e) * _lit) for c, e in zip(CYLINDER_COLOR, CYLINDER_EDGE)))

# Tooth lengths: graded from the long bass tooth to the short treble one
TOOTH_LENGTHS = [
    round(TOOTH_LONG - (TOOTH_LONG - TOOTH_SHORT) * i / (NUM_TEETH - 1))
    for i in range(NUM_TEETH)]


class MusicBox(Visual):
    name = "MUSIC BOX"
    description = "Cylinder music box"
    category = "music"
    GUIDE = {
        'desc': 'A rotating brass cylinder with pins plucking a steel comb, seen from above. The pins are a real tune, Scott Joplin\'s "The Entertainer", and the comb is cut for it: one tooth for each of the 55 notes the piece uses, long bass teeth at the left, short treble teeth at the right. The original mechanical music player.',
        'credit': 'Score: Mutopia Project',
        'legend': {
            'top line': 'Title of the tune, alternating with its composer.',
            '# BPM': 'Tempo in quarter notes per minute, shown after you change it.',
        },
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3       # 1-6
        self.tempo_shown = 0.0     # seconds left to show the tempo
        self._rewind()

    def _rewind(self):
        """Start the tune over: first pins just coming over the cylinder."""
        self.pos = -VISIBLE_TICKS          # tick now at the comb
        self.next_pin = 0
        self.tooth_energy = [0.0] * NUM_TEETH   # 0..1, rings down

    def _bpm(self):
        return round(BPM * TEMPO_SCALES[self.speed_level - 1])

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            self.tempo_shown = TEMPO_SECONDS
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            self.tempo_shown = TEMPO_SECONDS
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.tempo_shown = max(0.0, self.tempo_shown - dt)

        ticks_per_sec = self._bpm() / 60.0 * TICKS_PER_BEAT
        self.pos += ticks_per_sec * dt

        # Pluck the tooth of every pin that has come round to the comb
        while self.next_pin < len(PINS) and PINS[self.next_pin][0] <= self.pos:
            self.tooth_energy[PINS[self.next_pin][1]] = 1.0
            self.next_pin += 1

        for i in range(NUM_TEETH):
            if self.tooth_energy[i] > 0.0:
                self.tooth_energy[i] = max(0.0, self.tooth_energy[i] - 2.5 * dt)

        if self.pos > TUNE_END + TAIL_SECONDS * ticks_per_sec:
            self._rewind()

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        self._draw_box(d)
        self._draw_cylinder(d)
        self._draw_comb(d)
        self._draw_hud(d)

    def _draw_box(self, d):
        """Draw the wooden case: dark interior inside a lighter rim."""
        d.draw_rect(0, BOX_TOP, GRID_SIZE, GRID_SIZE - BOX_TOP, BOX_DARK)
        d.draw_rect(0, BOX_TOP, GRID_SIZE, GRID_SIZE - BOX_TOP, BOX_COLOR, filled=False)

    def _draw_cylinder(self, d):
        """Draw the cylinder and the pins on the half of it facing up."""
        left, right = COMB_LEFT, COMB_LEFT + NUM_TEETH - 1
        for row, color in enumerate(CYLINDER_ROWS):
            y = CYLINDER_TOP + row
            for x in range(left, right + 1):
                d.set_pixel(x, y, color)

        # Axle ends
        axle_y = int(CYLINDER_CY)
        for x in (left - 2, left - 1, right + 1, right + 2):
            d.set_pixel(x, axle_y, AXLE_COLOR)
            d.set_pixel(x, axle_y + 1, AXLE_COLOR)

        # Pins: one that is due now is at the comb edge, later ones further
        # back over the top of the cylinder
        first = bisect_left(PIN_STARTS, self.pos)
        last = bisect_right(PIN_STARTS, self.pos + VISIBLE_TICKS)
        for start, tooth in PINS[first:last]:
            angle = math.pi / 2 - (start - self.pos) / TICKS_PER_RADIAN
            y = int(CYLINDER_CY + CYLINDER_R * math.sin(angle))
            y = max(CYLINDER_TOP, min(CYLINDER_BOTTOM, y))
            # Dimmer toward the edges, where the pin is seen side-on
            lit = 0.45 + 0.55 * math.cos(angle)
            d.set_pixel(COMB_LEFT + tooth, y, (
                int(PIN_COLOR[0] * lit), int(PIN_COLOR[1] * lit), int(PIN_COLOR[2] * lit)))

    def _draw_comb(self, d):
        """Draw the comb: tips at the cylinder, roots on a diagonal, plate below."""
        for i in range(NUM_TEETH):
            x = COMB_LEFT + i
            root = TOOTH_TIP + TOOTH_LENGTHS[i]
            base = TOOTH_LIGHT if i % 2 == 0 else TOOTH_DARK
            energy = self.tooth_energy[i]
            if energy > 0.0:
                color = (
                    int(base[0] + (PLUCK_FLASH[0] - base[0]) * energy),
                    int(base[1] + (PLUCK_FLASH[1] - base[1]) * energy),
                    int(base[2] + (PLUCK_FLASH[2] - base[2]) * energy))
            else:
                color = base
            for y in range(TOOTH_TIP, root):
                d.set_pixel(x, y, color)
            for y in range(root, PLATE_BOTTOM + 1):
                d.set_pixel(x, y, COMB_PLATE)

        # Screws holding the plate to the bedplate
        for i in (NUM_TEETH // 6, NUM_TEETH // 2, NUM_TEETH - NUM_TEETH // 6):
            d.set_pixel(COMB_LEFT + i, PLATE_BOTTOM - 2, COMB_SCREW)

    def _draw_hud(self, d):
        """Draw the tune's title / composer, or the tempo just after a change."""
        if self.tempo_shown > 0.0:
            text = f"{self._bpm()} BPM"
        elif int(self.time / TITLE_SECONDS) % 2 == 0:
            text = TITLE
        else:
            text = COMPOSER
        d.draw_text_small(1, 0, text, HUD_COLOR)

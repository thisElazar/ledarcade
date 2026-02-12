#!/usr/bin/env python3
"""Assemble chordchart.py with embedded chord data.

Usage:
  1. Run extract_chords.py first to generate /tmp/chord_data_v2.py
  2. python3 build_chordchart.py
"""

import sys

# Read the raw chord data
data_path = sys.argv[1] if len(sys.argv) > 1 else '/tmp/chord_data_v2.py'
with open(data_path) as f:
    chord_data_text = f.read()

# Extract lines between { and } for each dict
guitar_lines = []
ukulele_lines = []
target = None
for line in chord_data_text.split('\n'):
    stripped = line.rstrip()
    if stripped.startswith('GUITAR_CHORDS'):
        target = guitar_lines
        continue
    elif stripped.startswith('UKULELE_CHORDS'):
        target = ukulele_lines
        continue
    elif stripped == '}':
        if target is not None:
            target = None
        continue
    if target is not None and stripped:
        target.append(stripped)

guitar_block = '\n'.join(guitar_lines)
ukulele_block = '\n'.join(ukulele_lines)

HEADER = '''"""Chord chart viewer for guitar and ukulele on 64x64 LED matrix."""

import math
import random
from . import Visual

# Chord data from tombatossals/chords-db (MIT license)
# Format: {(root, suffix): [(frets, fingers, baseFret, barres), ...]}
# frets: -1=muted, 0=open, 1+=fret relative to baseFret

'''

BODY = r'''

# ─── Constants ───────────────────────────────────────────────────────────────

ROOTS = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

SUFFIXES = [
    'major', 'minor', '7', 'maj7', 'm7', 'dim', 'aug',
    'sus2', 'sus4', 'add9', 'dim7', '6', 'm6', '9', 'm9',
]

# Short display names for header
SUFFIX_DISPLAY = {
    'major': 'MAJ', 'minor': 'MIN', '7': '7', 'maj7': 'MA7', 'm7': 'M7',
    'dim': 'DIM', 'aug': 'AUG', 'sus2': 'SU2', 'sus4': 'SU4', 'add9': 'AD9',
    'dim7': 'DI7', '6': '6', 'm6': 'M6', '9': '9', 'm9': 'M9',
}

# 3x5 font for flat symbol (lowercase b) - not in the main font since
# draw_text_small uppercases everything. We render roots manually.
FLAT_GLYPH = ['100', '100', '110', '101', '110']

# Finger colors (1=index=blue, 2=middle=green, 3=ring=orange, 4=pinky=red)
FINGER_COLORS = {
    0: (120, 120, 120),  # no finger / thumb
    1: (60, 120, 220),   # index - blue
    2: (50, 200, 80),    # middle - green
    3: (230, 150, 30),   # ring - orange
    4: (220, 50, 50),    # pinky - red
}

# Layout constants
GUITAR_STRINGS = [12, 20, 28, 36, 44, 52]  # x positions for 6 strings
UKULELE_STRINGS = [16, 26, 36, 46]          # x positions for 4 strings

FRET_TOP = 13       # y of top of fretboard (below nut)
FRET_H = 11         # pixels per fret
NUM_FRETS = 4       # frets shown
FRET_BOTTOM = FRET_TOP + FRET_H * NUM_FRETS  # y=57

# Fret wire y positions
FRET_WIRES = [FRET_TOP + FRET_H * i for i in range(NUM_FRETS + 1)]
# Dot center y positions (midpoint of each fret)
DOT_CENTERS = [FRET_TOP + FRET_H * i + FRET_H // 2 for i in range(NUM_FRETS)]

# Colors
WOOD_BG = (60, 35, 15)
WOOD_LIGHT = (80, 50, 20)
FRET_WIRE = (160, 160, 170)
NUT_COLOR = (230, 230, 230)
STRING_COLOR = (140, 140, 150)
MUTED_COLOR = (200, 50, 50)
OPEN_COLOR = (50, 200, 80)
HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)


class ChordChart(Visual):
    name = "CHORD CHART"
    description = "Guitar & ukulele chords"
    category = "music"

    def reset(self):
        self.time = 0.0
        self.root_idx = 0       # index into ROOTS
        self.suffix_idx = 0     # index into SUFFIXES
        self.voicing_idx = 0    # which voicing of current chord
        self.instrument = 0     # 0=guitar, 1=ukulele
        self.fade_timer = 0.0   # fade-in animation
        self.shimmer_phase = [random.uniform(0, 6.28) for _ in range(6)]

    def _chord_db(self):
        return UKULELE_CHORDS if self.instrument == 1 else GUITAR_CHORDS

    def _string_xs(self):
        return UKULELE_STRINGS if self.instrument == 1 else GUITAR_STRINGS

    def _num_strings(self):
        return 4 if self.instrument == 1 else 6

    def _current_voicings(self):
        key = (ROOTS[self.root_idx], SUFFIXES[self.suffix_idx])
        return self._chord_db().get(key, [])

    def _current_voicing(self):
        voicings = self._current_voicings()
        if not voicings:
            return None
        idx = min(self.voicing_idx, len(voicings) - 1)
        return voicings[idx]

    def _clamp_voicing(self):
        voicings = self._current_voicings()
        if voicings:
            self.voicing_idx = min(self.voicing_idx, len(voicings) - 1)
        else:
            self.voicing_idx = 0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Both buttons together: switch instrument
        if input_state.action_l and input_state.action_r:
            self.instrument = 1 - self.instrument
            self._clamp_voicing()
            self.fade_timer = 0.3
            self.shimmer_phase = [random.uniform(0, 6.28)
                                  for _ in range(self._num_strings())]
            return True

        # Left/Right buttons: cycle key (root note)
        if input_state.action_l:
            self.root_idx = (self.root_idx - 1) % len(ROOTS)
            self._clamp_voicing()
            self.fade_timer = 0.3
            consumed = True
        elif input_state.action_r:
            self.root_idx = (self.root_idx + 1) % len(ROOTS)
            self._clamp_voicing()
            self.fade_timer = 0.3
            consumed = True

        # Up/Down: cycle chord type (suffix)
        if input_state.up_pressed:
            self.suffix_idx = (self.suffix_idx - 1) % len(SUFFIXES)
            self._clamp_voicing()
            self.fade_timer = 0.3
            consumed = True
        elif input_state.down_pressed:
            self.suffix_idx = (self.suffix_idx + 1) % len(SUFFIXES)
            self._clamp_voicing()
            self.fade_timer = 0.3
            consumed = True

        # Left/Right d-pad: cycle voicings
        if input_state.left_pressed:
            voicings = self._current_voicings()
            if voicings:
                self.voicing_idx = (self.voicing_idx - 1) % len(voicings)
            self.fade_timer = 0.2
            consumed = True
        elif input_state.right_pressed:
            voicings = self._current_voicings()
            if voicings:
                self.voicing_idx = (self.voicing_idx + 1) % len(voicings)
            self.fade_timer = 0.2
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        if self.fade_timer > 0:
            self.fade_timer = max(0, self.fade_timer - dt)

    def draw(self):
        d = self.display
        d.clear()

        self._draw_header(d)
        self._draw_fretboard(d)
        voicing = self._current_voicing()
        if voicing:
            self._draw_nut(d, voicing)
            self._draw_markers(d, voicing)
            self._draw_dots(d, voicing)
            self._draw_barres(d, voicing)
        self._draw_strings(d)
        self._draw_footer(d, voicing)

    def _draw_char(self, d, x, y, char, color):
        """Draw a single 3x5 character, supporting lowercase 'b' for flat."""
        if char == 'b':
            glyph = FLAT_GLYPH
        else:
            FONT = {
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
                '#': ['010', '111', '010', '111', '010'],
                ' ': ['000', '000', '000', '000', '000'],
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
                '/': ['001', '010', '010', '010', '100'],
                '-': ['000', '000', '111', '000', '000'],
            }
            ch = char.upper()
            glyph = FONT.get(ch)
            if glyph is None:
                return  # unknown char, skip
        for row_idx, row in enumerate(glyph):
            for col_idx, pixel in enumerate(row):
                if pixel == '1':
                    d.set_pixel(x + col_idx, y + row_idx, color)

    def _draw_text(self, d, x, y, text, color):
        """Draw text with flat-aware rendering (preserves case for 'b')."""
        cursor = x
        for char in text:
            self._draw_char(d, cursor, y, char, color)
            cursor += 4
        return cursor

    def _draw_header(self, d):
        # Header background
        d.draw_rect(0, 0, 64, 7, HEADER_BG)

        root = ROOTS[self.root_idx]
        suffix = SUFFIX_DISPLAY[SUFFIXES[self.suffix_idx]]

        # Draw root with flat-aware rendering, then suffix uppercase
        cursor = self._draw_text(d, 1, 1, root, (255, 220, 100))
        self._draw_text(d, cursor, 1, ' ' + suffix, (255, 220, 100))

        # Instrument indicator right-aligned
        inst_label = 'UKE' if self.instrument == 1 else 'GTR'
        d.draw_text_small(49, 1, inst_label, (150, 180, 220))

        # Thin separator
        for x in range(64):
            d.set_pixel(x, 7, (60, 60, 80))

    def _draw_fretboard(self, d):
        # Wood background
        string_xs = self._string_xs()
        left = string_xs[0] - 3
        right = string_xs[-1] + 3
        for y in range(FRET_TOP, FRET_BOTTOM + 1):
            for x in range(left, right + 1):
                # Subtle grain
                grain = ((x * 7 + y * 13) % 5)
                r = WOOD_BG[0] + grain
                g = WOOD_BG[1] + grain
                b = WOOD_BG[2] + grain // 2
                d.set_pixel(x, y, (r, g, b))

        # Fret wires
        for fy in FRET_WIRES:
            for x in range(left, right + 1):
                d.set_pixel(x, fy, FRET_WIRE)

    def _draw_nut(self, d, voicing):
        frets, fingers, base_fret, barres = voicing
        string_xs = self._string_xs()
        left = string_xs[0] - 3
        right = string_xs[-1] + 3

        if base_fret == 1:
            # Thick white nut (2px)
            for y in [11, 12]:
                for x in range(left, right + 1):
                    d.set_pixel(x, y, NUT_COLOR)
        else:
            # Thin line + fret number to the left
            for x in range(left, right + 1):
                d.set_pixel(x, 12, FRET_WIRE)
            # Draw base fret number
            fret_str = str(base_fret)
            self._draw_text(d, left - len(fret_str) * 4 - 1, 15, fret_str, TEXT_DIM)

    def _draw_markers(self, d, voicing):
        """Draw open (O) and muted (X) markers above the nut."""
        frets, fingers, base_fret, barres = voicing
        string_xs = self._string_xs()

        for i, (fret, sx) in enumerate(zip(frets, string_xs)):
            if fret == 0:
                # Open string: green hollow diamond
                cy = 9
                d.set_pixel(sx, cy - 1, OPEN_COLOR)
                d.set_pixel(sx - 1, cy, OPEN_COLOR)
                d.set_pixel(sx + 1, cy, OPEN_COLOR)
                d.set_pixel(sx, cy + 1, OPEN_COLOR)
            elif fret == -1:
                # Muted string: red X
                cy = 9
                d.set_pixel(sx - 1, cy - 1, MUTED_COLOR)
                d.set_pixel(sx + 1, cy - 1, MUTED_COLOR)
                d.set_pixel(sx, cy, MUTED_COLOR)
                d.set_pixel(sx - 1, cy + 1, MUTED_COLOR)
                d.set_pixel(sx + 1, cy + 1, MUTED_COLOR)

    def _draw_dots(self, d, voicing):
        """Draw finger dots on the fretboard."""
        frets, fingers, base_fret, barres = voicing
        string_xs = self._string_xs()

        # Fade-in alpha
        alpha = 1.0
        if self.fade_timer > 0:
            alpha = 1.0 - (self.fade_timer / 0.3)
            alpha = max(0.0, min(1.0, alpha))

        for i, (fret, finger, sx) in enumerate(zip(frets, fingers, string_xs)):
            if fret <= 0:
                continue  # skip open and muted

            fret_idx = fret - 1  # 0-indexed fret position
            if fret_idx < 0 or fret_idx >= NUM_FRETS:
                continue

            cy = DOT_CENTERS[fret_idx]
            color = FINGER_COLORS.get(finger, FINGER_COLORS[0])

            # Check if this string is part of a barre (skip individual dot)
            if barres and fret in barres:
                # Will be drawn by _draw_barres
                continue

            # Apply fade
            color = tuple(int(c * alpha) for c in color)

            # Draw filled circle r=2
            d.draw_circle(sx, cy, 2, color, filled=True)

    def _draw_barres(self, d, voicing):
        """Draw barre chord bars."""
        frets, fingers, base_fret, barres = voicing
        string_xs = self._string_xs()

        if not barres:
            return

        alpha = 1.0
        if self.fade_timer > 0:
            alpha = 1.0 - (self.fade_timer / 0.3)
            alpha = max(0.0, min(1.0, alpha))

        for barre_fret in barres:
            fret_idx = barre_fret - 1
            if fret_idx < 0 or fret_idx >= NUM_FRETS:
                continue

            cy = DOT_CENTERS[fret_idx]

            # Find the range of strings that have this fret value
            barre_strings = [i for i, f in enumerate(frets) if f == barre_fret]
            if len(barre_strings) < 2:
                # Single string, just draw a dot
                if barre_strings:
                    si = barre_strings[0]
                    finger = fingers[si]
                    color = FINGER_COLORS.get(finger, FINGER_COLORS[0])
                    color = tuple(int(c * alpha) for c in color)
                    d.draw_circle(string_xs[si], cy, 2, color, filled=True)
                continue

            first_s = min(barre_strings)
            last_s = max(barre_strings)
            x1 = string_xs[first_s]
            x2 = string_xs[last_s]

            # Use the finger color from the first barred string
            finger = fingers[first_s]
            color = FINGER_COLORS.get(finger, FINGER_COLORS[0])
            color = tuple(int(c * alpha) for c in color)

            # Draw barre as a rounded bar
            d.draw_rect(x1 - 1, cy - 1, x2 - x1 + 3, 3, color)

            # Draw dots at each end for roundness
            d.draw_circle(x1, cy, 2, color, filled=True)
            d.draw_circle(x2, cy, 2, color, filled=True)

    def _draw_strings(self, d):
        """Draw string lines with subtle shimmer."""
        string_xs = self._string_xs()
        num = self._num_strings()

        for i, sx in enumerate(string_xs):
            phase = self.shimmer_phase[i] if i < len(self.shimmer_phase) else 0
            for y in range(FRET_TOP, FRET_BOTTOM + 1):
                # Skip pixels where fret wires are
                if y in FRET_WIRES:
                    continue
                shimmer = int(15 * math.sin(self.time * 2.5 + phase + y * 0.3))
                brightness = STRING_COLOR[0] + shimmer
                brightness = max(80, min(200, brightness))
                d.set_pixel(sx, y, (brightness, brightness, brightness + 10))

    def _draw_footer(self, d, voicing):
        """Draw voicing number and fret info at bottom."""
        voicings = self._current_voicings()
        num_v = len(voicings)
        if num_v == 0:
            d.draw_text_small(14, 59, 'NO DATA', (180, 80, 80))
            return

        idx = min(self.voicing_idx, num_v - 1) + 1

        # Voicing indicator "1/3"
        v_text = f'{idx}/{num_v}'
        self._draw_text(d, 1, 59, v_text, TEXT_DIM)

        # Base fret info on right side
        if voicing:
            frets, fingers, base_fret, barres = voicing
            if base_fret > 1:
                fr_text = f'FR{base_fret}'
                d.draw_text_small(45, 59, fr_text, TEXT_DIM)
'''

# Build the final file
output = HEADER
output += "GUITAR_CHORDS = {\n"
output += guitar_block + "\n"
output += "}\n\n"
output += "UKULELE_CHORDS = {\n"
output += ukulele_block + "\n"
output += "}\n"
output += BODY

target = '/Users/fields/Desktop/FunWithArt/arcadePanel/led-arcade/visuals/chordchart.py'
with open(target, 'w') as f:
    f.write(output)

print(f"Written chordchart.py ({len(output)} chars, {output.count(chr(10))} lines)")

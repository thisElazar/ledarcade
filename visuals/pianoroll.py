"""
Piano Roll
==========
Player piano with scrolling paper roll, hammer mechanism, and keyboard.
Notes scroll down through a cream paper roll, trigger hammers that pivot
upward to strike, and depress the corresponding piano keys below.

Regions:
  y=3-38:  Paper roll with colored note rectangles scrolling down
  y=39-49: Hammer mechanism (16 hammers pivot upward on trigger, decay back)
  y=50-63: Piano keys (white/black pattern, depress on note)

Controls:
  Left/Right - Adjust tempo (6 levels)
  Up/Down    - Cycle song pattern (Classical, Ragtime, Jazz, Pop)
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette ---
PAPER_COLOR = (220, 210, 180)
PAPER_DARK = (200, 190, 160)
PAPER_EDGE = (180, 170, 140)
ROLL_FRAME = (100, 70, 30)
ROLL_SPINDLE = (140, 100, 40)

HAMMER_REST = (120, 120, 130)
HAMMER_ACTIVE = (200, 200, 210)
HAMMER_PIVOT = (80, 80, 90)
HAMMER_HEAD = (180, 180, 190)
HAMMER_HEAD_HIT = (255, 255, 220)

KEY_WHITE = (200, 200, 200)
KEY_WHITE_PRESSED = (140, 140, 150)
KEY_BLACK = (30, 30, 35)
KEY_BLACK_PRESSED = (60, 60, 70)
KEY_EDGE = (100, 100, 110)

HUD_COLOR = (160, 160, 170)

# Note colors by pitch class (mod 12) - rainbow spread
NOTE_COLORS = [
    (255, 60, 60),     # C  - red
    (255, 100, 50),    # C# - red-orange
    (255, 160, 40),    # D  - orange
    (255, 220, 40),    # D# - gold
    (220, 255, 40),    # E  - yellow-green
    (60, 220, 60),     # F  - green
    (40, 200, 180),    # F# - teal
    (50, 140, 255),    # G  - blue
    (80, 80, 255),     # G# - indigo
    (160, 60, 255),    # A  - purple
    (220, 50, 200),    # A# - magenta
    (255, 60, 140),    # B  - pink
]

# --- Layout ---
ROLL_TOP = 3
ROLL_BOTTOM = 38
ROLL_LEFT = 2
ROLL_RIGHT = 61
ROLL_HEIGHT = ROLL_BOTTOM - ROLL_TOP

HAMMER_TOP = 39
HAMMER_BOTTOM = 49

KEY_TOP = 50
KEY_BOTTOM = 63

NUM_KEYS = 16  # 16 piano keys spanning the width
KEY_WIDTH = 4  # pixels per key

# Map 16 keys to pitches (two octaves of white+black, simplified)
# Using a C major scale spread: C D E F G A B C D E F G A B C D
KEY_PITCHES = [0, 2, 4, 5, 7, 9, 11, 12, 14, 16, 17, 19, 21, 23, 24, 26]
# Which keys are "black" keys (sharps/flats)
KEY_IS_BLACK = [False, False, False, False, False, False, False,
                False, False, False, False, False, False, False, False, False]
# Mark positions 1,3,6,8,10,13,15 as black for visual pattern
for _i in [1, 3, 6, 8, 10, 13, 15]:
    if _i < NUM_KEYS:
        KEY_IS_BLACK[_i] = True

# Tempo levels (BPM)
TEMPO_BPMS = [60, 80, 100, 120, 150, 180]
PATTERN_NAMES = ["CLASSICAL", "RAGTIME", "JAZZ", "POP"]

# --- Procedural melody patterns ---
# Each pattern is a function that generates a list of (key_index, start_beat, duration)
# We pre-generate 64 beats of each pattern

def _gen_classical():
    """Arpeggiated chords with sustained bass."""
    notes = []
    beat = 0
    chords = [
        [0, 4, 7],    # C major
        [5, 9, 12],   # F major
        [7, 11, 14],  # G major
        [0, 4, 7],    # C major
        [2, 5, 9],    # Dm
        [4, 7, 11],   # Em
        [5, 9, 12],   # F major
        [7, 11, 14],  # G major
    ]
    for chord in chords:
        for i, key in enumerate(chord):
            if key < NUM_KEYS:
                notes.append((key, beat + i * 0.5, 1.5))
        # Bass note
        bass = chord[0]
        if bass < NUM_KEYS:
            notes.append((bass, beat, 3.5))
        beat += 4
    return notes

def _gen_ragtime():
    """Stride piano: alternating bass-chord pattern with syncopation."""
    notes = []
    beat = 0
    bass_keys = [0, 5, 7, 0, 2, 5, 7, 0]
    chord_sets = [
        [4, 7],    [9, 12],   [11, 14],  [4, 7],
        [5, 9],    [9, 12],   [11, 14],  [4, 7],
    ]
    for bar in range(8):
        bass = bass_keys[bar % len(bass_keys)]
        chords = chord_sets[bar % len(chord_sets)]
        # Oom-pah pattern
        if bass < NUM_KEYS:
            notes.append((bass, beat, 0.5))
            notes.append((bass, beat + 2, 0.5))
        for c in chords:
            if c < NUM_KEYS:
                notes.append((c, beat + 1, 0.5))
                notes.append((c, beat + 3, 0.5))
        # Syncopated melody on top
        melody = [12, 14, 15, 14, 12, 11, 9, 7]
        mk = melody[bar % len(melody)]
        if mk < NUM_KEYS:
            notes.append((mk, beat + 0.5, 1.0))
            notes.append((mk, beat + 2.5, 0.5))
        beat += 4
    return notes

def _gen_jazz():
    """Jazz voicings with walking bass and extended chords."""
    notes = []
    beat = 0
    # Walking bass line
    bass_walk = [0, 2, 4, 5, 7, 5, 4, 2, 0, 7, 5, 4, 2, 4, 5, 7,
                 0, 2, 4, 5, 7, 9, 7, 5, 4, 2, 0, 2, 4, 5, 7, 0]
    # Chord stabs on off-beats
    chord_voicings = [
        [4, 9, 14],   [7, 11, 15], [5, 9, 14],  [4, 11, 14],
        [7, 12, 15],  [5, 9, 14],  [4, 9, 12],  [7, 11, 15],
    ]
    for i in range(32):
        bk = bass_walk[i % len(bass_walk)]
        if bk < NUM_KEYS:
            notes.append((bk, beat, 0.8))
        # Chord stab every 2 beats, offset by half
        if i % 2 == 1:
            chord = chord_voicings[(i // 2) % len(chord_voicings)]
            for c in chord:
                if c < NUM_KEYS:
                    notes.append((c, beat + 0.5, 0.5))
        beat += 1
    return notes

def _gen_pop():
    """Pop/rock pattern with steady rhythm and catchy melody."""
    notes = []
    beat = 0
    # Steady bass pulse
    bass_pattern = [0, 0, 5, 5, 7, 7, 5, 5]
    # Chord pad
    pads = [
        [4, 7, 12], [4, 7, 12], [9, 12, 14], [9, 12, 14],
        [11, 14, 7], [11, 14, 7], [9, 12, 14], [9, 12, 14],
    ]
    # Melody
    melody_notes = [12, 14, 15, 14, 12, 11, 12, 14,
                    15, 14, 12, 9, 7, 9, 12, 14]
    for bar in range(8):
        bass = bass_pattern[bar % len(bass_pattern)]
        if bass < NUM_KEYS:
            notes.append((bass, beat, 1.0))
            notes.append((bass, beat + 2, 1.0))
        pad = pads[bar % len(pads)]
        for c in pad:
            if c < NUM_KEYS:
                notes.append((c, beat + 1, 2.0))
        # Melody notes
        for j in range(4):
            mk = melody_notes[(bar * 2 + j) % len(melody_notes)]
            if mk < NUM_KEYS:
                notes.append((mk, beat + j, 0.8))
        beat += 4
    return notes


PATTERNS = [_gen_classical(), _gen_ragtime(), _gen_jazz(), _gen_pop()]
# Calculate total beats for each pattern
PATTERN_BEATS = []
for p in PATTERNS:
    max_beat = max(n[1] + n[2] for n in p) if p else 1
    PATTERN_BEATS.append(max_beat)


class PianoRoll(Visual):
    name = "PIANO ROLL"
    description = "Player piano"
    category = "music"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.tempo_level = 3       # 1-6
        self.pattern_index = 0     # 0-3
        self.scroll_pos = 0.0      # current beat position
        self.hammer_energy = [0.0] * NUM_KEYS   # 0..1, decays
        self.key_press = [0.0] * NUM_KEYS       # 0..1, decays

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.tempo_level = min(6, self.tempo_level + 1)
            consumed = True
        elif input_state.left_pressed:
            self.tempo_level = max(1, self.tempo_level - 1)
            consumed = True
        if input_state.up_pressed:
            self.pattern_index = (self.pattern_index + 1) % len(PATTERNS)
            consumed = True
        elif input_state.down_pressed:
            self.pattern_index = (self.pattern_index - 1) % len(PATTERNS)
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        bpm = TEMPO_BPMS[self.tempo_level - 1]
        beats_per_sec = bpm / 60.0
        self.scroll_pos += beats_per_sec * dt

        # Wrap scroll position at end of pattern
        total_beats = PATTERN_BEATS[self.pattern_index]
        if self.scroll_pos >= total_beats:
            self.scroll_pos -= total_beats

        # Check which notes are active at current beat
        pattern = PATTERNS[self.pattern_index]
        total = PATTERN_BEATS[self.pattern_index]
        current_beat = self.scroll_pos

        for note in pattern:
            key_idx, start, dur = note
            # Check if note is currently being struck (within a small window)
            # Account for wrapping
            note_end = start + dur
            hit_window = 0.1
            # Is current_beat within hit_window of start?
            diff = (current_beat - start) % total
            if diff < hit_window or diff > total - hit_window:
                if self.hammer_energy[key_idx] < 0.3:
                    self.hammer_energy[key_idx] = 1.0
                    self.key_press[key_idx] = 1.0

        # Decay hammers and keys
        for i in range(NUM_KEYS):
            self.hammer_energy[i] *= (1.0 - 5.0 * dt)
            if self.hammer_energy[i] < 0.01:
                self.hammer_energy[i] = 0.0
            self.key_press[i] *= (1.0 - 4.0 * dt)
            if self.key_press[i] < 0.01:
                self.key_press[i] = 0.0

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        self._draw_roll(d)
        self._draw_hammers(d)
        self._draw_keys(d)
        self._draw_hud(d)

    def _draw_roll(self, d):
        """Draw the paper roll with scrolling note rectangles."""
        # Paper background
        for y in range(ROLL_TOP, ROLL_BOTTOM + 1):
            for x in range(ROLL_LEFT, ROLL_RIGHT + 1):
                # Slight vertical stripes for paper texture
                if x % 8 == 0:
                    d.set_pixel(x, y, PAPER_EDGE)
                else:
                    d.set_pixel(x, y, PAPER_COLOR)

        # Frame edges (spindle rollers at top and bottom of roll)
        d.draw_line(ROLL_LEFT, ROLL_TOP - 1, ROLL_RIGHT, ROLL_TOP - 1, ROLL_FRAME)
        d.draw_line(ROLL_LEFT, ROLL_BOTTOM + 1, ROLL_RIGHT, ROLL_BOTTOM + 1, ROLL_FRAME)
        # Spindle circles at edges
        d.set_pixel(ROLL_LEFT - 1, ROLL_TOP - 1, ROLL_SPINDLE)
        d.set_pixel(ROLL_RIGHT + 1, ROLL_TOP - 1, ROLL_SPINDLE)
        d.set_pixel(ROLL_LEFT - 1, ROLL_BOTTOM + 1, ROLL_SPINDLE)
        d.set_pixel(ROLL_RIGHT + 1, ROLL_BOTTOM + 1, ROLL_SPINDLE)

        # Key lane guides (dim vertical lines separating key lanes)
        roll_width = ROLL_RIGHT - ROLL_LEFT
        for k in range(NUM_KEYS + 1):
            lane_x = ROLL_LEFT + int(k * roll_width / NUM_KEYS)
            if ROLL_LEFT <= lane_x <= ROLL_RIGHT:
                for y in range(ROLL_TOP, ROLL_BOTTOM + 1):
                    d.set_pixel(lane_x, y, PAPER_DARK)

        # Draw notes
        pattern = PATTERNS[self.pattern_index]
        total = PATTERN_BEATS[self.pattern_index]
        current_beat = self.scroll_pos
        roll_width = ROLL_RIGHT - ROLL_LEFT
        lane_w = roll_width / NUM_KEYS

        # How many beats are visible on the roll
        visible_beats = 8.0
        pixels_per_beat = ROLL_HEIGHT / visible_beats

        for note in pattern:
            key_idx, start, dur = note
            # Note position relative to current scroll (notes scroll downward)
            # A note at current_beat should be at the bottom of the roll
            beat_offset = (start - current_beat) % total
            # Wrap: if beat_offset > half the total, it's behind us
            if beat_offset > total / 2:
                beat_offset -= total

            # Y position: bottom of roll = current beat, top = future
            # beat_offset > 0 means future (above), < 0 means past (below)
            note_y_bottom = ROLL_BOTTOM - int(beat_offset * pixels_per_beat)
            note_y_top = ROLL_BOTTOM - int((beat_offset + dur) * pixels_per_beat)

            # Clamp to roll area
            ny_top = max(ROLL_TOP, min(ROLL_BOTTOM, note_y_top))
            ny_bot = max(ROLL_TOP, min(ROLL_BOTTOM, note_y_bottom))

            if ny_bot <= ny_top:
                continue

            # X position based on key lane
            nx_left = ROLL_LEFT + int(key_idx * lane_w) + 1
            nx_right = ROLL_LEFT + int((key_idx + 1) * lane_w) - 1
            nx_left = max(ROLL_LEFT, nx_left)
            nx_right = min(ROLL_RIGHT, nx_right)

            if nx_right <= nx_left:
                continue

            # Color based on pitch
            pitch = KEY_PITCHES[key_idx] if key_idx < len(KEY_PITCHES) else 0
            color = NOTE_COLORS[pitch % 12]

            # Dim notes that are further away (near top of roll)
            dist_from_bottom = ROLL_BOTTOM - ny_top
            brightness = 0.5 + 0.5 * (1.0 - dist_from_bottom / ROLL_HEIGHT)

            cr = int(color[0] * brightness)
            cg = int(color[1] * brightness)
            cb = int(color[2] * brightness)

            for y in range(ny_top, ny_bot):
                for x in range(nx_left, nx_right + 1):
                    d.set_pixel(x, y, (cr, cg, cb))

    def _draw_hammers(self, d):
        """Draw 16 hammers that pivot upward when triggered."""
        roll_width = ROLL_RIGHT - ROLL_LEFT
        lane_w = roll_width / NUM_KEYS
        hammer_height = HAMMER_BOTTOM - HAMMER_TOP

        for k in range(NUM_KEYS):
            energy = self.hammer_energy[k]
            cx = ROLL_LEFT + int((k + 0.5) * lane_w)

            # Pivot point at bottom
            pivot_y = HAMMER_BOTTOM

            # Hammer swings upward: at rest hangs down, at energy=1 points up
            # Angle from vertical: 0 = hanging down, pi/2 = horizontal
            angle = energy * (math.pi * 0.4)

            # Hammer shaft
            shaft_len = hammer_height - 2
            tip_x = cx + int(math.sin(angle) * 0.5)
            tip_y = pivot_y - int(math.cos(angle) * shaft_len)
            tip_y = max(HAMMER_TOP, tip_y)

            # Draw shaft
            if energy > 0.5:
                shaft_color = HAMMER_ACTIVE
            else:
                shaft_color = HAMMER_REST

            d.draw_line(cx, pivot_y, tip_x, tip_y, shaft_color)

            # Pivot dot
            d.set_pixel(cx, pivot_y, HAMMER_PIVOT)

            # Hammer head at tip
            if energy > 0.7:
                d.set_pixel(tip_x, tip_y, HAMMER_HEAD_HIT)
                if tip_x > 0:
                    d.set_pixel(tip_x - 1, tip_y, HAMMER_HEAD_HIT)
            elif energy > 0.01:
                d.set_pixel(tip_x, tip_y, HAMMER_HEAD)

        # Mechanism rail
        d.draw_line(ROLL_LEFT, HAMMER_TOP, ROLL_RIGHT, HAMMER_TOP, HAMMER_PIVOT)

    def _draw_keys(self, d):
        """Draw piano keyboard with white and black keys."""
        roll_width = ROLL_RIGHT - ROLL_LEFT
        lane_w = roll_width / NUM_KEYS

        # Draw all white keys first
        for k in range(NUM_KEYS):
            is_black = KEY_IS_BLACK[k]
            press = self.key_press[k]

            kx_left = ROLL_LEFT + int(k * lane_w)
            kx_right = ROLL_LEFT + int((k + 1) * lane_w) - 1

            if is_black:
                continue

            # White key
            if press > 0.3:
                color = KEY_WHITE_PRESSED
            else:
                color = KEY_WHITE

            for y in range(KEY_TOP, KEY_BOTTOM + 1):
                for x in range(kx_left, kx_right + 1):
                    if x == kx_left or x == kx_right:
                        d.set_pixel(x, y, KEY_EDGE)
                    elif y == KEY_BOTTOM:
                        d.set_pixel(x, y, KEY_EDGE)
                    else:
                        d.set_pixel(x, y, color)

            # Depression effect: shift top pixels down
            if press > 0.3:
                for x in range(kx_left + 1, kx_right):
                    d.set_pixel(x, KEY_TOP, KEY_EDGE)

        # Draw black keys on top (shorter)
        black_bottom = KEY_TOP + 8
        for k in range(NUM_KEYS):
            if not KEY_IS_BLACK[k]:
                continue

            press = self.key_press[k]
            kx_left = ROLL_LEFT + int(k * lane_w)
            kx_right = ROLL_LEFT + int((k + 1) * lane_w) - 1

            if press > 0.3:
                color = KEY_BLACK_PRESSED
            else:
                color = KEY_BLACK

            for y in range(KEY_TOP, black_bottom + 1):
                for x in range(kx_left, kx_right + 1):
                    d.set_pixel(x, y, color)

            if press > 0.3:
                d.set_pixel(kx_left + 1, KEY_TOP, (50, 50, 55))

    def _draw_hud(self, d):
        """Draw tempo and pattern info."""
        bpm = TEMPO_BPMS[self.tempo_level - 1]
        d.draw_text_small(2, 0, f"{bpm}BPM", HUD_COLOR)
        name = PATTERN_NAMES[self.pattern_index]
        # Right-align pattern name (4px per char)
        name_w = len(name) * 4
        d.draw_text_small(GRID_SIZE - name_w - 2, 0, name, HUD_COLOR)

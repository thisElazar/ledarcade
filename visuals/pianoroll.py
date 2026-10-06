"""
Piano Roll
==========
Player piano: a paper roll scrolls down over a tracker bar, and every
perforation that reaches the bar fires a hammer and presses its key.

The rolls are real pieces - Satie, Bach, Beethoven, Chopin, Sousa, Joplin -
converted note for note from public-domain Mutopia Project scores by
tools/build_piano_rolls.py. The keyboard is 64 keys wide, one pixel per key,
so each piece keeps its true pitches and the two hands stay apart.

Regions:
  y=0-4:   Title of the roll, alternating with its composer
  y=7-43:  Paper roll; perforations scroll down at constant paper speed
  y=44:    Tracker bar - a note sounds when its perforation reaches it
  y=45-49: Hammers (one per key, kick up on each strike)
  y=50-63: Keyboard (64 keys, lit while held)

Controls:
  Left/Right - Adjust tempo (6 levels)
  Up/Down    - Change roll
"""

import math
from bisect import bisect_left, bisect_right

from . import Visual, Display, Colors, GRID_SIZE
from .pianoroll_data import ROLLS, TICKS_PER_BEAT


# --- Color Palette ---
PAPER_COLOR = (150, 138, 104)
PAPER_DARK = (128, 117, 88)      # octave guide under every C
ROLL_FRAME = (100, 70, 30)
TRACKER_BAR = (190, 140, 50)

HAMMER_REST = (60, 60, 68)
HAMMER_HEAD_HIT = (255, 255, 220)

KEY_WHITE = (170, 170, 170)
KEY_BLACK = (20, 20, 24)
KEY_EDGE = (90, 90, 100)

HUD_COLOR = (160, 160, 170)

# Perforation / held-key colors by staff: right hand, left hand
HAND_COLORS = [(210, 40, 30), (20, 60, 200)]
HAND_KEY_COLORS = [(255, 90, 60), (70, 130, 255)]

# --- Layout ---
ROLL_TOP = 7
ROLL_BOTTOM = 43
ROLL_HEIGHT = ROLL_BOTTOM - ROLL_TOP + 1

HAMMER_TOP = 45
HAMMER_BOTTOM = 49

KEY_TOP = 50
KEY_BOTTOM = 63
BLACK_KEY_BOTTOM = KEY_TOP + 8

NUM_KEYS = GRID_SIZE  # one pixel per key
BLACK_PITCHES = (1, 3, 6, 8, 10)

# A real roll runs at one paper speed for the whole piece, so fast music is
# short perforations rather than a faster scroll. The tempo lever scales it.
PAPER_SPEED = 9.0  # pixels per second at the piece's own tempo
TEMPO_SCALES = [0.5, 0.75, 1.0, 1.25, 1.5, 2.0]

TITLE_SECONDS = 4.0    # header alternates title / composer this often
TEMPO_SECONDS = 2.0    # header shows the tempo this long after a change
TAIL_SECONDS = 2.0     # blank paper after the last note, before the next roll

# Per roll: note start ticks (for bisect) and the longest note
ROLL_STARTS = [[n[0] for n in r['notes']] for r in ROLLS]
ROLL_MAX_DUR = [max(n[1] for n in r['notes']) for r in ROLLS]
ROLL_END = [max(n[0] + n[1] for n in r['notes']) for r in ROLLS]


class PianoRoll(Visual):
    name = "PIANO ROLL"
    description = "Player piano"
    category = "music"
    GUIDE = {
        'desc': 'A player piano with 64 keys. Real pieces - Satie, Bach, Beethoven, Chopin, Sousa, Joplin - scroll past as perforations in a paper roll; each one fires a hammer and presses its key as it crosses the brass tracker bar. Watch what the left hand does: a slow bass-and-chord sway in the Gymnopedie, broken chords in the Bach prelude, the leaping stride of a rag.',
        'credit': 'Scores: Mutopia Project',
        'legend': {
            'top line': 'Title of the roll, alternating with its composer.',
            '# BPM': 'Tempo in quarter notes per minute, shown after you change it.',
            'red / blue': 'Notes written on the upper staff (right hand) / lower staff (left hand).',
        },
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.tempo_level = 3       # 1-6
        self.tempo_shown = 0.0     # seconds left to show the tempo
        self.roll_index = 0
        self._load_roll()

    def _load_roll(self):
        """Thread the current roll: first note just entering at the top."""
        self.roll = ROLLS[self.roll_index]
        # Ticks of music per pixel of paper at this piece's tempo
        self.ticks_per_px = self.roll['bpm'] / 60.0 * TICKS_PER_BEAT / PAPER_SPEED
        self.pos = -ROLL_HEIGHT * self.ticks_per_px   # tick at the tracker bar
        self.next_note = 0
        self.hammer = [0.0] * NUM_KEYS       # 0..1, decays
        self.held_until = [self.pos] * NUM_KEYS   # tick at which the key lifts
        self.key_hand = [0] * NUM_KEYS

    def _bpm(self):
        return round(self.roll['bpm'] * TEMPO_SCALES[self.tempo_level - 1])

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.tempo_level = min(6, self.tempo_level + 1)
            self.tempo_shown = TEMPO_SECONDS
            consumed = True
        elif input_state.left_pressed:
            self.tempo_level = max(1, self.tempo_level - 1)
            self.tempo_shown = TEMPO_SECONDS
            consumed = True
        if input_state.up_pressed:
            self.roll_index = (self.roll_index + 1) % len(ROLLS)
            self._load_roll()
            consumed = True
        elif input_state.down_pressed:
            self.roll_index = (self.roll_index - 1) % len(ROLLS)
            self._load_roll()
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt
        self.tempo_shown = max(0.0, self.tempo_shown - dt)

        ticks_per_sec = self._bpm() / 60.0 * TICKS_PER_BEAT
        self.pos += ticks_per_sec * dt

        # Strike every note whose perforation has reached the tracker bar
        notes = self.roll['notes']
        low = self.roll['low']
        while self.next_note < len(notes) and notes[self.next_note][0] <= self.pos:
            start, dur, pitch, hand = notes[self.next_note]
            key = pitch - low
            self.hammer[key] = 1.0
            self.held_until[key] = max(self.held_until[key], start + dur)
            self.key_hand[key] = hand
            self.next_note += 1

        for i in range(NUM_KEYS):
            if self.hammer[i] > 0.0:
                self.hammer[i] = max(0.0, self.hammer[i] - 6.0 * dt)

        # End of the roll: put the next one on
        if self.pos > ROLL_END[self.roll_index] + TAIL_SECONDS * ticks_per_sec:
            self.roll_index = (self.roll_index + 1) % len(ROLLS)
            self._load_roll()

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        self._draw_roll(d)
        self._draw_hammers(d)
        self._draw_keys(d)
        self._draw_hud(d)

    def _draw_roll(self, d):
        """Draw the paper and the perforations currently over it."""
        low = self.roll['low']

        # Paper, with a darker guide line under every C
        for x in range(NUM_KEYS):
            color = PAPER_DARK if (low + x) % 12 == 0 else PAPER_COLOR
            for y in range(ROLL_TOP, ROLL_BOTTOM + 1):
                d.set_pixel(x, y, color)

        d.draw_line(0, ROLL_TOP - 1, GRID_SIZE - 1, ROLL_TOP - 1, ROLL_FRAME)
        d.draw_line(0, ROLL_BOTTOM + 1, GRID_SIZE - 1, ROLL_BOTTOM + 1, TRACKER_BAR)

        # Only the notes that can overlap the visible stretch of paper
        notes = self.roll['notes']
        starts = ROLL_STARTS[self.roll_index]
        top_tick = self.pos + ROLL_HEIGHT * self.ticks_per_px
        first = bisect_left(starts, self.pos - ROLL_MAX_DUR[self.roll_index])
        last = bisect_right(starts, top_tick)

        for start, dur, pitch, hand in notes[first:last]:
            # The tracker bar reads the paper at ROLL_BOTTOM; later is higher
            # (rounding up, so a hole touches the bar exactly when it sounds)
            y_bot = ROLL_BOTTOM - math.ceil((start - self.pos) / self.ticks_per_px)
            y_top = ROLL_BOTTOM - math.ceil((start + dur - self.pos) / self.ticks_per_px) + 1
            # Leave a pixel of paper between repeated notes on one key
            y_top = min(y_top + 1, y_bot)
            x = pitch - low
            color = HAND_COLORS[hand]
            for y in range(max(ROLL_TOP, y_top), min(ROLL_BOTTOM, y_bot) + 1):
                d.set_pixel(x, y, color)

    def _draw_hammers(self, d):
        """Draw one hammer per key; a strike kicks it up toward the bar."""
        reach = HAMMER_BOTTOM - HAMMER_TOP
        for x in range(NUM_KEYS):
            energy = self.hammer[x]
            if energy <= 0.0:
                d.set_pixel(x, HAMMER_BOTTOM, HAMMER_REST)
                continue
            tip_y = HAMMER_BOTTOM - int(energy * reach + 0.5)
            for y in range(tip_y + 1, HAMMER_BOTTOM + 1):
                d.set_pixel(x, y, HAMMER_REST)
            d.set_pixel(x, tip_y, HAMMER_HEAD_HIT)

    def _draw_keys(self, d):
        """Draw the 64-key keyboard, one pixel per key; held keys light up."""
        low = self.roll['low']
        for x in range(NUM_KEYS):
            held = self.held_until[x] > self.pos
            lit = HAND_KEY_COLORS[self.key_hand[x]]
            if (low + x) % 12 in BLACK_PITCHES:
                # Black key on top; below it, the gap between two white keys
                color = lit if held else KEY_BLACK
                for y in range(KEY_TOP, BLACK_KEY_BOTTOM + 1):
                    d.set_pixel(x, y, color)
                for y in range(BLACK_KEY_BOTTOM + 1, KEY_BOTTOM + 1):
                    d.set_pixel(x, y, KEY_EDGE)
            else:
                color = lit if held else KEY_WHITE
                for y in range(KEY_TOP, KEY_BOTTOM + 1):
                    d.set_pixel(x, y, color)

    def _draw_hud(self, d):
        """Draw the roll's title / composer, or the tempo just after a change."""
        if self.tempo_shown > 0.0:
            text = f"{self._bpm()} BPM"
        elif int(self.time / TITLE_SECONDS) % 2 == 0:
            text = self.roll['title']
        else:
            text = self.roll['composer']
        d.draw_text_small(1, 0, text, HUD_COLOR)

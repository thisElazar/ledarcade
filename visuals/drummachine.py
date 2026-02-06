"""
DrumMachine - TR-808 Step Sequencer Visualization
==================================================
A 16-step drum machine with sweeping playhead. Each row represents a
different drum instrument (kick, snare, hi-hat, etc.) with procedurally
generated patterns across multiple genres.

Controls:
  Left/Right - Adjust BPM (80-180)
  Up/Down    - Cycle genre pattern
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Drum instrument definitions: (name, color)
INSTRUMENTS = [
    ("KICK",  (255, 40, 40)),     # Red
    ("SNARE", (255, 220, 40)),    # Yellow
    ("HAT",   (40, 220, 255)),    # Cyan
    ("OPEN",  (40, 255, 120)),    # Green
    ("CLAP",  (255, 100, 200)),   # Pink
    ("TOM",   (255, 140, 40)),    # Orange
    ("RIM",   (160, 80, 255)),    # Purple
    ("PERC",  (200, 200, 200)),   # White/gray
]

# Genre patterns: each genre is a dict mapping instrument index to list of 16 steps (1=on, 0=off)
PATTERNS = {
    "House": {
        0: [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],  # kick: four on floor
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],  # snare: 2 and 4
        2: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,0],  # hat: 8ths
        3: [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,1,0],  # open hat: offbeats
        4: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,1],  # clap
        5: [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0],  # tom
        6: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,1,0,0],  # rim
        7: [0,0,1,0, 0,0,0,0, 0,0,1,0, 0,0,0,0],  # perc
    },
    "HipHop": {
        0: [1,0,0,0, 0,0,0,0, 1,0,1,0, 0,0,0,0],  # kick: syncopated
        1: [0,0,0,0, 1,0,0,1, 0,0,0,0, 1,0,0,0],  # snare: lazy swing
        2: [1,0,1,0, 1,0,1,0, 1,0,1,0, 1,0,1,1],  # hat: rolling
        3: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,0,1],  # open hat
        4: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],  # clap
        5: [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,1,0],  # tom
        6: [0,0,0,1, 0,0,0,0, 0,0,0,1, 0,0,0,0],  # rim
        7: [0,0,0,0, 0,1,0,0, 0,0,0,0, 0,1,0,0],  # perc
    },
    "Funk": {
        0: [1,0,0,1, 0,0,1,0, 0,1,0,0, 1,0,0,0],  # kick: syncopated
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],  # snare
        2: [1,1,1,1, 1,1,1,1, 1,1,1,1, 1,1,1,1],  # hat: 16ths
        3: [0,0,0,0, 0,0,0,0, 0,0,1,0, 0,0,0,0],  # open hat
        4: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],  # clap on 2 and 4
        5: [0,0,0,0, 0,0,0,0, 1,0,0,1, 0,0,0,0],  # tom
        6: [0,1,0,0, 0,1,0,0, 0,1,0,0, 0,1,0,0],  # rim: and beats
        7: [0,0,1,0, 0,0,0,1, 0,0,1,0, 0,0,0,1],  # perc: ghost notes
    },
    "Break": {
        0: [1,0,0,0, 0,0,1,0, 0,1,0,0, 0,0,0,0],  # kick: amen-ish
        1: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,1,0],  # snare: breakbeat
        2: [1,0,1,1, 0,0,1,0, 1,0,1,1, 0,0,1,0],  # hat: shuffled
        3: [0,0,0,0, 0,1,0,0, 0,0,0,0, 0,1,0,0],  # open hat
        4: [0,0,0,0, 1,0,0,0, 0,0,0,0, 0,0,1,0],  # clap
        5: [0,0,0,0, 0,0,0,0, 0,1,0,0, 0,0,0,1],  # tom: fills
        6: [0,0,0,0, 0,0,1,0, 0,0,0,0, 0,0,0,0],  # rim
        7: [0,0,0,1, 0,0,0,0, 0,0,0,1, 0,0,0,0],  # perc
    },
    "Techno": {
        0: [1,0,0,0, 1,0,0,0, 1,0,0,0, 1,0,0,0],  # kick: four on floor
        1: [0,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],  # snare: sparse
        2: [0,0,1,0, 0,0,1,0, 0,0,1,0, 0,0,1,0],  # hat: offbeat
        3: [0,0,0,0, 0,0,0,1, 0,0,0,0, 0,0,0,1],  # open hat
        4: [0,0,0,0, 1,0,0,0, 0,0,0,0, 1,0,0,0],  # clap: 2 and 4
        5: [0,0,0,0, 0,0,0,0, 0,0,0,0, 0,0,1,0],  # tom
        6: [1,0,0,0, 0,0,0,0, 1,0,0,0, 0,0,0,0],  # rim
        7: [0,1,0,0, 0,0,0,0, 0,1,0,0, 0,0,0,0],  # perc
    },
}

GENRE_NAMES = list(PATTERNS.keys())


class DrumMachine(Visual):
    name = "DRUM MACHINE"
    description = "TR-808 sequencer"
    category = "music"

    # Grid layout constants
    PAD_COLS = 16
    PAD_ROWS = 8
    # Each pad is 3px wide with 1px gap = 4px per step, 16 steps = 64px
    PAD_W = 3
    PAD_GAP_X = 1
    # Top area for text = 8px, remaining 56px for 8 rows = 7px per row
    HEADER_H = 8
    ROW_H = 7
    PAD_H = 5

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.bpm = 120
        self.genre_index = 0
        self.step_time = 0.0       # accumulator for step timing
        self.current_step = 0      # 0-15
        self.flash_timers = {}     # (row, col) -> remaining flash time
        self.flash_duration = 0.08
        self._load_pattern()

    def _load_pattern(self):
        """Load the current genre pattern into the grid."""
        genre = GENRE_NAMES[self.genre_index]
        self.pattern = PATTERNS[genre]

    def _step_interval(self):
        """Seconds per 16th-note step at current BPM."""
        # BPM is quarter notes per minute; 4 steps per beat
        return 60.0 / (self.bpm * 4)

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right adjust BPM
        if input_state.right_pressed:
            self.bpm = min(180, self.bpm + 5)
            consumed = True
        if input_state.left_pressed:
            self.bpm = max(80, self.bpm - 5)
            consumed = True

        # Up/Down cycle genre
        if input_state.up_pressed:
            self.genre_index = (self.genre_index - 1) % len(GENRE_NAMES)
            self._load_pattern()
            consumed = True
        if input_state.down_pressed:
            self.genre_index = (self.genre_index + 1) % len(GENRE_NAMES)
            self._load_pattern()
            consumed = True

        return consumed

    def update(self, dt):
        self.time += dt

        # Advance step sequencer
        interval = self._step_interval()
        self.step_time += dt
        while self.step_time >= interval:
            self.step_time -= interval
            self.current_step = (self.current_step + 1) % self.PAD_COLS

            # Trigger flashes for active pads on this step
            for row in range(self.PAD_ROWS):
                if self.pattern.get(row, [0]*16)[self.current_step]:
                    self.flash_timers[(row, self.current_step)] = self.flash_duration

        # Decay flash timers
        expired = []
        for key in self.flash_timers:
            self.flash_timers[key] -= dt
            if self.flash_timers[key] <= 0:
                expired.append(key)
        for key in expired:
            del self.flash_timers[key]

    def draw(self):
        self.display.clear(Colors.BLACK)

        genre = GENRE_NAMES[self.genre_index]

        # -- Header: genre name left, BPM right --
        self.display.draw_text_small(2, 1, genre.upper(), (180, 180, 180))
        bpm_str = str(self.bpm)
        bpm_x = GRID_SIZE - len(bpm_str) * 4 - 2
        self.display.draw_text_small(bpm_x, 1, bpm_str, (180, 180, 180))

        # -- Draw pads --
        for row in range(self.PAD_ROWS):
            base_color = INSTRUMENTS[row][1]
            y_top = self.HEADER_H + row * self.ROW_H + 1

            for col in range(self.PAD_COLS):
                x_left = col * (self.PAD_W + self.PAD_GAP_X)
                active = self.pattern.get(row, [0]*16)[col]

                # Determine pad color
                if (row, col) in self.flash_timers:
                    # Flashing white on hit
                    t = self.flash_timers[(row, col)] / self.flash_duration
                    color = (
                        min(255, int(base_color[0] + (255 - base_color[0]) * t)),
                        min(255, int(base_color[1] + (255 - base_color[1]) * t)),
                        min(255, int(base_color[2] + (255 - base_color[2]) * t)),
                    )
                elif active:
                    # Active pad: full color
                    color = base_color
                else:
                    # Inactive pad: dim color
                    color = (base_color[0] // 6, base_color[1] // 6, base_color[2] // 6)

                # Draw the pad rectangle
                for py in range(self.PAD_H):
                    for px in range(self.PAD_W):
                        sx = x_left + px
                        sy = y_top + py
                        if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                            self.display.set_pixel(sx, sy, color)

        # -- Draw playhead (vertical line) --
        head_x = self.current_step * (self.PAD_W + self.PAD_GAP_X) + self.PAD_W // 2
        # Pulsing brightness based on time
        pulse = int(180 + 75 * math.sin(self.time * 12.0))
        pulse = max(0, min(255, pulse))
        head_color = (pulse, pulse, pulse)

        for y in range(self.HEADER_H, GRID_SIZE):
            if 0 <= head_x < GRID_SIZE:
                # Blend: make playhead visible over pads
                existing = self._get_pad_at(head_x, y)
                if existing:
                    # Additive blend
                    blended = (
                        min(255, existing[0] + pulse // 3),
                        min(255, existing[1] + pulse // 3),
                        min(255, existing[2] + pulse // 3),
                    )
                    self.display.set_pixel(head_x, y, blended)
                else:
                    self.display.set_pixel(head_x, y, (pulse // 4, pulse // 4, pulse // 4))

        # -- Draw beat markers at bottom --
        marker_y = GRID_SIZE - 1
        for beat in range(4):
            step = beat * 4
            mx = step * (self.PAD_W + self.PAD_GAP_X) + self.PAD_W // 2
            if 0 <= mx < GRID_SIZE:
                brightness = 120 if step == self.current_step else 40
                self.display.set_pixel(mx, marker_y, (brightness, brightness, brightness))

    def _get_pad_at(self, x, y):
        """Return the color of any pad at pixel (x, y), or None."""
        col = x // (self.PAD_W + self.PAD_GAP_X)
        x_in_cell = x % (self.PAD_W + self.PAD_GAP_X)
        if x_in_cell >= self.PAD_W:
            return None  # In the gap
        if col < 0 or col >= self.PAD_COLS:
            return None

        row_pixel = y - self.HEADER_H
        if row_pixel < 0:
            return None
        row = row_pixel // self.ROW_H
        y_in_row = row_pixel % self.ROW_H
        if row < 0 or row >= self.PAD_ROWS:
            return None
        if y_in_row < 1 or y_in_row >= 1 + self.PAD_H:
            return None  # In the gap between rows

        base_color = INSTRUMENTS[row][1]
        active = self.pattern.get(row, [0]*16)[col]

        if (row, col) in self.flash_timers:
            t = self.flash_timers[(row, col)] / self.flash_duration
            return (
                min(255, int(base_color[0] + (255 - base_color[0]) * t)),
                min(255, int(base_color[1] + (255 - base_color[1]) * t)),
                min(255, int(base_color[2] + (255 - base_color[2]) * t)),
            )
        elif active:
            return base_color
        else:
            return (base_color[0] // 6, base_color[1] // 6, base_color[2] // 6)

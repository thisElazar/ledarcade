"""
Latin Grooves - Multi-instrument Latin step sequencer on 64x64 LED matrix.
==========================================================================
A 16-step drum machine with Latin percussion instruments and genre presets.

Controls:
  Left/Right - Adjust BPM (40-230)
  Up/Down    - Cycle genre pattern
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


# Latin percussion instruments: (name, color)
INSTRUMENTS = [
    ("CLAVE",   (255, 255, 255)),  # White
    ("BELL",    (255, 220, 40)),   # Yellow
    ("HI CGA",  (255, 160, 40)),  # Orange
    ("LO CGA",  (255, 40, 40)),   # Red
    ("TIMBAL", (40, 220, 255)),    # Cyan
    ("GUIRO",  (40, 255, 120)),    # Green
    ("BASS",   (160, 80, 255)),    # Purple
    ("KEYS",   (255, 100, 200)),   # Pink
]

# Genre patterns: each maps instrument index to 16-step arrays
PATTERNS = {
    "Salsa": {
        0: [1,0,0,1,0,0,1,0, 0,0,1,0,1,0,0,0],  # son clave 3-2
        1: [1,0,0,0,1,0,1,0, 1,0,0,0,1,0,1,0],  # campana bell
        2: [0,0,1,0,0,0,0,1, 0,0,1,0,0,0,0,1],  # hi conga slaps
        3: [1,0,0,0,1,0,1,1, 1,0,0,0,1,0,1,1],  # lo conga tumbao
        4: [1,0,1,1,0,1,1,0, 1,1,0,1,1,0,1,0],  # cascara on timbales
        5: [1,0,1,0,1,0,1,0, 1,0,1,0,1,0,1,0],  # guiro steady
        6: [0,0,0,1,0,0,0,0, 0,0,0,1,0,0,0,0],  # bass anticipated
        7: [0,1,0,1,0,1,0,1, 0,1,0,1,0,1,0,1],  # piano montuno
    },
    "Bossa Nova": {
        0: [1,0,0,1,0,0,1,0, 0,1,0,0,1,0,0,0],  # bossa clave
        1: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no bell
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no lo conga
        4: [1,0,1,0,1,0,1,0, 1,0,1,0,1,0,1,0],  # hi-hat 8ths
        5: [1,0,1,0,1,0,1,0, 1,0,1,0,1,0,1,0],  # shaker 8ths
        6: [1,0,0,0,0,0,0,0, 1,0,0,0,0,0,0,0],  # bass on 1 and 3
        7: [1,0,0,1,0,1,0,0, 1,0,0,1,0,1,0,0],  # guitar pattern
    },
    "Samba": {
        0: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no clave
        1: [1,0,0,1,0,0,1,0, 1,0,0,0,1,0,0,1],  # agogo bells
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [0,0,0,0,0,0,0,0, 1,0,0,0,0,0,0,0],  # surdo low on beat 2
        4: [1,1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1],  # caixa 16ths
        5: [1,1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1],  # shaker 16ths
        6: [1,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # surdo high on 1
        7: [1,0,1,1,0,1,1,0, 1,0,0,0,1,0,0,1],  # tamborim
    },
    "Cha-Cha-Cha": {
        0: [0,0,1,0,1,0,0,0, 1,0,0,1,0,0,1,0],  # son clave 2-3
        1: [1,0,0,0,1,0,0,0, 1,0,0,0,1,0,0,0],  # cowbell quarters
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no lo conga
        4: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no timbale
        5: [1,0,0,0,0,1,0,0, 1,0,0,0,0,1,0,0],  # guiro long-short
        6: [1,0,0,0,0,0,0,0, 1,0,0,0,0,0,0,0],  # bass
        7: [0,0,0,0,0,0,1,1, 1,0,0,0,0,0,1,1],  # cha-cha-CHA
    },
    "Mambo": {
        0: [1,0,0,1,0,0,1,0, 0,0,1,0,1,0,0,0],  # son clave 3-2
        1: [1,0,1,0,1,0,1,0, 1,0,1,0,1,0,1,0],  # bell 8ths
        2: [0,0,1,0,0,0,0,1, 0,0,1,0,0,0,0,1],  # hi conga
        3: [1,0,0,0,1,0,1,1, 1,0,0,0,1,0,1,1],  # lo conga tumbao
        4: [1,0,1,1,0,1,1,0, 1,1,0,1,1,0,1,0],  # cascara
        5: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no guiro
        6: [0,0,0,1,0,0,0,0, 0,0,0,1,0,0,0,0],  # bass anticipated
        7: [0,0,1,0,0,1,0,0, 0,0,1,0,0,1,0,0],  # horn riffs
    },
    "Cumbia": {
        0: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no clave
        1: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no bell
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no lo conga
        4: [0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0],  # snare on 2 and 4
        5: [1,0,1,0,1,0,1,0, 1,0,1,0,1,0,1,0],  # guacharaca 8ths
        6: [1,0,0,0,0,0,0,0, 1,0,0,0,0,0,0,0],  # kick on 1 and 3
        7: [1,0,0,0,1,0,0,0, 1,0,0,0,1,0,0,0],  # accordion/keys
    },
    "Merengue": {
        0: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no clave
        1: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no bell
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no lo conga
        4: [1,0,1,1,0,1,1,0, 1,0,1,1,0,1,1,0],  # tambora
        5: [1,1,1,1,1,1,1,1, 1,1,1,1,1,1,1,1],  # guira 16ths
        6: [1,0,0,0,0,0,0,0, 1,0,0,0,0,0,0,0],  # bass on downbeats
        7: [0,1,0,1,0,1,0,1, 0,1,0,1,0,1,0,1],  # keys offbeat
    },
    "Reggaeton": {
        0: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no clave
        1: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no bell
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no lo conga
        4: [0,0,0,1,0,0,1,0, 0,0,0,1,0,0,1,0],  # dembow snare
        5: [1,0,1,0,1,0,1,0, 1,0,1,0,1,0,1,0],  # hi-hat 8ths
        6: [1,0,0,0,1,0,0,0, 1,0,0,0,1,0,0,0],  # kick four-on-floor
        7: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no keys
    },
    "Guaguanco": {
        0: [1,0,0,1,0,0,0,1, 0,0,1,0,1,0,0,0],  # rumba clave 3-2
        1: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no bell
        2: [0,0,1,0,1,0,0,1, 0,0,1,0,1,0,0,1],  # quinto improvise
        3: [1,0,0,1,0,0,1,0, 1,0,0,1,0,0,1,0],  # tumbadora ostinato
        4: [1,0,1,1,0,1,1,0, 1,1,0,1,1,0,1,0],  # palitos/cascara
        5: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no guiro
        6: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no bass
        7: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no keys
    },
    "Mozambique": {
        0: [0,0,1,0,1,0,0,0, 1,0,0,1,0,0,0,1],  # rumba clave 2-3
        1: [1,0,1,1,0,1,1,0, 1,1,0,1,1,0,1,0],  # bell pattern
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [1,0,0,1,0,0,1,0, 0,0,1,0,0,1,0,0],  # congas
        4: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no timbale
        5: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no guiro
        6: [1,0,0,0,1,0,0,0, 1,0,0,0,1,0,0,0],  # bombo bass
        7: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no keys
    },
    "Songo": {
        0: [0,0,1,0,1,0,0,0, 1,0,0,1,0,0,0,1],  # rumba clave 2-3 (loose)
        1: [1,0,0,0,0,0,0,0, 1,0,0,0,0,0,0,0],  # cymbal bell half-notes
        2: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no hi conga
        3: [0,0,0,1,0,0,0,0, 0,0,0,1,0,0,0,0],  # conga accents
        4: [0,0,1,0,1,0,0,1, 0,0,0,0,1,0,0,0],  # snare syncopated
        5: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no guiro
        6: [0,0,0,1,0,0,0,0, 0,1,0,0,0,0,0,1],  # bass tumbao
        7: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no keys
    },
    "Bembe": {
        0: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no clave
        1: [1,0,1,1,0,1,1,0, 1,1,0,1,0,0,0,0],  # bembe bell (approx 16)
        2: [0,0,0,0,1,0,0,0, 0,0,0,0,1,0,0,0],  # hi conga
        3: [1,0,0,0,0,0,1,0, 0,0,1,0,0,0,0,0],  # lo conga
        4: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no timbale
        5: [1,0,1,0,1,0,1,0, 1,0,1,0,1,0,1,0],  # shaker
        6: [1,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # bass
        7: [0,0,0,0,0,0,0,0, 0,0,0,0,0,0,0,0],  # no keys
    },
}

PATTERN_BPM = {
    "Salsa": 95,
    "Bossa Nova": 125,
    "Samba": 105,
    "Cha-Cha-Cha": 120,
    "Mambo": 115,
    "Cumbia": 95,
    "Merengue": 150,
    "Reggaeton": 90,
    "Guaguanco": 105,
    "Mozambique": 110,
    "Songo": 100,
    "Bembe": 120,
}

GENRE_NAMES = list(PATTERNS.keys())


class LatinGrooves(Visual):
    name = "LATIN GROOVES"
    description = "Latin percussion sequencer"
    category = "music"

    PAD_COLS = 16
    PAD_ROWS = 8
    PAD_W = 3
    PAD_GAP_X = 1
    HEADER_H = 8
    ROW_H = 7
    PAD_H = 5

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.bpm = 95
        self.genre_index = 0
        self.step_time = 0.0
        self.current_step = 0
        self.flash_timers = {}
        self.flash_duration = 0.08
        self._load_pattern()

    def _load_pattern(self):
        genre = GENRE_NAMES[self.genre_index]
        self.pattern = PATTERNS[genre]
        self.bpm = PATTERN_BPM.get(genre, 100)

    def _step_interval(self):
        return 60.0 / (self.bpm * 4)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.right_pressed:
            self.bpm = min(230, self.bpm + 5)
            consumed = True
        if input_state.left_pressed:
            self.bpm = max(40, self.bpm - 5)
            consumed = True

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

        interval = self._step_interval()
        self.step_time += dt
        while self.step_time >= interval:
            self.step_time -= interval
            self.current_step = (self.current_step + 1) % self.PAD_COLS

            for row in range(self.PAD_ROWS):
                if self.pattern.get(row, [0]*16)[self.current_step]:
                    self.flash_timers[(row, self.current_step)] = self.flash_duration

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

        # Header: genre name left, BPM right
        self.display.draw_text_small(2, 1, genre.upper(), (180, 180, 180))
        bpm_str = str(self.bpm)
        bpm_x = GRID_SIZE - len(bpm_str) * 4 - 2
        self.display.draw_text_small(bpm_x, 1, bpm_str, (180, 180, 180))

        # Draw pads
        for row in range(self.PAD_ROWS):
            base_color = INSTRUMENTS[row][1]
            y_top = self.HEADER_H + row * self.ROW_H + 1

            for col in range(self.PAD_COLS):
                x_left = col * (self.PAD_W + self.PAD_GAP_X)
                active = self.pattern.get(row, [0]*16)[col]

                if (row, col) in self.flash_timers:
                    t = self.flash_timers[(row, col)] / self.flash_duration
                    color = (
                        min(255, int(base_color[0] + (255 - base_color[0]) * t)),
                        min(255, int(base_color[1] + (255 - base_color[1]) * t)),
                        min(255, int(base_color[2] + (255 - base_color[2]) * t)),
                    )
                elif active:
                    color = base_color
                else:
                    color = (base_color[0] // 6, base_color[1] // 6, base_color[2] // 6)

                for py in range(self.PAD_H):
                    for px in range(self.PAD_W):
                        sx = x_left + px
                        sy = y_top + py
                        if 0 <= sx < GRID_SIZE and 0 <= sy < GRID_SIZE:
                            self.display.set_pixel(sx, sy, color)

        # Playhead
        head_x = self.current_step * (self.PAD_W + self.PAD_GAP_X) + self.PAD_W // 2
        pulse = int(180 + 75 * math.sin(self.time * 12.0))
        pulse = max(0, min(255, pulse))

        for y in range(self.HEADER_H, GRID_SIZE):
            if 0 <= head_x < GRID_SIZE:
                existing = self._get_pad_at(head_x, y)
                if existing:
                    blended = (
                        min(255, existing[0] + pulse // 3),
                        min(255, existing[1] + pulse // 3),
                        min(255, existing[2] + pulse // 3),
                    )
                    self.display.set_pixel(head_x, y, blended)
                else:
                    self.display.set_pixel(head_x, y, (pulse // 4, pulse // 4, pulse // 4))

        # Beat markers
        marker_y = GRID_SIZE - 1
        for beat in range(4):
            step = beat * 4
            mx = step * (self.PAD_W + self.PAD_GAP_X) + self.PAD_W // 2
            if 0 <= mx < GRID_SIZE:
                brightness = 120 if step == self.current_step else 40
                self.display.set_pixel(mx, marker_y, (brightness, brightness, brightness))

    def _get_pad_at(self, x, y):
        col = x // (self.PAD_W + self.PAD_GAP_X)
        x_in_cell = x % (self.PAD_W + self.PAD_GAP_X)
        if x_in_cell >= self.PAD_W:
            return None
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
            return None

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

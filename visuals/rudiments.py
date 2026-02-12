"""PAS 40 International Drum Rudiments on 64x64 LED matrix."""

import math
from . import Visual

# ── Note types ──────────────────────────────────────────────────────
N = 'n'     # normal
A = 'a'     # accented
FN = 'fn'   # flam + normal
FA = 'fa'   # flam + accented
DN = 'dn'   # drag + normal
DA = 'da'   # drag + accented

# ── Categories ──────────────────────────────────────────────────────
CATEGORIES = ["ROLLS", "DIDDLES", "FLAMS", "DRAGS"]
CAT_COLORS = [
    (220, 60, 60),    # Rolls  = red
    (50, 200, 80),    # Diddles = green
    (230, 190, 50),   # Flams  = gold
    (60, 140, 255),   # Drags  = blue
]

# ── Hand colors ─────────────────────────────────────────────────────
R_NORM  = (255, 160, 40)
R_ACC   = (255, 220, 80)
R_GRACE = (140, 90, 25)
L_NORM  = (60, 140, 255)
L_ACC   = (120, 200, 255)
L_GRACE = (30, 70, 140)

FLASH_COLOR = (255, 255, 255)
HEADER_BG = (20, 20, 30)
TEXT_DIM = (120, 120, 140)
DIVIDER_COLOR = (50, 50, 60)

# ── Layout constants ────────────────────────────────────────────────
NOTE_X_MIN = 4
NOTE_X_MAX = 60
R_LANE_Y = 24   # center of right-hand lane
L_LANE_Y = 46   # center of left-hand lane

# ── All 40 PAS rudiments ───────────────────────────────────────────
RUDIMENTS = [
    # ── ROLLS (cat 0) ────────────────────────────────────
    {'name': 'SINGLE STROKE ROLL', 'short': 'SGL ROLL',
     'cat': 0, 'pas': 1, 'div': 4,
     'notes': [('R',N),('L',N),('R',N),('L',N),('R',N),('L',N),('R',N),('L',N)]},

    {'name': 'SINGLE STROKE FOUR', 'short': 'SGL FOUR',
     'cat': 0, 'pas': 2, 'div': 4,
     'notes': [('R',A),('L',N),('R',N),('L',N)]},

    {'name': 'SINGLE STROKE SEVEN', 'short': 'SGL SEVEN',
     'cat': 0, 'pas': 3, 'div': 4,
     'notes': [('R',A),('L',N),('R',N),('L',N),('R',N),('L',N),('R',N)]},

    {'name': 'MULTIPLE BOUNCE ROLL', 'short': 'BUZZ ROLL',
     'cat': 0, 'pas': 4, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N)]},

    {'name': 'TRIPLE STROKE ROLL', 'short': 'TRIPLE',
     'cat': 0, 'pas': 5, 'div': 6,
     'notes': [('R',N),('R',N),('R',N),('L',N),('L',N),('L',N)]},

    {'name': 'DOUBLE STROKE OPEN ROLL', 'short': 'DBL OPEN',
     'cat': 0, 'pas': 6, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N)]},

    {'name': 'FIVE STROKE ROLL', 'short': 'FIVE ROLL',
     'cat': 0, 'pas': 7, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',A)]},

    {'name': 'SIX STROKE ROLL', 'short': 'SIX ROLL',
     'cat': 0, 'pas': 8, 'div': 4,
     'notes': [('R',A),('L',N),('L',N),('R',N),('R',N),('L',A)]},

    {'name': 'SEVEN STROKE ROLL', 'short': 'SEVEN ROLL',
     'cat': 0, 'pas': 9, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',A)]},

    {'name': 'NINE STROKE ROLL', 'short': 'NINE ROLL',
     'cat': 0, 'pas': 10, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',A)]},

    {'name': 'TEN STROKE ROLL', 'short': 'TEN ROLL',
     'cat': 0, 'pas': 11, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',A),('L',A)]},

    {'name': 'ELEVEN STROKE ROLL', 'short': 'ELEVEN ROLL',
     'cat': 0, 'pas': 12, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',A)]},

    {'name': 'THIRTEEN STROKE ROLL', 'short': 'THIRTEEN',
     'cat': 0, 'pas': 13, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',A)]},

    {'name': 'FIFTEEN STROKE ROLL', 'short': 'FIFTEEN',
     'cat': 0, 'pas': 14, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',A)]},

    {'name': 'SEVENTEEN STROKE ROLL', 'short': 'SEVENTEEN',
     'cat': 0, 'pas': 15, 'div': 4,
     'notes': [('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',N),('R',N),('L',N),('L',N),('R',A)]},

    # ── DIDDLES (cat 1) ──────────────────────────────────
    {'name': 'SINGLE PARADIDDLE', 'short': 'PARADIDDLE',
     'cat': 1, 'pas': 16, 'div': 4,
     'notes': [('R',A),('L',N),('R',N),('R',N),('L',A),('R',N),('L',N),('L',N)]},

    {'name': 'DOUBLE PARADIDDLE', 'short': 'DBL PARA',
     'cat': 1, 'pas': 17, 'div': 4,
     'notes': [('R',A),('L',N),('R',N),('L',N),('R',N),('R',N),('L',A),('R',N),('L',N),('R',N),('L',N),('L',N)]},

    {'name': 'TRIPLE PARADIDDLE', 'short': 'TRP PARA',
     'cat': 1, 'pas': 18, 'div': 4,
     'notes': [('R',A),('L',N),('R',N),('L',N),('R',N),('L',N),('R',N),('R',N),
               ('L',A),('R',N),('L',N),('R',N),('L',N),('R',N),('L',N),('L',N)]},

    {'name': 'SINGLE PARADIDDLE-DIDDLE', 'short': 'PARA-DIDL',
     'cat': 1, 'pas': 19, 'div': 4,
     'notes': [('R',A),('L',N),('R',N),('R',N),('L',N),('L',N)]},

    # ── FLAMS (cat 2) ────────────────────────────────────
    {'name': 'FLAM', 'short': 'FLAM',
     'cat': 2, 'pas': 20, 'div': 4,
     'notes': [('R',FA),('L',FA)]},

    {'name': 'FLAM ACCENT', 'short': 'FLM ACCENT',
     'cat': 2, 'pas': 21, 'div': 3,
     'notes': [('R',FA),('L',N),('R',N),('L',FA),('R',N),('L',N)]},

    {'name': 'FLAM TAP', 'short': 'FLM TAP',
     'cat': 2, 'pas': 22, 'div': 4,
     'notes': [('R',FA),('R',N),('L',FA),('L',N)]},

    {'name': 'FLAMACUE', 'short': 'FLAMACUE',
     'cat': 2, 'pas': 23, 'div': 4,
     'notes': [('R',FA),('L',A),('R',N),('L',N),('R',FA)]},

    {'name': 'FLAM PARADIDDLE', 'short': 'FLM PARA',
     'cat': 2, 'pas': 24, 'div': 4,
     'notes': [('R',FA),('L',N),('R',N),('R',N),('L',FA),('R',N),('L',N),('L',N)]},

    {'name': 'SINGLE FLAMMED MILL', 'short': 'FLM MILL',
     'cat': 2, 'pas': 25, 'div': 4,
     'notes': [('R',FA),('L',N),('R',N),('R',N),('L',FA),('R',N),('L',N),('L',N)]},

    {'name': 'FLAM PARADIDDLE-DIDDLE', 'short': 'FLM PDD',
     'cat': 2, 'pas': 26, 'div': 4,
     'notes': [('R',FA),('L',N),('R',N),('R',N),('L',N),('L',N),
               ('R',FA),('L',N),('R',N),('R',N),('L',N),('L',N)]},

    {'name': 'PATAFLAFLA', 'short': 'PATAFLA',
     'cat': 2, 'pas': 27, 'div': 4,
     'notes': [('R',FA),('L',N),('R',N),('L',FA),('R',N),('L',FA),('R',N),('L',FA)]},

    {'name': 'SWISS ARMY TRIPLET', 'short': 'SWISS TRP',
     'cat': 2, 'pas': 28, 'div': 3,
     'notes': [('R',FA),('R',N),('L',N),('L',FA),('L',N),('R',N)]},

    {'name': 'INVERTED FLAM TAP', 'short': 'INV FLM',
     'cat': 2, 'pas': 29, 'div': 4,
     'notes': [('R',FN),('L',A),('L',FN),('R',A)]},

    {'name': 'FLAM DRAG', 'short': 'FLM DRAG',
     'cat': 2, 'pas': 30, 'div': 4,
     'notes': [('R',FA),('L',N),('R',N),('L',FA)]},

    # ── DRAGS (cat 3) ────────────────────────────────────
    {'name': 'DRAG', 'short': 'DRAG',
     'cat': 3, 'pas': 31, 'div': 4,
     'notes': [('R',DN),('L',DN)]},

    {'name': 'SINGLE DRAG TAP', 'short': 'SGL DRG T',
     'cat': 3, 'pas': 32, 'div': 4,
     'notes': [('R',DN),('L',N),('R',DN),('L',N)]},

    {'name': 'DOUBLE DRAG TAP', 'short': 'DBL DRG T',
     'cat': 3, 'pas': 33, 'div': 4,
     'notes': [('R',DN),('R',DN),('L',N),('L',DN),('L',DN),('R',N)]},

    {'name': 'LESSON 25', 'short': 'LESSON 25',
     'cat': 3, 'pas': 34, 'div': 4,
     'notes': [('R',DN),('L',DN),('R',A),('L',DN),('R',DN),('L',A)]},

    {'name': 'SINGLE DRAGADIDDLE', 'short': 'DRAGADIDL',
     'cat': 3, 'pas': 35, 'div': 4,
     'notes': [('R',DN),('R',N),('R',N),('L',DN),('L',N),('L',N)]},

    {'name': 'DRAG PARADIDDLE 1', 'short': 'DRG PD 1',
     'cat': 3, 'pas': 36, 'div': 4,
     'notes': [('R',A),('R',DN),('L',N),('R',N),('R',N),('L',A),('L',DN),('R',N),('L',N),('L',N)]},

    {'name': 'DRAG PARADIDDLE 2', 'short': 'DRG PD 2',
     'cat': 3, 'pas': 37, 'div': 4,
     'notes': [('R',A),('R',DN),('L',N),('R',N),('L',N),('R',N),('R',N)]},

    {'name': 'SINGLE RATAMACUE', 'short': 'SGL RATA',
     'cat': 3, 'pas': 38, 'div': 4,
     'notes': [('R',DN),('L',N),('R',N),('L',A)]},

    {'name': 'DOUBLE RATAMACUE', 'short': 'DBL RATA',
     'cat': 3, 'pas': 39, 'div': 4,
     'notes': [('R',DN),('L',N),('R',N),('R',DN),('L',N),('R',N),('L',A)]},

    {'name': 'TRIPLE RATAMACUE', 'short': 'TRP RATA',
     'cat': 3, 'pas': 40, 'div': 4,
     'notes': [('R',DN),('L',N),('R',N),('R',DN),('L',N),('R',N),('R',DN),('L',N),('R',N),('L',A)]},
]

# Build per-category index
_CAT_RUDIMENTS = [[] for _ in range(4)]
for _i, _r in enumerate(RUDIMENTS):
    _CAT_RUDIMENTS[_r['cat']].append(_i)


class DrumRudiments(Visual):
    name = "RUDIMENTS"
    description = "PAS 40 drum rudiments"
    category = "music"

    # Auto-scroll: initial delay before repeat, then repeat interval
    SCROLL_DELAY = 0.4   # seconds before auto-scroll kicks in
    SCROLL_RATE = 0.12   # seconds between repeats during auto-scroll
    BPM_MIN = 40
    BPM_MAX = 200
    BPM_STEP = 5

    def reset(self):
        self.time = 0.0
        self.rud_idx = 0        # index into flat RUDIMENTS list (0..39)
        self.playing = True     # animation running
        self.playhead = 0.0     # 0..1 progress through pattern
        self.tempo = 80.0       # BPM
        self._scroll_x = 0.0   # for scrolling long names
        self._flash = [0.0] * 20  # per-note flash timers
        # Auto-scroll state for up/down held
        self._scroll_dir = 0    # -1, 0, +1
        self._scroll_hold = 0.0 # how long held so far
        self._scroll_accum = 0.0 # accumulator for repeat ticks

    def _current_rudiment(self):
        return RUDIMENTS[self.rud_idx % len(RUDIMENTS)]

    def _step_rudiment(self, direction):
        """Move to next/prev rudiment, reset playhead and scroll."""
        self.rud_idx = (self.rud_idx + direction) % len(RUDIMENTS)
        self.playhead = 0.0
        self._scroll_x = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down: cycle rudiments with auto-scroll on hold
        if input_state.up_pressed:
            self._step_rudiment(-1)
            self._scroll_dir = -1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True
        elif input_state.down_pressed:
            self._step_rudiment(1)
            self._scroll_dir = 1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True

        # If direction released, stop auto-scroll
        if not input_state.up and not input_state.down:
            self._scroll_dir = 0

        # Left/Right: adjust BPM
        if input_state.left_pressed:
            self.tempo = max(self.BPM_MIN, self.tempo - self.BPM_STEP)
            consumed = True
        elif input_state.right_pressed:
            self.tempo = min(self.BPM_MAX, self.tempo + self.BPM_STEP)
            consumed = True

        # Either action button: toggle play/pause
        if input_state.action_l or input_state.action_r:
            self.playing = not self.playing
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Auto-scroll when up/down held past debounce
        if self._scroll_dir != 0:
            self._scroll_hold += dt
            if self._scroll_hold >= self.SCROLL_DELAY:
                self._scroll_accum += dt
                while self._scroll_accum >= self.SCROLL_RATE:
                    self._scroll_accum -= self.SCROLL_RATE
                    self._step_rudiment(self._scroll_dir)

        rud = self._current_rudiment()
        notes = rud['notes']
        n = len(notes)

        # Advance playhead
        if self.playing and n > 0:
            cycle_time = self._cycle_time(rud)
            self.playhead += dt / cycle_time
            if self.playhead >= 1.0:
                self.playhead -= 1.0

        # Update flash timers
        for i in range(len(self._flash)):
            if self._flash[i] > 0:
                self._flash[i] = max(0.0, self._flash[i] - dt)

        # Trigger flash for current note
        if n > 0:
            current_note = int(self.playhead * n) % n
            if len(self._flash) < n:
                self._flash = [0.0] * n
            prev_note = int((self.playhead - dt / max(0.01, self._cycle_time(rud))) * n) % n
            if current_note != prev_note or (self.playhead < dt / max(0.01, self._cycle_time(rud))):
                self._flash[current_note] = 0.15

        # Scroll long names
        name = rud['name']
        name_px = len(name) * 4
        avail = 48  # pixels available for name in header
        if name_px > avail:
            self._scroll_x += dt * 18
            total = name_px + 16  # gap before wrap
            if self._scroll_x >= total:
                self._scroll_x -= total

    def _cycle_time(self, rud):
        notes = rud['notes']
        n = len(notes)
        if n == 0:
            return 1.0
        div = rud.get('div', 4)
        beats = n * (4.0 / div)
        return beats * 60.0 / self.tempo

    def draw(self):
        d = self.display
        d.clear()

        rud = self._current_rudiment()
        notes = rud['notes']

        self._draw_header(d, rud)
        self._draw_separator(d, 7)
        self._draw_sticking(d, rud)
        self._draw_lanes(d, rud)
        self._draw_divider(d)
        self._draw_footer(d, rud)

    def _draw_header(self, d, rud):
        # Background
        d.draw_rect(0, 0, 64, 7, HEADER_BG)

        cat_color = CAT_COLORS[rud['cat']]

        # PAS number left
        pas_str = str(rud['pas'])
        d.draw_text_small(1, 1, pas_str, cat_color)

        # Name, scrolls if long
        name = rud['name']
        name_px = len(name) * 4
        name_start_x = len(pas_str) * 4 + 2
        avail = 63 - name_start_x

        if name_px <= avail:
            # Fits — draw centered in available space
            offset = name_start_x + (avail - name_px) // 2
            d.draw_text_small(offset, 1, name, (255, 220, 100))
        else:
            # Scroll
            total = name_px + 16
            sx = int(self._scroll_x) % total
            for cx in range(name_start_x, 63):
                px = sx + (cx - name_start_x)
                char_idx = px // 4
                col = px % 4
                if col < 3 and 0 <= char_idx < len(name):
                    ch = name[char_idx]
                    self._draw_char_col(d, cx, 1, ch, col, (255, 220, 100))

    def _draw_char_col(self, d, x, y, ch, col, color):
        """Draw a single column of a 3x5 character."""
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
            ' ': ['000', '000', '000', '000', '000'],
            '-': ['000', '000', '111', '000', '000'],
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
        }
        ch_upper = ch.upper()
        glyph = FONT.get(ch_upper)
        if glyph is None or col >= 3:
            return
        for row_idx, row in enumerate(glyph):
            if row[col] == '1':
                d.set_pixel(x, y + row_idx, color)

    def _draw_separator(self, d, y):
        for x in range(64):
            d.set_pixel(x, y, (60, 60, 80))

    def _draw_sticking(self, d, rud):
        """Draw sticking text R/L in rows y=8..12."""
        notes = rud['notes']
        n = len(notes)
        if n == 0:
            return

        # Compute x positions for each note
        xs = self._note_xs(n)

        for i, (hand, ntype) in enumerate(notes):
            x = xs[i]
            is_r = hand == 'R'
            # Color based on accent
            if ntype in (A, FA, DA):
                color = R_ACC if is_r else L_ACC
            else:
                color = R_NORM if is_r else L_NORM

            # Flash
            if i < len(self._flash) and self._flash[i] > 0:
                f = min(1.0, self._flash[i] / 0.1)
                color = _blend(color, FLASH_COLOR, f)

            d.draw_text_small(x - 1, 8, hand, color)

    def _draw_lanes(self, d, rud):
        """Draw the note dots in R and L lanes."""
        notes = rud['notes']
        n = len(notes)
        if n == 0:
            return

        xs = self._note_xs(n)

        # Playhead position
        ph_x = NOTE_X_MIN + self.playhead * (NOTE_X_MAX - NOTE_X_MIN)

        for i, (hand, ntype) in enumerate(notes):
            x = xs[i]
            is_r = hand == 'R'
            lane_y = R_LANE_Y if is_r else L_LANE_Y

            is_accent = ntype in (A, FA, DA)
            is_flam = ntype in (FN, FA)
            is_drag = ntype in (DN, DA)

            # Base color
            if is_accent:
                base_color = R_ACC if is_r else L_ACC
            else:
                base_color = R_NORM if is_r else L_NORM

            grace_color = R_GRACE if is_r else L_GRACE

            # Flash
            flash_f = 0.0
            if i < len(self._flash) and self._flash[i] > 0:
                flash_f = min(1.0, self._flash[i] / 0.1)

            color = _blend(base_color, FLASH_COLOR, flash_f)

            # Draw grace notes first (behind main note)
            if is_flam:
                # Single grace note: small dot offset to the left
                gx = max(1, x - 4)
                gy = lane_y - 3
                d.set_pixel(gx, gy, _blend(grace_color, FLASH_COLOR, flash_f * 0.5))
                # Connecting line
                d.draw_line(gx + 1, gy + 1, x - 1, lane_y - 1,
                           _blend(grace_color, FLASH_COLOR, flash_f * 0.3))

            if is_drag:
                # Two stacked grace dots offset to the left
                gx = max(1, x - 4)
                gc = _blend(grace_color, FLASH_COLOR, flash_f * 0.5)
                d.set_pixel(gx, lane_y - 2, gc)
                d.set_pixel(gx, lane_y + 2, gc)
                # Connecting lines
                lc = _blend(grace_color, FLASH_COLOR, flash_f * 0.3)
                d.draw_line(gx + 1, lane_y - 1, x - 1, lane_y, lc)
                d.draw_line(gx + 1, lane_y + 1, x - 1, lane_y, lc)

            # Main note
            if is_accent:
                d.draw_circle(x, lane_y, 2, color, filled=True)
            else:
                # Small dot
                d.set_pixel(x, lane_y, color)
                d.set_pixel(x - 1, lane_y, color)
                d.set_pixel(x + 1, lane_y, color)
                d.set_pixel(x, lane_y - 1, color)
                d.set_pixel(x, lane_y + 1, color)

        # Draw playhead line
        px = int(ph_x)
        if 0 <= px < 64:
            for y in range(14, 57):
                if y == 35:
                    continue  # skip divider
                alpha = 0.3
                existing = d.get_pixel(px, y)
                blended = _blend(existing, (255, 255, 255), alpha)
                d.set_pixel(px, y, blended)

    def _draw_divider(self, d):
        """Dotted center divider between R and L lanes."""
        for x in range(0, 64, 2):
            d.set_pixel(x, 35, DIVIDER_COLOR)

    def _draw_footer(self, d, rud):
        """Draw position indicator, BPM, and category."""
        d.draw_rect(0, 58, 64, 6, HEADER_BG)
        self._draw_separator(d, 58)

        # Position "1/40" left
        pos_str = f'{self.rud_idx + 1}/{len(RUDIMENTS)}'
        d.draw_text_small(1, 59, pos_str, TEXT_DIM)

        # Pause indicator or BPM center-right
        if not self.playing:
            d.draw_text_small(25, 59, 'II', (200, 200, 200))

        # BPM right-aligned
        bpm_str = f'{int(self.tempo)}'
        bpm_px = len(bpm_str) * 4
        d.draw_text_small(63 - bpm_px, 59, bpm_str, CAT_COLORS[rud['cat']])

    def _note_xs(self, n):
        """Compute evenly-spaced x positions for n notes."""
        if n <= 1:
            return [32]
        xs = []
        for i in range(n):
            x = NOTE_X_MIN + int(i * (NOTE_X_MAX - NOTE_X_MIN) / (n - 1))
            xs.append(x)
        return xs


def _blend(c1, c2, t):
    """Blend two RGB colors. t=0 -> c1, t=1 -> c2."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )

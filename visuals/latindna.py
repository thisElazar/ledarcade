"""Latin DNA - Foundational Latin rhythm patterns on 64x64 LED matrix.

Controls:
  Up/Down    - Cycle patterns (hold to auto-scroll)
  Left/Right - Adjust BPM
  Action     - Play/Pause
"""

from . import Visual

# ── Categories ──────────────────────────────────────────────────────
CATEGORIES = ["FOUNDATIONS", "CLAVES", "BELLS", "DRUMS"]
CAT_COLORS = [
    (220, 180, 50),    # Foundations = warm gold
    (255, 255, 255),   # Claves = white
    (40, 220, 255),    # Bells = cyan
    (255, 160, 40),    # Drums = orange
]

# ── Layout constants ────────────────────────────────────────────────
HEADER_BG = (20, 20, 30)
TEXT_DIM = (120, 120, 140)
BEAT_BRIGHT = (160, 160, 180)
BEAT_DIM = (70, 70, 90)
REST_COLOR = (35, 35, 45)
FLASH_COLOR = (255, 255, 255)
BAR_DIV_COLOR = (100, 70, 140)

LABEL_Y = 10       # beat label text y
CELL_Y_TOP = 17    # top of grid cells
CELL_H = 13        # height of grid cells
DESC_Y = 37        # description text y

# ── All patterns ────────────────────────────────────────────────────
# Grid positions are 8th notes: 2 per beat.
# 8-step  = 1 bar of 4/4   (beats 1+2+3+4+)
# 16-step = 2 bars of 4/4  (beats 1+2+3+4+ | 1+2+3+4+)
# 12-step = 1 bar of 12/8  (4 dotted-quarter pulses, 3 subdivisions each)
#
# Verified against Wikipedia (Clave rhythm), Berklee PULSE, Ethan Hein,
# and standard percussion pedagogy sources.

PATTERNS = [
    # ── FOUNDATIONS (cat 0) ─────────────────────────────────
    {'name': 'TRESILLO', 'cat': 0, 'num': 1,
     'steps': 8, 'beats': 4,
     'grid': [1,0,0,1,0,0,1,0],
     'desc': '3+3+2  THE FOUNDATION  AFRICAN ORIGIN'},

    {'name': 'HABANERA', 'cat': 0, 'num': 2,
     'steps': 8, 'beats': 4,
     'grid': [1,0,0,1,0,1,1,0],
     'desc': 'TRESILLO + BEAT 3  TANGO  HAVANA TO BUENOS AIRES'},

    # ── CLAVES (cat 1) ─────────────────────────────────────
    # Son Clave 3-2: bar 1 (3-side) = 1, &2, 4 / bar 2 (2-side) = 2, 3
    {'name': 'SON CLAVE 3-2', 'cat': 1, 'num': 3,
     'steps': 16, 'beats': 8,
     'grid': [1,0,0,1,0,0,1,0, 0,0,1,0,1,0,0,0],
     'desc': 'CUBAN SON  SALSA  MAMBO  LATIN JAZZ'},

    # Son Clave 2-3: bars swapped (2-side first, then 3-side)
    {'name': 'SON CLAVE 2-3', 'cat': 1, 'num': 4,
     'steps': 16, 'beats': 8,
     'grid': [0,0,1,0,1,0,0,0, 1,0,0,1,0,0,1,0],
     'desc': 'REVERSED SON  LAID-BACK VERSE FEEL'},

    # Rumba Clave 3-2: third stroke of 3-side shifted to &4 (position 7)
    # 2-side same as Son Clave
    {'name': 'RUMBA CLAVE 3-2', 'cat': 1, 'num': 5,
     'steps': 16, 'beats': 8,
     'grid': [1,0,0,1,0,0,0,1, 0,0,1,0,1,0,0,0],
     'desc': 'RUMBA  GUAGUANCO  SONGO  TIMBA'},

    {'name': 'RUMBA CLAVE 2-3', 'cat': 1, 'num': 6,
     'steps': 16, 'beats': 8,
     'grid': [0,0,1,0,1,0,0,0, 1,0,0,1,0,0,0,1],
     'desc': 'REVERSED RUMBA  FOLKLORIC'},

    # Bossa Nova Clave: 3-side same as Son / 2-side = &1, 3
    {'name': 'BOSSA NOVA CLAVE', 'cat': 1, 'num': 7,
     'steps': 16, 'beats': 8,
     'grid': [1,0,0,1,0,0,1,0, 0,1,0,0,1,0,0,0],
     'desc': 'BOSSA NOVA  FLOWING  EVEN'},

    # ── BELLS (cat 2) ──────────────────────────────────────
    # Standard 7-stroke bell pattern in 12/8
    # Spacing: 2-2-1-2-2-2-1
    {'name': 'BEMBE BELL', 'cat': 2, 'num': 8,
     'steps': 12, 'beats': 4,
     'grid': [1,0,1,0,1,1,0,1,0,1,1,0],
     'desc': '7-STROKE BELL  6/8 FEEL  SUB-SAHARAN AFRICA'},

    {'name': 'CASCARA', 'cat': 2, 'num': 9,
     'steps': 16, 'beats': 8,
     'grid': [1,0,1,1,0,1,1,0, 1,1,0,1,1,0,1,0],
     'desc': 'TIMBALE SHELL  SALSA TIMEKEEPER'},

    # ── DRUMS (cat 3) ──────────────────────────────────────
    {'name': 'CONGA TUMBAO', 'cat': 3, 'num': 10,
     'steps': 8, 'beats': 4,
     'grid': [1,0,1,0,1,0,1,1],
     'desc': 'OPEN TONES + SLAPS  SALSA CONGAS'},
]

# Build per-category index
_CAT_PATTERNS = [[] for _ in range(len(CATEGORIES))]
for _i, _p in enumerate(PATTERNS):
    _CAT_PATTERNS[_p['cat']].append(_i)


class LatinDNA(Visual):
    name = "LATIN DNA"
    description = "Latin rhythm patterns"
    category = "music"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    BPM_MIN = 40
    BPM_MAX = 200
    BPM_STEP = 5

    def reset(self):
        self.time = 0.0
        self.pat_idx = 0
        self.playing = True
        self.playhead = 0.0
        self.tempo = 100.0
        self._name_scroll_x = 0.0
        self._desc_scroll_x = 0.0
        self._flash = [0.0] * 20
        self._bg_flash = 0.0     # whole-background pulse on hits
        self._scroll_dir = 0
        self._scroll_hold = 0.0
        self._scroll_accum = 0.0

    def _current(self):
        return PATTERNS[self.pat_idx % len(PATTERNS)]

    def _step_pattern(self, direction):
        self.pat_idx = (self.pat_idx + direction) % len(PATTERNS)
        self.playhead = 0.0
        self._name_scroll_x = 0.0
        self._desc_scroll_x = 0.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self._step_pattern(-1)
            self._scroll_dir = -1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True
        elif input_state.down_pressed:
            self._step_pattern(1)
            self._scroll_dir = 1
            self._scroll_hold = 0.0
            self._scroll_accum = 0.0
            consumed = True

        if not input_state.up and not input_state.down:
            self._scroll_dir = 0

        if input_state.left_pressed:
            self.tempo = max(self.BPM_MIN, self.tempo - self.BPM_STEP)
            consumed = True
        elif input_state.right_pressed:
            self.tempo = min(self.BPM_MAX, self.tempo + self.BPM_STEP)
            consumed = True

        if input_state.action_l or input_state.action_r:
            self.playing = not self.playing
            consumed = True

        return consumed

    def _cycle_time(self, pat):
        beats = pat.get('beats', pat['steps'] / 2)
        return beats * 60.0 / self.tempo

    def update(self, dt: float):
        self.time += dt

        # Auto-scroll when up/down held
        if self._scroll_dir != 0:
            self._scroll_hold += dt
            if self._scroll_hold >= self.SCROLL_DELAY:
                self._scroll_accum += dt
                while self._scroll_accum >= self.SCROLL_RATE:
                    self._scroll_accum -= self.SCROLL_RATE
                    self._step_pattern(self._scroll_dir)

        pat = self._current()
        n = pat['steps']
        cycle = self._cycle_time(pat)

        # Advance playhead
        if self.playing and n > 0:
            self.playhead += dt / cycle
            if self.playhead >= 1.0:
                self.playhead -= 1.0

        # Update flash timers
        for i in range(len(self._flash)):
            if self._flash[i] > 0:
                self._flash[i] = max(0.0, self._flash[i] - dt)

        # Trigger flash for current step on hit
        if n > 0:
            current_step = int(self.playhead * n) % n
            if len(self._flash) < n:
                self._flash = [0.0] * n
            prev_step = int((self.playhead - dt / max(0.01, cycle)) * n) % n
            if current_step != prev_step or (self.playhead < dt / max(0.01, cycle)):
                if pat['grid'][current_step]:
                    self._flash[current_step] = 0.15
                    self._bg_flash = 0.12

        # Decay background flash
        if self._bg_flash > 0:
            self._bg_flash = max(0.0, self._bg_flash - dt)

        # Scroll long name
        name = pat['name']
        name_px = len(name) * 4
        num_str = str(pat['num'])
        name_start_x = len(num_str) * 4 + 2
        avail = 63 - name_start_x
        if name_px > avail:
            self._name_scroll_x += dt * 18
            total = name_px + 16
            if self._name_scroll_x >= total:
                self._name_scroll_x -= total

        # Scroll description
        desc = pat['desc']
        desc_px = len(desc) * 4
        if desc_px > 60:
            self._desc_scroll_x += dt * 16
            total = desc_px + 20
            if self._desc_scroll_x >= total:
                self._desc_scroll_x -= total

    # ── Drawing ─────────────────────────────────────────────────────

    def draw(self):
        d = self.display

        # Background flash: black -> subtle gray on hits
        if self._bg_flash > 0:
            g = int(25 * min(1.0, self._bg_flash / 0.08))
            d.clear((g, g, g))
        else:
            d.clear()

        pat = self._current()
        cat_color = CAT_COLORS[pat['cat']]

        self._draw_header(d, pat, cat_color)
        self._draw_separator(d, 7)
        self._draw_beats_and_grid(d, pat, cat_color)
        self._draw_desc(d, pat)
        self._draw_separator(d, 57)
        self._draw_footer(d, pat, cat_color)

    def _draw_header(self, d, pat, cat_color):
        d.draw_rect(0, 0, 64, 7, HEADER_BG)

        num_str = str(pat['num'])
        d.draw_text_small(1, 1, num_str, cat_color)

        name = pat['name']
        name_px = len(name) * 4
        name_start_x = len(num_str) * 4 + 2
        avail = 63 - name_start_x

        if name_px <= avail:
            offset = name_start_x + (avail - name_px) // 2
            d.draw_text_small(offset, 1, name, (255, 220, 100))
        else:
            total = name_px + 16
            sx = int(self._name_scroll_x) % total
            for cx in range(name_start_x, 63):
                px = sx + (cx - name_start_x)
                char_idx = px // 4
                col = px % 4
                if col < 3 and 0 <= char_idx < len(name):
                    self._draw_char_col(d, cx, 1, name[char_idx], col,
                                        (255, 220, 100))

    def _draw_beats_and_grid(self, d, pat, cat_color):
        """Draw beat labels, grid cells, bar divider, and playhead."""
        n = pat['steps']
        grid = pat['grid']
        xs, cell_w, div_x = self._layout(n)
        labels = self._beat_labels(n)

        # ── Beat labels above cells ──
        for i, label in enumerate(labels):
            if not label:
                continue
            is_beat = label in '1234'
            color = BEAT_BRIGHT if is_beat else BEAT_DIM
            # Center label (3px font) in cell
            lx = xs[i] + max(0, (cell_w - 3) // 2)
            d.draw_text_small(lx, LABEL_Y, label, color)

        # ── Bar divider (for 16-step two-bar patterns) ──
        if div_x is not None:
            for y in range(LABEL_Y, CELL_Y_TOP + CELL_H):
                d.set_pixel(div_x, y, BAR_DIV_COLOR)

        # ── Grid cells ──
        for i in range(n):
            x = xs[i]
            hit = grid[i]
            color = cat_color if hit else REST_COLOR

            # Flash
            if i < len(self._flash) and self._flash[i] > 0:
                f = min(1.0, self._flash[i] / 0.1)
                color = _blend(color, FLASH_COLOR, f)

            for py in range(CELL_H):
                for px_off in range(cell_w):
                    sx = x + px_off
                    sy = CELL_Y_TOP + py
                    if 0 <= sx < 64 and 0 <= sy < 64:
                        d.set_pixel(sx, sy, color)

        # ── Playhead ──
        self._draw_playhead(d, n, xs, cell_w)

    def _draw_playhead(self, d, n, xs, cell_w):
        """Sweep playhead across each bar; jumps across bar gap for 16-step."""
        if n == 16:
            # Two bars — sweep within each bar independently
            if self.playhead < 0.5:
                t = self.playhead * 2
                x_start = xs[0]
                x_end = xs[7] + cell_w
            else:
                t = (self.playhead - 0.5) * 2
                x_start = xs[8]
                x_end = xs[15] + cell_w
            ph_x = int(x_start + t * (x_end - x_start))
        else:
            ph_x = int(xs[0] + self.playhead * (xs[-1] + cell_w - xs[0]))

        if 0 <= ph_x < 64:
            for y in range(CELL_Y_TOP - 1, CELL_Y_TOP + CELL_H + 1):
                if 0 <= y < 64:
                    existing = d.get_pixel(ph_x, y)
                    blended = _blend(existing, (255, 255, 255), 0.5)
                    d.set_pixel(ph_x, y, blended)

    def _draw_desc(self, d, pat):
        """Draw scrolling description text."""
        desc = pat['desc']
        desc_px = len(desc) * 4

        if desc_px <= 60:
            x = (64 - desc_px) // 2
            d.draw_text_small(x, DESC_Y, desc, TEXT_DIM)
        else:
            total = desc_px + 20
            sx = int(self._desc_scroll_x) % total
            for cx in range(1, 63):
                px = sx + (cx - 1)
                char_idx = px // 4
                col = px % 4
                if col < 3 and 0 <= char_idx < len(desc):
                    self._draw_char_col(d, cx, DESC_Y, desc[char_idx], col,
                                        TEXT_DIM)

    def _draw_footer(self, d, pat, cat_color):
        d.draw_rect(0, 58, 64, 6, HEADER_BG)

        # Position counter
        pos_str = f'{self.pat_idx + 1}/{len(PATTERNS)}'
        d.draw_text_small(1, 59, pos_str, TEXT_DIM)

        # Pause indicator
        if not self.playing:
            d.draw_text_small(25, 59, 'II', (200, 200, 200))

        # BPM right-aligned
        bpm_str = f'{int(self.tempo)}'
        bpm_px = len(bpm_str) * 4
        d.draw_text_small(63 - bpm_px, 59, bpm_str, cat_color)

    def _draw_separator(self, d, y):
        for x in range(64):
            d.set_pixel(x, y, (60, 60, 80))

    # ── Layout helpers ──────────────────────────────────────────────

    def _layout(self, n):
        """Returns (xs, cell_w, divider_x_or_None) for n steps."""
        if n == 16:
            # Two bars of 8 with bar divider gap
            # Bar 1: 8 cells × 3px + 7 gaps × 1px = 31px (x 0-30)
            # Divider: x = 31
            # Bar 2: 8 cells × 3px + 7 gaps × 1px = 31px (x 33-63)
            cw, gap = 3, 1
            xs = [i * (cw + gap) for i in range(8)]
            xs += [33 + i * (cw + gap) for i in range(8)]
            return xs, cw, 31
        elif n == 8:
            # Single bar, wider cells for clarity
            cw, gap = 5, 2
            tw = n * cw + (n - 1) * gap
            sx = (64 - tw) // 2
            return [sx + i * (cw + gap) for i in range(n)], cw, None
        elif n == 12:
            # Compound time (12/8), 12 cells evenly spaced
            cw, gap = 3, 1
            tw = n * cw + (n - 1) * gap
            sx = (64 - tw) // 2
            return [sx + i * (cw + gap) for i in range(n)], cw, None
        else:
            cw, gap = 3, 1
            tw = n * cw + (n - 1) * gap
            sx = max(0, (64 - tw) // 2)
            return [sx + i * (cw + gap) for i in range(n)], cw, None

    def _beat_labels(self, n):
        """Return label string for each step position."""
        if n == 8:
            # 1 bar of 4/4, 8th notes: 1 + 2 + 3 + 4 +
            return ['1', '+', '2', '+', '3', '+', '4', '+']
        elif n == 16:
            # 2 bars of 4/4, 8th notes: each bar gets 1 + 2 + 3 + 4 +
            bar = ['1', '+', '2', '+', '3', '+', '4', '+']
            return bar + bar
        elif n == 12:
            # 12/8: 4 dotted-quarter pulses, mark only the main beats
            return ['1', '', '', '2', '', '', '3', '', '', '4', '', '']
        else:
            return ['' for _ in range(n)]

    def _draw_char_col(self, d, x, y, ch, col, color):
        """Draw a single column of a 3x5 character."""
        glyph = _FONT.get(ch.upper())
        if glyph is None or col >= 3:
            return
        for row_idx, row in enumerate(glyph):
            if row[col] == '1':
                d.set_pixel(x, y + row_idx, color)


# ── Shared font for scrolling text ─────────────────────────────────
_FONT = {
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
    '+': ['000', '010', '111', '010', '000'],
    '/': ['001', '001', '010', '100', '100'],
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


def _blend(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )

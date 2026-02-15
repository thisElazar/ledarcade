"""Circle of Fifths — interactive music theory visualization on 64x64 LED matrix.

Controls:
  Left/Right - Rotate selection around the circle (by fifths)
  Up/Down    - Cycle view: key names / key signatures / chord progressions
  Action     - Toggle major/minor emphasis
"""

import math
from . import Visual

# ── Circle of Fifths data ──────────────────────────────────────────
KEYS = [
    {'major': 'C',  'minor': 'Am',  'sharps': 0, 'flats': 0},
    {'major': 'G',  'minor': 'Em',  'sharps': 1, 'flats': 0},
    {'major': 'D',  'minor': 'Bm',  'sharps': 2, 'flats': 0},
    {'major': 'A',  'minor': 'F#m', 'sharps': 3, 'flats': 0},
    {'major': 'E',  'minor': 'C#m', 'sharps': 4, 'flats': 0},
    {'major': 'B',  'minor': 'G#m', 'sharps': 5, 'flats': 0},
    {'major': 'Gb', 'minor': 'Ebm', 'sharps': 0, 'flats': 6},
    {'major': 'Db', 'minor': 'Bbm', 'sharps': 0, 'flats': 5},
    {'major': 'Ab', 'minor': 'Fm',  'sharps': 0, 'flats': 4},
    {'major': 'Eb', 'minor': 'Cm',  'sharps': 0, 'flats': 3},
    {'major': 'Bb', 'minor': 'Gm',  'sharps': 0, 'flats': 2},
    {'major': 'F',  'minor': 'Dm',  'sharps': 0, 'flats': 1},
]

# Common chords in each major key (scale-degree Roman numerals)
# I  ii  iii  IV  V  vi  vii*
CHORD_NAMES = ['I', 'ii', 'iii', 'IV', 'V', 'vi', 'vii']
CHORD_QUALITY = ['', 'm', 'm', '', '', 'm', 'dim']

# Build chord names for each key from scale degrees
SCALE_NOTES = ['C', 'Db', 'D', 'Eb', 'E', 'F', 'Gb', 'G', 'Ab', 'A', 'Bb', 'B']
MAJOR_STEPS = [0, 2, 4, 5, 7, 9, 11]  # W W H W W W H

# Map major key names to chromatic index
_KEY_TO_CHROM = {
    'C': 0, 'Db': 1, 'D': 2, 'Eb': 3, 'E': 4, 'F': 5,
    'Gb': 6, 'G': 7, 'Ab': 8, 'A': 9, 'Bb': 10, 'B': 11,
}

VIEW_NAMES = ['KEYS', 'SIGNATURES']
NUM_VIEWS = 2

# Circle geometry
CX, CY = 32, 30
OUTER_R = 24

# ── Helpers ────────────────────────────────────────────────────────

def _key_angle(i):
    """Angle for key index i (0=top, clockwise)."""
    return -math.pi / 2 + i * (2 * math.pi / 12)


def _pos(cx, cy, radius, i):
    """(x, y) integer position for key index i on circle."""
    a = _key_angle(i)
    return cx + int(radius * math.cos(a)), cy + int(radius * math.sin(a))


def _hsv_to_rgb(h, s, v):
    """Convert HSV (h in 0-360, s/v in 0-1) to RGB tuple."""
    h = h % 360
    c = v * s
    x = c * (1 - abs((h / 60) % 2 - 1))
    m = v - c
    if h < 60:
        r, g, b = c, x, 0
    elif h < 120:
        r, g, b = x, c, 0
    elif h < 180:
        r, g, b = 0, c, x
    elif h < 240:
        r, g, b = 0, x, c
    elif h < 300:
        r, g, b = x, 0, c
    else:
        r, g, b = c, 0, x
    return (int((r + m) * 255), int((g + m) * 255), int((b + m) * 255))


def _dim(color, factor):
    """Dim an RGB tuple by a factor (0-1)."""
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def _key_hue(i):
    """HSV hue for key position i (0-11), mapped around the color wheel."""
    return i * 30  # 360/12 = 30 degrees per step


def _chords_for_key(key_name):
    """Return string of common chords for a major key, e.g. 'C Dm Em F G Am Bdim'."""
    root = _KEY_TO_CHROM.get(key_name, 0)
    parts = []
    for deg, qual in zip(MAJOR_STEPS, CHORD_QUALITY):
        note_idx = (root + deg) % 12
        note = SCALE_NOTES[note_idx]
        parts.append(note + qual)
    return '  '.join(parts)


def _sig_label(key_data):
    """Return key signature label like '2#' or '3b' or '0'."""
    if key_data['sharps'] > 0:
        return '%d#' % key_data['sharps']
    elif key_data['flats'] > 0:
        return '%db' % key_data['flats']
    return '0'


# ── Visual class ───────────────────────────────────────────────────

class CircleOfFifths(Visual):
    name = "CIRCLE OF 5THS"
    description = "Interactive circle of fifths"
    category = "music"

    def reset(self):
        self.time = 0.0
        self.selected = 0        # index into KEYS (0=C)
        self.view = 0            # 0=key names, 1=signatures, 2=chords
        self.minor_mode = False  # False=major emphasis, True=minor emphasis
        self._pulse = 0.0       # subtle pulse animation on selected key

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: rotate selection
        if input_state.right_pressed:
            self.selected = (self.selected + 1) % 12
            consumed = True
        if input_state.left_pressed:
            self.selected = (self.selected - 1) % 12
            consumed = True

        # Up/Down: cycle view
        if input_state.up_pressed:
            self.view = (self.view - 1) % NUM_VIEWS
            consumed = True
        if input_state.down_pressed:
            self.view = (self.view + 1) % NUM_VIEWS
            consumed = True

        # Action: toggle major/minor emphasis
        if input_state.action_l or input_state.action_r:
            self.minor_mode = not self.minor_mode
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self._pulse += dt

    def draw(self):
        d = self.display
        d.clear()

        key_data = KEYS[self.selected]
        pulse = 0.15 * math.sin(self._pulse * 3.0)  # gentle brightness pulse

        # ── Draw connecting lines between adjacent keys (subtle) ──
        for i in range(12):
            j = (i + 1) % 12
            x0, y0 = _pos(CX, CY, OUTER_R, i)
            x1, y1 = _pos(CX, CY, OUTER_R, j)
            dist_from_sel = min(abs(i - self.selected), 12 - abs(i - self.selected))
            dist_j = min(abs(j - self.selected), 12 - abs(j - self.selected))
            if dist_from_sel <= 1 and dist_j <= 1:
                line_color = (50, 50, 70)
            else:
                line_color = (20, 20, 30)
            d.draw_line(x0, y0, x1, y1, line_color)

        # ── Draw ring (major keys with paired minor labels) ──
        for i in range(12):
            x, y = _pos(CX, CY, OUTER_R, i)
            hue = _key_hue(i)
            dist = min(abs(i - self.selected), 12 - abs(i - self.selected))

            if dist == 0:
                # Selected key — bright with pulse
                bright = min(1.0, 0.95 + pulse)
                sat = 0.9
            elif dist == 1:
                # Adjacent (closely related) — medium
                bright = 0.55
                sat = 0.7
            elif dist == 6:
                # Tritone (opposite) — dim
                bright = 0.15
                sat = 0.4
            else:
                bright = 0.3
                sat = 0.5

            if self.minor_mode and dist != 0:
                bright *= 0.6  # dim outer when minor is primary

            color = _hsv_to_rgb(hue, sat, bright)

            # Draw key indicator — 3x3 block for selected, 2x2 for others
            if dist == 0:
                d.draw_rect(x - 1, y - 1, 3, 3, color)
            else:
                d.set_pixel(x, y, color)
                d.set_pixel(x + 1, y, color)
                d.set_pixel(x, y + 1, color)
                d.set_pixel(x + 1, y + 1, color)

            # Position labels near the dot — major outside, minor inside
            a = _key_angle(i)

            # Major label: outside the ring
            if self.view == 0:
                major_label = KEYS[i]['major']
            else:
                major_label = _sig_label(KEYS[i])
            lx = CX + int((OUTER_R + 5) * math.cos(a))
            ly = CY + int((OUTER_R + 5) * math.sin(a))
            tw = len(major_label) * 4
            lx -= tw // 2
            ly -= 2
            lx = max(0, min(lx, 63 - tw))
            ly = max(0, min(ly, 59))
            major_lc = _dim(color, 1.2) if dist == 0 else _dim(color, 0.9)
            major_lc = (min(255, major_lc[0]), min(255, major_lc[1]), min(255, major_lc[2]))
            if not self.minor_mode:
                d.draw_text_raw(lx, ly, major_label, major_lc)
            else:
                d.draw_text_raw(lx, ly, major_label, _dim(major_lc, 0.5))

            # Minor label: just inside the ring
            minor_label = KEYS[i]['minor']
            mlx = CX + int((OUTER_R - 7) * math.cos(a))
            mly = CY + int((OUTER_R - 7) * math.sin(a))
            mtw = len(minor_label) * 4
            mlx -= mtw // 2
            mly -= 2
            mlx = max(0, min(mlx, 63 - mtw))
            mly = max(0, min(mly, 59))
            # Minor color — desaturated, dimmer version of the key color
            if dist == 0:
                minor_bright = min(1.0, 0.8 + pulse) if self.minor_mode else 0.45
                minor_sat = 0.7 if self.minor_mode else 0.4
            elif dist == 1:
                minor_bright = 0.35 if self.minor_mode else 0.2
                minor_sat = 0.5
            else:
                minor_bright = 0.18 if self.minor_mode else 0.1
                minor_sat = 0.35
            minor_color = _hsv_to_rgb(hue, minor_sat, minor_bright)
            if dist <= 2 or self.minor_mode:
                d.draw_text_raw(mlx, mly, minor_label, minor_color)

        # ── Center: selected key info ──
        sel_color = _hsv_to_rgb(_key_hue(self.selected), 0.8, 0.9)
        if self.minor_mode:
            key_name = key_data['minor']
        else:
            key_name = key_data['major']
        sig = _sig_label(key_data)
        # Key name centered above midpoint
        kw = len(key_name) * 4
        d.draw_text_raw(CX - kw // 2, CY - 5, key_name, sel_color)
        # Signature centered below midpoint
        sw = len(sig) * 4
        d.draw_text_raw(CX - sw // 2, CY + 1, sig, _dim(sel_color, 0.6))

        # ── Title at top ──
        d.draw_text_small(2, 1, '5THS', (60, 60, 80))

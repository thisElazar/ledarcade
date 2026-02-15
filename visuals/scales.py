"""Musical scales reference with piano keyboard diagram on 64x64 LED matrix.

Controls:
  Up/Down    - Cycle through scales
  Left/Right - Transpose root note (C, C#, D, ... B)
  Action     - Toggle note names / interval numbers / scale degrees
"""

import math
from . import Visual

# ── Note names in chromatic order ─────────────────────────────────
CHROMATIC = ['C', 'C#', 'D', 'Eb', 'E', 'F', 'F#', 'G', 'Ab', 'A', 'Bb', 'B']

# ── Scale degree labels (relative to major scale) ─────────────────
# Indexed by semitone offset 0-11; None = not in any diatonic position
DEGREE_LABELS = {
    0: 'R', 1: 'b2', 2: '2', 3: 'b3', 4: '3', 5: '4',
    6: 'b5', 7: '5', 8: 'b6', 9: '6', 10: 'b7', 11: '7',
}

# ── Scale data ────────────────────────────────────────────────────
SCALES = [
    # ── Major & Minor ─────────────────────────────────────
    {
        'name': 'MAJOR',
        'family': 'Major & Minor',
        'subtitle': 'IONIAN - HAPPY BRIGHT',
        'intervals': [0, 2, 4, 5, 7, 9, 11],
        'pattern': 'W W H W W W H',
    },
    {
        'name': 'NAT MINOR',
        'family': 'Major & Minor',
        'subtitle': 'AEOLIAN - SAD DARK',
        'intervals': [0, 2, 3, 5, 7, 8, 10],
        'pattern': 'W H W W H W W',
    },
    {
        'name': 'HARM MINOR',
        'family': 'Major & Minor',
        'subtitle': 'RAISED 7TH - EXOTIC',
        'intervals': [0, 2, 3, 5, 7, 8, 11],
        'pattern': 'W H W W H WH H',
    },
    {
        'name': 'MEL MINOR',
        'family': 'Major & Minor',
        'subtitle': 'ASCENDING - JAZZ',
        'intervals': [0, 2, 3, 5, 7, 9, 11],
        'pattern': 'W H W W W W H',
    },

    # ── Pentatonic & Blues ────────────────────────────────
    {
        'name': 'MAJ PENT',
        'family': 'Pentatonic & Blues',
        'subtitle': 'COUNTRY FOLK HAPPY',
        'intervals': [0, 2, 4, 7, 9],
        'pattern': 'W W WH W WH',
    },
    {
        'name': 'MIN PENT',
        'family': 'Pentatonic & Blues',
        'subtitle': 'ROCK BLUES UNIVERSAL',
        'intervals': [0, 3, 5, 7, 10],
        'pattern': 'WH W W WH W',
    },
    {
        'name': 'BLUES',
        'family': 'Pentatonic & Blues',
        'subtitle': 'BLUE NOTE ADDED',
        'intervals': [0, 3, 5, 6, 7, 10],
        'pattern': 'WH W H H WH W',
    },

    # ── Modes ─────────────────────────────────────────────
    {
        'name': 'DORIAN',
        'family': 'Modes',
        'subtitle': 'JAZZY MINOR',
        'intervals': [0, 2, 3, 5, 7, 9, 10],
        'pattern': 'W H W W W H W',
    },
    {
        'name': 'PHRYGIAN',
        'family': 'Modes',
        'subtitle': 'SPANISH FLAMENCO',
        'intervals': [0, 1, 3, 5, 7, 8, 10],
        'pattern': 'H W W W H W W',
    },
    {
        'name': 'LYDIAN',
        'family': 'Modes',
        'subtitle': 'DREAMY BRIGHT',
        'intervals': [0, 2, 4, 6, 7, 9, 11],
        'pattern': 'W W W H W W H',
    },
    {
        'name': 'MIXOLYDIAN',
        'family': 'Modes',
        'subtitle': 'DOMINANT BLUESY',
        'intervals': [0, 2, 4, 5, 7, 9, 10],
        'pattern': 'W W H W W H W',
    },
    {
        'name': 'LOCRIAN',
        'family': 'Modes',
        'subtitle': 'DIMINISHED UNSTABLE',
        'intervals': [0, 1, 3, 5, 6, 8, 10],
        'pattern': 'H W W H W W W',
    },

    # ── Exotic ────────────────────────────────────────────
    {
        'name': 'WHOLE TONE',
        'family': 'Exotic',
        'subtitle': 'DREAMY FLOATING',
        'intervals': [0, 2, 4, 6, 8, 10],
        'pattern': 'W W W W W W',
    },
    {
        'name': 'CHROMATIC',
        'family': 'Exotic',
        'subtitle': 'ALL 12 TONES',
        'intervals': [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11],
        'pattern': 'ALL HALF STEPS',
    },
    {
        'name': 'HUNGARIAN',
        'family': 'Exotic',
        'subtitle': 'HUNGARIAN MINOR',
        'intervals': [0, 2, 3, 6, 7, 8, 11],
        'pattern': 'W H WH H H WH H',
    },
    {
        'name': 'JAPANESE',
        'family': 'Exotic',
        'subtitle': 'IN SCALE - KOTO',
        'intervals': [0, 1, 5, 7, 8],
        'pattern': 'H WW W H WW',
    },
]

# ── Display modes for action button toggle ────────────────────────
MODE_NAMES = ['NOTES', 'NUMBERS', 'DEGREES']

# ── Piano keyboard layout constants ───────────────────────────────
# 7 white keys at 8px each = 56px, starting at x=4
KB_LEFT = 4           # left edge of keyboard
KB_WHITE_W = 8        # white key width (drawn as W-1 for 1px gap)
KB_WHITE_H = 26       # white key height
KB_BLACK_W = 5        # black key width
KB_BLACK_H = 15       # black key height
KB_TOP = 17           # top of keyboard area
KB_BOTTOM = KB_TOP + KB_WHITE_H - 1

# White key x positions (left edge of each key)
# 7 white keys: C=0, D=1, E=2, F=3, G=4, A=5, B=6
WHITE_KEY_X = [KB_LEFT + i * KB_WHITE_W for i in range(7)]

# Black key x positions (centered between white keys)
# C#=between C&D, D#=between D&E, F#=between F&G, G#=between G&A, A#=between A&B
BLACK_KEY_INDICES = [0, 1, 3, 4, 5]  # which white key pairs have a black between them
BLACK_KEY_X = [KB_LEFT + i * KB_WHITE_W + KB_WHITE_W - KB_BLACK_W // 2
               for i in BLACK_KEY_INDICES]

# Map semitone (0-11) to key type and position
# semitone: (is_black, key_index_for_drawing)
# White keys: C=0, D=2, E=4, F=5, G=7, A=9, B=11
# Black keys: C#=1, D#=3, F#=6, G#=8, A#=10
WHITE_SEMITONES = [0, 2, 4, 5, 7, 9, 11]  # C D E F G A B
BLACK_SEMITONES = [1, 3, 6, 8, 10]         # C# D# F# G# A#

# Center x of each white key
WHITE_CENTER_X = [KB_LEFT + i * KB_WHITE_W + KB_WHITE_W // 2 for i in range(7)]

# Center x of each black key
BLACK_CENTER_X = [KB_LEFT + i * KB_WHITE_W + KB_WHITE_W - KB_BLACK_W // 2 + KB_BLACK_W // 2
                  for i in BLACK_KEY_INDICES]

# Mapping from semitone to (is_black, center_x, key_left_x, key_width)
KEY_MAP = {}
for i, s in enumerate(WHITE_SEMITONES):
    KEY_MAP[s] = (False, WHITE_CENTER_X[i], WHITE_KEY_X[i], KB_WHITE_W)
for i, s in enumerate(BLACK_SEMITONES):
    KEY_MAP[s] = (True, BLACK_CENTER_X[i], BLACK_KEY_X[i], KB_BLACK_W)

# ── Colors ────────────────────────────────────────────────────────
HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
WHITE_KEY_COLOR = (180, 180, 180)
WHITE_KEY_EDGE = (120, 120, 120)
BLACK_KEY_COLOR = (25, 25, 30)
BLACK_KEY_EDGE = (50, 50, 55)
KEY_BG = (15, 15, 20)


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


def _root_color(chromatic_idx, sat=0.85, val=0.9):
    """Color for a root note, matching circle-of-fifths hue mapping."""
    fifths_pos = (chromatic_idx * 7) % 12
    hue = fifths_pos * 30  # same as circle5ths: 360/12 = 30 per step
    return _hsv_to_rgb(hue, sat, val)


class Scales(Visual):
    name = "SCALES"
    description = "Piano scale reference"
    category = "music"

    def reset(self):
        self.time = 0.0
        self.scale_idx = 0
        self.root_idx = 0         # index into CHROMATIC (0=C)
        self.display_mode = 0     # 0=note names, 1=interval numbers, 2=scale degrees

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Up/Down: cycle scales
        if input_state.up_pressed:
            self.scale_idx = (self.scale_idx - 1) % len(SCALES)
            consumed = True
        elif input_state.down_pressed:
            self.scale_idx = (self.scale_idx + 1) % len(SCALES)
            consumed = True

        # Left/Right: transpose root
        if input_state.left_pressed:
            self.root_idx = (self.root_idx - 1) % len(CHROMATIC)
            consumed = True
        elif input_state.right_pressed:
            self.root_idx = (self.root_idx + 1) % len(CHROMATIC)
            consumed = True

        # Action: toggle display mode
        if input_state.action_l or input_state.action_r:
            self.display_mode = (self.display_mode + 1) % len(MODE_NAMES)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        d = self.display
        d.clear()

        scale = SCALES[self.scale_idx]
        root = self.root_idx
        color = _root_color(root)

        # Get active semitones (absolute, 0-11)
        active_semitones = set((root + iv) % 12 for iv in scale['intervals'])

        # ── Header: scale name + root ──────────────────────
        self._draw_header(d, scale, root, color)

        # ── Piano keyboard ─────────────────────────────────
        self._draw_keyboard(d, active_semitones, root, color)

        # ── Note labels below keyboard ─────────────────────
        self._draw_labels(d, scale, active_semitones, root, color)

        # ── Footer ────────────────────────────────────────
        self._draw_footer(d, scale, color)

    def _draw_header(self, d, scale, root, color):
        """Draw scale name and key at top."""
        d.draw_rect(0, 0, 64, 8, HEADER_BG)

        root_name = CHROMATIC[root]
        title = root_name + ' ' + scale['name']

        # Truncate if too long for display
        if len(title) > 14:
            title = title[:14]

        d.draw_text_raw(2, 1, title, color)

        # Subtitle / character description
        subtitle = scale.get('subtitle', '')
        if subtitle:
            if len(subtitle) > 14:
                subtitle = subtitle[:14]
            d.draw_text_raw(2, 9, subtitle, _dim(color, 0.4))

        # Thin separator line
        for x in range(64):
            d.set_pixel(x, 16, (40, 40, 50))

    def _draw_keyboard(self, d, active_semitones, root, color):
        """Draw piano keyboard with highlighted scale tones."""
        # Background behind keyboard
        d.draw_rect(KB_LEFT - 1, KB_TOP, KB_WHITE_W * 7 + 2, KB_WHITE_H + 1, KEY_BG)

        # Draw white keys first
        for i, semitone in enumerate(WHITE_SEMITONES):
            kx = WHITE_KEY_X[i]
            is_active = semitone in active_semitones
            is_root = semitone == root

            if is_root:
                key_color = _root_color(root, sat=1.0, val=1.0)
            elif is_active:
                key_color = color
            else:
                key_color = WHITE_KEY_COLOR

            # Key body
            d.draw_rect(kx, KB_TOP, KB_WHITE_W - 1, KB_WHITE_H, key_color)

            # Darken edges for depth if not highlighted
            if not is_active and not is_root:
                for y in range(KB_TOP, KB_BOTTOM + 1):
                    d.set_pixel(kx + KB_WHITE_W - 2, y, WHITE_KEY_EDGE)

        # Draw black keys on top
        for i, semitone in enumerate(BLACK_SEMITONES):
            kx = BLACK_KEY_X[i]
            is_active = semitone in active_semitones
            is_root = semitone == root

            if is_root:
                key_color = _root_color(root, sat=1.0, val=1.0)
            elif is_active:
                key_color = _dim(color, 0.8)
            else:
                key_color = BLACK_KEY_COLOR

            # Key body
            d.draw_rect(kx, KB_TOP, KB_BLACK_W, KB_BLACK_H, key_color)

            # Subtle edge highlight
            if not is_active and not is_root:
                for y in range(KB_TOP, KB_TOP + KB_BLACK_H):
                    d.set_pixel(kx + KB_BLACK_W - 1, y, BLACK_KEY_EDGE)

    def _draw_labels(self, d, scale, active_semitones, root, color):
        """Draw note name / number / degree labels below keys."""
        white_y = KB_BOTTOM + 2
        black_y = white_y + 7  # stagger black-key labels to avoid overlap

        for iv in scale['intervals']:
            semitone = (root + iv) % 12
            is_black, cx, kx, kw = KEY_MAP[semitone]
            is_root = (semitone == root)

            if self.display_mode == 0:
                # Note names — use raw text for proper # and b glyphs
                label = CHROMATIC[semitone]
            elif self.display_mode == 1:
                # Interval numbers (1-based position in scale)
                idx = scale['intervals'].index(iv)
                label = str(idx + 1)
            else:
                # Scale degrees
                label = DEGREE_LABELS.get(iv, '?')
                if len(label) > 2:
                    label = label[:2]

            lc = _root_color(root, sat=1.0, val=1.0) if is_root else _dim(color, 0.9)

            # Center the label on the key
            tw = len(label) * 4
            lx = cx - tw // 2

            # Clamp to display bounds
            lx = max(0, min(63 - tw, lx))

            label_y = black_y if is_black else white_y
            d.draw_text_raw(lx, label_y, label, lc)

    def _draw_footer(self, d, scale, color):
        """Draw scale position and display mode at bottom."""
        # Separator line above footer
        for x in range(64):
            d.set_pixel(x, 57, (40, 40, 50))

        # Scale position indicator
        pos_text = f'{self.scale_idx + 1}/{len(SCALES)}'
        d.draw_text_raw(2, 59, pos_text, TEXT_DIM)

        # Display mode indicator on right
        mode_label = MODE_NAMES[self.display_mode][:3]
        d.draw_text_raw(44, 59, mode_label, TEXT_DIM)

def _dim(color, factor):
    """Dim a color by a factor (0.0 to 1.0)."""
    return tuple(max(0, min(255, int(c * factor))) for c in color)

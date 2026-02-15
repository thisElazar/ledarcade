"""Knots - Animated knot-tying reference on 64x64 LED matrix.

Each knot shows a step-by-step rope animation that progressively forms the
knot shape through keyframe stages.  Below: name, use description.

Ten knots across three families: Essential, Hitches, Bends.
"""

import math
from . import Visual

# ── Rope colors ──────────────────────────────────────────────────
ROPE_MAIN = (200, 170, 110)
ROPE_HI   = (230, 205, 150)
ROPE_SHAD = (150, 125, 75)
ROPE_TIP  = (255, 245, 210)    # bright working-end marker

# Second rope (for sheet bend, square knot)
ROPE2_MAIN = (140, 90, 60)
ROPE2_HI   = (175, 120, 85)
ROPE2_SHAD = (100, 65, 40)
ROPE2_TIP  = (220, 160, 110)

# Speed multipliers
SPEEDS = [0.5, 0.75, 1.0, 1.5, 2.0]
SPEED_LABELS = ['.5X', '.75X', '1X', '1.5X', '2X']
DEFAULT_SPEED_IDX = 2  # 1.0x

# UI
HEADER_BG = (20, 20, 30)
TEXT_DIM = (100, 100, 120)
SEP_COLOR = (50, 50, 70)
LABEL_DIM = (70, 70, 90)

# Families
FAMILIES = ["ESSENTIAL", "HITCHES", "BENDS"]
FAMILY_COLORS = [
    (180, 140, 80),    # ESSENTIAL = warm tan
    (120, 160, 200),   # HITCHES = steel blue
    (160, 130, 100),   # BENDS = brown
]

# ── Knot data ─────────────────────────────────────────────────────
# Each keyframe is a list of (x, y) points the rope passes through.
# The animation area is roughly y=9..33, x=2..61.
# 'post' entries define a vertical post/cleat to draw behind the rope.

KNOTS = [
    # ── ESSENTIAL (0) ──
    {'name': 'OVERHAND', 'family': 0, 'num': 1,
     'desc': 'SIMPLEST KNOT / STOPPER / BASE FOR OTHERS',
     'labels': ['ROPE', 'LOOP', 'TUCK', 'PULL', 'OVERHAND'],
     'frames': [
         # Straight rope
         [(8, 22), (16, 22), (24, 22), (32, 22), (40, 22), (48, 22), (56, 22)],
         # Form a loop
         [(8, 22), (20, 22), (32, 16), (40, 22), (32, 28), (24, 22), (32, 16)],
         # Tuck end through
         [(8, 22), (20, 22), (30, 16), (38, 22), (30, 28), (26, 22), (30, 14), (38, 18)],
         # Pulling tight
         [(10, 22), (22, 22), (28, 18), (32, 22), (28, 26), (26, 22), (30, 18), (42, 20)],
         # Finished overhand
         [(12, 22), (24, 22), (29, 19), (32, 22), (29, 25), (27, 22), (31, 19), (40, 22)],
     ],
     'hold': [1.5, 1.2, 1.2, 1.2, 2.5]},

    {'name': 'FIGURE EIGHT', 'family': 0, 'num': 2,
     'desc': 'STOPPER KNOT / CLIMBING / SAILING / EASY TO UNTIE',
     'labels': ['ROPE', 'LOOP', 'TWIST', 'TUCK', 'PULL', 'FIGURE 8'],
     'frames': [
         [(8, 22), (16, 22), (24, 22), (32, 22), (40, 22), (48, 22), (56, 22)],
         # Make a loop
         [(8, 22), (18, 22), (28, 14), (38, 22), (28, 30), (18, 22)],
         # Cross over (figure 8 shape forming)
         [(8, 22), (18, 22), (28, 14), (38, 22), (28, 30), (20, 24), (28, 18), (38, 14)],
         # Tuck through
         [(8, 22), (18, 22), (26, 14), (36, 20), (30, 28), (22, 24), (26, 16), (36, 12)],
         # Tighten
         [(12, 22), (22, 22), (27, 16), (33, 22), (27, 28), (24, 22), (28, 17), (36, 18)],
         # Done
         [(14, 22), (24, 22), (28, 17), (33, 22), (28, 27), (25, 22), (29, 17), (36, 20)],
     ],
     'hold': [1.5, 1.0, 1.0, 1.0, 1.0, 2.5]},

    {'name': 'SQUARE KNOT', 'family': 0, 'num': 3,
     'desc': 'REEF KNOT / FIRST AID / PACKAGES / FLAT & SECURE',
     'labels': ['TWO ROPES', 'CROSS', 'WRAP', 'CROSS BACK', 'PULL', 'SQUARE'],
     'two_ropes': True,
     'frames': [
         # Two rope ends
         [(8, 20), (20, 20), (32, 20)],
         # Cross right over left
         [(8, 20), (22, 20), (34, 18), (40, 14)],
         # Wrap under
         [(8, 20), (22, 20), (30, 16), (26, 14), (22, 18), (30, 22)],
         # Cross left over right
         [(8, 20), (22, 20), (30, 16), (26, 14), (24, 18), (30, 22), (36, 18)],
         # Pull tight
         [(10, 20), (24, 20), (29, 17), (32, 20), (29, 23), (26, 20), (30, 17), (38, 20)],
         # Finished
         [(12, 20), (25, 20), (29, 17), (33, 20), (29, 23), (26, 20), (30, 17), (40, 20)],
     ],
     'frames2': [
         [(56, 24), (44, 24), (32, 24)],
         [(56, 24), (42, 24), (30, 26), (24, 30)],
         [(56, 24), (42, 24), (34, 28), (38, 30), (42, 26), (34, 22)],
         [(56, 24), (42, 24), (34, 28), (38, 30), (40, 26), (34, 22), (28, 26)],
         [(54, 24), (40, 24), (35, 27), (32, 24), (35, 21), (38, 24), (34, 27), (26, 24)],
         [(52, 24), (39, 24), (35, 27), (31, 24), (35, 21), (38, 24), (34, 27), (24, 24)],
     ],
     'hold': [1.5, 1.0, 1.0, 1.0, 1.0, 2.5]},

    {'name': 'SLIP KNOT', 'family': 0, 'num': 4,
     'desc': 'QUICK RELEASE / CROCHET / TEMPORARY TIE / PULL TO UNDO',
     'labels': ['ROPE', 'BIGHT', 'LOOP OVER', 'PULL BIGHT', 'SLIP KNOT'],
     'frames': [
         [(8, 22), (16, 22), (24, 22), (32, 22), (40, 22), (48, 22), (56, 22)],
         # Form a bight (U-shape in standing part)
         [(8, 22), (18, 22), (24, 28), (30, 22), (40, 22), (48, 22), (56, 22)],
         # Loop the working end around
         [(8, 22), (18, 22), (24, 28), (30, 18), (36, 24), (30, 30), (24, 24), (30, 18)],
         # Pull bight through
         [(8, 22), (20, 22), (26, 26), (32, 20), (28, 16), (24, 20), (28, 24), (40, 22)],
         # Finished slip knot
         [(10, 22), (22, 22), (28, 24), (32, 20), (28, 16), (25, 20), (29, 24), (42, 22)],
     ],
     'hold': [1.5, 1.2, 1.2, 1.2, 2.5]},

    # ── HITCHES (1) ──
    {'name': 'CLOVE HITCH', 'family': 1, 'num': 5,
     'desc': 'SECURING TO A POST / QUICK TIE / ADJUSTABLE',
     'labels': ['ROPE', 'WRAP 1', 'WRAP 2', 'TUCK', 'CLOVE HITCH'],
     'post': (32, 12, 32),  # x, y_top, y_bot
     'frames': [
         [(8, 22), (16, 22), (24, 22), (40, 22), (48, 22), (56, 22)],
         # First wrap around post
         [(8, 22), (18, 22), (28, 18), (36, 22), (40, 26), (36, 30), (28, 26)],
         # Second wrap
         [(8, 22), (18, 22), (28, 18), (36, 20), (36, 26), (28, 30), (28, 24), (36, 18)],
         # Tuck under
         [(8, 22), (18, 22), (28, 18), (36, 20), (36, 26), (28, 28), (28, 22), (36, 16), (44, 14)],
         # Done
         [(8, 22), (20, 22), (28, 18), (36, 20), (36, 26), (28, 28), (28, 22), (36, 16), (46, 14)],
     ],
     'hold': [1.5, 1.2, 1.2, 1.2, 2.5]},

    {'name': 'CLEAT HITCH', 'family': 1, 'num': 6,
     'desc': 'DOCKING BOATS / SECURING TO CLEATS / NAUTICAL',
     'labels': ['ROPE', 'AROUND', 'CROSS', 'FIGURE 8', 'LOCK', 'CLEAT'],
     'cleat': True,
     'frames': [
         [(8, 24), (16, 24), (24, 24), (32, 24), (40, 24), (48, 24)],
         # Around the far horn
         [(8, 24), (18, 24), (36, 20), (42, 24), (36, 28), (28, 24)],
         # Cross over
         [(8, 24), (18, 24), (36, 20), (42, 24), (36, 28), (26, 22), (36, 18)],
         # Figure-8 pattern
         [(8, 24), (18, 24), (36, 20), (42, 24), (36, 28), (26, 22), (36, 18), (42, 22)],
         # Locking hitch
         [(8, 24), (18, 24), (36, 20), (42, 24), (36, 28), (26, 22), (36, 18), (40, 20), (32, 18)],
         # Done
         [(8, 24), (18, 24), (36, 20), (42, 24), (36, 28), (26, 22), (36, 18), (40, 20), (30, 16)],
     ],
     'hold': [1.5, 1.0, 1.0, 1.0, 1.0, 2.5]},

    {'name': 'TAUT-LINE', 'family': 1, 'num': 7,
     'desc': 'ADJUSTABLE CAMPING / GUY LINES / SLIDES UNDER LOAD',
     'labels': ['ROPE', 'LOOP', 'WRAP 1', 'WRAP 2', 'TUCK OUT', 'TAUT-LINE'],
     'post': (20, 12, 32),
     'frames': [
         [(8, 16), (16, 16), (20, 16), (20, 28), (32, 28), (44, 28), (56, 28)],
         # Form loop around standing line
         [(8, 16), (16, 16), (20, 16), (20, 28), (28, 24), (24, 20), (20, 24)],
         # First wrap inside loop
         [(8, 16), (16, 16), (20, 16), (20, 28), (26, 24), (22, 20), (20, 24), (24, 28)],
         # Second wrap
         [(8, 16), (16, 16), (20, 16), (20, 28), (26, 22), (22, 18), (20, 22), (24, 26), (28, 22)],
         # Tuck outside the loop
         [(8, 16), (16, 16), (20, 16), (20, 28), (26, 22), (22, 18), (22, 22), (26, 26), (30, 22), (36, 18)],
         # Done
         [(8, 16), (16, 16), (20, 16), (20, 28), (26, 22), (22, 18), (22, 22), (26, 26), (30, 22), (40, 16)],
     ],
     'hold': [1.5, 1.0, 1.0, 1.0, 1.0, 2.5]},

    {"name": "TRUCKER'S", 'family': 1, 'num': 8,
     'desc': 'SECURING LOADS / 3:1 ADVANTAGE / VERY STRONG',
     'labels': ['ROPE', 'BIGHT', 'LOOP', 'THREAD', 'PULL', "TRUCKER'S"],
     'frames': [
         [(8, 14), (20, 14), (32, 14), (44, 14), (56, 14), (56, 22), (56, 30)],
         # Form a bight in the middle
         [(8, 14), (20, 14), (28, 20), (36, 14), (48, 14), (56, 22), (56, 30)],
         # Make a slip loop
         [(8, 14), (20, 14), (26, 18), (32, 14), (28, 22), (34, 18), (48, 14), (56, 22), (56, 30)],
         # Thread working end through anchor and back up
         [(8, 14), (20, 14), (26, 18), (32, 14), (28, 22), (34, 18), (46, 16), (50, 24), (44, 30), (36, 26)],
         # Pull tight for mechanical advantage
         [(8, 14), (20, 14), (26, 18), (32, 14), (28, 22), (34, 18), (44, 18), (48, 26), (42, 30), (34, 24)],
         # Done
         [(8, 14), (20, 14), (26, 18), (32, 14), (28, 22), (34, 18), (42, 18), (46, 26), (40, 30), (32, 24)],
     ],
     'hold': [1.5, 1.0, 1.0, 1.0, 1.0, 2.5]},

    # ── BENDS (2) ──
    {'name': 'BOWLINE', 'family': 2, 'num': 9,
     'desc': 'KING OF KNOTS / RESCUE / SAILING / WILL NOT SLIP',
     'labels': ['ROPE', 'LOOP', 'UP THRU', 'AROUND', 'BACK DOWN', 'BOWLINE'],
     'frames': [
         [(8, 28), (16, 28), (24, 28), (32, 28), (40, 28), (48, 28), (56, 28)],
         # Small loop in standing part
         [(8, 28), (16, 28), (24, 28), (30, 22), (36, 28), (44, 28), (56, 28)],
         # Working end up through loop
         [(8, 28), (16, 28), (24, 28), (30, 22), (36, 28), (36, 22), (32, 16), (28, 20)],
         # Around behind standing part
         [(8, 28), (16, 28), (24, 28), (30, 22), (36, 28), (36, 22), (30, 14), (22, 16), (20, 22)],
         # Back down through loop
         [(8, 28), (16, 28), (24, 28), (30, 22), (36, 28), (36, 22), (30, 14), (22, 18), (26, 24), (32, 20)],
         # Finished bowline with loop
         [(8, 28), (18, 28), (26, 28), (30, 22), (36, 28), (36, 22), (30, 14), (22, 18), (26, 24), (32, 20)],
     ],
     'hold': [1.5, 1.0, 1.0, 1.0, 1.0, 2.5]},

    {'name': 'SHEET BEND', 'family': 2, 'num': 10,
     'desc': 'JOINING TWO ROPES / DIFFERENT SIZES / RELIABLE',
     'labels': ['TWO ROPES', 'BIGHT', 'THROUGH', 'AROUND', 'TUCK', 'SHEET BEND'],
     'two_ropes': True,
     'frames': [
         # Rope 1 straight
         [(8, 20), (20, 20), (32, 20), (44, 20), (56, 20)],
         # Rope 1 forms a bight
         [(8, 20), (20, 20), (32, 16), (44, 20), (56, 20)],
         # Still a bight
         [(8, 20), (20, 20), (32, 14), (44, 20), (56, 20)],
         # Bight held
         [(8, 20), (20, 20), (32, 14), (44, 20), (56, 20)],
         # Bight held
         [(8, 20), (20, 20), (32, 14), (44, 20), (56, 20)],
         # Done
         [(8, 20), (20, 20), (32, 14), (44, 20), (56, 20)],
     ],
     'frames2': [
         # Rope 2 straight below
         [(8, 28), (20, 28), (32, 28), (44, 28), (56, 28)],
         # Rope 2 approaches
         [(8, 28), (20, 28), (28, 26), (36, 28), (48, 28)],
         # Through the bight from below
         [(8, 28), (22, 28), (28, 22), (32, 12), (36, 18), (42, 28)],
         # Around behind both legs
         [(8, 28), (22, 28), (28, 22), (32, 12), (24, 14), (18, 18), (22, 24)],
         # Tuck under itself
         [(8, 28), (22, 28), (28, 22), (32, 12), (24, 14), (20, 18), (24, 22), (32, 18)],
         # Done
         [(8, 28), (22, 28), (28, 22), (32, 12), (24, 14), (20, 18), (24, 22), (34, 18)],
     ],
     'hold': [1.5, 1.0, 1.0, 1.0, 1.0, 2.5]},
]

# Build per-family index
_FAMILY_KNOTS = [[] for _ in range(len(FAMILIES))]
for _i, _k in enumerate(KNOTS):
    _FAMILY_KNOTS[_k['family']].append(_i)


def _dim(color, factor=0.4):
    return (int(color[0] * factor), int(color[1] * factor), int(color[2] * factor))


def _lerp_points(pts_a, pts_b, t):
    """Interpolate between two keyframes. Handles different point counts."""
    len_a, len_b = len(pts_a), len(pts_b)
    # Use the longer list as target length
    n = max(len_a, len_b)
    result = []
    for i in range(n):
        # Map index into each list
        ia = min(i, len_a - 1)
        ib = min(i, len_b - 1)
        ax, ay = pts_a[ia]
        bx, by = pts_b[ib]
        result.append((ax + (bx - ax) * t, ay + (by - ay) * t))
    return result


class Knots(Visual):
    name = "KNOTS"
    description = "Knot-tying reference"
    category = "household"

    SCROLL_DELAY = 0.4
    SCROLL_RATE = 0.12
    SCROLL_LEAD_IN = 30

    # Layout
    NAME_Y = 1
    SEP1_Y = 7
    ANIM_TOP = 8
    ANIM_BOT = 43
    LABEL_Y = 44
    SEP2_Y = 50
    DESC_Y = 51
    FOOT_SEP_Y = 57
    FOOT_Y = 59
    ROPE_Y_SHIFT = 4   # shift rope data down to center in expanded area

    # Transition
    TRANSITION_TIME = 0.4  # seconds to interpolate between keyframes

    def reset(self):
        self.time = 0.0
        self.knot_idx = 0
        self.speed_idx = DEFAULT_SPEED_IDX
        self.frame = 0
        self.frame_timer = 0.0
        self.transition_t = 1.0  # 1.0 = fully at current frame
        self._name_scroll_x = 0.0
        self._desc_scroll_x = 0.0

    def _current(self):
        return KNOTS[self.knot_idx % len(KNOTS)]

    def _step(self, direction):
        self.knot_idx = (self.knot_idx + direction) % len(KNOTS)
        self._name_scroll_x = 0.0
        self._desc_scroll_x = 0.0
        self.frame = 0
        self.frame_timer = 0.0
        self.transition_t = 1.0

    def _jump_family(self, direction):
        cur = self._current()['family']
        target = (cur + direction) % len(FAMILIES)
        if _FAMILY_KNOTS[target]:
            self.knot_idx = _FAMILY_KNOTS[target][0]
        self._name_scroll_x = 0.0
        self._desc_scroll_x = 0.0
        self.frame = 0
        self.frame_timer = 0.0
        self.transition_t = 1.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self._step(-1)
            consumed = True
        elif input_state.down_pressed:
            self._step(1)
            consumed = True

        if input_state.left_pressed:
            self.speed_idx = max(0, self.speed_idx - 1)
            consumed = True
        elif input_state.right_pressed:
            self.speed_idx = min(len(SPEEDS) - 1, self.speed_idx + 1)
            consumed = True

        if input_state.action_l or input_state.action_r:
            # Restart current knot animation
            self.frame = 0
            self.frame_timer = 0.0
            self.transition_t = 1.0
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        speed = SPEEDS[self.speed_idx]

        knot = self._current()
        n_frames = len(knot['frames'])

        # Advance animation (scaled by speed)
        self.frame_timer += dt * speed
        hold = knot['hold'][self.frame]

        if self.transition_t < 1.0:
            self.transition_t = min(1.0, self.transition_t + dt * speed / self.TRANSITION_TIME)

        if self.frame_timer >= hold:
            self.frame_timer -= hold
            old_frame = self.frame
            self.frame = (self.frame + 1) % n_frames
            if self.frame != old_frame:
                self.transition_t = 0.0

        # Scroll text
        knot = self._current()
        self._name_scroll_x = self._advance_scroll(
            self._name_scroll_x, knot['name'], 48, dt, 18)
        self._desc_scroll_x = self._advance_scroll(
            self._desc_scroll_x, knot['desc'], 60, dt, 16)

    def _advance_scroll(self, scroll_x, text, avail_px, dt, speed):
        text_px = len(text) * 4
        if text_px > avail_px:
            scroll_x += dt * speed
            total = self.SCROLL_LEAD_IN + text_px + 20
            if scroll_x >= total:
                scroll_x -= total
        return scroll_x

    # ── Drawing ───────────────────────────────────────────────────

    def draw(self):
        d = self.display
        d.clear()

        knot = self._current()
        fam = knot['family']
        fam_color = FAMILY_COLORS[fam]

        # ── Header ──
        d.draw_rect(0, 0, 64, self.SEP1_Y, HEADER_BG)
        num_str = str(knot['num'])
        d.draw_text_small(1, self.NAME_Y, num_str, _dim(fam_color, 0.6))
        name_x = len(num_str) * 4 + 2
        self._draw_scrolling_text(d, name_x, self.NAME_Y,
                                  knot['name'], fam_color,
                                  self._name_scroll_x, 63 - name_x)
        self._draw_sep(d, self.SEP1_Y)

        # ── Animation area ──
        self._draw_animation(d, knot)
        self._draw_sep(d, self.SEP2_Y)

        # ── Description (scrolling) ──
        self._draw_scrolling_text(d, 2, self.DESC_Y,
                                  knot['desc'], TEXT_DIM,
                                  self._desc_scroll_x, 60)

        # ── Footer ──
        self._draw_sep(d, self.FOOT_SEP_Y)
        d.draw_rect(0, self.FOOT_SEP_Y + 1, 64, 6, HEADER_BG)
        pos_str = f'{self.knot_idx + 1}/{len(KNOTS)}'
        d.draw_text_small(1, self.FOOT_Y, pos_str, TEXT_DIM)
        spd_str = SPEED_LABELS[self.speed_idx]
        spd_px = len(spd_str) * 4
        d.draw_text_small(63 - spd_px, self.FOOT_Y, spd_str, TEXT_DIM)

    def _draw_animation(self, d, knot):
        frame = self.frame
        n_frames = len(knot['frames'])
        ys = self.ROPE_Y_SHIFT

        # Step label — below the animation area
        label = knot['labels'][frame] if frame < len(knot['labels']) else ''
        label_px = len(label) * 4
        d.draw_text_small((64 - label_px) // 2, self.LABEL_Y, label, LABEL_DIM)

        # Draw post if present (shifted)
        if 'post' in knot:
            px, py_top, py_bot = knot['post']
            post_color = (80, 70, 55)
            post_hi = (100, 90, 70)
            for y in range(py_top + ys, py_bot + ys + 1):
                d.set_pixel(px - 1, y, post_color)
                d.set_pixel(px, y, post_hi)
                d.set_pixel(px + 1, y, post_color)

        # Draw cleat if present (shifted)
        if knot.get('cleat'):
            self._draw_cleat(d, 32, 24 + ys)

        # ── Current rope with interpolation ──
        cur_pts = knot['frames'][frame]
        if self.transition_t < 1.0 and frame > 0:
            prev_pts = knot['frames'][frame - 1]
            t = self.transition_t
            t = t * t * (3 - 2 * t)  # smoothstep
            pts = _lerp_points(prev_pts, cur_pts, t)
        else:
            pts = [(float(x), float(y)) for x, y in cur_pts]
        pts = [(x, y + ys) for x, y in pts]

        self._draw_rope(d, pts, ROPE_MAIN, ROPE_HI, ROPE_SHAD)
        self._draw_tip(d, pts, ROPE_TIP)

        # ── Second rope if present ──
        if knot.get('two_ropes') and 'frames2' in knot:
            cur_pts2 = knot['frames2'][frame]
            if self.transition_t < 1.0 and frame > 0:
                prev_pts2 = knot['frames2'][frame - 1]
                t = self.transition_t
                t = t * t * (3 - 2 * t)
                pts2 = _lerp_points(prev_pts2, cur_pts2, t)
            else:
                pts2 = [(float(x), float(y)) for x, y in cur_pts2]
            pts2 = [(x, y + ys) for x, y in pts2]
            self._draw_rope(d, pts2, ROPE2_MAIN, ROPE2_HI, ROPE2_SHAD)
            self._draw_tip(d, pts2, ROPE2_TIP)

    def _draw_rope(self, d, points, color, highlight, _shadow):
        """Draw 2px rope with standing→working gradient."""
        if len(points) < 2:
            return

        n_segs = len(points) - 1
        for i in range(n_segs):
            # Gradient: standing end dim, working end bright
            f = (0.5 + 0.5 * (i / (n_segs - 1))) if n_segs > 1 else 1.0
            seg_c = _dim(color, f)
            seg_h = _dim(highlight, f)

            x0, y0 = int(points[i][0]), int(points[i][1])
            x1, y1 = int(points[i + 1][0]), int(points[i + 1][1])

            # Clamp to animation area
            y0 = max(self.ANIM_TOP, min(self.ANIM_BOT, y0))
            y1 = max(self.ANIM_TOP, min(self.ANIM_BOT, y1))
            x0 = max(0, min(63, x0))
            x1 = max(0, min(63, x1))

            # Main line
            d.draw_line(x0, y0, x1, y1, seg_c)

            # Highlight offset (2px total width)
            dx = x1 - x0
            dy = y1 - y0
            length = math.sqrt(dx * dx + dy * dy)
            if length > 0:
                nx = -dy / length
                ny = dx / length
                d.draw_line(x0 + int(round(nx)), y0 + int(round(ny)),
                            x1 + int(round(nx)), y1 + int(round(ny)),
                            seg_h)

        # Dots at control points for knot texture
        for idx, (px, py) in enumerate(points):
            ix, iy = int(px), int(py)
            if self.ANIM_TOP <= iy <= self.ANIM_BOT and 0 <= ix < 64:
                f = idx / max(1, len(points) - 1)
                d.set_pixel(ix, iy, _dim(highlight, 0.5 + 0.5 * f))

    def _draw_tip(self, d, points, color):
        """Draw a bright marker at the working end of the rope."""
        if not points:
            return
        tx, ty = int(points[-1][0]), int(points[-1][1])
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                px, py = tx + dx, ty + dy
                if self.ANIM_TOP <= py <= self.ANIM_BOT and 0 <= px < 64:
                    d.set_pixel(px, py, color)

    def _draw_cleat(self, d, cx, cy):
        """Draw a simple boat cleat shape."""
        cleat_color = (100, 100, 110)
        cleat_hi = (130, 130, 145)
        cleat_dark = (70, 70, 80)
        # Base
        for x in range(cx - 3, cx + 4):
            d.set_pixel(x, cy, cleat_color)
            d.set_pixel(x, cy + 1, cleat_dark)
        # Horns
        for x in range(cx - 6, cx - 2):
            d.set_pixel(x, cy - 1, cleat_hi)
            d.set_pixel(x, cy - 2, cleat_color)
        for x in range(cx + 3, cx + 7):
            d.set_pixel(x, cy - 1, cleat_hi)
            d.set_pixel(x, cy - 2, cleat_color)
        # Center post
        d.set_pixel(cx, cy - 1, cleat_hi)
        d.set_pixel(cx, cy - 2, cleat_hi)

    # ── Text helpers ──────────────────────────────────────────────

    def _draw_scrolling_text(self, d, start_x, y, text, color, scroll_x, avail_px):
        text_px = len(text) * 4
        if text_px <= avail_px:
            x = start_x + (avail_px - text_px) // 2
            d.draw_text_small(x, y, text, color)
        else:
            lead = self.SCROLL_LEAD_IN
            total = lead + text_px + 20
            sx = int(scroll_x) % total
            end_x = start_x + avail_px
            for cx in range(start_x, min(end_x, 63)):
                px = sx + (cx - start_x) - lead
                if px < 0:
                    continue
                char_idx = px // 4
                col = px % 4
                if col < 3 and 0 <= char_idx < len(text):
                    ch = text[char_idx]
                    self._draw_char_col(d, cx, y, ch, col, color)

    def _draw_sep(self, d, y):
        for x in range(64):
            d.set_pixel(x, y, SEP_COLOR)

    def _draw_char_col(self, d, x, y, ch, col, color):
        glyph = _FONT.get(ch.upper())
        if glyph is None or col >= 3:
            return
        for row_idx, row in enumerate(glyph):
            if row[col] == '1':
                d.set_pixel(x, y + row_idx, color)


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
    ':': ['000', '010', '000', '010', '000'],
    '/': ['001', '001', '010', '100', '100'],
    '(': ['010', '100', '100', '100', '010'],
    ')': ['010', '001', '001', '001', '010'],
    '&': ['010', '101', '010', '101', '011'],
    "'": ['010', '010', '000', '000', '000'],
    '.': ['000', '000', '000', '000', '010'],
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

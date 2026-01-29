"""
Solitaire Win - Cascading cards
===============================
The classic Windows Solitaire victory animation with bouncing cards.

Controls:
  Left/Right - Adjust spawn rate
  Space      - Reset cascade
  Escape     - Exit
"""

import random
from collections import deque
from . import Visual, Display, Colors, GRID_SIZE


# Card colors (suits)
CARD_COLORS = (
    (255, 50, 50),    # Hearts - red
    (255, 50, 50),    # Diamonds - red
    (40, 40, 40),     # Spades - black
    (40, 40, 40),     # Clubs - black
)

# Card dimensions (2x scale for bold visibility)
CARD_W = 12
CARD_H = 16

# Trail length — shorter than before since 2x cards cover more area
TRAIL_LEN = 8

# Pre-compute rainbow lookup table (avoids per-frame hue_to_rgb calls)
_RAINBOW_SIZE = 64
_RAINBOW_LUT = []
for _i in range(_RAINBOW_SIZE):
    _h6 = _i / _RAINBOW_SIZE * 6.0
    _s = int(_h6)
    _f = _h6 - _s
    if _s == 0:
        _RAINBOW_LUT.append((255, int(255 * _f), 0))
    elif _s == 1:
        _RAINBOW_LUT.append((int(255 * (1 - _f)), 255, 0))
    elif _s == 2:
        _RAINBOW_LUT.append((0, 255, int(255 * _f)))
    elif _s == 3:
        _RAINBOW_LUT.append((0, int(255 * (1 - _f)), 255))
    elif _s == 4:
        _RAINBOW_LUT.append((int(255 * _f), 0, 255))
    else:
        _RAINBOW_LUT.append((255, 0, int(255 * (1 - _f))))
_RAINBOW_LUT = tuple(_RAINBOW_LUT)

# Pre-compute background row for fast clear
_BG_COLOR = (0, 50, 20)
_BG_ROW = [_BG_COLOR] * GRID_SIZE

# Pre-compute card face colors
_BORDER_COLOR = (200, 200, 200)
_FACE_COLOR = (255, 255, 255)


class Card:
    """A single bouncing card."""
    __slots__ = ('x', 'y', 'vx', 'vy', 'color', 'trail', 'alive', 'bounces', 'hue_offset')

    def __init__(self, x, color):
        self.x = x
        self.y = 0
        self.vx = random.uniform(-20, 20)
        self.vy = 0
        self.color = color
        self.trail = deque(maxlen=TRAIL_LEN)
        self.alive = True
        self.bounces = 0
        self.hue_offset = random.random()


class Solitaire(Visual):
    name = "SOLITAIRE"
    description = "Card cascade"
    category = "household"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.spawn_timer = 0.0
        self.spawn_rate = 0.15  # Seconds between card spawns
        self.cards = []
        self.gravity = 120  # Pixels per second squared
        self.bounce_damping = 0.75

        # Spawn a full deck to start
        for _ in range(52):
            self._spawn_card()

    def _spawn_card(self):
        """Spawn a new card at top of screen."""
        x = random.uniform(0, GRID_SIZE - CARD_W)
        color = random.choice(CARD_COLORS)
        card = Card(x, color)
        card.vy = random.uniform(3, 50)
        card.vx = random.uniform(-60, 60)
        self.cards.append(card)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if (input_state.action_l or input_state.action_r):
            self.cards = []
            for _ in range(3):
                self._spawn_card()
            consumed = True

        if input_state.right:
            self.spawn_rate = max(0.1, self.spawn_rate - 0.05)
            consumed = True

        if input_state.left:
            self.spawn_rate = min(1.0, self.spawn_rate + 0.05)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Spawn new cards
        self.spawn_timer += dt
        if self.spawn_timer >= self.spawn_rate:
            self.spawn_timer = 0
            self._spawn_card()

        # Pre-compute loop invariants
        gravity_dt = self.gravity * dt
        bounce_damp = self.bounce_damping
        bottom = GRID_SIZE - CARD_H
        right_edge = GRID_SIZE - CARD_W

        # Update cards
        for card in self.cards:
            # Save position for trail (deque auto-evicts oldest)
            card.trail.append((int(card.x), int(card.y)))

            # Apply gravity
            card.vy += gravity_dt

            # Move
            card.x += card.vx * dt
            card.y += card.vy * dt

            # Bounce off bottom
            if card.y >= bottom:
                card.y = bottom
                card.vy = -card.vy * bounce_damp
                card.bounces += 1

                # Kill card after too many bounces or too slow
                if card.bounces > 10 or abs(card.vy) < 1:
                    card.alive = False

            # Bounce off sides
            if card.x <= 0:
                card.x = 0
                card.vx = abs(card.vx) * 0.9
            elif card.x >= right_edge:
                card.x = right_edge
                card.vx = -abs(card.vx) * 0.9

            # Kill if off screen bottom (shouldn't happen with bouncing)
            if card.y > GRID_SIZE + 20:
                card.alive = False

        # Remove dead cards
        self.cards = [c for c in self.cards if c.alive]

        # Keep a minimum number of cards (full deck)
        while len(self.cards) < 52:
            self._spawn_card()

    def draw(self):
        buf = self.display.buffer

        # Fast clear — slice-assign pre-computed background row
        for row in buf:
            row[:] = _BG_ROW

        # Draw all cards with rainbow trails (oldest first so newest on top)
        for card in self.cards:
            trail = card.trail
            trail_len = len(trail)

            if trail_len > 0:
                # Pre-compute per-trail scaling factors
                hue_base = card.hue_offset
                hue_scale = 0.5 / max(1, trail_len)
                alpha_scale = 0.8 / trail_len

                for i, (tx, ty) in enumerate(trail):
                    # Rainbow color from LUT
                    hue_idx = int((hue_base + i * hue_scale) * _RAINBOW_SIZE) % _RAINBOW_SIZE
                    r, g, b = _RAINBOW_LUT[hue_idx]
                    alpha = (i + 1) * alpha_scale
                    color = (int(r * alpha), int(g * alpha), int(b * alpha))

                    # Fill card-sized rect directly into buffer (clamped bounds)
                    x0 = max(0, tx)
                    y0 = max(0, ty)
                    x1 = min(GRID_SIZE, tx + CARD_W)
                    y1 = min(GRID_SIZE, ty + CARD_H)
                    if x0 < x1 and y0 < y1:
                        fill = [color] * (x1 - x0)
                        for sy in range(y0, y1):
                            buf[sy][x0:x1] = fill

            # Draw current card face directly into buffer
            ix, iy = int(card.x), int(card.y)
            x0 = max(0, ix)
            y0 = max(0, iy)
            x1 = min(GRID_SIZE, ix + CARD_W)
            y1 = min(GRID_SIZE, iy + CARD_H)
            if x0 < x1 and y0 < y1:
                suit_color = card.color
                for sy in range(y0, y1):
                    dy = sy - iy
                    row = buf[sy]
                    is_border_y = (dy == 0 or dy == CARD_H - 1)
                    is_pip_y = (6 <= dy <= 9)
                    for sx in range(x0, x1):
                        dx = sx - ix
                        if is_border_y or dx == 0 or dx == CARD_W - 1:
                            row[sx] = _BORDER_COLOR
                        elif is_pip_y and 4 <= dx <= 7:
                            row[sx] = suit_color
                        else:
                            row[sx] = _FACE_COLOR

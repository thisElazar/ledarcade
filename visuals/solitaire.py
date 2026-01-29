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
from . import Visual, Display, Colors, GRID_SIZE


# Card colors (suits)
CARD_COLORS = [
    (255, 50, 50),    # Hearts - red
    (255, 50, 50),    # Diamonds - red
    (40, 40, 40),     # Spades - black
    (40, 40, 40),     # Clubs - black
]

# Card back color
CARD_BACK = (30, 60, 180)  # Blue


class Card:
    """A single bouncing card."""
    def __init__(self, x, color):
        self.x = x
        self.y = 0
        self.vx = random.uniform(-20, 20)
        self.vy = 0
        self.color = color
        self.trail = []  # List of (x, y) positions for trail
        self.max_trail = 20
        self.alive = True
        self.bounces = 0
        self.hue_offset = random.random()  # For rainbow variation


class Solitaire(Visual):
    name = "SOLITAIRE"
    description = "Card cascade"
    category = "household"

    CARD_W = 6
    CARD_H = 8

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.spawn_timer = 0.0
        self.spawn_rate = 0.15  # Seconds between card spawns
        self.cards = []
        self.gravity = 120  # Pixels per second squared
        self.bounce_damping = 0.75

        # Spawn a bunch of cards to start
        for _ in range(52):
            self._spawn_card()

    def _spawn_card(self):
        """Spawn a new card at top of screen."""
        x = random.uniform(self.CARD_W, GRID_SIZE - self.CARD_W * 2)
        color = random.choice(CARD_COLORS)
        card = Card(x, color)
        card.vy = random.uniform(3, 50)  # Initial downward velocity
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

        # Update cards
        for card in self.cards:
            # Save position for trail
            card.trail.append((int(card.x), int(card.y)))
            if len(card.trail) > card.max_trail:
                card.trail.pop(0)

            # Apply gravity
            card.vy += self.gravity * dt

            # Move
            card.x += card.vx * dt
            card.y += card.vy * dt

            # Bounce off bottom
            if card.y >= GRID_SIZE - self.CARD_H:
                card.y = GRID_SIZE - self.CARD_H
                card.vy = -card.vy * self.bounce_damping
                card.bounces += 1

                # Kill card after too many bounces or too slow
                if card.bounces > 10 or abs(card.vy) < 1:
                    card.alive = False

            # Bounce off sides
            if card.x <= 0:
                card.x = 0
                card.vx = abs(card.vx) * 0.9
            elif card.x >= GRID_SIZE - self.CARD_W:
                card.x = GRID_SIZE - self.CARD_W
                card.vx = -abs(card.vx) * 0.9

            # Kill if off screen bottom (shouldn't happen with bouncing)
            if card.y > GRID_SIZE + 20:
                card.alive = False

        # Remove dead cards
        self.cards = [c for c in self.cards if c.alive]

        # Keep a minimum number of cards
        while len(self.cards) < 52:
            self._spawn_card()

    def _draw_card(self, x, y, color, alpha=1.0):
        """Draw a single card at position."""
        ix, iy = int(x), int(y)

        for py in range(self.CARD_H):
            for px in range(self.CARD_W):
                screen_x = ix + px
                screen_y = iy + py

                if 0 <= screen_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                    # Card face: white with colored pip in center
                    if px == 0 or px == self.CARD_W - 1 or py == 0 or py == self.CARD_H - 1:
                        # Border
                        r = int(200 * alpha)
                        g = int(200 * alpha)
                        b = int(200 * alpha)
                    elif 2 <= px <= 3 and 3 <= py <= 4:
                        # Suit pip in center
                        r = int(color[0] * alpha)
                        g = int(color[1] * alpha)
                        b = int(color[2] * alpha)
                    else:
                        # White face
                        r = int(255 * alpha)
                        g = int(255 * alpha)
                        b = int(255 * alpha)

                    self.display.set_pixel(screen_x, screen_y, (r, g, b))

    def _hue_to_rgb(self, h):
        """Convert hue (0-1) to RGB."""
        h = h % 1.0
        h6 = h * 6.0
        i = int(h6)
        f = h6 - i

        if i == 0:
            return (255, int(255 * f), 0)
        elif i == 1:
            return (int(255 * (1 - f)), 255, 0)
        elif i == 2:
            return (0, 255, int(255 * f))
        elif i == 3:
            return (0, int(255 * (1 - f)), 255)
        elif i == 4:
            return (int(255 * f), 0, 255)
        else:
            return (255, 0, int(255 * (1 - f)))

    def _draw_trail_segment(self, x, y, color, alpha):
        """Draw a trail segment (just a filled rectangle)."""
        ix, iy = int(x), int(y)

        for py in range(self.CARD_H):
            for px in range(self.CARD_W):
                screen_x = ix + px
                screen_y = iy + py

                if 0 <= screen_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                    r = int(color[0] * alpha)
                    g = int(color[1] * alpha)
                    b = int(color[2] * alpha)
                    self.display.set_pixel(screen_x, screen_y, (r, g, b))

    def draw(self):
        # Dark green background (like felt table)
        self.display.clear((0, 50, 20))

        # Draw cards with rainbow trails (oldest first so newest on top)
        for card in self.cards:
            # Draw rainbow trail
            trail_len = len(card.trail)
            for i, (tx, ty) in enumerate(card.trail):
                # Rainbow hue cycles through trail
                hue = card.hue_offset + (i / max(1, trail_len)) * 0.5
                color = self._hue_to_rgb(hue)
                alpha = (i + 1) / trail_len * 0.8
                self._draw_trail_segment(tx, ty, color, alpha)

            # Draw current card on top
            self._draw_card(card.x, card.y, card.color, 1.0)

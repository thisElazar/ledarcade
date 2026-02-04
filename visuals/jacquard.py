"""
Jacquard Loom Punch Card
========================
The Jacquard loom (1804) used punch cards to control the weaving of complex patterns.
Each card row controlled which warp threads were raised. Cards were chained together
in a continuous loop. This is the direct ancestor of computer programming - Babbage
saw this mechanism and it inspired the Analytical Engine. Ada Lovelace made the
connection explicit.

This visual focuses on the card-reading mechanism:
- Chain of punch cards feeding through the reader
- Visible holes in the cards (pattern of punched/unpunched positions)
- Needle array that passes through holes or is blocked
- Hook mechanism that raises/lowers based on needle position
- Cards advance one row at a time

Controls:
  Left/Right - Adjust speed (6 levels)
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


# --- Color Palette (industrial) ---

# Punch card (aged paper/cardboard)
CARD_COLOR = (240, 230, 200)
CARD_SHADOW = (200, 190, 160)
CARD_EDGE = (180, 170, 140)

# Punched holes (reveal darkness behind)
HOLE_COLOR = (30, 25, 20)

# Dark iron (mechanism frame)
DARK_IRON = (70, 70, 80)
DARK_IRON_LIGHT = (90, 90, 100)
DARK_IRON_DARK = (50, 50, 60)

# Brass (needles, accents)
BRASS = (180, 150, 50)
BRASS_DIM = (140, 115, 35)
BRASS_BRIGHT = (210, 175, 70)

# Steel (hooks, springs)
STEEL = (160, 160, 170)
STEEL_LIGHT = (180, 180, 190)
STEEL_DARK = (120, 120, 130)

# Copper (wire, connecting rods)
COPPER = (180, 110, 50)
COPPER_DIM = (140, 85, 40)

# HUD
HUD_COLOR = (160, 160, 170)

# Binary indicator colors
BIT_ON = (100, 200, 100)   # Hole = 1 = through
BIT_OFF = (200, 100, 100)  # Solid = 0 = blocked


# --- Layout Constants ---

# Card dimensions
CARD_WIDTH = 40           # Width of visible card area
CARD_HEIGHT = 12          # Height of one card
CARD_LEFT = 12            # X position of card left edge
CARD_RIGHT = CARD_LEFT + CARD_WIDTH

# Hole grid on card
HOLES_PER_ROW = 8         # Number of hole positions per row
HOLE_SPACING = 4          # Pixels between hole centers
HOLE_SIZE = 2             # Hole width/height
FIRST_HOLE_X = CARD_LEFT + 6  # X of first hole center
ROWS_PER_CARD = 3         # Visible rows per card

# Reader mechanism
READER_Y = 32             # Y position of the reading head
READER_HEIGHT = 8         # Height of reader slot

# Needle array
NEEDLE_Y_TOP = READER_Y - 4
NEEDLE_Y_BOT = READER_Y + READER_HEIGHT + 4
NEEDLE_LENGTH = 16

# Hook array (right side)
HOOK_LEFT = CARD_RIGHT + 4
HOOK_WIDTH = 8
HOOK_Y = READER_Y

# Speed levels (rows per second)
SPEED_RPS = [0.5, 1.0, 2.0, 3.0, 5.0, 8.0]


class Jacquard(Visual):
    name = "JACQUARD"
    description = "Punch card loom"
    category = "mechanics"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_level = 3  # 1-6

        # Card chain - list of cards, each card is list of rows
        # Each row is a list of booleans (True = hole, False = solid)
        self.cards = []
        self._generate_cards(6)  # Generate initial cards

        # Scroll position (in pixels)
        self.scroll_y = 0.0
        self.row_height = 4  # Pixels per row

        # Current row being read (for needle/hook animation)
        self.current_row_idx = 0
        self.current_row_data = self.cards[0][0] if self.cards else [False] * HOLES_PER_ROW

        # Animation phases
        self.read_phase = 0.0  # 0-1 for needle probe animation
        self.advancing = False  # True when card is advancing

        # Row counter
        self.rows_read = 0

    def _generate_cards(self, count):
        """Generate punch cards with semi-random patterns."""
        for _ in range(count):
            card = []
            for row_idx in range(ROWS_PER_CARD):
                # Generate pattern - mix of random and structured
                row = []
                pattern_type = random.randint(0, 3)

                if pattern_type == 0:
                    # Random
                    row = [random.random() < 0.4 for _ in range(HOLES_PER_ROW)]
                elif pattern_type == 1:
                    # Alternating
                    base = random.randint(0, 1)
                    row = [(i + base) % 2 == 0 for i in range(HOLES_PER_ROW)]
                elif pattern_type == 2:
                    # Symmetric
                    half = [random.random() < 0.5 for _ in range(HOLES_PER_ROW // 2)]
                    row = half + half[::-1]
                else:
                    # Sparse
                    row = [False] * HOLES_PER_ROW
                    for _ in range(random.randint(1, 3)):
                        row[random.randint(0, HOLES_PER_ROW - 1)] = True

                card.append(row)
            self.cards.append(card)

    def handle_input(self, input_state):
        consumed = False
        if input_state.right_pressed:
            self.speed_level = min(6, self.speed_level + 1)
            consumed = True
        elif input_state.left_pressed:
            self.speed_level = max(1, self.speed_level - 1)
            consumed = True
        return consumed

    def update(self, dt):
        self.time += dt

        # Get current speed
        rps = SPEED_RPS[self.speed_level - 1]
        row_duration = 1.0 / rps

        # Update read phase
        self.read_phase += dt / row_duration

        if self.read_phase >= 1.0:
            self.read_phase = 0.0
            self.rows_read += 1

            # Advance to next row
            total_rows = sum(len(card) for card in self.cards)
            self.current_row_idx = (self.current_row_idx + 1) % total_rows

            # Find which card and row we're on
            row_count = 0
            for card in self.cards:
                if row_count + len(card) > self.current_row_idx:
                    local_row = self.current_row_idx - row_count
                    self.current_row_data = card[local_row]
                    break
                row_count += len(card)

            # Generate new card if needed (keep buffer)
            if self.current_row_idx > len(self.cards) * ROWS_PER_CARD // 2:
                self._generate_cards(1)
                # Remove old cards to prevent memory growth
                if len(self.cards) > 10:
                    self.cards.pop(0)
                    self.current_row_idx -= ROWS_PER_CARD

        # Scroll position (smooth)
        total_row_offset = self.current_row_idx + self.read_phase
        self.scroll_y = total_row_offset * self.row_height

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)

        # Draw order: back to front
        self._draw_frame(d)
        self._draw_cards(d)
        self._draw_reader_mechanism(d)
        self._draw_needles(d)
        self._draw_hooks(d)
        self._draw_binary_display(d)
        self._draw_hud(d)

    def _draw_frame(self, d):
        """Draw the mechanism frame."""
        # Main frame outline
        d.draw_rect(CARD_LEFT - 4, 8, CARD_WIDTH + 8, 48, DARK_IRON)

        # Frame border highlights
        d.draw_line(CARD_LEFT - 4, 8, CARD_RIGHT + 3, 8, DARK_IRON_LIGHT)
        d.draw_line(CARD_LEFT - 4, 8, CARD_LEFT - 4, 55, DARK_IRON_LIGHT)
        d.draw_line(CARD_RIGHT + 3, 8, CARD_RIGHT + 3, 55, DARK_IRON_DARK)
        d.draw_line(CARD_LEFT - 4, 55, CARD_RIGHT + 3, 55, DARK_IRON_DARK)

        # Reader slot frame (darker area where cards pass through)
        d.draw_rect(CARD_LEFT - 2, READER_Y - 1, CARD_WIDTH + 4, READER_HEIGHT + 2, DARK_IRON_DARK)

        # Brass rivets on frame
        for y in [12, 28, 44]:
            d.set_pixel(CARD_LEFT - 3, y, BRASS)
            d.set_pixel(CARD_RIGHT + 2, y, BRASS)

    def _draw_cards(self, d):
        """Draw the chain of punch cards scrolling through."""
        # Calculate visible card range
        base_y = 10  # Top of card display area
        visible_height = 44

        # Draw cards from top to bottom
        y_offset = -(self.scroll_y % (CARD_HEIGHT + 2))

        card_y = base_y + int(y_offset)
        card_idx = int(self.scroll_y // (CARD_HEIGHT + 2)) % len(self.cards)

        while card_y < base_y + visible_height + CARD_HEIGHT:
            if card_y + CARD_HEIGHT > base_y and card_y < base_y + visible_height:
                self._draw_single_card(d, card_y, self.cards[card_idx % len(self.cards)])
            card_y += CARD_HEIGHT + 2  # Card height + gap
            card_idx += 1

    def _draw_single_card(self, d, y, card_data):
        """Draw a single punch card."""
        # Card body (clipped to visible area)
        for cy in range(CARD_HEIGHT):
            draw_y = y + cy
            if 10 <= draw_y < 54:  # Clip to frame
                for cx in range(CARD_WIDTH):
                    # Card base color with slight texture
                    if (cx + cy) % 8 == 0:
                        color = CARD_SHADOW
                    else:
                        color = CARD_COLOR
                    d.set_pixel(CARD_LEFT + cx, draw_y, color)

        # Card edge (left)
        for cy in range(CARD_HEIGHT):
            draw_y = y + cy
            if 10 <= draw_y < 54:
                d.set_pixel(CARD_LEFT, draw_y, CARD_EDGE)

        # Card edge (top and bottom)
        if 10 <= y < 54:
            d.draw_line(CARD_LEFT, y, CARD_RIGHT - 1, y, CARD_EDGE)
        if 10 <= y + CARD_HEIGHT - 1 < 54:
            d.draw_line(CARD_LEFT, y + CARD_HEIGHT - 1, CARD_RIGHT - 1, y + CARD_HEIGHT - 1, CARD_EDGE)

        # Punch holes
        for row_idx, row_data in enumerate(card_data):
            hole_y = y + 2 + row_idx * self.row_height
            if 10 <= hole_y < 54 and 10 <= hole_y + HOLE_SIZE - 1 < 54:
                for hole_idx, is_punched in enumerate(row_data):
                    hole_x = FIRST_HOLE_X + hole_idx * HOLE_SPACING
                    if is_punched:
                        # Draw hole (dark rectangle)
                        for dy in range(HOLE_SIZE):
                            for dx in range(HOLE_SIZE):
                                d.set_pixel(hole_x + dx, hole_y + dy, HOLE_COLOR)

    def _draw_reader_mechanism(self, d):
        """Draw the card reader mechanism."""
        # Reader guides (brass rails)
        d.draw_line(CARD_LEFT - 1, READER_Y - 2, CARD_RIGHT, READER_Y - 2, BRASS)
        d.draw_line(CARD_LEFT - 1, READER_Y + READER_HEIGHT + 1, CARD_RIGHT, READER_Y + READER_HEIGHT + 1, BRASS)

        # Spring mechanism on left (card tensioner)
        spring_x = CARD_LEFT - 6
        for i in range(5):
            y = READER_Y + i * 2
            d.set_pixel(spring_x, y, STEEL)
            d.set_pixel(spring_x + 1, y + 1, STEEL_DARK)

    def _draw_needles(self, d):
        """Draw the needle array that probes the card."""
        # Needles extend from top, probe through card holes
        needle_probe_depth = int(4 * math.sin(self.read_phase * math.pi))

        for i, is_through in enumerate(self.current_row_data):
            nx = FIRST_HOLE_X + i * HOLE_SPACING

            # Needle body (vertical line)
            needle_top = READER_Y - 6
            needle_bot = READER_Y + needle_probe_depth

            # Draw needle
            for y in range(needle_top, needle_bot + 1):
                if is_through and y > READER_Y:
                    # Needle passes through hole
                    d.set_pixel(nx, y, BRASS_BRIGHT)
                else:
                    d.set_pixel(nx, y, BRASS)

            # Needle tip (brighter)
            d.set_pixel(nx, needle_bot, BRASS_BRIGHT)

            # Needle blocked indicator (when hitting solid card)
            if not is_through and needle_probe_depth > 1:
                # Show small "blocked" mark
                d.set_pixel(nx, READER_Y + 1, STEEL_LIGHT)

    def _draw_hooks(self, d):
        """Draw the hook mechanism that responds to needle positions."""
        # Hooks are lifted when needles pass through (hole = 1)
        hook_lift_amount = int(3 * math.sin(self.read_phase * math.pi))

        for i, is_lifted in enumerate(self.current_row_data):
            hx = HOOK_LEFT + 1
            hy_base = READER_Y - 2 + i * 2

            if i >= 4:
                # Second column of hooks
                hx = HOOK_LEFT + 5
                hy_base = READER_Y - 2 + (i - 4) * 2

            # Hook position
            if is_lifted:
                hy = hy_base - hook_lift_amount
                hook_color = COPPER
            else:
                hy = hy_base
                hook_color = COPPER_DIM

            # Draw hook (small L shape)
            d.set_pixel(hx, hy, hook_color)
            d.set_pixel(hx, hy + 1, hook_color)
            d.set_pixel(hx + 1, hy + 1, hook_color)

        # Hook frame
        d.draw_rect(HOOK_LEFT, READER_Y - 4, HOOK_WIDTH, 12, DARK_IRON, filled=False)
        d.draw_line(HOOK_LEFT + 4, READER_Y - 4, HOOK_LEFT + 4, READER_Y + 7, DARK_IRON_DARK)

    def _draw_binary_display(self, d):
        """Draw binary indicator showing current row as 0s and 1s."""
        # Show the binary nature - hole = 1, solid = 0
        binary_y = 58

        for i, is_hole in enumerate(self.current_row_data):
            bx = 8 + i * 6
            color = BIT_ON if is_hole else BIT_OFF

            # Draw 0 or 1
            if is_hole:
                # Draw "1"
                d.set_pixel(bx + 1, binary_y, color)
                d.set_pixel(bx, binary_y + 1, color)
                d.set_pixel(bx + 1, binary_y + 1, color)
                d.set_pixel(bx + 1, binary_y + 2, color)
                d.set_pixel(bx + 1, binary_y + 3, color)
                d.set_pixel(bx, binary_y + 4, color)
                d.set_pixel(bx + 1, binary_y + 4, color)
                d.set_pixel(bx + 2, binary_y + 4, color)
            else:
                # Draw "0"
                d.set_pixel(bx + 1, binary_y, color)
                d.set_pixel(bx, binary_y + 1, color)
                d.set_pixel(bx + 2, binary_y + 1, color)
                d.set_pixel(bx, binary_y + 2, color)
                d.set_pixel(bx + 2, binary_y + 2, color)
                d.set_pixel(bx, binary_y + 3, color)
                d.set_pixel(bx + 2, binary_y + 3, color)
                d.set_pixel(bx + 1, binary_y + 4, color)

    def _draw_hud(self, d):
        """Draw speed and row counter."""
        rps = SPEED_RPS[self.speed_level - 1]
        d.draw_text_small(2, 2, f"R:{rps:.1f}", HUD_COLOR)

        # Row counter (right side)
        d.draw_text_small(42, 2, f"{self.rows_read}", HUD_COLOR)

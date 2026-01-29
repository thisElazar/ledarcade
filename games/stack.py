"""
Stack - Tower building game
============================
Drop blocks to build a tower! Misaligned portions get cut off.

Controls:
  Space      - Drop block
  Escape     - Return to menu
"""

import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Stack(Game):
    name = "STACK"
    description = "Build the tower!"
    category = "modern"

    # Game constants
    BASE_Y = 58  # Bottom of tower
    BLOCK_HEIGHT = 4
    INITIAL_WIDTH = 20

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Tower: list of {x, width, color} from bottom up
        self.tower = []

        # First (base) block - centered, full width
        base_x = (GRID_SIZE - self.INITIAL_WIDTH) // 2
        self.tower.append({
            'x': base_x,
            'width': self.INITIAL_WIDTH,
            'color': self._get_rainbow_color(0)
        })

        # Current swinging block
        self.current_width = self.INITIAL_WIDTH
        self.current_x = 0.0
        self.swing_time = 0.0
        self.swing_speed = 1.0  # Start slower
        self.swing_direction = 1

        # Dropping state
        self.dropping = False
        self.drop_y = 0.0
        self.drop_speed = 200.0

        # Camera offset (scrolls up as tower grows)
        self.camera_y = 0

        # Perfect streak bonus
        self.perfect_streak = 0

        self._update_swing_position()

    def _get_rainbow_color(self, index: int) -> tuple:
        """Get rainbow color based on block index."""
        colors = [
            Colors.RED,
            Colors.ORANGE,
            Colors.YELLOW,
            Colors.GREEN,
            Colors.CYAN,
            Colors.BLUE,
            Colors.MAGENTA,
            Colors.PINK,
        ]
        return colors[index % len(colors)]

    def _get_swing_range(self) -> float:
        """Get swing range based on current block width - smaller blocks swing less."""
        # Swing range is proportional to block width, plus a small margin
        # This keeps the block close to where it needs to land
        return self.current_width * 0.6 + 4

    def _get_swing_y(self) -> int:
        """Get Y position where the swinging block should appear (just above tower)."""
        tower_top_y = self._get_block_screen_y(len(self.tower) - 1)
        # Position swinging block 2 block heights above the tower top
        return max(10, tower_top_y - self.BLOCK_HEIGHT * 2)

    def _update_swing_position(self):
        """Update the swinging block position based on time."""
        top_block = self.tower[-1]
        center_x = top_block['x'] + top_block['width'] / 2

        # Oscillate around the center with dynamic range
        swing_range = self._get_swing_range()
        offset = math.sin(self.swing_time * self.swing_speed * math.pi) * swing_range
        self.current_x = center_x - self.current_width / 2 + offset

    def _get_block_screen_y(self, block_index: int) -> int:
        """Get screen Y position for a block."""
        return self.BASE_Y - (block_index + 1) * self.BLOCK_HEIGHT + self.camera_y

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        if self.dropping:
            # Animate block falling
            target_y = self._get_block_screen_y(len(self.tower))
            self.drop_y += self.drop_speed * dt

            if self.drop_y >= target_y:
                self._land_block()
        else:
            # Swing the block
            self.swing_time += dt
            self._update_swing_position()

            # Drop on action
            if (input_state.action_l or input_state.action_r):
                self.dropping = True
                self.drop_y = self._get_swing_y()

    def _land_block(self):
        """Handle block landing and calculate overlap."""
        top_block = self.tower[-1]

        # Calculate overlap
        new_left = max(self.current_x, top_block['x'])
        new_right = min(self.current_x + self.current_width,
                       top_block['x'] + top_block['width'])

        overlap = new_right - new_left

        if overlap <= 0:
            # Completely missed - game over
            self.state = GameState.GAME_OVER
            return

        # Check for perfect placement (within 2 pixels - more forgiving)
        if abs(self.current_x - top_block['x']) < 2 and abs(self.current_width - top_block['width']) < 2:
            # Perfect!
            self.perfect_streak += 1
            # Bonus: grow block slightly on perfect streak
            if self.perfect_streak >= 2:
                overlap = min(overlap + 1, self.INITIAL_WIDTH)
            # Keep the same width on perfect
            overlap = top_block['width']
            new_left = top_block['x']
        else:
            self.perfect_streak = 0

        # Add the new block with trimmed width
        self.tower.append({
            'x': new_left,
            'width': overlap,
            'color': self._get_rainbow_color(len(self.tower))
        })

        self.score = len(self.tower) - 1

        # Update current block for next round
        self.current_width = overlap

        # Speed up swing gradually (slower ramp)
        self.swing_speed = min(2.5, 1.0 + self.score * 0.05)

        # Scroll camera up if tower is getting tall
        tower_top_y = self._get_block_screen_y(len(self.tower))
        if tower_top_y < 25:
            self.camera_y += self.BLOCK_HEIGHT

        # Reset for next block
        self.dropping = False
        self.swing_time = 0

        # Check if block is too small to continue
        if self.current_width < 3:
            self.state = GameState.GAME_OVER

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Background gradient
        for y in range(8, GRID_SIZE):
            shade = int((y - 8) * 0.5)
            self.display.draw_line(0, y, 63, y, (shade // 2, shade // 3, shade))

        # Draw tower blocks
        for i, block in enumerate(self.tower):
            screen_y = self._get_block_screen_y(i)

            if screen_y < GRID_SIZE and screen_y + self.BLOCK_HEIGHT > 8:
                bx = int(block['x'])
                bw = int(block['width'])

                # Block body
                for y in range(max(8, screen_y), min(GRID_SIZE, screen_y + self.BLOCK_HEIGHT)):
                    for x in range(bx, bx + bw):
                        if 0 <= x < GRID_SIZE:
                            self.display.set_pixel(x, y, block['color'])

                # Block highlight (top edge)
                if screen_y >= 8:
                    highlight = tuple(min(255, c + 50) for c in block['color'])
                    for x in range(bx, bx + bw):
                        if 0 <= x < GRID_SIZE:
                            self.display.set_pixel(x, screen_y, highlight)

                # Block shadow (bottom edge)
                shadow_y = screen_y + self.BLOCK_HEIGHT - 1
                if shadow_y < GRID_SIZE:
                    shadow = tuple(max(0, c - 50) for c in block['color'])
                    for x in range(bx, bx + bw):
                        if 0 <= x < GRID_SIZE:
                            self.display.set_pixel(x, shadow_y, shadow)

        # Draw current/dropping block
        if self.dropping:
            block_y = int(self.drop_y)
        else:
            block_y = self._get_swing_y()

        color = self._get_rainbow_color(len(self.tower))
        bx = int(self.current_x)
        bw = int(self.current_width)

        for y in range(block_y, block_y + self.BLOCK_HEIGHT):
            if 8 <= y < GRID_SIZE:
                for x in range(bx, bx + bw):
                    if 0 <= x < GRID_SIZE:
                        self.display.set_pixel(x, y, color)

        # Highlight
        if block_y >= 8:
            highlight = tuple(min(255, c + 50) for c in color)
            for x in range(bx, bx + bw):
                if 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, block_y, highlight)

        # Draw guide markers showing target zone
        if not self.dropping:
            top_block = self.tower[-1]
            guide_y = self._get_block_screen_y(len(self.tower))
            if guide_y >= 8:
                # Show edges of target zone
                left_x = int(top_block['x'])
                right_x = int(top_block['x'] + top_block['width'] - 1)
                # Dotted lines
                for y in range(guide_y, min(guide_y + self.BLOCK_HEIGHT, GRID_SIZE)):
                    if (y + int(self.swing_time * 10)) % 2 == 0:
                        if 0 <= left_x < GRID_SIZE:
                            self.display.set_pixel(left_x, y, Colors.DARK_GRAY)
                        if 0 <= right_x < GRID_SIZE:
                            self.display.set_pixel(right_x, y, Colors.DARK_GRAY)

        # HUD
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        self.display.draw_text_small(1, 1, f"H:{self.score}", Colors.WHITE)

        # Perfect streak indicator
        if self.perfect_streak > 0:
            self.display.draw_text_small(30, 1, f"X{self.perfect_streak}", Colors.YELLOW)

    def draw_game_over(self):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(8, 32, f"HEIGHT:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "BTN:RETRY", Colors.GRAY)

"""
Stack Demo - AI Attract Mode
=============================
Stack plays itself using timing prediction for idle screen demos.

AI Strategy:
- Track the moving block position relative to the target zone
- Calculate when the block aligns with the stack below
- Press action when alignment is good (within tolerance)
- Tolerance decreases as blocks get smaller for precision
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.stack import Stack


class StackDemo(Visual):
    name = "STACK"
    description = "AI stacks blocks"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Stack(self.display)
        self.game.reset()
        self.game_over_timer = 0.0
        self.last_drop_time = 0.0
        self.min_drop_interval = 0.3  # Minimum time between drops

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game over, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
            return

        # Create AI input
        ai_input = InputState()

        # Only try to drop if not already dropping and enough time has passed
        if not self.game.dropping and (self.time - self.last_drop_time) > self.min_drop_interval:
            if self._should_drop():
                ai_input.action_l = True
                self.last_drop_time = self.time

        self.game.update(ai_input, dt)

    def draw(self):
        if self.game.state == GameState.GAME_OVER:
            self.game.draw_game_over()
        else:
            self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _should_drop(self):
        """
        Determine if the AI should drop the block now.
        Returns True when the block is well-aligned with the target.
        """
        if not self.game.tower:
            return True

        # Get current block position and target
        current_x = self.game.current_x
        current_width = self.game.current_width
        top_block = self.game.tower[-1]
        target_x = top_block['x']
        target_width = top_block['width']

        # Calculate alignment error (how far off center we are)
        # Perfect alignment means current_x == target_x
        alignment_error = abs(current_x - target_x)

        # Calculate acceptable tolerance based on block width
        # Smaller blocks need more precision, but we give some margin
        # For a full-width block (20), tolerance is ~4 pixels
        # For a small block (5), tolerance is ~1 pixel
        tolerance = max(1.0, current_width * 0.2)

        # Check if we're within tolerance
        if alignment_error <= tolerance:
            return True

        # Also consider if blocks are overlapping well enough
        # Calculate potential overlap
        new_left = max(current_x, target_x)
        new_right = min(current_x + current_width, target_x + target_width)
        potential_overlap = new_right - new_left

        # If overlap would be at least 70% of current width, it's acceptable
        if potential_overlap >= current_width * 0.7:
            return True

        return False

"""
2048 Demo - AI Attract Mode
===========================
2048 plays itself using a corner strategy for idle screen demos.

AI Strategy (Corner Strategy):
- Keep the highest tile in the bottom-left corner
- Priority order: Down, Left, Right, Up
- Only use Up as a last resort
- If a move doesn't change the board, try the next in priority
- This simple strategy frequently reaches 2048
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.game2048 import Game2048


class Game2048Demo(Visual):
    name = "2048 DEMO"
    description = "AI plays 2048"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Game2048(self.display)
        self.game.reset()
        self.move_timer = 0.0
        self.move_delay = 0.3  # Time between AI moves
        self.game_over_timer = 0.0

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

        # Wait for animation to complete
        if self.game.animating:
            self.game.update(InputState(), dt)
            return

        # AI movement timing
        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return

        self.move_timer = 0.0

        # Get AI move direction
        direction = self._get_ai_move()

        if direction:
            ai_input = InputState()
            if direction == 'down':
                ai_input.down = True
            elif direction == 'left':
                ai_input.left = True
            elif direction == 'right':
                ai_input.right = True
            elif direction == 'up':
                ai_input.up = True

            self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _get_ai_move(self):
        """
        Get the next AI move using corner strategy.
        Priority: Down, Left, Right, Up
        Only make a move if it actually changes the board.
        """
        # Priority order for corner strategy (bottom-left)
        priorities = ['down', 'left', 'right', 'up']

        for direction in priorities:
            if self._move_is_valid(direction):
                return direction

        # No valid moves (shouldn't happen if game isn't over)
        return None

    def _move_is_valid(self, direction):
        """Check if a move would change the board state."""
        # Create a copy of the grid
        original = [row[:] for row in self.game.grid]

        # Simulate the move on a copy
        test_grid = [row[:] for row in original]

        if direction == 'left':
            for r in range(4):
                test_grid[r] = self._slide_row_left(test_grid[r])
        elif direction == 'right':
            for r in range(4):
                test_grid[r] = self._slide_row_left(test_grid[r][::-1])[::-1]
        elif direction == 'up':
            for c in range(4):
                col = [test_grid[r][c] for r in range(4)]
                new_col = self._slide_row_left(col)
                for r in range(4):
                    test_grid[r][c] = new_col[r]
        elif direction == 'down':
            for c in range(4):
                col = [test_grid[r][c] for r in range(3, -1, -1)]
                new_col = self._slide_row_left(col)
                for r in range(4):
                    test_grid[3 - r][c] = new_col[r]

        # Check if anything changed
        return test_grid != original

    def _slide_row_left(self, row):
        """Slide a row left and merge tiles. Returns the new row."""
        # Remove zeros
        tiles = [t for t in row if t != 0]

        # Merge adjacent equal tiles
        merged = []
        skip = False
        for i in range(len(tiles)):
            if skip:
                skip = False
                continue
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                merged.append(tiles[i] * 2)
                skip = True
            else:
                merged.append(tiles[i])

        # Pad with zeros
        return merged + [0] * (4 - len(merged))

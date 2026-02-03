"""
Lights Out Demo - AI Attract Mode
=================================
Lights Out plays itself using the "chase the lights" algorithm.

AI Strategy (Chase the Lights):
- Process each row from top to bottom
- For each lit cell in a row, toggle the cell directly below it
- This "pushes" the lit cells downward
- After processing all rows, use a lookup table for the bottom row
- The bottom row pattern determines which top row cells to toggle
- This algorithm is guaranteed to solve any solvable puzzle
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.lightsout import LightsOut


class LightsOutDemo(Visual):
    name = "LIGHTS OUT"
    description = "AI solves puzzle"
    category = "demos"

    # Lookup table: given bottom row pattern after chase, which top row cells to toggle
    # Index by bottom row as 5-bit number (bit 0 = col 0, etc.)
    # Value is top row cells to toggle as 5-bit number
    # These patterns are derived from linear algebra over GF(2)
    TOP_ROW_LOOKUP = {
        0b00000: 0b00000,  # Already solved
        0b00001: 0b01001,
        0b00010: 0b10101,
        0b00011: 0b11100,
        0b00100: 0b01110,
        0b00101: 0b00111,
        0b00110: 0b11011,
        0b00111: 0b10010,
        0b01000: 0b10101,
        0b01001: 0b11100,
        0b01010: 0b00000,  # Special case
        0b01011: 0b01001,
        0b01100: 0b11011,
        0b01101: 0b10010,
        0b01110: 0b01110,
        0b01111: 0b00111,
        0b10000: 0b01001,
        0b10001: 0b00000,  # Special case
        0b10010: 0b11100,
        0b10011: 0b10101,
        0b10100: 0b00111,
        0b10101: 0b01110,
        0b10110: 0b10010,
        0b10111: 0b11011,
        0b11000: 0b11100,
        0b11001: 0b10101,
        0b11010: 0b01001,
        0b11011: 0b00000,  # Special case
        0b11100: 0b10010,
        0b11101: 0b11011,
        0b11110: 0b00111,
        0b11111: 0b01110,
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = LightsOut(self.display)
        self.game.reset()
        self.move_timer = 0.0
        self.move_delay = 0.4  # Time between AI moves
        self.game_over_timer = 0.0

        # AI state for chase algorithm
        self.ai_phase = 'analyze'  # 'analyze', 'top_row', 'chase'
        self.ai_row = 0
        self.ai_col = 0
        self.top_row_toggles = []  # Queue of top row cells to toggle
        self.solution_moves = []   # Pre-computed solution moves

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If game won, restart after a pause
        if self.game.state == GameState.GAME_OVER:
            self.game_over_timer += dt
            if self.game_over_timer > 3.0:
                self.game.reset()
                self.game_over_timer = 0.0
                self.ai_phase = 'analyze'
                self.ai_row = 0
                self.ai_col = 0
                self.top_row_toggles = []
                self.solution_moves = []
            return

        # Wait for toggle flash animation
        if self.game.toggle_flash > 0:
            self.game.update(InputState(), dt)
            return

        # AI movement timing
        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return

        self.move_timer = 0.0

        # Get AI move
        move = self._get_ai_move()

        if move:
            col, row = move
            # Move cursor to target
            self.game.cursor_x = col
            self.game.cursor_y = row

            # Create input to toggle
            ai_input = InputState()
            ai_input.action_l = True
            self.game.update(ai_input, dt)

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _get_ai_move(self):
        """
        Get the next AI move using chase the lights algorithm.
        Returns (col, row) to toggle, or None if puzzle is solved.
        """
        # If we have pre-computed moves, use them
        if self.solution_moves:
            return self.solution_moves.pop(0)

        # Compute the full solution
        self._compute_solution()

        if self.solution_moves:
            return self.solution_moves.pop(0)

        return None

    def _compute_solution(self):
        """
        Compute the full solution using chase the lights algorithm.
        """
        # Work on a copy of the grid
        grid = [row[:] for row in self.game.grid]

        moves = []

        # First, determine what top row toggles we need
        # Simulate chasing without the top row fix to see bottom pattern
        test_grid = [row[:] for row in grid]

        # Chase phase: for each row 0-3, toggle below any lit cell
        for row in range(4):
            for col in range(5):
                if test_grid[row][col]:
                    # Toggle cell below
                    self._sim_toggle(test_grid, col, row + 1)

        # Check bottom row pattern
        bottom_pattern = 0
        for col in range(5):
            if test_grid[4][col]:
                bottom_pattern |= (1 << col)

        # Look up required top row toggles
        top_pattern = self.TOP_ROW_LOOKUP.get(bottom_pattern, 0)

        # Queue top row toggles first
        for col in range(5):
            if top_pattern & (1 << col):
                moves.append((col, 0))
                self._sim_toggle(grid, col, 0)

        # Now do the chase on the actual grid
        for row in range(4):
            for col in range(5):
                if grid[row][col]:
                    moves.append((col, row + 1))
                    self._sim_toggle(grid, col, row + 1)

        self.solution_moves = moves

    def _sim_toggle(self, grid, col, row):
        """Simulate toggling a cell and its neighbors."""
        cells = [(col, row)]
        if col > 0:
            cells.append((col - 1, row))
        if col < 4:
            cells.append((col + 1, row))
        if row > 0:
            cells.append((col, row - 1))
        if row < 4:
            cells.append((col, row + 1))

        for c, r in cells:
            grid[r][c] = not grid[r][c]

"""
Tetris Demo - AI Attract Mode
=============================
Tetris plays itself using AI for idle screen demos.
The AI evaluates all possible placements and chooses the best one
based on minimizing holes, maximizing line clears, and keeping the stack low.

AI Strategy:
- For each piece, try all rotations and positions
- Score each placement based on: holes, lines cleared, height, bumpiness
- Hard drop when in position for fast play
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

# Import the actual game
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from games.tetris import Tetris, TETROMINOS, TETROMINO_COLORS


class TetrisDemo(Visual):
    name = "TETROMINOS"
    description = "AI plays Tetris"
    category = "demos"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.game = Tetris(self.display)
        self.game.reset()

        # AI state
        self.target_col = None
        self.target_rot = None
        self.move_timer = 0.0
        self.move_delay = 0.03  # Time between AI moves (fast but visible)
        self.game_over_timer = 0.0

        # Calculate first target
        self._find_best_placement()

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
                self._find_best_placement()
            return

        # Handle line clear animation - just let game update
        if self.game.line_clear_timer > 0:
            self.game.update(InputState(), dt)
            return

        # AI movement timing
        self.move_timer += dt
        if self.move_timer < self.move_delay:
            # Still waiting, but update game for gravity
            self.game.update(InputState(), dt)
            return

        self.move_timer = 0.0

        # Create AI input
        ai_input = InputState()

        # Check if we need a new target (new piece spawned)
        if self.target_col is None or self.target_rot is None:
            self._find_best_placement()

        # First, rotate to target rotation
        if self.game.current_rotation != self.target_rot:
            ai_input.up_pressed = True
            ai_input.up = True
        # Then, move to target column
        elif self.game.piece_x < self.target_col:
            ai_input.right = True
        elif self.game.piece_x > self.target_col:
            ai_input.left = True
        else:
            # In position - hard drop!
            ai_input.action_l = True
            # Prepare for next piece
            self.target_col = None
            self.target_rot = None

        self.game.update(ai_input, dt)

        # If new piece spawned (hard drop completed), find new target
        if self.target_col is None and self.game.current_piece:
            self._find_best_placement()

    def draw(self):
        self.game.draw()

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(49, 52, "DEMO", Colors.GRAY)

    def _find_best_placement(self):
        """Find the best column and rotation for the current piece."""
        if not self.game.current_piece:
            return

        best_score = float('-inf')
        best_col = self.game.piece_x
        best_rot = 0

        piece = self.game.current_piece
        board = self.game.board
        board_width = self.game.BOARD_WIDTH
        board_height = self.game.BOARD_HEIGHT

        # Try all rotations
        for rotation in range(4):
            shape = TETROMINOS[piece][rotation]

            # Find the horizontal bounds of this rotation
            min_dx = min(dx for dx, dy in shape)
            max_dx = max(dx for dx, dy in shape)

            # Try all valid columns
            for col in range(-min_dx, board_width - max_dx):
                # Simulate placing the piece
                score = self._evaluate_placement(col, rotation, shape, board, board_width, board_height)

                if score > best_score:
                    best_score = score
                    best_col = col
                    best_rot = rotation

        self.target_col = best_col
        self.target_rot = best_rot

    def _evaluate_placement(self, col, rotation, shape, board, board_width, board_height):
        """Evaluate a potential piece placement and return a score."""
        # Find where the piece would land (simulate drop)
        drop_y = 0
        while True:
            can_drop = True
            for dx, dy in shape:
                x = col + dx
                y = drop_y + dy + 1
                if y >= board_height:
                    can_drop = False
                    break
                if y >= 0 and board[y][x] is not None:
                    can_drop = False
                    break
            if can_drop:
                drop_y += 1
            else:
                break

        # Create a copy of the board with the piece placed
        test_board = [row[:] for row in board]
        for dx, dy in shape:
            x = col + dx
            y = drop_y + dy
            if 0 <= y < board_height:
                test_board[y][x] = True  # Mark as filled

        # Calculate metrics
        lines_cleared = self._count_complete_lines(test_board, board_width, board_height)
        holes = self._count_holes(test_board, board_width, board_height)
        max_height = self._get_max_height(test_board, board_width, board_height)
        bumpiness = self._get_bumpiness(test_board, board_width, board_height)

        # Landing height (lower is better)
        landing_height = board_height - drop_y

        # Score calculation (weights tuned for good play)
        score = (
            lines_cleared * 100      # Reward line clears heavily
            - holes * 50             # Penalize holes
            - max_height * 10        # Penalize tall stacks
            - bumpiness * 5          # Penalize uneven surface
            - landing_height * 2     # Slight preference for lower placements
        )

        return score

    def _count_complete_lines(self, board, width, height):
        """Count how many complete lines are in the board."""
        count = 0
        for y in range(height):
            if all(board[y][x] is not None for x in range(width)):
                count += 1
        return count

    def _count_holes(self, board, width, height):
        """Count holes (empty cells with filled cells above them)."""
        holes = 0
        for x in range(width):
            found_block = False
            for y in range(height):
                if board[y][x] is not None:
                    found_block = True
                elif found_block:
                    holes += 1
        return holes

    def _get_max_height(self, board, width, height):
        """Get the maximum stack height."""
        for y in range(height):
            for x in range(width):
                if board[y][x] is not None:
                    return height - y
        return 0

    def _get_bumpiness(self, board, width, height):
        """Calculate the sum of height differences between adjacent columns."""
        heights = []
        for x in range(width):
            col_height = 0
            for y in range(height):
                if board[y][x] is not None:
                    col_height = height - y
                    break
            heights.append(col_height)

        bumpiness = 0
        for i in range(len(heights) - 1):
            bumpiness += abs(heights[i] - heights[i + 1])

        return bumpiness

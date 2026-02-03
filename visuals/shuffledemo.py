"""
Shuffle Demo - AI Attract Mode
==============================
Sliding tile puzzle (15-puzzle) plays itself using AI solving strategy.
The AI solves the puzzle row by row, top to bottom, using simple heuristics.

AI Strategy:
- Solve the puzzle row by row, starting from the top
- For each position, find the tile that belongs there
- Move that tile toward its goal position
- Use a simple manhattan distance heuristic
- Special handling for the last two tiles in each row
"""

from . import Visual, Display, Colors, GRID_SIZE
from arcade import InputState, GameState

import random


class ShuffleDemo(Visual):
    name = "SHUFFLE DEMO"
    description = "AI solves puzzle"
    category = "demos"

    # Board layout
    BOARD_SIZE = 4  # 4x4 grid (15-puzzle)
    TILE_SIZE = 14  # Each tile is 14x14 pixels
    GAP = 1
    BOARD_PIXELS = TILE_SIZE * BOARD_SIZE + GAP * (BOARD_SIZE + 1)  # 60
    BOARD_X = (GRID_SIZE - BOARD_PIXELS) // 2
    BOARD_Y = (GRID_SIZE - BOARD_PIXELS) // 2 + 2

    # Colors
    TILE_COLORS = [
        (200, 80, 80),    # Red-ish
        (80, 200, 80),    # Green-ish
        (80, 80, 200),    # Blue-ish
        (200, 200, 80),   # Yellow-ish
    ]
    TILE_BG = (60, 60, 70)
    BOARD_BG = (30, 30, 40)
    TEXT_COLOR = Colors.WHITE

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.move_timer = 0.0
        self.move_delay = 0.3  # Time between AI moves
        self.win_timer = 0.0

        # Initialize solved board
        # Board is 4x4, values 1-15 with 0 representing the empty space
        # Position [row][col] contains the tile number (0 = empty)
        self.board = [[0] * 4 for _ in range(4)]
        for r in range(4):
            for c in range(4):
                self.board[r][c] = r * 4 + c + 1
        self.board[3][3] = 0  # Empty space

        # Track empty position
        self.empty_row = 3
        self.empty_col = 3

        # Shuffle the board
        self._shuffle_board()

        # Game state
        self.solved = False
        self.move_count = 0

        # AI solving state
        self.solving_phase = 'row'  # 'row', 'last_row'
        self.target_row = 0
        self.target_col = 0

    def _shuffle_board(self, moves=100):
        """Shuffle by making random valid moves (ensures solvability)."""
        for _ in range(moves):
            # Get valid moves (adjacent to empty)
            valid_moves = []
            if self.empty_row > 0:
                valid_moves.append((-1, 0))  # Move tile from above down
            if self.empty_row < 3:
                valid_moves.append((1, 0))   # Move tile from below up
            if self.empty_col > 0:
                valid_moves.append((0, -1))  # Move tile from left right
            if self.empty_col < 3:
                valid_moves.append((0, 1))   # Move tile from right left

            # Pick a random move
            dr, dc = random.choice(valid_moves)
            self._slide_tile(self.empty_row + dr, self.empty_col + dc)

    def _slide_tile(self, row, col):
        """Slide tile at (row, col) into the empty space if adjacent."""
        # Check if adjacent to empty
        if abs(row - self.empty_row) + abs(col - self.empty_col) != 1:
            return False

        # Swap
        self.board[self.empty_row][self.empty_col] = self.board[row][col]
        self.board[row][col] = 0
        self.empty_row = row
        self.empty_col = col
        return True

    def _get_goal_position(self, tile):
        """Get the goal (row, col) for a tile number."""
        if tile == 0:
            return (3, 3)
        return ((tile - 1) // 4, (tile - 1) % 4)

    def _find_tile(self, tile):
        """Find current position of a tile."""
        for r in range(4):
            for c in range(4):
                if self.board[r][c] == tile:
                    return (r, c)
        return None

    def _is_solved(self):
        """Check if puzzle is solved."""
        for r in range(4):
            for c in range(4):
                expected = r * 4 + c + 1 if (r, c) != (3, 3) else 0
                if self.board[r][c] != expected:
                    return False
        return True

    def _get_movable_tiles(self):
        """Get list of tiles that can move (adjacent to empty)."""
        movable = []
        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            r, c = self.empty_row + dr, self.empty_col + dc
            if 0 <= r < 4 and 0 <= c < 4:
                movable.append((r, c))
        return movable

    def handle_input(self, input_state):
        # Demo doesn't respond to input (auto-plays)
        return False

    def update(self, dt):
        self.time += dt

        # If solved, restart after a pause
        if self.solved:
            self.win_timer += dt
            if self.win_timer > 3.0:
                self.reset()
            return

        # AI movement timing
        self.move_timer += dt
        if self.move_timer < self.move_delay:
            return

        self.move_timer = 0.0

        # Make AI move
        move = self._get_ai_move()
        if move:
            self._slide_tile(move[0], move[1])
            self.move_count += 1

        # Check for win
        if self._is_solved():
            self.solved = True
            self.win_timer = 0.0

    def _get_ai_move(self):
        """
        Get the next AI move using row-by-row solving strategy.
        Returns (row, col) of tile to move, or None.
        """
        # Find the first unsolved position
        target_tile = None
        target_goal = None

        # Check rows 0-2 first (can use standard solving)
        for r in range(3):
            for c in range(4):
                expected = r * 4 + c + 1
                if self.board[r][c] != expected:
                    target_tile = expected
                    target_goal = (r, c)
                    break
            if target_tile:
                break

        # If first 3 rows solved, work on last row
        if not target_tile:
            for c in range(4):
                expected = 12 + c + 1 if c < 3 else 0
                if self.board[3][c] != expected:
                    target_tile = expected
                    target_goal = (3, c)
                    break

        if not target_tile:
            return None  # Solved!

        # Find where the target tile currently is
        tile_pos = self._find_tile(target_tile)
        if not tile_pos:
            return None

        # Strategy: Move the empty space toward the tile, then move tile toward goal
        return self._move_toward_goal(tile_pos, target_goal, target_tile)

    def _move_toward_goal(self, tile_pos, goal_pos, tile_value):
        """
        Move a tile toward its goal position.
        Returns the position of a tile to slide.
        """
        tile_r, tile_c = tile_pos
        goal_r, goal_c = goal_pos

        # If tile is already in position, move on
        if tile_pos == goal_pos:
            return None

        # Get movable tiles
        movable = self._get_movable_tiles()

        # If the target tile is movable and moving it gets closer to goal, do it
        if tile_pos in movable:
            # Calculate if this move helps
            new_empty_r, new_empty_c = tile_r, tile_c
            new_tile_r, new_tile_c = self.empty_row, self.empty_col

            old_dist = abs(tile_r - goal_r) + abs(tile_c - goal_c)
            new_dist = abs(new_tile_r - goal_r) + abs(new_tile_c - goal_c)

            if new_dist < old_dist:
                return tile_pos

        # Otherwise, move empty space toward tile (or around it to push)
        best_move = None
        best_score = float('inf')

        for move_r, move_c in movable:
            # Don't move tiles that are already in their correct position
            # in the solved rows (to avoid messing up solved parts)
            tile_at_pos = self.board[move_r][move_c]
            tile_goal = self._get_goal_position(tile_at_pos)

            # Check if moving this tile would displace a correctly placed tile
            # in a row we've already solved
            if (move_r, move_c) == tile_goal and move_r < goal_r:
                continue  # Don't move correctly placed tiles in earlier rows

            # Score based on how this move helps us
            # We want empty space to be on the opposite side of tile from goal
            # so we can push tile toward goal

            # Calculate where empty would be after this move
            new_empty_r, new_empty_c = move_r, move_c

            # Calculate ideal empty position (opposite side of tile from goal)
            if goal_r < tile_r:
                ideal_empty_r = tile_r + 1
            elif goal_r > tile_r:
                ideal_empty_r = tile_r - 1
            else:
                ideal_empty_r = tile_r

            if goal_c < tile_c:
                ideal_empty_c = tile_c + 1
            elif goal_c > tile_c:
                ideal_empty_c = tile_c - 1
            else:
                ideal_empty_c = tile_c

            # Clamp to valid positions
            ideal_empty_r = max(0, min(3, ideal_empty_r))
            ideal_empty_c = max(0, min(3, ideal_empty_c))

            # Score: distance from new empty position to ideal position
            score = abs(new_empty_r - ideal_empty_r) + abs(new_empty_c - ideal_empty_c)

            # Bonus: if this moves the target tile closer to goal
            if (move_r, move_c) == tile_pos:
                tile_new_r, tile_new_c = self.empty_row, self.empty_col
                old_dist = abs(tile_r - goal_r) + abs(tile_c - goal_c)
                new_dist = abs(tile_new_r - goal_r) + abs(tile_new_c - goal_c)
                if new_dist < old_dist:
                    score -= 10  # Big bonus for progress

            if score < best_score:
                best_score = score
                best_move = (move_r, move_c)

        return best_move

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw board background
        self.display.draw_rect(
            self.BOARD_X - 1, self.BOARD_Y - 1,
            self.BOARD_PIXELS + 2, self.BOARD_PIXELS + 2,
            self.BOARD_BG
        )

        # Draw tiles
        for r in range(4):
            for c in range(4):
                self._draw_tile(r, c)

        # Draw move count
        self.display.draw_text_small(2, 1, f"M:{self.move_count}", Colors.WHITE)

        # Draw win message
        if self.solved:
            # Flash "SOLVED!" text
            if int(self.time * 3) % 2 == 0:
                self.display.draw_text_small(18, 1, "SOLVED!", Colors.GREEN)

        # Overlay "DEMO" text (blinking)
        if int(self.time * 2) % 2 == 0:
            self.display.draw_text_small(46, 1, "DEMO", Colors.GRAY)

    def _draw_tile(self, row, col):
        """Draw a single tile."""
        tile = self.board[row][col]

        x = self.BOARD_X + self.GAP + col * (self.TILE_SIZE + self.GAP)
        y = self.BOARD_Y + self.GAP + row * (self.TILE_SIZE + self.GAP)

        if tile == 0:
            # Empty space - draw dark background
            self.display.draw_rect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.BOARD_BG)
            return

        # Tile color based on row of goal position
        goal_row = (tile - 1) // 4
        color = self.TILE_COLORS[goal_row]

        # Draw tile background
        self.display.draw_rect(x, y, self.TILE_SIZE, self.TILE_SIZE, color)

        # Draw slightly darker border
        border_color = (color[0] * 2 // 3, color[1] * 2 // 3, color[2] * 2 // 3)
        for i in range(self.TILE_SIZE):
            self.display.set_pixel(x + i, y, border_color)
            self.display.set_pixel(x + i, y + self.TILE_SIZE - 1, border_color)
            self.display.set_pixel(x, y + i, border_color)
            self.display.set_pixel(x + self.TILE_SIZE - 1, y + i, border_color)

        # Draw tile number
        if tile < 10:
            text_x = x + 5
        else:
            text_x = x + 3

        text_y = y + 4
        self.display.draw_text_small(text_x, text_y, str(tile), self.TEXT_COLOR)

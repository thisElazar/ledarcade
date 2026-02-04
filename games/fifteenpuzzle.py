"""
15 Puzzle - Classic Sliding Tile Toy
=====================================
The classic 1880s sliding puzzle. Arrange tiles 1-15 in order
by sliding them into the empty space.

Controls:
  Arrow Keys - Slide tile into empty space
  Space      - Shuffle / New game (when solved)
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class FifteenPuzzle(Game):
    name = "15 PUZZLE"
    description = "1880s sliding puzzle"
    category = "toys"

    # Board layout (matching demo style)
    BOARD_SIZE = 4
    TILE_SIZE = 14
    GAP = 1
    BOARD_PIXELS = TILE_SIZE * BOARD_SIZE + GAP * (BOARD_SIZE + 1)  # 60
    BOARD_X = (GRID_SIZE - BOARD_PIXELS) // 2
    BOARD_Y = (GRID_SIZE - BOARD_PIXELS) // 2 + 2

    # Colors for each row (matching demo)
    TILE_COLORS = [
        (200, 80, 80),    # Row 1: Red
        (80, 200, 80),    # Row 2: Green
        (80, 80, 200),    # Row 3: Blue
        (200, 200, 80),   # Row 4: Yellow
    ]
    BOARD_BG = (30, 30, 40)
    TEXT_COLOR = Colors.WHITE

    def __init__(self, display: Display):
        super().__init__(display)
        self.best_moves = 999
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.moves = 0
        self.won = False

        # Board as 2D array [row][col], values 1-15 with 0 for empty
        self.board = [[0] * 4 for _ in range(4)]
        for r in range(4):
            for c in range(4):
                self.board[r][c] = r * 4 + c + 1
        self.board[3][3] = 0

        self.empty_row = 3
        self.empty_col = 3

        # Shuffle
        self.shuffle()

        # Input timing
        self.move_cooldown = 0

    def shuffle(self):
        """Shuffle by making random valid moves (ensures solvability)."""
        for _ in range(200):
            moves = []
            if self.empty_row > 0:
                moves.append((-1, 0))
            if self.empty_row < 3:
                moves.append((1, 0))
            if self.empty_col > 0:
                moves.append((0, -1))
            if self.empty_col < 3:
                moves.append((0, 1))

            dr, dc = random.choice(moves)
            self.slide_tile(self.empty_row + dr, self.empty_col + dc)

        self.moves = 0
        self.won = False

    def slide_tile(self, row, col):
        """Slide tile at (row, col) into empty space if adjacent."""
        if abs(row - self.empty_row) + abs(col - self.empty_col) != 1:
            return False

        # Swap
        self.board[self.empty_row][self.empty_col] = self.board[row][col]
        self.board[row][col] = 0
        self.empty_row = row
        self.empty_col = col
        return True

    def is_solved(self):
        """Check if puzzle is solved."""
        for r in range(4):
            for c in range(4):
                expected = r * 4 + c + 1 if (r, c) != (3, 3) else 0
                if self.board[r][c] != expected:
                    return False
        return True

    def try_move(self, direction):
        """Try to slide a tile based on direction input."""
        # Direction is where the tile comes FROM to fill empty
        if direction == 'up' and self.empty_row < 3:
            tile_row, tile_col = self.empty_row + 1, self.empty_col
        elif direction == 'down' and self.empty_row > 0:
            tile_row, tile_col = self.empty_row - 1, self.empty_col
        elif direction == 'left' and self.empty_col < 3:
            tile_row, tile_col = self.empty_row, self.empty_col + 1
        elif direction == 'right' and self.empty_col > 0:
            tile_row, tile_col = self.empty_row, self.empty_col - 1
        else:
            return False

        if self.slide_tile(tile_row, tile_col):
            self.moves += 1
            return True
        return False

    def update(self, input_state: InputState, dt: float):
        if self.move_cooldown > 0:
            self.move_cooldown -= dt

        if self.won:
            if input_state.action_l or input_state.action_r:
                self.reset()
            return

        if self.move_cooldown <= 0:
            moved = False
            if input_state.up:
                moved = self.try_move('up')
            elif input_state.down:
                moved = self.try_move('down')
            elif input_state.left:
                moved = self.try_move('left')
            elif input_state.right:
                moved = self.try_move('right')

            if moved:
                self.move_cooldown = 0.12
                if self.is_solved():
                    self.won = True
                    if self.moves < self.best_moves:
                        self.best_moves = self.moves

        # Reshuffle with button
        if input_state.action_l or input_state.action_r:
            if not self.won:
                self.shuffle()

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
                self.draw_tile(r, c)

        # Draw move count at top
        self.display.draw_text_small(2, 1, f"M:{self.moves}", Colors.WHITE)

        # Draw best score
        if self.best_moves < 999:
            self.display.draw_text_small(36, 1, f"B:{self.best_moves}", Colors.YELLOW)

        # Win message
        if self.won:
            if int(self.moves * 0.1) % 2 == 0:  # Flash
                self.display.draw_text_small(18, 1, "SOLVED!", Colors.GREEN)

    def draw_tile(self, row, col):
        """Draw a single tile."""
        tile = self.board[row][col]

        x = self.BOARD_X + self.GAP + col * (self.TILE_SIZE + self.GAP)
        y = self.BOARD_Y + self.GAP + row * (self.TILE_SIZE + self.GAP)

        if tile == 0:
            # Empty space
            self.display.draw_rect(x, y, self.TILE_SIZE, self.TILE_SIZE, self.BOARD_BG)
            return

        # Color based on which row the tile BELONGS to
        goal_row = (tile - 1) // 4
        color = self.TILE_COLORS[goal_row]

        # Draw tile
        self.display.draw_rect(x, y, self.TILE_SIZE, self.TILE_SIZE, color)

        # Draw darker top border
        border_color = (color[0] * 2 // 3, color[1] * 2 // 3, color[2] * 2 // 3)
        for i in range(self.TILE_SIZE):
            self.display.set_pixel(x + i, y, border_color)

        # Draw number
        tx = x + 3 if tile < 10 else x + 1
        ty = y + 4
        self.display.draw_text_small(tx, ty, str(tile), self.TEXT_COLOR)

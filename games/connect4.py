"""
Connect 4 - Two Player Strategy Game
=====================================
Drop pieces to connect 4 in a row!

Controls:
  Left/Right - Choose column
  Space      - Drop piece
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


# Players
PLAYER_1 = 1  # Red
PLAYER_2 = 2  # Yellow


class Connect4(Game):
    name = "CONNECT4"
    description = "2P Strategy"
    category = "2_player"

    # Board dimensions
    COLS = 7
    ROWS = 6

    # Visual layout - centered on 64x64
    CELL_SIZE = 8  # 8x8 pixels per cell
    BOARD_WIDTH = COLS * CELL_SIZE  # 56 pixels
    BOARD_HEIGHT = ROWS * CELL_SIZE  # 48 pixels
    BOARD_X = (GRID_SIZE - BOARD_WIDTH) // 2  # 4 pixels from left
    BOARD_Y = GRID_SIZE - BOARD_HEIGHT - 2  # 2 pixels from bottom

    # Colors
    BOARD_COLOR = (30, 30, 180)  # Blue board
    EMPTY_COLOR = (15, 15, 60)   # Dark slot
    PLAYER_1_COLOR = (255, 60, 60)   # Red
    PLAYER_2_COLOR = (255, 220, 40)  # Yellow
    CURSOR_COLOR = Colors.WHITE
    WIN_HIGHLIGHT = Colors.WHITE

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Board state - 0 = empty, 1 = player 1, 2 = player 2
        self.board = [[0 for _ in range(self.COLS)] for _ in range(self.ROWS)]

        # Game state
        self.current_player = PLAYER_1
        self.cursor_col = 3  # Start in middle

        # Animation state
        self.dropping = False
        self.drop_col = 0
        self.drop_row = 0  # Target row
        self.drop_y = 0.0  # Current visual y position
        self.drop_speed = 60.0  # Pixels per second

        # Win state
        self.winner = None
        self.win_cells = []  # List of (row, col) for winning 4

        # Input timing
        self.move_timer = 0
        self.move_delay = 0.12

        # Win animation
        self.win_flash_timer = 0

    def get_drop_row(self, col: int) -> int:
        """Find the lowest empty row in a column, or -1 if full."""
        for row in range(self.ROWS - 1, -1, -1):
            if self.board[row][col] == 0:
                return row
        return -1

    def check_win(self, row: int, col: int, player: int) -> list:
        """Check if placing at (row, col) creates a win. Returns winning cells or empty list."""
        directions = [
            (0, 1),   # Horizontal
            (1, 0),   # Vertical
            (1, 1),   # Diagonal down-right
            (1, -1),  # Diagonal down-left
        ]

        for dr, dc in directions:
            cells = [(row, col)]

            # Check positive direction
            r, c = row + dr, col + dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == player:
                cells.append((r, c))
                r += dr
                c += dc

            # Check negative direction
            r, c = row - dr, col - dc
            while 0 <= r < self.ROWS and 0 <= c < self.COLS and self.board[r][c] == player:
                cells.append((r, c))
                r -= dr
                c -= dc

            if len(cells) >= 4:
                return cells

        return []

    def is_board_full(self) -> bool:
        """Check if the board is completely full (draw)."""
        return all(self.board[0][col] != 0 for col in range(self.COLS))

    def update(self, input_state: InputState, dt: float):
        if self.state == GameState.GAME_OVER:
            # Flash winning pieces
            self.win_flash_timer += dt
            return

        # Handle drop animation
        if self.dropping:
            target_y = self.BOARD_Y + self.drop_row * self.CELL_SIZE
            self.drop_y += self.drop_speed * dt

            if self.drop_y >= target_y:
                # Drop complete
                self.drop_y = target_y
                self.dropping = False
                self.board[self.drop_row][self.drop_col] = self.current_player

                # Check for win
                win_cells = self.check_win(self.drop_row, self.drop_col, self.current_player)
                if win_cells:
                    self.winner = self.current_player
                    self.win_cells = win_cells
                    self.state = GameState.GAME_OVER
                elif self.is_board_full():
                    self.winner = None  # Draw
                    self.state = GameState.GAME_OVER
                else:
                    # Switch players
                    self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1
            return

        # Cursor movement
        self.move_timer += dt

        if input_state.left and self.move_timer >= self.move_delay:
            self.cursor_col = max(0, self.cursor_col - 1)
            self.move_timer = 0
        elif input_state.right and self.move_timer >= self.move_delay:
            self.cursor_col = min(self.COLS - 1, self.cursor_col + 1)
            self.move_timer = 0
        elif not input_state.left and not input_state.right:
            self.move_timer = self.move_delay  # Allow immediate move on new press

        # Drop piece
        if (input_state.action_l or input_state.action_r):
            drop_row = self.get_drop_row(self.cursor_col)
            if drop_row >= 0:
                self.dropping = True
                self.drop_col = self.cursor_col
                self.drop_row = drop_row
                self.drop_y = self.BOARD_Y - self.CELL_SIZE  # Start above board

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw turn indicator at top
        self.draw_turn_indicator()

        # Draw the board frame
        self.display.draw_rect(
            self.BOARD_X - 1, self.BOARD_Y - 1,
            self.BOARD_WIDTH + 2, self.BOARD_HEIGHT + 2,
            self.BOARD_COLOR
        )

        # Draw slots and pieces
        for row in range(self.ROWS):
            for col in range(self.COLS):
                self.draw_cell(row, col)

        # Draw dropping piece
        if self.dropping:
            self.draw_dropping_piece()

        # Draw cursor (preview piece above board)
        if not self.dropping and self.state == GameState.PLAYING:
            self.draw_cursor()

        # Draw win/draw message
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()

    def draw_turn_indicator(self):
        """Draw whose turn it is."""
        color = self.PLAYER_1_COLOR if self.current_player == PLAYER_1 else self.PLAYER_2_COLOR
        text = "P1" if self.current_player == PLAYER_1 else "P2"

        # Draw player indicator
        self.display.draw_text_small(2, 2, text, color)

        # Draw a small piece preview
        cx = 18
        cy = 4
        self.draw_piece(cx, cy, color, radius=2)

    def draw_cell(self, row: int, col: int):
        """Draw a single board cell."""
        x = self.BOARD_X + col * self.CELL_SIZE
        y = self.BOARD_Y + row * self.CELL_SIZE

        # Draw slot background (circular hole effect)
        center_x = x + self.CELL_SIZE // 2
        center_y = y + self.CELL_SIZE // 2

        piece = self.board[row][col]

        # Check if this is a winning cell
        is_win_cell = (row, col) in self.win_cells
        flash_on = int(self.win_flash_timer * 6) % 2 == 0

        if piece == 0:
            # Empty slot
            self.draw_piece(center_x, center_y, self.EMPTY_COLOR, radius=3)
        elif piece == PLAYER_1:
            color = self.PLAYER_1_COLOR
            if is_win_cell and flash_on:
                color = self.WIN_HIGHLIGHT
            self.draw_piece(center_x, center_y, color, radius=3)
        else:
            color = self.PLAYER_2_COLOR
            if is_win_cell and flash_on:
                color = self.WIN_HIGHLIGHT
            self.draw_piece(center_x, center_y, color, radius=3)

    def draw_piece(self, cx: int, cy: int, color: tuple, radius: int = 3):
        """Draw a circular piece at center (cx, cy)."""
        # Simple filled circle using distance check
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, color)

    def draw_dropping_piece(self):
        """Draw the piece that's currently falling."""
        x = self.BOARD_X + self.drop_col * self.CELL_SIZE
        center_x = x + self.CELL_SIZE // 2
        center_y = int(self.drop_y) + self.CELL_SIZE // 2

        color = self.PLAYER_1_COLOR if self.current_player == PLAYER_1 else self.PLAYER_2_COLOR
        self.draw_piece(center_x, center_y, color, radius=3)

    def draw_cursor(self):
        """Draw the cursor piece above the selected column."""
        x = self.BOARD_X + self.cursor_col * self.CELL_SIZE
        center_x = x + self.CELL_SIZE // 2
        center_y = self.BOARD_Y - 6  # Above the board

        color = self.PLAYER_1_COLOR if self.current_player == PLAYER_1 else self.PLAYER_2_COLOR

        # Draw piece
        self.draw_piece(center_x, center_y, color, radius=2)

        # Draw down arrow indicator
        self.display.set_pixel(center_x, center_y + 4, self.CURSOR_COLOR)

    def draw_game_over(self):
        """Draw game over overlay."""
        # Dim the background slightly by drawing semi-transparent overlay
        # (simplified - just draw text on top)

        if self.winner:
            winner_text = "P1 WINS!" if self.winner == PLAYER_1 else "P2 WINS!"
            color = self.PLAYER_1_COLOR if self.winner == PLAYER_1 else self.PLAYER_2_COLOR
        else:
            winner_text = "DRAW!"
            color = Colors.GRAY

        # Draw winner text at top
        text_x = (GRID_SIZE - len(winner_text) * 4) // 2
        self.display.draw_text_small(text_x, 2, winner_text, color)

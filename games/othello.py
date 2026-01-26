"""
Othello (Reversi) - Two Player Strategy Game
=============================================
Flip your opponent's pieces by sandwiching them!

Controls:
  Arrow Keys - Move cursor
  Space      - Place piece
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


# Players
PLAYER_1 = 1  # Black (goes first)
PLAYER_2 = 2  # White


class Othello(Game):
    name = "OTHELLO"
    description = "2P Strategy"
    category = "2_player"

    # Board layout
    BOARD_SIZE = 8
    CELL_SIZE = 7  # 7x7 pixels per square (56x56 total)
    BOARD_OFFSET_X = 4
    BOARD_OFFSET_Y = 8

    # Colors
    BOARD_COLOR = (30, 120, 50)  # Green felt
    GRID_COLOR = (20, 80, 35)
    PLAYER_1_COLOR = (30, 30, 30)    # Black
    PLAYER_2_COLOR = (240, 240, 240)  # White
    CURSOR_COLOR = Colors.YELLOW
    VALID_MOVE_COLOR = (80, 180, 100)

    # Animation
    FLIP_DURATION = 0.3  # seconds per flip animation

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Board: 0 = empty, 1 = player 1, 2 = player 2
        self.board = [[0 for _ in range(8)] for _ in range(8)]

        # Initial 4 pieces in center
        self.board[3][3] = PLAYER_2
        self.board[3][4] = PLAYER_1
        self.board[4][3] = PLAYER_1
        self.board[4][4] = PLAYER_2

        # Game state
        self.current_player = PLAYER_1  # Black goes first
        self.cursor_x = 3
        self.cursor_y = 3

        # Valid moves for current player
        self.valid_moves = self.get_valid_moves(self.current_player)

        # Flip animation
        self.flipping = False
        self.flip_cells = []  # List of (col, row) being flipped
        self.flip_timer = 0
        self.flip_to_player = None

        # Score
        self.p1_score = 2
        self.p2_score = 2

        # Win state
        self.winner = None
        self.game_over_reason = ""

        # Input timing
        self.move_timer = 0
        self.move_delay = 0.12
        self.last_direction = (0, 0)

        # Pass tracking
        self.consecutive_passes = 0

    def get_valid_moves(self, player: int) -> list:
        """Get all valid moves for a player."""
        moves = []
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == 0:
                    if self.get_flips(col, row, player):
                        moves.append((col, row))
        return moves

    def get_flips(self, col: int, row: int, player: int) -> list:
        """Get list of pieces that would be flipped by placing at (col, row)."""
        if self.board[row][col] != 0:
            return []

        opponent = PLAYER_2 if player == PLAYER_1 else PLAYER_1
        all_flips = []

        # Check all 8 directions
        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),          (0, 1),
            (1, -1),  (1, 0), (1, 1)
        ]

        for dr, dc in directions:
            flips = []
            r, c = row + dr, col + dc

            # Move in direction while finding opponent pieces
            while 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == opponent:
                flips.append((c, r))
                r += dr
                c += dc

            # Valid only if we end on our own piece
            if flips and 0 <= r < 8 and 0 <= c < 8 and self.board[r][c] == player:
                all_flips.extend(flips)

        return all_flips

    def make_move(self, col: int, row: int):
        """Place a piece and flip captured pieces."""
        flips = self.get_flips(col, row, self.current_player)
        if not flips:
            return False

        # Place piece
        self.board[row][col] = self.current_player

        # Start flip animation
        self.flipping = True
        self.flip_cells = flips
        self.flip_timer = 0
        self.flip_to_player = self.current_player

        return True

    def finish_flip(self):
        """Complete the flip animation and end turn."""
        # Flip all captured pieces
        for col, row in self.flip_cells:
            self.board[row][col] = self.flip_to_player

        self.flipping = False
        self.flip_cells = []
        self.consecutive_passes = 0

        self.end_turn()

    def end_turn(self):
        """Switch to next player."""
        # Update scores
        self.update_scores()

        # Switch players
        self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1
        self.valid_moves = self.get_valid_moves(self.current_player)

        # Check if current player must pass
        if not self.valid_moves:
            self.consecutive_passes += 1

            if self.consecutive_passes >= 2:
                # Both players passed - game over
                self.end_game()
            else:
                # Pass to other player
                self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1
                self.valid_moves = self.get_valid_moves(self.current_player)

                if not self.valid_moves:
                    # Other player also can't move - game over
                    self.end_game()

    def update_scores(self):
        """Count pieces for each player."""
        self.p1_score = 0
        self.p2_score = 0
        for row in range(8):
            for col in range(8):
                if self.board[row][col] == PLAYER_1:
                    self.p1_score += 1
                elif self.board[row][col] == PLAYER_2:
                    self.p2_score += 1

    def end_game(self):
        """Determine winner and end game."""
        self.update_scores()
        self.state = GameState.GAME_OVER

        if self.p1_score > self.p2_score:
            self.winner = PLAYER_1
            self.game_over_reason = f"P1 WINS {self.p1_score}-{self.p2_score}"
        elif self.p2_score > self.p1_score:
            self.winner = PLAYER_2
            self.game_over_reason = f"P2 WINS {self.p2_score}-{self.p1_score}"
        else:
            self.winner = None
            self.game_over_reason = f"DRAW {self.p1_score}-{self.p2_score}"

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Handle flip animation
        if self.flipping:
            self.flip_timer += dt
            if self.flip_timer >= self.FLIP_DURATION:
                self.finish_flip()
            return

        # Cursor movement
        dx, dy = input_state.dx, input_state.dy

        if (dx, dy) != (0, 0):
            if (dx, dy) != self.last_direction:
                self.cursor_x = max(0, min(7, self.cursor_x + dx))
                self.cursor_y = max(0, min(7, self.cursor_y + dy))
                self.move_timer = 0
                self.last_direction = (dx, dy)
            else:
                self.move_timer += dt
                if self.move_timer >= self.move_delay:
                    self.cursor_x = max(0, min(7, self.cursor_x + dx))
                    self.cursor_y = max(0, min(7, self.cursor_y + dy))
                    self.move_timer = 0
        else:
            self.last_direction = (0, 0)
            self.move_timer = 0

        # Place piece
        if input_state.action:
            if (self.cursor_x, self.cursor_y) in self.valid_moves:
                self.make_move(self.cursor_x, self.cursor_y)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        self.draw_hud()

        # Draw board background
        self.display.draw_rect(
            self.BOARD_OFFSET_X, self.BOARD_OFFSET_Y,
            self.BOARD_SIZE * self.CELL_SIZE,
            self.BOARD_SIZE * self.CELL_SIZE,
            self.BOARD_COLOR
        )

        # Draw grid lines
        for i in range(9):
            # Vertical
            x = self.BOARD_OFFSET_X + i * self.CELL_SIZE
            self.display.draw_line(
                x, self.BOARD_OFFSET_Y,
                x, self.BOARD_OFFSET_Y + self.BOARD_SIZE * self.CELL_SIZE - 1,
                self.GRID_COLOR
            )
            # Horizontal
            y = self.BOARD_OFFSET_Y + i * self.CELL_SIZE
            self.display.draw_line(
                self.BOARD_OFFSET_X, y,
                self.BOARD_OFFSET_X + self.BOARD_SIZE * self.CELL_SIZE - 1, y,
                self.GRID_COLOR
            )

        # Draw pieces and valid moves
        for row in range(8):
            for col in range(8):
                self.draw_cell(col, row)

        # Draw cursor
        if not self.flipping:
            self.draw_cursor()

        # Game over
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()

    def draw_hud(self):
        """Draw score and turn indicator."""
        # Player 1 score (black)
        self.display.draw_text_small(1, 1, f"P1:{self.p1_score:2d}", self.PLAYER_1_COLOR)

        # Player 2 score (white)
        self.display.draw_text_small(36, 1, f"P2:{self.p2_score:2d}", self.PLAYER_2_COLOR)

        # Turn indicator (highlight current player's score)
        if self.current_player == PLAYER_1:
            self.display.set_pixel(0, 1, Colors.YELLOW)
        else:
            self.display.set_pixel(35, 1, Colors.YELLOW)

    def draw_cell(self, col: int, row: int):
        """Draw a single cell with piece or valid move indicator."""
        cx = self.BOARD_OFFSET_X + col * self.CELL_SIZE + self.CELL_SIZE // 2
        cy = self.BOARD_OFFSET_Y + row * self.CELL_SIZE + self.CELL_SIZE // 2

        piece = self.board[row][col]

        # Check if this cell is being flipped
        is_flipping = (col, row) in self.flip_cells

        if piece != 0:
            if is_flipping:
                # Animate flip - shrink then grow with new color
                progress = self.flip_timer / self.FLIP_DURATION
                if progress < 0.5:
                    # Shrinking (old color)
                    radius = int(2 * (1 - progress * 2))
                    color = self.PLAYER_1_COLOR if piece == PLAYER_1 else self.PLAYER_2_COLOR
                else:
                    # Growing (new color)
                    radius = int(2 * ((progress - 0.5) * 2))
                    color = self.PLAYER_1_COLOR if self.flip_to_player == PLAYER_1 else self.PLAYER_2_COLOR
                if radius > 0:
                    self.draw_piece(cx, cy, color, radius)
            else:
                color = self.PLAYER_1_COLOR if piece == PLAYER_1 else self.PLAYER_2_COLOR
                self.draw_piece(cx, cy, color, 2)
        elif (col, row) in self.valid_moves and not self.flipping:
            # Valid move indicator - small dot
            self.display.set_pixel(cx, cy, self.VALID_MOVE_COLOR)

    def draw_piece(self, cx: int, cy: int, color: tuple, radius: int = 2):
        """Draw a circular piece."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    px, py = cx + dx, cy + dy
                    if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                        self.display.set_pixel(px, py, color)

    def draw_cursor(self):
        """Draw cursor around current cell."""
        px = self.BOARD_OFFSET_X + self.cursor_x * self.CELL_SIZE
        py = self.BOARD_OFFSET_Y + self.cursor_y * self.CELL_SIZE
        size = self.CELL_SIZE

        c = self.CURSOR_COLOR

        # Draw corners
        self.display.set_pixel(px, py, c)
        self.display.set_pixel(px + 1, py, c)
        self.display.set_pixel(px, py + 1, c)

        self.display.set_pixel(px + size - 1, py, c)
        self.display.set_pixel(px + size - 2, py, c)
        self.display.set_pixel(px + size - 1, py + 1, c)

        self.display.set_pixel(px, py + size - 1, c)
        self.display.set_pixel(px + 1, py + size - 1, c)
        self.display.set_pixel(px, py + size - 2, c)

        self.display.set_pixel(px + size - 1, py + size - 1, c)
        self.display.set_pixel(px + size - 2, py + size - 1, c)
        self.display.set_pixel(px + size - 1, py + size - 2, c)

    def draw_game_over(self):
        """Draw game over message."""
        if self.winner == PLAYER_1:
            color = self.PLAYER_1_COLOR
        elif self.winner == PLAYER_2:
            color = self.PLAYER_2_COLOR
        else:
            color = Colors.GRAY

        # Draw result
        self.display.draw_text_small(4, 1, self.game_over_reason, color)

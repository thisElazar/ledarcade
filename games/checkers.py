"""
Checkers - Two Player Strategy Game
====================================
Classic checkers on a 64x64 LED display!

Controls:
  Arrow Keys - Move cursor
  Space      - Select piece / Confirm move
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


# Players
PLAYER_1 = 1  # Red (bottom)
PLAYER_2 = 2  # White (top)


class Piece:
    """Represents a checker piece."""

    def __init__(self, player: int, is_king: bool = False):
        self.player = player
        self.is_king = is_king


class Checkers(Game):
    name = "CHECKERS"
    description = "2P Strategy"
    category = "2_player"

    # Board layout
    BOARD_SIZE = 8
    CELL_SIZE = 7  # 7x7 pixels per square (56x56 total)
    BOARD_OFFSET_X = 4
    BOARD_OFFSET_Y = 6

    # Colors
    LIGHT_SQUARE = (180, 160, 130)
    DARK_SQUARE = (80, 60, 40)
    PLAYER_1_COLOR = (220, 50, 50)   # Red
    PLAYER_2_COLOR = (240, 240, 240)  # White
    KING_ACCENT = (255, 215, 0)  # Gold crown
    CURSOR_COLOR = Colors.CYAN
    SELECTED_COLOR = Colors.YELLOW
    VALID_MOVE_COLOR = (100, 200, 100)
    MUST_JUMP_COLOR = (255, 150, 50)  # Orange for mandatory jump

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Initialize board
        self.board = [[None for _ in range(8)] for _ in range(8)]
        self.setup_pieces()

        # Game state
        self.current_player = PLAYER_1
        self.cursor_x = 0
        self.cursor_y = 5

        # Selection state
        self.selected_pos = None
        self.valid_moves = []  # List of (row, col) destinations
        self.jump_moves = []   # Subset of valid_moves that are jumps
        self.must_jump = False  # True if current player must jump

        # Multi-jump state
        self.multi_jump_pos = None  # Position during multi-jump sequence
        self.multi_jump_player = None

        # Win state
        self.winner = None
        self.game_over_reason = ""

        # Input timing
        self.move_timer = 0
        self.move_delay = 0.15
        self.last_direction = (0, 0)

        # Check for available jumps
        self.update_must_jump()

    def setup_pieces(self):
        """Set up initial checker positions."""
        # Player 2 (white) at top
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:  # Dark squares only
                    self.board[row][col] = Piece(PLAYER_2)

        # Player 1 (red) at bottom
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    self.board[row][col] = Piece(PLAYER_1)

    def get_piece(self, col: int, row: int) -> Piece:
        """Get piece at position."""
        if 0 <= col < 8 and 0 <= row < 8:
            return self.board[row][col]
        return None

    def get_moves_for_piece(self, col: int, row: int) -> tuple:
        """Get valid moves and jumps for a piece. Returns (moves, jumps)."""
        piece = self.get_piece(col, row)
        if not piece or piece.player != self.current_player:
            return [], []

        moves = []
        jumps = []

        # Direction of movement
        if piece.is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif piece.player == PLAYER_1:
            directions = [(-1, -1), (-1, 1)]  # Moving up
        else:
            directions = [(1, -1), (1, 1)]  # Moving down

        for dr, dc in directions:
            new_row, new_col = row + dr, col + dc

            # Check simple move
            if 0 <= new_row < 8 and 0 <= new_col < 8:
                if self.board[new_row][new_col] is None:
                    moves.append((new_col, new_row))
                # Check jump
                elif self.board[new_row][new_col].player != piece.player:
                    jump_row, jump_col = new_row + dr, new_col + dc
                    if 0 <= jump_row < 8 and 0 <= jump_col < 8:
                        if self.board[jump_row][jump_col] is None:
                            jumps.append((jump_col, jump_row))

        return moves, jumps

    def get_all_jumps(self, player: int) -> list:
        """Get all available jumps for a player."""
        all_jumps = []
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece and piece.player == player:
                    _, jumps = self.get_moves_for_piece(col, row)
                    if jumps:
                        all_jumps.append((col, row, jumps))
        return all_jumps

    def update_must_jump(self):
        """Check if current player must make a jump."""
        self.must_jump = len(self.get_all_jumps(self.current_player)) > 0

    def can_continue_jumping(self, col: int, row: int) -> list:
        """Check if piece at position can make another jump."""
        piece = self.get_piece(col, row)
        if not piece:
            return []

        jumps = []

        # Direction of movement (same logic as get_moves_for_piece)
        if piece.is_king:
            directions = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        elif piece.player == PLAYER_1:
            directions = [(-1, -1), (-1, 1)]  # Moving up
        else:
            directions = [(1, -1), (1, 1)]  # Moving down

        for dr, dc in directions:
            adj_row, adj_col = row + dr, col + dc

            # Check for opponent piece to jump over
            if 0 <= adj_row < 8 and 0 <= adj_col < 8:
                adj_piece = self.board[adj_row][adj_col]
                if adj_piece and adj_piece.player != piece.player:
                    # Check landing spot
                    jump_row, jump_col = adj_row + dr, adj_col + dc
                    if 0 <= jump_row < 8 and 0 <= jump_col < 8:
                        if self.board[jump_row][jump_col] is None:
                            jumps.append((jump_col, jump_row))

        return jumps

    def make_move(self, from_col: int, from_row: int, to_col: int, to_row: int):
        """Execute a move."""
        piece = self.board[from_row][from_col]

        # Check if this is a jump
        is_jump = abs(to_row - from_row) == 2

        if is_jump:
            # Remove captured piece
            cap_row = (from_row + to_row) // 2
            cap_col = (from_col + to_col) // 2
            self.board[cap_row][cap_col] = None

        # Move piece
        self.board[to_row][to_col] = piece
        self.board[from_row][from_col] = None

        # Check for king promotion
        if piece.player == PLAYER_1 and to_row == 0:
            piece.is_king = True
        elif piece.player == PLAYER_2 and to_row == 7:
            piece.is_king = True

        # Check for multi-jump
        if is_jump:
            more_jumps = self.can_continue_jumping(to_col, to_row)
            if more_jumps:
                self.multi_jump_pos = (to_col, to_row)
                self.multi_jump_player = piece.player
                self.selected_pos = (to_col, to_row)
                self.valid_moves = more_jumps
                self.jump_moves = more_jumps
                # Move cursor to first valid jump destination
                self.cursor_x, self.cursor_y = more_jumps[0]
                return  # Don't end turn

        self.end_turn()

    def end_turn(self):
        """End current turn and switch players."""
        self.multi_jump_pos = None
        self.multi_jump_player = None
        self.selected_pos = None
        self.valid_moves = []
        self.jump_moves = []

        # Switch players
        self.current_player = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1

        # Update jump requirement
        self.update_must_jump()

        # Check for win
        self.check_win()

    def check_win(self):
        """Check if the game is over."""
        # Count pieces and check for available moves
        p1_pieces = 0
        p2_pieces = 0
        current_has_moves = False

        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    if piece.player == PLAYER_1:
                        p1_pieces += 1
                    else:
                        p2_pieces += 1

                    if piece.player == self.current_player:
                        moves, jumps = self.get_moves_for_piece(col, row)
                        if moves or jumps:
                            current_has_moves = True

        # Check for win conditions
        if p1_pieces == 0:
            self.winner = PLAYER_2
            self.game_over_reason = "P2 WINS!"
            self.state = GameState.GAME_OVER
        elif p2_pieces == 0:
            self.winner = PLAYER_1
            self.game_over_reason = "P1 WINS!"
            self.state = GameState.GAME_OVER
        elif not current_has_moves:
            # Current player has no moves - they lose
            self.winner = PLAYER_2 if self.current_player == PLAYER_1 else PLAYER_1
            self.game_over_reason = f"P{self.winner} WINS!"
            self.state = GameState.GAME_OVER

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Cursor movement with repeat delay
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

        # Select / Move
        if input_state.action:
            cursor_pos = (self.cursor_x, self.cursor_y)

            if self.multi_jump_pos:
                # During multi-jump, can only continue jumping
                if cursor_pos in self.valid_moves:
                    self.make_move(
                        self.multi_jump_pos[0], self.multi_jump_pos[1],
                        self.cursor_x, self.cursor_y
                    )
            elif self.selected_pos is None:
                # Try to select a piece
                piece = self.get_piece(self.cursor_x, self.cursor_y)
                if piece and piece.player == self.current_player:
                    moves, jumps = self.get_moves_for_piece(self.cursor_x, self.cursor_y)

                    # If must jump, only allow selecting pieces with jumps
                    if self.must_jump:
                        if jumps:
                            self.selected_pos = cursor_pos
                            self.valid_moves = jumps  # Only jumps allowed
                            self.jump_moves = jumps
                    else:
                        if moves or jumps:
                            self.selected_pos = cursor_pos
                            self.valid_moves = moves + jumps
                            self.jump_moves = jumps
            else:
                # Try to make a move
                if cursor_pos in self.valid_moves:
                    self.make_move(
                        self.selected_pos[0], self.selected_pos[1],
                        self.cursor_x, self.cursor_y
                    )
                    # Only clear selection if NOT in a multi-jump sequence
                    # (make_move sets multi_jump_pos if more jumps available)
                    if not self.multi_jump_pos:
                        self.selected_pos = None
                        self.valid_moves = []
                        self.jump_moves = []
                elif cursor_pos == self.selected_pos:
                    # Deselect
                    self.selected_pos = None
                    self.valid_moves = []
                    self.jump_moves = []
                else:
                    # Try selecting different piece
                    piece = self.get_piece(self.cursor_x, self.cursor_y)
                    if piece and piece.player == self.current_player:
                        moves, jumps = self.get_moves_for_piece(self.cursor_x, self.cursor_y)
                        if self.must_jump:
                            if jumps:
                                self.selected_pos = cursor_pos
                                self.valid_moves = jumps
                                self.jump_moves = jumps
                        else:
                            if moves or jumps:
                                self.selected_pos = cursor_pos
                                self.valid_moves = moves + jumps
                                self.jump_moves = jumps
                            else:
                                self.selected_pos = None
                                self.valid_moves = []
                                self.jump_moves = []
                    else:
                        self.selected_pos = None
                        self.valid_moves = []
                        self.jump_moves = []

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        self.draw_hud()

        # Draw board
        for row in range(8):
            for col in range(8):
                self.draw_square(col, row)

        # Game over overlay
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()

    def draw_hud(self):
        """Draw turn indicator and jump warning."""
        color = self.PLAYER_1_COLOR if self.current_player == PLAYER_1 else self.PLAYER_2_COLOR
        text = "P1" if self.current_player == PLAYER_1 else "P2"

        self.display.draw_text_small(2, 0, text, color)

        if self.must_jump:
            self.display.draw_text_small(20, 0, "JUMP!", self.MUST_JUMP_COLOR)

    def draw_square(self, col: int, row: int):
        """Draw a single board square."""
        px = self.BOARD_OFFSET_X + col * self.CELL_SIZE
        py = self.BOARD_OFFSET_Y + row * self.CELL_SIZE

        # Base square color
        is_light = (col + row) % 2 == 0
        color = self.LIGHT_SQUARE if is_light else self.DARK_SQUARE

        # Highlighting
        pos = (col, row)

        if pos in self.valid_moves:
            color = self.blend_colors(color, self.VALID_MOVE_COLOR, 0.5)

        if self.selected_pos == pos:
            color = self.blend_colors(color, self.SELECTED_COLOR, 0.4)

        # Draw square
        self.display.draw_rect(px, py, self.CELL_SIZE, self.CELL_SIZE, color)

        # Draw piece
        piece = self.get_piece(col, row)
        if piece:
            self.draw_piece(px, py, piece)

        # Draw valid move indicator
        if pos in self.valid_moves and not piece:
            cx = px + self.CELL_SIZE // 2
            cy = py + self.CELL_SIZE // 2
            self.display.set_pixel(cx, cy, self.VALID_MOVE_COLOR)

        # Draw cursor
        if (col, row) == (self.cursor_x, self.cursor_y):
            self.draw_cursor(px, py)

    def draw_piece(self, px: int, py: int, piece: Piece):
        """Draw a checker piece."""
        cx = px + self.CELL_SIZE // 2
        cy = py + self.CELL_SIZE // 2

        color = self.PLAYER_1_COLOR if piece.player == PLAYER_1 else self.PLAYER_2_COLOR

        # Draw main piece (filled circle)
        radius = 2
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx * dx + dy * dy <= radius * radius:
                    self.display.set_pixel(cx + dx, cy + dy, color)

        # Draw king crown
        if piece.is_king:
            self.display.set_pixel(cx, cy - 1, self.KING_ACCENT)
            self.display.set_pixel(cx - 1, cy, self.KING_ACCENT)
            self.display.set_pixel(cx + 1, cy, self.KING_ACCENT)

    def draw_cursor(self, px: int, py: int):
        """Draw cursor corners."""
        c = self.CURSOR_COLOR
        size = self.CELL_SIZE

        # Corners
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
        color = self.PLAYER_1_COLOR if self.winner == PLAYER_1 else self.PLAYER_2_COLOR
        self.display.draw_text_small(8, 0, self.game_over_reason, color)

    def blend_colors(self, c1: tuple, c2: tuple, factor: float) -> tuple:
        """Blend two colors."""
        return (
            int(c1[0] * (1 - factor) + c2[0] * factor),
            int(c1[1] * (1 - factor) + c2[1] * factor),
            int(c1[2] * (1 - factor) + c2[2] * factor),
        )

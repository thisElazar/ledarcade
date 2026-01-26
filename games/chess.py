"""
Chess - Two Player Strategy Game
================================
Classic chess on a 64x64 LED display!

Controls:
  Arrow Keys - Move cursor
  Space      - Select piece / Confirm move
  Z          - Cancel selection
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


# Piece types
KING = 'K'
QUEEN = 'Q'
ROOK = 'R'
BISHOP = 'B'
KNIGHT = 'N'
PAWN = 'P'

# Colors/sides
WHITE = 'w'
BLACK = 'b'


# Piece sprites (5x5 pixel art for each piece)
# 1 = piece color, 2 = accent/outline
PIECE_SPRITES = {
    KING: [
        '00100',
        '01110',
        '00100',
        '01110',
        '11111',
    ],
    QUEEN: [
        '01010',
        '10101',
        '01110',
        '01110',
        '11111',
    ],
    ROOK: [
        '10101',
        '11111',
        '01110',
        '11111',
        '11111',
    ],
    BISHOP: [
        '00100',
        '01110',
        '01110',
        '00100',
        '01110',
    ],
    KNIGHT: [
        '01100',
        '11110',
        '01110',
        '00110',
        '01111',
    ],
    PAWN: [
        '00000',
        '00100',
        '01110',
        '00100',
        '01110',
    ],
}


class Piece:
    """Represents a chess piece."""

    def __init__(self, piece_type: str, color: str):
        self.type = piece_type
        self.color = color
        self.has_moved = False

    def __repr__(self):
        return f"{self.color}{self.type}"


class Chess(Game):
    name = "CHESS"
    description = "2P Strategy"

    # Board layout
    BOARD_SIZE = 8
    CELL_SIZE = 7  # 7x7 pixels per square (56x56 total board)
    BOARD_OFFSET_X = 4  # Left margin
    BOARD_OFFSET_Y = 8  # Top margin (leaves room for HUD)

    # Colors
    LIGHT_SQUARE = (180, 140, 100)
    DARK_SQUARE = (120, 80, 50)
    WHITE_PIECE = (255, 255, 255)
    BLACK_PIECE = (40, 40, 40)
    CURSOR_COLOR = Colors.CYAN
    SELECTED_COLOR = Colors.YELLOW
    VALID_MOVE_COLOR = (100, 200, 100)
    CHECK_COLOR = Colors.RED
    LAST_MOVE_COLOR = (100, 100, 180)

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
        self.current_turn = WHITE
        self.cursor_x = 4
        self.cursor_y = 6  # Start near white pieces
        self.selected_pos = None  # (x, y) of selected piece
        self.valid_moves = []  # List of valid destination squares

        # Special move tracking
        self.en_passant_target = None  # Square where en passant capture is possible
        self.last_move = None  # ((from_x, from_y), (to_x, to_y))

        # Check state
        self.in_check = False
        self.is_checkmate = False
        self.game_over_reason = ""

        # Pawn promotion
        self.promoting_pawn = None  # (x, y) if a pawn needs promotion
        self.promotion_choice = 0  # Index into promotion options

        # Input timing
        self.move_timer = 0
        self.move_delay = 0.15
        self.last_direction = (0, 0)

    def setup_pieces(self):
        """Set up the initial chess position."""
        # Back rank piece order
        back_rank = [ROOK, KNIGHT, BISHOP, QUEEN, KING, BISHOP, KNIGHT, ROOK]

        # Black pieces (top)
        for x, piece_type in enumerate(back_rank):
            self.board[0][x] = Piece(piece_type, BLACK)
        for x in range(8):
            self.board[1][x] = Piece(PAWN, BLACK)

        # White pieces (bottom)
        for x, piece_type in enumerate(back_rank):
            self.board[7][x] = Piece(piece_type, WHITE)
        for x in range(8):
            self.board[6][x] = Piece(PAWN, WHITE)

    def get_piece(self, x: int, y: int) -> Piece:
        """Get piece at position, or None if empty."""
        if 0 <= x < 8 and 0 <= y < 8:
            return self.board[y][x]
        return None

    def find_king(self, color: str) -> tuple:
        """Find the position of a king."""
        for y in range(8):
            for x in range(8):
                piece = self.board[y][x]
                if piece and piece.type == KING and piece.color == color:
                    return (x, y)
        return None

    def is_square_attacked(self, x: int, y: int, by_color: str) -> bool:
        """Check if a square is attacked by any piece of the given color."""
        for sy in range(8):
            for sx in range(8):
                piece = self.board[sy][sx]
                if piece and piece.color == by_color:
                    moves = self.get_raw_moves(sx, sy, piece)
                    if (x, y) in moves:
                        return True
        return False

    def get_raw_moves(self, x: int, y: int, piece: Piece) -> list:
        """Get all moves for a piece without considering check."""
        moves = []
        color = piece.color
        enemy = BLACK if color == WHITE else WHITE

        if piece.type == PAWN:
            direction = -1 if color == WHITE else 1
            start_row = 6 if color == WHITE else 1

            # Forward move
            if self.get_piece(x, y + direction) is None:
                moves.append((x, y + direction))
                # Double move from start
                if y == start_row and self.get_piece(x, y + 2 * direction) is None:
                    moves.append((x, y + 2 * direction))

            # Captures
            for dx in [-1, 1]:
                nx = x + dx
                ny = y + direction
                target = self.get_piece(nx, ny)
                if target and target.color == enemy:
                    moves.append((nx, ny))
                # En passant
                if self.en_passant_target == (nx, ny):
                    moves.append((nx, ny))

        elif piece.type == KNIGHT:
            knight_moves = [
                (2, 1), (2, -1), (-2, 1), (-2, -1),
                (1, 2), (1, -2), (-1, 2), (-1, -2)
            ]
            for dx, dy in knight_moves:
                nx, ny = x + dx, y + dy
                if 0 <= nx < 8 and 0 <= ny < 8:
                    target = self.get_piece(nx, ny)
                    if target is None or target.color == enemy:
                        moves.append((nx, ny))

        elif piece.type == BISHOP:
            moves.extend(self.get_sliding_moves(x, y, [(1, 1), (1, -1), (-1, 1), (-1, -1)], enemy))

        elif piece.type == ROOK:
            moves.extend(self.get_sliding_moves(x, y, [(1, 0), (-1, 0), (0, 1), (0, -1)], enemy))

        elif piece.type == QUEEN:
            moves.extend(self.get_sliding_moves(x, y, [
                (1, 0), (-1, 0), (0, 1), (0, -1),
                (1, 1), (1, -1), (-1, 1), (-1, -1)
            ], enemy))

        elif piece.type == KING:
            for dx in [-1, 0, 1]:
                for dy in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < 8 and 0 <= ny < 8:
                        target = self.get_piece(nx, ny)
                        if target is None or target.color == enemy:
                            moves.append((nx, ny))

        return moves

    def get_sliding_moves(self, x: int, y: int, directions: list, enemy: str) -> list:
        """Get moves for sliding pieces (bishop, rook, queen)."""
        moves = []
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            while 0 <= nx < 8 and 0 <= ny < 8:
                target = self.get_piece(nx, ny)
                if target is None:
                    moves.append((nx, ny))
                elif target.color == enemy:
                    moves.append((nx, ny))
                    break
                else:
                    break
                nx += dx
                ny += dy
        return moves

    def get_legal_moves(self, x: int, y: int) -> list:
        """Get all legal moves for a piece (considering check)."""
        piece = self.get_piece(x, y)
        if not piece:
            return []

        raw_moves = self.get_raw_moves(x, y, piece)
        legal_moves = []

        for mx, my in raw_moves:
            if self.is_move_legal(x, y, mx, my):
                legal_moves.append((mx, my))

        # Add castling moves for king
        if piece.type == KING and not piece.has_moved:
            legal_moves.extend(self.get_castling_moves(x, y, piece.color))

        return legal_moves

    def get_castling_moves(self, king_x: int, king_y: int, color: str) -> list:
        """Check if castling is possible."""
        moves = []
        enemy = BLACK if color == WHITE else WHITE
        row = 7 if color == WHITE else 0

        if king_y != row or king_x != 4:
            return moves

        # Check if king is in check
        if self.is_square_attacked(king_x, king_y, enemy):
            return moves

        # Kingside castling
        rook = self.get_piece(7, row)
        if rook and rook.type == ROOK and not rook.has_moved:
            # Check squares are empty
            if self.get_piece(5, row) is None and self.get_piece(6, row) is None:
                # Check king doesn't pass through or end in check
                if not self.is_square_attacked(5, row, enemy) and \
                   not self.is_square_attacked(6, row, enemy):
                    moves.append((6, row))

        # Queenside castling
        rook = self.get_piece(0, row)
        if rook and rook.type == ROOK and not rook.has_moved:
            # Check squares are empty
            if self.get_piece(1, row) is None and self.get_piece(2, row) is None and \
               self.get_piece(3, row) is None:
                # Check king doesn't pass through or end in check
                if not self.is_square_attacked(2, row, enemy) and \
                   not self.is_square_attacked(3, row, enemy):
                    moves.append((2, row))

        return moves

    def is_move_legal(self, from_x: int, from_y: int, to_x: int, to_y: int) -> bool:
        """Check if a move is legal (doesn't leave king in check)."""
        piece = self.board[from_y][from_x]
        if not piece:
            return False

        # Simulate the move
        captured = self.board[to_y][to_x]
        en_passant_capture = None

        # Handle en passant capture
        if piece.type == PAWN and (to_x, to_y) == self.en_passant_target:
            ep_y = to_y + (1 if piece.color == WHITE else -1)
            en_passant_capture = self.board[ep_y][to_x]
            self.board[ep_y][to_x] = None

        self.board[to_y][to_x] = piece
        self.board[from_y][from_x] = None

        # Check if own king is in check
        king_pos = self.find_king(piece.color)
        enemy = BLACK if piece.color == WHITE else WHITE
        in_check = self.is_square_attacked(king_pos[0], king_pos[1], enemy)

        # Undo the move
        self.board[from_y][from_x] = piece
        self.board[to_y][to_x] = captured

        if en_passant_capture:
            ep_y = to_y + (1 if piece.color == WHITE else -1)
            self.board[ep_y][to_x] = en_passant_capture

        return not in_check

    def make_move(self, from_x: int, from_y: int, to_x: int, to_y: int):
        """Execute a move on the board."""
        piece = self.board[from_y][from_x]

        # Handle en passant capture
        if piece.type == PAWN and (to_x, to_y) == self.en_passant_target:
            ep_y = to_y + (1 if piece.color == WHITE else -1)
            self.board[ep_y][to_x] = None

        # Update en passant target
        self.en_passant_target = None
        if piece.type == PAWN and abs(to_y - from_y) == 2:
            self.en_passant_target = (to_x, (from_y + to_y) // 2)

        # Handle castling
        if piece.type == KING and abs(to_x - from_x) == 2:
            if to_x == 6:  # Kingside
                rook = self.board[to_y][7]
                self.board[to_y][7] = None
                self.board[to_y][5] = rook
                rook.has_moved = True
            else:  # Queenside
                rook = self.board[to_y][0]
                self.board[to_y][0] = None
                self.board[to_y][3] = rook
                rook.has_moved = True

        # Make the move
        self.board[to_y][to_x] = piece
        self.board[from_y][from_x] = None
        piece.has_moved = True

        # Store last move for highlighting
        self.last_move = ((from_x, from_y), (to_x, to_y))

        # Check for pawn promotion
        promotion_row = 0 if piece.color == WHITE else 7
        if piece.type == PAWN and to_y == promotion_row:
            self.promoting_pawn = (to_x, to_y)
            self.promotion_choice = 0
            return  # Don't switch turns yet

        self.end_turn()

    def end_turn(self):
        """End the current turn and check game state."""
        # Switch turns
        self.current_turn = BLACK if self.current_turn == WHITE else WHITE

        # Check if opponent is in check
        king_pos = self.find_king(self.current_turn)
        enemy = BLACK if self.current_turn == WHITE else WHITE
        self.in_check = self.is_square_attacked(king_pos[0], king_pos[1], enemy)

        # Check for checkmate or stalemate
        has_legal_move = False
        for y in range(8):
            for x in range(8):
                piece = self.board[y][x]
                if piece and piece.color == self.current_turn:
                    if self.get_legal_moves(x, y):
                        has_legal_move = True
                        break
            if has_legal_move:
                break

        if not has_legal_move:
            self.state = GameState.GAME_OVER
            if self.in_check:
                self.is_checkmate = True
                winner = "WHITE" if self.current_turn == BLACK else "BLACK"
                self.game_over_reason = f"{winner} WINS!"
            else:
                self.is_checkmate = False
                self.game_over_reason = "STALEMATE"

    def promote_pawn(self, piece_type: str):
        """Promote a pawn to the chosen piece."""
        x, y = self.promoting_pawn
        piece = self.board[y][x]
        self.board[y][x] = Piece(piece_type, piece.color)
        self.board[y][x].has_moved = True
        self.promoting_pawn = None
        self.end_turn()

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Handle pawn promotion
        if self.promoting_pawn:
            promotion_pieces = [QUEEN, ROOK, BISHOP, KNIGHT]

            if input_state.left:
                self.promotion_choice = (self.promotion_choice - 1) % 4
            elif input_state.right:
                self.promotion_choice = (self.promotion_choice + 1) % 4
            elif input_state.action:
                self.promote_pawn(promotion_pieces[self.promotion_choice])
            return

        # Cursor movement with repeat delay
        dx, dy = input_state.dx, input_state.dy

        if (dx, dy) != (0, 0):
            if (dx, dy) != self.last_direction:
                # New direction - move immediately
                self.cursor_x = max(0, min(7, self.cursor_x + dx))
                self.cursor_y = max(0, min(7, self.cursor_y + dy))
                self.move_timer = 0
                self.last_direction = (dx, dy)
            else:
                # Same direction - use repeat delay
                self.move_timer += dt
                if self.move_timer >= self.move_delay:
                    self.cursor_x = max(0, min(7, self.cursor_x + dx))
                    self.cursor_y = max(0, min(7, self.cursor_y + dy))
                    self.move_timer = 0
        else:
            self.last_direction = (0, 0)
            self.move_timer = 0

        # Cancel selection
        if input_state.secondary:
            self.selected_pos = None
            self.valid_moves = []

        # Select piece or make move
        if input_state.action:
            cursor_pos = (self.cursor_x, self.cursor_y)

            if self.selected_pos is None:
                # Try to select a piece
                piece = self.get_piece(self.cursor_x, self.cursor_y)
                if piece and piece.color == self.current_turn:
                    moves = self.get_legal_moves(self.cursor_x, self.cursor_y)
                    if moves:
                        self.selected_pos = cursor_pos
                        self.valid_moves = moves
            else:
                # Try to make a move
                if cursor_pos in self.valid_moves:
                    self.make_move(
                        self.selected_pos[0], self.selected_pos[1],
                        self.cursor_x, self.cursor_y
                    )
                    self.selected_pos = None
                    self.valid_moves = []
                elif cursor_pos == self.selected_pos:
                    # Clicking same square deselects
                    self.selected_pos = None
                    self.valid_moves = []
                else:
                    # Try to select a different piece
                    piece = self.get_piece(self.cursor_x, self.cursor_y)
                    if piece and piece.color == self.current_turn:
                        moves = self.get_legal_moves(self.cursor_x, self.cursor_y)
                        if moves:
                            self.selected_pos = cursor_pos
                            self.valid_moves = moves
                        else:
                            self.selected_pos = None
                            self.valid_moves = []
                    else:
                        self.selected_pos = None
                        self.valid_moves = []

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        turn_text = "WHITE" if self.current_turn == WHITE else "BLACK"
        turn_color = Colors.WHITE if self.current_turn == WHITE else Colors.GRAY
        self.display.draw_text_small(1, 1, turn_text, turn_color)

        if self.in_check:
            self.display.draw_text_small(32, 1, "CHECK", Colors.RED)

        # Draw board
        for y in range(8):
            for x in range(8):
                self.draw_square(x, y)

        # Draw pawn promotion UI
        if self.promoting_pawn:
            self.draw_promotion_ui()

    def draw_square(self, x: int, y: int):
        """Draw a single board square with piece."""
        px = self.BOARD_OFFSET_X + x * self.CELL_SIZE
        py = self.BOARD_OFFSET_Y + y * self.CELL_SIZE

        # Base square color
        is_light = (x + y) % 2 == 0
        base_color = self.LIGHT_SQUARE if is_light else self.DARK_SQUARE

        # Apply highlighting
        color = base_color

        # Last move highlight
        if self.last_move:
            if (x, y) in self.last_move:
                color = self.blend_colors(color, self.LAST_MOVE_COLOR, 0.4)

        # Valid move highlight
        if (x, y) in self.valid_moves:
            color = self.blend_colors(color, self.VALID_MOVE_COLOR, 0.5)

        # Check highlight on king
        if self.in_check:
            piece = self.get_piece(x, y)
            if piece and piece.type == KING and piece.color == self.current_turn:
                color = self.blend_colors(color, self.CHECK_COLOR, 0.6)

        # Draw the square
        self.display.draw_rect(px, py, self.CELL_SIZE, self.CELL_SIZE, color)

        # Selected square border
        if self.selected_pos == (x, y):
            self.display.draw_rect(px, py, self.CELL_SIZE, self.CELL_SIZE,
                                   self.SELECTED_COLOR, filled=False)

        # Draw piece
        piece = self.get_piece(x, y)
        if piece:
            self.draw_piece(px + 1, py + 1, piece)

        # Draw valid move indicator (dot for empty, corner for capture)
        if (x, y) in self.valid_moves:
            if piece:
                # Capture indicator - corners
                corner_color = self.VALID_MOVE_COLOR
                self.display.set_pixel(px, py, corner_color)
                self.display.set_pixel(px + self.CELL_SIZE - 1, py, corner_color)
                self.display.set_pixel(px, py + self.CELL_SIZE - 1, corner_color)
                self.display.set_pixel(px + self.CELL_SIZE - 1, py + self.CELL_SIZE - 1, corner_color)
            else:
                # Empty square indicator - center dot
                cx = px + self.CELL_SIZE // 2
                cy = py + self.CELL_SIZE // 2
                self.display.set_pixel(cx, cy, self.VALID_MOVE_COLOR)

        # Cursor
        if (x, y) == (self.cursor_x, self.cursor_y):
            self.draw_cursor(px, py)

    def draw_piece(self, x: int, y: int, piece: Piece):
        """Draw a chess piece sprite."""
        sprite = PIECE_SPRITES[piece.type]
        color = self.WHITE_PIECE if piece.color == WHITE else self.BLACK_PIECE
        outline = self.BLACK_PIECE if piece.color == WHITE else self.WHITE_PIECE

        for row_idx, row in enumerate(sprite):
            for col_idx, pixel in enumerate(row):
                if pixel == '1':
                    self.display.set_pixel(x + col_idx, y + row_idx, color)

    def draw_cursor(self, px: int, py: int):
        """Draw the cursor around a square."""
        c = self.CURSOR_COLOR
        size = self.CELL_SIZE

        # Draw corners of cursor
        # Top-left
        self.display.set_pixel(px, py, c)
        self.display.set_pixel(px + 1, py, c)
        self.display.set_pixel(px, py + 1, c)

        # Top-right
        self.display.set_pixel(px + size - 1, py, c)
        self.display.set_pixel(px + size - 2, py, c)
        self.display.set_pixel(px + size - 1, py + 1, c)

        # Bottom-left
        self.display.set_pixel(px, py + size - 1, c)
        self.display.set_pixel(px + 1, py + size - 1, c)
        self.display.set_pixel(px, py + size - 2, c)

        # Bottom-right
        self.display.set_pixel(px + size - 1, py + size - 1, c)
        self.display.set_pixel(px + size - 2, py + size - 1, c)
        self.display.set_pixel(px + size - 1, py + size - 2, c)

    def draw_promotion_ui(self):
        """Draw pawn promotion selection UI."""
        # Semi-transparent overlay
        for y in range(20, 44):
            for x in range(8, 56):
                current = self.display.get_pixel(x, y)
                dimmed = (current[0] // 3, current[1] // 3, current[2] // 3)
                self.display.set_pixel(x, y, dimmed)

        # Title
        self.display.draw_text_small(12, 22, "PROMOTE", Colors.WHITE)

        # Options
        promotion_pieces = [QUEEN, ROOK, BISHOP, KNIGHT]
        piece_color = WHITE if self.current_turn == BLACK else BLACK  # Piece that's promoting
        # Wait - the pawn that's promoting belongs to the player who just moved
        # After make_move we haven't switched turns yet during promotion
        promoting_color = WHITE if self.current_turn == WHITE else BLACK

        for i, piece_type in enumerate(promotion_pieces):
            px = 12 + i * 11
            py = 32

            # Highlight selected
            if i == self.promotion_choice:
                self.display.draw_rect(px - 1, py - 1, 9, 9, Colors.YELLOW, filled=False)

            # Draw piece
            temp_piece = Piece(piece_type, promoting_color)
            self.draw_piece(px + 1, py + 1, temp_piece)

    def blend_colors(self, c1: tuple, c2: tuple, factor: float) -> tuple:
        """Blend two colors together."""
        return (
            int(c1[0] * (1 - factor) + c2[0] * factor),
            int(c1[1] * (1 - factor) + c2[1] * factor),
            int(c1[2] * (1 - factor) + c2[2] * factor),
        )

    def draw_game_over(self):
        """Draw game over/win screen."""
        self.display.clear(Colors.BLACK)

        if self.is_checkmate:
            self.display.draw_text_small(4, 20, "CHECKMATE!", Colors.YELLOW)
            self.display.draw_text_small(4, 32, self.game_over_reason, Colors.WHITE)
        else:
            self.display.draw_text_small(4, 20, "DRAW", Colors.GRAY)
            self.display.draw_text_small(4, 32, self.game_over_reason, Colors.WHITE)

        self.display.draw_text_small(4, 50, "SPACE:AGAIN", Colors.GRAY)

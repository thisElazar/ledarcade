"""
Tetris - The classic puzzle game
================================
Stack the falling blocks and clear lines!

Controls:
  Left/Right - Move piece
  Up         - Rotate piece
  Down       - Soft drop (faster fall)
  Space      - Hard drop (instant drop)
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


# Tetromino shapes (each rotation state)
TETROMINOS = {
    'I': [
        [(0, 1), (1, 1), (2, 1), (3, 1)],
        [(2, 0), (2, 1), (2, 2), (2, 3)],
        [(0, 2), (1, 2), (2, 2), (3, 2)],
        [(1, 0), (1, 1), (1, 2), (1, 3)],
    ],
    'O': [
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (2, 1)],
    ],
    'T': [
        [(1, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (1, 2)],
        [(1, 0), (0, 1), (1, 1), (1, 2)],
    ],
    'S': [
        [(1, 0), (2, 0), (0, 1), (1, 1)],
        [(1, 0), (1, 1), (2, 1), (2, 2)],
        [(1, 1), (2, 1), (0, 2), (1, 2)],
        [(0, 0), (0, 1), (1, 1), (1, 2)],
    ],
    'Z': [
        [(0, 0), (1, 0), (1, 1), (2, 1)],
        [(2, 0), (1, 1), (2, 1), (1, 2)],
        [(0, 1), (1, 1), (1, 2), (2, 2)],
        [(1, 0), (0, 1), (1, 1), (0, 2)],
    ],
    'J': [
        [(0, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (2, 0), (1, 1), (1, 2)],
        [(0, 1), (1, 1), (2, 1), (2, 2)],
        [(1, 0), (1, 1), (0, 2), (1, 2)],
    ],
    'L': [
        [(2, 0), (0, 1), (1, 1), (2, 1)],
        [(1, 0), (1, 1), (1, 2), (2, 2)],
        [(0, 1), (1, 1), (2, 1), (0, 2)],
        [(0, 0), (1, 0), (1, 1), (1, 2)],
    ],
}

TETROMINO_COLORS = {
    'I': Colors.CYAN,
    'O': Colors.YELLOW,
    'T': Colors.MAGENTA,
    'S': Colors.GREEN,
    'Z': Colors.RED,
    'J': Colors.BLUE,
    'L': Colors.ORANGE,
}


class Tetris(Game):
    name = "TETRIS"
    description = "Clear lines!"
    category = "arcade"

    # Playfield dimensions (standard Tetris is 10 wide, 20 tall)
    BOARD_WIDTH = 10
    BOARD_HEIGHT = 20

    def __init__(self, display: Display):
        super().__init__(display)

        # Board uses 3x3 cells for max visibility (30x60 pixels)
        self.cell_size = 3
        # Center the board horizontally: (64 - 30) / 2 = 17
        self.board_x = 17
        # Start at y=2 for 60px tall board (rows 2-61)
        self.board_y = 2

        self.reset()
    
    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lines = 0
        self.level = 1
        
        # Board (0 = empty, otherwise color tuple)
        self.board = [[None for _ in range(self.BOARD_WIDTH)] for _ in range(self.BOARD_HEIGHT)]
        
        # Current piece
        self.current_piece = None
        self.current_rotation = 0
        self.piece_x = 0
        self.piece_y = 0
        
        # Next piece
        self.next_piece = random.choice(list(TETROMINOS.keys()))
        
        # Spawn first piece
        self.spawn_piece()
        
        # Timing
        self.fall_timer = 0
        self.fall_delay = 0.8  # Seconds per drop
        self.move_timer = 0
        self.move_delay = 0.1  # Seconds between auto-repeat moves
        self.lock_timer = 0
        self.lock_delay = 0.5  # Seconds before locking
        
        # Input handling
        self.das_timer = 0  # Delayed auto-shift
        self.das_delay = 0.15
        self.das_direction = 0
        
        # Effects
        self.line_clear_rows = []
        self.line_clear_timer = 0
    
    def spawn_piece(self):
        """Spawn a new piece at the top."""
        self.current_piece = self.next_piece
        self.next_piece = random.choice(list(TETROMINOS.keys()))
        self.current_rotation = 0
        self.piece_x = self.BOARD_WIDTH // 2 - 2
        self.piece_y = 0
        self.lock_timer = 0
        
        # Check if spawn position is blocked (game over)
        if self.check_collision():
            self.state = GameState.GAME_OVER
    
    def get_piece_blocks(self):
        """Get the current piece's block positions."""
        shape = TETROMINOS[self.current_piece][self.current_rotation]
        return [(self.piece_x + dx, self.piece_y + dy) for dx, dy in shape]
    
    def check_collision(self, dx=0, dy=0, rotation=None):
        """Check if piece would collide at offset position."""
        if rotation is None:
            rotation = self.current_rotation
        
        shape = TETROMINOS[self.current_piece][rotation]
        
        for block_dx, block_dy in shape:
            x = self.piece_x + block_dx + dx
            y = self.piece_y + block_dy + dy
            
            # Check bounds
            if x < 0 or x >= self.BOARD_WIDTH:
                return True
            if y >= self.BOARD_HEIGHT:
                return True
            
            # Check board collision (only if y >= 0)
            if y >= 0 and self.board[y][x] is not None:
                return True
        
        return False
    
    def lock_piece(self):
        """Lock the current piece in place."""
        color = TETROMINO_COLORS[self.current_piece]
        
        for x, y in self.get_piece_blocks():
            if 0 <= y < self.BOARD_HEIGHT:
                self.board[y][x] = color
        
        # Check for line clears
        self.check_lines()
        
        # Spawn next piece
        self.spawn_piece()
    
    def check_lines(self):
        """Check for and clear completed lines."""
        lines_to_clear = []
        
        for y in range(self.BOARD_HEIGHT):
            if all(self.board[y][x] is not None for x in range(self.BOARD_WIDTH)):
                lines_to_clear.append(y)
        
        if lines_to_clear:
            self.line_clear_rows = lines_to_clear
            self.line_clear_timer = 0.3
            
            # Scoring
            line_scores = [0, 100, 300, 500, 800]  # 0, 1, 2, 3, 4 lines
            self.score += line_scores[len(lines_to_clear)] * self.level
            self.lines += len(lines_to_clear)
            
            # Level up every 10 lines
            self.level = self.lines // 10 + 1
            self.fall_delay = max(0.1, 0.8 - (self.level - 1) * 0.07)
    
    def clear_lines(self):
        """Actually remove the cleared lines."""
        for y in sorted(self.line_clear_rows, reverse=True):
            del self.board[y]
            self.board.insert(0, [None for _ in range(self.BOARD_WIDTH)])
        
        self.line_clear_rows = []
    
    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Handle line clear animation
        if self.line_clear_timer > 0:
            self.line_clear_timer -= dt
            if self.line_clear_timer <= 0:
                self.clear_lines()
            return
        
        # Horizontal movement with DAS (Delayed Auto-Shift)
        move_dx = 0
        if input_state.left:
            if self.das_direction != -1:
                self.das_direction = -1
                self.das_timer = 0
                move_dx = -1
            else:
                self.das_timer += dt
                if self.das_timer >= self.das_delay:
                    self.move_timer += dt
                    if self.move_timer >= self.move_delay:
                        self.move_timer = 0
                        move_dx = -1
        elif input_state.right:
            if self.das_direction != 1:
                self.das_direction = 1
                self.das_timer = 0
                move_dx = 1
            else:
                self.das_timer += dt
                if self.das_timer >= self.das_delay:
                    self.move_timer += dt
                    if self.move_timer >= self.move_delay:
                        self.move_timer = 0
                        move_dx = 1
        else:
            self.das_direction = 0
            self.das_timer = 0
        
        if move_dx != 0 and not self.check_collision(dx=move_dx):
            self.piece_x += move_dx
            self.lock_timer = 0  # Reset lock delay on movement
        
        # Rotation (Up only)
        if input_state.up:
            new_rotation = (self.current_rotation + 1) % 4
            if not self.check_collision(rotation=new_rotation):
                self.current_rotation = new_rotation
                self.lock_timer = 0
            # Try wall kicks
            elif not self.check_collision(dx=-1, rotation=new_rotation):
                self.piece_x -= 1
                self.current_rotation = new_rotation
                self.lock_timer = 0
            elif not self.check_collision(dx=1, rotation=new_rotation):
                self.piece_x += 1
                self.current_rotation = new_rotation
                self.lock_timer = 0

        # Hard drop (Action button)
        if (input_state.action_l or input_state.action_r):
            while not self.check_collision(dy=1):
                self.piece_y += 1
                self.score += 2
            self.lock_piece()
            return

        # Soft drop (Down held = faster fall)
        drop_delay = self.fall_delay / 10 if input_state.down else self.fall_delay
        
        # Gravity
        self.fall_timer += dt
        if self.fall_timer >= drop_delay:
            self.fall_timer = 0

            if not self.check_collision(dy=1):
                self.piece_y += 1
                if input_state.down:
                    self.score += 1  # Bonus for soft drop
                self.lock_timer = 0
            else:
                # Piece is resting - start lock timer
                self.lock_timer += dt + drop_delay
                if self.lock_timer >= self.lock_delay:
                    self.lock_piece()
    
    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw board border
        bx, by = self.board_x, self.board_y
        bw = self.BOARD_WIDTH * self.cell_size
        bh = self.BOARD_HEIGHT * self.cell_size

        self.display.draw_rect(bx - 1, by - 1, bw + 2, bh + 2, Colors.DARK_GRAY, filled=False)

        # Draw board contents
        for y in range(self.BOARD_HEIGHT):
            for x in range(self.BOARD_WIDTH):
                if self.board[y][x] is not None:
                    color = self.board[y][x]
                    px = bx + x * self.cell_size
                    py = by + y * self.cell_size
                    self.display.draw_rect(px, py, self.cell_size, self.cell_size, color)

        # Draw line clear effect
        if self.line_clear_rows:
            flash = int(self.line_clear_timer * 10) % 2 == 0
            for y in self.line_clear_rows:
                py = by + y * self.cell_size
                color = Colors.WHITE if flash else Colors.BLACK
                self.display.draw_rect(bx, py, bw, self.cell_size, color)

        # Draw current piece
        if self.current_piece and not self.line_clear_rows:
            color = TETROMINO_COLORS[self.current_piece]

            # Draw ghost piece (where it will land)
            ghost_y = self.piece_y
            while not self.check_collision(dy=ghost_y - self.piece_y + 1):
                ghost_y += 1

            ghost_color = (color[0] // 4, color[1] // 4, color[2] // 4)
            shape = TETROMINOS[self.current_piece][self.current_rotation]
            for block_dx, block_dy in shape:
                x = self.piece_x + block_dx
                y = ghost_y + block_dy
                if y >= 0:
                    px = bx + x * self.cell_size
                    py = by + y * self.cell_size
                    self.display.draw_rect(px, py, self.cell_size, self.cell_size, ghost_color)

            # Draw actual piece
            for x, y in self.get_piece_blocks():
                if y >= 0:
                    px = bx + x * self.cell_size
                    py = by + y * self.cell_size
                    self.display.draw_rect(px, py, self.cell_size, self.cell_size, color)

        # LEFT SIDE INFO (x 0-15)
        # Score
        self.display.draw_text_small(1, 2, "SC", Colors.GRAY)
        score_str = str(self.score)
        # Stack score digits vertically if needed
        if self.score < 1000:
            self.display.draw_text_small(1, 10, score_str, Colors.WHITE)
        else:
            # Show abbreviated score
            self.display.draw_text_small(1, 10, f"{self.score // 1000}K", Colors.WHITE)

        # Level
        self.display.draw_text_small(1, 26, "LV", Colors.GRAY)
        self.display.draw_text_small(1, 34, f"{self.level}", Colors.CYAN)

        # Lines
        self.display.draw_text_small(1, 50, "LN", Colors.GRAY)
        self.display.draw_text_small(1, 58, f"{self.lines}", Colors.WHITE)

        # RIGHT SIDE INFO (x 48-63)
        # Next piece preview
        self.display.draw_text_small(49, 2, "NX", Colors.GRAY)

        if self.next_piece:
            color = TETROMINO_COLORS[self.next_piece]
            shape = TETROMINOS[self.next_piece][0]
            # Draw next piece with 2px cells to fit in side panel
            for block_dx, block_dy in shape:
                px = 49 + block_dx * 2
                py = 12 + block_dy * 2
                self.display.draw_rect(px, py, 2, 2, color)
    
    def draw_game_over(self):
        """Custom game over for Tetris."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(2, 15, "GAME OVER", Colors.RED)
        self.display.draw_text_small(2, 28, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(2, 38, f"LINES:{self.lines}", Colors.CYAN)
        self.display.draw_text_small(2, 52, "SPACE:RETRY", Colors.GRAY)

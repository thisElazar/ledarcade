"""
2048 - Sliding Tile Puzzle
===========================
Slide tiles to combine them and reach 2048!

Controls:
  Arrow Keys - Slide all tiles in that direction
  Space      - Restart (when game over)
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import random


class Game2048(Game):
    name = "2048"
    description = "Slide & Merge"
    category = "modern"

    # Grid layout - sized to fit 64x64 with HUD
    GRID_SIZE_TILES = 4
    CELL_SIZE = 11  # 11x11 per cell
    GAP = 1
    BOARD_SIZE = CELL_SIZE * GRID_SIZE_TILES + GAP * (GRID_SIZE_TILES + 1)  # 49
    BOARD_X = (GRID_SIZE - BOARD_SIZE) // 2  # 7
    BOARD_Y = 8  # Below HUD

    # Colors for each tile value (bold saturated for LED matrix)
    TILE_COLORS = {
        0: (20, 20, 30),       # Empty (dark)
        2: (80, 80, 100),      # Cool gray
        4: (60, 100, 140),     # Steel blue
        8: (220, 140, 30),     # Orange
        16: (240, 100, 30),    # Dark orange
        32: (220, 50, 50),     # Red
        64: (200, 30, 30),     # Deep red
        128: (240, 220, 50),   # Bright yellow
        256: (50, 200, 50),    # Green
        512: (30, 160, 220),   # Sky blue
        1024: (180, 50, 220),  # Purple
        2048: (255, 255, 100), # Gold
    }

    TEXT_DARK = (255, 255, 255)
    TEXT_LIGHT = (255, 255, 255)
    BOARD_BG = (40, 40, 50)

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.best_score = 0

        # 4x4 grid of tile values (0 = empty)
        self.grid = [[0] * 4 for _ in range(4)]

        # Spawn initial tiles
        self.spawn_tile()
        self.spawn_tile()

        # Animation state
        self.animating = False
        self.anim_timer = 0
        self.anim_duration = 0.1

        # Track if move was made (for spawning new tile)
        self.moved = False

        # Win state
        self.won = False
        self.game_over = False

        # Input cooldown
        self.input_cooldown = 0

    def spawn_tile(self):
        """Spawn a new tile (90% chance of 2, 10% chance of 4)."""
        empty = [(r, c) for r in range(4) for c in range(4) if self.grid[r][c] == 0]
        if empty:
            r, c = random.choice(empty)
            self.grid[r][c] = 2 if random.random() < 0.9 else 4

    def slide_row_left(self, row: list) -> tuple:
        """Slide a row left and merge. Returns (new_row, score_gained, moved)."""
        # Remove zeros
        tiles = [t for t in row if t != 0]
        score = 0
        moved = tiles != [t for t in row if t != 0] or len(tiles) != len([t for t in row if t != 0])

        # Merge adjacent equal tiles
        merged = []
        skip = False
        for i in range(len(tiles)):
            if skip:
                skip = False
                continue
            if i + 1 < len(tiles) and tiles[i] == tiles[i + 1]:
                merged.append(tiles[i] * 2)
                score += tiles[i] * 2
                skip = True
            else:
                merged.append(tiles[i])

        # Pad with zeros
        result = merged + [0] * (4 - len(merged))

        # Check if anything moved
        moved = result != row

        return result, score, moved

    def move(self, direction: str) -> bool:
        """Execute a move in the given direction. Returns True if anything moved."""
        moved = False
        total_score = 0

        if direction == 'left':
            for r in range(4):
                new_row, score, row_moved = self.slide_row_left(self.grid[r])
                if row_moved:
                    self.grid[r] = new_row
                    moved = True
                    total_score += score

        elif direction == 'right':
            for r in range(4):
                reversed_row = self.grid[r][::-1]
                new_row, score, row_moved = self.slide_row_left(reversed_row)
                if row_moved:
                    self.grid[r] = new_row[::-1]
                    moved = True
                    total_score += score

        elif direction == 'up':
            for c in range(4):
                col = [self.grid[r][c] for r in range(4)]
                new_col, score, col_moved = self.slide_row_left(col)
                if col_moved:
                    for r in range(4):
                        self.grid[r][c] = new_col[r]
                    moved = True
                    total_score += score

        elif direction == 'down':
            for c in range(4):
                col = [self.grid[r][c] for r in range(3, -1, -1)]
                new_col, score, col_moved = self.slide_row_left(col)
                if col_moved:
                    for r in range(4):
                        self.grid[3 - r][c] = new_col[r]
                    moved = True
                    total_score += score

        self.score += total_score
        if self.score > self.best_score:
            self.best_score = self.score

        return moved

    def check_win(self):
        """Check if player has won (reached 2048)."""
        for row in self.grid:
            if 2048 in row:
                return True
        return False

    def check_game_over(self):
        """Check if no moves are possible."""
        # Check for empty cells
        for row in self.grid:
            if 0 in row:
                return False

        # Check for possible merges
        for r in range(4):
            for c in range(4):
                val = self.grid[r][c]
                # Check right
                if c < 3 and self.grid[r][c + 1] == val:
                    return False
                # Check down
                if r < 3 and self.grid[r + 1][c] == val:
                    return False

        return True

    def update(self, input_state: InputState, dt: float):
        # Handle animation
        if self.animating:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_duration:
                self.animating = False
                if self.moved:
                    self.spawn_tile()
                    self.moved = False

                    # Check win/lose
                    if self.check_win() and not self.won:
                        self.won = True
                    if self.check_game_over():
                        self.game_over = True
                        self.state = GameState.GAME_OVER
            return

        # Input cooldown
        if self.input_cooldown > 0:
            self.input_cooldown -= dt
            return

        if self.state == GameState.GAME_OVER:
            if (input_state.action_l or input_state.action_r):
                self.reset()
            return

        # Handle movement
        direction = None
        if input_state.left:
            direction = 'left'
        elif input_state.right:
            direction = 'right'
        elif input_state.up:
            direction = 'up'
        elif input_state.down:
            direction = 'down'

        if direction:
            self.moved = self.move(direction)
            if self.moved:
                self.animating = True
                self.anim_timer = 0
            self.input_cooldown = 0.15

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw score at top
        self.draw_score()

        # Draw board background
        self.display.draw_rect(
            self.BOARD_X, self.BOARD_Y,
            self.BOARD_SIZE, self.BOARD_SIZE,
            self.BOARD_BG
        )

        # Draw tiles
        for r in range(4):
            for c in range(4):
                self.draw_tile(r, c)

        # Draw win message
        if self.won and self.state == GameState.PLAYING:
            self.display.draw_text_small(16, 28, "WIN!", Colors.YELLOW)

        # Draw game over
        if self.state == GameState.GAME_OVER:
            self.draw_game_over()

    def draw_score(self):
        """Draw score at top."""
        score_str = str(self.score)
        if self.score > 9999:
            score_str = f"{self.score // 1000}K"
        self.display.draw_text_small(1, 1, score_str, Colors.WHITE)

    def draw_tile(self, row: int, col: int):
        """Draw a single tile."""
        value = self.grid[row][col]

        x = self.BOARD_X + self.GAP + col * (self.CELL_SIZE + self.GAP)
        y = self.BOARD_Y + self.GAP + row * (self.CELL_SIZE + self.GAP)

        # Get tile color
        color = self.TILE_COLORS.get(value, self.TILE_COLORS[2048])

        # Draw tile background
        self.display.draw_rect(x, y, self.CELL_SIZE, self.CELL_SIZE, color)

        # Draw value
        if value > 0:
            text_color = self.TEXT_DARK if value < 8 else self.TEXT_LIGHT
            self.draw_tile_value(x, y, value, text_color)

    def draw_tile_value(self, x: int, y: int, value: int, color: tuple):
        """Draw the numeric value on a tile."""
        # Center the text in the tile
        text = str(value)

        # Calculate text width (approximately 4 pixels per character)
        text_width = len(text) * 4
        text_x = x + (self.CELL_SIZE - text_width) // 2
        text_y = y + (self.CELL_SIZE - 5) // 2  # 5 is font height

        # For large numbers, use smaller positioning
        if value >= 1000:
            # Draw abbreviated
            if value >= 1024:
                text = "1K" if value == 1024 else "2K"
            text_width = len(text) * 4
            text_x = x + (self.CELL_SIZE - text_width) // 2

        self.display.draw_text_small(text_x, text_y, text, color)

    def draw_game_over(self):
        """Draw game over overlay."""
        # Semi-dim the board
        self.display.draw_text_small(8, 26, "GAME OVER", Colors.RED)
        self.display.draw_text_small(8, 38, f"SCORE:{self.score}", Colors.WHITE)

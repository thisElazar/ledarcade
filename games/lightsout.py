"""
Lights Out - Puzzle Game
=========================
Toggle lights to turn them all off!
Toggling a light also toggles its neighbors.

Controls:
  Arrow Keys - Move cursor
  Space      - Toggle light (and adjacent lights)
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import random


class LightsOut(Game):
    name = "LIGHTS OUT"
    description = "1995 Tiger Electronics"
    category = "toys"

    # Grid layout
    GRID_CELLS = 5
    CELL_SIZE = 10  # 10x10 per cell
    GAP = 2
    BOARD_SIZE = CELL_SIZE * GRID_CELLS + GAP * (GRID_CELLS + 1)  # 62
    BOARD_X = (GRID_SIZE - BOARD_SIZE) // 2
    BOARD_Y = (GRID_SIZE - BOARD_SIZE) // 2 + 4  # Offset down for HUD

    # Colors
    LIGHT_ON = (255, 255, 100)   # Bright yellow
    LIGHT_OFF = (40, 40, 50)     # Dark gray
    BOARD_BG = (0, 0, 0)         # True black
    CURSOR_COLOR = Colors.CYAN

    def __init__(self, display: Display):
        super().__init__(display)
        self.high_score = 0
        self.best_level = 0
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # 5x5 grid of lights (True = on, False = off)
        self.grid = [[False] * 5 for _ in range(5)]

        # Game state
        self.cursor_x = 2
        self.cursor_y = 2
        self.moves = 0
        self.level = 1

        # Generate a solvable puzzle by working backwards
        self.generate_puzzle()

        # Animation
        self.toggle_flash = 0
        self.flash_cells = []

        # Input timing
        self.move_timer = 0
        self.move_delay = 0.12
        self.last_direction = (0, 0)

    def generate_puzzle(self, num_toggles: int = None):
        """Generate a solvable puzzle by making random toggles."""
        if num_toggles is None:
            num_toggles = 5 + self.level * 2  # More toggles = harder

        # Start with all lights off
        self.grid = [[False] * 5 for _ in range(5)]

        # Make random toggles to create puzzle
        for _ in range(num_toggles):
            r = random.randint(0, 4)
            c = random.randint(0, 4)
            self.toggle(c, r, animate=False)

        # Make sure at least some lights are on
        total_on = sum(sum(row) for row in self.grid)
        if total_on < 3:
            self.generate_puzzle(num_toggles)

    def toggle(self, col: int, row: int, animate: bool = True):
        """Toggle a light and its neighbors."""
        cells = [(col, row)]

        # Add neighbors
        if col > 0:
            cells.append((col - 1, row))
        if col < 4:
            cells.append((col + 1, row))
        if row > 0:
            cells.append((col, row - 1))
        if row < 4:
            cells.append((col, row + 1))

        # Toggle all
        for c, r in cells:
            self.grid[r][c] = not self.grid[r][c]

        if animate:
            self.flash_cells = cells
            self.toggle_flash = 0.15

    def check_win(self) -> bool:
        """Check if all lights are off."""
        return all(not light for row in self.grid for light in row)

    def count_lights_on(self) -> int:
        """Count how many lights are on."""
        return sum(sum(row) for row in self.grid)

    def next_level(self):
        """Advance to next level."""
        self.level += 1
        self.moves = 0
        self.generate_puzzle()

    def update(self, input_state: InputState, dt: float):
        # Update flash animation
        if self.toggle_flash > 0:
            self.toggle_flash -= dt
            if self.toggle_flash <= 0:
                self.flash_cells = []

        if self.state == GameState.GAME_OVER:
            # Won - press space for next level
            if (input_state.action_l or input_state.action_r):
                self.next_level()
                self.state = GameState.PLAYING
            return

        # Cursor movement
        dx, dy = input_state.dx, input_state.dy

        if (dx, dy) != (0, 0):
            if (dx, dy) != self.last_direction:
                self.cursor_x = max(0, min(4, self.cursor_x + dx))
                self.cursor_y = max(0, min(4, self.cursor_y + dy))
                self.move_timer = 0
                self.last_direction = (dx, dy)
            else:
                self.move_timer += dt
                if self.move_timer >= self.move_delay:
                    self.cursor_x = max(0, min(4, self.cursor_x + dx))
                    self.cursor_y = max(0, min(4, self.cursor_y + dy))
                    self.move_timer = 0
        else:
            self.last_direction = (0, 0)
            self.move_timer = 0

        # Toggle light
        if (input_state.action_l or input_state.action_r) and self.toggle_flash <= 0:
            self.toggle(self.cursor_x, self.cursor_y)
            self.moves += 1

            if self.check_win():
                self.score += max(1, 100 - self.moves * 5)  # Bonus for fewer moves
                self.high_score = max(self.high_score, self.score)
                self.best_level = max(self.best_level, self.level)
                self.state = GameState.GAME_OVER

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw HUD
        self.draw_hud()

        # Draw board background
        self.display.draw_rect(
            self.BOARD_X, self.BOARD_Y,
            self.BOARD_SIZE, self.BOARD_SIZE,
            self.BOARD_BG
        )

        # Draw lights
        for r in range(5):
            for c in range(5):
                self.draw_light(c, r)

        # Draw cursor
        self.draw_cursor()

        # Win message
        if self.state == GameState.GAME_OVER:
            self.draw_win()

    def draw_hud(self):
        """Draw level, moves, and lights remaining."""
        self.display.draw_text_small(1, 1, f"L{self.level}", Colors.YELLOW)
        self.display.draw_text_small(20, 1, f"M:{self.moves}", Colors.WHITE)

        lights_on = self.count_lights_on()
        self.display.draw_text_small(44, 1, f"{lights_on}", self.LIGHT_ON if lights_on > 0 else Colors.GREEN)

        # Show best level at bottom if achieved
        if self.best_level > 0:
            self.display.draw_text_small(2, 57, f"BEST:L{self.best_level}", Colors.GRAY)

    def draw_light(self, col: int, row: int):
        """Draw a single light."""
        x = self.BOARD_X + self.GAP + col * (self.CELL_SIZE + self.GAP)
        y = self.BOARD_Y + self.GAP + row * (self.CELL_SIZE + self.GAP)

        is_on = self.grid[row][col]

        # Check if this cell is flashing
        is_flashing = (col, row) in self.flash_cells

        if is_flashing:
            # Flash white briefly
            color = Colors.WHITE
        elif is_on:
            color = self.LIGHT_ON
        else:
            color = self.LIGHT_OFF

        # Draw light
        self.display.draw_rect(x, y, self.CELL_SIZE, self.CELL_SIZE, color)

        # Add subtle gradient/glow effect for on lights
        if is_on and not is_flashing:
            # Brighter center
            cx = x + self.CELL_SIZE // 2
            cy = y + self.CELL_SIZE // 2
            self.display.set_pixel(cx, cy, (255, 255, 200))
            self.display.set_pixel(cx - 1, cy, (255, 255, 180))
            self.display.set_pixel(cx + 1, cy, (255, 255, 180))
            self.display.set_pixel(cx, cy - 1, (255, 255, 180))
            self.display.set_pixel(cx, cy + 1, (255, 255, 180))

    def draw_cursor(self):
        """Draw cursor around selected light."""
        x = self.BOARD_X + self.GAP + self.cursor_x * (self.CELL_SIZE + self.GAP)
        y = self.BOARD_Y + self.GAP + self.cursor_y * (self.CELL_SIZE + self.GAP)
        size = self.CELL_SIZE

        c = self.CURSOR_COLOR

        # Draw corners
        # Top-left
        self.display.set_pixel(x - 1, y - 1, c)
        self.display.set_pixel(x, y - 1, c)
        self.display.set_pixel(x - 1, y, c)

        # Top-right
        self.display.set_pixel(x + size, y - 1, c)
        self.display.set_pixel(x + size - 1, y - 1, c)
        self.display.set_pixel(x + size, y, c)

        # Bottom-left
        self.display.set_pixel(x - 1, y + size, c)
        self.display.set_pixel(x, y + size, c)
        self.display.set_pixel(x - 1, y + size - 1, c)

        # Bottom-right
        self.display.set_pixel(x + size, y + size, c)
        self.display.set_pixel(x + size - 1, y + size, c)
        self.display.set_pixel(x + size, y + size - 1, c)

    def draw_win(self):
        """Draw win message."""
        self.display.draw_text_small(12, 1, "CLEAR!", Colors.GREEN)
        if self.level >= self.best_level:
            self.display.draw_text_small(30, 57, "NEW BEST!", Colors.YELLOW)

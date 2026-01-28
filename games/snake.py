"""
Snake - Classic arcade game
============================
Eat food to grow longer. Don't hit yourself or the walls!

Controls:
  Arrow Keys - Change direction
  Space      - Start game / Restart after game over
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Snake(Game):
    name = "SNAKE"
    description = "Eat food, grow longer!"
    category = "retro"

    # Scale factor - each game unit is 2x2 pixels
    SCALE = 2
    GAME_WIDTH = GRID_SIZE // 2   # 32 units
    GAME_HEIGHT = GRID_SIZE // 2  # 32 units

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Snake starts in the middle, going right (in game units)
        start_x, start_y = self.GAME_WIDTH // 2, self.GAME_HEIGHT // 2
        self.snake = [(start_x, start_y), (start_x - 1, start_y), (start_x - 2, start_y)]
        self.direction = (1, 0)  # Moving right
        self.next_direction = (1, 0)

        # Movement timing
        self.move_timer = 0
        self.move_delay = 0.12  # Seconds between moves

        # Food
        self.food = None
        self.spawn_food()

        # Effects
        self.flash_timer = 0
    
    def spawn_food(self):
        """Spawn food at a random empty location (in game units)."""
        while True:
            x = random.randint(1, self.GAME_WIDTH - 2)
            y = random.randint(4, self.GAME_HEIGHT - 2)  # Leave room for score (4 game units = 8 pixels)
            if (x, y) not in self.snake:
                self.food = (x, y)
                break
    
    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Handle direction input (can't reverse)
        if input_state.up and self.direction != (0, 1):
            self.next_direction = (0, -1)
        elif input_state.down and self.direction != (0, -1):
            self.next_direction = (0, 1)
        elif input_state.left and self.direction != (1, 0):
            self.next_direction = (-1, 0)
        elif input_state.right and self.direction != (-1, 0):
            self.next_direction = (1, 0)
        
        # Update flash effect
        if self.flash_timer > 0:
            self.flash_timer -= dt
        
        # Move snake on timer
        self.move_timer += dt
        if self.move_timer >= self.move_delay:
            self.move_timer = 0
            self.direction = self.next_direction
            self.move_snake()
    
    def move_snake(self):
        """Move the snake one step (in game units)."""
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])

        # Check wall collision (in game units)
        if (new_head[0] < 0 or new_head[0] >= self.GAME_WIDTH or
            new_head[1] < 4 or new_head[1] >= self.GAME_HEIGHT):  # Top 4 game units (8 pixels) for score
            self.state = GameState.GAME_OVER
            return

        # Check self collision
        if new_head in self.snake[:-1]:
            self.state = GameState.GAME_OVER
            return

        # Move snake
        self.snake.insert(0, new_head)

        # Check food collision
        if new_head == self.food:
            self.score += 10
            self.flash_timer = 0.1
            self.spawn_food()

            # Speed up slightly
            self.move_delay = max(0.05, self.move_delay - 0.002)
        else:
            self.snake.pop()  # Remove tail if not eating
    
    def draw_block(self, gx, gy, color):
        """Draw a 2x2 block at game coordinates."""
        px, py = gx * self.SCALE, gy * self.SCALE
        for dx in range(self.SCALE):
            for dy in range(self.SCALE):
                if 0 <= px + dx < GRID_SIZE and 0 <= py + dy < GRID_SIZE:
                    self.display.set_pixel(px + dx, py + dy, color)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw border for play area (at pixel level)
        self.display.draw_line(0, 7, 63, 7, Colors.DARK_GRAY)

        # Draw snake (2x2 blocks)
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                # Head is brighter
                color = Colors.LIME if self.flash_timer > 0 else Colors.GREEN
            else:
                # Body gradient
                shade = max(100, 255 - i * 8)
                color = (0, shade, 0)
            self.draw_block(x, y, color)

        # Draw eyes on head (single pixel within the 2x2 head block)
        head_x, head_y = self.snake[0]
        px, py = head_x * self.SCALE, head_y * self.SCALE
        if self.direction == (1, 0):  # Right
            self.display.set_pixel(px + 1, py, Colors.WHITE)
            self.display.set_pixel(px + 1, py + 1, Colors.WHITE)
        elif self.direction == (-1, 0):  # Left
            self.display.set_pixel(px, py, Colors.WHITE)
            self.display.set_pixel(px, py + 1, Colors.WHITE)
        elif self.direction == (0, -1):  # Up
            self.display.set_pixel(px, py, Colors.WHITE)
            self.display.set_pixel(px + 1, py, Colors.WHITE)
        elif self.direction == (0, 1):  # Down
            self.display.set_pixel(px, py + 1, Colors.WHITE)
            self.display.set_pixel(px + 1, py + 1, Colors.WHITE)

        # Draw food (2x2 block)
        if self.food:
            fx, fy = self.food
            self.draw_block(fx, fy, Colors.RED)

        # Draw score
        self.display.draw_text_small(1, 1, f"SCORE:{self.score}", Colors.WHITE)

        # Draw length indicator
        length_str = f"LEN:{len(self.snake)}"
        self.display.draw_text_small(40, 1, length_str, Colors.GREEN)

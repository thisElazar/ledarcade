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
    
    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()
    
    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        
        # Snake starts in the middle, going right
        start_x, start_y = GRID_SIZE // 2, GRID_SIZE // 2
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
        """Spawn food at a random empty location."""
        while True:
            x = random.randint(1, GRID_SIZE - 2)
            y = random.randint(8, GRID_SIZE - 2)  # Leave room for score
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
        """Move the snake one step."""
        head_x, head_y = self.snake[0]
        new_head = (head_x + self.direction[0], head_y + self.direction[1])
        
        # Check wall collision
        if (new_head[0] < 0 or new_head[0] >= GRID_SIZE or
            new_head[1] < 7 or new_head[1] >= GRID_SIZE):  # Top 7 rows for score
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
    
    def draw(self):
        self.display.clear(Colors.BLACK)
        
        # Draw border for play area
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        
        # Draw snake
        for i, (x, y) in enumerate(self.snake):
            if i == 0:
                # Head is brighter
                color = Colors.LIME if self.flash_timer > 0 else Colors.GREEN
            else:
                # Body gradient
                shade = max(100, 255 - i * 8)
                color = (0, shade, 0)
            self.display.set_pixel(x, y, color)
        
        # Draw eyes on head
        head_x, head_y = self.snake[0]
        if self.direction == (1, 0):  # Right
            self.display.set_pixel(head_x, head_y, Colors.WHITE)
        elif self.direction == (-1, 0):  # Left
            self.display.set_pixel(head_x, head_y, Colors.WHITE)
        elif self.direction == (0, -1):  # Up
            self.display.set_pixel(head_x, head_y, Colors.WHITE)
        elif self.direction == (0, 1):  # Down
            self.display.set_pixel(head_x, head_y, Colors.WHITE)
        
        # Draw food (pulsing effect)
        if self.food:
            fx, fy = self.food
            self.display.set_pixel(fx, fy, Colors.RED)
            # Glow effect
            for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                gx, gy = fx + dx, fy + dy
                if 0 <= gx < GRID_SIZE and 7 <= gy < GRID_SIZE:
                    if (gx, gy) not in self.snake:
                        self.display.set_pixel(gx, gy, (64, 0, 0))
        
        # Draw score
        self.display.draw_text_small(1, 1, f"SCORE:{self.score}", Colors.WHITE)
        
        # Draw length indicator
        length_str = f"LEN:{len(self.snake)}"
        self.display.draw_text_small(40, 1, length_str, Colors.GREEN)

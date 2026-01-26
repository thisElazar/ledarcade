"""
Breakout - Classic brick breaker
================================
Bounce the ball to break all the bricks!

Controls:
  Left/Right - Move paddle
  Space      - Launch ball / Restart
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Breakout(Game):
    name = "BREAKOUT"
    description = "Break all the bricks!"
    
    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()
    
    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        
        # Paddle
        self.paddle_width = 10
        self.paddle_x = GRID_SIZE // 2 - self.paddle_width // 2
        self.paddle_y = GRID_SIZE - 4
        
        # Ball
        self.ball_x = float(GRID_SIZE // 2)
        self.ball_y = float(self.paddle_y - 2)
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_speed = 45.0  # Pixels per second
        self.ball_launched = False
        
        # Bricks
        self.bricks = []
        self.setup_bricks()
        
        # Effects
        self.shake_timer = 0
    
    def setup_bricks(self):
        """Create the brick layout."""
        self.bricks = []
        brick_colors = [
            Colors.RED,
            Colors.ORANGE,
            Colors.YELLOW,
            Colors.GREEN,
            Colors.CYAN,
        ]
        
        # 5 rows of bricks, starting at row 10
        brick_width = 4
        brick_height = 2
        bricks_per_row = GRID_SIZE // brick_width
        
        for row in range(5):
            for col in range(bricks_per_row):
                brick = {
                    'x': col * brick_width,
                    'y': 10 + row * (brick_height + 1),
                    'w': brick_width - 1,
                    'h': brick_height,
                    'color': brick_colors[row],
                    'points': (5 - row) * 10,  # Top rows worth more
                }
                self.bricks.append(brick)
    
    def launch_ball(self):
        """Launch the ball from the paddle."""
        if not self.ball_launched:
            angle = random.uniform(-0.4, 0.4)  # Random angle
            self.ball_dx = math.sin(angle) * self.ball_speed
            self.ball_dy = -self.ball_speed  # Always go up
            self.ball_launched = True
    
    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Move paddle
        paddle_speed = 60  # Pixels per second
        if input_state.left:
            self.paddle_x = max(0, self.paddle_x - paddle_speed * dt)
        if input_state.right:
            self.paddle_x = min(GRID_SIZE - self.paddle_width, self.paddle_x + paddle_speed * dt)
        
        # Launch ball
        if input_state.action and not self.ball_launched:
            self.launch_ball()
        
        # Ball follows paddle if not launched
        if not self.ball_launched:
            self.ball_x = self.paddle_x + self.paddle_width / 2
            self.ball_y = self.paddle_y - 2
            return
        
        # Update shake
        if self.shake_timer > 0:
            self.shake_timer -= dt
        
        # Move ball
        self.ball_x += self.ball_dx * dt
        self.ball_y += self.ball_dy * dt
        
        # Wall collisions
        if self.ball_x <= 0:
            self.ball_x = 0
            self.ball_dx = abs(self.ball_dx)
        if self.ball_x >= GRID_SIZE - 1:
            self.ball_x = GRID_SIZE - 1
            self.ball_dx = -abs(self.ball_dx)
        if self.ball_y <= 7:  # Top wall (below score)
            self.ball_y = 7
            self.ball_dy = abs(self.ball_dy)
        
        # Bottom - lose life
        if self.ball_y >= GRID_SIZE:
            self.lives -= 1
            self.ball_launched = False
            if self.lives <= 0:
                self.state = GameState.GAME_OVER
        
        # Paddle collision
        ball_ix, ball_iy = int(self.ball_x), int(self.ball_y)
        if (self.ball_dy > 0 and 
            self.paddle_y <= ball_iy <= self.paddle_y + 1 and
            self.paddle_x <= ball_ix <= self.paddle_x + self.paddle_width):
            
            # Bounce angle depends on where ball hit paddle
            hit_pos = (self.ball_x - self.paddle_x) / self.paddle_width
            angle = (hit_pos - 0.5) * 1.2  # -0.6 to 0.6 radians
            
            speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
            self.ball_dx = math.sin(angle) * speed
            self.ball_dy = -abs(math.cos(angle) * speed)
            self.ball_y = self.paddle_y - 1
        
        # Brick collisions
        for brick in self.bricks[:]:
            if self.ball_brick_collision(brick):
                self.bricks.remove(brick)
                self.score += brick['points']
                # No screen shake
                
                # Speed up slightly
                self.ball_speed = min(80, self.ball_speed + 0.5)
                break
        
        # Win condition
        if not self.bricks:
            self.state = GameState.WIN
    
    def ball_brick_collision(self, brick) -> bool:
        """Check and handle ball-brick collision."""
        bx, by = int(self.ball_x), int(self.ball_y)
        
        if (brick['x'] <= bx <= brick['x'] + brick['w'] and
            brick['y'] <= by <= brick['y'] + brick['h']):
            
            # Determine bounce direction
            # Simple: reverse y direction
            self.ball_dy = -self.ball_dy
            return True
        
        return False
    
    def draw(self):
        self.display.clear(Colors.BLACK)
        
        # Screen shake offset
        shake_x = random.randint(-1, 1) if self.shake_timer > 0 else 0
        shake_y = random.randint(-1, 1) if self.shake_timer > 0 else 0
        
        # Draw score and lives
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        
        # Draw lives as hearts/dots
        for i in range(self.lives):
            self.display.set_pixel(55 + i * 3, 2, Colors.RED)
            self.display.set_pixel(56 + i * 3, 2, Colors.RED)
            self.display.set_pixel(55 + i * 3, 3, Colors.RED)
        
        # Draw separator
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        
        # Draw bricks
        for brick in self.bricks:
            self.display.draw_rect(
                brick['x'] + shake_x, 
                brick['y'] + shake_y,
                brick['w'], 
                brick['h'], 
                brick['color']
            )
        
        # Draw paddle
        paddle_ix = int(self.paddle_x)
        for i in range(self.paddle_width):
            self.display.set_pixel(paddle_ix + i + shake_x, self.paddle_y + shake_y, Colors.WHITE)
            self.display.set_pixel(paddle_ix + i + shake_x, self.paddle_y + 1 + shake_y, Colors.GRAY)
        
        # Draw ball
        ball_ix, ball_iy = int(self.ball_x), int(self.ball_y)
        self.display.set_pixel(ball_ix + shake_x, ball_iy + shake_y, Colors.WHITE)
        
        # Draw launch prompt
        if not self.ball_launched:
            self.display.draw_text_small(8, 40, "SPACE:LAUNCH", Colors.GRAY)
    
    def draw_game_over(self):
        """Custom game over for Breakout."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(12, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)

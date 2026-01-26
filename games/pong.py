"""
Pong - The original arcade classic
==================================
Beat the AI opponent! First to 7 wins.

Controls:
  Up/Down - Move paddle
  Space   - Start game / Restart
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Pong(Game):
    name = "PONG"
    description = "Beat the AI!"
    
    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()
    
    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.ai_score = 0
        self.win_score = 7
        
        # Paddles
        self.paddle_height = 8
        self.paddle_width = 2
        
        # Player paddle (left side)
        self.player_y = GRID_SIZE // 2 - self.paddle_height // 2
        
        # AI paddle (right side)
        self.ai_y = GRID_SIZE // 2 - self.paddle_height // 2
        self.ai_speed = 25.0  # AI movement speed (slower = easier)
        
        # Ball
        self.ball_x = float(GRID_SIZE // 2)
        self.ball_y = float(GRID_SIZE // 2)
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_speed = 50.0
        self.ball_active = False
        
        # Game state
        self.serve_timer = 0
        self.serving = True
        self.last_scorer = 'player'  # Who serves next
        
        # Effects
        self.flash_timer = 0
        self.flash_side = None
    
    def serve_ball(self):
        """Serve the ball."""
        self.ball_x = GRID_SIZE // 2
        self.ball_y = GRID_SIZE // 2
        
        # Serve toward the last scorer's opponent
        direction = 1 if self.last_scorer == 'player' else -1
        angle = random.uniform(-0.5, 0.5)
        
        self.ball_dx = direction * self.ball_speed * math.cos(angle)
        self.ball_dy = self.ball_speed * math.sin(angle)
        self.ball_active = True
        self.serving = False
    
    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        
        # Serve on space
        if self.serving:
            self.serve_timer += dt
            if input_state.action or self.serve_timer > 1.5:
                self.serve_ball()
                self.serve_timer = 0
            return
        
        # Update flash effect
        if self.flash_timer > 0:
            self.flash_timer -= dt
        
        # Player paddle movement
        paddle_speed = 50.0
        if input_state.up:
            self.player_y = max(8, self.player_y - paddle_speed * dt)
        if input_state.down:
            self.player_y = min(GRID_SIZE - self.paddle_height, self.player_y + paddle_speed * dt)
        
        # AI paddle movement (tracks ball with some delay/imperfection)
        ai_target = self.ball_y - self.paddle_height / 2
        
        # Add some randomness to AI (more randomness = easier)
        ai_target += random.uniform(-4, 4)
        
        # AI moves toward target
        if self.ai_y < ai_target - 1:
            self.ai_y = min(GRID_SIZE - self.paddle_height, self.ai_y + self.ai_speed * dt)
        elif self.ai_y > ai_target + 1:
            self.ai_y = max(8, self.ai_y - self.ai_speed * dt)
        
        if not self.ball_active:
            return
        
        # Move ball
        self.ball_x += self.ball_dx * dt
        self.ball_y += self.ball_dy * dt
        
        # Top/bottom wall bounce
        if self.ball_y <= 8:
            self.ball_y = 8
            self.ball_dy = abs(self.ball_dy)
        if self.ball_y >= GRID_SIZE - 1:
            self.ball_y = GRID_SIZE - 1
            self.ball_dy = -abs(self.ball_dy)
        
        # Player paddle collision (left side)
        player_paddle_x = 3
        if (self.ball_dx < 0 and 
            player_paddle_x <= self.ball_x <= player_paddle_x + self.paddle_width + 1 and
            self.player_y <= self.ball_y <= self.player_y + self.paddle_height):
            
            # Bounce with angle based on hit position
            hit_pos = (self.ball_y - self.player_y) / self.paddle_height
            angle = (hit_pos - 0.5) * 1.2
            
            self.ball_dx = abs(self.ball_speed * math.cos(angle))
            self.ball_dy = self.ball_speed * math.sin(angle)
            self.ball_x = player_paddle_x + self.paddle_width + 1
            
            # Speed up slightly
            self.ball_speed = min(80, self.ball_speed + 1)
        
        # AI paddle collision (right side)
        ai_paddle_x = GRID_SIZE - 5
        if (self.ball_dx > 0 and
            ai_paddle_x - 1 <= self.ball_x <= ai_paddle_x + self.paddle_width and
            self.ai_y <= self.ball_y <= self.ai_y + self.paddle_height):
            
            hit_pos = (self.ball_y - self.ai_y) / self.paddle_height
            angle = (hit_pos - 0.5) * 1.2
            
            self.ball_dx = -abs(self.ball_speed * math.cos(angle))
            self.ball_dy = self.ball_speed * math.sin(angle)
            self.ball_x = ai_paddle_x - 1
            
            self.ball_speed = min(80, self.ball_speed + 1)
        
        # Scoring
        if self.ball_x <= 0:
            # AI scores
            self.ai_score += 1
            self.last_scorer = 'ai'
            self.ball_active = False
            self.serving = True
            self.flash_timer = 0.3
            self.flash_side = 'left'
            self.ball_speed = 50.0
            
            if self.ai_score >= self.win_score:
                self.state = GameState.GAME_OVER
        
        elif self.ball_x >= GRID_SIZE - 1:
            # Player scores
            self.score += 1
            self.last_scorer = 'player'
            self.ball_active = False
            self.serving = True
            self.flash_timer = 0.3
            self.flash_side = 'right'
            self.ball_speed = 50.0
            
            if self.score >= self.win_score:
                self.state = GameState.WIN
    
    def draw(self):
        self.display.clear(Colors.BLACK)
        
        # Flash effect on scoring
        if self.flash_timer > 0:
            if self.flash_side == 'left':
                self.display.draw_rect(0, 8, 32, 56, (30, 0, 0))
            else:
                self.display.draw_rect(32, 8, 32, 56, (0, 30, 0))
        
        # Draw scores
        self.display.draw_text_small(20, 1, f"{self.score}", Colors.GREEN)
        self.display.draw_text_small(36, 1, f"{self.ai_score}", Colors.RED)
        
        # Draw center line
        self.display.draw_line(0, 7, 63, 7, Colors.DARK_GRAY)
        
        # Draw dashed center line
        for y in range(8, GRID_SIZE, 4):
            self.display.set_pixel(GRID_SIZE // 2, y, Colors.DARK_GRAY)
            self.display.set_pixel(GRID_SIZE // 2, y + 1, Colors.DARK_GRAY)
        
        # Draw player paddle (left)
        player_paddle_x = 3
        for dy in range(self.paddle_height):
            for dx in range(self.paddle_width):
                self.display.set_pixel(player_paddle_x + dx, int(self.player_y) + dy, Colors.GREEN)
        
        # Draw AI paddle (right)
        ai_paddle_x = GRID_SIZE - 5
        for dy in range(self.paddle_height):
            for dx in range(self.paddle_width):
                self.display.set_pixel(ai_paddle_x + dx, int(self.ai_y) + dy, Colors.RED)
        
        # Draw ball
        if self.ball_active:
            ball_ix, ball_iy = int(self.ball_x), int(self.ball_y)
            self.display.set_pixel(ball_ix, ball_iy, Colors.WHITE)
            self.display.set_pixel(ball_ix + 1, ball_iy, Colors.WHITE)
            self.display.set_pixel(ball_ix, ball_iy + 1, Colors.WHITE)
            self.display.set_pixel(ball_ix + 1, ball_iy + 1, Colors.WHITE)
        
        # Draw serve prompt
        if self.serving:
            self.display.draw_text_small(12, 30, "GET READY", Colors.YELLOW)
    
    def draw_game_over(self):
        """Custom game over for Pong."""
        self.display.clear(Colors.BLACK)
        
        if self.state == GameState.WIN:
            self.display.draw_text_small(12, 20, "YOU WIN!", Colors.GREEN)
        else:
            self.display.draw_text_small(12, 20, "YOU LOSE", Colors.RED)
        
        self.display.draw_text_small(8, 35, f"FINAL:{self.score}-{self.ai_score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)

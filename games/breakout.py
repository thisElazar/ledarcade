"""
Breakout - Classic 1976 Atari arcade game
=========================================
Authentic recreation of the original Breakout mechanics.

Original rules:
- 8 rows of bricks (2 rows each: red, orange, green, yellow)
- Points: Red=7, Orange=5, Green=3, Yellow=1
- Paddle shrinks to half after ball hits top wall
- Ball speeds up after 4 hits, again after 12 hits
- Ball is fastest when in orange/red rows
- 3 lives to clear 2 screens (max score 896)

Controls:
  Left/Right - Move paddle
  Space      - Launch ball
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

# Playfield layout (64px total)
# [4px wall][4px x 14 columns = 56px bricks][4px wall]
WALL_SIZE = 4
PLAY_LEFT = 4
PLAY_RIGHT = 60
BRICKS_PER_ROW = 14


class Breakout(Game):
    name = "BREAK OUT"
    description = "Classic 1976 Atari"
    category = "arcade"
    GUIDE = {
        'desc': 'Move a paddle to bounce a ball into rows of bricks. Clear all bricks to win. Ball speeds up; paddle shrinks after hitting the ceiling.',
    }

    # Authentic color scheme (bottom to top): Yellow, Green, Orange, Red
    BRICK_ROWS = [
        {'color': Colors.YELLOW, 'points': 1},
        {'color': Colors.YELLOW, 'points': 1},
        {'color': Colors.GREEN, 'points': 3},
        {'color': Colors.GREEN, 'points': 3},
        {'color': Colors.ORANGE, 'points': 5},
        {'color': Colors.ORANGE, 'points': 5},
        {'color': Colors.RED, 'points': 7},
        {'color': Colors.RED, 'points': 7},
    ]

    # Speed tiers (pixels per second)
    SPEED_INITIAL = 40.0
    SPEED_AFTER_4 = 50.0
    SPEED_AFTER_12 = 62.0
    SPEED_TOP_ROWS = 75.0  # After first orange/red brick hit (persists for the ball)

    # Quantized paddle deflection zones (fixed angles, radians from vertical)
    PADDLE_ANGLES = [-0.85, -0.5, -0.17, 0.17, 0.5, 0.85]

    # Paddle sizes
    PADDLE_FULL = 12
    PADDLE_HALF = 6

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.screen = 1  # Current screen (1 or 2)
        self.hit_count = 0  # Total brick hits this ball
        self.orange_hit = False  # Hit an orange-row brick this ball?
        self.red_hit = False     # Hit a red-row brick this ball?
        self.hit_ceiling = False  # Has ball hit top wall this screen?

        # Paddle - centered within walled playfield
        self.paddle_width = self.PADDLE_FULL
        self.paddle_x = PLAY_LEFT + (PLAY_RIGHT - PLAY_LEFT - self.paddle_width) // 2
        self.paddle_y = GRID_SIZE - 4

        # Ball
        self.ball_x = float(GRID_SIZE // 2)
        self.ball_y = float(self.paddle_y - 2)
        self.prev_ball_x = self.ball_x
        self.ball_dx = 0.0
        self.ball_dy = 0.0
        self.ball_speed = self.SPEED_INITIAL
        self.ball_launched = False

        # Bricks
        self.bricks = []
        self.setup_bricks()

    def setup_bricks(self):
        """Create the authentic 8-row brick layout."""
        self.bricks = []

        brick_width = 4
        brick_height = 2
        start_y = 8  # Start below score area

        # 8 rows, bottom to top (index 0 = bottom yellow, index 7 = top red)
        for row in range(8):
            row_def = self.BRICK_ROWS[row]
            for col in range(BRICKS_PER_ROW):
                brick = {
                    'x': PLAY_LEFT + col * brick_width,
                    'y': start_y + (7 - row) * (brick_height + 1),  # Top rows at top
                    'w': brick_width - 1,
                    'h': brick_height,
                    'color': row_def['color'],
                    'points': row_def['points'],
                    'row': row,  # Track which row for speed changes
                }
                self.bricks.append(brick)

    def launch_ball(self):
        """Launch the ball from the paddle."""
        if not self.ball_launched:
            angle = random.uniform(-0.4, 0.4)
            self.ball_dx = math.sin(angle) * self.ball_speed
            self.ball_dy = -self.ball_speed
            self.ball_launched = True
            self.hit_count = 0
            self.orange_hit = False
            self.red_hit = False

    def get_current_speed(self):
        """Calculate ball speed based on authentic rules."""
        # Base speed from hit count
        if self.hit_count >= 12:
            speed = self.SPEED_AFTER_12
        elif self.hit_count >= 4:
            speed = self.SPEED_AFTER_4
        else:
            speed = self.SPEED_INITIAL

        # Persistent speed-up once an orange or red brick has been hit
        if self.orange_hit or self.red_hit:
            speed = max(speed, self.SPEED_TOP_ROWS)

        return speed

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Move paddle (constrained within walls)
        paddle_speed = 60
        if input_state.left:
            self.paddle_x = max(PLAY_LEFT, self.paddle_x - paddle_speed * dt)
        if input_state.right:
            self.paddle_x = min(PLAY_RIGHT - self.paddle_width, self.paddle_x + paddle_speed * dt)

        # Launch ball
        if (input_state.action_l or input_state.action_r) and not self.ball_launched:
            self.launch_ball()

        # Ball follows paddle if not launched
        if not self.ball_launched:
            self.ball_x = self.paddle_x + self.paddle_width / 2
            self.ball_y = self.paddle_y - 2
            return

        # Update ball speed based on game state
        self.ball_speed = self.get_current_speed()

        # Normalize and apply speed
        current_speed = math.sqrt(self.ball_dx**2 + self.ball_dy**2)
        if current_speed > 0:
            scale = self.ball_speed / current_speed
            self.ball_dx *= scale
            self.ball_dy *= scale

        # Move ball (remember previous x for brick collision axis)
        self.prev_ball_x = self.ball_x
        self.ball_x += self.ball_dx * dt
        self.ball_y += self.ball_dy * dt

        # Wall collisions (2x2 ball, bounce off side walls)
        if self.ball_x <= PLAY_LEFT:
            self.ball_x = PLAY_LEFT
            self.ball_dx = abs(self.ball_dx)
        if self.ball_x >= PLAY_RIGHT - 2:
            self.ball_x = PLAY_RIGHT - 2
            self.ball_dx = -abs(self.ball_dx)

        # Top wall - shrink paddle (authentic mechanic)
        if self.ball_y <= 7:
            self.ball_y = 7
            self.ball_dy = abs(self.ball_dy)
            if not self.hit_ceiling:
                self.hit_ceiling = True
                self.paddle_width = self.PADDLE_HALF
                # Re-center paddle at new width
                self.paddle_x = min(self.paddle_x, PLAY_RIGHT - self.paddle_width)

        # Bottom - lose life
        if self.ball_y >= GRID_SIZE - 1:
            self.lives -= 1
            self.ball_launched = False
            if self.lives <= 0:
                self.state = GameState.GAME_OVER
            else:
                # Reset for next ball but keep paddle size
                self.hit_count = 0
                self.orange_hit = False
                self.red_hit = False

        # Paddle collision
        ball_ix, ball_iy = int(self.ball_x), int(self.ball_y)
        ball_bottom = ball_iy + 1
        if (self.ball_dy > 0 and
            self.paddle_y <= ball_bottom <= self.paddle_y + 1 and
            self.paddle_x - 1 <= ball_ix <= self.paddle_x + self.paddle_width):

            # Quantized deflection: fixed angle per paddle zone
            hit_pos = (self.ball_x - self.paddle_x) / self.paddle_width
            zone = min(len(self.PADDLE_ANGLES) - 1,
                       max(0, int(hit_pos * len(self.PADDLE_ANGLES))))
            angle = self.PADDLE_ANGLES[zone]

            self.ball_dx = math.sin(angle) * self.ball_speed
            self.ball_dy = -abs(math.cos(angle) * self.ball_speed)
            self.ball_y = self.paddle_y - 2

        # Brick collisions
        for brick in self.bricks[:]:
            if self.ball_brick_collision(brick):
                self.bricks.remove(brick)
                self.score += brick['points']
                self.hit_count += 1
                # Persistent speed triggers: first orange / red brick hit
                if brick['row'] >= 6:
                    self.red_hit = True
                elif brick['row'] >= 4:
                    self.orange_hit = True
                break

        # Screen cleared - advance or win
        if not self.bricks:
            if self.screen < 2:
                # Advance to screen 2
                self.screen = 2
                self.setup_bricks()
                self.ball_launched = False
                self.hit_ceiling = False
                self.paddle_width = self.PADDLE_FULL
                self.paddle_x = PLAY_LEFT + (PLAY_RIGHT - PLAY_LEFT - self.paddle_width) // 2
            else:
                # Both screens cleared - game complete!
                self.state = GameState.WIN

    def ball_brick_collision(self, brick) -> bool:
        """Check and handle ball-brick collision (2x2 ball).

        Bounce axis is decided by penetration: if the ball was outside the
        brick's x-span last frame it hit a side (flip dx), otherwise it hit
        the top/bottom (flip dy).
        """
        bx, by = int(self.ball_x), int(self.ball_y)

        for dx in range(2):
            for dy in range(2):
                px, py = bx + dx, by + dy
                if (brick['x'] <= px <= brick['x'] + brick['w'] and
                    brick['y'] <= py <= brick['y'] + brick['h']):
                    prev_bx = int(self.prev_ball_x)
                    if (prev_bx + 1 < brick['x'] or
                            prev_bx > brick['x'] + brick['w']):
                        self.ball_dx = -self.ball_dx
                    else:
                        self.ball_dy = -self.ball_dy
                    return True
        return False

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw score and lives
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)

        # Draw lives as dots
        for i in range(self.lives):
            self.display.set_pixel(50 + i * 4, 2, Colors.WHITE)
            self.display.set_pixel(51 + i * 4, 2, Colors.WHITE)
            self.display.set_pixel(50 + i * 4, 3, Colors.WHITE)
            self.display.set_pixel(51 + i * 4, 3, Colors.WHITE)

        # Draw separator
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)

        # Draw side walls
        self.display.draw_rect(0, 7, PLAY_LEFT, GRID_SIZE - 7, Colors.DARK_GRAY)
        self.display.draw_rect(PLAY_RIGHT, 7, GRID_SIZE - PLAY_RIGHT, GRID_SIZE - 7, Colors.DARK_GRAY)

        # Draw bricks
        for brick in self.bricks:
            self.display.draw_rect(
                brick['x'],
                brick['y'],
                brick['w'],
                brick['h'],
                brick['color']
            )

        # Draw paddle
        paddle_ix = int(self.paddle_x)
        for i in range(self.paddle_width):
            self.display.set_pixel(paddle_ix + i, self.paddle_y, Colors.WHITE)
            self.display.set_pixel(paddle_ix + i, self.paddle_y + 1, Colors.GRAY)

        # Draw ball (2x2 pixels)
        ball_ix, ball_iy = int(self.ball_x), int(self.ball_y)
        self.display.set_pixel(ball_ix, ball_iy, Colors.WHITE)
        self.display.set_pixel(ball_ix + 1, ball_iy, Colors.WHITE)
        self.display.set_pixel(ball_ix, ball_iy + 1, Colors.WHITE)
        self.display.set_pixel(ball_ix + 1, ball_iy + 1, Colors.WHITE)

        # Draw launch prompt
        if not self.ball_launched:
            if self.screen == 1:
                self.display.draw_text_small(4, 45, "BTN:LAUNCH", Colors.GRAY)
            else:
                self.display.draw_text_small(8, 40, "SCREEN 2", Colors.CYAN)
                self.display.draw_text_small(4, 50, "BTN:LAUNCH", Colors.GRAY)

    def draw_game_over(self, selection: int = 0):
        """Custom game over — nods to the original's 896 max score on a win."""
        self.display.clear(Colors.BLACK)

        if self.state == GameState.WIN:
            self.display.draw_text_small(12, 12, "YOU WIN!", Colors.GREEN)
            self.display.draw_text_small(8, 22, f"SCORE:{self.score}", Colors.WHITE)
            self.display.draw_text_small(8, 32, "MAX: 896", Colors.YELLOW)
        else:
            self.display.draw_text_small(8, 12, "GAME OVER", Colors.RED)
            self.display.draw_text_small(8, 22, f"SCORE:{self.score}", Colors.WHITE)

        # Draw selection options
        if selection == 0:
            self.display.draw_text_small(4, 44, ">PLAY AGAIN", Colors.YELLOW)
            self.display.draw_text_small(4, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(4, 44, " PLAY AGAIN", Colors.GRAY)
            self.display.draw_text_small(4, 54, ">MENU", Colors.YELLOW)

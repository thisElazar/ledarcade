"""
Arkanoid - 1986 Taito block breaker
===================================
The game that revolutionized brick breakers with varied levels,
power-ups, and different brick types.

Features:
- Multiple unique level layouts
- Power-ups (extend paddle, multi-ball, laser, slow, extra life)
- Different brick types (normal, hard, indestructible)
- Progressive difficulty

Controls:
  Left/Right - Move paddle (Vaus)
  Space      - Launch ball / Fire laser
"""

import random
import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
from games.arkanoid_levels import LEVEL_DATA


# Playfield layout (64px total)
# [4px wall][5px x 11 columns = 55px bricks][5px wall]
PLAY_LEFT = 4       # first pixel of playfield
PLAY_RIGHT = 59     # first pixel of right wall
BRICK_WIDTH = 5     # stride per column
BRICK_DRAW_W = 4    # drawn width (stride - 1 gap)
BRICK_HEIGHT = 2    # drawn height
BRICK_STRIDE_Y = 3  # vertical stride (height + 1 gap)
BRICK_START_Y = 8   # first brick row y position
NUM_COLS = 11

# Character-to-color mapping for level data
BRICK_CHAR_MAP = {
    '0': None,
    '1': 'white',   '2': 'orange',  '3': 'cyan',
    '4': 'green',   '5': 'red',     '6': 'blue',
    '7': 'pink',    '8': 'yellow',  '9': 'silver',
    'A': 'gold',
}


class Arkanoid(Game):
    name = "ARKANOID"
    description = "1986 Taito classic"
    category = "retro"

    # Brick types
    BRICK_NORMAL = 0     # One hit to destroy
    BRICK_HARD = 1       # Two hits to destroy
    BRICK_INDESTRUCTIBLE = 2  # Cannot be destroyed

    # Power-up types
    POWERUP_NONE = 0
    POWERUP_EXTEND = 1   # Wider paddle
    POWERUP_LASER = 2    # Shoot lasers
    POWERUP_SLOW = 3     # Slow ball
    POWERUP_MULTI = 4    # Multi-ball
    POWERUP_LIFE = 5     # Extra life (Player)

    # Colors for brick types
    BRICK_COLORS = {
        'white': Colors.WHITE,
        'orange': Colors.ORANGE,
        'cyan': Colors.CYAN,
        'green': Colors.GREEN,
        'red': Colors.RED,
        'blue': Colors.BLUE,
        'pink': Colors.PINK,
        'yellow': Colors.YELLOW,
        'silver': Colors.GRAY,      # Hard brick
        'gold': (200, 180, 50),     # Indestructible
    }

    # Paddle sizes
    PADDLE_NORMAL = 10
    PADDLE_EXTENDED = 14

    # Ball speed scaling (like original 1986 Arkanoid)
    BASE_BALL_SPEED = 45.0          # Starting speed on level 1
    SPEED_INCREMENT_PER_HIT = 0.5   # Small speed increase per brick hit
    SPEED_INCREMENT_PER_LEVEL = 3.0 # Speed increase per level
    MAX_BALL_SPEED = 90.0           # Maximum speed cap to keep game playable

    def __init__(self, display: Display):
        super().__init__(display)
        self.levels = self.define_levels()
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.lives = 3
        self.level = 0
        self.next_bonus_life = 20000  # first at 20K, then every 60K

        # Paddle (Vaus) - centered within walled playfield
        self.paddle_width = self.PADDLE_NORMAL
        self.paddle_x = PLAY_LEFT + (PLAY_RIGHT - PLAY_LEFT - self.paddle_width) // 2
        self.paddle_y = GRID_SIZE - 4

        # Balls (support multi-ball)
        self.balls = []
        self.spawn_ball()

        # Power-ups
        self.active_powerup = self.POWERUP_NONE
        self.powerup_timer = 0
        self.falling_powerups = []  # {'x', 'y', 'type'}

        # Laser
        self.lasers = []  # {'x', 'y'}
        self.laser_cooldown = 0

        # Bricks
        self.bricks = []
        self.load_level(self.level)

    def get_level_base_speed(self):
        """Calculate the base ball speed for the current level."""
        speed = self.BASE_BALL_SPEED + (self.level * self.SPEED_INCREMENT_PER_LEVEL)
        return min(speed, self.MAX_BALL_SPEED)

    def spawn_ball(self, x=None, y=None, launched=False):
        """Create a new ball."""
        if x is None:
            x = self.paddle_x + self.paddle_width / 2
        if y is None:
            y = self.paddle_y - 2

        ball = {
            'x': float(x),
            'y': float(y),
            'dx': 0.0,
            'dy': 0.0,
            'speed': self.get_level_base_speed(),
            'launched': launched,
        }

        if launched:
            angle = random.uniform(-0.5, 0.5)
            ball['dx'] = math.sin(angle) * ball['speed']
            ball['dy'] = -ball['speed']

        self.balls.append(ball)

    def define_levels(self):
        """Build level list from NES Arkanoid level data."""
        return [{'name': d['name'], 'bricks': self.parse_level(d['rows'])}
                for d in LEVEL_DATA]

    def parse_level(self, rows):
        """Parse compact row strings into brick dicts."""
        bricks = []
        for row_idx, row_str in enumerate(rows):
            for col_idx, ch in enumerate(row_str):
                color_name = BRICK_CHAR_MAP.get(ch)
                if color_name is None:
                    continue
                if ch == '9':
                    brick_type = self.BRICK_HARD
                elif ch == 'A':
                    brick_type = self.BRICK_INDESTRUCTIBLE
                else:
                    brick_type = self.BRICK_NORMAL
                bricks.append({
                    'x': PLAY_LEFT + col_idx * BRICK_WIDTH,
                    'y': BRICK_START_Y + row_idx * BRICK_STRIDE_Y,
                    'w': BRICK_DRAW_W,
                    'h': BRICK_HEIGHT,
                    'color': self.BRICK_COLORS[color_name],
                    'type': brick_type,
                    'hits': 1,  # adjusted in load_level for silver/gold
                    'powerup': brick_type == self.BRICK_NORMAL and random.random() < 0.15,
                })
        return bricks

    def load_level(self, level_idx):
        """Load a level's brick layout."""
        if level_idx >= len(self.levels):
            level_idx = level_idx % len(self.levels)  # Loop levels

        silver_hits = 2 + (self.level // 8)  # +1 hit every 8 stages
        level_data = self.levels[level_idx]
        self.bricks = []
        for brick_def in level_data['bricks']:
            brick = dict(brick_def)  # Copy to avoid modifying template
            if brick['type'] == self.BRICK_HARD:
                brick['hits'] = silver_hits
            elif brick['type'] == self.BRICK_INDESTRUCTIBLE:
                brick['hits'] = 999
            self.bricks.append(brick)

    def launch_ball(self, ball):
        """Launch a ball from the paddle."""
        if not ball['launched']:
            angle = random.uniform(-0.4, 0.4)
            ball['dx'] = math.sin(angle) * ball['speed']
            ball['dy'] = -ball['speed']
            ball['launched'] = True

    def spawn_powerup(self, x, y):
        """Spawn a falling power-up."""
        powerup_type = random.choice([
            self.POWERUP_EXTEND,
            self.POWERUP_LASER,
            self.POWERUP_SLOW,
            self.POWERUP_MULTI,
            self.POWERUP_LIFE,
        ])
        self.falling_powerups.append({
            'x': x,
            'y': y,
            'type': powerup_type,
        })

    def deactivate_powerup(self):
        """Clean up effects of the current active powerup."""
        if self.active_powerup == self.POWERUP_EXTEND:
            self.paddle_width = self.PADDLE_NORMAL
        elif self.active_powerup == self.POWERUP_SLOW:
            base_speed = self.get_level_base_speed()
            for ball in self.balls:
                ball['speed'] = base_speed
                current_speed = math.sqrt(ball['dx']**2 + ball['dy']**2)
                if current_speed > 0:
                    scale = ball['speed'] / current_speed
                    ball['dx'] *= scale
                    ball['dy'] *= scale
        self.active_powerup = self.POWERUP_NONE

    def apply_powerup(self, powerup_type):
        """Apply a power-up effect."""
        # Life is instant — just add a life, don't replace active powerup
        if powerup_type == self.POWERUP_LIFE:
            self.lives += 1
            return

        # Deactivate previous powerup before applying new one
        self.deactivate_powerup()

        self.active_powerup = powerup_type
        self.powerup_timer = 10.0  # 10 seconds

        if powerup_type == self.POWERUP_EXTEND:
            self.paddle_width = self.PADDLE_EXTENDED
        elif powerup_type == self.POWERUP_MULTI:
            # Spawn extra balls
            for ball in self.balls[:]:
                if ball['launched']:
                    self.spawn_ball(ball['x'], ball['y'], launched=True)
                    break
        elif powerup_type == self.POWERUP_SLOW:
            # Slow powerup reduces speed to 2/3 of level base speed
            slow_speed = self.get_level_base_speed() * 0.67
            for ball in self.balls:
                ball['speed'] = slow_speed
                current_speed = math.sqrt(ball['dx']**2 + ball['dy']**2)
                if current_speed > 0:
                    scale = ball['speed'] / current_speed
                    ball['dx'] *= scale
                    ball['dy'] *= scale

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Move paddle (constrained within walls)
        paddle_speed = 65
        if input_state.left:
            self.paddle_x = max(PLAY_LEFT, self.paddle_x - paddle_speed * dt)
        if input_state.right:
            self.paddle_x = min(PLAY_RIGHT - self.paddle_width, self.paddle_x + paddle_speed * dt)

        # Launch ball or fire laser
        if (input_state.action_l or input_state.action_r):
            for ball in self.balls:
                if not ball['launched']:
                    self.launch_ball(ball)
                    break
            else:
                # All balls launched - fire laser if active
                if self.active_powerup == self.POWERUP_LASER and self.laser_cooldown <= 0:
                    self.lasers.append({'x': self.paddle_x + self.paddle_width // 2, 'y': self.paddle_y - 2})
                    self.laser_cooldown = 0.3

        # Update laser cooldown
        if self.laser_cooldown > 0:
            self.laser_cooldown -= dt

        # Update power-up timer
        if self.powerup_timer > 0:
            self.powerup_timer -= dt
            if self.powerup_timer <= 0:
                self.deactivate_powerup()

        # Update balls
        for ball in self.balls[:]:
            if not ball['launched']:
                ball['x'] = self.paddle_x + self.paddle_width / 2
                ball['y'] = self.paddle_y - 2
                continue

            # Move ball
            ball['x'] += ball['dx'] * dt
            ball['y'] += ball['dy'] * dt

            # Wall collisions (bounce off side walls)
            if ball['x'] <= PLAY_LEFT:
                ball['x'] = PLAY_LEFT
                ball['dx'] = abs(ball['dx'])
            if ball['x'] >= PLAY_RIGHT - 2:
                ball['x'] = PLAY_RIGHT - 2
                ball['dx'] = -abs(ball['dx'])
            if ball['y'] <= 7:
                ball['y'] = 7
                ball['dy'] = abs(ball['dy'])

            # Bottom - remove ball
            if ball['y'] >= GRID_SIZE:
                self.balls.remove(ball)
                continue

            # Paddle collision
            ball_ix, ball_iy = int(ball['x']), int(ball['y'])
            if (ball['dy'] > 0 and
                self.paddle_y <= ball_iy + 1 <= self.paddle_y + 2 and
                self.paddle_x - 1 <= ball_ix <= self.paddle_x + self.paddle_width):

                hit_pos = (ball['x'] - self.paddle_x) / self.paddle_width
                angle = (hit_pos - 0.5) * 1.2
                ball['dx'] = math.sin(angle) * ball['speed']
                ball['dy'] = -abs(math.cos(angle) * ball['speed'])
                ball['y'] = self.paddle_y - 2

            # Brick collisions
            for brick in self.bricks[:]:
                if self.ball_brick_collision(ball, brick):
                    brick['hits'] -= 1
                    # Increase ball speed slightly on each hit (like original Arkanoid)
                    if brick['type'] != self.BRICK_INDESTRUCTIBLE:
                        ball['speed'] = min(ball['speed'] + self.SPEED_INCREMENT_PER_HIT, self.MAX_BALL_SPEED)
                        # Update velocity direction to use new speed
                        current_speed = math.sqrt(ball['dx']**2 + ball['dy']**2)
                        if current_speed > 0:
                            scale = ball['speed'] / current_speed
                            ball['dx'] *= scale
                            ball['dy'] *= scale
                    if brick['hits'] <= 0 and brick['type'] != self.BRICK_INDESTRUCTIBLE:
                        if brick.get('powerup'):
                            self.spawn_powerup(brick['x'] + brick['w'] // 2, brick['y'])
                        self.bricks.remove(brick)
                        self.score += 10
                    elif brick['type'] == self.BRICK_HARD:
                        # Darken hard brick on first hit
                        brick['color'] = Colors.DARK_GRAY
                    break

        # Update lasers
        for laser in self.lasers[:]:
            laser['y'] -= 120 * dt
            if laser['y'] < 7:
                self.lasers.remove(laser)
                continue

            # Laser-brick collision
            for brick in self.bricks[:]:
                if (brick['x'] <= laser['x'] <= brick['x'] + brick['w'] and
                    brick['y'] <= laser['y'] <= brick['y'] + brick['h']):
                    if brick['type'] != self.BRICK_INDESTRUCTIBLE:
                        brick['hits'] -= 1
                        if brick['hits'] <= 0:
                            self.bricks.remove(brick)
                            self.score += 10
                    self.lasers.remove(laser)
                    break

        # Update falling power-ups
        for powerup in self.falling_powerups[:]:
            powerup['y'] += 40 * dt
            if powerup['y'] >= GRID_SIZE:
                self.falling_powerups.remove(powerup)
                continue

            # Catch power-up
            if (self.paddle_y <= powerup['y'] <= self.paddle_y + 2 and
                self.paddle_x <= powerup['x'] <= self.paddle_x + self.paddle_width):
                self.apply_powerup(powerup['type'])
                self.falling_powerups.remove(powerup)

        # Score-based bonus lives (20K, then every 60K after)
        while self.score >= self.next_bonus_life:
            self.lives += 1
            self.next_bonus_life += 60000

        # Check for lost all balls
        if not self.balls:
            self.lives -= 1
            if self.lives <= 0:
                self.state = GameState.GAME_OVER
            else:
                self.spawn_ball()
                self.active_powerup = self.POWERUP_NONE
                self.paddle_width = self.PADDLE_NORMAL

        # Check level complete (only count destructible bricks)
        destructible = [b for b in self.bricks if b['type'] != self.BRICK_INDESTRUCTIBLE]
        if not destructible:
            self.level += 1
            if self.level >= len(self.levels):
                self.state = GameState.WIN
            else:
                self.load_level(self.level)
                self.balls = []
                self.spawn_ball()
                self.falling_powerups = []
                self.lasers = []
                self.active_powerup = self.POWERUP_NONE
                self.paddle_width = self.PADDLE_NORMAL

    def ball_brick_collision(self, ball, brick) -> bool:
        """Check ball-brick collision."""
        bx, by = int(ball['x']), int(ball['y'])

        for dx in range(2):
            for dy in range(2):
                px, py = bx + dx, by + dy
                if (brick['x'] <= px <= brick['x'] + brick['w'] and
                    brick['y'] <= py <= brick['y'] + brick['h']):
                    ball['dy'] = -ball['dy']
                    return True
        return False

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Draw score and lives
        self.display.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        for i in range(self.lives):
            self.display.set_pixel(52 + i * 4, 2, Colors.CYAN)
            self.display.set_pixel(53 + i * 4, 2, Colors.CYAN)

        # Draw separator
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)

        # Draw side walls
        self.display.draw_rect(0, 7, PLAY_LEFT, GRID_SIZE - 7, Colors.DARK_GRAY)
        self.display.draw_rect(PLAY_RIGHT, 7, GRID_SIZE - PLAY_RIGHT, GRID_SIZE - 7, Colors.DARK_GRAY)

        # Draw bricks
        for brick in self.bricks:
            self.display.draw_rect(brick['x'], brick['y'], brick['w'], brick['h'], brick['color'])

        # Draw paddle — top row matches active powerup color
        paddle_ix = int(self.paddle_x)
        powerup_paddle_colors = {
            self.POWERUP_EXTEND: Colors.CYAN,
            self.POWERUP_LASER: Colors.RED,
            self.POWERUP_SLOW: Colors.GREEN,
            self.POWERUP_MULTI: Colors.MAGENTA,
        }
        color = powerup_paddle_colors.get(self.active_powerup, Colors.CYAN)
        for i in range(self.paddle_width):
            self.display.set_pixel(paddle_ix + i, self.paddle_y, color)
            self.display.set_pixel(paddle_ix + i, self.paddle_y + 1, Colors.BLUE)

        # Draw balls
        for ball in self.balls:
            bx, by = int(ball['x']), int(ball['y'])
            self.display.set_pixel(bx, by, Colors.WHITE)
            self.display.set_pixel(bx + 1, by, Colors.WHITE)
            self.display.set_pixel(bx, by + 1, Colors.WHITE)
            self.display.set_pixel(bx + 1, by + 1, Colors.WHITE)

        # Draw lasers
        for laser in self.lasers:
            lx, ly = int(laser['x']), int(laser['y'])
            self.display.set_pixel(lx, ly, Colors.RED)
            self.display.set_pixel(lx, ly + 1, Colors.RED)
            self.display.set_pixel(lx, ly + 2, Colors.ORANGE)

        # Draw falling power-ups
        powerup_colors = {
            self.POWERUP_EXTEND: Colors.CYAN,
            self.POWERUP_LASER: Colors.RED,
            self.POWERUP_SLOW: Colors.GREEN,
            self.POWERUP_MULTI: Colors.MAGENTA,
            self.POWERUP_LIFE: Colors.GRAY,
        }
        powerup_letters = {
            self.POWERUP_EXTEND: 'E',  # Extend
            self.POWERUP_LASER: 'L',   # Laser
            self.POWERUP_SLOW: 'S',    # Slow
            self.POWERUP_MULTI: 'M',   # Multi-ball
            self.POWERUP_LIFE: 'P',    # Player (extra life)
        }
        for powerup in self.falling_powerups:
            px, py = int(powerup['x']), int(powerup['y'])
            color = powerup_colors.get(powerup['type'], Colors.WHITE)
            letter = powerup_letters.get(powerup['type'], '?')
            # Draw capsule background (6x5 pill shape)
            for dx in range(6):
                for dy in range(5):
                    # Rounded corners
                    if (dx == 0 or dx == 5) and (dy == 0 or dy == 4):
                        continue
                    self.display.set_pixel(px - 2 + dx, py - 1 + dy, color)
            # Draw letter in contrasting color
            self.display.draw_text_small(px - 1, py, letter, Colors.BLACK)

        # Draw launch prompt
        if self.balls and not self.balls[0]['launched']:
            level_name = self.levels[self.level % len(self.levels)]['name']
            self.display.draw_text_small(12, 38, level_name, Colors.YELLOW)
            self.display.draw_text_small(8, 50, "BTN:START", Colors.GRAY)

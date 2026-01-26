"""
Flappy Bird - Tap to fly through pipes
======================================
Tap to flap, navigate through pipe gaps. Don't hit the pipes or ground!

Controls:
  Space      - Flap (gain upward velocity)
  Escape     - Return to menu
"""

import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE


class Flappy(Game):
    name = "FLAPPY"
    description = "Tap to flap through pipes!"
    category = "modern"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Bird properties
        self.bird_x = 15  # Fixed horizontal position
        self.bird_y = 30.0  # Vertical position (float for smooth movement)
        self.bird_vy = 0.0  # Vertical velocity

        # Physics
        self.gravity = 120.0  # Pixels per second squared
        self.flap_strength = -45.0  # Upward velocity on flap
        self.max_fall_speed = 80.0

        # Ground
        self.ground_y = GRID_SIZE - 4

        # Pipes
        self.pipes = []  # List of {'x': float, 'gap_y': int, 'scored': bool}
        self.pipe_speed = 40.0  # Pixels per second
        self.pipe_width = 6
        self.gap_height = 16  # Height of the passable gap
        self.pipe_spacing = 30  # Horizontal distance between pipes

        # Spawn first pipe
        self.spawn_pipe(GRID_SIZE + 10)

        # Animation
        self.wing_timer = 0
        self.wing_up = False

        # Game started flag (wait for first flap)
        self.started = False

    def spawn_pipe(self, x: float):
        """Spawn a new pipe at the given x position."""
        # Random gap position, leaving room at top and bottom
        min_gap_y = 12  # Below HUD
        max_gap_y = self.ground_y - self.gap_height - 4
        gap_y = random.randint(min_gap_y, max_gap_y)

        self.pipes.append({
            'x': x,
            'gap_y': gap_y,
            'scored': False
        })

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Flap on action
        if input_state.action:
            self.bird_vy = self.flap_strength
            self.started = True
            self.wing_up = True
            self.wing_timer = 0.1

        # Don't move until first flap
        if not self.started:
            return

        # Apply gravity
        self.bird_vy += self.gravity * dt
        self.bird_vy = min(self.bird_vy, self.max_fall_speed)

        # Move bird
        self.bird_y += self.bird_vy * dt

        # Wing animation
        if self.wing_timer > 0:
            self.wing_timer -= dt
            if self.wing_timer <= 0:
                self.wing_up = False

        # Check ground collision
        if self.bird_y >= self.ground_y - 2:
            self.state = GameState.GAME_OVER
            return

        # Check ceiling
        if self.bird_y < 8:
            self.bird_y = 8
            self.bird_vy = 0

        # Move pipes
        for pipe in self.pipes:
            pipe['x'] -= self.pipe_speed * dt

            # Score when passing pipe
            if not pipe['scored'] and pipe['x'] + self.pipe_width < self.bird_x:
                pipe['scored'] = True
                self.score += 1
                # Speed up slightly
                self.pipe_speed = min(70, self.pipe_speed + 1)

        # Remove off-screen pipes
        self.pipes = [p for p in self.pipes if p['x'] > -self.pipe_width]

        # Spawn new pipes
        if self.pipes:
            rightmost = max(p['x'] for p in self.pipes)
            if rightmost < GRID_SIZE - self.pipe_spacing + 10:
                self.spawn_pipe(rightmost + self.pipe_spacing)

        # Check pipe collisions
        bird_box = (self.bird_x - 1, int(self.bird_y) - 1, 3, 3)  # x, y, w, h
        for pipe in self.pipes:
            px = int(pipe['x'])
            gap_y = pipe['gap_y']

            # Top pipe collision
            if self.rect_collision(bird_box, (px, 7, self.pipe_width, gap_y - 7)):
                self.state = GameState.GAME_OVER
                return

            # Bottom pipe collision
            bottom_top = gap_y + self.gap_height
            if self.rect_collision(bird_box, (px, bottom_top, self.pipe_width, self.ground_y - bottom_top)):
                self.state = GameState.GAME_OVER
                return

    def rect_collision(self, r1, r2) -> bool:
        """Check if two rectangles (x, y, w, h) overlap."""
        x1, y1, w1, h1 = r1
        x2, y2, w2, h2 = r2
        return (x1 < x2 + w2 and x1 + w1 > x2 and
                y1 < y2 + h2 and y1 + h1 > y2)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Sky background (dark blue)
        for y in range(7, self.ground_y):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, (0, 0, 30))

        # Draw pipes
        for pipe in self.pipes:
            px = int(pipe['x'])
            gap_y = pipe['gap_y']

            # Top pipe
            for x in range(px, px + self.pipe_width):
                for y in range(7, gap_y):
                    if 0 <= x < GRID_SIZE:
                        # Pipe edge
                        if x == px or x == px + self.pipe_width - 1:
                            self.display.set_pixel(x, y, (0, 100, 0))
                        else:
                            self.display.set_pixel(x, y, Colors.GREEN)

            # Top pipe lip
            for x in range(px - 1, px + self.pipe_width + 1):
                for y in range(gap_y - 2, gap_y):
                    if 0 <= x < GRID_SIZE:
                        self.display.set_pixel(x, y, Colors.GREEN)

            # Bottom pipe
            bottom_top = gap_y + self.gap_height
            for x in range(px, px + self.pipe_width):
                for y in range(bottom_top, self.ground_y):
                    if 0 <= x < GRID_SIZE:
                        if x == px or x == px + self.pipe_width - 1:
                            self.display.set_pixel(x, y, (0, 100, 0))
                        else:
                            self.display.set_pixel(x, y, Colors.GREEN)

            # Bottom pipe lip
            for x in range(px - 1, px + self.pipe_width + 1):
                for y in range(bottom_top, bottom_top + 2):
                    if 0 <= x < GRID_SIZE:
                        self.display.set_pixel(x, y, Colors.GREEN)

        # Draw ground
        for x in range(GRID_SIZE):
            for y in range(self.ground_y, GRID_SIZE):
                self.display.set_pixel(x, y, (100, 70, 40))  # Brown
        # Ground top edge
        for x in range(GRID_SIZE):
            self.display.set_pixel(x, self.ground_y, (60, 180, 60))  # Grass

        # Draw bird (3x3 yellow)
        bx, by = self.bird_x, int(self.bird_y)
        bird_color = Colors.YELLOW

        # Body
        for dx in range(-1, 2):
            for dy in range(-1, 2):
                self.display.set_pixel(bx + dx, by + dy, bird_color)

        # Eye
        self.display.set_pixel(bx + 1, by - 1, Colors.WHITE)
        self.display.set_pixel(bx + 1, by, Colors.BLACK)  # Pupil

        # Beak
        self.display.set_pixel(bx + 2, by, Colors.ORANGE)

        # Wing (animated)
        wing_y = by if self.wing_up else by + 1
        self.display.set_pixel(bx - 1, wing_y, Colors.ORANGE)

        # HUD
        self.display.draw_line(0, 6, 63, 6, Colors.DARK_GRAY)
        self.display.draw_text_small(28, 1, f"{self.score}", Colors.WHITE)

        # Start prompt
        if not self.started:
            self.display.draw_text_small(8, 30, "SPACE:FLAP", Colors.WHITE)

    def draw_game_over(self):
        """Custom game over screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(16, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(4, 50, "SPACE:RETRY", Colors.GRAY)

"""
DVD Bounce - Classic screensaver
================================
The iconic bouncing rectangle that changes color on edge hits.
Extra celebration when it hits a corner!

Controls:
  Left/Right - Adjust speed
  Up/Down    - Cycle color palette
  Space      - Randomize position/direction
  Escape     - Exit
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


COLORS = [
    (255, 0, 0),      # Red
    (255, 127, 0),    # Orange
    (255, 255, 0),    # Yellow
    (0, 255, 0),      # Green
    (0, 255, 255),    # Cyan
    (0, 127, 255),    # Light blue
    (127, 0, 255),    # Purple
    (255, 0, 255),    # Magenta
    (255, 0, 127),    # Pink
]


class DVD(Visual):
    name = "DVD"
    description = "Bouncing logo"
    category = "household"

    LOGO_W = 12
    LOGO_H = 8

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 25.0  # Pixels per second

        # Position (float for smooth movement)
        self.x = random.uniform(0, GRID_SIZE - self.LOGO_W)
        self.y = random.uniform(0, GRID_SIZE - self.LOGO_H)

        # Velocity
        self.dx = random.choice([-1, 1])
        self.dy = random.choice([-1, 1])

        # Color
        self.color_idx = random.randint(0, len(COLORS) - 1)

        # Corner hit celebration
        self.corner_flash = 0.0

    def _next_color(self):
        """Advance to next color."""
        self.color_idx = (self.color_idx + 1) % len(COLORS)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if (input_state.action_l or input_state.action_r):
            self.reset()
            consumed = True

        if input_state.right:
            self.speed = min(60.0, self.speed + 2.0)
            consumed = True

        if input_state.left:
            self.speed = max(10.0, self.speed - 2.0)
            consumed = True

        if input_state.up_pressed:
            self.color_idx = (self.color_idx + 1) % len(COLORS)
            consumed = True

        if input_state.down_pressed:
            self.color_idx = (self.color_idx - 1) % len(COLORS)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Decay corner flash
        if self.corner_flash > 0:
            self.corner_flash -= dt * 3

        # Move
        self.x += self.dx * self.speed * dt
        self.y += self.dy * self.speed * dt

        # Bounce off edges
        hit_x = False
        hit_y = False

        if self.x <= 0:
            self.x = 0
            self.dx = 1
            hit_x = True
        elif self.x >= GRID_SIZE - self.LOGO_W:
            self.x = GRID_SIZE - self.LOGO_W
            self.dx = -1
            hit_x = True

        if self.y <= 0:
            self.y = 0
            self.dy = 1
            hit_y = True
        elif self.y >= GRID_SIZE - self.LOGO_H:
            self.y = GRID_SIZE - self.LOGO_H
            self.dy = -1
            hit_y = True

        # Change color on any edge hit
        if hit_x or hit_y:
            self._next_color()

        # Corner hit - extra celebration!
        if hit_x and hit_y:
            self.corner_flash = 1.0

    def draw(self):
        # Background - flash white on corner hit
        if self.corner_flash > 0:
            flash = int(255 * self.corner_flash)
            self.display.clear((flash, flash, flash))
        else:
            self.display.clear(Colors.BLACK)

        # Draw simple rectangle
        color = COLORS[self.color_idx]
        ix, iy = int(self.x), int(self.y)

        for py in range(self.LOGO_H):
            for px in range(self.LOGO_W):
                screen_x = ix + px
                screen_y = iy + py
                if 0 <= screen_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                    self.display.set_pixel(screen_x, screen_y, color)

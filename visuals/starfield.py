"""
Starfield - Classic 3D starfield effect
=======================================
Stars fly toward the viewer from the center of the screen.

Controls:
  Left/Right - Adjust speed
  Space      - Toggle warp mode
  Escape     - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


class Star:
    def __init__(self):
        self.reset()

    def reset(self):
        # Position in 3D space (z is depth, 0 = at viewer, 1 = far away)
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(0.1, 1.0)
        self.x = math.cos(angle) * distance
        self.y = math.sin(angle) * distance
        self.z = random.uniform(0.5, 1.0)


class Starfield(Visual):
    name = "STARFIELD"
    description = "3D star tunnel"
    category = "nature"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 0.5  # Base speed
        self.warp = False
        self.stars = [Star() for _ in range(100)]

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right:
            self.speed = min(2.0, self.speed + 0.05)
            consumed = True
        if input_state.left:
            self.speed = max(0.1, self.speed - 0.05)
            consumed = True
        if (input_state.action_l or input_state.action_r):
            self.warp = not self.warp
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        effective_speed = self.speed * (3.0 if self.warp else 1.0)

        for star in self.stars:
            # Move star toward viewer
            star.z -= effective_speed * dt

            # Reset star if it passes the viewer
            if star.z <= 0.01:
                star.reset()
                star.z = 1.0

    def draw(self):
        self.display.clear(Colors.BLACK)
        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2

        # Sort stars by depth (far to near) for proper layering
        sorted_stars = sorted(self.stars, key=lambda s: -s.z)

        for star in sorted_stars:
            # Project 3D position to 2D screen
            if star.z > 0.01:
                screen_x = int(cx + (star.x / star.z) * cx)
                screen_y = int(cy + (star.y / star.z) * cy)

                # Brightness based on depth (closer = brighter)
                brightness = int(255 * (1.0 - star.z))
                brightness = max(50, min(255, brightness))

                # Size based on depth (closer = larger)
                if star.z < 0.2:
                    size = 2
                else:
                    size = 1

                # Draw star if on screen
                if 0 <= screen_x < GRID_SIZE and 0 <= screen_y < GRID_SIZE:
                    if self.warp:
                        # Warp mode: draw trails
                        color = (brightness, brightness, int(brightness * 0.8))
                        # Draw a short line from current to previous position
                        prev_z = star.z + self.speed * 0.1
                        prev_x = int(cx + (star.x / prev_z) * cx)
                        prev_y = int(cy + (star.y / prev_z) * cy)
                        self.display.draw_line(prev_x, prev_y, screen_x, screen_y, color)
                    else:
                        color = (brightness, brightness, brightness)
                        self.display.set_pixel(screen_x, screen_y, color)
                        if size == 2:
                            self.display.set_pixel(screen_x + 1, screen_y, color)
                            self.display.set_pixel(screen_x, screen_y + 1, color)

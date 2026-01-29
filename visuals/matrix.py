"""
Matrix - Digital rain effect
============================
Falling green characters like The Matrix.

Controls:
  Left/Right - Adjust speed
  Space      - Toggle rainbow mode
  Escape     - Exit
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Drop:
    """A single falling drop with a trail."""
    def __init__(self, x):
        self.x = x
        self.reset()

    def reset(self):
        self.y = random.uniform(-20, -1)
        self.speed = random.uniform(15, 35)
        self.length = random.randint(5, 15)
        self.char_timer = 0
        self.chars = [random.randint(0, 9) for _ in range(self.length)]


class Matrix(Visual):
    name = "MATRIX"
    description = "Digital rain"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed_mult = 1.0
        self.rainbow = False

        # Create drops for each column (with some density variation)
        self.drops = []
        for x in range(GRID_SIZE):
            # Multiple drops per column, staggered
            for _ in range(random.randint(1, 2)):
                drop = Drop(x)
                drop.y = random.uniform(-GRID_SIZE * 2, GRID_SIZE)
                self.drops.append(drop)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right:
            self.speed_mult = min(3.0, self.speed_mult + 0.1)
            consumed = True
        if input_state.left:
            self.speed_mult = max(0.3, self.speed_mult - 0.1)
            consumed = True
        if (input_state.action_l or input_state.action_r):
            self.rainbow = not self.rainbow
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        for drop in self.drops:
            # Move drop down
            drop.y += drop.speed * self.speed_mult * dt

            # Randomly change characters in trail
            drop.char_timer += dt
            if drop.char_timer > 0.1:
                drop.char_timer = 0
                idx = random.randint(0, drop.length - 1)
                drop.chars[idx] = random.randint(0, 9)

            # Reset when fully off screen
            if drop.y - drop.length > GRID_SIZE:
                drop.reset()

    def _get_color(self, brightness, drop_x):
        """Get color based on brightness and mode."""
        if self.rainbow:
            # Cycle through hues based on x position and time
            hue = (drop_x / GRID_SIZE + self.time * 0.1) % 1.0
            h = hue * 6.0
            i = int(h)
            f = h - i
            v = brightness / 255.0

            if i == 0:
                return (int(255 * v), int(255 * v * f), 0)
            elif i == 1:
                return (int(255 * v * (1 - f)), int(255 * v), 0)
            elif i == 2:
                return (0, int(255 * v), int(255 * v * f))
            elif i == 3:
                return (0, int(255 * v * (1 - f)), int(255 * v))
            elif i == 4:
                return (int(255 * v * f), 0, int(255 * v))
            else:
                return (int(255 * v), 0, int(255 * v * (1 - f)))
        else:
            # Classic green
            return (0, brightness, int(brightness * 0.4))

    def draw(self):
        self.display.clear(Colors.BLACK)

        for drop in self.drops:
            head_y = int(drop.y)

            for i in range(drop.length):
                y = head_y - i

                if 0 <= y < GRID_SIZE:
                    # Brightness fades along trail
                    if i == 0:
                        # Head is brightest (white-ish for matrix look)
                        if self.rainbow:
                            color = self._get_color(255, drop.x)
                        else:
                            color = (200, 255, 200)
                    else:
                        # Trail fades
                        fade = 1.0 - (i / drop.length)
                        brightness = int(200 * fade * fade)
                        color = self._get_color(brightness, drop.x)

                    self.display.set_pixel(drop.x, y, color)

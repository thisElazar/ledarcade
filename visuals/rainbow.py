"""
Rainbow - Classic Color Wheel Cycle
====================================
The iconic LED panel demo - smooth HSV color cycling
with multiple pattern modes.

Controls:
  Left/Right - Adjust cycle speed
  Up/Down    - Cycle through pattern modes
  Space      - Reverse direction
  Escape     - Exit
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


class Rainbow(Visual):
    name = "RAINBOW"
    description = "Color wheel cycle"
    category = "digital"

    # Pattern mode names
    MODE_NAMES = [
        "SOLID",
        "HORIZONTAL",
        "VERTICAL",
        "RADIAL",
        "DIAGONAL",
        "SPIRAL",
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.direction = 1  # 1 = forward, -1 = reverse
        self.mode = 0  # Current pattern mode
        self.num_modes = len(self.MODE_NAMES)

        # Center of display for radial/spiral patterns
        self.center_x = GRID_SIZE / 2
        self.center_y = GRID_SIZE / 2

        # Max distance from center (for normalization)
        self.max_radius = math.sqrt(self.center_x**2 + self.center_y**2)

    def hsv_to_rgb(self, h: float, s: float = 1.0, v: float = 1.0) -> tuple:
        """
        Convert HSV to RGB color.
        h: hue (0.0 - 1.0, wraps around)
        s: saturation (0.0 - 1.0)
        v: value/brightness (0.0 - 1.0)
        Returns (r, g, b) tuple with values 0-255.
        """
        h = h % 1.0  # Wrap hue to 0-1 range

        if s == 0.0:
            # Grayscale
            gray = int(v * 255)
            return (gray, gray, gray)

        i = int(h * 6.0)
        f = (h * 6.0) - i
        p = v * (1.0 - s)
        q = v * (1.0 - s * f)
        t = v * (1.0 - s * (1.0 - f))

        i = i % 6

        if i == 0:
            r, g, b = v, t, p
        elif i == 1:
            r, g, b = q, v, p
        elif i == 2:
            r, g, b = p, v, t
        elif i == 3:
            r, g, b = p, q, v
        elif i == 4:
            r, g, b = t, p, v
        else:
            r, g, b = v, p, q

        return (int(r * 255), int(g * 255), int(b * 255))

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Speed control
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.left:
            self.speed = max(0.1, self.speed - 0.1)
            consumed = True

        # Mode cycling
        if input_state.up:
            self.mode = (self.mode + 1) % self.num_modes
            consumed = True
        if input_state.down:
            self.mode = (self.mode - 1) % self.num_modes
            consumed = True

        # Direction reversal
        if (input_state.action_l or input_state.action_r):
            self.direction *= -1
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed * self.direction

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Base hue offset from time (completes cycle every ~4 seconds at speed 1.0)
        base_hue = self.time * 0.25

        if self.mode == 0:
            # SOLID: Entire display is one color cycling through hue
            color = self.hsv_to_rgb(base_hue)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    self.display.set_pixel(x, y, color)

        elif self.mode == 1:
            # HORIZONTAL: Gradient scrolling left/right
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    hue = base_hue + (x / GRID_SIZE)
                    color = self.hsv_to_rgb(hue)
                    self.display.set_pixel(x, y, color)

        elif self.mode == 2:
            # VERTICAL: Gradient scrolling up/down
            for y in range(GRID_SIZE):
                hue = base_hue + (y / GRID_SIZE)
                color = self.hsv_to_rgb(hue)
                for x in range(GRID_SIZE):
                    self.display.set_pixel(x, y, color)

        elif self.mode == 3:
            # RADIAL: Circular gradient emanating from center
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    dx = x - self.center_x
                    dy = y - self.center_y
                    dist = math.sqrt(dx * dx + dy * dy)
                    normalized_dist = dist / self.max_radius
                    hue = base_hue + normalized_dist
                    color = self.hsv_to_rgb(hue)
                    self.display.set_pixel(x, y, color)

        elif self.mode == 4:
            # DIAGONAL: Gradient along diagonal
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    # Diagonal position normalized to 0-1
                    diag = (x + y) / (2 * GRID_SIZE)
                    hue = base_hue + diag
                    color = self.hsv_to_rgb(hue)
                    self.display.set_pixel(x, y, color)

        elif self.mode == 5:
            # SPIRAL: Combines angle and distance from center
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    dx = x - self.center_x
                    dy = y - self.center_y
                    dist = math.sqrt(dx * dx + dy * dy)
                    angle = math.atan2(dy, dx)  # -pi to pi

                    # Normalize angle to 0-1
                    normalized_angle = (angle + math.pi) / (2 * math.pi)
                    normalized_dist = dist / self.max_radius

                    # Combine angle and distance for spiral effect
                    # More spiral arms with higher multiplier on dist
                    hue = base_hue + normalized_angle + (normalized_dist * 2)
                    color = self.hsv_to_rgb(hue)
                    self.display.set_pixel(x, y, color)

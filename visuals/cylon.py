"""
Cylon - Larson Scanner Effect
=============================
The iconic sweeping eye from Knight Rider and Battlestar Galactica.
A bright eye sweeps horizontally with an exponential decay trail.

Controls:
  Left/Right - Adjust sweep speed
  Up/Down    - Cycle color palette
  Space      - Toggle single bar / full screen mode
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


class Cylon(Visual):
    name = "CYLON"
    description = "Larson scanner"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Scanner position (0 to GRID_SIZE-1, fractional for smooth movement)
        self.position = 0.0
        self.direction = 1  # 1 = moving right, -1 = moving left

        # Eye width (pixels)
        self.eye_width = 5

        # Speed control
        self.speed = 40.0  # Pixels per second
        self.min_speed = 10.0
        self.max_speed = 120.0

        # Color palettes
        self.palette_index = 0
        self.palettes = ["red", "blue", "cyan", "rainbow"]

        # Display mode: 0 = single bar, 1 = full screen (multiple scanners)
        self.mode = 0

        # Trail buffer - stores brightness (0-255) for each column
        # In full mode, we have a trail buffer per row
        self.trail = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Decay rate (multiplier per frame, lower = longer trail)
        self.decay = 0.85

    def _get_color(self, brightness: float, row: int = 0) -> tuple:
        """Convert brightness (0-1) to color based on current palette."""
        if brightness <= 0:
            return Colors.BLACK

        palette = self.palettes[self.palette_index]

        if palette == "red":
            # Classic Knight Rider red
            return (int(255 * brightness), int(20 * brightness), int(10 * brightness))

        elif palette == "blue":
            # Blue variant
            return (int(30 * brightness), int(50 * brightness), int(255 * brightness))

        elif palette == "cyan":
            # Cyan/teal
            return (int(20 * brightness), int(255 * brightness), int(200 * brightness))

        else:  # rainbow
            # Different hue per row for rainbow effect
            hue = (row / GRID_SIZE + self.time * 0.1) % 1.0
            return self._hsv_to_rgb(hue, 1.0, brightness)

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> tuple:
        """Convert HSV to RGB."""
        if s == 0:
            return (int(255 * v), int(255 * v), int(255 * v))

        h = h * 6.0
        i = int(h)
        f = h - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))

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

        return (int(255 * r), int(255 * g), int(255 * b))

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right - adjust speed
        if input_state.right:
            self.speed = min(self.max_speed, self.speed + 5.0)
            consumed = True
        if input_state.left:
            self.speed = max(self.min_speed, self.speed - 5.0)
            consumed = True

        # Up/Down - cycle color palette
        if input_state.up:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index - 1) % len(self.palettes)
            consumed = True

        # Space - toggle mode
        if (input_state.action_l or input_state.action_r):
            self.mode = (self.mode + 1) % 2
            # Clear trails when switching modes
            self.trail = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Move the scanner position
        self.position += self.direction * self.speed * dt

        # Bounce at edges
        if self.position >= GRID_SIZE - 1:
            self.position = GRID_SIZE - 1
            self.direction = -1
        elif self.position <= 0:
            self.position = 0
            self.direction = 1

        # Update trail with decay
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.trail[y][x] *= self.decay

        # Add eye brightness to trail
        eye_center = int(self.position)
        half_width = self.eye_width // 2

        if self.mode == 0:
            # Single bar mode - scanner spans all rows at center
            for y in range(GRID_SIZE):
                for i in range(-half_width, half_width + 1):
                    x = eye_center + i
                    if 0 <= x < GRID_SIZE:
                        # Gaussian-like brightness falloff from center
                        dist = abs(i) / (half_width + 1)
                        brightness = 1.0 - dist * dist
                        # Keep the brighter value
                        self.trail[y][x] = max(self.trail[y][x], brightness)
        else:
            # Full screen mode - multiple scanners at different phases
            for y in range(GRID_SIZE):
                # Each row has a phase offset
                phase_offset = y / GRID_SIZE * math.pi * 2
                # Calculate position for this row's scanner
                row_pos = (math.sin(self.time * self.speed / 20.0 + phase_offset) + 1) / 2
                row_center = int(row_pos * (GRID_SIZE - 1))

                for i in range(-half_width, half_width + 1):
                    x = row_center + i
                    if 0 <= x < GRID_SIZE:
                        dist = abs(i) / (half_width + 1)
                        brightness = 1.0 - dist * dist
                        self.trail[y][x] = max(self.trail[y][x], brightness)

    def draw(self):
        self.display.clear(Colors.BLACK)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                brightness = self.trail[y][x]
                if brightness > 0.01:  # Skip very dim pixels
                    color = self._get_color(brightness, y)
                    self.display.set_pixel(x, y, color)

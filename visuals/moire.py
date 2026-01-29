"""
Moire - Classic interference pattern effect
============================================
Overlapping geometric patterns creating hypnotic interference effects.
Two pattern layers animate with slight offset/rotation relative to each other.

Controls:
  Left/Right - Adjust animation speed
  Up/Down    - Cycle color palette
  Space      - Cycle pattern type
  Escape     - Exit
"""

import math
from . import Visual, Display, Colors, GRID_SIZE


class Moire(Visual):
    name = "MOIRE"
    description = "Interference patterns"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.pattern_index = 0
        self.palette_index = 0

        # Pattern types: circles, lines, grid, radial
        self.patterns = [
            ("circles", self._draw_circles),
            ("lines", self._draw_lines),
            ("grid", self._draw_grid),
            ("radial", self._draw_radial),
        ]

        # Color palettes
        self.palettes = ["bw", "rainbow", "fire", "ocean", "matrix"]

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True
        # Up/Down cycle color palette
        if input_state.up_pressed:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True
        if input_state.down_pressed:
            self.palette_index = (self.palette_index - 1) % len(self.palettes)
            consumed = True
        # Action cycles pattern type
        if (input_state.action_l or input_state.action_r):
            self.pattern_index = (self.pattern_index + 1) % len(self.patterns)
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

    def _get_color(self, value: float) -> tuple:
        """Convert interference value (0-1) to color based on current palette."""
        palette = self.palettes[self.palette_index]

        if palette == "bw":
            intensity = int(255 * value)
            return (intensity, intensity, intensity)

        elif palette == "rainbow":
            h = (value + self.time * 0.1) % 1.0
            h6 = h * 6.0
            i = int(h6)
            f = h6 - i
            if i == 0:
                return (255, int(255 * f), 0)
            elif i == 1:
                return (int(255 * (1 - f)), 255, 0)
            elif i == 2:
                return (0, 255, int(255 * f))
            elif i == 3:
                return (0, int(255 * (1 - f)), 255)
            elif i == 4:
                return (int(255 * f), 0, 255)
            else:
                return (255, 0, int(255 * (1 - f)))

        elif palette == "fire":
            if value < 0.33:
                t = value / 0.33
                return (int(255 * t), 0, 0)
            elif value < 0.66:
                t = (value - 0.33) / 0.33
                return (255, int(200 * t), 0)
            else:
                t = (value - 0.66) / 0.34
                return (255, 200 + int(55 * t), int(255 * t))

        elif palette == "ocean":
            if value < 0.5:
                t = value / 0.5
                return (0, int(100 * t), int(150 + 105 * t))
            else:
                t = (value - 0.5) / 0.5
                return (int(255 * t), 100 + int(155 * t), 255)

        else:  # matrix
            return (0, int(255 * value), int(80 * value))

    def _draw_circles(self):
        """Concentric circles pattern - two centers offset and moving."""
        cx1, cy1 = 32, 32  # First center (static)
        # Second center orbits around first
        offset = 8 + 4 * math.sin(self.time * 0.5)
        cx2 = 32 + offset * math.cos(self.time * 0.7)
        cy2 = 32 + offset * math.sin(self.time * 0.7)

        freq1 = 6.0  # Ring frequency for pattern 1
        freq2 = 6.5  # Slightly different frequency for moire

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Distance from each center
                d1 = math.sqrt((x - cx1) ** 2 + (y - cy1) ** 2)
                d2 = math.sqrt((x - cx2) ** 2 + (y - cy2) ** 2)

                # Create ring patterns with sine
                v1 = (math.sin(d1 * freq1 * 0.1) + 1) * 0.5
                v2 = (math.sin(d2 * freq2 * 0.1) + 1) * 0.5

                # XOR-like interference
                value = abs(v1 - v2)

                color = self._get_color(value)
                self.display.set_pixel(x, y, color)

    def _draw_lines(self):
        """Parallel lines at slightly different angles."""
        angle1 = self.time * 0.3
        angle2 = self.time * 0.3 + 0.1 + 0.05 * math.sin(self.time * 0.5)

        freq = 8.0  # Line spacing

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Project onto perpendicular direction for each angle
                px = x - 32
                py = y - 32

                # Line pattern 1
                proj1 = px * math.cos(angle1) + py * math.sin(angle1)
                v1 = (math.sin(proj1 * freq * 0.2) + 1) * 0.5

                # Line pattern 2
                proj2 = px * math.cos(angle2) + py * math.sin(angle2)
                v2 = (math.sin(proj2 * freq * 0.2) + 1) * 0.5

                # Interference
                value = abs(v1 - v2)

                color = self._get_color(value)
                self.display.set_pixel(x, y, color)

    def _draw_grid(self):
        """Two grid patterns at slightly different scales/rotations."""
        angle = self.time * 0.2
        scale1 = 8.0
        scale2 = 8.0 + 0.5 * math.sin(self.time * 0.4)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                px = x - 32
                py = y - 32

                # Rotate second grid
                rx = px * math.cos(angle) - py * math.sin(angle)
                ry = px * math.sin(angle) + py * math.cos(angle)

                # Grid pattern 1 (static)
                v1x = (math.sin(px * scale1 * 0.15) + 1) * 0.5
                v1y = (math.sin(py * scale1 * 0.15) + 1) * 0.5
                v1 = v1x * v1y

                # Grid pattern 2 (rotated)
                v2x = (math.sin(rx * scale2 * 0.15) + 1) * 0.5
                v2y = (math.sin(ry * scale2 * 0.15) + 1) * 0.5
                v2 = v2x * v2y

                # Interference
                value = abs(v1 - v2)

                color = self._get_color(value)
                self.display.set_pixel(x, y, color)

    def _draw_radial(self):
        """Radial spokes from two offset centers."""
        cx1, cy1 = 32, 32
        offset = 6 + 3 * math.sin(self.time * 0.6)
        cx2 = 32 + offset * math.cos(self.time * 0.5)
        cy2 = 32 + offset * math.sin(self.time * 0.5)

        spokes = 16  # Number of spokes

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Angle from each center
                a1 = math.atan2(y - cy1, x - cx1)
                a2 = math.atan2(y - cy2, x - cx2)

                # Spoke patterns
                v1 = (math.sin(a1 * spokes) + 1) * 0.5
                v2 = (math.sin(a2 * spokes + self.time) + 1) * 0.5

                # Interference
                value = abs(v1 - v2)

                color = self._get_color(value)
                self.display.set_pixel(x, y, color)

    def draw(self):
        self.display.clear(Colors.BLACK)
        # Call the current pattern's draw function
        _, draw_func = self.patterns[self.pattern_index]
        draw_func()

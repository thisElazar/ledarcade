"""
Twister - Classic rotating bars effect
======================================
Vertical color bars that appear to twist and rotate, creating
a 3D barber pole illusion through per-row phase offsets.

Controls:
  Left/Right - Adjust rotation speed
  Up/Down    - Cycle color palette
  Space      - Toggle twist intensity
  Escape     - Exit
"""

import math
from typing import Tuple
from . import Visual, Display, Colors, GRID_SIZE


class Twister(Visual):
    name = "TWISTER"
    description = "Rotating bars"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_index = 0
        self.twist_mode = 0  # 0=normal, 1=intense, 2=wave
        self.num_bars = 8  # Number of color bars

        # Available color palettes
        self.palettes = [
            self._palette_rainbow,
            self._palette_primary,
            self._palette_neon,
            self._palette_fire,
            self._palette_ice,
            self._palette_candy,
        ]
        self.palette_names = ["RAINBOW", "PRIMARY", "NEON", "FIRE", "ICE", "CANDY"]

    def _palette_rainbow(self, bar_index: int, num_bars: int) -> Tuple[int, int, int]:
        """Rainbow gradient across bars"""
        hue = bar_index / num_bars
        return self._hsv_to_rgb(hue, 1.0, 1.0)

    def _palette_primary(self, bar_index: int, num_bars: int) -> Tuple[int, int, int]:
        """Bold primary colors"""
        colors = [
            (255, 0, 0),    # Red
            (255, 255, 0),  # Yellow
            (0, 255, 0),    # Green
            (0, 255, 255),  # Cyan
            (0, 0, 255),    # Blue
            (255, 0, 255),  # Magenta
        ]
        return colors[bar_index % len(colors)]

    def _palette_neon(self, bar_index: int, num_bars: int) -> Tuple[int, int, int]:
        """Bright neon colors"""
        colors = [
            (255, 0, 128),   # Hot pink
            (0, 255, 128),   # Spring green
            (128, 0, 255),   # Purple
            (255, 128, 0),   # Orange
            (0, 128, 255),   # Sky blue
            (255, 255, 0),   # Yellow
        ]
        return colors[bar_index % len(colors)]

    def _palette_fire(self, bar_index: int, num_bars: int) -> Tuple[int, int, int]:
        """Fire/warm colors"""
        t = bar_index / num_bars
        if t < 0.33:
            return (255, int(200 * t / 0.33), 0)
        elif t < 0.66:
            return (255, 200 + int(55 * (t - 0.33) / 0.33), int(100 * (t - 0.33) / 0.33))
        else:
            return (255, 255, 100 + int(100 * (t - 0.66) / 0.34))

    def _palette_ice(self, bar_index: int, num_bars: int) -> Tuple[int, int, int]:
        """Cool ice/blue colors"""
        t = bar_index / num_bars
        r = int(100 + 155 * t)
        g = int(150 + 105 * t)
        b = 255
        return (r, g, b)

    def _palette_candy(self, bar_index: int, num_bars: int) -> Tuple[int, int, int]:
        """Candy/pastel stripes"""
        colors = [
            (255, 150, 200),  # Pink
            (255, 255, 255),  # White
            (150, 200, 255),  # Light blue
            (255, 255, 255),  # White
            (200, 255, 150),  # Light green
            (255, 255, 255),  # White
        ]
        return colors[bar_index % len(colors)]

    def _hsv_to_rgb(self, h: float, s: float, v: float) -> Tuple[int, int, int]:
        """Convert HSV to RGB. h, s, v in range [0, 1]"""
        if s == 0:
            val = int(v * 255)
            return (val, val, val)

        h = h * 6.0
        i = int(h)
        f = h - i
        p = v * (1 - s)
        q = v * (1 - s * f)
        t = v * (1 - s * (1 - f))

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
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True

        # Palette cycling
        if input_state.up:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index - 1) % len(self.palettes)
            consumed = True

        # Twist mode toggle
        if input_state.action:
            self.twist_mode = (self.twist_mode + 1) % 3
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

    def draw(self):
        self.display.clear(Colors.BLACK)
        palette_func = self.palettes[self.palette_index]

        # Bar width in radians (full circle / number of bars)
        bar_width = (2 * math.pi) / self.num_bars

        for y in range(GRID_SIZE):
            # Calculate twist amount based on y position and mode
            if self.twist_mode == 0:
                # Normal twist - linear phase offset per row
                twist_amount = 1.5
            elif self.twist_mode == 1:
                # Intense twist - more rotation per row
                twist_amount = 3.0
            else:
                # Wave twist - sinusoidal variation
                twist_amount = 1.5 + math.sin(self.time * 0.5) * 1.0

            # Phase offset for this row creates the twist illusion
            # The key: each row has a slightly different phase
            row_phase = (y / GRID_SIZE) * twist_amount * math.pi

            # Add time-based rotation
            base_phase = self.time * 2.0 + row_phase

            for x in range(GRID_SIZE):
                # Map x to angle (0 to 2*pi across the width)
                # This creates the "cylinder" effect
                angle = (x / GRID_SIZE) * 2 * math.pi + base_phase

                # Normalize angle to 0-2pi range
                angle = angle % (2 * math.pi)

                # Determine which bar this pixel belongs to
                bar_index = int(angle / bar_width) % self.num_bars

                # Get the base color for this bar
                color = palette_func(bar_index, self.num_bars)

                # Add shading based on angle to give 3D cylinder effect
                # The "front" of the cylinder (angle near pi) is brightest
                shade = (math.cos(angle - math.pi) + 1) / 2  # 0 to 1
                shade = 0.4 + shade * 0.6  # Map to 0.4 - 1.0 range

                # Apply shading
                shaded_color = (
                    int(color[0] * shade),
                    int(color[1] * shade),
                    int(color[2] * shade)
                )

                self.display.set_pixel(x, y, shaded_color)

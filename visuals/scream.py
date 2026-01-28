"""
The Scream - Edvard Munch animated
====================================
Munch's "The Scream" (1893) with animated swirling sky
and subtle figure tremor.

Controls:
  Up/Down    - Adjust animation speed
"""

import math
import random
import os
from . import Visual, Display, Colors, GRID_SIZE

try:
    from PIL import Image
    HAS_PIL = True
except ImportError:
    HAS_PIL = False


class Scream(Visual):
    name = "SCREAM"
    description = "Munch animated"
    category = "art"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0

        # Load image
        self.pixels = [[Colors.BLACK for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.load_image()

        # Classify pixels into zones for different animation
        self.sky_mask = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.water_mask = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.figure_mask = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._classify_pixels()

        # Phase offsets for organic animation
        self.phase_offsets = [[random.uniform(0, math.pi * 2)
                               for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def load_image(self):
        """Load The Scream image from assets."""
        if not HAS_PIL:
            self._draw_fallback()
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        image_path = os.path.join(project_dir, "assets", "scream.png")

        if not os.path.exists(image_path):
            self._draw_fallback()
            return

        try:
            img = Image.open(image_path)
            img = img.convert("RGB")
            img = img.resize((GRID_SIZE, GRID_SIZE), Image.Resampling.NEAREST)

            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    r, g, b = img.getpixel((x, y))
                    self.pixels[y][x] = (r, g, b)
        except Exception:
            self._draw_fallback()

    def _draw_fallback(self):
        """Simple gradient if image can't be loaded."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if y < 35:
                    # Orange sky
                    t = y / 35.0
                    self.pixels[y][x] = (200, int(100 + 50 * t), int(30 * t))
                else:
                    # Dark bridge/ground
                    self.pixels[y][x] = (40, 30, 25)

    def _classify_pixels(self):
        """Identify sky, water, and figure regions by color."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r, g, b = self.pixels[y][x]
                brightness = (r + g + b) / 3.0

                # Sky: warm orange/yellow/red tones in upper portion
                # High red, moderate-to-high green, low blue
                is_warm = r > 100 and r > b and (r + g) > (b * 3)
                is_sky_region = y < 45
                if is_warm and is_sky_region and brightness > 40:
                    self.sky_mask[y][x] = True
                    continue

                # Water/landscape: darker blue-green tones in lower portion
                is_dark_blue = b > 40 and b > r and y > 25
                is_dark_green = g > 40 and g > r and brightness < 120 and y > 25
                if is_dark_blue or is_dark_green:
                    self.water_mask[y][x] = True
                    continue

                # Figure: very dark pixels in the central area
                is_dark = brightness < 50
                is_central = 20 < x < 44 and 20 < y < 58
                if is_dark and is_central:
                    self.figure_mask[y][x] = True

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.speed = min(3.0, self.speed + 0.05)
            consumed = True
        if input_state.down:
            self.speed = max(0.2, self.speed - 0.05)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

    def draw(self):
        """Draw The Scream with animated swirling sky."""
        t = self.time

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r, g, b = self.pixels[y][x]

                if self.sky_mask[y][x]:
                    # Swirling sky: sinusoidal color shift that flows
                    # in wave-like bands across the sky
                    phase = self.phase_offsets[y][x]

                    # Two overlapping waves for organic movement
                    wave1 = math.sin(t * 1.5 + y * 0.15 + phase)
                    wave2 = math.sin(t * 0.8 + x * 0.1 + y * 0.08 + phase * 0.7)
                    combined = (wave1 + wave2) * 0.5  # -1 to 1

                    # Shift warm colors: push between orange and deeper red
                    shift = int(combined * 20)
                    r = max(0, min(255, r + shift))
                    g = max(0, min(255, g + int(shift * 0.6)))
                    b = max(0, min(255, b + int(shift * 0.2)))

                elif self.water_mask[y][x]:
                    # Subtle ripple on water/landscape
                    phase = self.phase_offsets[y][x]
                    ripple = math.sin(t * 1.2 + x * 0.2 + phase) * 0.5 + 0.5
                    shift = int((ripple - 0.5) * 12)
                    r = max(0, min(255, r + shift // 3))
                    g = max(0, min(255, g + shift // 2))
                    b = max(0, min(255, b + shift))

                elif self.figure_mask[y][x]:
                    # Very subtle tremor on the figure — slight brightness pulse
                    pulse = math.sin(t * 2.5) * 0.5 + 0.5
                    shift = int((pulse - 0.5) * 6)  # very subtle
                    r = max(0, min(255, r + shift))
                    g = max(0, min(255, g + shift))
                    b = max(0, min(255, b + shift))

                self.display.set_pixel(x, y, (r, g, b))

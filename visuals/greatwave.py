"""
Great Wave - Hokusai's masterpiece animated
============================================
Katsushika Hokusai's "The Great Wave off Kanagawa" with
a gentle shimmering effect on the sea.

Controls:
  Up/Down    - Adjust shimmer speed
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


class GreatWave(Visual):
    name = "GREATWAVE"
    description = "Hokusai animated"
    category = "art"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 2.0  # Fast shimmer looks best

        # Load image
        self.pixels = [[Colors.BLACK for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.load_image()

        # Pre-calculate which pixels are "blue" (the sea)
        # Store the base hue info for each blue pixel
        self.blue_mask = [[False for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.identify_sea_pixels()

        # Each blue pixel gets a random phase offset for organic shimmer
        self.phase_offsets = [[random.uniform(0, math.pi * 2) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def load_image(self):
        """Load the Great Wave image from assets."""
        if not HAS_PIL:
            self.draw_fallback()
            return

        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_dir = os.path.dirname(script_dir)
        image_path = os.path.join(project_dir, "assets", "greatwave.png")

        if not os.path.exists(image_path):
            self.draw_fallback()
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
            self.draw_fallback()

    def draw_fallback(self):
        """Simple pattern if image can't be loaded."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if y < 20:
                    self.pixels[y][x] = (200, 180, 150)
                else:
                    self.pixels[y][x] = (30, 60, 100)

    def identify_sea_pixels(self):
        """Find pixels that are blue-ish (the sea areas)."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r, g, b = self.pixels[y][x]

                # Check if pixel is blue-ish:
                # Blue channel is significant and blue > red
                # This catches the deep blues and teals of the water
                is_blue = b > 60 and b > r and g < 200

                # Also exclude very bright pixels (foam/sky)
                brightness = (r + g + b) / 3
                is_not_bright = brightness < 180

                self.blue_mask[y][x] = is_blue and is_not_bright

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.speed = min(2.0, self.speed + 0.05)
            consumed = True
        if input_state.down:
            self.speed = max(0.1, self.speed - 0.05)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

    def draw(self):
        """Draw the wave with shimmering sea."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r, g, b = self.pixels[y][x]

                if self.blue_mask[y][x]:
                    # Shimmer effect: slow sine wave modulation
                    phase = self.phase_offsets[y][x]
                    shimmer = math.sin(self.time * 2.0 + phase) * 0.5 + 0.5  # 0 to 1

                    # Vary the color within a subtle range
                    # Shift toward slightly lighter/darker blue
                    shift = int((shimmer - 0.5) * 25)  # -12 to +12

                    r = max(0, min(255, r + shift // 2))
                    g = max(0, min(255, g + shift // 2))
                    b = max(0, min(255, b + shift))

                self.display.set_pixel(x, y, (r, g, b))

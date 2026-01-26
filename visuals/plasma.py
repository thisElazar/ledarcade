"""
Plasma - Classic demoscene effect
=================================
Colorful, smoothly animated plasma waves using sine functions.

Controls:
  Space  - Cycle color palette
  Escape - Exit
"""

import math
from typing import Tuple
from . import Visual, Display, Colors, GRID_SIZE


class Plasma(Visual):
    name = "PLASMA"
    description = "Classic plasma waves"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.palette_index = 0
        self.palettes = [
            self._make_palette_fire,
            self._make_palette_ocean,
            self._make_palette_rainbow,
            self._make_palette_matrix,
        ]

    def _make_palette_fire(self, v: float) -> Tuple:
        """Fire palette: black -> red -> orange -> yellow -> white"""
        if v < 0.33:
            t = v / 0.33
            return (int(255 * t), 0, 0)
        elif v < 0.66:
            t = (v - 0.33) / 0.33
            return (255, int(128 * t), 0)
        else:
            t = (v - 0.66) / 0.34
            return (255, 128 + int(127 * t), int(255 * t))

    def _make_palette_ocean(self, v: float) -> Tuple:
        """Ocean palette: deep blue -> cyan -> white"""
        if v < 0.5:
            t = v / 0.5
            return (0, int(100 * t), int(150 + 105 * t))
        else:
            t = (v - 0.5) / 0.5
            return (int(255 * t), 100 + int(155 * t), 255)

    def _make_palette_rainbow(self, v: float) -> Tuple:
        """Rainbow palette using HSV-like mapping"""
        h = v * 6.0
        i = int(h)
        f = h - i
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

    def _make_palette_matrix(self, v: float) -> Tuple:
        """Matrix palette: black -> dark green -> bright green"""
        return (0, int(255 * v * v), int(100 * v))

    def handle_input(self, input_state) -> bool:
        if input_state.action:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            return True
        return False

    def update(self, dt: float):
        self.time += dt

    def draw(self):
        self.display.clear(Colors.BLACK)
        palette_func = self.palettes[self.palette_index]
        t = self.time

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Multiple overlapping sine waves for plasma effect
                v1 = math.sin(x * 0.1 + t)
                v2 = math.sin(y * 0.1 + t * 0.7)
                v3 = math.sin((x + y) * 0.1 + t * 0.5)
                v4 = math.sin(math.sqrt((x - 32) ** 2 + (y - 32) ** 2) * 0.15 - t)

                # Combine and normalize to 0-1
                v = (v1 + v2 + v3 + v4) / 4.0
                v = (v + 1.0) / 2.0  # Map from [-1,1] to [0,1]

                color = palette_func(v)
                self.display.set_pixel(x, y, color)

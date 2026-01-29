"""
XOR Pattern - Classic mathematical fractal effect
=================================================
Bitwise XOR operations on coordinates create beautiful Sierpinski-like
fractal patterns. Simple math, stunning visuals.

Controls:
  Left/Right - Adjust animation speed
  Up/Down    - Cycle color palette
  Space      - Cycle pattern variation
  Escape     - Exit
"""

from typing import Tuple
from . import Visual, Display, Colors, GRID_SIZE


class XORPattern(Visual):
    name = "XOR"
    description = "Fractal patterns"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_index = 0
        self.pattern_index = 0

        # Color palettes
        self.palettes = [
            self._palette_rainbow,
            self._palette_fire,
            self._palette_ocean,
            self._palette_matrix,
            self._palette_purple,
            self._palette_grayscale,
        ]
        self.palette_names = ["Rainbow", "Fire", "Ocean", "Matrix", "Purple", "Gray"]

        # Pattern variations
        self.patterns = [
            self._pattern_basic,
            self._pattern_scroll,
            self._pattern_mod8,
            self._pattern_mod16,
            self._pattern_and_xor,
            self._pattern_or_xor,
            self._pattern_scaled,
            self._pattern_interference,
        ]
        self.pattern_names = [
            "Basic", "Scroll", "Mod8", "Mod16",
            "AND+XOR", "OR+XOR", "Scaled", "Interference"
        ]

    # ========== Color Palettes ==========

    def _palette_rainbow(self, v: int) -> Tuple:
        """Rainbow palette using HSV-like mapping"""
        h = (v / 256.0) * 6.0
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

    def _palette_fire(self, v: int) -> Tuple:
        """Fire palette: black -> red -> orange -> yellow -> white"""
        n = v / 255.0
        if n < 0.33:
            t = n / 0.33
            return (int(255 * t), 0, 0)
        elif n < 0.66:
            t = (n - 0.33) / 0.33
            return (255, int(200 * t), 0)
        else:
            t = (n - 0.66) / 0.34
            return (255, 200 + int(55 * t), int(255 * t))

    def _palette_ocean(self, v: int) -> Tuple:
        """Ocean palette: deep blue -> cyan -> white"""
        n = v / 255.0
        if n < 0.5:
            t = n / 0.5
            return (0, int(100 * t), int(150 + 105 * t))
        else:
            t = (n - 0.5) / 0.5
            return (int(255 * t), 100 + int(155 * t), 255)

    def _palette_matrix(self, v: int) -> Tuple:
        """Matrix palette: black -> dark green -> bright green"""
        n = v / 255.0
        return (0, int(255 * n), int(80 * n))

    def _palette_purple(self, v: int) -> Tuple:
        """Purple/magenta palette"""
        n = v / 255.0
        if n < 0.5:
            t = n / 0.5
            return (int(128 * t), 0, int(255 * t))
        else:
            t = (n - 0.5) / 0.5
            return (128 + int(127 * t), int(100 * t), 255)

    def _palette_grayscale(self, v: int) -> Tuple:
        """Simple grayscale"""
        return (v, v, v)

    # ========== XOR Pattern Variations ==========

    def _pattern_basic(self, x: int, y: int, t: int) -> int:
        """Basic XOR with time animation"""
        return (x ^ y ^ t) & 255

    def _pattern_scroll(self, x: int, y: int, t: int) -> int:
        """Scrolling XOR pattern"""
        return ((x + t) ^ (y + t)) & 255

    def _pattern_mod8(self, x: int, y: int, t: int) -> int:
        """XOR with mod 8 for color banding"""
        val = (x ^ y ^ t)
        return ((val % 8) * 32) & 255

    def _pattern_mod16(self, x: int, y: int, t: int) -> int:
        """XOR with mod 16 for finer banding"""
        val = (x ^ y ^ t)
        return ((val % 16) * 16) & 255

    def _pattern_and_xor(self, x: int, y: int, t: int) -> int:
        """Combination of AND and XOR"""
        return ((x & y) ^ (x ^ y) ^ t) & 255

    def _pattern_or_xor(self, x: int, y: int, t: int) -> int:
        """Combination of OR and XOR"""
        return ((x | y) ^ (x ^ y) ^ t) & 255

    def _pattern_scaled(self, x: int, y: int, t: int) -> int:
        """Scaled coordinates for different density"""
        sx = x * 2
        sy = y * 2
        return (sx ^ sy ^ t) & 255

    def _pattern_interference(self, x: int, y: int, t: int) -> int:
        """Multiple XOR patterns interfering"""
        v1 = x ^ y
        v2 = (x + 32) ^ (y + 32)
        return (v1 ^ v2 ^ t) & 255

    # ========== Visual Interface ==========

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Speed control
        if input_state.right:
            self.speed = min(5.0, self.speed + 0.2)
            consumed = True
        if input_state.left:
            self.speed = max(0.1, self.speed - 0.2)
            consumed = True

        # Color palette (Up/Down)
        if input_state.up:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index - 1) % len(self.palettes)
            consumed = True

        # Pattern variation (Space/Action)
        if (input_state.action_l or input_state.action_r):
            self.pattern_index = (self.pattern_index + 1) % len(self.patterns)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

    def draw(self):
        self.display.clear(Colors.BLACK)

        palette_func = self.palettes[self.palette_index]
        pattern_func = self.patterns[self.pattern_index]

        # Convert time to integer for XOR operations
        t = int(self.time * 10) & 255

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Get XOR pattern value (0-255)
                value = pattern_func(x, y, t)
                # Map to color
                color = palette_func(value)
                self.display.set_pixel(x, y, color)

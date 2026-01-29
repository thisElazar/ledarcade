"""
Sine Scroller - Classic demoscene effect
========================================
A horizontal band that scrolls while oscillating vertically with sine waves.
Creates the classic "wavy" scroller effect from 80s/90s demo scene.

Controls:
  Left/Right - Adjust wave/scroll speed
  Up/Down    - Cycle color palette
  Action     - Cycle pattern type
  Escape     - Exit
"""

import math
from typing import Tuple, List
from . import Visual, Display, Colors, GRID_SIZE


class SineScroller(Visual):
    name = "SINESCROLL"
    description = "Wavy scroller"
    category = "digital"

    # Pattern types
    PATTERN_SOLID = 0
    PATTERN_DOTS = 1
    PATTERN_GRADIENT = 2
    PATTERN_MULTIBAND = 3
    PATTERN_COUNT = 4

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_index = 0
        self.pattern_index = 0

        # Wave parameters
        self.wave_amplitude = 12  # Vertical oscillation amplitude
        self.wave_frequency = 0.15  # How many waves across screen
        self.band_height = 8  # Height of the scrolling band

        # For multiband mode
        self.num_bands = 4

        # Color palettes
        self.palettes = [
            self._palette_rainbow,
            self._palette_fire,
            self._palette_cyan,
            self._palette_neon,
            self._palette_ocean,
        ]

    def _palette_rainbow(self, t: float) -> Tuple[int, int, int]:
        """Rainbow cycling based on position/time"""
        h = (t * 6.0) % 6.0
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

    def _palette_fire(self, t: float) -> Tuple[int, int, int]:
        """Fire colors: red -> orange -> yellow"""
        t = t % 1.0
        if t < 0.5:
            return (255, int(200 * t * 2), 0)
        else:
            return (255, 200 + int(55 * (t - 0.5) * 2), int(255 * (t - 0.5) * 2))

    def _palette_cyan(self, t: float) -> Tuple[int, int, int]:
        """Cyan/electric blue palette"""
        t = t % 1.0
        brightness = 0.5 + 0.5 * math.sin(t * math.pi * 2)
        return (0, int(200 * brightness), int(255 * brightness))

    def _palette_neon(self, t: float) -> Tuple[int, int, int]:
        """Neon pink/purple"""
        t = t % 1.0
        if t < 0.5:
            return (255, 0, int(255 * t * 2))
        else:
            return (int(255 * (1 - (t - 0.5) * 2)), 0, 255)

    def _palette_ocean(self, t: float) -> Tuple[int, int, int]:
        """Deep ocean blues"""
        t = t % 1.0
        return (0, int(100 + 100 * t), int(150 + 105 * t))

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

        # Pattern cycling (on action button press)
        if (input_state.action_l or input_state.action_r):
            self.pattern_index = (self.pattern_index + 1) % self.PATTERN_COUNT
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

    def _get_wave_y(self, x: int, phase_offset: float = 0.0) -> float:
        """Calculate the Y position for a given X using sine wave"""
        # Primary wave
        y = math.sin(x * self.wave_frequency + self.time * 2.0 + phase_offset)
        # Add secondary wave for more complex motion
        y += 0.3 * math.sin(x * self.wave_frequency * 2.1 + self.time * 3.0 + phase_offset)
        # Normalize and scale
        y = y / 1.3  # Account for combined amplitude
        y = GRID_SIZE // 2 + y * self.wave_amplitude
        return y

    def _draw_solid_band(self):
        """Draw a solid color band following sine wave"""
        palette = self.palettes[self.palette_index]

        for x in range(GRID_SIZE):
            center_y = self._get_wave_y(x)
            color = palette((x + self.time * 20) / GRID_SIZE)

            # Draw vertical band centered on wave
            half_height = self.band_height // 2
            for dy in range(-half_height, half_height + 1):
                y = int(center_y + dy)
                if 0 <= y < GRID_SIZE:
                    # Slight brightness falloff at edges
                    edge_factor = 1.0 - abs(dy) / (half_height + 1) * 0.3
                    final_color = (
                        int(color[0] * edge_factor),
                        int(color[1] * edge_factor),
                        int(color[2] * edge_factor)
                    )
                    self.display.set_pixel(x, y, final_color)

    def _draw_dots_pattern(self):
        """Draw dots following sine wave path"""
        palette = self.palettes[self.palette_index]

        for x in range(GRID_SIZE):
            center_y = self._get_wave_y(x)

            # Draw dots at intervals
            for dot_offset in range(-2, 3):
                y = int(center_y + dot_offset * 3)
                if 0 <= y < GRID_SIZE:
                    # Color based on position
                    color = palette((x + dot_offset * 10 + self.time * 20) / GRID_SIZE)
                    self.display.set_pixel(x, y, color)

                    # Make dots slightly larger
                    if x + 1 < GRID_SIZE:
                        self.display.set_pixel(x + 1, y, color)

    def _draw_gradient_band(self):
        """Draw a gradient band with smooth color transitions"""
        palette = self.palettes[self.palette_index]

        for x in range(GRID_SIZE):
            center_y = self._get_wave_y(x)

            # Draw gradient from top to bottom of band
            half_height = self.band_height // 2 + 2
            for dy in range(-half_height, half_height + 1):
                y = int(center_y + dy)
                if 0 <= y < GRID_SIZE:
                    # Position within band (0 to 1)
                    band_pos = (dy + half_height) / (half_height * 2)
                    # Color based on both x position and band position
                    color = palette((x / GRID_SIZE + band_pos * 0.5 + self.time * 0.5) % 1.0)

                    # Fade at edges
                    edge_dist = abs(dy) / half_height
                    fade = max(0, 1.0 - edge_dist * edge_dist)

                    final_color = (
                        int(color[0] * fade),
                        int(color[1] * fade),
                        int(color[2] * fade)
                    )
                    self.display.set_pixel(x, y, final_color)

    def _draw_multiband(self):
        """Draw multiple parallel bands with phase offsets"""
        palette = self.palettes[self.palette_index]

        for band in range(self.num_bands):
            phase_offset = band * math.pi / 2  # Quarter phase offset per band

            for x in range(GRID_SIZE):
                center_y = self._get_wave_y(x, phase_offset)
                color = palette((band / self.num_bands + self.time * 0.3) % 1.0)

                # Thinner bands for multiband mode
                band_h = 3
                for dy in range(-band_h // 2, band_h // 2 + 1):
                    y = int(center_y + dy)
                    if 0 <= y < GRID_SIZE:
                        # Brightness based on band index for depth effect
                        brightness = 0.5 + 0.5 * (band / self.num_bands)
                        final_color = (
                            int(color[0] * brightness),
                            int(color[1] * brightness),
                            int(color[2] * brightness)
                        )
                        self.display.set_pixel(x, y, final_color)

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.pattern_index == self.PATTERN_SOLID:
            self._draw_solid_band()
        elif self.pattern_index == self.PATTERN_DOTS:
            self._draw_dots_pattern()
        elif self.pattern_index == self.PATTERN_GRADIENT:
            self._draw_gradient_band()
        elif self.pattern_index == self.PATTERN_MULTIBAND:
            self._draw_multiband()

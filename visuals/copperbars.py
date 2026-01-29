"""
CopperBars - Amiga demoscene raster bars effect
================================================
Classic metallic horizontal gradient bars bouncing with sine waves.
A tribute to the legendary Amiga copper/raster bar demos.

Controls:
  Left/Right - Adjust animation speed
  Up/Down    - Cycle color palette
  Space      - Change wave pattern
  Escape     - Exit
"""

import math
from typing import List, Tuple
from . import Visual, Display, Colors, GRID_SIZE


class Bar:
    """A single copper bar with position and properties."""

    def __init__(self, base_color: Tuple[int, int, int], phase: float,
                 amplitude: float, frequency: float, height: int = 8):
        self.base_color = base_color
        self.phase = phase
        self.amplitude = amplitude
        self.frequency = frequency
        self.height = height
        self.y = 0.0  # Current center y position


class CopperBars(Visual):
    name = "COPPERBARS"
    description = "Amiga raster bars"
    category = "digital"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.palette_index = 0
        self.wave_pattern = 0

        # Color palettes for the bars
        self.palettes = [
            self._palette_rainbow,
            self._palette_copper,
            self._palette_neon,
            self._palette_mono,
        ]
        self.palette_names = ["RAINBOW", "COPPER", "NEON", "MONO"]

        # Wave patterns
        self.wave_patterns = [
            "sine",      # Classic sine wave
            "bounce",    # Bouncing motion
            "cascade",   # Cascading waves
            "chaos",     # Multiple frequencies
        ]

        self._create_bars()

    def _palette_rainbow(self, index: int) -> Tuple[int, int, int]:
        """Rainbow palette - full spectrum."""
        hues = [
            (255, 0, 0),     # Red
            (255, 128, 0),   # Orange
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 255, 255),   # Cyan
            (0, 128, 255),   # Light blue
            (128, 0, 255),   # Purple
            (255, 0, 255),   # Magenta
        ]
        return hues[index % len(hues)]

    def _palette_copper(self, index: int) -> Tuple[int, int, int]:
        """Copper/gold metallic palette - classic Amiga look."""
        coppers = [
            (255, 180, 80),   # Bright copper
            (220, 140, 40),   # Gold
            (180, 100, 20),   # Bronze
            (255, 200, 100),  # Light gold
            (200, 120, 30),   # Dark copper
            (255, 160, 60),   # Orange copper
            (180, 140, 60),   # Brass
            (255, 220, 140),  # Pale gold
        ]
        return coppers[index % len(coppers)]

    def _palette_neon(self, index: int) -> Tuple[int, int, int]:
        """Neon/synthwave palette."""
        neons = [
            (255, 0, 128),    # Hot pink
            (0, 255, 255),    # Cyan
            (255, 0, 255),    # Magenta
            (0, 255, 128),    # Neon green
            (128, 0, 255),    # Purple
            (255, 128, 0),    # Orange
            (0, 128, 255),    # Electric blue
            (255, 255, 0),    # Yellow
        ]
        return neons[index % len(neons)]

    def _palette_mono(self, index: int) -> Tuple[int, int, int]:
        """Monochrome blue palette."""
        # Different shades/intensities of blue
        blues = [
            (100, 150, 255),
            (50, 100, 255),
            (150, 180, 255),
            (80, 130, 255),
            (120, 160, 255),
            (60, 110, 255),
            (140, 170, 255),
            (90, 140, 255),
        ]
        return blues[index % len(blues)]

    def _create_bars(self):
        """Create the copper bars with current palette."""
        num_bars = 7
        palette_func = self.palettes[self.palette_index]

        self.bars: List[Bar] = []
        for i in range(num_bars):
            base_color = palette_func(i)
            # Stagger phases for nice wave effect
            phase = (i / num_bars) * math.pi * 2
            # Vary amplitude slightly
            amplitude = 20 + (i % 3) * 4
            # Base frequency with slight variation
            frequency = 1.0 + (i % 2) * 0.3
            # Bar height (slightly varied)
            height = 6 + (i % 3)

            bar = Bar(base_color, phase, amplitude, frequency, height)
            self.bars.append(bar)

    def _get_bar_gradient(self, base_color: Tuple[int, int, int],
                          row_offset: int, bar_height: int) -> Tuple[int, int, int]:
        """
        Calculate the metallic gradient color for a row within a bar.
        Creates a shiny cylindrical look: dark -> bright -> dark
        """
        # Normalize position within bar (-1 to 1, 0 is center)
        half_height = bar_height / 2
        normalized = row_offset / half_height  # -1 to 1

        # Metallic gradient: edges are darker, center is brightest
        # Use cosine for smooth falloff
        brightness = math.cos(normalized * math.pi / 2)
        brightness = brightness ** 0.7  # Adjust curve for metallic look

        # Add specular highlight near center-top
        specular = 0.0
        if -0.3 < normalized < 0.3:
            specular = 0.3 * (1 - abs(normalized) / 0.3)

        # Calculate final color
        r = int(base_color[0] * brightness + 255 * specular)
        g = int(base_color[1] * brightness + 255 * specular)
        b = int(base_color[2] * brightness + 255 * specular)

        # Clamp values
        r = min(255, max(0, r))
        g = min(255, max(0, g))
        b = min(255, max(0, b))

        return (r, g, b)

    def _calculate_bar_y(self, bar: Bar, time: float) -> float:
        """Calculate the Y position of a bar based on wave pattern."""
        center = GRID_SIZE / 2
        pattern = self.wave_patterns[self.wave_pattern]

        if pattern == "sine":
            # Classic smooth sine wave
            return center + math.sin(time * bar.frequency + bar.phase) * bar.amplitude

        elif pattern == "bounce":
            # Bouncing ball motion (abs of sine)
            wave = abs(math.sin(time * bar.frequency * 0.7 + bar.phase))
            return 10 + wave * (GRID_SIZE - 20 - bar.height)

        elif pattern == "cascade":
            # Cascading waterfall effect
            base = math.sin(time * 0.8 + bar.phase)
            secondary = math.sin(time * 1.6 + bar.phase * 2) * 0.3
            return center + (base + secondary) * bar.amplitude * 0.7

        elif pattern == "chaos":
            # Multiple overlapping frequencies
            wave1 = math.sin(time * bar.frequency + bar.phase)
            wave2 = math.sin(time * bar.frequency * 1.7 + bar.phase * 0.5) * 0.5
            wave3 = math.sin(time * bar.frequency * 0.3 + bar.phase * 2) * 0.3
            return center + (wave1 + wave2 + wave3) * bar.amplitude * 0.6

        return center

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Adjust speed
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.1)
            consumed = True
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.1)
            consumed = True

        # Cycle palette
        if input_state.up:
            self.palette_index = (self.palette_index + 1) % len(self.palettes)
            self._create_bars()
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index - 1) % len(self.palettes)
            self._create_bars()
            consumed = True

        # Change wave pattern
        if (input_state.action_l or input_state.action_r):
            self.wave_pattern = (self.wave_pattern + 1) % len(self.wave_patterns)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt * self.speed

        # Update bar positions
        for bar in self.bars:
            bar.y = self._calculate_bar_y(bar, self.time)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Create a buffer for additive blending
        screen_buffer = [[(0, 0, 0) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Sort bars by Y position for proper layering (back to front)
        sorted_bars = sorted(self.bars, key=lambda b: b.y)

        # Draw each bar
        for bar in sorted_bars:
            center_y = bar.y
            half_height = bar.height / 2

            # Draw each row of the bar
            for row_offset in range(-int(half_height), int(half_height) + 1):
                y = int(center_y + row_offset)

                if 0 <= y < GRID_SIZE:
                    # Get gradient color for this row
                    color = self._get_bar_gradient(bar.base_color, row_offset, bar.height)

                    # Draw full horizontal line
                    for x in range(GRID_SIZE):
                        # Additive blending with existing color
                        existing = screen_buffer[y][x]
                        new_color = (
                            min(255, existing[0] + color[0]),
                            min(255, existing[1] + color[1]),
                            min(255, existing[2] + color[2])
                        )
                        screen_buffer[y][x] = new_color

        # Copy buffer to display
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, screen_buffer[y][x])

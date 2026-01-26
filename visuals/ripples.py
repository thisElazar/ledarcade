"""
Ripples - Pressure Wave Visual
==============================
A cellular automaton simulating pressure waves spreading
through a medium, creating rippling circular patterns
like raindrops on still water.

Inspired by the "Pond" rule from CelLab by Rudy Rucker and John Walker.
Source: https://fourmilab.ch/cellab/

Controls:
  Up/Down    - Change color palette
  Left/Right - Adjust wave damping
  Space      - Drop new ripple
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Ripples(Visual):
    name = "RIPPLES"
    description = "Rippling waves"
    category = "nature"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.update_interval = 0.03  # Time between CA updates

        # Wave parameters
        self.damping = 0.98  # Damping factor (1.0 = no damping, lower = more damping)
        self.max_height = 127  # Maximum wave height (centered around 0)
        self.auto_drop_interval = 2.0  # Seconds between auto raindrops
        self.auto_drop_timer = 0.0

        # Color palettes (matching Quarks/Hodge style)
        self.palettes = [
            # Rainbow spectrum
            self.make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150), (100, 255, 100), (255, 255, 0), (255, 100, 0), (150, 0, 100)]),
            # Rainbow inverted
            self.make_gradient([(150, 0, 100), (255, 100, 0), (255, 255, 0), (100, 255, 100), (0, 200, 150), (0, 100, 200), (20, 0, 80)]),
            # Ocean blues
            self.make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150), (100, 200, 200), (200, 230, 255)]),
            # Ocean inverted
            self.make_gradient([(200, 230, 255), (100, 200, 200), (0, 150, 150), (0, 50, 100), (0, 0, 40)]),
            # Fire
            self.make_gradient([(40, 0, 0), (150, 30, 0), (255, 100, 0), (255, 200, 50), (255, 255, 200)]),
            # Fire inverted
            self.make_gradient([(255, 255, 200), (255, 200, 50), (255, 100, 0), (150, 30, 0), (40, 0, 0)]),
            # Forest greens
            self.make_gradient([(0, 20, 0), (0, 80, 40), (50, 150, 50), (150, 220, 100), (220, 255, 180)]),
            # Forest inverted
            self.make_gradient([(220, 255, 180), (150, 220, 100), (50, 150, 50), (0, 80, 40), (0, 20, 0)]),
            # Purple/pink
            self.make_gradient([(40, 0, 60), (100, 0, 150), (200, 50, 200), (255, 150, 220), (255, 220, 255)]),
            # Purple inverted
            self.make_gradient([(255, 220, 255), (255, 150, 220), (200, 50, 200), (100, 0, 150), (40, 0, 60)]),
        ]
        self.current_palette = 0
        self.colors = self.palettes[self.current_palette]

        # Initialize grids for wave simulation
        # Current height values (can be negative, centered around 0)
        self.grid = [[0.0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        # Previous height values (needed for wave equation)
        self.prev_grid = [[0.0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Drop initial raindrops
        self.init_pattern()

    def make_gradient(self, key_colors):
        """Create 256-color gradient from key colors."""
        gradient = []
        segments = len(key_colors) - 1
        per_segment = 256 // segments

        for i in range(256):
            seg = min(i // per_segment, segments - 1)
            t = (i % per_segment) / per_segment
            c1 = key_colors[seg]
            c2 = key_colors[seg + 1]
            gradient.append((
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            ))

        return gradient

    def make_banded_rainbow(self, num_bands):
        """Create dense rainbow banding - multiple repeating rainbow cycles."""
        gradient = []
        rainbow = [
            (255, 0, 0),     # Red
            (255, 127, 0),   # Orange
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (75, 0, 130),    # Indigo
            (148, 0, 211),   # Violet
        ]
        for i in range(256):
            cycle_pos = (i * num_bands * len(rainbow)) / 256
            color_idx = int(cycle_pos) % len(rainbow)
            next_idx = (color_idx + 1) % len(rainbow)
            t = cycle_pos % 1.0
            c1 = rainbow[color_idx]
            c2 = rainbow[next_idx]
            gradient.append((
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            ))
        return gradient

    def make_mono_bands(self, base_color, num_bands):
        """Create monochromatic bands - alternating light/dark stripes."""
        import math
        gradient = []
        for i in range(256):
            band_pos = (i * num_bands * 2) / 256
            brightness = (math.sin(band_pos * math.pi) + 1) / 2
            gradient.append((
                int(base_color[0] * brightness),
                int(base_color[1] * brightness),
                int(base_color[2] * brightness),
            ))
        return gradient

    def init_pattern(self):
        """Initialize with a few random ripples."""
        # Clear grids
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = 0.0
                self.prev_grid[y][x] = 0.0

        # Drop a few initial raindrops
        num_drops = random.randint(3, 6)
        for _ in range(num_drops):
            self.drop_ripple()

    def drop_ripple(self, x=None, y=None):
        """Drop a single raindrop at the given position or random location."""
        if x is None:
            x = random.randint(5, GRID_SIZE - 6)
        if y is None:
            y = random.randint(5, GRID_SIZE - 6)

        # Create a splash with variable size for more interesting patterns
        strength = random.uniform(0.3, 1.0) * self.max_height
        radius = random.randint(1, 5)

        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist = (dx * dx + dy * dy) ** 0.5
                if dist <= radius:
                    nx = (x + dx) % GRID_SIZE
                    ny = (y + dy) % GRID_SIZE
                    # Gaussian-like falloff for smoother initial shape
                    falloff = 1.0 - (dist / (radius + 1))
                    self.grid[ny][nx] = strength * falloff

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.current_palette = (self.current_palette + 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True
        if input_state.down:
            self.current_palette = (self.current_palette - 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True

        if input_state.left:
            self.damping = max(0.90, self.damping - 0.01)
            consumed = True
        if input_state.right:
            self.damping = min(0.999, self.damping + 0.01)
            consumed = True

        if input_state.action:
            self.drop_ripple()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt
        self.auto_drop_timer += dt

        # Auto-drop raindrops periodically
        if self.auto_drop_timer >= self.auto_drop_interval:
            self.auto_drop_timer = 0.0
            self.drop_ripple()

        while self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            self.step_ca()

    def step_ca(self):
        """Perform one step of the wave cellular automaton."""
        # Temporary grid to store new values
        new_grid = [[0.0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Calculate average of 4 cardinal neighbors (Von Neumann neighborhood)
                # Using 4 neighbors gives cleaner circular waves
                neighbors_sum = 0.0
                neighbors_sum += self.grid[(y - 1) % GRID_SIZE][x]  # North
                neighbors_sum += self.grid[(y + 1) % GRID_SIZE][x]  # South
                neighbors_sum += self.grid[y][(x - 1) % GRID_SIZE]  # West
                neighbors_sum += self.grid[y][(x + 1) % GRID_SIZE]  # East

                neighbors_avg = neighbors_sum / 2.0  # Divide by 2 (not 4) for wave equation

                # Wave equation: new = average_of_neighbors - previous
                # This creates propagating waves
                new_value = neighbors_avg - self.prev_grid[y][x]

                # Apply damping to prevent infinite oscillation
                new_value *= self.damping

                # Clamp to prevent overflow
                new_value = max(-self.max_height, min(self.max_height, new_value))

                new_grid[y][x] = new_value

        # Shift grids: current becomes previous, new becomes current
        self.prev_grid = self.grid
        self.grid = new_grid

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Map wave displacement to color - no motion is black, ripples have color
                height = self.grid[y][x]
                # Use absolute value so both positive and negative waves show color
                intensity = abs(height) / self.max_height
                intensity = min(1.0, intensity)

                # Map intensity to color index (0 = no motion, 255 = max displacement)
                color_index = int(intensity * 255)

                # Scale the color by intensity so no motion = black
                base_color = self.colors[color_index]
                color = (
                    int(base_color[0] * intensity),
                    int(base_color[1] * intensity),
                    int(base_color[2] * intensity),
                )
                self.display.set_pixel(x, y, color)

"""
Rug - Averaging Cellular Automaton
==================================
The classic Rug rule from CelLab: each cell becomes one more
than the average of its eight neighbors. Run in "nowrap" mode
with edge seeding, patterns grow inward creating carpet-like
fractal designs.

Based on the "Rug" rule from CelLab by Rudy Rucker and John Walker.
Documentation notes: "Rug rules will look better when wrap is turned off"
and starting blank in nowrap mode creates "a chaotic carpet slowly
growing inward."
Source: https://fourmilab.ch/cellab/

Controls:
  Up/Down    - Change color palette
  Left/Right - Adjust speed
  Space      - Reset with new pattern
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Rug(Visual):
    name = "RUG"
    description = "Carpet fractals"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.update_timer = 0.0
        self.update_interval = 0.08  # Slower CA = smoother on Pi

        # Color palettes
        self.palettes = [
            # Dense rainbow banding - repeating rainbow stripes
            self.make_banded_rainbow(16),  # 16 rainbow cycles
            self.make_banded_rainbow(8),   # 8 rainbow cycles
            # Monochromatic banded - 10 stripes light/dark
            self.make_mono_bands((0, 100, 255), 10),  # Blue bands
            self.make_mono_bands((255, 50, 50), 10),  # Red bands
            self.make_mono_bands((50, 255, 100), 10), # Green bands
            self.make_mono_bands((255, 200, 50), 10), # Gold bands
            self.make_mono_bands((200, 100, 255), 10), # Purple bands
            self.make_mono_bands((255, 255, 255), 10), # White/gray bands
            # Original smooth gradients
            self.make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150), (100, 255, 100), (255, 255, 0), (255, 100, 0), (150, 0, 100)]),
            self.make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150), (100, 200, 200), (200, 230, 255)]),
        ]
        self.current_palette = 0
        self.colors = self.palettes[self.current_palette]

        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Edge values for "open" boundary mode
        self.edge_val = random.randint(100, 200)

        self.init_pattern()

    def make_gradient(self, key_colors):
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
            # Which cycle and position within cycle
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
        gradient = []
        for i in range(256):
            # Calculate band position (0 to num_bands*2)
            band_pos = (i * num_bands * 2) / 256
            # Use sine wave for smooth light/dark transition
            import math
            brightness = (math.sin(band_pos * math.pi) + 1) / 2  # 0 to 1
            # Apply brightness to base color
            gradient.append((
                int(base_color[0] * brightness),
                int(base_color[1] * brightness),
                int(base_color[2] * brightness),
            ))
        return gradient

    def init_pattern(self):
        """Initialize blank with seeded edges - patterns grow inward."""
        # Start mostly blank
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = 0

        # Seed the edges with values
        self.edge_val = random.randint(100, 200)
        for i in range(GRID_SIZE):
            self.grid[0][i] = self.edge_val  # Top
            self.grid[GRID_SIZE-1][i] = self.edge_val  # Bottom
            self.grid[i][0] = self.edge_val  # Left
            self.grid[i][GRID_SIZE-1] = self.edge_val  # Right

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
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        if input_state.action:
            self.init_pattern()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt * self.speed

        while self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            self.step_ca()

    def get_cell(self, x, y):
        """Get cell - out of bounds returns edge value (open boundary)."""
        if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
            return self.edge_val
        return self.grid[y][x]

    def step_ca(self):
        """Rug rule: new = (sum of 8 neighbors // 8 + 1) mod 256, nowrap mode."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Sum 8 neighbors with open boundary (edge value outside)
                total = 0
                total += self.get_cell(x - 1, y - 1)
                total += self.get_cell(x, y - 1)
                total += self.get_cell(x + 1, y - 1)
                total += self.get_cell(x - 1, y)
                total += self.get_cell(x + 1, y)
                total += self.get_cell(x - 1, y + 1)
                total += self.get_cell(x, y + 1)
                total += self.get_cell(x + 1, y + 1)

                # Rug rule: average of neighbors + 1
                self.next_grid[y][x] = (total // 8 + 1) % 256

        self.grid, self.next_grid = self.next_grid, self.grid

        # Slowly drift the edge value to create evolving patterns
        if random.random() < 0.02:
            self.edge_val = (self.edge_val + random.choice([-1, 1])) % 256

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                color = self.colors[state]
                self.display.set_pixel(x, y, color)

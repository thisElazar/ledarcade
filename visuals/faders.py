"""
Faders - Life+Brain Hybrid Visual
=================================
A cellular automaton that combines Life's persistence with
Brain's refractory states. Firing cells leave slowly fading
trails, creating beautiful dissolving patterns.

Based on the "Faders" rule from CelLab by Rudy Rucker and John Walker,
described as Rucker's "pride and joy."
Source: https://fourmilab.ch/cellab/

Controls:
  Up/Down    - Change color palette
  Left/Right - Adjust decay length (trail duration)
  Space      - Reset with random pattern
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Faders(Visual):
    name = "FADERS"
    description = "Fading trails"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.update_interval = 0.05  # Fixed update rate

        # States: 0 = dead, 1 = firing, 2 to max_state = refractory (fading)
        self.max_state = 64  # Number of refractory states (adjustable)
        self.min_decay = 16
        self.max_decay = 128
        self.refractory_states = self.max_state - 1

        # Color palettes - original gradient first, then banded options
        self.current_palette = 0
        self.palette_generators = [
            lambda: self.make_colors(),  # Original gradient
            lambda: self.make_banded_rainbow_colors(8),
            lambda: self.make_banded_rainbow_colors(4),
            lambda: self.make_mono_band_colors((0, 100, 255), 6),   # Blue
            lambda: self.make_mono_band_colors((255, 50, 50), 6),   # Red
            lambda: self.make_mono_band_colors((50, 255, 100), 6),  # Green
            lambda: self.make_mono_band_colors((255, 200, 50), 6),  # Gold
            lambda: self.make_mono_band_colors((200, 100, 255), 6), # Purple
        ]
        self.colors = self.palette_generators[self.current_palette]()

        # Initialize grid
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        self.init_random()

    def make_colors(self):
        """Create colors: dead=dark, firing=bright, refractory=fading."""
        colors = [(5, 5, 15)]  # State 0: dead

        # State 1: firing (bright white)
        colors.append((255, 255, 255))

        # States 2+: refractory (fading through colors)
        for i in range(2, self.max_state + 1):
            t = (i - 2) / max(1, self.refractory_states - 1)
            # Fade from bright through colors to dark
            if t < 0.2:
                # White to cyan
                st = t / 0.2
                colors.append((
                    int(255 - 155 * st),
                    int(255 - 55 * st),
                    int(255)
                ))
            elif t < 0.4:
                # Cyan to blue
                st = (t - 0.2) / 0.2
                colors.append((
                    int(100 - 70 * st),
                    int(200 - 100 * st),
                    int(255 - 55 * st)
                ))
            elif t < 0.6:
                # Blue to purple
                st = (t - 0.4) / 0.2
                colors.append((
                    int(30 + 70 * st),
                    int(100 - 60 * st),
                    int(200 - 50 * st)
                ))
            elif t < 0.8:
                # Purple to dark magenta
                st = (t - 0.6) / 0.2
                colors.append((
                    int(100 - 60 * st),
                    int(40 - 30 * st),
                    int(150 - 100 * st)
                ))
            else:
                # Dark magenta to nearly black
                st = (t - 0.8) / 0.2
                colors.append((
                    int(40 - 35 * st),
                    int(10 - 5 * st),
                    int(50 - 35 * st)
                ))

        return colors

    def make_banded_rainbow_colors(self, num_bands):
        """Create colors with banded rainbow for refractory states."""
        import math
        colors = [(5, 5, 15)]  # State 0: dead (dark)
        colors.append((255, 255, 255))  # State 1: firing (bright white)

        rainbow = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211),
        ]

        # States 2+: refractory with banded rainbow that fades
        for i in range(2, self.max_state + 1):
            t = (i - 2) / max(1, self.refractory_states - 1)
            # Banded rainbow color
            cycle_pos = (i * num_bands * len(rainbow)) / self.max_state
            color_idx = int(cycle_pos) % len(rainbow)
            next_idx = (color_idx + 1) % len(rainbow)
            blend = cycle_pos % 1.0
            c1 = rainbow[color_idx]
            c2 = rainbow[next_idx]
            base_r = int(c1[0] + (c2[0] - c1[0]) * blend)
            base_g = int(c1[1] + (c2[1] - c1[1]) * blend)
            base_b = int(c1[2] + (c2[2] - c1[2]) * blend)
            # Fade brightness as state increases
            brightness = 1.0 - (t * 0.85)
            colors.append((
                int(base_r * brightness),
                int(base_g * brightness),
                int(base_b * brightness),
            ))
        return colors

    def make_mono_band_colors(self, base_color, num_bands):
        """Create colors with monochromatic banding for refractory states."""
        import math
        colors = [(5, 5, 15)]  # State 0: dead
        colors.append((255, 255, 255))  # State 1: firing

        # States 2+: refractory with banded mono that fades
        for i in range(2, self.max_state + 1):
            t = (i - 2) / max(1, self.refractory_states - 1)
            # Banded brightness
            band_pos = (i * num_bands * 2) / self.max_state
            band_brightness = (math.sin(band_pos * math.pi) + 1) / 2
            # Overall fade as state increases
            fade = 1.0 - (t * 0.85)
            final_brightness = band_brightness * fade
            colors.append((
                int(base_color[0] * final_brightness),
                int(base_color[1] * final_brightness),
                int(base_color[2] * final_brightness),
            ))
        return colors

    def init_random(self):
        """Initialize with random firing cells."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if random.random() < 0.15:
                    self.grid[y][x] = 1  # Firing
                else:
                    self.grid[y][x] = 0  # Dead

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.current_palette = (self.current_palette + 1) % len(self.palette_generators)
            self.colors = self.palette_generators[self.current_palette]()
            consumed = True
        if input_state.down:
            self.current_palette = (self.current_palette - 1) % len(self.palette_generators)
            self.colors = self.palette_generators[self.current_palette]()
            consumed = True

        if input_state.left:
            # Shorter decay = faster pulses
            self.max_state = max(self.min_decay, self.max_state - 8)
            self.refractory_states = self.max_state - 1
            self.colors = self.palette_generators[self.current_palette]()
            consumed = True
        if input_state.right:
            # Longer decay = slower change
            self.max_state = min(self.max_decay, self.max_state + 8)
            self.refractory_states = self.max_state - 1
            self.colors = self.palette_generators[self.current_palette]()
            consumed = True

        if input_state.action:
            self.init_random()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt

        if self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            self.step_ca()

    def step_ca(self):
        """Perform one step of the Faders cellular automaton."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]

                # Count firing neighbors (state 1)
                firing_neighbors = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx = (x + dx) % GRID_SIZE
                        ny = (y + dy) % GRID_SIZE
                        if self.grid[ny][nx] == 1:
                            firing_neighbors += 1

                if state == 0:
                    # Dead cell: fires if 2 or 3 firing neighbors
                    if firing_neighbors == 2 or firing_neighbors == 3:
                        self.next_grid[y][x] = 1
                    else:
                        self.next_grid[y][x] = 0

                elif state == 1:
                    # Firing cell: stays firing if 2 or 3 firing neighbors
                    # Otherwise enters refractory state
                    if firing_neighbors == 2 or firing_neighbors == 3:
                        self.next_grid[y][x] = 1
                    else:
                        self.next_grid[y][x] = 2  # Start fading

                else:
                    # Refractory cell: fade toward dead
                    if state < self.max_state:
                        self.next_grid[y][x] = state + 1
                    else:
                        self.next_grid[y][x] = 0  # Fully faded = dead

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                if state < len(self.colors):
                    color = self.colors[state]
                else:
                    color = self.colors[-1]
                self.display.set_pixel(x, y, color)

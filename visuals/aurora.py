"""
Aurora - Flowing Paint Visual
=============================
A cellular automaton creating globby paint effects
that flow vertically down the screen with 1D glider
interactions on a ring topology.

Based on the "Aurora" rule from CelLab by Rudy Rucker and John Walker.
Source: https://fourmilab.ch/cellab/

Controls:
  Up/Down    - Change color palette
  Left/Right - Adjust flow speed
  Space      - Reset with new pattern
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Aurora(Visual):
    name = "AURORA"
    description = "Flowing paint"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.update_timer = 0.0
        self.update_interval = 0.04  # Time between CA updates

        # Color palettes - banded for maximum visual impact
        self.palettes = [
            # Dense rainbow banding
            self.make_banded_rainbow(16),
            self.make_banded_rainbow(8),
            # Monochromatic bands
            self.make_mono_bands((0, 100, 255), 10),   # Blue bands
            self.make_mono_bands((255, 50, 50), 10),   # Red bands
            self.make_mono_bands((50, 255, 100), 10),  # Green bands
            self.make_mono_bands((255, 200, 50), 10),  # Gold bands
            self.make_mono_bands((200, 100, 255), 10), # Purple bands
            self.make_mono_bands((255, 255, 255), 10), # White/gray bands
            # Smooth gradients
            self.make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150), (100, 255, 100), (255, 255, 0), (255, 100, 0), (150, 0, 100)]),
            self.make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150), (100, 200, 200), (200, 230, 255)]),
        ]
        self.current_palette = 0
        self.colors = self.palettes[self.current_palette]

        # Initialize grid with 256 states
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Initialize with random pattern
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
        import math
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
        """Initialize with vertical streaks and random seeds."""
        # Clear grid
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = 0

        # Create vertical streaks of varying widths
        num_streaks = random.randint(8, 16)
        for _ in range(num_streaks):
            x = random.randint(0, GRID_SIZE - 1)
            width = random.randint(1, 4)
            base_val = random.randint(64, 255)

            for dx in range(-width // 2, width // 2 + 1):
                col = (x + dx) % GRID_SIZE
                for y in range(GRID_SIZE):
                    # Vertical gradient with some noise
                    noise = random.randint(-30, 30)
                    val = max(0, min(255, base_val + noise - (y * 2)))
                    self.grid[y][col] = max(self.grid[y][col], val)

        # Add some random bright seeds
        num_seeds = random.randint(20, 40)
        for _ in range(num_seeds):
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE // 2)  # Seeds in top half
            val = random.randint(180, 255)
            self.grid[y][x] = val

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.current_palette = (self.current_palette + 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True
        if input_state.down_pressed:
            self.current_palette = (self.current_palette - 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True

        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        if (input_state.action_l or input_state.action_r):
            self.init_pattern()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt * self.speed

        # Run CA updates
        while self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            self.step_ca()

    def step_ca(self):
        """
        Perform one step of the Aurora cellular automaton.

        The Aurora rule creates flowing paint effects by:
        1. Each row is treated as a 1D ring
        2. Cells interact with horizontal neighbors (1D CA behavior)
        3. Results flow/shift downward creating vertical streaming
        4. Wraps toroidally for seamless patterns
        """
        # Process each row as a 1D CA, with results shifted down
        for y in range(GRID_SIZE):
            # Target row is one below (with wrap)
            target_y = (y + 1) % GRID_SIZE

            for x in range(GRID_SIZE):
                # Get wider horizontal neighbors for smearier effect
                left2 = self.grid[y][(x - 2) % GRID_SIZE]
                left = self.grid[y][(x - 1) % GRID_SIZE]
                center = self.grid[y][x]
                right = self.grid[y][(x + 1) % GRID_SIZE]
                right2 = self.grid[y][(x + 2) % GRID_SIZE]

                # Wider horizontal smear with strong center weight
                horizontal_sum = left2 + left * 2 + center * 4 + right * 2 + right2

                # Less division = more persistence, slower dissipation
                new_val = horizontal_sum // 10

                # Horizontal drift for smearing
                if random.random() < 0.15:
                    drift = random.choice([-1, 1])
                    drift_x = (x + drift) % GRID_SIZE
                    new_val = (new_val + self.grid[y][drift_x]) // 2

                self.next_grid[target_y][x] = min(255, new_val)

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid

        # Inject new energy - vertical streaks with trails like init_pattern
        if random.random() < 0.2:
            x = random.randint(0, GRID_SIZE - 1)
            width = random.randint(1, 4)
            base_val = random.randint(200, 255)
            streak_length = random.randint(GRID_SIZE // 3, GRID_SIZE // 2)

            for dx in range(-width, width + 1):
                col = (x + dx) % GRID_SIZE
                for row in range(streak_length):
                    # Fade down the streak
                    fade = 1.0 - (row / streak_length)
                    noise = random.randint(-20, 20)
                    val = max(0, min(255, int(base_val * fade) + noise))
                    # Blend with existing rather than overwrite
                    self.grid[row][col] = max(self.grid[row][col], val)

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                color = self.colors[state]
                self.display.set_pixel(x, y, color)

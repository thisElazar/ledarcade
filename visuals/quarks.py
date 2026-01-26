"""
Quarks - Cellular Automaton Visual
==================================
A heat diffusion cellular automaton that creates smooth,
flowing mandala-like patterns. Each cell averages its
neighbors and adds 1, creating cycling color waves.
Animated "quark" hotspots roam the field, injecting energy.

Based on the "Rug" rule from CelLab by Rudy Rucker and John Walker.
Source: https://fourmilab.ch/cellab/

Controls:
  Left/Right - Adjust speed
  Up/Down    - Change color palette
  Space      - Reset with new pattern
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


class Quarks(Visual):
    name = "QUARKS"
    description = "Flowing mandalas"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.update_timer = 0.0
        self.update_interval = 0.05  # Time between CA updates

        # Color palettes (normal and inverted versions)
        self.palettes = [
            # Rainbow spectrum
            self.make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150), (100, 255, 100), (255, 255, 0), (255, 100, 0), (150, 0, 100)]),
            # Rainbow inverted (light to dark)
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
            # Banded rainbow
            self.make_banded_rainbow(16),
            self.make_banded_rainbow(8),
            # Monochromatic bands
            self.make_mono_bands((0, 100, 255), 10),   # Blue bands
            self.make_mono_bands((255, 50, 50), 10),   # Red bands
            self.make_mono_bands((50, 255, 100), 10),  # Green bands
            self.make_mono_bands((255, 200, 50), 10),  # Gold bands
            self.make_mono_bands((200, 100, 255), 10), # Purple bands
        ]
        self.current_palette = 0
        self.colors = self.palettes[self.current_palette]

        # Initialize grid with 256 states
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Initialize with boundary values and some seeds
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
        """Initialize with random values and seed points."""
        # Start with random values
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = random.randint(0, 255)

        # Create animated seed points (hotspots that inject energy)
        self.seeds = []
        num_seeds = random.randint(4, 7)
        for _ in range(num_seeds):
            # Choose shape: pinwheel or donut
            shape = random.choice(['pinwheel', 'pinwheel', 'donut'])  # 2:1 ratio

            seed = {
                'base_x': random.uniform(0, GRID_SIZE),
                'base_y': random.uniform(0, GRID_SIZE),
                'phase': random.uniform(0, math.pi * 2),
                'freq': random.uniform(0.8, 1.5),
                'shape': shape,
                # Movement parameters
                'move_radius': random.uniform(12, 22),  # How far they roam
                'move_speed_x': random.uniform(0.15, 0.35) * random.choice([-1, 1]),
                'move_speed_y': random.uniform(0.15, 0.35) * random.choice([-1, 1]),
                'move_phase_x': random.uniform(0, math.pi * 2),
                'move_phase_y': random.uniform(0, math.pi * 2),
                # Rotation parameters
                'rot_speed': random.uniform(0.4, 1.0) * random.choice([-1, 1]),
                'rot_phase': random.uniform(0, math.pi * 2),
            }

            if shape == 'pinwheel':
                seed['arm_length'] = random.randint(2, 3)
                seed['num_arms'] = random.choice([3, 4])  # 3 or 4 arm pinwheels
            else:  # donut
                seed['inner_radius'] = 1
                seed['outer_radius'] = 2

            self.seeds.append(seed)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.right:
            self.speed = min(5.0, self.speed + 0.2)
            consumed = True
        if input_state.left:
            self.speed = max(0.1, self.speed - 0.2)
            consumed = True

        if input_state.up:
            self.current_palette = (self.current_palette + 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True
        if input_state.down:
            self.current_palette = (self.current_palette - 1) % len(self.palettes)
            self.colors = self.palettes[self.current_palette]
            consumed = True

        if input_state.action:
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
        """Perform one step of the Rug cellular automaton."""
        # Update all cells with toroidal wrapping
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Average of 8 neighbors with wrapping
                total = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx = (x + dx) % GRID_SIZE
                        ny = (y + dy) % GRID_SIZE
                        total += self.grid[ny][nx]

                avg = total // 8
                # New state is average + 1, wrapping at 256
                self.next_grid[y][x] = (avg + 1) % 256

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid

        # Inject energy from animated seed points
        for seed in self.seeds:
            # Calculate moving position
            move_x = math.sin(self.time * seed['move_speed_x'] + seed['move_phase_x']) * seed['move_radius']
            move_y = math.sin(self.time * seed['move_speed_y'] + seed['move_phase_y']) * seed['move_radius']

            cx = int(seed['base_x'] + move_x) % GRID_SIZE
            cy = int(seed['base_y'] + move_y) % GRID_SIZE

            # Pulsing value based on time
            val = int(128 + 127 * math.sin(self.time * seed['freq'] + seed['phase']))

            # Current rotation angle
            angle = self.time * seed['rot_speed'] + seed['rot_phase']

            if seed['shape'] == 'pinwheel':
                # Draw rotating pinwheel arms
                num_arms = seed['num_arms']
                arm_length = seed['arm_length']
                for arm in range(num_arms):
                    arm_angle = angle + (arm * 2 * math.pi / num_arms)
                    for dist in range(arm_length + 1):
                        px = int(cx + math.cos(arm_angle) * dist) % GRID_SIZE
                        py = int(cy + math.sin(arm_angle) * dist) % GRID_SIZE
                        self.grid[py][px] = val
            else:  # donut
                # Draw rotating donut (ring of points)
                inner_r = seed['inner_radius']
                outer_r = seed['outer_radius']
                # Draw points around the ring
                num_points = 12
                for i in range(num_points):
                    point_angle = angle + (i * 2 * math.pi / num_points)
                    # Average of inner and outer radius for the ring
                    r = (inner_r + outer_r) / 2
                    px = int(cx + math.cos(point_angle) * r) % GRID_SIZE
                    py = int(cy + math.sin(point_angle) * r) % GRID_SIZE
                    self.grid[py][px] = val

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                color = self.colors[state]
                self.display.set_pixel(x, y, color)

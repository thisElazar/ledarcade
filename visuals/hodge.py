"""
Hodge - Hodgepodge Machine Visual
=================================
A cellular automaton simulating the Belousov-Zhabotinsky
chemical reaction. Creates beautiful spiral wave patterns
that self-organize from random initial conditions.

Based on the Hodgepodge Machine by Gerhardt & Schuster,
as implemented in CelLab by Rudy Rucker and John Walker.
Source: https://fourmilab.ch/cellab/

Controls:
  Up/Down    - Change color palette
  Left/Right - Adjust infection rate (g parameter)
  Space      - Reset with random pattern
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Hodge(Visual):
    name = "HODGE"
    description = "Spiral waves"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.speed = 1.0
        self.base_interval = 0.1   # Base CA rate, tuned for Pi
        self.min_interval = 0.05   # Fastest allowed (prevents lag)

        # Hodgepodge parameters
        self.n = 63  # Max state (ill state)
        self.k1 = 2  # Infection divisor for infected neighbors
        self.k2 = 3  # Infection divisor for ill neighbors
        self.g = 5.0   # Infection growth constant (float for fine tuning)

        # Color palettes - smooth gradients first, then banded options
        self.palettes = [
            # Smooth gradients (original)
            self.make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150), (100, 255, 100), (255, 255, 0), (255, 100, 0), (150, 0, 100)]),
            self.make_gradient([(150, 0, 100), (255, 100, 0), (255, 255, 0), (100, 255, 100), (0, 200, 150), (0, 100, 200), (20, 0, 80)]),
            self.make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150), (100, 200, 200), (200, 230, 255)]),
            self.make_gradient([(200, 230, 255), (100, 200, 200), (0, 150, 150), (0, 50, 100), (0, 0, 40)]),
            self.make_gradient([(40, 0, 0), (150, 30, 0), (255, 100, 0), (255, 200, 50), (255, 255, 200)]),
            self.make_gradient([(0, 20, 0), (0, 80, 40), (50, 150, 50), (150, 220, 100), (220, 255, 180)]),
            self.make_gradient([(40, 0, 60), (100, 0, 150), (200, 50, 200), (255, 150, 220), (255, 220, 255)]),
            # Banded options
            self.make_banded_rainbow(8),
            self.make_banded_rainbow(4),
            self.make_mono_bands((0, 100, 255), 6),
            self.make_mono_bands((255, 50, 50), 6),
            self.make_mono_bands((50, 255, 100), 6),
        ]
        self.current_palette = 0
        self.colors = self.palettes[self.current_palette]

        # Initialize grid
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        self.init_random()

    def make_gradient(self, key_colors):
        """Create gradient with n+1 colors from key colors."""
        gradient = []
        num_colors = self.n + 1  # 64 colors for states 0-63
        segments = len(key_colors) - 1
        per_segment = num_colors // segments

        for i in range(num_colors):
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
        num_colors = self.n + 1
        rainbow = [
            (255, 0, 0),     # Red
            (255, 127, 0),   # Orange
            (255, 255, 0),   # Yellow
            (0, 255, 0),     # Green
            (0, 0, 255),     # Blue
            (75, 0, 130),    # Indigo
            (148, 0, 211),   # Violet
        ]
        for i in range(num_colors):
            cycle_pos = (i * num_bands * len(rainbow)) / num_colors
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
        num_colors = self.n + 1
        for i in range(num_colors):
            band_pos = (i * num_bands * 2) / num_colors
            brightness = (math.sin(band_pos * math.pi) + 1) / 2
            gradient.append((
                int(base_color[0] * brightness),
                int(base_color[1] * brightness),
                int(base_color[2] * brightness),
            ))
        return gradient

    def init_random(self):
        """Initialize with random states."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Mostly healthy with some infected
                if random.random() < 0.2:
                    self.grid[y][x] = random.randint(1, self.n)
                else:
                    self.grid[y][x] = 0

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
            self.g = max(2.0, self.g - 0.25)
            consumed = True
        if input_state.right:
            self.g = min(15, self.g + 0.25)
            consumed = True

        if (input_state.action_l or input_state.action_r):
            self.init_random()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt

        # Speed adjusts interval: faster = shorter interval
        effective_interval = max(self.base_interval / self.speed, self.min_interval)

        # Only run 1 CA step per frame max (prevents lag)
        if self.update_timer >= effective_interval:
            self.update_timer = 0
            self.step_ca()

    def step_ca(self):
        """Perform one step of the Hodgepodge cellular automaton."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]

                # Count neighbors
                infected = 0  # States 1 to n-1
                ill = 0       # State n
                total = state  # Sum including self

                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        if dx == 0 and dy == 0:
                            continue
                        nx = (x + dx) % GRID_SIZE
                        ny = (y + dy) % GRID_SIZE
                        neighbor = self.grid[ny][nx]
                        total += neighbor

                        if neighbor == self.n:
                            ill += 1
                        elif neighbor > 0:
                            infected += 1

                # Apply rules based on current state
                if state == 0:
                    # Healthy cell - can become infected
                    new_state = (infected // self.k1) + (ill // self.k2)
                    self.next_grid[y][x] = min(new_state, self.n)

                elif state == self.n:
                    # Ill cell - becomes healthy
                    self.next_grid[y][x] = 0

                else:
                    # Infected cell - gets sicker
                    # Average of 9-cell neighborhood + g
                    avg = total // 9
                    new_state = avg + int(self.g)
                    self.next_grid[y][x] = min(new_state, self.n)

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid

        # Check if simulation has died out (all cells healthy)
        alive = False
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] > 0:
                    alive = True
                    break
            if alive:
                break

        if not alive:
            # Auto-reset when everything dies
            self.init_random()

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                color = self.colors[state]
                self.display.set_pixel(x, y, color)

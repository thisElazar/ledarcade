"""
Sandpile - Abelian Sandpile Model
==================================
Self-organized criticality: sand grains accumulate and topple in
chain-reaction avalanches, forming stunning fractal patterns.
Bak, Tang, Wiesenfeld (1987).

Each cell holds an integer count of "sand grains." When a cell
reaches 4 or more grains it topples, distributing one grain to
each cardinal neighbor. Grains that fall off the edge are lost
(open boundary conditions), which is essential for the classic
fractal geometry.

Two modes:
  Center drop  - Grains added at center produce an iconic symmetric fractal.
  Random drop  - Grains added at random positions create organic avalanches.

Controls:
  Up/Down     - Change color palette
  Left/Right  - Adjust speed
  Space       - Toggle center/random drop mode
  Escape      - Exit
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Sandpile(Visual):
    name = "SANDPILE"
    description = "Fractal avalanches"
    category = "digital"

    # Color palettes: each maps grain counts 0-3 plus overflow (4+)
    PALETTES = [
        # Classic: dark blue, cyan, yellow-green, purple, white
        ((5, 5, 30), (0, 200, 200), (200, 220, 0), (180, 0, 220), (255, 255, 255)),
        # Fire: black, red, orange, yellow, white
        ((10, 5, 0), (200, 30, 0), (255, 140, 0), (255, 240, 50), (255, 255, 255)),
        # Ocean: deep blue, blue, cyan, seafoam, white
        ((5, 5, 40), (20, 60, 180), (0, 180, 220), (100, 240, 200), (255, 255, 255)),
        # Earth: dark brown, brown, tan, cream, white
        ((20, 10, 5), (120, 70, 30), (180, 140, 80), (230, 210, 170), (255, 255, 255)),
        # Neon: black, magenta, cyan, green, white
        ((5, 0, 5), (220, 0, 200), (0, 220, 220), (0, 255, 80), (255, 255, 255)),
        # Grayscale: black, dark, medium, light, white
        ((10, 10, 10), (80, 80, 80), (150, 150, 150), (220, 220, 220), (255, 255, 255)),
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0

        # Grid of grain counts, indexed [y][x]
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Drop mode: True = center, False = random
        self.center_mode = True

        # Grains added per update cycle
        self.drop_rate = 4

        # Topple passes per frame
        self.topple_steps = 100

        # Timing
        self.update_timer = 0.0
        self.base_interval = 0.03
        self.min_interval = 0.01

        # Palette
        self.palette_index = 0

        # Center coordinates
        self.cx = GRID_SIZE // 2
        self.cy = GRID_SIZE // 2

        # Track total grains dropped
        self.total_dropped = 0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action:
            # Toggle between center and random drop mode
            self.center_mode = not self.center_mode
            # Reset grid when switching modes so the new pattern is clean
            self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
            self.total_dropped = 0
            consumed = True

        # Up/Down: cycle color palette
        if input_state.up:
            self.palette_index = (self.palette_index + 1) % len(self.PALETTES)
            consumed = True
        if input_state.down:
            self.palette_index = (self.palette_index - 1) % len(self.PALETTES)
            consumed = True

        # Left/Right: adjust speed
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        return consumed

    def _drop_grains(self):
        """Add grains to the grid."""
        for _ in range(self.drop_rate):
            if self.center_mode:
                x, y = self.cx, self.cy
            else:
                x = random.randint(0, GRID_SIZE - 1)
                y = random.randint(0, GRID_SIZE - 1)
            self.grid[y][x] += 1
            self.total_dropped += 1

    def _topple(self, max_steps):
        """Run toppling until stable or max_steps exhausted.

        Each step scans the entire grid once. Any cell with >= 4 grains
        topples: loses 4 grains, each cardinal neighbor gains 1.
        Grains that would go off-edge are lost (open boundary).

        Returns True if the grid is now stable (no cell >= 4).
        """
        size = GRID_SIZE
        grid = self.grid

        for _ in range(max_steps):
            stable = True
            for y in range(size):
                row = grid[y]
                for x in range(size):
                    if row[x] >= 4:
                        stable = False
                        # Topple this cell
                        row[x] -= 4
                        # Distribute to cardinal neighbors (open boundary)
                        if y > 0:
                            grid[y - 1][x] += 1
                        if y < size - 1:
                            grid[y + 1][x] += 1
                        if x > 0:
                            row[x - 1] += 1
                        if x < size - 1:
                            row[x + 1] += 1
            if stable:
                return True
        return False

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt

        effective_interval = max(self.base_interval / self.speed, self.min_interval)

        if self.update_timer >= effective_interval:
            self.update_timer -= effective_interval

            # Drop new grains
            self._drop_grains()

            # Scale topple steps with speed for responsive feel
            steps = int(self.topple_steps * self.speed)
            steps = max(10, min(500, steps))
            self._topple(steps)

    def draw(self):
        colors = self.PALETTES[self.palette_index]
        grid = self.grid
        set_pixel = self.display.set_pixel

        for y in range(GRID_SIZE):
            row = grid[y]
            for x in range(GRID_SIZE):
                grains = row[x]
                if grains >= 4:
                    # Mid-avalanche: white flash
                    set_pixel(x, y, colors[4])
                else:
                    set_pixel(x, y, colors[grains])

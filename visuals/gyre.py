"""
Gyre - Swirling Vortex Visual
=============================
A cellular automaton that creates beautiful swirling spiral
patterns through directional cell state propagation. The plane
is divided into quadrants, and cells copy from different
neighbors based on their quadrant, creating a refraction effect
at boundaries that draws patterns into spiraling gyres.

Conceived by William Gosper and implemented in CelLab by
Rudy Rucker and John Walker.
Source: https://fourmilab.ch/cellab/

Controls:
  Up/Down    - Change color palette
  Left/Right - Adjust speed
  Space      - Reset with new pattern
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Gyre(Visual):
    name = "GYRE"
    description = "Swirling vortex"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.speed = 1.0
        self.update_timer = 0.0
        self.update_interval = 0.12  # Slower updates for smoother look

        # Color palettes - smooth gradients first, then gentler banding
        self.palettes = [
            # Smooth gradients (original)
            self.make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150), (100, 255, 100), (255, 255, 0), (255, 100, 0), (150, 0, 100)]),
            self.make_gradient([(150, 0, 100), (255, 100, 0), (255, 255, 0), (100, 255, 100), (0, 200, 150), (0, 100, 200), (20, 0, 80)]),
            self.make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150), (100, 200, 200), (200, 230, 255)]),
            self.make_gradient([(40, 0, 0), (150, 30, 0), (255, 100, 0), (255, 200, 50), (255, 255, 200)]),
            self.make_gradient([(0, 20, 0), (0, 80, 40), (50, 150, 50), (150, 220, 100), (220, 255, 180)]),
            self.make_gradient([(40, 0, 60), (100, 0, 150), (200, 50, 200), (255, 150, 220), (255, 220, 255)]),
            # Gentler banding (halved)
            self.make_banded_rainbow(8),
            self.make_banded_rainbow(4),
            self.make_mono_bands((0, 100, 255), 5),
            self.make_mono_bands((255, 50, 50), 5),
            self.make_mono_bands((50, 255, 100), 5),
            self.make_mono_bands((200, 100, 255), 5),
        ]
        self.current_palette = 0
        self.colors = self.palettes[self.current_palette]

        # Initialize grid with 256 states
        self.grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.next_grid = [[0 for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        # Center of the gyre (for quadrant calculation)
        self.center_x = GRID_SIZE // 2
        self.center_y = GRID_SIZE // 2

        # Initialize with seed pattern
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
        """Initialize with seed patterns that will spiral nicely."""
        # Clear grid
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = 0

        # Choose a pattern type
        pattern_type = random.choice(['blocks', 'rings', 'random_clusters', 'cross'])

        if pattern_type == 'blocks':
            # Create several blocks of random colors near center
            num_blocks = random.randint(3, 6)
            for _ in range(num_blocks):
                bx = random.randint(self.center_x - 15, self.center_x + 15)
                by = random.randint(self.center_y - 15, self.center_y + 15)
                size = random.randint(4, 10)
                color = random.randint(64, 255)
                for dy in range(size):
                    for dx in range(size):
                        nx = (bx + dx) % GRID_SIZE
                        ny = (by + dy) % GRID_SIZE
                        self.grid[ny][nx] = color

        elif pattern_type == 'rings':
            # Create concentric rings
            num_rings = random.randint(3, 5)
            for i in range(num_rings):
                radius = 5 + i * 6
                color = (i + 1) * (256 // (num_rings + 1))
                self.draw_ring(self.center_x, self.center_y, radius, color, 2)

        elif pattern_type == 'random_clusters':
            # Scatter random clusters
            num_clusters = random.randint(8, 15)
            for _ in range(num_clusters):
                cx = random.randint(10, GRID_SIZE - 10)
                cy = random.randint(10, GRID_SIZE - 10)
                size = random.randint(3, 8)
                color = random.randint(64, 255)
                for dy in range(-size, size + 1):
                    for dx in range(-size, size + 1):
                        if dx * dx + dy * dy <= size * size:
                            nx = (cx + dx) % GRID_SIZE
                            ny = (cy + dy) % GRID_SIZE
                            self.grid[ny][nx] = color

        else:  # cross
            # Create a cross pattern
            arm_length = 20
            arm_width = 4
            color = random.randint(128, 255)
            # Horizontal arm
            for dx in range(-arm_length, arm_length + 1):
                for dy in range(-arm_width // 2, arm_width // 2 + 1):
                    nx = (self.center_x + dx) % GRID_SIZE
                    ny = (self.center_y + dy) % GRID_SIZE
                    self.grid[ny][nx] = color
            # Vertical arm
            for dy in range(-arm_length, arm_length + 1):
                for dx in range(-arm_width // 2, arm_width // 2 + 1):
                    nx = (self.center_x + dx) % GRID_SIZE
                    ny = (self.center_y + dy) % GRID_SIZE
                    self.grid[ny][nx] = color

    def draw_ring(self, cx, cy, radius, color, thickness):
        """Draw a ring of given radius and thickness."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - cx
                dy = y - cy
                dist = (dx * dx + dy * dy) ** 0.5
                if abs(dist - radius) <= thickness / 2:
                    self.grid[y][x] = color

    def get_quadrant(self, x, y):
        """
        Determine which quadrant a cell is in relative to center.
        Quadrants are arranged as:
          2  0
          3  1
        """
        if x >= self.center_x:
            if y < self.center_y:
                return 0  # Northeast
            else:
                return 1  # Southeast
        else:
            if y < self.center_y:
                return 2  # Northwest
            else:
                return 3  # Southwest

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
            self.speed = max(0.1, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(5.0, self.speed + 0.2)
            consumed = True

        if (input_state.action_l or input_state.action_r):
            self.init_pattern()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt * self.speed

        while self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            self.step_ca()

    def step_ca(self):
        """
        Perform one step of the Gyre cellular automaton.

        The Gyre rule divides the plane into quadrants and has each cell
        copy from a specific neighbor based on its quadrant:
        - Quadrant 0 (NE): copies from southeast neighbor
        - Quadrant 1 (SE): copies from southwest neighbor
        - Quadrant 2 (NW): copies from northeast neighbor
        - Quadrant 3 (SW): copies from northwest neighbor

        This creates a circulation effect where patterns spiral toward
        and around the center due to refraction at quadrant boundaries.
        """
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                quadrant = self.get_quadrant(x, y)

                # Determine source cell based on quadrant
                # Each quadrant copies from a diagonal neighbor that creates
                # a clockwise circulation pattern
                if quadrant == 0:  # NE quadrant: copy from SE
                    sx = (x + 1) % GRID_SIZE
                    sy = (y + 1) % GRID_SIZE
                elif quadrant == 1:  # SE quadrant: copy from SW
                    sx = (x - 1) % GRID_SIZE
                    sy = (y + 1) % GRID_SIZE
                elif quadrant == 2:  # NW quadrant: copy from NE
                    sx = (x + 1) % GRID_SIZE
                    sy = (y - 1) % GRID_SIZE
                else:  # SW quadrant: copy from NW
                    sx = (x - 1) % GRID_SIZE
                    sy = (y - 1) % GRID_SIZE

                # Blend gyre source with local neighborhood for blob cohesion
                gyre_val = self.grid[sy][sx]

                # Average with immediate neighbors for smoother blobs
                n = self.grid[(y - 1) % GRID_SIZE][x]
                s = self.grid[(y + 1) % GRID_SIZE][x]
                e = self.grid[y][(x + 1) % GRID_SIZE]
                w = self.grid[y][(x - 1) % GRID_SIZE]
                center = self.grid[y][x]

                local_avg = (n + s + e + w + center * 2) // 6

                # Blend: mostly gyre direction but with local smoothing
                self.next_grid[y][x] = (gyre_val * 2 + local_avg) // 3

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid

        # Inject color energy to keep patterns alive
        if random.random() < 0.15:
            # Inject near center for spiraling effect
            angle = random.uniform(0, 6.28)
            dist = random.uniform(5, 20)
            import math
            cx = int(self.center_x + math.cos(angle) * dist)
            cy = int(self.center_y + math.sin(angle) * dist)
            size = random.randint(2, 5)
            color = random.randint(100, 255)
            for dy in range(-size, size + 1):
                for dx in range(-size, size + 1):
                    if dx * dx + dy * dy <= size * size:
                        nx = (cx + dx) % GRID_SIZE
                        ny = (cy + dy) % GRID_SIZE
                        self.grid[ny][nx] = color

        # Also occasionally inject at edges to create new spiraling material
        if random.random() < 0.1:
            edge = random.choice(['top', 'bottom', 'left', 'right'])
            color = random.randint(100, 255)
            length = random.randint(5, 15)
            if edge == 'top':
                x = random.randint(0, GRID_SIZE - 1)
                for i in range(length):
                    self.grid[i][x] = color
            elif edge == 'bottom':
                x = random.randint(0, GRID_SIZE - 1)
                for i in range(length):
                    self.grid[GRID_SIZE - 1 - i][x] = color
            elif edge == 'left':
                y = random.randint(0, GRID_SIZE - 1)
                for i in range(length):
                    self.grid[y][i] = color
            else:
                y = random.randint(0, GRID_SIZE - 1)
                for i in range(length):
                    self.grid[y][GRID_SIZE - 1 - i] = color

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                color = self.colors[state]
                self.display.set_pixel(x, y, color)

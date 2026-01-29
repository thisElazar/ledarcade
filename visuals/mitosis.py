"""
Mitosis - Cell Colony Simulation
=================================
Colonies grow, divide when large enough, compete for space, and die.
A cellular automata approach inspired by biological cell division.

Rules:
  - Colonies grow over time
  - Above threshold size, colonies split into two daughter cells
  - Overlapping colonies compete (larger absorbs smaller)
  - Old colonies fade and die
  - Random mutations can occur

Controls:
  Up/Down    - Change color palette
  Left/Right - Adjust growth rate
  Space      - Add new colonies
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


class Colony:
    """A single cell colony that can grow and divide."""

    def __init__(self, x, y, radius=2.0, energy=1.0, generation=0):
        self.x = x
        self.y = y
        self.radius = radius
        self.energy = energy  # Health/vitality (0-1)
        self.age = 0.0
        self.generation = generation  # How many splits from original
        self.growth_rate = random.uniform(0.8, 1.2)  # Individual variation
        self.hue_offset = random.uniform(-0.1, 0.1)  # Color variation
        self.alive = True

    def area(self):
        return math.pi * self.radius * self.radius


class Mitosis(Visual):
    name = "MITOSIS"
    description = "Cell division"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Simulation parameters - tuned for equilibrium
        self.base_growth_rate = 1.2  # Radius units per second
        self.split_radius = 6.5      # Split when radius exceeds this
        self.min_radius = 2.0        # Minimum colony size
        self.max_colonies = 40       # Population cap
        self.competition_strength = 0.5  # Stronger competition
        self.fade_rate = 0.35        # Faster energy drain
        self.energy_from_area = 0.008  # Less energy from size

        # Colony list
        self.colonies = []
        self._seed_colonies()

        # Color palettes - gradient from black to bright
        self.palettes = [
            # Classic green (biological)
            ((0, 0, 0), (20, 70, 30), (50, 140, 60), (100, 200, 100), (180, 255, 180)),
            # Electric blue
            ((0, 0, 0), (20, 40, 120), (50, 100, 200), (100, 160, 255), (200, 220, 255)),
            # Magenta pulse
            ((0, 0, 0), (80, 20, 100), (150, 50, 170), (200, 100, 220), (255, 180, 255)),
            # Fire bands
            ((0, 0, 0), (120, 30, 0), (200, 80, 0), (255, 160, 50), (255, 230, 150)),
            # Cyan glow
            ((0, 0, 0), (0, 80, 90), (30, 150, 160), (80, 210, 210), (180, 255, 255)),
            # Gold automata
            ((0, 0, 0), (90, 60, 10), (170, 120, 30), (230, 180, 60), (255, 230, 140)),
            # Radioactive (banded green-yellow)
            ((0, 0, 0), (30, 90, 0), (80, 180, 0), (160, 230, 50), (220, 255, 150)),
            # Vaporwave (pink-cyan bands)
            ((0, 0, 0), (120, 40, 90), (200, 80, 150), (100, 180, 220), (220, 200, 255)),
            # Lava bands
            ((0, 0, 0), (100, 20, 10), (180, 50, 20), (230, 120, 40), (255, 200, 100)),
            # Cool white
            ((0, 0, 0), (40, 50, 60), (100, 120, 140), (170, 190, 210), (240, 250, 255)),
        ]
        self.current_palette = 0

        # Render buffer for smooth blobs
        self.buffer = [[(0, 0, 0) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

    def _seed_colonies(self):
        """Create initial colonies."""
        self.colonies = []
        num_seeds = random.randint(3, 6)
        for _ in range(num_seeds):
            x = random.uniform(12, GRID_SIZE - 12)
            y = random.uniform(12, GRID_SIZE - 12)
            radius = random.uniform(2.5, 3.5)
            self.colonies.append(Colony(x, y, radius, energy=0.8))

    def _add_colony(self, x, y):
        """Add a new colony at position."""
        if len(self.colonies) < self.max_colonies:
            self.colonies.append(Colony(x, y, radius=2.5, energy=1.0))

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up:
            self.current_palette = (self.current_palette + 1) % len(self.palettes)
            consumed = True

        if input_state.down:
            self.current_palette = (self.current_palette - 1) % len(self.palettes)
            consumed = True

        if input_state.left:
            self.base_growth_rate = max(0.5, self.base_growth_rate - 0.2)
            consumed = True

        if input_state.right:
            self.base_growth_rate = min(4.0, self.base_growth_rate + 0.2)
            consumed = True

        if (input_state.action_l or input_state.action_r):
            # Add new colonies at random positions
            for _ in range(3):
                x = random.uniform(8, GRID_SIZE - 8)
                y = random.uniform(8, GRID_SIZE - 8)
                self._add_colony(x, y)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Update each colony
        for colony in self.colonies:
            if not colony.alive:
                continue

            colony.age += dt

            # Grow based on energy
            growth = self.base_growth_rate * colony.growth_rate * colony.energy * dt
            colony.radius += growth

            # Energy dynamics: gain from size, lose from age
            colony.energy += colony.area() * self.energy_from_area * dt
            colony.energy -= self.fade_rate * dt
            colony.energy = max(0.0, min(1.5, colony.energy))

            # Die if energy depleted or too old
            max_age = 15 - colony.generation * 2  # Later generations die younger
            if colony.energy <= 0.1 or colony.age > max(5, max_age):
                colony.alive = False
                continue

            # Boundary push
            margin = colony.radius + 2
            if colony.x < margin:
                colony.x = margin
            elif colony.x > GRID_SIZE - margin:
                colony.x = GRID_SIZE - margin
            if colony.y < margin:
                colony.y = margin
            elif colony.y > GRID_SIZE - margin:
                colony.y = GRID_SIZE - margin

        # Mitosis: split large colonies
        new_colonies = []
        for colony in self.colonies:
            if colony.alive and colony.radius >= self.split_radius:
                if len(self.colonies) + len(new_colonies) < self.max_colonies:
                    # Split into two daughter cells
                    angle = random.uniform(0, math.pi * 2)
                    offset = colony.radius * 0.4
                    new_radius = colony.radius * 0.6

                    # Daughter 1 (modify existing)
                    colony.x += math.cos(angle) * offset
                    colony.y += math.sin(angle) * offset
                    colony.radius = new_radius
                    colony.energy *= 0.4  # Splitting is costly
                    colony.age = 0  # Reset age
                    colony.generation += 1

                    # Daughter 2 (new colony)
                    daughter = Colony(
                        colony.x - math.cos(angle) * offset * 2,
                        colony.y - math.sin(angle) * offset * 2,
                        new_radius,
                        energy=colony.energy,
                        generation=colony.generation
                    )
                    daughter.age = 0
                    daughter.hue_offset = colony.hue_offset + random.uniform(-0.05, 0.05)
                    new_colonies.append(daughter)

        self.colonies.extend(new_colonies)

        # Competition: overlapping colonies compete
        for i, c1 in enumerate(self.colonies):
            if not c1.alive:
                continue
            for c2 in self.colonies[i + 1:]:
                if not c2.alive:
                    continue

                dx = c2.x - c1.x
                dy = c2.y - c1.y
                dist = math.sqrt(dx * dx + dy * dy)
                overlap = (c1.radius + c2.radius) - dist

                if overlap > 0:
                    # Push apart
                    if dist > 0.1:
                        push = overlap * 0.3
                        nx, ny = dx / dist, dy / dist
                        c1.x -= nx * push * 0.5
                        c1.y -= ny * push * 0.5
                        c2.x += nx * push * 0.5
                        c2.y += ny * push * 0.5

                    # Energy competition - larger drains smaller
                    if c1.area() > c2.area():
                        transfer = self.competition_strength * dt
                        c2.energy -= transfer
                        c1.energy += transfer * 0.5
                    else:
                        transfer = self.competition_strength * dt
                        c1.energy -= transfer
                        c2.energy += transfer * 0.5

        # Remove dead colonies
        self.colonies = [c for c in self.colonies if c.alive]

        # Spontaneous generation if population too low
        if len(self.colonies) < 3 and random.random() < 0.02:
            x = random.uniform(10, GRID_SIZE - 10)
            y = random.uniform(10, GRID_SIZE - 10)
            self._add_colony(x, y)

    def draw(self):
        palette = self.palettes[self.current_palette]

        # Clear buffer to black
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.buffer[y][x] = (0, 0, 0)

        # Draw colonies as soft blobs using distance fields
        for colony in self.colonies:
            if not colony.alive:
                continue

            # Bounding box for efficiency
            r = int(colony.radius) + 3
            x0 = max(0, int(colony.x) - r)
            x1 = min(GRID_SIZE, int(colony.x) + r + 1)
            y0 = max(0, int(colony.y) - r)
            y1 = min(GRID_SIZE, int(colony.y) + r + 1)

            for py in range(y0, y1):
                for px in range(x0, x1):
                    dx = px - colony.x
                    dy = py - colony.y
                    dist = math.sqrt(dx * dx + dy * dy)

                    if dist < colony.radius + 1:
                        # Intensity based on distance from edge
                        if dist < colony.radius - 1:
                            intensity = 1.0
                        else:
                            intensity = max(0, colony.radius + 1 - dist) / 2

                        # Modulate by energy
                        intensity *= 0.5 + colony.energy * 0.5

                        # Color from palette based on intensity (smooth interpolation)
                        intensity = max(0, min(1, intensity))
                        idx = intensity * (len(palette) - 1)
                        idx_low = int(idx)
                        idx_high = min(len(palette) - 1, idx_low + 1)
                        t = idx - idx_low

                        c_low = palette[idx_low]
                        c_high = palette[idx_high]
                        color = (
                            int(c_low[0] + (c_high[0] - c_low[0]) * t),
                            int(c_low[1] + (c_high[1] - c_low[1]) * t),
                            int(c_low[2] + (c_high[2] - c_low[2]) * t),
                        )

                        # Max blend - take brightest, avoids washing out to white
                        existing = self.buffer[py][px]
                        self.buffer[py][px] = (
                            max(existing[0], color[0]),
                            max(existing[1], color[1]),
                            max(existing[2], color[2]),
                        )

        # Copy buffer to display
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, self.buffer[y][x])

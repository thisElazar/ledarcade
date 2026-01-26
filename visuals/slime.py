"""
Slime Mold - Competing colonies
===============================
Multiple slime mold colonies grow and aggressively compete for territory.
One colony may eventually dominate!

Controls:
  Space   - Reset with new random colonies
  Up/Down - Adjust growth speed
  Escape  - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


# Colony colors
COLONY_COLORS = [
    (255, 50, 50),    # Red
    (50, 255, 50),    # Green
    (50, 100, 255),   # Blue
    (255, 255, 50),   # Yellow
    (255, 50, 255),   # Magenta
    (50, 255, 255),   # Cyan
]


class Slime(Visual):
    name = "SLIME"
    description = "Competing colonies"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.growth_speed = 1.0
        self.step_timer = 0.0

        # Grid stores colony ID (0 = empty, 1+ = colony number)
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Strength of each cell (for competition)
        self.strength = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Age of each cell (for brightness)
        self.age = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Number of colonies - always use all 6
        self.num_colonies = 6

        # Colony base power levels (tighter range for balanced start)
        self.colony_base_power = {}
        for i in range(1, self.num_colonies + 1):
            self.colony_base_power[i] = random.uniform(0.95, 1.05)

        # Cache for colony counts (updated each step)
        self._cached_counts = {}
        self._cached_total = 0

        # Spawn initial colonies as small seeds
        self._spawn_colonies()

    def _spawn_colonies(self):
        """Spawn tiny colony seeds at random positions."""
        for colony_id in range(1, self.num_colonies + 1):
            # Find a spot away from edges and other colonies
            for _ in range(50):
                cx = random.randint(8, GRID_SIZE - 8)
                cy = random.randint(8, GRID_SIZE - 8)

                # Check if far enough from existing colonies
                too_close = False
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if self.grid[y][x] > 0:
                            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                            if dist < 15:
                                too_close = True
                                break
                    if too_close:
                        break

                if not too_close:
                    break

            # Spawn a small seed cluster
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if random.random() < 0.7:
                            self.grid[ny][nx] = colony_id
                            self.strength[ny][nx] = 1.0
                            self.age[ny][nx] = 0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action:
            self.reset()
            consumed = True

        if input_state.up:
            self.growth_speed = min(3.0, self.growth_speed + 0.2)
            consumed = True

        if input_state.down:
            self.growth_speed = max(0.2, self.growth_speed - 0.2)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Age all cells
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] > 0:
                    self.age[y][x] += dt

        # Growth timer
        self.step_timer += dt * self.growth_speed

        if self.step_timer >= 0.08:
            self.step_timer = 0
            # Cache colony counts once per step for performance
            self._cached_counts = self._get_colony_counts()
            self._cached_total = sum(self._cached_counts.values())
            self._growth_step()
            self._competition_step()

        # Check for winner - reset if one colony dominates (70%+)
        colony_counts = {}
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                c = self.grid[y][x]
                if c > 0:
                    colony_counts[c] = colony_counts.get(c, 0) + 1

        total_area = GRID_SIZE * GRID_SIZE
        for colony_id, count in colony_counts.items():
            if count >= total_area:
                # Winner! Reset after brief pause
                if random.random() < 0.02:
                    self.reset()
                break

    def _get_colony_counts(self):
        """Count cells per colony."""
        counts = {}
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                c = self.grid[y][x]
                if c > 0:
                    counts[c] = counts.get(c, 0) + 1
        return counts

    def _get_colony_power(self, colony_id):
        """Get dynamic power for a colony based on size (last stand + momentum)."""
        # Use cached counts for performance
        total_cells = getattr(self, '_cached_total', 0)
        if total_cells == 0:
            return 1.0

        my_cells = getattr(self, '_cached_counts', {}).get(colony_id, 0)
        base = self.colony_base_power.get(colony_id, 1.0)

        if my_cells == 0:
            return base

        # Calculate share of territory
        share = my_cells / total_cells

        # Dynamic power modifier:
        # - Very small (< 10% share): "last stand" boost
        # - Medium: normal
        # - Large (> 40% share): momentum boost
        if share < 0.10:
            # Last stand: boost up to 1.3x when nearly eliminated
            modifier = 1.0 + (0.10 - share) * 3  # Up to 1.3 at 0%
        elif share > 0.40:
            # Momentum: boost based on dominance
            modifier = 1.0 + (share - 0.40) * 0.5  # Up to 1.3 at 100%
        else:
            modifier = 1.0

        return base * modifier

    def _count_neighbors(self, x, y):
        """Count neighbors by colony."""
        counts = {}
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    colony = self.grid[ny][nx]
                    if colony > 0:
                        strength = self.strength[ny][nx]
                        if colony not in counts:
                            counts[colony] = 0
                        counts[colony] += strength
        return counts

    def _growth_step(self):
        """Colonies grow into empty space."""
        # Find frontier cells (empty cells adjacent to colonies)
        frontier = []

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] == 0:
                    neighbors = self._count_neighbors(x, y)
                    if neighbors:
                        frontier.append((x, y, neighbors))

        # Grow into frontier cells
        random.shuffle(frontier)

        for x, y, neighbors in frontier:
            # Growth chance
            if random.random() > 0.15:
                continue

            # Winner is colony with most neighbor strength
            winner = max(neighbors, key=neighbors.get)
            strength = neighbors[winner] * self._get_colony_power(winner)

            # Spindly growth: less likely if would create thick area
            same_neighbor_count = sum(1 for dy in [-1, 0, 1] for dx in [-1, 0, 1]
                                       if (dx != 0 or dy != 0) and
                                       0 <= x + dx < GRID_SIZE and
                                       0 <= y + dy < GRID_SIZE and
                                       self.grid[y + dy][x + dx] == winner)

            if same_neighbor_count > 3:
                if random.random() > 0.3:
                    continue

            # Grow!
            self.grid[y][x] = winner
            self.strength[y][x] = min(1.0, strength * 0.3)
            self.age[y][x] = 0

    def _competition_step(self):
        """Colonies attack each other at borders."""
        attacks = []

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                colony = self.grid[y][x]
                if colony == 0:
                    continue

                my_strength = self.strength[y][x] * self._get_colony_power(colony)
                neighbors = self._count_neighbors(x, y)

                # Check for enemy neighbors
                for enemy, enemy_strength in neighbors.items():
                    if enemy != colony:
                        enemy_power = enemy_strength * self._get_colony_power(enemy)

                        # Enemy is stronger? Might take over this cell
                        if enemy_power > my_strength * 1.2:
                            attacks.append((x, y, colony, enemy, enemy_power - my_strength))

        # Process attacks
        for x, y, old_colony, new_colony, advantage in attacks:
            # Probability based on advantage
            if random.random() < advantage * 0.1:
                self.grid[y][x] = new_colony
                self.strength[y][x] = 0.5
                self.age[y][x] = 0

        # Strengthen interior cells, weaken edge cells
        new_strength = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                colony = self.grid[y][x]
                if colony == 0:
                    continue

                neighbors = self._count_neighbors(x, y)
                same = neighbors.get(colony, 0)
                enemies = sum(s for c, s in neighbors.items() if c != colony)
                cell_age = self.age[y][x]

                if enemies > 0:
                    # Under attack - weaken
                    new_strength[y][x] = max(0.1, self.strength[y][x] - 0.02)
                elif same > 3:
                    # Safe interior - strengthen (but not forever)
                    new_strength[y][x] = min(1.0, self.strength[y][x] + 0.01)
                else:
                    new_strength[y][x] = self.strength[y][x]

                # DEATH CYCLE: Very old cells start to decay
                if cell_age > 10:
                    # Old cells weaken over time
                    decay = (cell_age - 10) * 0.003
                    new_strength[y][x] = max(0.1, new_strength[y][x] - decay)

                # BORDER INSTABILITY: Strong cells at borders can randomly destabilize
                if enemies > 0 and self.strength[y][x] > 0.8:
                    if random.random() < 0.01:
                        # Random instability - weaken significantly
                        new_strength[y][x] = 0.3

                # Die if too weak
                if new_strength[y][x] < 0.05:
                    self.grid[y][x] = 0
                    new_strength[y][x] = 0
                    self.age[y][x] = 0

        self.strength = new_strength

    def draw(self):
        self.display.clear(Colors.BLACK)

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                colony = self.grid[y][x]

                if colony > 0:
                    # Get base color for colony
                    base_color = COLONY_COLORS[(colony - 1) % len(COLONY_COLORS)]
                    strength = self.strength[y][x]

                    # Brightness based on strength
                    brightness = 0.3 + 0.7 * strength

                    r = int(base_color[0] * brightness)
                    g = int(base_color[1] * brightness)
                    b = int(base_color[2] * brightness)

                    self.display.set_pixel(x, y, (r, g, b))

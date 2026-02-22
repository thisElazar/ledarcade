"""
Predator-Prey - Lotka-Volterra Ecology
=========================================
Spatial predator-prey dynamics on a 64x64 toroidal grid.
Rabbits (green) reproduce by spreading. Foxes (orange) hunt,
reproduce when fed, starve otherwise. Produces beautiful
traveling waves of predators chasing prey fronts.

Controls:
  Left/Right  - Prey reproduction rate
  Up/Down     - Predator hunting efficiency
  Space       - Reseed
"""

import random
from . import Visual, Display, Colors, GRID_SIZE

# Cell states
EMPTY = 0
RABBIT = 1
FOX = 2

# Neighbor offsets (4-connected, toroidal)
NEIGHBORS = [(0, -1), (0, 1), (-1, 0), (1, 0)]


class PredPrey(Visual):
    name = "PREDATOR-PREY"
    description = "Lotka-Volterra ecology"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.06

        # Tunable parameters
        self.prey_rate = 0.08          # probability rabbit reproduces per step
        self.prey_rate_min = 0.02
        self.prey_rate_max = 0.20

        self.hunt_efficiency = 0.60    # probability fox catches adjacent rabbit
        self.hunt_eff_min = 0.20
        self.hunt_eff_max = 1.00

        # Fox energy parameters
        self.max_energy = 20
        self.eat_energy = 15
        self.reproduce_threshold = 15

        # Grids
        self.grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.energy = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Auto-reseed timer
        self.reseed_delay = 0.0

        # Population counts (updated each step)
        self.rabbit_count = 0
        self.fox_count = 0

        self._seed()

    def _seed(self):
        """Scatter ~30% rabbits and ~5% foxes randomly."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                r = random.random()
                if r < 0.30:
                    self.grid[y][x] = RABBIT
                    self.energy[y][x] = 0
                elif r < 0.35:
                    self.grid[y][x] = FOX
                    self.energy[y][x] = self.max_energy
                else:
                    self.grid[y][x] = EMPTY
                    self.energy[y][x] = 0
        self._count_populations()

    def _count_populations(self):
        """Update cached population counts."""
        rc = 0
        fc = 0
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                s = self.grid[y][x]
                if s == RABBIT:
                    rc += 1
                elif s == FOX:
                    fc += 1
        self.rabbit_count = rc
        self.fox_count = fc

    def _get_neighbors(self, x, y):
        """Return list of (nx, ny) for 4-connected toroidal neighbors."""
        return [
            ((x + dx) % GRID_SIZE, (y + dy) % GRID_SIZE)
            for dx, dy in NEIGHBORS
        ]

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: reseed
        if input_state.action_l or input_state.action_r:
            self.grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
            self.energy = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
            self._seed()
            self.reseed_delay = 0.0
            self.overlay_text = "RESEED"
            self.overlay_timer = 1.5
            consumed = True

        # Left/Right: prey reproduction rate
        if input_state.left:
            self.prey_rate = max(self.prey_rate_min,
                                 round(self.prey_rate - 0.01, 2))
            self.overlay_text = f"PREY {self.prey_rate:.2f}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.right:
            self.prey_rate = min(self.prey_rate_max,
                                 round(self.prey_rate + 0.01, 2))
            self.overlay_text = f"PREY {self.prey_rate:.2f}"
            self.overlay_timer = 1.5
            consumed = True

        # Up/Down: predator hunting efficiency
        if input_state.up_pressed:
            self.hunt_efficiency = min(self.hunt_eff_max,
                                       round(self.hunt_efficiency + 0.05, 2))
            self.overlay_text = f"HUNT {self.hunt_efficiency:.2f}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.down_pressed:
            self.hunt_efficiency = max(self.hunt_eff_min,
                                       round(self.hunt_efficiency - 0.05, 2))
            self.overlay_text = f"HUNT {self.hunt_efficiency:.2f}"
            self.overlay_timer = 1.5
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Auto-reseed when both populations are very low
        if self.rabbit_count < 10 and self.fox_count < 10:
            self.reseed_delay += dt
            if self.reseed_delay >= 2.0:
                self.grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
                self.energy = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
                self._seed()
                self.reseed_delay = 0.0
        else:
            self.reseed_delay = 0.0

        # Step simulation on timer
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    def _step(self):
        """Advance one simulation step, processing cells in random order."""
        N = GRID_SIZE

        # Build random processing order
        coords = [(x, y) for y in range(N) for x in range(N)]
        random.shuffle(coords)

        new_grid = [row[:] for row in self.grid]
        new_energy = [row[:] for row in self.energy]

        # Track which cells have already been written this step
        # to avoid conflicts (e.g. two rabbits reproducing into same cell)
        claimed = [[False] * N for _ in range(N)]

        for x, y in coords:
            state = self.grid[y][x]

            if state == RABBIT:
                # Reproduction: try to spread to a random empty neighbor
                if random.random() < self.prey_rate:
                    nbs = self._get_neighbors(x, y)
                    random.shuffle(nbs)
                    for nx, ny in nbs:
                        if (new_grid[ny][nx] == EMPTY and
                                not claimed[ny][nx]):
                            new_grid[ny][nx] = RABBIT
                            claimed[ny][nx] = True
                            break

            elif state == FOX:
                # Lose energy
                e = self.energy[y][x] - 1

                # Hunt: try to eat an adjacent rabbit
                ate = False
                nbs = self._get_neighbors(x, y)
                random.shuffle(nbs)
                for nx, ny in nbs:
                    # Check current grid for rabbits (not new_grid,
                    # so rabbits don't vanish before being processed)
                    if self.grid[ny][nx] == RABBIT:
                        if random.random() < self.hunt_efficiency:
                            # Eat the rabbit
                            new_grid[ny][nx] = EMPTY
                            new_energy[ny][nx] = 0
                            claimed[ny][nx] = True
                            e += self.eat_energy
                            if e > self.max_energy:
                                e = self.max_energy
                            ate = True
                            break

                # Death check
                if e <= 0:
                    new_grid[y][x] = EMPTY
                    new_energy[y][x] = 0
                    continue

                new_energy[y][x] = e

                # Reproduction
                if e >= self.reproduce_threshold:
                    nbs2 = self._get_neighbors(x, y)
                    random.shuffle(nbs2)
                    for nx, ny in nbs2:
                        if (new_grid[ny][nx] == EMPTY and
                                not claimed[ny][nx]):
                            new_grid[ny][nx] = FOX
                            baby_energy = e // 2
                            new_energy[ny][nx] = baby_energy
                            new_energy[y][x] = e - baby_energy
                            claimed[ny][nx] = True
                            break

        self.grid = new_grid
        self.energy = new_energy
        self._count_populations()

    def draw(self):
        N = GRID_SIZE

        for y in range(N):
            row_grid = self.grid[y]
            row_energy = self.energy[y]
            for x in range(N):
                state = row_grid[x]

                if state == EMPTY:
                    self.display.set_pixel(x, y, (5, 8, 5))

                elif state == RABBIT:
                    # Green; slightly dimmer in dense clusters
                    # Count local rabbit density for visual variation
                    density = 0
                    for dx, dy in NEIGHBORS:
                        nx = (x + dx) % N
                        ny = (y + dy) % N
                        if self.grid[ny][nx] == RABBIT:
                            density += 1
                    # 0 neighbors = bright, 4 = slightly dimmer
                    t = density / 4.0
                    r = int(40 - 20 * t)
                    g = int(220 - 50 * t)
                    b = int(60 - 30 * t)
                    self.display.set_pixel(x, y, (r, g, b))

                elif state == FOX:
                    # Orange gradient based on energy
                    e = row_energy[x]
                    t = max(0.0, min(1.0, e / self.max_energy))
                    # Starving (t=0): dark red (180,40,20)
                    # Well-fed (t=1): bright orange (255,160,40)
                    r = int(180 + 75 * t)
                    g = int(40 + 120 * t)
                    b = int(20 + 20 * t)
                    self.display.set_pixel(x, y, (r, g, b))

        # Population bar at y=63 (bottom row)
        total = self.rabbit_count + self.fox_count
        if total > 0:
            rabbit_px = max(0, int(N * self.rabbit_count / total))
            for bx in range(N):
                if bx < rabbit_px:
                    self.display.set_pixel(bx, N - 1, (30, 180, 50))
                else:
                    self.display.set_pixel(bx, N - 1, (220, 130, 30))
        else:
            # All empty -- dim bar
            for bx in range(N):
                self.display.set_pixel(bx, N - 1, (15, 15, 15))

        # Overlay text (parameter changes, reseed)
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            self.display.draw_text_small(2, 1, self.overlay_text, oc)

        # Population HUD -- show briefly after reseed or always faintly
        pop_text = f"R:{self.rabbit_count} F:{self.fox_count}"
        # Show faint population counter in corner
        self.display.draw_text_small(2, 57, pop_text, (80, 80, 80))

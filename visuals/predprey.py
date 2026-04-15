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

import math
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
    category = "science_macro"

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

        # Textured ground noise (static per reset)
        self.ground_noise = [
            [random.random() for _ in range(GRID_SIZE)]
            for _ in range(GRID_SIZE)
        ]

        # Kill flash events: list of (x, y, age)  -- age in seconds
        self.kill_flashes = []
        # Fox birth glow events: list of (x, y, age)
        self.birth_glows = []

        # Fox head direction cache: (dx, dy) per cell, assigned on spawn
        self.fox_head_dir = [
            [random.choice(NEIGHBORS) for _ in range(GRID_SIZE)]
            for _ in range(GRID_SIZE)
        ]

        # Rolling population history for strip chart (last 64 entries)
        self.pop_history = []

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
            self.kill_flashes.clear()
            self.birth_glows.clear()
            self.pop_history.clear()
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
                self.kill_flashes.clear()
                self.birth_glows.clear()
                self.pop_history.clear()
        else:
            self.reseed_delay = 0.0

        # Age and prune kill flashes (0.2s lifetime)
        self.kill_flashes = [
            (kx, ky, age + dt)
            for kx, ky, age in self.kill_flashes
            if age + dt < 0.2
        ]
        # Age and prune birth glows (0.15s lifetime)
        self.birth_glows = [
            (bx, by, age + dt)
            for bx, by, age in self.birth_glows
            if age + dt < 0.15
        ]

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

        # Event lists for this step
        step_kills = []
        step_births = []

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
                            # Record kill event
                            step_kills.append((nx, ny))
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
                            # Record fox birth event and assign random head dir
                            step_births.append((nx, ny))
                            self.fox_head_dir[ny][nx] = random.choice(NEIGHBORS)
                            break

        self.grid = new_grid
        self.energy = new_energy
        self._count_populations()

        # Append flash events (age starts at 0.0)
        for kx, ky in step_kills:
            self.kill_flashes.append((kx, ky, 0.0))
        # Cap kill flashes
        if len(self.kill_flashes) > 50:
            self.kill_flashes = self.kill_flashes[-50:]

        for bx, by in step_births:
            self.birth_glows.append((bx, by, 0.0))
        # Cap birth glows
        if len(self.birth_glows) > 50:
            self.birth_glows = self.birth_glows[-50:]

        # Record population history (one entry per sim step)
        total_cells = N * N
        self.pop_history.append((
            self.rabbit_count / total_cells,
            self.fox_count / total_cells,
        ))
        if len(self.pop_history) > 64:
            self.pop_history = self.pop_history[-64:]

    def draw(self):
        N = GRID_SIZE
        sim_rows = 58  # rows 0-57 for simulation; 58 = separator; 59-63 = chart

        # -- Main grid rendering (rows 0-57) --
        for y in range(sim_rows):
            row_grid = self.grid[y]
            row_energy = self.energy[y]
            for x in range(N):
                state = row_grid[x]

                if state == EMPTY:
                    # Textured ground
                    noise = self.ground_noise[y][x]
                    # Blend between dark earth and faint grass
                    shimmer = math.sin(self.time * 0.5 + x * 0.3 + y * 0.2) * 3
                    er = int(8 + (5 - 8) * noise)      # 8 -> 5
                    eg = int(12 + (18 - 12) * noise)    # 12 -> 18
                    eb = int(5 + (8 - 5) * noise)       # 5 -> 8
                    eg = max(0, min(255, eg + int(shimmer)))
                    self.display.set_pixel(x, y, (er, eg, eb))

                elif state == RABBIT:
                    # Wavefront-aware coloring based on neighbor count
                    density = 0
                    for dx, dy in NEIGHBORS:
                        nx = (x + dx) % N
                        ny = (y + dy) % N
                        if self.grid[ny][nx] == RABBIT:
                            density += 1
                    # Isolated (0-1): bright (50, 230, 70)
                    # Clustered (3-4): dim (35, 160, 40)
                    if density <= 1:
                        t = density / 1.0 if density > 0 else 0.0
                        # 0 neighbors: (50,230,70), 1 neighbor: blend toward mid
                        r = int(50 - 5 * t)
                        g = int(230 - 23 * t)
                        b = int(70 - 10 * t)
                    else:
                        # 2-4: blend from mid toward dim
                        t = (density - 2) / 2.0
                        r = int(42 - 7 * t)
                        g = int(195 - 35 * t)
                        b = int(55 - 15 * t)
                    self.display.set_pixel(x, y, (r, g, b))

                elif state == FOX:
                    # Orange gradient based on energy (body pixel)
                    e = row_energy[x]
                    t = max(0.0, min(1.0, e / self.max_energy))
                    # Starving (t=0): dark red (180,40,20)
                    # Well-fed (t=1): bright orange (255,160,40)
                    r = int(180 + 75 * t)
                    g = int(40 + 120 * t)
                    b = int(20 + 20 * t)
                    self.display.set_pixel(x, y, (r, g, b))

                    # Head pixel in direction of prey (brighter/yellower)
                    nbs = self._get_neighbors(x, y)
                    head_dx, head_dy = 0, 0
                    for nx, ny in nbs:
                        if ny < sim_rows and self.grid[ny][nx] == RABBIT:
                            head_dx = nx - x
                            head_dy = ny - y
                            if head_dx > 1:
                                head_dx = -1
                            elif head_dx < -1:
                                head_dx = 1
                            if head_dy > 1:
                                head_dy = -1
                            elif head_dy < -1:
                                head_dy = 1
                            break
                    if head_dx == 0 and head_dy == 0:
                        head_dx, head_dy = self.fox_head_dir[y][x]
                    hx = (x + head_dx) % N
                    hy = (y + head_dy) % N
                    # Only draw head if target cell is not another fox body
                    if hy < sim_rows and self.grid[hy][hx] != FOX:
                        hr = min(255, r + 30)
                        hg = min(255, g + 50)
                        hb = min(255, b + 10)
                        self.display.set_pixel(hx, hy, (hr, hg, hb))

        # -- Kill flashes (white sparks) --
        for kx, ky, age in self.kill_flashes:
            if ky >= sim_rows:
                continue
            fade = 1.0 - age / 0.2  # 1.0 -> 0.0 over 0.2s
            # Center pixel: white-yellow
            cr = int(255 * fade)
            cg = int(255 * fade)
            cb = int(200 * fade)
            self.display.set_pixel(kx, ky, (cr, cg, cb))
            # Cardinal neighbors at half brightness on first frame only
            if age < 0.06:
                hr = cr // 2
                hg = cg // 2
                hb = cb // 2
                for dx, dy in NEIGHBORS:
                    nx = (kx + dx) % N
                    ny = (ky + dy) % N
                    if ny < sim_rows:
                        self.display.set_pixel(nx, ny, (hr, hg, hb))

        # -- Fox birth glows (warm single pixel) --
        for bx, by, age in self.birth_glows:
            if by >= sim_rows:
                continue
            fade = 1.0 - age / 0.15
            br = int(255 * fade)
            bg = int(200 * fade)
            bb = int(100 * fade)
            self.display.set_pixel(bx, by, (br, bg, bb))

        # -- Separator line at row 58 --
        for sx in range(N):
            self.display.set_pixel(sx, 58, (25, 25, 25))

        # -- Rolling population strip chart (rows 59-63, 5 rows) --
        chart_top = 59
        chart_rows = 5
        if self.pop_history:
            # Find peak for normalization
            peak = 0.0
            for rf, ff in self.pop_history:
                peak = max(peak, rf + ff)
            if peak < 0.001:
                peak = 0.001
            # Scale so peak fills the chart
            scale = chart_rows / peak

            hist_len = len(self.pop_history)
            for col in range(N):
                # Map column to history index
                idx = col - (N - hist_len)
                if idx < 0 or idx >= hist_len:
                    # No data yet for this column -- dim
                    for row in range(chart_rows):
                        self.display.set_pixel(col, chart_top + row, (3, 3, 3))
                    continue

                rf, ff = self.pop_history[idx]
                rabbit_px = max(0, min(chart_rows, int(rf * scale + 0.5)))
                fox_px = max(0, min(chart_rows - rabbit_px,
                                    int(ff * scale + 0.5)))

                # Draw from bottom up: rabbits green, then foxes orange, rest dark
                for row in range(chart_rows):
                    py = chart_top + (chart_rows - 1 - row)  # bottom-up
                    if row < rabbit_px:
                        self.display.set_pixel(col, py, (30, 180, 50))
                    elif row < rabbit_px + fox_px:
                        self.display.set_pixel(col, py, (220, 130, 30))
                    else:
                        self.display.set_pixel(col, py, (3, 3, 3))
        else:
            # No history yet
            for col in range(N):
                for row in range(chart_rows):
                    self.display.set_pixel(col, chart_top + row, (3, 3, 3))

        # Overlay text (parameter changes, reseed)
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            self.display.draw_text_small(2, 1, self.overlay_text, oc)

        # Population HUD -- faint counter above the chart
        pop_text = f"R:{self.rabbit_count} F:{self.fox_count}"
        self.display.draw_text_small(2, 52, pop_text, (80, 80, 80))

"""
Ecosystem - Multi-Trophic Food Web Simulation
===============================================
Five trophic levels: Soil -> Grass -> Herbivore -> Predator -> Apex.
Each organism has an energy budget -- eat to gain, move to spend,
reproduce when surplus, die when depleted. Dead organisms decompose
back into soil nutrients. The 10% rule emerges naturally: far fewer
apex predators than herbivores, always.

Controls:
  Left/Right  - Sunlight / primary productivity
  Up/Down     - Cycle view mode
  Action      - Reseed
"""

import random
from . import Visual, Display, Colors, GRID_SIZE

# Cell content types
EMPTY = 0
GRASS = 1
HERBIVORE = 2
PREDATOR = 3
APEX = 4
DECOMP = 5

# Colors
COL_GRASS = (30, 180, 50)
COL_HERB = (220, 200, 40)
COL_PRED = (240, 120, 30)
COL_APEX = (220, 50, 40)
COL_DECOMP = (120, 80, 30)

# Neighbor offsets (4-connected)
DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]
# Extended search (8-connected + distance 2)
DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

VIEW_MODES = ["ALL", "ENERGY", "GRASS", "HERBI", "PRED", "APEX"]


class Ecosystem(Visual):
    name = "ECOSYSTEM"
    description = "Multi-trophic food web"
    category = "nature"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.06

        # Sunlight / primary productivity
        self.sunlight = 0.5
        self.sun_min = 0.2
        self.sun_max = 1.0

        # View mode
        self.view_idx = 0

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_text = ""

        N = GRID_SIZE

        # Soil nutrient grid (0.0 - 1.0 per cell)
        self.soil = [[1.0] * N for _ in range(N)]

        # Organism grid -- stores type
        self.grid = [[EMPTY] * N for _ in range(N)]

        # Energy grid (for mobile organisms and decomp timer)
        self.energy = [[0.0] * N for _ in range(N)]

        # Population counts
        self.counts = {GRASS: 0, HERBIVORE: 0, PREDATOR: 0, APEX: 0, DECOMP: 0}

        self._seed()

    def _seed(self):
        N = GRID_SIZE
        # Reset grids
        for y in range(N):
            for x in range(N):
                self.soil[y][x] = 1.0
                self.grid[y][x] = EMPTY
                self.energy[y][x] = 0.0

        # Scatter grass (~40%)
        cells = [(x, y) for y in range(N) for x in range(N)]
        random.shuffle(cells)
        n_grass = int(0.4 * N * N)
        for i in range(n_grass):
            x, y = cells[i]
            self.grid[y][x] = GRASS
            self.energy[y][x] = 0

        # Place herbivores
        remaining = cells[n_grass:]
        random.shuffle(remaining)
        for i in range(min(80, len(remaining))):
            x, y = remaining[i]
            self.grid[y][x] = HERBIVORE
            self.energy[y][x] = 50

        # Place predators
        remaining = remaining[80:]
        random.shuffle(remaining)
        for i in range(min(20, len(remaining))):
            x, y = remaining[i]
            self.grid[y][x] = PREDATOR
            self.energy[y][x] = 60

        # Place apex
        remaining = remaining[20:]
        random.shuffle(remaining)
        for i in range(min(5, len(remaining))):
            x, y = remaining[i]
            self.grid[y][x] = APEX
            self.energy[y][x] = 80

        self._count()

    def _count(self):
        c = {GRASS: 0, HERBIVORE: 0, PREDATOR: 0, APEX: 0, DECOMP: 0}
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                s = self.grid[y][x]
                if s in c:
                    c[s] += 1
        self.counts = c

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Action: reseed
        if input_state.action_l or input_state.action_r:
            self._seed()
            self.overlay_text = "RESEED"
            self.overlay_timer = 1.5
            consumed = True

        # Left/Right: sunlight
        if input_state.left:
            self.sunlight = max(self.sun_min, round(self.sunlight - 0.02, 2))
            self.overlay_text = f"SUN {self.sunlight:.1f}"
            self.overlay_timer = 1.5
            consumed = True
        if input_state.right:
            self.sunlight = min(self.sun_max, round(self.sunlight + 0.02, 2))
            self.overlay_text = f"SUN {self.sunlight:.1f}"
            self.overlay_timer = 1.5
            consumed = True

        # Up/Down: cycle view
        if input_state.up_pressed:
            self.view_idx = (self.view_idx - 1) % len(VIEW_MODES)
            self.overlay_text = VIEW_MODES[self.view_idx]
            self.overlay_timer = 1.5
            consumed = True
        if input_state.down_pressed:
            self.view_idx = (self.view_idx + 1) % len(VIEW_MODES)
            self.overlay_text = VIEW_MODES[self.view_idx]
            self.overlay_timer = 1.5
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    def _find_prey_near(self, x, y, prey_type, radius=2):
        """Find nearest prey of given type within radius. Returns (px, py) or None."""
        N = GRID_SIZE
        best = None
        best_dist = 999
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % N
                ny = (y + dy) % N
                if self.grid[ny][nx] == prey_type:
                    d = abs(dx) + abs(dy)
                    if d < best_dist:
                        best_dist = d
                        best = (nx, ny)
        return best

    def _move_toward(self, x, y, tx, ty):
        """Return (nx, ny) one step toward target, toroidal."""
        N = GRID_SIZE
        dx = ((tx - x + N + N // 2) % N) - N // 2
        dy = ((ty - y + N + N // 2) % N) - N // 2
        # Move in the dominant direction
        if abs(dx) >= abs(dy):
            return (x + (1 if dx > 0 else -1)) % N, y
        else:
            return x, (y + (1 if dy > 0 else -1)) % N

    def _step(self):
        N = GRID_SIZE
        grid = self.grid
        energy = self.energy
        soil = self.soil

        # --- Phase 1: Soil regeneration (sunlight drives it) ---
        regen = 0.02 * self.sunlight
        for y in range(N):
            for x in range(N):
                if soil[y][x] < 1.0:
                    soil[y][x] = min(1.0, soil[y][x] + regen)

        # --- Phase 2: Decomposition ---
        for y in range(N):
            for x in range(N):
                if grid[y][x] == DECOMP:
                    energy[y][x] -= 1
                    # Enrich surrounding soil
                    soil[y][x] = min(1.0, soil[y][x] + 0.15)
                    for dx, dy2 in DIRS:
                        nx, ny = (x + dx) % N, (y + dy2) % N
                        soil[ny][nx] = min(1.0, soil[ny][nx] + 0.05)
                    if energy[y][x] <= 0:
                        grid[y][x] = EMPTY
                        energy[y][x] = 0

        # --- Phase 3: Grass growth ---
        # Collect empty cells adjacent to grass for reproduction
        grass_spread = []
        for y in range(N):
            for x in range(N):
                if grid[y][x] == GRASS:
                    # Grass survives if soil > 0.1
                    if soil[y][x] < 0.1:
                        grid[y][x] = EMPTY
                        continue
                    # Consume nutrients
                    soil[y][x] = max(0.0, soil[y][x] - 0.1)
                    # Try to spread
                    if random.random() < 0.12 * self.sunlight:
                        for dx2, dy2 in DIRS:
                            nx, ny = (x + dx2) % N, (y + dy2) % N
                            if grid[ny][nx] == EMPTY and soil[ny][nx] > 0.3:
                                grass_spread.append((nx, ny))

        # Place new grass (avoid duplicates)
        spread_set = set()
        random.shuffle(grass_spread)
        for gx, gy in grass_spread:
            if (gx, gy) not in spread_set and grid[gy][gx] == EMPTY:
                grid[gy][gx] = GRASS
                spread_set.add((gx, gy))

        # --- Phase 4: Mobile organisms (randomized order) ---
        movers = []
        for y in range(N):
            for x in range(N):
                t = grid[y][x]
                if t in (HERBIVORE, PREDATOR, APEX):
                    movers.append((x, y, t))
        random.shuffle(movers)

        # Track claimed cells to prevent collisions
        claimed = set()

        for ox, oy, otype in movers:
            # Check if this organism is still here (might have been eaten)
            if grid[oy][ox] != otype:
                continue

            e = energy[oy][ox]

            # Energy cost
            if otype == HERBIVORE:
                e -= 1
                prey_type = GRASS
                eat_gain = 20
                repro_thresh = 80
            elif otype == PREDATOR:
                e -= 2
                prey_type = HERBIVORE
                eat_gain = 40
                repro_thresh = 100
            else:  # APEX
                e -= 3
                prey_type = PREDATOR
                eat_gain = 60
                repro_thresh = 120

            # Death
            if e <= 0:
                grid[oy][ox] = DECOMP
                energy[oy][ox] = 5  # decomp timer
                continue

            energy[oy][ox] = e

            # Try to eat adjacent prey
            ate = False
            nbs = [(ox + dx, oy + dy) for dx, dy in DIRS]
            random.shuffle(nbs)
            for nx, ny in nbs:
                nx %= N
                ny %= N
                if grid[ny][nx] == prey_type:
                    # Eat it
                    if prey_type == GRASS:
                        grid[ny][nx] = EMPTY
                    else:
                        grid[ny][nx] = DECOMP
                        energy[ny][nx] = 5
                    e += eat_gain
                    energy[oy][ox] = e
                    ate = True
                    break

            # Movement (if didn't eat, try to move toward prey or randomly)
            if not ate:
                target = self._find_prey_near(ox, oy, prey_type, 2)
                if target:
                    mx, my = self._move_toward(ox, oy, target[0], target[1])
                else:
                    d = random.choice(DIRS)
                    mx = (ox + d[0]) % N
                    my = (oy + d[1]) % N

                if (grid[my][mx] == EMPTY and (mx, my) not in claimed):
                    grid[my][mx] = otype
                    energy[my][mx] = e
                    grid[oy][ox] = EMPTY
                    energy[oy][ox] = 0
                    claimed.add((mx, my))
                    ox, oy = mx, my  # update position for reproduction

            # Reproduction
            if e >= repro_thresh:
                nbs2 = [(ox + dx, oy + dy) for dx, dy in DIRS]
                random.shuffle(nbs2)
                for nx, ny in nbs2:
                    nx %= N
                    ny %= N
                    if grid[ny][nx] == EMPTY and (nx, ny) not in claimed:
                        baby_e = e // 2
                        energy[oy][ox] = e - baby_e
                        grid[ny][nx] = otype
                        energy[ny][nx] = baby_e
                        claimed.add((nx, ny))
                        break

        # --- Phase 5: Auto-recovery ---
        self._count()
        if self.counts[HERBIVORE] == 0:
            self._scatter(HERBIVORE, 5, 50)
        if self.counts[PREDATOR] == 0:
            self._scatter(PREDATOR, 3, 60)
        if self.counts[APEX] == 0:
            self._scatter(APEX, 1, 80)
        self._count()

    def _scatter(self, otype, n, start_energy):
        """Place n organisms of otype at random empty cells."""
        N = GRID_SIZE
        empties = []
        for y in range(N):
            for x in range(N):
                if self.grid[y][x] == EMPTY:
                    empties.append((x, y))
        random.shuffle(empties)
        for i in range(min(n, len(empties))):
            x, y = empties[i]
            self.grid[y][x] = otype
            self.energy[y][x] = start_energy

    def draw(self):
        self.display.clear()
        N = GRID_SIZE
        view = VIEW_MODES[self.view_idx]

        # Pyramid area: x = 56..63 (width 8)
        PYRA_X = 56

        for y in range(N):
            for x in range(N):
                # Leave pyramid area for overlay
                if x >= PYRA_X:
                    continue

                s = self.grid[y][x]

                if view == "ALL":
                    self._draw_cell_all(x, y, s)
                elif view == "ENERGY":
                    self._draw_cell_energy(x, y, s)
                elif view == "GRASS":
                    self._draw_cell_filter(x, y, s, GRASS)
                elif view == "HERBI":
                    self._draw_cell_filter(x, y, s, HERBIVORE)
                elif view == "PRED":
                    self._draw_cell_filter(x, y, s, PREDATOR)
                elif view == "APEX":
                    self._draw_cell_filter(x, y, s, APEX)

        # Draw biomass pyramid
        self._draw_pyramid()

        # Overlay text
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            self.display.draw_text_small(2, 1, self.overlay_text, oc)

        # Population HUD (faint)
        pop = (f"G{self.counts[GRASS]} H{self.counts[HERBIVORE]} "
               f"P{self.counts[PREDATOR]} A{self.counts[APEX]}")
        self.display.draw_text_small(2, 57, pop, (60, 60, 60))

    def _draw_cell_all(self, x, y, s):
        """Draw cell in ALL view mode."""
        if s == EMPTY:
            # Show soil nutrients as background
            n = self.soil[y][x]
            g = int(10 + 20 * n)
            self.display.set_pixel(x, y, (5, g, 5))
        elif s == GRASS:
            # Vary green by soil richness
            n = self.soil[y][x]
            g = int(120 + 60 * n)
            self.display.set_pixel(x, y, (20, g, 35))
        elif s == HERBIVORE:
            self.display.set_pixel(x, y, COL_HERB)
        elif s == PREDATOR:
            self.display.set_pixel(x, y, COL_PRED)
        elif s == APEX:
            self.display.set_pixel(x, y, COL_APEX)
        elif s == DECOMP:
            self.display.set_pixel(x, y, COL_DECOMP)

    def _draw_cell_energy(self, x, y, s):
        """Draw cell colored by energy level (blue=low, red=high)."""
        if s == EMPTY:
            n = self.soil[y][x]
            self.display.set_pixel(x, y, (3, int(8 * n), 3))
        elif s == GRASS:
            self.display.set_pixel(x, y, (10, 60, 10))
        elif s == DECOMP:
            self.display.set_pixel(x, y, (40, 25, 10))
        else:
            # Map energy to blue->red gradient
            if s == HERBIVORE:
                t = min(1.0, self.energy[y][x] / 80.0)
            elif s == PREDATOR:
                t = min(1.0, self.energy[y][x] / 100.0)
            else:
                t = min(1.0, self.energy[y][x] / 120.0)
            r = int(40 + 200 * t)
            b = int(200 - 180 * t)
            g = int(40 * (1.0 - abs(t - 0.5) * 2))
            self.display.set_pixel(x, y, (r, g, b))

    def _draw_cell_filter(self, x, y, s, highlight):
        """Draw cell, highlighting only one species."""
        if s == highlight:
            if s == GRASS:
                self.display.set_pixel(x, y, COL_GRASS)
            elif s == HERBIVORE:
                self.display.set_pixel(x, y, COL_HERB)
            elif s == PREDATOR:
                self.display.set_pixel(x, y, COL_PRED)
            elif s == APEX:
                self.display.set_pixel(x, y, COL_APEX)
        else:
            # Dim everything else
            self.display.set_pixel(x, y, (3, 3, 3))

    def _draw_pyramid(self):
        """Draw biomass pyramid at x=56..63, showing population bars."""
        PX = 56
        PW = 8  # pyramid width
        N = GRID_SIZE

        # Background for pyramid area
        for y in range(N):
            for x in range(PX, PX + PW):
                self.display.set_pixel(x, y, (2, 2, 2))

        # Population values
        g = self.counts[GRASS]
        h = self.counts[HERBIVORE]
        p = self.counts[PREDATOR]
        a = self.counts[APEX]

        # Scale: grass gets full width, others proportional
        max_pop = max(g, 1)
        levels = [
            (g, COL_GRASS),
            (h, COL_HERB),
            (p, COL_PRED),
            (a, COL_APEX),
        ]

        # Draw from bottom up, each level gets a band
        band_h = 14  # height per band
        gap = 1
        start_y = N - 2  # bottom margin

        for i, (pop, color) in enumerate(levels):
            bar_w = max(1, int(PW * pop / max_pop)) if pop > 0 else 0
            bar_top = start_y - (i + 1) * (band_h + gap)
            bar_bot = start_y - i * (band_h + gap)

            # Center the bar
            bar_x = PX + (PW - bar_w) // 2

            for y in range(max(0, bar_top), min(N, bar_bot)):
                for x in range(bar_x, min(PX + PW, bar_x + bar_w)):
                    # Slight gradient: brighter at center
                    cx = bar_x + bar_w // 2
                    dist = abs(x - cx)
                    fade = max(0.5, 1.0 - dist * 0.1)
                    c = (int(color[0] * fade), int(color[1] * fade),
                         int(color[2] * fade))
                    self.display.set_pixel(x, y, c)

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

# Colors -- maximally separated hues
COL_HERB = (80, 200, 255)    # cyan-blue
COL_PRED = (255, 140, 40)    # orange
COL_APEX = (255, 50, 220)    # magenta-pink
COL_DECOMP = (120, 80, 30)

# Neighbor offsets (4-connected)
DIRS = [(0, -1), (0, 1), (-1, 0), (1, 0)]
# Extended search (8-connected + distance 2)
DIRS8 = [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]

VIEW_MODES = ["NATURAL", "ENERGY", "XRAY"]

# Maximum event particles
MAX_EVENTS = 30


class Ecosystem(Visual):
    name = "ECOSYSTEM"
    description = "Multi-trophic food web"
    category = "science_macro"

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

        # Overlay (for control feedback)
        self.overlay_timer = 0.0
        self.overlay_text = ""

        # Event particles: (x, y, kind, timer) where kind is 'eat' or 'die'
        self.events = []

        N = GRID_SIZE

        # Soil nutrient grid (0.0 - 1.0 per cell)
        self.soil = [[1.0] * N for _ in range(N)]

        # Soil noise grid -- generated via bilinear interpolation of 8x8 coarse grid
        self.soil_noise = [[0.0] * N for _ in range(N)]

        # Organism grid -- stores type
        self.grid = [[EMPTY] * N for _ in range(N)]

        # Energy grid (for mobile organisms and decomp timer)
        self.energy = [[0.0] * N for _ in range(N)]

        # Facing direction grid (for mobile organisms)
        self.facing = [[0] * N for _ in range(N)]

        # Population counts
        self.counts = {GRASS: 0, HERBIVORE: 0, PREDATOR: 0, APEX: 0, DECOMP: 0}

        self._seed()

    def _generate_soil_noise(self):
        """Generate spatially coherent soil noise via bilinear interpolation of an 8x8 coarse grid."""
        N = GRID_SIZE
        G = 8  # coarse grid size
        cell_size = N / G  # 8.0 pixels per coarse cell

        # Generate coarse random grid (with wrap-around padding)
        coarse = [[random.random() * 0.4 - 0.2 for _ in range(G)] for _ in range(G)]

        for y in range(N):
            for x in range(N):
                # Map pixel to coarse grid coordinates
                gx = x / cell_size
                gy = y / cell_size
                # Integer coarse cell indices
                gx0 = int(gx) % G
                gy0 = int(gy) % G
                gx1 = (gx0 + 1) % G
                gy1 = (gy0 + 1) % G
                # Fractional position within the coarse cell
                fx = gx - int(gx)
                fy = gy - int(gy)
                # Bilinear interpolation
                top = coarse[gy0][gx0] * (1 - fx) + coarse[gy0][gx1] * fx
                bot = coarse[gy1][gx0] * (1 - fx) + coarse[gy1][gx1] * fx
                self.soil_noise[y][x] = top * (1 - fy) + bot * fy

    def _seed(self):
        N = GRID_SIZE
        # Reset grids
        for y in range(N):
            for x in range(N):
                self.soil[y][x] = 1.0
                self.grid[y][x] = EMPTY
                self.energy[y][x] = 0.0
                self.facing[y][x] = random.randint(0, 3)

        # Regenerate soil noise (spatially coherent)
        self._generate_soil_noise()

        # Clear events
        self.events = []

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
            self.energy[y][x] = 70

        # Place predators
        remaining = remaining[80:]
        random.shuffle(remaining)
        for i in range(min(20, len(remaining))):
            x, y = remaining[i]
            self.grid[y][x] = PREDATOR
            self.energy[y][x] = 80

        # Place apex
        remaining = remaining[20:]
        random.shuffle(remaining)
        for i in range(min(5, len(remaining))):
            x, y = remaining[i]
            self.grid[y][x] = APEX
            self.energy[y][x] = 100

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

        # Decay event particle timers
        if self.events:
            alive = []
            for ex, ey, kind, timer in self.events:
                t = timer - dt
                if t > 0:
                    alive.append((ex, ey, kind, t))
            self.events = alive

        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    def _facing_from_delta(self, dx, dy):
        """Return facing direction index from movement delta."""
        if abs(dx) >= abs(dy):
            return 3 if dx > 0 else 2  # RIGHT or LEFT
        else:
            return 1 if dy > 0 else 0  # DOWN or UP

    def _find_near(self, x, y, target_types, radius=3):
        """Find nearest organism of any given type within radius. Returns (px, py) or None."""
        N = GRID_SIZE
        best = None
        best_dist = 999
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % N
                ny = (y + dy) % N
                if self.grid[ny][nx] in target_types:
                    d = abs(dx) + abs(dy)
                    if d < best_dist:
                        best_dist = d
                        best = (nx, ny)
        return best

    def _find_prey_near(self, x, y, prey_type, radius=3):
        """Find nearest prey of given type within radius. Returns (px, py) or None."""
        return self._find_near(x, y, (prey_type,), radius)

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

    def _move_away(self, x, y, tx, ty):
        """Return (nx, ny) one step away from threat, toroidal."""
        N = GRID_SIZE
        dx = ((tx - x + N + N // 2) % N) - N // 2
        dy = ((ty - y + N + N // 2) % N) - N // 2
        # Flee in the dominant direction (opposite of toward)
        if abs(dx) >= abs(dy):
            return (x + (-1 if dx > 0 else 1)) % N, y
        else:
            return x, (y + (-1 if dy > 0 else 1)) % N

    def _add_event(self, x, y, kind, duration):
        """Add an event particle, capping at MAX_EVENTS."""
        if len(self.events) < MAX_EVENTS:
            self.events.append((x, y, kind, duration))

    def _step(self):
        N = GRID_SIZE
        grid = self.grid
        energy = self.energy
        soil = self.soil
        facing = self.facing

        # --- Phase 1: Soil regeneration (sunlight drives it) ---
        regen = 0.03 * self.sunlight
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
        grass_spread = []
        for y in range(N):
            for x in range(N):
                if grid[y][x] == GRASS:
                    # Grass survives if soil > 0.1
                    if soil[y][x] < 0.1:
                        grid[y][x] = EMPTY
                        continue
                    # Consume nutrients
                    soil[y][x] = max(0.0, soil[y][x] - 0.07)
                    # Try to spread to adjacent empty cells
                    if random.random() < 0.15 * self.sunlight:
                        for dx2, dy2 in DIRS:
                            nx, ny = (x + dx2) % N, (y + dy2) % N
                            if grid[ny][nx] == EMPTY and soil[ny][nx] > 0.25:
                                grass_spread.append((nx, ny))
                elif grid[y][x] == EMPTY and soil[y][x] > 0.85:
                    # Spontaneous grass on very rich soil
                    if random.random() < 0.02 * self.sunlight:
                        grass_spread.append((x, y))

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

            # Energy cost (halved for longer lifetimes)
            if otype == HERBIVORE:
                e -= 0.5
                prey_type = GRASS
                eat_gain = 25
                repro_thresh = 80
                threat_types = (PREDATOR, APEX)
            elif otype == PREDATOR:
                e -= 1
                prey_type = HERBIVORE
                eat_gain = 50
                repro_thresh = 100
                threat_types = (APEX,)
            else:  # APEX
                e -= 1.5
                prey_type = PREDATOR
                eat_gain = 70
                repro_thresh = 120
                threat_types = ()

            # Death
            if e <= 0:
                grid[oy][ox] = DECOMP
                energy[oy][ox] = 5  # decomp timer
                self._add_event(ox, oy, 'die', 0.3)
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
                    # Update facing toward prey
                    fdx = ((nx - ox + N + N // 2) % N) - N // 2
                    fdy = ((ny - oy + N + N // 2) % N) - N // 2
                    facing[oy][ox] = self._facing_from_delta(fdx, fdy)
                    # Eat it
                    if prey_type == GRASS:
                        grid[ny][nx] = EMPTY
                    else:
                        grid[ny][nx] = DECOMP
                        energy[ny][nx] = 5
                    e += eat_gain
                    energy[oy][ox] = e
                    ate = True
                    self._add_event(ox, oy, 'eat', 0.4)
                    break

            # Movement: flee threats > chase prey > wander
            if not ate:
                threat = None
                if threat_types:
                    threat = self._find_near(ox, oy, threat_types, 3)

                if threat:
                    # Flee from nearest threat
                    mx, my = self._move_away(ox, oy, threat[0], threat[1])
                else:
                    # Chase prey or wander
                    target = self._find_prey_near(ox, oy, prey_type, 3)
                    if target:
                        mx, my = self._move_toward(ox, oy, target[0], target[1])
                    else:
                        d = random.choice(DIRS)
                        mx = (ox + d[0]) % N
                        my = (oy + d[1]) % N

                if (grid[my][mx] == EMPTY and (mx, my) not in claimed):
                    # Update facing direction
                    fdx = ((mx - ox + N + N // 2) % N) - N // 2
                    fdy = ((my - oy + N + N // 2) % N) - N // 2
                    facing[my][mx] = self._facing_from_delta(fdx, fdy)
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
                        # Child faces away from parent
                        fdx = ((nx - ox + N + N // 2) % N) - N // 2
                        fdy = ((ny - oy + N + N // 2) % N) - N // 2
                        facing[ny][nx] = self._facing_from_delta(fdx, fdy)
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

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def _px(self, x, y, color):
        """Set pixel with bounds check."""
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.display.set_pixel(x, y, color)

    def _clamp(self, v):
        return max(0, min(255, int(v)))

    def _sunlight_tint(self, r, g, b):
        """Apply subtle ambient tint based on sunlight level."""
        s = self.sunlight
        if s > 0.5:
            # High sunlight: warm golden shift
            t = (s - 0.5) * 2.0  # 0..1
            r = self._clamp(r + 8 * t)
            g = self._clamp(g + 4 * t)
        else:
            # Low sunlight: cool blue shift
            t = (0.5 - s) * 2.0  # 0..1
            b = self._clamp(b + 6 * t)
        return (r, g, b)

    def draw(self):
        self.display.clear()
        N = GRID_SIZE
        view = VIEW_MODES[self.view_idx]

        # Draw area is rows 0..61 (bottom 2 rows reserved for population bar)
        draw_h = N - 2

        # --- Pass 1: Background (soil, grass, decomp) ---
        for y in range(draw_h):
            for x in range(N):
                s = self.grid[y][x]
                if view == "NATURAL":
                    self._draw_bg_natural(x, y, s)
                elif view == "ENERGY":
                    self._draw_bg_energy(x, y, s)
                else:  # XRAY
                    pass  # black background, drawn by clear()

        # --- Pass 2: Organism sprites (trophic order: herbi, pred, apex) ---
        herbivores = []
        predators = []
        apexes = []
        for y in range(draw_h):
            for x in range(N):
                s = self.grid[y][x]
                if s == HERBIVORE:
                    herbivores.append((x, y))
                elif s == PREDATOR:
                    predators.append((x, y))
                elif s == APEX:
                    apexes.append((x, y))

        if view == "NATURAL":
            self._draw_sprites_natural(herbivores, predators, apexes)
        elif view == "ENERGY":
            self._draw_sprites_energy(herbivores, predators, apexes)
        else:  # XRAY
            self._draw_sprites_xray(herbivores, predators, apexes)

        # --- Pass 3: Event particles ---
        self._draw_events()

        # --- Pass 4: Population bar (bottom 2 rows, y=62-63) ---
        self._draw_population_bar()

        # --- Pass 5: Control feedback overlay ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            self.display.draw_text_small(2, 1, self.overlay_text, oc)

    # --- Background drawing ---

    def _draw_bg_natural(self, x, y, s):
        """Draw background pixel for NATURAL view."""
        noise = self.soil_noise[y][x]
        if s == EMPTY:
            n = self.soil[y][x]
            # Warm earth tones for empty soil
            r = self._clamp(20 + 30 * n + 15 * noise)
            g = self._clamp(12 + 18 * n + 10 * noise)
            b = self._clamp(5 + 8 * n + 5 * noise)
            self.display.set_pixel(x, y, self._sunlight_tint(r, g, b))
        elif s == GRASS:
            n = self.soil[y][x]
            base_g = 120 + 60 * n + 30 * noise
            g = int(max(90, min(200, base_g)))
            r = int(max(10, min(40, 20 + 10 * noise)))
            b = int(max(20, min(50, 35 + 10 * noise)))
            self.display.set_pixel(x, y, self._sunlight_tint(r, g, b))
        elif s == DECOMP:
            t = self.energy[y][x] / 5.0  # 1.0=fresh, 0.0=almost gone
            r = int(60 + 60 * t)
            g = int(35 + 45 * t)
            b = int(10 + 20 * t)
            self.display.set_pixel(x, y, (r, g, b))
        # HERBIVORE/PREDATOR/APEX drawn in sprite pass

    def _draw_bg_energy(self, x, y, s):
        """Draw background pixel for ENERGY view -- nutrient heatmap on soil."""
        if s == EMPTY:
            n = self.soil[y][x]
            # Blue-to-red nutrient heatmap
            r = self._clamp(int(120 * n))
            b = self._clamp(int(80 * (1.0 - n)))
            g = self._clamp(int(30 * n))
            self.display.set_pixel(x, y, (r, g, b))
        elif s == GRASS:
            self.display.set_pixel(x, y, (10, 60, 10))
        elif s == DECOMP:
            self.display.set_pixel(x, y, (40, 25, 10))
        # Mobile organisms drawn in sprite pass

    # --- Sprite drawing ---

    def _draw_herb_sprite(self, x, y, color):
        """Herbivore: single bright pixel."""
        self._px(x, y, color)

    def _draw_pred_sprite(self, x, y, color):
        """Predator: clean 2x2 block."""
        self._px(x, y, color)
        self._px(x + 1, y, color)
        self._px(x, y + 1, color)
        self._px(x + 1, y + 1, color)

    def _draw_apex_sprite(self, x, y, color):
        """Apex: 5px cross/plus shape."""
        self._px(x, y, color)      # center
        self._px(x - 1, y, color)  # left
        self._px(x + 1, y, color)  # right
        self._px(x, y - 1, color)  # up
        self._px(x, y + 1, color)  # down

    def _draw_sprites_natural(self, herbivores, predators, apexes):
        """Draw all organism sprites in trophic order (NATURAL view)."""
        for x, y in herbivores:
            e = self.energy[y][x]
            bright = max(0.5, min(1.0, e / 80.0))
            color = (int(COL_HERB[0] * bright),
                     int(COL_HERB[1] * bright),
                     int(COL_HERB[2] * bright))
            self._draw_herb_sprite(x, y, color)

        for x, y in predators:
            self._draw_pred_sprite(x, y, COL_PRED)

        for x, y in apexes:
            self._draw_apex_sprite(x, y, COL_APEX)

    def _draw_sprites_energy(self, herbivores, predators, apexes):
        """Draw organism sprites with energy-based blue->red gradient."""
        for group, max_e, draw_fn in [
            (herbivores, 80.0, self._draw_herb_sprite),
            (predators, 100.0, self._draw_pred_sprite),
            (apexes, 120.0, self._draw_apex_sprite),
        ]:
            for x, y in group:
                t = min(1.0, self.energy[y][x] / max_e)
                r = int(40 + 200 * t)
                b = int(200 - 180 * t)
                g = int(40 * (1.0 - abs(t - 0.5) * 2))
                draw_fn(x, y, (r, g, b))

    def _draw_sprites_xray(self, herbivores, predators, apexes):
        """XRAY view: black bg, all creatures at full species color."""
        for x, y in herbivores:
            self._draw_herb_sprite(x, y, COL_HERB)
        for x, y in predators:
            self._draw_pred_sprite(x, y, COL_PRED)
        for x, y in apexes:
            self._draw_apex_sprite(x, y, COL_APEX)

    def _draw_events(self):
        """Render event particles: eat = white burst, die = red flicker."""
        for ex, ey, kind, timer in self.events:
            if kind == 'eat':
                # Bright white-to-species-color burst, fading out
                max_t = 0.4
                alpha = min(1.0, timer / (max_t * 0.5))
                # Determine species color at this cell (may have moved, use white base)
                s = self.grid[ey][ex] if 0 <= ex < GRID_SIZE and 0 <= ey < GRID_SIZE else EMPTY
                if s == HERBIVORE:
                    base = COL_HERB
                elif s == PREDATOR:
                    base = COL_PRED
                elif s == APEX:
                    base = COL_APEX
                else:
                    base = (255, 255, 255)
                # Lerp from white toward species color as timer decays
                fade = timer / max_t  # 1.0 = just started, 0.0 = ending
                r = self._clamp(base[0] + (255 - base[0]) * fade * alpha)
                g = self._clamp(base[1] + (255 - base[1]) * fade * alpha)
                b = self._clamp(base[2] + (255 - base[2]) * fade * alpha)
                self._px(ex, ey, (r, g, b))
            elif kind == 'die':
                # Dim red flicker
                max_t = 0.3
                alpha = min(1.0, timer / (max_t * 0.5))
                brightness = int(140 * alpha)
                self._px(ex, ey, (brightness, int(brightness * 0.2), 0))

    def _draw_population_bar(self):
        """Draw stacked proportional population bar on bottom 2 rows (y=62-63)."""
        N = GRID_SIZE
        total = (self.counts[GRASS] + self.counts[HERBIVORE]
                 + self.counts[PREDATOR] + self.counts[APEX])
        if total == 0:
            return

        # Species in order: grass, herbivore, predator, apex
        species = [
            (self.counts[GRASS], (30, 160, 40)),      # green
            (self.counts[HERBIVORE], COL_HERB),        # cyan
            (self.counts[PREDATOR], COL_PRED),         # orange
            (self.counts[APEX], COL_APEX),             # magenta
        ]

        x_pos = 0
        for count, color in species:
            if count == 0:
                continue
            # Proportional width, minimum 1px if population exists
            w = max(1, int(round(count / total * N)))
            # Don't overshoot the grid
            if x_pos + w > N:
                w = N - x_pos
            if w <= 0:
                break
            # Slightly dimmed for the bar so it doesn't overpower the scene
            dim_color = (color[0] * 3 // 4, color[1] * 3 // 4, color[2] * 3 // 4)
            for bx in range(x_pos, x_pos + w):
                self._px(bx, N - 2, dim_color)
                self._px(bx, N - 1, dim_color)
            x_pos += w

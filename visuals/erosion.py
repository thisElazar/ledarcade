"""
Erosion - Hydraulic Landscape
================================
Rain falls on procedural terrain, flows downhill, carves valleys and
rivers. Watch a river system emerge from nothing as water finds its
path through the landscape.

Controls:
  Left/Right  - Rainfall intensity
  Up/Down     - Rock type (hardness)
  Button      - New terrain
"""

import random, math
from . import Visual, Display, Colors, GRID_SIZE

RAIN_LEVELS = [
    (5,  'DRIZZLE'),
    (10, 'LIGHT RAIN'),
    (20, 'RAIN'),
    (35, 'DOWNPOUR'),
    (50, 'MONSOON'),
]

ROCK_TYPES = [
    (0.15, 'SAND'),
    (0.30, 'SOIL'),
    (0.50, 'ROCK'),
    (0.70, 'GRANITE'),
    (0.85, 'DIAMOND'),
]

TERRAIN_PRESETS = [
    'MOUNTAIN',
    'COASTAL',
    'VOLCANO',
    'PLATEAU',
    'CANYON',
]


class Erosion(Visual):
    name = "EROSION"
    description = "Hydraulic landscape"
    category = "nature"

    TERRAIN_COLORS = [
        (0.80, (200, 200, 200)),
        (0.60, (160, 140, 90)),
        (0.40, (80, 120, 50)),
        (0.20, (30, 80, 40)),
        (0.00, (20, 40, 80)),
    ]

    WATER_COLOR = (40, 100, 220)

    DEPOSIT_RATE = 0.3
    EVAPORATION = 0.01
    MAX_DROPLET_STEPS = 64
    MIN_CAPACITY = 0.01
    GRAVITY = 4.0
    FRICTION = 0.05
    INERTIA = 0.3

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.rain_idx = 2
        self.rock_idx = 2
        self.terrain_preset = 0

        self.height = None
        self.flow = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._generate_terrain()

        self.rain_particles = []
        self._init_rain_particles()

        self.update_timer = 0.0
        self.update_interval = 0.03
        self.overlay_timer = 2.5
        self.overlay_text = TERRAIN_PRESETS[self.terrain_preset]
        self.flat_check_timer = 0.0

    def _init_rain_particles(self):
        self.rain_particles = []
        count = RAIN_LEVELS[self.rain_idx][0]
        for _ in range(min(count, 40)):
            self.rain_particles.append([
                random.uniform(0, GRID_SIZE),
                random.uniform(-GRID_SIZE, GRID_SIZE),
                random.uniform(60, 100),
            ])

    # ------------------------------------------------------------------
    # Terrain generation
    # ------------------------------------------------------------------

    def _generate_terrain(self):
        self.height = self._diamond_square()
        preset = TERRAIN_PRESETS[self.terrain_preset]
        if preset == 'MOUNTAIN':
            self._add_ridge()
        elif preset == 'COASTAL':
            self._add_coastal()
        elif preset == 'VOLCANO':
            self._add_volcano()
        elif preset == 'PLATEAU':
            self._add_plateau()
        elif preset == 'CANYON':
            self._add_canyon()
        self.flow = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

    def _diamond_square(self):
        size = 65
        grid = [[0.0] * size for _ in range(size)]
        for cy in (0, size - 1):
            for cx in (0, size - 1):
                grid[cy][cx] = random.random()

        step = size - 1
        scale = 0.5
        while step > 1:
            half = step // 2
            for y in range(0, size - 1, step):
                for x in range(0, size - 1, step):
                    avg = (grid[y][x] + grid[y][x + step] +
                           grid[y + step][x] + grid[y + step][x + step]) / 4.0
                    grid[y + half][x + half] = avg + (random.random() - 0.5) * scale
            for y in range(0, size, half):
                x_start = half if (y // half) % 2 == 0 else 0
                for x in range(x_start, size, step):
                    total = 0.0
                    count = 0
                    if y >= half:
                        total += grid[y - half][x]
                        count += 1
                    if y + half < size:
                        total += grid[y + half][x]
                        count += 1
                    if x >= half:
                        total += grid[y][x - half]
                        count += 1
                    if x + half < size:
                        total += grid[y][x + half]
                        count += 1
                    grid[y][x] = total / count + (random.random() - 0.5) * scale
            step = half
            scale *= 0.5

        hmin = float('inf')
        hmax = float('-inf')
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                v = grid[y][x]
                if v < hmin:
                    hmin = v
                if v > hmax:
                    hmax = v
        rng = hmax - hmin if hmax > hmin else 1.0
        result = []
        for y in range(GRID_SIZE):
            row = []
            for x in range(GRID_SIZE):
                row.append((grid[y][x] - hmin) / rng)
            result.append(row)
        return result

    def _add_ridge(self):
        mid_y = GRID_SIZE // 2
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dy = abs(y - mid_y)
                ridge = 0.25 * math.exp(-(dy * dy) / 18.0)
                wave = 0.5 + 0.5 * math.sin(x * 0.3)
                self.height[y][x] = min(1.0, self.height[y][x] + ridge * wave)

    def _add_coastal(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                slope = x / GRID_SIZE
                shore = 0.3 + 0.1 * math.sin(y * 0.4)
                if slope < shore:
                    self.height[y][x] = 0.05 + self.height[y][x] * 0.1
                else:
                    cliff = min(1.0, (slope - shore) * 3.0)
                    self.height[y][x] = 0.1 + self.height[y][x] * 0.5 * cliff + cliff * 0.3

    def _add_volcano(self):
        cx, cy = GRID_SIZE // 2, GRID_SIZE // 2
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - cx
                dy = y - cy
                dist = math.sqrt(dx * dx + dy * dy)
                cone = max(0, 1.0 - dist / 28.0)
                crater = 0.0
                if dist < 5:
                    crater = 0.15 * (1.0 - dist / 5.0)
                self.height[y][x] = min(1.0, self.height[y][x] * 0.3 + cone * 0.7 - crater)

    def _add_plateau(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = abs(x - GRID_SIZE // 2) / (GRID_SIZE // 2)
                dy = abs(y - GRID_SIZE // 2) / (GRID_SIZE // 2)
                edge = max(dx, dy)
                if edge < 0.6:
                    self.height[y][x] = 0.6 + self.height[y][x] * 0.15
                else:
                    drop = (edge - 0.6) / 0.4
                    self.height[y][x] = max(0.1, 0.6 - drop * 0.5 + self.height[y][x] * 0.2)

    def _add_canyon(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.height[y][x] = 0.5 + self.height[y][x] * 0.3
                cx = GRID_SIZE // 2 + int(8 * math.sin(y * 0.15))
                dist = abs(x - cx)
                if dist < 6:
                    depth = (1.0 - dist / 6.0) * 0.45
                    self.height[y][x] = max(0.05, self.height[y][x] - depth)

    # ------------------------------------------------------------------
    # Hydraulic erosion
    # ------------------------------------------------------------------

    def _gradient(self, fx, fy):
        ix = int(fx)
        iy = int(fy)
        ix = max(0, min(ix, GRID_SIZE - 2))
        iy = max(0, min(iy, GRID_SIZE - 2))
        u = fx - ix
        v = fy - iy

        h = self.height
        h00 = h[iy][ix]
        h10 = h[iy][ix + 1]
        h01 = h[iy + 1][ix]
        h11 = h[iy + 1][ix + 1]

        gx = (h10 - h00) * (1.0 - v) + (h11 - h01) * v
        gy = (h01 - h00) * (1.0 - u) + (h11 - h10) * u

        height = h00 * (1.0 - u) * (1.0 - v) + h10 * u * (1.0 - v) + \
                 h01 * (1.0 - u) * v + h11 * u * v

        return gx, gy, height

    def _erode_droplet(self, start_x, start_y):
        px = float(start_x)
        py = float(start_y)
        dx = 0.0
        dy = 0.0
        speed = 1.0
        volume = 1.0
        sediment = 0.0
        h = self.height
        flow = self.flow
        size = GRID_SIZE
        inertia = self.INERTIA
        hardness = ROCK_TYPES[self.rock_idx][0]

        for _ in range(self.MAX_DROPLET_STEPS):
            ix = int(px)
            iy = int(py)
            if ix < 0 or ix >= size or iy < 0 or iy >= size:
                break

            flow[iy][ix] += 1.0

            gx, gy, old_h = self._gradient(px, py)

            dx = dx * inertia - gx * (1.0 - inertia)
            dy = dy * inertia - gy * (1.0 - inertia)

            dl = math.sqrt(dx * dx + dy * dy)
            if dl < 1e-6:
                angle = random.random() * 2.0 * math.pi
                dx = math.cos(angle)
                dy = math.sin(angle)
            else:
                dx /= dl
                dy /= dl

            new_px = px + dx
            new_py = py + dy

            if new_px < 0 or new_px >= size - 1 or new_py < 0 or new_py >= size - 1:
                break

            _, _, new_h = self._gradient(new_px, new_py)
            height_diff = new_h - old_h

            slope = max(-height_diff, 0.0)
            capacity = max(slope * speed * volume, self.MIN_CAPACITY)

            if sediment < capacity:
                amount = min((capacity - sediment) * (1.0 - hardness),
                             -height_diff if height_diff < 0 else capacity * 0.1)
                amount = max(0.0, amount)
                cix = max(0, min(ix, size - 1))
                ciy = max(0, min(iy, size - 1))
                h[ciy][cix] = max(0.0, h[ciy][cix] - amount)
                sediment += amount
            else:
                amount = self.DEPOSIT_RATE * (sediment - capacity)
                cix = max(0, min(ix, size - 1))
                ciy = max(0, min(iy, size - 1))
                h[ciy][cix] = min(1.0, h[ciy][cix] + amount)
                sediment -= amount

            speed = math.sqrt(max(0.0, speed * speed + height_diff * self.GRAVITY))
            speed *= (1.0 - self.FRICTION)
            speed = max(speed, 0.1)

            volume -= self.EVAPORATION
            if volume < 0.01:
                cix = int(new_px)
                ciy = int(new_py)
                if 0 <= cix < size and 0 <= ciy < size:
                    h[ciy][cix] = min(1.0, h[ciy][cix] + sediment)
                break

            px = new_px
            py = new_py

    def _run_erosion(self, count):
        size = GRID_SIZE
        for _ in range(count):
            x = random.random() * (size - 1)
            y = random.random() * (size - 1)
            self._erode_droplet(x, y)

    def _check_flatness(self):
        total = 0.0
        total_sq = 0.0
        n = GRID_SIZE * GRID_SIZE
        h = self.height
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                v = h[y][x]
                total += v
                total_sq += v * v
        mean = total / n
        var = total_sq / n - mean * mean
        std = math.sqrt(max(0.0, var))
        if std < 0.05:
            self.terrain_preset = (self.terrain_preset + 1) % len(TERRAIN_PRESETS)
            self._generate_terrain()
            self.overlay_text = TERRAIN_PRESETS[self.terrain_preset]
            self.overlay_timer = 2.5

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left_pressed:
            self.rain_idx = max(0, self.rain_idx - 1)
            self.overlay_timer = 2.0
            self.overlay_text = RAIN_LEVELS[self.rain_idx][1]
            self._init_rain_particles()
            consumed = True
        if input_state.right_pressed:
            self.rain_idx = min(len(RAIN_LEVELS) - 1, self.rain_idx + 1)
            self.overlay_timer = 2.0
            self.overlay_text = RAIN_LEVELS[self.rain_idx][1]
            self._init_rain_particles()
            consumed = True

        if input_state.up_pressed:
            self.rock_idx = min(len(ROCK_TYPES) - 1, self.rock_idx + 1)
            self.overlay_timer = 2.0
            self.overlay_text = ROCK_TYPES[self.rock_idx][1]
            consumed = True
        if input_state.down_pressed:
            self.rock_idx = max(0, self.rock_idx - 1)
            self.overlay_timer = 2.0
            self.overlay_text = ROCK_TYPES[self.rock_idx][1]
            consumed = True

        if input_state.action_l or input_state.action_r:
            self.terrain_preset = (self.terrain_preset + 1) % len(TERRAIN_PRESETS)
            self._generate_terrain()
            self.overlay_text = TERRAIN_PRESETS[self.terrain_preset]
            self.overlay_timer = 2.5
            consumed = True

        return consumed

    # ------------------------------------------------------------------
    # Update / Draw
    # ------------------------------------------------------------------

    def update(self, dt: float):
        self.time += dt

        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        self.update_timer += dt
        if self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            rainfall = RAIN_LEVELS[self.rain_idx][0]
            self._run_erosion(rainfall)

            for y in range(GRID_SIZE):
                row = self.flow[y]
                for x in range(GRID_SIZE):
                    row[x] *= 0.95

        # Rain particles
        for rp in self.rain_particles:
            rp[1] += rp[2] * dt
            rp[0] += 3.0 * dt
            if rp[1] > GRID_SIZE:
                rp[1] = random.uniform(-8, -1)
                rp[0] = random.uniform(0, GRID_SIZE)

        self.flat_check_timer += dt
        if self.flat_check_timer >= 5.0:
            self.flat_check_timer = 0.0
            self._check_flatness()

    def _terrain_color(self, h):
        for threshold, color in self.TERRAIN_COLORS:
            if h >= threshold:
                return color
        return self.TERRAIN_COLORS[-1][1]

    def draw(self):
        set_pixel = self.display.set_pixel
        h = self.height
        flow = self.flow
        wc = self.WATER_COLOR

        for y in range(GRID_SIZE):
            h_row = h[y]
            f_row = flow[y]
            for x in range(GRID_SIZE):
                hv = h_row[x]
                tr, tg, tb = self._terrain_color(hv)

                fv = f_row[x]
                if fv > 0.5:
                    blend = min(fv / 20.0, 0.8)
                    r = int(tr * (1.0 - blend) + wc[0] * blend)
                    g = int(tg * (1.0 - blend) + wc[1] * blend)
                    b = int(tb * (1.0 - blend) + wc[2] * blend)
                    set_pixel(x, y, (r, g, b))
                else:
                    set_pixel(x, y, (tr, tg, tb))

        # Rain particles
        for rp in self.rain_particles:
            ix, iy = int(rp[0]), int(rp[1])
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                set_pixel(ix, iy, (150, 180, 255))
            iy1 = iy - 1
            if 0 <= ix < GRID_SIZE and 0 <= iy1 < GRID_SIZE:
                set_pixel(ix, iy1, (100, 130, 220))

        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(200 * alpha))
            self.display.draw_text_small(2, 2, self.overlay_text, c)

"""
Erosion - Hydraulic Landscape
================================
Rain falls on procedural terrain, flows downhill, carves valleys and
rivers. Watch a river system emerge from nothing as water finds its
path through the landscape.

Controls:
  Left/Right  - Rainfall rate
  Up/Down     - Rock hardness
  Space       - Flood event
"""

import random, math
from . import Visual, Display, Colors, GRID_SIZE


class Erosion(Visual):
    name = "EROSION"
    description = "Hydraulic landscape"
    category = "nature"

    # Terrain color bands: (threshold, color)
    # Evaluated top-down; first threshold <= height wins
    TERRAIN_COLORS = [
        (0.80, (200, 200, 200)),  # peaks: light gray/white
        (0.60, (160, 140, 90)),   # high land: tan/brown
        (0.40, (80, 120, 50)),    # mid land: green-brown
        (0.20, (30, 80, 40)),     # low land: dark green
        (0.00, (20, 40, 80)),     # deep/valley: dark blue
    ]

    WATER_COLOR = (40, 100, 220)  # blue tint for flow overlay

    # Rainfall presets
    RAIN_MIN = 5
    RAIN_MAX = 50
    RAIN_DEFAULT = 15
    RAIN_STEP = 5

    # Hardness presets
    HARD_MIN = 0.1
    HARD_MAX = 0.9
    HARD_DEFAULT = 0.4
    HARD_STEP = 0.1

    # Erosion constants
    DEPOSIT_RATE = 0.3
    EVAPORATION = 0.01
    MAX_DROPLET_STEPS = 64
    MIN_CAPACITY = 0.01
    GRAVITY = 4.0
    FRICTION = 0.05
    INERTIA = 0.3  # blend between current dir and gradient dir

    FLOOD_COUNT = 500

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        # Parameters
        self.rainfall = self.RAIN_DEFAULT
        self.hardness = self.HARD_DEFAULT

        # Generate terrain
        self.height = self._diamond_square()
        self._add_ridge()

        # Water flow accumulation grid
        self.flow = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

        # Timing
        self.update_timer = 0.0
        self.update_interval = 0.03

        # Overlay
        self.overlay_timer = 0.0
        self.overlay_lines = []

        # Flatness check timer
        self.flat_check_timer = 0.0

    # ------------------------------------------------------------------
    # Terrain generation: diamond-square
    # ------------------------------------------------------------------

    def _diamond_square(self):
        """Generate a heightmap using diamond-square algorithm."""
        # Need power-of-2 + 1 size; we use 65 then crop to 64
        size = 65
        grid = [[0.0] * size for _ in range(size)]

        # Seed corners
        for cy in (0, size - 1):
            for cx in (0, size - 1):
                grid[cy][cx] = random.random()

        step = size - 1
        scale = 0.5

        while step > 1:
            half = step // 2

            # Diamond step
            for y in range(0, size - 1, step):
                for x in range(0, size - 1, step):
                    avg = (grid[y][x] + grid[y][x + step] +
                           grid[y + step][x] + grid[y + step][x + step]) / 4.0
                    grid[y + half][x + half] = avg + (random.random() - 0.5) * scale

            # Square step
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

        # Crop to GRID_SIZE and normalize to 0.0-1.0
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
        """Add a ridge line across the middle to create interesting drainage."""
        mid_y = GRID_SIZE // 2
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Gaussian ridge centered on mid_y
                dy = abs(y - mid_y)
                ridge = 0.25 * math.exp(-(dy * dy) / 18.0)
                # Vary ridge height along x for passes/gaps
                wave = 0.5 + 0.5 * math.sin(x * 0.3)
                self.height[y][x] = min(1.0, self.height[y][x] + ridge * wave)

    # ------------------------------------------------------------------
    # Hydraulic erosion
    # ------------------------------------------------------------------

    def _gradient(self, fx, fy):
        """Compute terrain gradient at fractional position (fx, fy).
        Returns (gx, gy, height) using bilinear interpolation."""
        ix = int(fx)
        iy = int(fy)
        # Clamp
        ix = max(0, min(ix, GRID_SIZE - 2))
        iy = max(0, min(iy, GRID_SIZE - 2))
        u = fx - ix
        v = fy - iy

        h = self.height
        h00 = h[iy][ix]
        h10 = h[iy][ix + 1]
        h01 = h[iy + 1][ix]
        h11 = h[iy + 1][ix + 1]

        # Gradient in x and y via bilinear
        gx = (h10 - h00) * (1.0 - v) + (h11 - h01) * v
        gy = (h01 - h00) * (1.0 - u) + (h11 - h10) * u

        # Interpolated height
        height = h00 * (1.0 - u) * (1.0 - v) + h10 * u * (1.0 - v) + \
                 h01 * (1.0 - u) * v + h11 * u * v

        return gx, gy, height

    def _erode_droplet(self, start_x, start_y):
        """Simulate a single water droplet."""
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

        for _ in range(self.MAX_DROPLET_STEPS):
            ix = int(px)
            iy = int(py)
            if ix < 0 or ix >= size or iy < 0 or iy >= size:
                break

            # Record flow
            flow[iy][ix] += 1.0

            # Get gradient
            gx, gy, old_h = self._gradient(px, py)

            # Blend direction with inertia
            dx = dx * inertia - gx * (1.0 - inertia)
            dy = dy * inertia - gy * (1.0 - inertia)

            # Normalize direction
            dl = math.sqrt(dx * dx + dy * dy)
            if dl < 1e-6:
                # Random direction if flat
                angle = random.random() * 2.0 * math.pi
                dx = math.cos(angle)
                dy = math.sin(angle)
            else:
                dx /= dl
                dy /= dl

            # Move
            new_px = px + dx
            new_py = py + dy

            # Check bounds
            if new_px < 0 or new_px >= size - 1 or new_py < 0 or new_py >= size - 1:
                break

            # New height
            _, _, new_h = self._gradient(new_px, new_py)
            height_diff = new_h - old_h

            # Carrying capacity
            slope = max(-height_diff, 0.0)
            capacity = max(slope * speed * volume, self.MIN_CAPACITY)

            if sediment < capacity:
                # Erode
                amount = min((capacity - sediment) * (1.0 - self.hardness),
                             -height_diff if height_diff < 0 else capacity * 0.1)
                amount = max(0.0, amount)
                # Lower terrain at old position
                cix = max(0, min(ix, size - 1))
                ciy = max(0, min(iy, size - 1))
                h[ciy][cix] = max(0.0, h[ciy][cix] - amount)
                sediment += amount
            else:
                # Deposit
                amount = self.DEPOSIT_RATE * (sediment - capacity)
                cix = max(0, min(ix, size - 1))
                ciy = max(0, min(iy, size - 1))
                h[ciy][cix] = min(1.0, h[ciy][cix] + amount)
                sediment -= amount

            # Update speed
            speed = math.sqrt(max(0.0, speed * speed + height_diff * self.GRAVITY))
            speed *= (1.0 - self.FRICTION)
            speed = max(speed, 0.1)

            # Evaporate
            volume -= self.EVAPORATION
            if volume < 0.01:
                # Deposit remaining sediment
                cix = int(new_px)
                ciy = int(new_py)
                if 0 <= cix < size and 0 <= ciy < size:
                    h[ciy][cix] = min(1.0, h[ciy][cix] + sediment)
                break

            px = new_px
            py = new_py

    def _run_erosion(self, count):
        """Run count droplets of rain."""
        size = GRID_SIZE
        for _ in range(count):
            x = random.random() * (size - 1)
            y = random.random() * (size - 1)
            self._erode_droplet(x, y)

    def _run_flood(self):
        """Flood event: many droplets from top edge."""
        size = GRID_SIZE
        for _ in range(self.FLOOD_COUNT):
            x = random.random() * (size - 1)
            self._erode_droplet(x, 0.0)

    def _check_flatness(self):
        """Check if terrain has become too flat; regenerate if so."""
        # Sample std dev
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
            self.height = self._diamond_square()
            self._add_ridge()
            self.flow = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: rainfall rate
        if input_state.left:
            self.rainfall = max(self.RAIN_MIN, self.rainfall - self.RAIN_STEP)
            self.overlay_timer = 2.0
            self.overlay_lines = [f"RAIN {self.rainfall}"]
            consumed = True
        if input_state.right:
            self.rainfall = min(self.RAIN_MAX, self.rainfall + self.RAIN_STEP)
            self.overlay_timer = 2.0
            self.overlay_lines = [f"RAIN {self.rainfall}"]
            consumed = True

        # Up/Down: rock hardness
        if input_state.up_pressed:
            self.hardness = min(self.HARD_MAX, round(self.hardness + self.HARD_STEP, 2))
            self.overlay_timer = 2.0
            self.overlay_lines = [f"HARD {self.hardness:.1f}"]
            consumed = True
        if input_state.down_pressed:
            self.hardness = max(self.HARD_MIN, round(self.hardness - self.HARD_STEP, 2))
            self.overlay_timer = 2.0
            self.overlay_lines = [f"HARD {self.hardness:.1f}"]
            consumed = True

        # Action: flood event
        if input_state.action_l or input_state.action_r:
            self._run_flood()
            self.overlay_timer = 2.0
            self.overlay_lines = ["FLOOD!"]
            consumed = True

        return consumed

    # ------------------------------------------------------------------
    # Update / Draw
    # ------------------------------------------------------------------

    def update(self, dt: float):
        self.time += dt

        # Overlay decay
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Erosion step
        self.update_timer += dt
        if self.update_timer >= self.update_interval:
            self.update_timer -= self.update_interval
            self._run_erosion(self.rainfall)

            # Decay flow grid
            for y in range(GRID_SIZE):
                row = self.flow[y]
                for x in range(GRID_SIZE):
                    row[x] *= 0.95

        # Periodic flatness check
        self.flat_check_timer += dt
        if self.flat_check_timer >= 5.0:
            self.flat_check_timer = 0.0
            self._check_flatness()

    def _terrain_color(self, h):
        """Return terrain color for height h (0.0 to 1.0)."""
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

                # Water flow tint
                fv = f_row[x]
                if fv > 0.5:
                    # Blend toward water color based on flow intensity
                    blend = min(fv / 20.0, 0.8)
                    r = int(tr * (1.0 - blend) + wc[0] * blend)
                    g = int(tg * (1.0 - blend) + wc[1] * blend)
                    b = int(tb * (1.0 - blend) + wc[2] * blend)
                    set_pixel(x, y, (r, g, b))
                else:
                    set_pixel(x, y, (tr, tg, tb))

        # HUD overlay
        if self.overlay_timer > 0 and self.overlay_lines:
            alpha = min(1.0, self.overlay_timer / 0.5)
            for i, line in enumerate(self.overlay_lines):
                cr = int(255 * alpha)
                cg = int(255 * alpha)
                cb = int(200 * alpha)
                self.display.draw_text_small(2, 2 + i * 8, line, (cr, cg, cb))

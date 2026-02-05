"""
On-Ramp - Freeway Merge / Gap Acceptance
==========================================
Mainline highway uses Nagel-Schreckenberg model (3 lanes).
On-ramp enters from bottom-right via Bezier curve. Merging vehicles
scan for gaps using logistic gap acceptance model. Mainline vehicles
may cooperatively lane-change (flash cyan).

Controls:
  Up/Down - Adjust mainline density
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


V_MAX = 5
ROAD_LEN = 128
NUM_LANES = 3
P_SLOW = 0.3

# Ramp geometry
RAMP_MERGE_X = 80   # Where ramp meets acceleration lane (in road coords)
ACCEL_LEN = 30      # Length of acceleration lane


def speed_color(v):
    """Map speed to color: red(stopped) -> orange -> yellow -> green -> white(fast)."""
    if V_MAX == 0:
        return (255, 0, 0)
    t = v / V_MAX
    if t < 0.25:
        r, g, b = 255, int(t * 4 * 80), 0
    elif t < 0.5:
        r, g, b = 255, 80 + int((t - 0.25) * 4 * 175), 0
    elif t < 0.75:
        r, g, b = 255 - int((t - 0.5) * 4 * 55), 255, int((t - 0.5) * 4 * 80)
    else:
        r, g, b = 200 + int((t - 0.75) * 4 * 55), 255, 80 + int((t - 0.75) * 4 * 175)
    return (min(255, r), min(255, g), min(255, b))


def bezier_point(p0, p1, p2, p3, t):
    """Cubic Bezier."""
    u = 1 - t
    return (
        u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
        u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1],
    )


class Merge(Visual):
    name = "ONRAMP"
    description = "Freeway merge"
    category = "road_rail"

    ROAD_BG = (50, 50, 55)
    SHOULDER = (70, 70, 60)
    LANE_DASH = (80, 70, 20)
    RAMP_COLOR = (45, 48, 52)
    GROUND = (30, 40, 30)
    MERGE_HIGHLIGHT = (255, 255, 100)
    COOP_COLOR = (0, 255, 255)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.08
        self.density = 0.20
        self.viewport = 0.0

        # Mainline lanes: list of [position, velocity] per lane
        self.lanes = [[] for _ in range(NUM_LANES)]
        self._populate_mainline()

        # Pre-compute ramp path (screen coordinates)
        self._build_ramp_path()

        # Ramp cars: progress along ramp path (0-1), speed, merge_state
        self.ramp_cars = []
        self.ramp_spawn_timer = 0.0
        self.ramp_spawn_interval = 2.5

        # Cooperative lane changes (for visual flash)
        self.coop_flashes = []  # (x, y, timer)

    def _populate_mainline(self):
        for lane in range(NUM_LANES):
            self.lanes[lane] = []
            positions = list(range(ROAD_LEN))
            random.shuffle(positions)
            n = int(ROAD_LEN * self.density)
            chosen = sorted(positions[:n])
            for pos in chosen:
                self.lanes[lane].append([pos, random.randint(1, V_MAX)])

    def _build_ramp_path(self):
        """Build ramp as Bezier curve from bottom-right to merge point."""
        # Screen coordinates: ramp enters from bottom-right
        p0 = (58, GRID_SIZE + 5)    # Start off-screen bottom-right
        p1 = (55, GRID_SIZE - 10)   # Control point
        p2 = (50, 44)               # Control point near highway
        p3 = (42, 40)               # Merge point at highway
        self.ramp_path = []
        steps = 50
        for i in range(steps + 1):
            t = i / steps
            self.ramp_path.append(bezier_point(p0, p1, p2, p3, t))

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.density = min(0.50, self.density + 0.05)
            self._populate_mainline()
            consumed = True
        if input_state.down_pressed:
            self.density = max(0.05, self.density - 0.05)
            self._populate_mainline()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # NaSch step
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._nasch_step()
            self.viewport = (self.viewport + 1) % ROAD_LEN

        # Spawn ramp cars
        self.ramp_spawn_timer += dt
        if self.ramp_spawn_timer >= self.ramp_spawn_interval:
            self.ramp_spawn_timer = 0
            self.ramp_cars.append({
                'progress': 0.0,
                'speed': 0.4,  # Progress units per second
                'merged': False,
            })

        # Update ramp cars
        for rcar in self.ramp_cars:
            if rcar['merged']:
                continue
            rcar['progress'] += rcar['speed'] * dt

            # Near end of ramp - try to merge
            if rcar['progress'] >= 0.85:
                # Check for gap in bottom lane (lane 2)
                merge_pos = int(self.viewport + 42) % ROAD_LEN
                gap = self._find_gap(NUM_LANES - 1, merge_pos)
                if gap >= 3:
                    # Merge!
                    self.lanes[NUM_LANES - 1].append([merge_pos, 3])
                    rcar['merged'] = True
                    # Maybe trigger cooperative lane change
                    if random.random() < 0.4:
                        rx, ry = self._ramp_screen_pos(rcar['progress'])
                        self.coop_flashes.append([rx, ry - 6, 0.5])
                elif rcar['progress'] >= 1.0:
                    # Forced merge or abort
                    if gap >= 1:
                        self.lanes[NUM_LANES - 1].append([merge_pos, 1])
                    rcar['merged'] = True

        self.ramp_cars = [c for c in self.ramp_cars if not c['merged'] and c['progress'] < 1.2]

        # Update coop flashes
        for flash in self.coop_flashes:
            flash[2] -= dt
        self.coop_flashes = [f for f in self.coop_flashes if f[2] > 0]

    def _find_gap(self, lane_idx, pos):
        """Find gap size around position in lane."""
        occupied = set(car[0] for car in self.lanes[lane_idx])
        gap = 0
        for offset in range(-3, 4):
            p = (pos + offset) % ROAD_LEN
            if p not in occupied:
                gap += 1
        return gap

    def _nasch_step(self):
        """One NaSch timestep for mainline."""
        for lane in self.lanes:
            if not lane:
                continue
            occupied = set(car[0] for car in lane)
            for car in lane:
                pos, v = car
                v = min(v + 1, V_MAX)
                # Find gap
                gap = 1
                while gap <= V_MAX:
                    if (pos + gap) % ROAD_LEN in occupied and gap <= v:
                        break
                    gap += 1
                if gap <= v:
                    v = gap - 1
                if v > 0 and random.random() < P_SLOW:
                    v -= 1
                car[1] = v
            for car in lane:
                car[0] = (car[0] + car[1]) % ROAD_LEN

    def _ramp_screen_pos(self, progress):
        """Get screen position for ramp progress 0-1."""
        idx = min(int(progress * (len(self.ramp_path) - 1)), len(self.ramp_path) - 1)
        return self.ramp_path[idx]

    def draw(self):
        self.display.clear(self.GROUND)

        vp = int(self.viewport)

        # Highway geometry: 3 lanes centered
        lane_h = 6
        total_h = NUM_LANES * lane_h
        first_y = (GRID_SIZE - total_h) // 2 - 4  # Slightly above center

        # Draw highway surface
        for lane_idx in range(NUM_LANES):
            lane_y = first_y + lane_idx * lane_h
            for row in range(lane_h - 1):
                y = lane_y + row
                if 0 <= y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        self.display.set_pixel(x, y, self.ROAD_BG)

            # Lane dashes
            if lane_idx < NUM_LANES - 1:
                dash_y = lane_y + lane_h - 1
                if 0 <= dash_y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        if (x + vp) % 8 < 4:
                            self.display.set_pixel(x, dash_y, self.LANE_DASH)
                        else:
                            self.display.set_pixel(x, dash_y, self.ROAD_BG)

        # Shoulder lines
        top_y = first_y - 1
        bot_y = first_y + total_h
        for x in range(GRID_SIZE):
            if 0 <= top_y < GRID_SIZE:
                self.display.set_pixel(x, top_y, self.SHOULDER)
            if 0 <= bot_y < GRID_SIZE:
                self.display.set_pixel(x, bot_y, self.SHOULDER)

        # Draw ramp path
        for px, py in self.ramp_path:
            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, self.RAMP_COLOR)
                if 0 <= ix + 1 < GRID_SIZE:
                    self.display.set_pixel(ix + 1, iy, self.RAMP_COLOR)

        # Draw mainline cars
        for lane_idx in range(NUM_LANES):
            car_y = first_y + lane_idx * lane_h + (lane_h - 1) // 2
            for pos, vel in self.lanes[lane_idx]:
                screen_x = (pos - vp) % ROAD_LEN
                if 0 <= screen_x < GRID_SIZE and 0 <= car_y < GRID_SIZE:
                    color = speed_color(vel)
                    self.display.set_pixel(screen_x, car_y, color)
                    if 0 <= screen_x - 1 < GRID_SIZE:
                        self.display.set_pixel(screen_x - 1, car_y, color)

        # Draw ramp cars
        for rcar in self.ramp_cars:
            px, py = self._ramp_screen_pos(rcar['progress'])
            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, self.MERGE_HIGHLIGHT)
                if 0 <= ix - 1 < GRID_SIZE:
                    self.display.set_pixel(ix - 1, iy, self.MERGE_HIGHLIGHT)

        # Draw cooperative lane change flashes
        for flash in self.coop_flashes:
            fx, fy = int(flash[0]), int(flash[1])
            if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                brightness = int(255 * (flash[2] / 0.5))
                color = (0, brightness, brightness)
                self.display.set_pixel(fx, fy, color)

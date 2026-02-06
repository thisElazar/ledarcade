"""
On-Ramp - Freeway Merge / Gap Acceptance
==========================================
Mainline highway uses Nagel-Schreckenberg model (3 lanes, 64 cells).
On-ramp enters from bottom-right via Bezier curve with an acceleration
lane that runs parallel to the highway. Merging vehicles scan for gaps.
Cooperative lane changes flash cyan.

Controls:
  Up/Down - Adjust mainline density
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


V_MAX = 5
ROAD_LEN = 64   # One screen width, wrapping
NUM_LANES = 3
P_SLOW = 0.3

# Highway vertical layout
LANE_H = 6
TOTAL_H = NUM_LANES * LANE_H
FIRST_Y = 14  # Top of first lane
# Lane centers: 14+2=16, 20+2=22, 26+2=28
# Bottom lane center = FIRST_Y + 2*LANE_H + (LANE_H-1)//2 = 14+12+2 = 28
BOT_LANE_Y = FIRST_Y + (NUM_LANES - 1) * LANE_H + (LANE_H - 1) // 2

# Merge point on the highway (screen x coordinate)
MERGE_X = 36

# Ramp path: Bezier from bottom-right up to acceleration lane, then straight
# to merge point
RAMP_ACCEL_Y = BOT_LANE_Y + LANE_H  # Acceleration lane just below bottom lane


def speed_color(v):
    """Map speed to color: red(stopped) -> orange -> yellow -> green -> white(fast)."""
    t = v / V_MAX if V_MAX > 0 else 0
    if t < 0.25:
        r, g, b = 255, int(t * 4 * 80), 0
    elif t < 0.5:
        r, g, b = 255, 80 + int((t - 0.25) * 4 * 175), 0
    elif t < 0.75:
        r, g, b = 255 - int((t - 0.5) * 4 * 55), 255, int((t - 0.5) * 4 * 80)
    else:
        r, g, b = 200 + int((t - 0.75) * 4 * 55), 255, 80 + int((t - 0.75) * 4 * 175)
    return (min(255, r), min(255, g), min(255, b))


def _bezier_pt(p0, p1, p2, p3, t):
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
    RAMP_COLOR = (48, 48, 53)
    GROUND = (30, 40, 30)
    ACCEL_COLOR = (50, 50, 55)
    MERGE_HIGHLIGHT = (255, 255, 100)
    COOP_COLOR = (0, 255, 255)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.08
        self.density = 0.20

        self.lanes = [[] for _ in range(NUM_LANES)]
        self._populate()

        self._build_ramp()

        self.ramp_cars = []
        self.ramp_spawn_timer = 0.0
        self.ramp_interval = 2.0

        self.coop_flashes = []

    def _populate(self):
        for lane in range(NUM_LANES):
            self.lanes[lane] = []
            positions = list(range(ROAD_LEN))
            random.shuffle(positions)
            n = int(ROAD_LEN * self.density)
            for pos in sorted(positions[:n]):
                self.lanes[lane].append([pos, random.randint(1, V_MAX)])

    def _build_ramp(self):
        """Build ramp path: Bezier curve from bottom-right to acceleration lane,
        then straight run parallel to highway, ending at merge point."""
        # Bezier: bottom-right corner up to start of accel lane
        p0 = (60, GRID_SIZE + 8)
        p1 = (58, GRID_SIZE - 8)
        p2 = (55, RAMP_ACCEL_Y + 4)
        p3 = (52, RAMP_ACCEL_Y)

        curve = []
        steps = 30
        for i in range(steps + 1):
            t = i / steps
            curve.append(_bezier_pt(p0, p1, p2, p3, t))

        # Acceleration lane: straight from (52, RAMP_ACCEL_Y) to (MERGE_X, RAMP_ACCEL_Y)
        accel = []
        for x in range(52, MERGE_X - 1, -1):
            accel.append((float(x), float(RAMP_ACCEL_Y)))

        # Final merge curve: from accel lane up into bottom highway lane
        merge_curve = []
        merge_steps = 8
        for i in range(merge_steps + 1):
            t = i / merge_steps
            x = MERGE_X - 1 - t * 4  # Move left a bit during merge
            y = RAMP_ACCEL_Y - t * (RAMP_ACCEL_Y - BOT_LANE_Y)
            merge_curve.append((x, y))

        self.ramp_path = curve + accel + merge_curve

        # Index where the accel lane starts (for merge logic)
        self.accel_start_idx = len(curve)
        # Index where the merge curve starts
        self.merge_start_idx = len(curve) + len(accel)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.density = min(0.50, self.density + 0.05)
            self._populate()
            consumed = True
        if input_state.down_pressed:
            self.density = max(0.05, self.density - 0.05)
            self._populate()
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # NaSch step
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._nasch_step()

        # Spawn ramp cars
        self.ramp_spawn_timer += dt
        if self.ramp_spawn_timer >= self.ramp_interval:
            self.ramp_spawn_timer = 0
            self.ramp_cars.append({
                'idx': 0.0,   # Float index into ramp_path
                'speed': 22.0,  # Points per second
                'merged': False,
                'waiting': False,
            })

        # Update ramp cars
        for rc in self.ramp_cars:
            if rc['merged']:
                continue

            # In acceleration lane or merge zone: check for gap
            if rc['idx'] >= self.merge_start_idx - 5:
                gap = self._find_gap(NUM_LANES - 1, MERGE_X)
                if gap >= 3:
                    # Merge successful
                    self.lanes[NUM_LANES - 1].append([MERGE_X, 3])
                    rc['merged'] = True
                    # Cooperative lane change flash
                    if random.random() < 0.4:
                        self.coop_flashes.append([MERGE_X - 3, BOT_LANE_Y - LANE_H, 0.6])
                    continue
                elif rc['idx'] >= len(self.ramp_path) - 3:
                    # Forced merge at end of accel lane
                    self.lanes[NUM_LANES - 1].append([MERGE_X, max(1, gap - 1)])
                    rc['merged'] = True
                    continue
                else:
                    rc['waiting'] = True
                    # Slow down in accel lane waiting for gap
                    rc['idx'] += rc['speed'] * dt * 0.3
            else:
                rc['waiting'] = False
                rc['idx'] += rc['speed'] * dt

        self.ramp_cars = [rc for rc in self.ramp_cars
                          if not rc['merged'] and rc['idx'] < len(self.ramp_path) + 5]

        # Update flashes
        for f in self.coop_flashes:
            f[2] -= dt
        self.coop_flashes = [f for f in self.coop_flashes if f[2] > 0]

    def _find_gap(self, lane_idx, pos):
        occupied = set(car[0] for car in self.lanes[lane_idx])
        gap = 0
        for offset in range(-3, 4):
            p = (pos + offset) % ROAD_LEN
            if p not in occupied:
                gap += 1
        return gap

    def _nasch_step(self):
        for lane in self.lanes:
            if not lane:
                continue
            occupied = set(car[0] for car in lane)
            for car in lane:
                pos, v = car
                v = min(v + 1, V_MAX)
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

    def _ramp_pos(self, rc):
        """Get screen position for a ramp car."""
        idx = max(0, min(rc['idx'], len(self.ramp_path) - 1))
        i = int(idx)
        if i >= len(self.ramp_path) - 1:
            return self.ramp_path[-1]
        frac = idx - i
        x0, y0 = self.ramp_path[i]
        x1, y1 = self.ramp_path[i + 1]
        return (x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)

    def draw(self):
        self.display.clear(self.GROUND)

        # Draw highway surface
        for lane_idx in range(NUM_LANES):
            lane_y = FIRST_Y + lane_idx * LANE_H
            for row in range(LANE_H - 1):
                y = lane_y + row
                if 0 <= y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        self.display.set_pixel(x, y, self.ROAD_BG)

            # Lane dashes between lanes
            if lane_idx < NUM_LANES - 1:
                dash_y = lane_y + LANE_H - 1
                if 0 <= dash_y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        if x % 8 < 4:
                            self.display.set_pixel(x, dash_y, self.LANE_DASH)
                        else:
                            self.display.set_pixel(x, dash_y, self.ROAD_BG)

        # Shoulder lines
        top_y = FIRST_Y - 1
        bot_y = FIRST_Y + TOTAL_H
        for x in range(GRID_SIZE):
            if 0 <= top_y < GRID_SIZE:
                self.display.set_pixel(x, top_y, self.SHOULDER)
            if 0 <= bot_y < GRID_SIZE:
                self.display.set_pixel(x, bot_y, self.SHOULDER)

        # Draw acceleration lane surface (just below bottom highway lane)
        # Only from ramp entry to merge point
        for x in range(MERGE_X - 2, 54):
            for dy in range(-1, 2):
                y = RAMP_ACCEL_Y + dy
                if 0 <= y < GRID_SIZE and 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, y, self.ACCEL_COLOR)

        # Draw ramp curve
        for px, py in self.ramp_path[:self.accel_start_idx]:
            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, self.RAMP_COLOR)
                if 0 <= ix - 1 < GRID_SIZE:
                    self.display.set_pixel(ix - 1, iy, self.RAMP_COLOR)

        # Draw mainline cars
        for lane_idx in range(NUM_LANES):
            car_y = FIRST_Y + lane_idx * LANE_H + (LANE_H - 1) // 2
            for pos, vel in self.lanes[lane_idx]:
                if 0 <= pos < GRID_SIZE and 0 <= car_y < GRID_SIZE:
                    color = speed_color(vel)
                    self.display.set_pixel(pos, car_y, color)
                    if 0 <= pos - 1 < GRID_SIZE:
                        self.display.set_pixel(pos - 1, car_y, color)

        # Draw ramp cars
        for rc in self.ramp_cars:
            if rc['merged']:
                continue
            px, py = self._ramp_pos(rc)
            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                color = self.MERGE_HIGHLIGHT
                if rc['waiting'] and int(self.time * 4) % 2 == 0:
                    color = (255, 180, 60)  # Dim when waiting
                self.display.set_pixel(ix, iy, color)
                if 0 <= ix - 1 < GRID_SIZE:
                    self.display.set_pixel(ix - 1, iy, color)

        # Draw cooperative lane change flashes
        for f in self.coop_flashes:
            fx, fy = int(f[0]), int(f[1])
            bright = int(255 * max(0, f[2] / 0.6))
            if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                self.display.set_pixel(fx, fy, (0, bright, bright))

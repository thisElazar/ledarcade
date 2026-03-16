"""
Highway - Nagel-Schreckenberg Traffic Model
=============================================
1D cellular automaton per lane. Each timestep:
  1. Accelerate: v = min(v+1, v_max)
  2. Brake:      v = min(v, gap-1)
  3. Random slow: with probability p, v = max(v-1, 0)
  4. Move:       position += v

Two modes (toggle with Space):
  FLOW  - 5-lane scrolling highway, phantom jams emerge naturally
  MERGE - 3-lane static highway with on-ramp, gap acceptance merging

Controls:
  Space      - Toggle mode
  Up/Down    - Adjust density
  Left/Right - Adjust randomization probability p
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


def speed_color(v, v_max):
    """Map speed to color: red(stopped) -> orange -> yellow -> green -> white(fast)."""
    if v_max == 0:
        return (255, 0, 0)
    t = v / v_max
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


class Highway(Visual):
    name = "HIGHWAY"
    description = "Nagel-Schreckenberg model"
    category = "road_rail"

    V_MAX = 5
    LANE_HEIGHT = 8

    ROAD_BG = (50, 50, 55)
    LANE_DASH = (80, 70, 20)
    SHOULDER = (70, 70, 60)
    RAMP_COLOR = (48, 48, 53)
    ACCEL_COLOR = (50, 50, 55)
    MERGE_HIGHLIGHT = (255, 255, 100)
    GROUND = (30, 40, 30)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.08
        self.density = 0.25
        self.p_slow = 0.3
        self.mode = 'flow'
        self._setup_mode()

    def _setup_mode(self):
        """Configure lanes and geometry for current mode."""
        if self.mode == 'flow':
            self.num_lanes = 5
            self.road_len = 256
        else:
            self.num_lanes = 3
            self.road_len = 64

        self.viewport = 0.0
        self.lanes = [[] for _ in range(self.num_lanes)]
        self._populate()

        # Merge mode extras
        self.ramp_cars = []
        self.ramp_spawn_timer = 0.0
        self.coop_flashes = []
        if self.mode == 'merge':
            self._build_ramp()

    def _populate(self):
        """Fill lanes at current density."""
        for lane_idx in range(self.num_lanes):
            self.lanes[lane_idx] = []
            positions = list(range(self.road_len))
            random.shuffle(positions)
            n_cars = int(self.road_len * self.density)
            chosen = sorted(positions[:n_cars])
            for pos in chosen:
                self.lanes[lane_idx].append([pos, random.randint(0, self.V_MAX)])

    # ------------------------------------------------------------------
    # Merge mode: ramp geometry
    # ------------------------------------------------------------------
    def _lane_geometry(self):
        """Compute vertical layout for current mode."""
        if self.mode == 'merge':
            first_y = 10  # Push up to make room for ramp below
        else:
            first_y = (GRID_SIZE - self.num_lanes * self.LANE_HEIGHT) // 2
        bot_lane_center = first_y + (self.num_lanes - 1) * self.LANE_HEIGHT + (self.LANE_HEIGHT - 1) // 2
        return first_y, bot_lane_center

    def _build_ramp(self):
        """Build on-ramp path: Bezier curve -> acceleration lane -> merge."""
        first_y, bot_lane_y = self._lane_geometry()
        accel_y = bot_lane_y + self.LANE_HEIGHT
        self._merge_x = 36
        self._accel_y = accel_y
        self._bot_lane_y = bot_lane_y

        # Bezier curve: bottom-right corner up to start of accel lane
        p0 = (60, GRID_SIZE + 8)
        p1 = (58, GRID_SIZE - 8)
        p2 = (55, accel_y + 4)
        p3 = (52, accel_y)

        curve = []
        for i in range(31):
            t = i / 30
            curve.append(_bezier_pt(p0, p1, p2, p3, t))

        # Acceleration lane: straight from (52, accel_y) to (merge_x, accel_y)
        accel = []
        for x in range(52, self._merge_x - 1, -1):
            accel.append((float(x), float(accel_y)))

        # Merge curve: from accel lane up into bottom highway lane
        merge_curve = []
        for i in range(9):
            t = i / 8
            x = self._merge_x - 1 - t * 4
            y = accel_y - t * (accel_y - bot_lane_y)
            merge_curve.append((x, y))

        self.ramp_path = curve + accel + merge_curve
        self._accel_start_idx = len(curve)
        self._merge_start_idx = len(curve) + len(accel)

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action_l or input_state.action_r:
            self.mode = 'merge' if self.mode == 'flow' else 'flow'
            self._setup_mode()
            consumed = True

        if input_state.up_pressed:
            self.density = min(0.60, self.density + 0.05)
            self._populate()
            consumed = True

        if input_state.down_pressed:
            self.density = max(0.05, self.density - 0.05)
            self._populate()
            consumed = True

        if input_state.right_pressed:
            self.p_slow = min(0.9, self.p_slow + 0.1)
            consumed = True

        if input_state.left_pressed:
            self.p_slow = max(0.0, self.p_slow - 0.1)
            consumed = True

        return consumed

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float):
        self.time += dt
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()
            # Scroll viewport in flow mode only
            if self.mode == 'flow':
                self.viewport = (self.viewport + 1) % self.road_len

        if self.mode == 'merge':
            self._update_ramp(dt)

    def _step(self):
        """One NaSch timestep for all lanes."""
        for lane in self.lanes:
            if not lane:
                continue
            occupied = set(car[0] for car in lane)

            for i in range(len(lane)):
                pos, v = lane[i]

                # 1. Accelerate
                v = min(v + 1, self.V_MAX)

                # 2. Brake: find gap to next car ahead
                gap = 1
                while gap <= self.V_MAX:
                    if (pos + gap) % self.road_len in occupied and gap <= v:
                        break
                    gap += 1
                if gap <= v:
                    v = gap - 1

                # 3. Random slow
                if v > 0 and random.random() < self.p_slow:
                    v -= 1

                lane[i][1] = v

            # 4. Move
            for car in lane:
                car[0] = (car[0] + car[1]) % self.road_len

    # ------------------------------------------------------------------
    # Merge mode: ramp update
    # ------------------------------------------------------------------
    def _update_ramp(self, dt):
        """Spawn and update on-ramp vehicles."""
        # Spawn ramp cars
        self.ramp_spawn_timer += dt
        if self.ramp_spawn_timer >= 2.0:
            self.ramp_spawn_timer = 0
            self.ramp_cars.append({
                'idx': 0.0,
                'speed': 22.0,
                'merged': False,
                'waiting': False,
            })

        # Update ramp cars
        for rc in self.ramp_cars:
            if rc['merged']:
                continue

            if rc['idx'] >= self._merge_start_idx - 5:
                gap = self._find_merge_gap()
                if gap >= 3:
                    self.lanes[self.num_lanes - 1].append([self._merge_x, 3])
                    rc['merged'] = True
                    if random.random() < 0.4:
                        self.coop_flashes.append([
                            self._merge_x - 3,
                            self._bot_lane_y - self.LANE_HEIGHT, 0.6
                        ])
                    continue
                elif rc['idx'] >= len(self.ramp_path) - 3:
                    self.lanes[self.num_lanes - 1].append([self._merge_x, max(1, gap - 1)])
                    rc['merged'] = True
                    continue
                else:
                    rc['waiting'] = True
                    rc['idx'] += rc['speed'] * dt * 0.3
            else:
                rc['waiting'] = False
                rc['idx'] += rc['speed'] * dt

        self.ramp_cars = [rc for rc in self.ramp_cars
                          if not rc['merged'] and rc['idx'] < len(self.ramp_path) + 5]

        # Coop flashes
        for f in self.coop_flashes:
            f[2] -= dt
        self.coop_flashes = [f for f in self.coop_flashes if f[2] > 0]

    def _find_merge_gap(self):
        """Find contiguous gap around merge position in bottom lane."""
        occupied = set(car[0] for car in self.lanes[self.num_lanes - 1])
        pos = self._merge_x
        if pos % self.road_len in occupied:
            return 0
        gap = 1
        for direction in (-1, 1):
            for step in range(1, 4):
                p = (pos + direction * step) % self.road_len
                if p in occupied:
                    break
                gap += 1
        return gap

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

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def draw(self):
        if self.mode == 'merge':
            self.display.clear(self.GROUND)
        else:
            self.display.clear((30, 30, 30))

        first_y, bot_lane_y = self._lane_geometry()
        vp = int(self.viewport)

        # Draw road surface + lane dashes + cars
        for lane_idx in range(self.num_lanes):
            lane_y = first_y + lane_idx * self.LANE_HEIGHT

            for row in range(self.LANE_HEIGHT - 1):
                y = lane_y + row
                if 0 <= y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        self.display.set_pixel(x, y, self.ROAD_BG)

            if lane_idx < self.num_lanes - 1:
                dash_y = lane_y + self.LANE_HEIGHT - 1
                if 0 <= dash_y < GRID_SIZE:
                    for x in range(GRID_SIZE):
                        if (x + vp) % 8 < 4:
                            self.display.set_pixel(x, dash_y, self.LANE_DASH)
                        else:
                            self.display.set_pixel(x, dash_y, self.ROAD_BG)

            car_y = lane_y + (self.LANE_HEIGHT - 1) // 2
            for pos, vel in self.lanes[lane_idx]:
                screen_x = (pos - vp) % self.road_len
                if 0 <= screen_x < GRID_SIZE and 0 <= car_y < GRID_SIZE:
                    color = speed_color(vel, self.V_MAX)
                    self.display.set_pixel(screen_x, car_y, color)
                    if 0 <= screen_x - 1 < GRID_SIZE:
                        self.display.set_pixel(screen_x - 1, car_y, color)

        # Shoulder lines
        top_shoulder = first_y - 1
        bot_shoulder = first_y + self.num_lanes * self.LANE_HEIGHT
        for x in range(GRID_SIZE):
            if 0 <= top_shoulder < GRID_SIZE:
                self.display.set_pixel(x, top_shoulder, self.SHOULDER)
            if self.mode == 'flow' and 0 <= bot_shoulder < GRID_SIZE:
                self.display.set_pixel(x, bot_shoulder, self.SHOULDER)

        # Merge mode: ramp geometry and vehicles
        if self.mode == 'merge':
            self._draw_ramp()

        # Mode label
        label = "FLOW" if self.mode == 'flow' else "MERGE"
        self.display.draw_text_small(2, 1, label, (120, 120, 120))

    def _draw_ramp(self):
        """Draw on-ramp infrastructure and vehicles."""
        # Acceleration lane surface
        for x in range(self._merge_x - 2, 54):
            for dy in range(-1, 2):
                y = self._accel_y + dy
                if 0 <= y < GRID_SIZE and 0 <= x < GRID_SIZE:
                    self.display.set_pixel(x, y, self.ACCEL_COLOR)

        # Bottom shoulder (below accel lane in merge mode)
        first_y, _ = self._lane_geometry()
        accel_bot = self._accel_y + 2
        for x in range(GRID_SIZE):
            if 0 <= accel_bot < GRID_SIZE:
                self.display.set_pixel(x, accel_bot, self.SHOULDER)

        # Ramp curve
        for px, py in self.ramp_path[:self._accel_start_idx]:
            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, self.RAMP_COLOR)
                if 0 <= ix - 1 < GRID_SIZE:
                    self.display.set_pixel(ix - 1, iy, self.RAMP_COLOR)

        # Ramp cars
        for rc in self.ramp_cars:
            if rc['merged']:
                continue
            px, py = self._ramp_pos(rc)
            ix, iy = int(px), int(py)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                color = self.MERGE_HIGHLIGHT
                if rc['waiting'] and int(self.time * 4) % 2 == 0:
                    color = (255, 180, 60)
                self.display.set_pixel(ix, iy, color)
                if 0 <= ix - 1 < GRID_SIZE:
                    self.display.set_pixel(ix - 1, iy, color)

        # Cooperative lane change flashes
        for f in self.coop_flashes:
            fx, fy = int(f[0]), int(f[1])
            bright = int(255 * max(0, f[2] / 0.6))
            if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
                self.display.set_pixel(fx, fy, (0, bright, bright))

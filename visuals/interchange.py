"""
Cloverleaf - Highway Interchanges
===================================
Pre-computed path geometry for three interchange types:
cloverleaf (loop ramps), diamond (diagonal ramps), turbine (sweeping curves).
Vehicles follow paths as colored dots. Auto-cycles between types.

Controls:
  Space    - Switch interchange type
  Up/Down  - Adjust traffic volume
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


CENTER = GRID_SIZE // 2


def bezier(p0, p1, p2, p3, t):
    """Cubic Bezier curve evaluation."""
    u = 1 - t
    return (
        u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0],
        u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1],
    )


def make_polyline(points, steps=40):
    """Sample a Bezier path into a polyline."""
    if len(points) == 4:
        return [bezier(points[0], points[1], points[2], points[3], t / steps) for t in range(steps + 1)]
    # Linear path
    result = []
    for i in range(len(points) - 1):
        for t in range(steps // (len(points) - 1) + 1):
            frac = t / (steps // (len(points) - 1))
            x = points[i][0] + (points[i+1][0] - points[i][0]) * frac
            y = points[i][1] + (points[i+1][1] - points[i][1]) * frac
            result.append((x, y))
    return result


class Interchange(Visual):
    name = "CLOVERLEAF"
    description = "Highway interchanges"
    category = "road_rail"

    TYPES = ['cloverleaf', 'diamond', 'turbine']

    HWY_COLOR = (55, 55, 60)
    RAMP_COLOR = (45, 45, 50)
    SHOULDER = (70, 70, 60)
    GROUND = (30, 45, 30)
    LANE_DASH = (80, 70, 20)

    CAR_COLORS = {
        'N': (255, 80, 80),
        'S': (80, 120, 255),
        'E': (80, 255, 80),
        'W': (255, 255, 80),
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.type_index = 0
        self.spawn_rate = 2.0
        self.spawn_timer = 0.0
        self.auto_timer = 0.0
        self.auto_interval = 18.0

        self.paths = {}
        self.road_pixels = set()
        self._build_paths()

        self.vehicles = []  # {path_key, progress, speed, color}

    def _build_paths(self):
        """Build paths for current interchange type."""
        self.paths = {}
        self.road_pixels = set()
        itype = self.TYPES[self.type_index]

        # Main highways (always present)
        # NS highway (vertical)
        for y in range(GRID_SIZE):
            for x in range(CENTER - 3, CENTER + 4):
                self.road_pixels.add((x, y))
        # EW highway (horizontal)
        for x in range(GRID_SIZE):
            for y in range(CENTER - 3, CENTER + 4):
                self.road_pixels.add((x, y))

        # Through paths
        self.paths['N_thru'] = [(CENTER + 2, GRID_SIZE + 2)] + [(CENTER + 2, y) for y in range(GRID_SIZE, -3, -1)]
        self.paths['S_thru'] = [(CENTER - 2, -3)] + [(CENTER - 2, y) for y in range(-2, GRID_SIZE + 3)]
        self.paths['E_thru'] = [(-3, CENTER + 2)] + [(x, CENTER + 2) for x in range(-2, GRID_SIZE + 3)]
        self.paths['W_thru'] = [(GRID_SIZE + 2, CENTER - 2)] + [(x, CENTER - 2) for x in range(GRID_SIZE + 1, -4, -1)]

        if itype == 'cloverleaf':
            self._build_cloverleaf_ramps()
        elif itype == 'diamond':
            self._build_diamond_ramps()
        else:
            self._build_turbine_ramps()

    def _build_cloverleaf_ramps(self):
        """Build cloverleaf loop ramp paths."""
        # Four loops in quadrants: NE, NW, SW, SE
        loop_r = 9
        offsets = [
            ('NE', CENTER + 6, CENTER - 6, 0),
            ('NW', CENTER - 6, CENTER - 6, math.pi / 2),
            ('SW', CENTER - 6, CENTER + 6, math.pi),
            ('SE', CENTER + 6, CENTER + 6, 3 * math.pi / 2),
        ]

        for name, cx, cy, start_angle in offsets:
            path = []
            steps = 40
            for i in range(steps + 1):
                angle = start_angle + (2 * math.pi * i / steps)
                x = cx + loop_r * math.cos(angle)
                y = cy + loop_r * math.sin(angle)
                path.append((x, y))
                ix, iy = int(x), int(y)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.road_pixels.add((ix, iy))
            self.paths[f'ramp_{name}'] = path

    def _build_diamond_ramps(self):
        """Build diamond interchange ramp paths."""
        # Four diagonal ramps connecting the highways
        ramp_len = 18
        ramp_configs = [
            ('NE', CENTER + 4, CENTER - 4, 1, -1),
            ('NW', CENTER - 4, CENTER - 4, -1, -1),
            ('SW', CENTER - 4, CENTER + 4, -1, 1),
            ('SE', CENTER + 4, CENTER + 4, 1, 1),
        ]

        for name, sx, sy, dx, dy in ramp_configs:
            path = []
            for i in range(ramp_len + 1):
                t = i / ramp_len
                x = sx + dx * t * 14
                y = sy + dy * t * 14
                path.append((x, y))
                ix, iy = int(x), int(y)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.road_pixels.add((ix, iy))
            self.paths[f'ramp_{name}'] = path

    def _build_turbine_ramps(self):
        """Build turbine interchange ramp paths (sweeping curves)."""
        # Four sweeping curves
        configs = [
            ('NE', math.pi, 3 * math.pi / 2),
            ('NW', 3 * math.pi / 2, 2 * math.pi),
            ('SW', 0, math.pi / 2),
            ('SE', math.pi / 2, math.pi),
        ]

        for name, start_a, end_a in configs:
            path = []
            steps = 35
            for i in range(steps + 1):
                t = i / steps
                angle = start_a + (end_a - start_a) * t
                r = 10 + 12 * t
                x = CENTER + r * math.cos(angle)
                y = CENTER + r * math.sin(angle)
                path.append((x, y))
                ix, iy = int(x), int(y)
                if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                    self.road_pixels.add((ix, iy))
            self.paths[f'ramp_{name}'] = path

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.action_l or input_state.action_r:
            self.type_index = (self.type_index + 1) % len(self.TYPES)
            self._build_paths()
            self.vehicles = []
            consumed = True
        if input_state.up_pressed:
            self.spawn_rate = min(6.0, self.spawn_rate + 0.5)
            consumed = True
        if input_state.down_pressed:
            self.spawn_rate = max(0.5, self.spawn_rate - 0.5)
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Auto-cycle type
        self.auto_timer += dt
        if self.auto_timer >= self.auto_interval:
            self.auto_timer = 0
            self.type_index = (self.type_index + 1) % len(self.TYPES)
            self._build_paths()
            self.vehicles = []

        # Spawn vehicles
        self.spawn_timer += dt
        if self.spawn_timer >= 1.0 / max(0.1, self.spawn_rate):
            self.spawn_timer = 0
            self._spawn_vehicle()

        # Update vehicles
        for v in self.vehicles:
            path = self.paths.get(v['path'])
            if path:
                v['progress'] += v['speed'] * dt
                if v['progress'] >= len(path) - 1:
                    v['done'] = True

        self.vehicles = [v for v in self.vehicles if not v.get('done')]

    def _spawn_vehicle(self):
        """Spawn a vehicle on a random path."""
        path_keys = list(self.paths.keys())
        if not path_keys:
            return
        key = random.choice(path_keys)
        # Determine direction for color
        if key.startswith('N'):
            color = self.CAR_COLORS['N']
        elif key.startswith('S'):
            color = self.CAR_COLORS['S']
        elif key.startswith('E'):
            color = self.CAR_COLORS['E']
        elif key.startswith('W'):
            color = self.CAR_COLORS['W']
        else:
            color = random.choice(list(self.CAR_COLORS.values()))

        self.vehicles.append({
            'path': key,
            'progress': 0.0,
            'speed': random.uniform(15, 25),
            'color': color,
        })

    def draw(self):
        self.display.clear(self.GROUND)

        # Draw all road pixels
        for x, y in self.road_pixels:
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, self.HWY_COLOR)

        # Lane dashes on main highways
        for y in range(GRID_SIZE):
            if CENTER - 3 <= y <= CENTER + 3:
                continue
            if y % 4 < 2:
                self.display.set_pixel(CENTER, y, self.LANE_DASH)
        for x in range(GRID_SIZE):
            if CENTER - 3 <= x <= CENTER + 3:
                continue
            if x % 4 < 2:
                self.display.set_pixel(x, CENTER, self.LANE_DASH)

        # Draw vehicles
        for v in self.vehicles:
            path = self.paths.get(v['path'])
            if not path:
                continue
            idx = min(int(v['progress']), len(path) - 1)
            x, y = path[idx]
            ix, iy = int(x), int(y)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, v['color'])

        # Type label
        label = self.TYPES[self.type_index].upper()[:8]
        self.display.draw_text_small(2, 1, label, (160, 160, 160))

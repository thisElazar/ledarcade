"""
Rotary - Roundabout with Gap Acceptance
=========================================
Vehicles approach from 4 directions, yield at entry by scanning
for gaps in circulating traffic, then follow a complete path through
the roundabout ring (CCW) and out the exit leg.

Controls:
  Up/Down - Adjust traffic volume
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


CX = 32
CY = 32
ISLAND_R = 8       # Central island radius
ROAD_R = 14        # Outer edge of circulatory road
RING_R = 11        # Center of ring road (where cars drive)
APPROACH_W = 6     # Approach road width

# Entry/exit angles in degrees (screen coords: 0=east, 90=south)
# In a roundabout, cars circulate CCW (in screen y-down, that means
# decreasing angle: right -> up -> left -> down)
LEGS = {
    'E': 0,
    'S': 90,
    'W': 180,
    'N': 270,
}
LEG_ORDER = ['E', 'S', 'W', 'N']

# Approach vectors (direction FROM which cars approach the roundabout)
APPROACH_VEC = {
    'E': (1, 0),    # Approach from east (going left toward center)
    'S': (0, 1),    # Approach from south (going up toward center)
    'W': (-1, 0),   # Approach from west (going right toward center)
    'N': (0, -1),   # Approach from north (going down toward center)
}


def _arc_pts(cx, cy, r, start_deg, sweep_deg, n=20):
    """Generate arc points. Negative sweep = CCW in screen coords."""
    pts = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(start_deg + sweep_deg * t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _lerp_pts(waypoints):
    """Densify waypoints to ~1px spacing."""
    pts = []
    for i in range(len(waypoints) - 1):
        x0, y0 = waypoints[i]
        x1, y1 = waypoints[i + 1]
        d = math.hypot(x1 - x0, y1 - y0)
        n = max(1, int(d * 1.5))
        for j in range(n):
            t = j / n
            pts.append((x0 + (x1 - x0) * t, y0 + (y1 - y0) * t))
    pts.append(waypoints[-1])
    return pts


class Roundabout(Visual):
    name = "ROTARY"
    description = "Roundabout gap acceptance"
    category = "road_rail"

    ISLAND_COLOR = (30, 70, 30)
    ROAD_COLOR = (55, 55, 60)
    CURB_COLOR = (90, 90, 80)
    APPROACH_COLOR = (50, 50, 55)
    GROUND = (35, 50, 35)
    YIELD_COLOR = (255, 255, 200)

    CAR_COLORS = [
        (255, 60, 60), (60, 120, 255), (255, 255, 80),
        (80, 255, 80), (255, 140, 60), (200, 80, 255),
        (255, 200, 200), (80, 255, 200),
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.spawn_rate = 1.5
        self.spawn_timer = 0.0

        # Pre-build all 12 origin-destination paths
        self._build_paths()

        # Vehicles: each has path, progress, speed, color, yield_idx, on_ring
        self.vehicles = []

    def _build_paths(self):
        """Build all 12 OD paths: 4 origins x 3 exits (no U-turns)."""
        self.paths = {}
        self.yield_indices = {}  # path_key -> index where ring arc starts

        for origin in LEG_ORDER:
            for dest in LEG_ORDER:
                if dest == origin:
                    continue
                key = f'{origin}_{dest}'
                path, yield_idx = self._make_od_path(origin, dest)
                self.paths[key] = path
                self.yield_indices[key] = yield_idx

    def _make_od_path(self, origin, dest):
        """Build a complete path: approach -> ring arc (CCW) -> departure."""
        origin_deg = LEGS[origin]
        dest_deg = LEGS[dest]

        # Approach: straight from screen edge to just outside the ring
        dvx, dvy = APPROACH_VEC[origin]
        # Start point: far from center along approach direction
        start = (CX + dvx * 34, CY + dvy * 34)
        # Yield point: just outside ring
        yield_pt = (CX + dvx * (ROAD_R + 2), CY + dvy * (ROAD_R + 2))
        # Ring entry point
        entry_a = math.radians(origin_deg)
        entry_pt = (CX + RING_R * math.cos(entry_a), CY + RING_R * math.sin(entry_a))

        approach = _lerp_pts([start, yield_pt, entry_pt])
        yield_idx = len(approach) - 1  # Last point of approach = ring entry

        # Ring arc (CCW = negative sweep in our coord system)
        # How far around the ring? CCW from origin to dest
        # CCW means decreasing angle in screen coords
        sweep = origin_deg - dest_deg
        if sweep <= 0:
            sweep += 360
        # Negative sweep for CCW direction
        ring_arc = _arc_pts(CX, CY, RING_R, origin_deg, -sweep, max(10, int(sweep / 6)))

        # Departure: from ring exit to screen edge
        exit_a = math.radians(dest_deg)
        exit_pt = (CX + RING_R * math.cos(exit_a), CY + RING_R * math.sin(exit_a))
        depart_outer = (CX + APPROACH_VEC[dest][0] * (ROAD_R + 2),
                        CY + APPROACH_VEC[dest][1] * (ROAD_R + 2))
        depart_end = (CX + APPROACH_VEC[dest][0] * 34,
                      CY + APPROACH_VEC[dest][1] * 34)
        departure = _lerp_pts([exit_pt, depart_outer, depart_end])

        # Combine (skip duplicate junction points)
        full = approach + ring_arc[1:] + departure[1:]
        return full, yield_idx

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.up_pressed:
            self.spawn_rate = min(4.0, self.spawn_rate + 0.3)
            consumed = True
        if input_state.down_pressed:
            self.spawn_rate = max(0.3, self.spawn_rate - 0.3)
            consumed = True
        return consumed

    def update(self, dt: float):
        self.time += dt

        # Spawn
        self.spawn_timer += dt
        if self.spawn_timer >= 1.0 / max(0.1, self.spawn_rate):
            self.spawn_timer = 0
            self._spawn()

        # Update vehicles
        for v in self.vehicles:
            path = self.paths[v['key']]
            yi = self.yield_indices[v['key']]

            # If approaching yield point, check gap
            if not v['past_yield'] and v['progress'] >= yi - 2:
                if self._gap_ok(v):
                    v['past_yield'] = True
                else:
                    # Stop near yield point
                    v['progress'] = min(v['progress'], float(yi - 1))
                    continue

            v['progress'] += v['speed'] * dt

        # Remove finished
        self.vehicles = [v for v in self.vehicles
                         if v['progress'] < len(self.paths[v['key']]) - 1]

    def _spawn(self):
        origin = random.choice(LEG_ORDER)
        dest_choices = [d for d in LEG_ORDER if d != origin]
        dest = random.choice(dest_choices)
        key = f'{origin}_{dest}'
        color = random.choice(self.CAR_COLORS)

        self.vehicles.append({
            'key': key,
            'progress': 0.0,
            'speed': random.uniform(16, 24),
            'color': color,
            'past_yield': False,
        })

    def _gap_ok(self, entering):
        """Check if there's room on the ring for this vehicle to enter."""
        yi = self.yield_indices[entering['key']]
        entry_path = self.paths[entering['key']]
        if yi >= len(entry_path):
            return True
        ex, ey = entry_path[yi]

        # Check all other vehicles that are ON the ring
        for other in self.vehicles:
            if other is entering:
                continue
            o_yi = self.yield_indices[other['key']]
            o_path = self.paths[other['key']]
            o_prog = other['progress']
            # Only check vehicles currently on the ring arc section
            ring_end = len(o_path) - self.yield_indices.get(other['key'], 0)
            if o_prog < o_yi or o_prog > len(o_path) - 10:
                continue
            # Get their position
            oi = int(min(o_prog, len(o_path) - 1))
            ox, oy = o_path[oi]
            dist = math.hypot(ox - ex, oy - ey)
            if dist < 6:
                return False
        return True

    def _vehicle_pos(self, v):
        path = self.paths[v['key']]
        i = int(min(v['progress'], len(path) - 1))
        frac = v['progress'] - i
        if i >= len(path) - 1:
            return path[-1]
        x0, y0 = path[i]
        x1, y1 = path[i + 1]
        return (x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)

    def draw(self):
        self.display.clear(self.GROUND)

        # Draw approach roads
        for leg, (dvx, dvy) in APPROACH_VEC.items():
            half = APPROACH_W // 2
            if dvx != 0:
                # Horizontal road
                sx = CX + (ROAD_R if dvx > 0 else -GRID_SIZE)
                ex = CX + (GRID_SIZE if dvx > 0 else -ROAD_R)
                for x in range(max(0, sx), min(GRID_SIZE, ex)):
                    for y in range(CY - half, CY + half):
                        if 0 <= y < GRID_SIZE:
                            self.display.set_pixel(x, y, self.APPROACH_COLOR)
            else:
                sy = CY + (ROAD_R if dvy > 0 else -GRID_SIZE)
                ey = CY + (GRID_SIZE if dvy > 0 else -ROAD_R)
                for y in range(max(0, sy), min(GRID_SIZE, ey)):
                    for x in range(CX - half, CX + half):
                        if 0 <= x < GRID_SIZE:
                            self.display.set_pixel(x, y, self.APPROACH_COLOR)

        # Draw circulatory road
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CX
                dy = y - CY
                dist = math.sqrt(dx * dx + dy * dy)
                if ISLAND_R < dist <= ROAD_R:
                    self.display.set_pixel(x, y, self.ROAD_COLOR)
                elif abs(dist - ISLAND_R) < 0.8 or abs(dist - ROAD_R) < 0.8:
                    self.display.set_pixel(x, y, self.CURB_COLOR)

        # Central island
        for y in range(CY - ISLAND_R, CY + ISLAND_R + 1):
            for x in range(CX - ISLAND_R, CX + ISLAND_R + 1):
                if (x - CX)**2 + (y - CY)**2 <= ISLAND_R * ISLAND_R:
                    if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                        self.display.set_pixel(x, y, self.ISLAND_COLOR)

        # Yield markers
        for leg in LEG_ORDER:
            deg = LEGS[leg]
            a = math.radians(deg)
            yx = int(CX + (ROAD_R + 1) * math.cos(a))
            yy = int(CY + (ROAD_R + 1) * math.sin(a))
            if 0 <= yx < GRID_SIZE and 0 <= yy < GRID_SIZE:
                self.display.set_pixel(yx, yy, self.YIELD_COLOR)

        # Draw vehicles
        for v in self.vehicles:
            x, y = self._vehicle_pos(v)
            ix, iy = int(x), int(y)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                color = v['color']
                # Flash yellow if waiting at yield
                if not v['past_yield'] and v['progress'] >= self.yield_indices[v['key']] - 2:
                    if int(self.time * 4) % 2 == 0:
                        color = (255, 200, 100)
                self.display.set_pixel(ix, iy, color)

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
ISLAND_R = 7       # Central island radius
ROAD_R = 15        # Outer edge of circulatory road
RING_R_OUT = 13    # Outer circulating lane (where cars drive)
RING_R_IN = 10     # Inner circulating lane
LANE_DIV_R = 11.5  # Divider between the two ring lanes
APPROACH_W = 6     # Approach road width (two lanes)
LANE_OFF = 1.5     # Perpendicular offset of each approach/exit lane
ENTRY_EXIT_SPLIT = 14   # Degrees the entry gore sits downstream of the exit gore

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
    GUIDE = {
        'desc': 'A traffic roundabout with entering and circulating vehicles. Yield-on-entry dynamics create a self-regulating flow. The European alternative to the four-way stop.',
    }

    ISLAND_COLOR = (30, 70, 30)
    ROAD_COLOR = (55, 55, 60)
    CURB_COLOR = (90, 90, 80)
    APPROACH_COLOR = (50, 50, 55)
    GROUND = (35, 50, 35)
    YIELD_COLOR = (255, 255, 200)
    LANE_DASH = (70, 65, 30)

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
        """Build all OD paths: 4 origins x 3 exits x 2 lanes (no U-turns)."""
        self.paths = {}
        self.yield_indices = {}  # path_key -> index where ring arc starts
        self.path_ring_r = {}    # path_key -> circulating radius (its lane)

        for origin in LEG_ORDER:
            for dest in LEG_ORDER:
                if dest == origin:
                    continue
                for lane, ring_r in ((0, RING_R_OUT), (1, RING_R_IN)):
                    key = f'{origin}_{dest}_{lane}'
                    path, yield_idx = self._make_od_path(origin, dest, ring_r, lane)
                    self.paths[key] = path
                    self.yield_indices[key] = yield_idx
                    self.path_ring_r[key] = ring_r

    def _make_od_path(self, origin, dest, ring_r, lane):
        """Build a complete path: approach -> ring arc (CCW) -> departure.

        ``lane`` 0 = outer, 1 = inner; the lane is realised purely by the
        circulating radius ``ring_r``. Each leg is a two-way road: inbound
        traffic uses one side, outbound the other (drive-on-right), so an
        arriving car and a departing car never share a line head-on.
        """
        origin_deg = LEGS[origin]
        dest_deg = LEGS[dest]

        # Approach (inbound side of the origin leg) -> this lane's ring radius.
        # Drive-on-the-right (North America): inbound keeps to the right of its
        # travel direction. Inbound travels toward the centre (-dv), so its
        # right-hand side is the perpendicular (dvy, -dvx).
        dvx, dvy = APPROACH_VEC[origin]
        ix, iy = dvy * LANE_OFF, -dvx * LANE_OFF        # inbound lane (right side)
        start = (CX + dvx * 34 + ix, CY + dvy * 34 + iy)
        yield_pt = (CX + dvx * (ROAD_R + 2) + ix, CY + dvy * (ROAD_R + 2) + iy)
        # Splitter-island geometry: a leg's entry joins the ring DOWNSTREAM
        # (CCW = decreasing angle) of where its exit leaves, so merging and
        # diverging traffic never meet at the same gore point.
        entry_deg = origin_deg - ENTRY_EXIT_SPLIT
        entry_a = math.radians(entry_deg)
        entry_pt = (CX + ring_r * math.cos(entry_a), CY + ring_r * math.sin(entry_a))

        # The yield line sits at ``yield_pt``, OUTSIDE the ring, so a car
        # waiting for a gap holds clear of the circulating lane rather than
        # stopping on top of it. The short merge segment then leads onto the
        # ring once the car accepts a gap.
        to_yield = _lerp_pts([start, yield_pt])
        merge = _lerp_pts([yield_pt, entry_pt])
        approach = to_yield + merge[1:]
        yield_idx = len(to_yield) - 1  # Index of the yield point (off the ring)

        # Ring arc (CCW = negative sweep in our coord system), from this lane's
        # entry gore round to its exit gore.
        exit_deg = dest_deg + ENTRY_EXIT_SPLIT
        sweep = (entry_deg - exit_deg) % 360
        if sweep <= 0:
            sweep += 360
        ring_arc = _arc_pts(CX, CY, ring_r, entry_deg, -sweep, max(8, int(sweep / 6)))

        # Departure (outbound side of the dest leg) -> screen edge. Outbound
        # travels away from centre (+dv), so its right-hand side is (-dvy, dvx)
        # — the opposite side of the road from the inbound lane.
        exit_a = math.radians(exit_deg)
        exit_pt = (CX + ring_r * math.cos(exit_a), CY + ring_r * math.sin(exit_a))
        ddvx, ddvy = APPROACH_VEC[dest]
        ox, oy = -ddvy * LANE_OFF, ddvx * LANE_OFF      # outbound lane (right side)
        depart_outer = (CX + ddvx * (ROAD_R + 2) + ox, CY + ddvy * (ROAD_R + 2) + oy)
        depart_end = (CX + ddvx * 34 + ox, CY + ddvy * 34 + oy)
        departure = _lerp_pts([exit_pt, depart_outer, depart_end])

        # Combine (skip duplicate junction points)
        full = approach + ring_arc[1:] + departure[1:]
        return full, yield_idx

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.right_pressed:
            self.spawn_rate = min(4.0, self.spawn_rate + 0.3)
            consumed = True
        if input_state.left_pressed:
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

            # Following distance: slow/stop if any vehicle ahead is too close
            if self._too_close(v):
                continue

            v['progress'] += v['speed'] * dt

        # Remove finished
        self.vehicles = [v for v in self.vehicles
                         if v['progress'] < len(self.paths[v['key']]) - 1]

    def _spawn(self):
        origin = random.choice(LEG_ORDER)
        dest_choices = [d for d in LEG_ORDER if d != origin]
        dest = random.choice(dest_choices)

        # North American lane discipline by how far around the car travels
        # (CCW): first exit (right turn) keeps the outer lane, the third exit
        # (left turn) takes the inner lane, a through movement may use either.
        sweep = (LEGS[origin] - LEGS[dest]) % 360
        if sweep <= 90:
            lane = 0           # right turn -> outer
        elif sweep >= 270:
            lane = 1           # left turn  -> inner
        else:
            lane = random.choice((0, 1))   # through -> either
        key = f'{origin}_{dest}_{lane}'

        # Don't spawn if another vehicle on the same approach lane is near the
        # start, or if the sibling lane on this leg is occupied at its start
        # (the two approach lanes are only ~3px apart at the screen edge).
        for other in self.vehicles:
            if other['progress'] < 10 and other['key'].startswith(f'{origin}_'):
                ox, oy = self._vehicle_pos(other)
                sx, sy = self._vehicle_pos({'key': key, 'progress': 0.0})
                if math.hypot(ox - sx, oy - sy) < 4:
                    return

        color = random.choice(self.CAR_COLORS)
        self.vehicles.append({
            'key': key,
            'progress': 0.0,
            'speed': random.uniform(16, 24),
            'color': color,
            'past_yield': False,
            'lane': lane,
            'ring_r': self.path_ring_r[key],
        })

    def _gap_ok(self, entering):
        """Gap acceptance: enter only when this car's target ring lane has a
        real gap. Reject if a circulating car sits on the entry point or is
        approaching it from upstream — and, for the inner lane, if either is
        true of the outer lane it must cross. Metering entry this way keeps the
        ring below jam density, so circulation never gridlocks."""
        enter_r = entering['ring_r']
        origin = entering['key'].split('_')[0]
        a_entry = math.radians(LEGS[origin] - ENTRY_EXIT_SPLIT)
        ex = CX + enter_r * math.cos(a_entry)
        ey = CY + enter_r * math.sin(a_entry)
        crit_ang = 11.0 / enter_r         # ~11px of upstream clearance on the ring

        for other in self.vehicles:
            if other is entering or not other['past_yield']:
                continue
            ox, oy = self._vehicle_pos(other)
            orr = math.hypot(ox - CX, oy - CY)
            if orr > ROAD_R + 1:          # already leaving the ring outward
                continue
            # Conflicts come from my own lane and any lane outside it that I
            # cross on the way in; a car strictly inside my radius can't block.
            if orr < enter_r - 1.5:
                continue
            # Keep a clear merge zone right around the entry point (a car just
            # downstream as well as one sitting on it) so the entering car
            # never materialises on top of circulating traffic.
            if math.hypot(ox - ex, oy - ey) < 6.0:
                return False
            # Approaching from upstream (CCW circulates with decreasing angle,
            # so an upstream car sits at a slightly larger angle than entry)?
            oa = math.atan2(oy - CY, ox - CX)
            if (oa - a_entry) % (2 * math.pi) < crit_ang:
                return False
        return True

    def _heading(self, v):
        """Unit vector of the vehicle's current direction of travel."""
        path = self.paths[v['key']]
        i = int(min(v['progress'], len(path) - 2))
        x0, y0 = path[i]
        x1, y1 = path[i + 1]
        dx, dy = x1 - x0, y1 - y0
        d = math.hypot(dx, dy) or 1.0
        return dx / d, dy / d

    def _too_close(self, v):
        """Decide whether vehicle ``v`` must hold position this frame.

        Two distinct rules, chosen to prevent both rear-end overlaps and the
        circular gridlock a fully rigid ring would suffer:

        * Same path: a forward cone (directly ahead, narrow laterally) gives
          firm car-following. Same-path chains always lead to an exit, so they
          drain and never lock.
        * Different path (merges, lane crossings): non-blocking priority — yield
          only to a conflicting car that is further along the ring. The
          higher-priority car keeps moving, so no closed rigid loop can form.
        """
        vx, vy = self._vehicle_pos(v)
        hx, hy = self._heading(v)
        v_ring = v['progress'] - self.yield_indices[v['key']]
        v_circ = math.hypot(vx - CX, vy - CY) <= ROAD_R + 0.5

        for other in self.vehicles:
            if other is v:
                continue
            ox, oy = self._vehicle_pos(other)
            rx, ry = ox - vx, oy - vy
            both_circ = v_circ and math.hypot(ox - CX, oy - CY) <= ROAD_R + 0.5
            same_lane = abs(v['ring_r'] - other['ring_r']) < 1.5

            if both_circ and other['key'] != v['key']:
                # Two different paths both circulating the ring (merges and
                # lane crossings): non-blocking priority — yield only to a
                # nearby car already further round the ring. The higher-priority
                # car keeps moving, so no rigid loop (gridlock) can form.
                if math.hypot(rx, ry) < (4.0 if same_lane else 2.2):
                    o_ring = other['progress'] - self.yield_indices[other['key']]
                    if o_ring > v_ring:
                        return True
            else:
                # Same path, or a car on the approach/exit legs (which queue
                # two ring-lanes into one inbound/outbound lane): firm
                # car-following on whoever is directly ahead in my lane. These
                # cases are linear and can never form a circular deadlock.
                ahead = rx * hx + ry * hy
                lateral = abs(rx * -hy + ry * hx)
                if 0 < ahead < 4.5 and lateral < 1.6:
                    return True
        return False

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

        # Dashed lane divider down the centre of each approach road
        for leg, (dvx, dvy) in APPROACH_VEC.items():
            if dvx != 0:
                rng = range(CX + ROAD_R, GRID_SIZE) if dvx > 0 else range(0, CX - ROAD_R)
                for x in rng:
                    if x % 4 < 2:
                        self.display.set_pixel(x, CY, self.LANE_DASH)
            else:
                rng = range(CY + ROAD_R, GRID_SIZE) if dvy > 0 else range(0, CY - ROAD_R)
                for y in rng:
                    if y % 4 < 2:
                        self.display.set_pixel(CX, y, self.LANE_DASH)

        # Draw circulatory road
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                dx = x - CX
                dy = y - CY
                dist = math.sqrt(dx * dx + dy * dy)
                if ISLAND_R < dist <= ROAD_R:
                    self.display.set_pixel(x, y, self.ROAD_COLOR)
                    # Dashed divider between the inner and outer ring lanes
                    if abs(dist - LANE_DIV_R) < 0.6:
                        ang = math.degrees(math.atan2(dy, dx))
                        if int(ang) % 24 < 12:
                            self.display.set_pixel(x, y, self.LANE_DASH)
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

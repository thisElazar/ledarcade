"""
Cloverleaf - Highway Interchanges
===================================
Pre-computed path geometry for three interchange types:
cloverleaf (270-degree loop ramps), diamond (diagonal ramps),
turbine (sweeping Bezier curves). Vehicles follow complete
origin-to-destination paths. Auto-cycles between types.

Controls:
  Space    - Switch interchange type
  Up/Down  - Adjust traffic volume
"""

import math
import random
from . import Visual, Display, Colors, GRID_SIZE


CENTER = GRID_SIZE // 2  # 32

# Highway lane centers (driving on right)
# NB (going up): east side = x=33, SB (going down): west side = x=31
# EB (going right): south side = y=33, WB (going left): north side = y=31
NB_X = 33
SB_X = 31
EB_Y = 33
WB_Y = 31


def _densify(waypoints):
    """Interpolate waypoints into ~1px-apart path points."""
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


def _arc(cx, cy, r, start_deg, sweep_deg, n=30):
    """Arc points. Positive sweep = CW in screen coords (y-down)."""
    pts = []
    for i in range(n + 1):
        t = i / n
        a = math.radians(start_deg + sweep_deg * t)
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    return pts


def _bezier(p0, p1, p2, p3, n=40):
    """Cubic Bezier curve points."""
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = u*u*u*p0[0] + 3*u*u*t*p1[0] + 3*u*t*t*p2[0] + t*t*t*p3[0]
        y = u*u*u*p0[1] + 3*u*u*t*p1[1] + 3*u*t*t*p2[1] + t*t*t*p3[1]
        pts.append((x, y))
    return pts


class Interchange(Visual):
    name = "CLOVERLEAF"
    description = "Highway interchanges"
    category = "road_rail"

    TYPES = ['cloverleaf', 'diamond', 'turbine']

    HWY_COLOR = (55, 55, 60)
    RAMP_COLOR = (48, 48, 53)
    SHOULDER = (70, 70, 60)
    GROUND = (30, 45, 30)
    LANE_DASH = (80, 70, 20)

    # Color by origin direction
    DIR_COLORS = {
        'NB': (255, 80, 80),
        'SB': (80, 120, 255),
        'EB': (80, 255, 80),
        'WB': (255, 255, 80),
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.type_index = 0
        self.spawn_rate = 2.5
        self.spawn_timer = 0.0
        self.auto_timer = 0.0
        self.auto_interval = 18.0
        self.vehicles = []
        self._build()

    def _build(self):
        """Build road geometry and vehicle paths for current type."""
        self.road_pixels = set()
        self.paths = {}

        # Main highways (6px wide: x/y 29-34)
        for y in range(GRID_SIZE):
            for x in range(29, 35):
                self.road_pixels.add((x, y))
        for x in range(GRID_SIZE):
            for y in range(29, 35):
                self.road_pixels.add((x, y))

        # Through paths (always available)
        self.paths['NB_thru'] = _densify([(NB_X, 66), (NB_X, -3)])
        self.paths['SB_thru'] = _densify([(SB_X, -3), (SB_X, 66)])
        self.paths['EB_thru'] = _densify([(-3, EB_Y), (66, EB_Y)])
        self.paths['WB_thru'] = _densify([(66, WB_Y), (-3, WB_Y)])

        builders = {
            'cloverleaf': self._build_cloverleaf,
            'diamond': self._build_diamond,
            'turbine': self._build_turbine,
        }
        builders[self.TYPES[self.type_index]]()

    def _paint_path(self, pts, thickness=1):
        """Add path pixels to road surface."""
        for x, y in pts:
            for dx in range(-thickness, thickness + 1):
                for dy in range(-thickness, thickness + 1):
                    ix, iy = int(x + dx), int(y + dy)
                    if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                        self.road_pixels.add((ix, iy))

    # ------------------------------------------------------------------
    # Cloverleaf: four 270-degree loop ramps for left turns
    # ------------------------------------------------------------------
    def _build_cloverleaf(self):
        LOOP_R = 7
        # NE loop (NB->WB): center (42, 22)
        # Entry at 180deg = (35,22) heading UP; exit at 90deg = (42,29) heading LEFT
        ne_arc = _arc(42, 22, LOOP_R, 180, 270, 30)
        self._paint_path(ne_arc, 1)
        ne_wp = ([(NB_X, 66), (NB_X, 26), (34, 24), (35, 22)]
                 + ne_arc
                 + [(42, 29), (40, 30), (38, WB_Y), (-3, WB_Y)])
        self.paths['NB_WB'] = _densify(ne_wp)

        # SE loop (EB->NB): center (42, 42)
        # Entry at 270deg = (42,35) heading RIGHT; exit at 180deg = (35,42) heading UP
        se_arc = _arc(42, 42, LOOP_R, 270, 270, 30)
        self._paint_path(se_arc, 1)
        se_wp = ([(-3, EB_Y), (36, EB_Y), (40, 34), (42, 35)]
                 + se_arc
                 + [(35, 42), (34, 40), (NB_X, 38), (NB_X, -3)])
        self.paths['EB_NB'] = _densify(se_wp)

        # SW loop (SB->EB): center (22, 42)
        # Entry at 0deg = (29,42) heading DOWN; exit at 270deg = (22,35) heading RIGHT
        sw_arc = _arc(22, 42, LOOP_R, 0, 270, 30)
        self._paint_path(sw_arc, 1)
        sw_wp = ([(SB_X, -3), (SB_X, 38), (30, 40), (29, 42)]
                 + sw_arc
                 + [(22, 35), (24, 34), (26, EB_Y), (66, EB_Y)])
        self.paths['SB_EB'] = _densify(sw_wp)

        # NW loop (WB->SB): center (22, 22)
        # Entry at 90deg = (22,29) heading LEFT; exit at 0deg = (29,22) heading DOWN
        nw_arc = _arc(22, 22, LOOP_R, 90, 270, 30)
        self._paint_path(nw_arc, 1)
        nw_wp = ([(66, WB_Y), (28, WB_Y), (24, 30), (22, 29)]
                 + nw_arc
                 + [(29, 22), (30, 24), (SB_X, 26), (SB_X, 66)])
        self.paths['WB_SB'] = _densify(nw_wp)

    # ------------------------------------------------------------------
    # Diamond: four short diagonal ramps
    # ------------------------------------------------------------------
    def _build_diamond(self):
        # NE ramp (NB->WB via diagonal)
        ne_wp = [(NB_X, 66), (NB_X, 27), (36, 25), (40, WB_Y), (-3, WB_Y)]
        ne_pts = _densify(ne_wp)
        self._paint_path(ne_pts, 1)
        self.paths['NB_WB'] = ne_pts

        # SE ramp (EB->NB via diagonal)
        se_wp = [(-3, EB_Y), (37, EB_Y), (39, 36), (NB_X, 39), (NB_X, -3)]
        se_pts = _densify(se_wp)
        self._paint_path(se_pts, 1)
        self.paths['EB_NB'] = se_pts

        # SW ramp (SB->EB via diagonal)
        sw_wp = [(SB_X, -3), (SB_X, 37), (28, 39), (24, EB_Y), (66, EB_Y)]
        sw_pts = _densify(sw_wp)
        self._paint_path(sw_pts, 1)
        self.paths['SB_EB'] = sw_pts

        # NW ramp (WB->SB via diagonal)
        nw_wp = [(66, WB_Y), (27, WB_Y), (25, 28), (SB_X, 25), (SB_X, 66)]
        nw_pts = _densify(nw_wp)
        self._paint_path(nw_pts, 1)
        self.paths['WB_SB'] = nw_pts

    # ------------------------------------------------------------------
    # Turbine: four sweeping Bezier curves
    # ------------------------------------------------------------------
    def _build_turbine(self):
        # NE curve (NB->WB): sweeps through upper-right
        ne_pts = _bezier((NB_X, 22), (NB_X, 6), (56, WB_Y), (42, WB_Y), 40)
        ne_full = _densify([(NB_X, 66), (NB_X, 22)]) + ne_pts + _densify([(42, WB_Y), (-3, WB_Y)])
        self._paint_path(ne_pts, 1)
        self.paths['NB_WB'] = ne_full

        # SE curve (EB->NB): sweeps through lower-right
        se_pts = _bezier((42, EB_Y), (58, EB_Y), (NB_X, 58), (NB_X, 42), 40)
        se_full = _densify([(-3, EB_Y), (42, EB_Y)]) + se_pts + _densify([(NB_X, 42), (NB_X, -3)])
        self._paint_path(se_pts, 1)
        self.paths['EB_NB'] = se_full

        # SW curve (SB->EB): sweeps through lower-left
        sw_pts = _bezier((SB_X, 42), (SB_X, 58), (8, EB_Y), (22, EB_Y), 40)
        sw_full = _densify([(SB_X, -3), (SB_X, 42)]) + sw_pts + _densify([(22, EB_Y), (66, EB_Y)])
        self._paint_path(sw_pts, 1)
        self.paths['SB_EB'] = sw_full

        # NW curve (WB->SB): sweeps through upper-left
        nw_pts = _bezier((22, WB_Y), (6, WB_Y), (SB_X, 6), (SB_X, 22), 40)
        nw_full = _densify([(66, WB_Y), (22, WB_Y)]) + nw_pts + _densify([(SB_X, 22), (SB_X, 66)])
        self._paint_path(nw_pts, 1)
        self.paths['WB_SB'] = nw_full

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------
    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.action_l or input_state.action_r:
            self.type_index = (self.type_index + 1) % len(self.TYPES)
            self._build()
            self.vehicles = []
            consumed = True
        if input_state.up_pressed:
            self.spawn_rate = min(6.0, self.spawn_rate + 0.5)
            consumed = True
        if input_state.down_pressed:
            self.spawn_rate = max(0.5, self.spawn_rate - 0.5)
            consumed = True
        return consumed

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    def update(self, dt: float):
        self.time += dt

        # Auto-cycle type
        self.auto_timer += dt
        if self.auto_timer >= self.auto_interval:
            self.auto_timer = 0
            self.type_index = (self.type_index + 1) % len(self.TYPES)
            self._build()
            self.vehicles = []

        # Spawn vehicles
        self.spawn_timer += dt
        if self.spawn_timer >= 1.0 / max(0.1, self.spawn_rate):
            self.spawn_timer = 0
            self._spawn()

        # Update vehicles
        for v in self.vehicles:
            v['progress'] += v['speed'] * dt

        # Remove finished vehicles
        self.vehicles = [v for v in self.vehicles
                         if v['progress'] < len(self.paths[v['key']]) - 1]

    def _spawn(self):
        """Spawn a vehicle on a random path."""
        keys = list(self.paths.keys())
        if not keys:
            return
        # Weight: more through traffic than ramp traffic
        thru_keys = [k for k in keys if k.endswith('_thru')]
        ramp_keys = [k for k in keys if not k.endswith('_thru')]
        if ramp_keys and random.random() < 0.4:
            key = random.choice(ramp_keys)
        elif thru_keys:
            key = random.choice(thru_keys)
        else:
            key = random.choice(keys)

        # Color by origin direction
        origin = key.split('_')[0]
        color = self.DIR_COLORS.get(origin, (255, 255, 255))

        self.vehicles.append({
            'key': key,
            'progress': 0.0,
            'speed': random.uniform(18, 28),
            'color': color,
        })

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------
    def _vehicle_pos(self, v):
        """Get interpolated screen position for a vehicle."""
        path = self.paths[v['key']]
        idx = v['progress']
        i = int(idx)
        if i >= len(path) - 1:
            return path[-1]
        frac = idx - i
        x0, y0 = path[i]
        x1, y1 = path[i + 1]
        return (x0 + (x1 - x0) * frac, y0 + (y1 - y0) * frac)

    def draw(self):
        self.display.clear(self.GROUND)

        # Draw road surface
        for x, y in self.road_pixels:
            if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
                self.display.set_pixel(x, y, self.HWY_COLOR)

        # Lane dashes on main highways (skip intersection zone)
        for y in range(GRID_SIZE):
            if 28 <= y <= 35:
                continue
            if y % 4 < 2:
                self.display.set_pixel(CENTER, y, self.LANE_DASH)
        for x in range(GRID_SIZE):
            if 28 <= x <= 35:
                continue
            if x % 4 < 2:
                self.display.set_pixel(x, CENTER, self.LANE_DASH)

        # Draw vehicles (2px each)
        for v in self.vehicles:
            x, y = self._vehicle_pos(v)
            ix, iy = int(x), int(y)
            if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
                self.display.set_pixel(ix, iy, v['color'])

        # Type label
        label = self.TYPES[self.type_index].upper()
        self.display.draw_text_small(2, 1, label, (160, 160, 160))

"""
Indy 500 - Top-Down Racing
===========================
Race a drone car through 6 tracks! First to 4 laps wins the track.
The final track is ice - watch your traction.

Controls:
  Left/Right - Steer
  Space      - Gas
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
import bisect
import math


def _define_tracks():
    """Return list of track configurations."""
    pi = math.pi
    return [
        # Track 1: Oval
        {
            'name': 'OVAL',
            'segments': [
                ('arc', 32, 34, 26, 22, 0, 2 * pi),
            ],
            'start': (38, 56, pi),
            'finish': (32, 56),
            'finish_axis': 'v',
            'finish_sign': -1,  # cos(angle) < 0 = going left
            'checkpoint': (32, 12),
            'cp_radius': 8,
        },
        # Track 2: Rectangle with rounded corners
        {
            'name': 'RECT',
            'segments': [
                ('line', 20, 16, 44, 16),        # top
                ('line', 52, 24, 52, 48),         # right
                ('line', 44, 56, 20, 56),         # bottom
                ('line', 12, 48, 12, 24),         # left
                ('arc', 44, 24, 8, 8, -pi/2, 0),  # top-right
                ('arc', 44, 48, 8, 8, 0, pi/2),   # bottom-right
                ('arc', 20, 48, 8, 8, pi/2, pi),  # bottom-left
                ('arc', 20, 24, 8, 8, pi, 3*pi/2),  # top-left
            ],
            'start': (38, 56, pi),
            'finish': (32, 56),
            'finish_axis': 'v',
            'finish_sign': -1,
            'checkpoint': (32, 16),
            'cp_radius': 8,
        },
        # Track 3: Figure 8 (two ellipses crossing in center)
        {
            'name': 'FIGURE 8',
            'segments': [
                ('arc', 32, 24, 16, 12, 0, 2 * pi),
                ('arc', 32, 48, 16, 12, 0, 2 * pi),
            ],
            'start': (42, 54, pi + pi/4),
            'finish': (22, 56),
            'finish_axis': 'v',
            'finish_sign': -1,
            'checkpoint': (32, 12),
            'cp_radius': 8,
        },
        # Track 4: L-Track
        {
            'name': 'L-TRACK',
            'segments': [
                ('line', 14, 54, 50, 54),   # bottom
                ('line', 50, 54, 50, 16),   # right
                ('line', 50, 16, 32, 16),   # top
                ('line', 32, 16, 32, 34),   # middle vertical
                ('line', 32, 34, 14, 34),   # middle horizontal
                ('line', 14, 34, 14, 54),   # left
            ],
            'start': (40, 54, pi),
            'finish': (26, 54),
            'finish_axis': 'v',
            'finish_sign': -1,
            'checkpoint': (50, 16),
            'cp_radius': 8,
            'drone_speed': 21.0,  # ~28s/4 laps: tight corners cost the player more
        },
        # Track 5: Diamond (45-degree rotated square)
        {
            'name': 'DIAMOND',
            'segments': [
                ('line', 32, 12, 56, 36),
                ('line', 56, 36, 32, 60),
                ('line', 32, 60, 8, 36),
                ('line', 8, 36, 32, 12),
            ],
            'start': (26, 54, math.atan2(-24, -24)),
            'finish': (32, 60),
            'finish_axis': 'v',
            'finish_sign': -1,
            'checkpoint': (32, 12),
            'cp_radius': 8,
            'drone_speed': 24.5,  # ~22s/4 laps
        },
        # Track 6: Ice oval — low traction, the car drifts wide
        {
            'name': 'ICE LAKE',
            'segments': [
                ('arc', 32, 36, 26, 20, 0, 2 * pi),
            ],
            'start': (38, 56, pi),
            'finish': (32, 56),
            'finish_axis': 'v',
            'finish_sign': -1,
            'checkpoint': (32, 16),
            'cp_radius': 8,
            'ice': True,
            'drone_speed': 17.0,  # ~34s/4 laps: drift cornering caps player pace
        },
    ]


TRACKS = _define_tracks()


class Indy500(Game):
    name = "INDIE 500"
    description = "6 tracks!"
    category = "retro"
    GUIDE = {
        'desc': 'Head-to-head racing against a drone car - first to 4 laps wins the track. Beat the drone on all 6 tracks for victory; if it finishes first, the race is over. Walls and bumping the drone send cars spinning, the steering snaps to 16 rotary detents on release, and the final ice track has barely any grip.',
    }

    TRACK_WIDTH = 12
    LAPS_TO_WIN = 4  # first car to 4 laps takes the track

    # Car parameters
    MAX_SPEED = 60.0
    ACCELERATION = 40.0
    FRICTION = 25.0
    TURN_SPEED = 4.0

    # Crash / bump spin
    SPIN_DURATION = 0.6   # Seconds spent spinning
    SPIN_RATE = 10.0      # Radians/sec while spinning
    SPIN_DECAY = 40.0     # Speed lost per second while spinning

    # Ice physics: velocity lerps toward heading this fast (per second)
    ICE_TRACTION = 1.5

    # Drone opponent
    DRONE_BASE_SPEED = 26.0   # Pixels/sec on track 1
    DRONE_SPEED_STEP = 2.0    # Added per track
    BUMP_DIST = 3.0           # Car-to-car contact distance
    BUMP_COOLDOWN = 1.5

    # Colors
    TRACK_COLOR = (60, 60, 70)
    ICE_COLOR = (170, 195, 220)
    GRASS_COLOR = (30, 80, 30)
    SNOW_COLOR = (205, 215, 230)
    CURB_COLOR = (200, 50, 50)
    CAR_COLOR = (255, 200, 50)
    CAR_ACCENT = (200, 100, 30)
    DRONE_COLOR = (80, 180, 255)
    DRONE_ACCENT = (40, 100, 200)
    FINISH_COLOR = Colors.WHITE

    def __init__(self, display: Display):
        super().__init__(display)
        self.track_mask = None
        self.curb_mask = None
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 0
        self.total_laps = 0
        self.victory = False
        self.transition_timer = 0.0
        self._load_track(0)

    def _load_track(self, level):
        """Load a track by index and reset car/lap state."""
        self.level = level
        track = TRACKS[level]

        # Car state
        sx, sy, sa = track['start']
        self.x = float(sx)
        self.y = float(sy)
        self.angle = sa
        self.speed = 0.0
        self.vx = 0.0
        self.vy = 0.0
        self.spin_timer = 0.0
        self._steer_prev = False

        # Lap tracking
        self.lap = 0
        self.lap_time = 0.0
        self.last_lap_time = 0.0
        self.crossed_finish = False
        self.checkpoint_passed = False
        self.off_track = False

        # Build masks and the drone's centerline path
        self._build_track_mask(track)
        self._build_waypoints(track)

        # Drone opponent state — gridded a few pixels up the road from the
        # player so the cars aren't stacked at the start
        self.drone_speed = track.get(
            'drone_speed', self.DRONE_BASE_SPEED + level * self.DRONE_SPEED_STEP)
        near = min(range(len(self.wp_pts)),
                   key=lambda i: (self.wp_pts[i][0] - self.x) ** 2
                   + (self.wp_pts[i][1] - self.y) ** 2)
        self.drone_dist = (self.wp_cum[near] + 10.0) % self.wp_total
        self.drone_lap = 0
        self.drone_spin = 0.0
        self.bump_cd = 0.0
        self.drone_x, self.drone_y, self.drone_angle = self._path_pos(
            self.drone_dist)

    def _build_track_mask(self, track):
        """Precompute boolean grid from track segments."""
        w = GRID_SIZE
        half = self.TRACK_WIDTH / 2.0
        self.track_mask = [[False] * w for _ in range(w)]

        for seg in track['segments']:
            if seg[0] == 'line':
                self._stamp_line(seg[1], seg[2], seg[3], seg[4], half)
            elif seg[0] == 'arc':
                self._stamp_arc(seg[1], seg[2], seg[3], seg[4],
                                seg[5], seg[6], half)

        # Build curb mask: on-track pixels with an off-track neighbor
        self.curb_mask = [[False] * w for _ in range(w)]
        for y in range(w):
            for x in range(w):
                if self.track_mask[y][x]:
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        nx, ny = x + dx, y + dy
                        if (nx < 0 or nx >= w or ny < 0 or ny >= w
                                or not self.track_mask[ny][nx]):
                            self.curb_mask[y][x] = True
                            break

    def _build_waypoints(self, track):
        """Sample segment centerlines into an ordered lap path for the drone.

        Segments aren't stored in path order, so each is sampled in its own
        direction and the pieces are chained end-to-end by nearest endpoint.
        Full-circle arcs are rings: they rotate to start wherever the chain
        reaches them (this is what makes the figure-8 traverse both loops).
        """
        two_pi = 2 * math.pi
        segs = []
        for seg in track['segments']:
            pts = []
            if seg[0] == 'line':
                x1, y1, x2, y2 = seg[1:5]
                length = math.hypot(x2 - x1, y2 - y1)
                steps = max(2, int(length / 2))
                for i in range(steps + 1):
                    t = i / steps
                    pts.append((x1 + (x2 - x1) * t, y1 + (y2 - y1) * t))
                closed = False
            else:
                cx, cy, rx, ry, a0, a1 = seg[1:7]
                span = a1 - a0
                if span < 0:
                    span += two_pi
                closed = span >= two_pi - 1e-6
                steps = max(8, int(span * max(rx, ry) / 2))
                count = steps if closed else steps + 1
                for i in range(count):
                    a = a0 + span * i / steps
                    pts.append((cx + math.cos(a) * rx, cy + math.sin(a) * ry))
            segs.append((pts, closed))

        def d2(p, q):
            return (p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2

        sx, sy, sa = track['start']
        hx, hy = math.cos(sa), math.sin(sa)

        # First segment: the one passing nearest the start position, oriented
        # to run the direction the player starts facing.
        first_i = min(range(len(segs)),
                      key=lambda i: min(d2(p, (sx, sy)) for p in segs[i][0]))
        pts, closed = segs.pop(first_i)
        near = min(range(len(pts)), key=lambda i: d2(pts[i], (sx, sy)))
        if closed:
            pts = pts[near:] + pts[:near]
            if (pts[1][0] - pts[0][0]) * hx + (pts[1][1] - pts[0][1]) * hy < 0:
                pts = [pts[0]] + pts[1:][::-1]
        else:
            j = min(near, len(pts) - 2)
            if (pts[j + 1][0] - pts[j][0]) * hx \
                    + (pts[j + 1][1] - pts[j][1]) * hy < 0:
                pts = pts[::-1]
        ordered = pts[:]

        # Chain the rest end-to-end by nearest endpoint (or nearest ring point)
        while segs:
            cur = ordered[-1]
            best = None  # (dist, seg_index, reversed, ring_rotation)
            for i, (pts, closed) in enumerate(segs):
                if closed:
                    idx = min(range(len(pts)), key=lambda k: d2(pts[k], cur))
                    cand = (d2(pts[idx], cur), i, False, idx)
                else:
                    d0 = d2(pts[0], cur)
                    d1 = d2(pts[-1], cur)
                    cand = (d0, i, False, 0) if d0 <= d1 else (d1, i, True, 0)
                if best is None or cand[0] < best[0]:
                    best = cand
            _, i, rev, rot = best
            pts, closed = segs.pop(i)
            if closed:
                pts = pts[rot:] + pts[:rot]
            elif rev:
                pts = pts[::-1]
            ordered.extend(pts)

        # Drop near-duplicate consecutive points (shared segment endpoints)
        deduped = [ordered[0]]
        for p in ordered[1:]:
            if d2(p, deduped[-1]) > 0.09:
                deduped.append(p)
        ordered = deduped

        # Cumulative distance along the loop (closing segment via wp_total)
        cum = [0.0]
        for i in range(1, len(ordered)):
            px, py = ordered[i - 1]
            qx, qy = ordered[i]
            cum.append(cum[-1] + math.hypot(qx - px, qy - py))
        last = ordered[-1]
        first = ordered[0]
        self.wp_pts = ordered
        self.wp_cum = cum
        self.wp_total = cum[-1] + math.hypot(first[0] - last[0],
                                             first[1] - last[1])

    def _path_pos(self, d):
        """Return (x, y, heading) at distance d along the waypoint loop."""
        n = len(self.wp_pts)
        d = d % self.wp_total
        i = bisect.bisect_right(self.wp_cum, d) - 1
        p0 = self.wp_pts[i]
        p1 = self.wp_pts[(i + 1) % n]
        if i + 1 < n:
            seg_len = self.wp_cum[i + 1] - self.wp_cum[i]
        else:
            seg_len = self.wp_total - self.wp_cum[i]
        t = (d - self.wp_cum[i]) / seg_len if seg_len > 1e-6 else 0.0
        x = p0[0] + (p1[0] - p0[0]) * t
        y = p0[1] + (p1[1] - p0[1]) * t
        ang = math.atan2(p1[1] - p0[1], p1[0] - p0[0])
        return x, y, ang

    def _stamp_line(self, x1, y1, x2, y2, half):
        """Stamp thick line onto track mask."""
        dx = x2 - x1
        dy = y2 - y1
        length = math.sqrt(dx * dx + dy * dy)
        if length < 0.1:
            self._stamp_circle(x1, y1, half)
            return
        steps = int(length * 2) + 1
        for i in range(steps + 1):
            t = i / steps
            self._stamp_circle(x1 + dx * t, y1 + dy * t, half)

    def _stamp_arc(self, cx, cy, rx, ry, a0, a1, half):
        """Stamp thick arc onto track mask."""
        span = a1 - a0
        if span < 0:
            span += 2 * math.pi
        steps = max(int(abs(span) * max(rx, ry) * 2), 60)
        for i in range(steps + 1):
            t = i / steps
            a = a0 + span * t
            self._stamp_circle(cx + math.cos(a) * rx,
                               cy + math.sin(a) * ry, half)

    def _stamp_circle(self, px, py, r):
        """Mark all pixels within radius r of (px, py) as on-track."""
        w = GRID_SIZE
        r2 = r * r
        ir = int(r) + 1
        ix, iy = int(round(px)), int(round(py))
        for dy in range(-ir, ir + 1):
            yy = iy + dy
            if 0 <= yy < w:
                for dx in range(-ir, ir + 1):
                    xx = ix + dx
                    if 0 <= xx < w:
                        ddx = xx - px
                        ddy = yy - py
                        if ddx * ddx + ddy * ddy <= r2:
                            self.track_mask[yy][xx] = True

    def point_on_track(self, x: float, y: float) -> bool:
        """Check if a point is on the track using precomputed mask."""
        ix, iy = int(x), int(y)
        if 0 <= ix < GRID_SIZE and 0 <= iy < GRID_SIZE:
            return self.track_mask[iy][ix]
        return False

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        # Track transition splash
        if self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self._load_track(self.level)
            return

        self.lap_time += dt
        track = TRACKS[self.level]

        if self.spin_timer > 0:
            # Spinning out — no control, bleeding speed
            self.spin_timer -= dt
            self.angle += self.SPIN_RATE * dt
            self.speed = max(0.0, self.speed - self.SPIN_DECAY * dt)
        else:
            # Steering
            steering = input_state.left or input_state.right
            if input_state.left:
                self.angle -= self.TURN_SPEED * dt
            if input_state.right:
                self.angle += self.TURN_SPEED * dt
            if self._steer_prev and not steering:
                # Rotary feel: snap heading to 16 detents on release
                step = math.pi / 8
                self.angle = round(self.angle / step) * step
            self._steer_prev = steering

            # Acceleration / friction
            if input_state.action_l_held or input_state.action_r_held:
                self.speed += self.ACCELERATION * dt
            else:
                self.speed -= self.FRICTION * dt
            self.speed = max(0, min(self.MAX_SPEED, self.speed))

        # Save position
        prev_x = self.x
        prev_y = self.y

        # Velocity: instant on tarmac, lerped toward heading on ice (drift)
        hvx = math.cos(self.angle) * self.speed
        hvy = math.sin(self.angle) * self.speed
        if track.get('ice'):
            blend = min(1.0, self.ICE_TRACTION * dt)
            self.vx += (hvx - self.vx) * blend
            self.vy += (hvy - self.vy) * blend
        else:
            self.vx = hvx
            self.vy = hvy

        new_x = self.x + self.vx * dt
        new_y = self.y + self.vy * dt

        # Collision with track boundary
        if self.point_on_track(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.off_track = False
        else:
            # Wall hit — spin out instead of dead-stopping
            if self.spin_timer <= 0:
                self.spin_timer = self.SPIN_DURATION
            self.speed *= 0.5
            self.vx = 0.0
            self.vy = 0.0
            self.x = prev_x - math.cos(self.angle) * 0.5
            self.y = prev_y - math.sin(self.angle) * 0.5
            self.off_track = True
            if not self.point_on_track(self.x, self.y):
                self.x = prev_x
                self.y = prev_y

        self.x = max(1, min(GRID_SIZE - 2, self.x))
        self.y = max(1, min(GRID_SIZE - 2, self.y))

        # Drone opponent
        self._update_drone(dt)
        if self.state != GameState.PLAYING:
            return

        # Car-to-car bump: both cars spin briefly
        if self.bump_cd > 0:
            self.bump_cd -= dt
        ddx = self.x - self.drone_x
        ddy = self.y - self.drone_y
        if (ddx * ddx + ddy * ddy < self.BUMP_DIST * self.BUMP_DIST
                and self.bump_cd <= 0):
            self.bump_cd = self.BUMP_COOLDOWN
            self.spin_timer = self.SPIN_DURATION
            self.drone_spin = self.SPIN_DURATION
            self.speed *= 0.5

        # Check checkpoint
        cpx, cpy = track['checkpoint']
        cpr = track['cp_radius']
        dx = self.x - cpx
        dy = self.y - cpy
        if dx * dx + dy * dy < cpr * cpr:
            self.checkpoint_passed = True

        # Check finish line crossing
        fx, fy = track['finish']
        if abs(self.x - fx) < 5 and abs(self.y - fy) < 5:
            if track['finish_axis'] == 'v':
                correct_dir = math.cos(self.angle) * track['finish_sign'] > 0
            else:
                correct_dir = math.sin(self.angle) * track['finish_sign'] > 0

            if correct_dir and not self.crossed_finish and self.checkpoint_passed:
                self.crossed_finish = True
                self.checkpoint_passed = False
                self.lap += 1
                self.last_lap_time = self.lap_time
                self.lap_time = 0.0
                if self.lap >= self.LAPS_TO_WIN:
                    # Beat the drone to 4 laps — take the track
                    self.total_laps += self.lap
                    if self.level + 1 >= len(TRACKS):
                        self.score = self.total_laps
                        self.victory = True
                        self.state = GameState.WIN
                    else:
                        self.level += 1
                        self.transition_timer = 1.5
        else:
            self.crossed_finish = False

    def _update_drone(self, dt: float):
        """Advance the drone along its waypoint loop."""
        if self.drone_spin > 0:
            self.drone_spin -= dt
            self.drone_angle += self.SPIN_RATE * dt
            return

        self.drone_dist += self.drone_speed * dt
        if self.drone_dist >= self.wp_total:
            self.drone_dist -= self.wp_total
            self.drone_lap += 1
            if self.drone_lap >= self.LAPS_TO_WIN:
                # Drone finished first — race lost
                self.score = self.total_laps + self.lap
                self.victory = False
                self.state = GameState.GAME_OVER
                return
        self.drone_x, self.drone_y, self.drone_angle = self._path_pos(
            self.drone_dist)

    def draw(self):
        # Transition splash between tracks
        if self.transition_timer > 0:
            self.display.clear(Colors.BLACK)
            track = TRACKS[self.level]
            self.display.draw_text_small(4, 24, f"TRACK {self.level + 1}",
                                         Colors.YELLOW)
            self.display.draw_text_small(4, 36, track['name'], Colors.WHITE)
            return

        track = TRACKS[self.level]
        self.display.clear(self.SNOW_COLOR if track.get('ice')
                           else self.GRASS_COLOR)
        self.draw_track()
        self.draw_finish_line()
        self.draw_racer(self.drone_x, self.drone_y, self.drone_angle,
                        self.DRONE_COLOR, self.DRONE_ACCENT)
        self.draw_racer(self.x, self.y, self.angle,
                        self.CAR_COLOR, self.CAR_ACCENT)
        self.draw_hud()

    def draw_track(self):
        """Draw track and curbs from precomputed masks."""
        surface = (self.ICE_COLOR if TRACKS[self.level].get('ice')
                   else self.TRACK_COLOR)
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.track_mask[y][x]:
                    if self.curb_mask[y][x]:
                        if (x + y) // 3 % 2 == 0:
                            color = self.CURB_COLOR
                        else:
                            color = Colors.WHITE
                    else:
                        color = surface
                    self.display.set_pixel(x, y, color)

    def draw_finish_line(self):
        """Draw checkerboard finish line at the track-specific position."""
        track = TRACKS[self.level]
        fx, fy = track['finish']
        hw = self.TRACK_WIDTH // 2 + 2

        if track['finish_axis'] == 'v':
            for y in range(GRID_SIZE):
                if abs(y - fy) <= hw and self.point_on_track(fx, y):
                    for dx in range(-1, 2):
                        px = int(fx) + dx
                        if 0 <= px < GRID_SIZE:
                            if (dx + y) % 2 == 0:
                                self.display.set_pixel(px, y,
                                                       self.FINISH_COLOR)
                            else:
                                self.display.set_pixel(px, y, Colors.BLACK)
        else:
            for x in range(GRID_SIZE):
                if abs(x - fx) <= hw and self.point_on_track(x, fy):
                    for dy in range(-1, 2):
                        py = int(fy) + dy
                        if 0 <= py < GRID_SIZE:
                            if (x + dy) % 2 == 0:
                                self.display.set_pixel(x, py,
                                                       self.FINISH_COLOR)
                            else:
                                self.display.set_pixel(x, py, Colors.BLACK)

    def draw_racer(self, x, y, angle, body, accent):
        """Draw a car (player or drone) at the given pose."""
        cx, cy = int(x), int(y)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # Front
        fx = int(cx + cos_a * 2)
        fy = int(cy + sin_a * 2)
        if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
            self.display.set_pixel(fx, fy, body)

        # Body
        self.display.set_pixel(cx, cy, body)

        # Back
        bx = int(cx - cos_a * 1)
        by = int(cy - sin_a * 1)
        if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
            self.display.set_pixel(bx, by, accent)

        # Sides
        sx1 = int(cx - sin_a)
        sy1 = int(cy + cos_a)
        sx2 = int(cx + sin_a)
        sy2 = int(cy - cos_a)
        if 0 <= sx1 < GRID_SIZE and 0 <= sy1 < GRID_SIZE:
            self.display.set_pixel(sx1, sy1, accent)
        if 0 <= sx2 < GRID_SIZE and 0 <= sy2 < GRID_SIZE:
            self.display.set_pixel(sx2, sy2, accent)

    def draw_hud(self):
        """Draw track number and player-vs-drone lap counters."""
        self.display.draw_text_small(1, 1, f"T{self.level + 1}", Colors.GRAY)
        self.display.draw_text_small(13, 1,
                                     f"P{self.lap}/{self.LAPS_TO_WIN}",
                                     Colors.WHITE)
        self.display.draw_text_small(36, 1,
                                     f"D{self.drone_lap}/{self.LAPS_TO_WIN}",
                                     self.DRONE_COLOR)

    def draw_game_over(self, selection: int = 0):
        """Draw game over or victory screen."""
        self.display.clear(Colors.BLACK)

        if self.victory:
            self.display.draw_text_small(4, 8, "VICTORY!", Colors.YELLOW)
            self.display.draw_text_small(4, 18, "ALL TRACKS", Colors.GREEN)
            self.display.draw_text_small(4, 26, "CLEARED!", Colors.GREEN)
            self.display.draw_text_small(4, 36, f"LAPS:{self.total_laps}",
                                         Colors.WHITE)
        else:
            self.display.draw_text_small(4, 10, "DRONE WINS!", Colors.RED)
            self.display.draw_text_small(4, 24, f"TRK:{self.level + 1}/6",
                                         Colors.WHITE)
            self.display.draw_text_small(4, 32, f"LAPS:{self.score}",
                                         Colors.WHITE)

        if selection == 0:
            self.display.draw_text_small(4, 48, ">PLAY AGAIN", Colors.YELLOW)
            self.display.draw_text_small(4, 56, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(4, 48, " PLAY AGAIN", Colors.GRAY)
            self.display.draw_text_small(4, 56, ">MENU", Colors.YELLOW)

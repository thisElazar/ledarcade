"""
Indy 500 - Top-Down Racing
===========================
Race through 5 tracks! Get more than 6 laps in 60s to advance.

Controls:
  Left/Right - Steer
  Space      - Gas
"""

from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE
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
        },
    ]


TRACKS = _define_tracks()


class Indy500(Game):
    name = "INDY 500"
    description = "5 tracks!"
    category = "retro"

    TRACK_WIDTH = 12
    LAPS_TO_ADVANCE = 7  # must get more than 6 laps in 60s

    # Car parameters
    MAX_SPEED = 60.0
    ACCELERATION = 40.0
    FRICTION = 25.0
    TURN_SPEED = 4.0

    # Colors
    TRACK_COLOR = (60, 60, 70)
    GRASS_COLOR = (30, 80, 30)
    CURB_COLOR = (200, 50, 50)
    CAR_COLOR = (255, 200, 50)
    CAR_ACCENT = (200, 100, 30)
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
        """Load a track by index and reset car/lap/timer state."""
        self.level = level
        track = TRACKS[level]

        # Car state
        sx, sy, sa = track['start']
        self.x = float(sx)
        self.y = float(sy)
        self.angle = sa
        self.speed = 0.0

        # Lap tracking
        self.lap = 0
        self.lap_time = 0.0
        self.last_lap_time = 0.0
        self.crossed_finish = False
        self.checkpoint_passed = False
        self.off_track = False

        # Timer
        self.time_remaining = 60.0

        # Build masks
        self._build_track_mask(track)

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
        if self.state == GameState.GAME_OVER:
            return

        # Track transition splash
        if self.transition_timer > 0:
            self.transition_timer -= dt
            if self.transition_timer <= 0:
                self._load_track(self.level)
            return

        # Countdown timer
        self.time_remaining -= dt
        if self.time_remaining <= 0:
            self.time_remaining = 0
            if self.lap >= self.LAPS_TO_ADVANCE:
                # Enough laps — advance to next track
                self.total_laps += self.lap
                if self.level + 1 >= len(TRACKS):
                    self.score = self.total_laps
                    self.victory = True
                    self.state = GameState.GAME_OVER
                else:
                    self.level += 1
                    self.transition_timer = 1.5
            else:
                self.score = self.total_laps + self.lap
                self.state = GameState.GAME_OVER
            return

        self.lap_time += dt

        # Steering
        if input_state.left:
            self.angle -= self.TURN_SPEED * dt
        if input_state.right:
            self.angle += self.TURN_SPEED * dt

        # Acceleration / friction
        if input_state.action_l_held or input_state.action_r_held:
            self.speed += self.ACCELERATION * dt
        else:
            self.speed -= self.FRICTION * dt
        self.speed = max(0, min(self.MAX_SPEED, self.speed))

        # Save position
        prev_x = self.x
        prev_y = self.y

        # Move
        new_x = self.x + math.cos(self.angle) * self.speed * dt
        new_y = self.y + math.sin(self.angle) * self.speed * dt

        # Collision with track boundary
        if self.point_on_track(new_x, new_y):
            self.x = new_x
            self.y = new_y
            self.off_track = False
        else:
            self.speed = 0
            self.x = prev_x - math.cos(self.angle) * 0.5
            self.y = prev_y - math.sin(self.angle) * 0.5
            self.off_track = True
            if not self.point_on_track(self.x, self.y):
                self.x = prev_x
                self.y = prev_y

        self.x = max(1, min(GRID_SIZE - 2, self.x))
        self.y = max(1, min(GRID_SIZE - 2, self.y))

        # Check checkpoint
        track = TRACKS[self.level]
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
        else:
            self.crossed_finish = False

    def draw(self):
        # Transition splash between tracks
        if self.transition_timer > 0:
            self.display.clear(Colors.BLACK)
            track = TRACKS[self.level]
            self.display.draw_text_small(4, 24, f"TRACK {self.level + 1}",
                                         Colors.YELLOW)
            self.display.draw_text_small(4, 36, track['name'], Colors.WHITE)
            return

        self.display.clear(self.GRASS_COLOR)
        self.draw_track()
        self.draw_finish_line()
        self.draw_car()
        self.draw_hud()

    def draw_track(self):
        """Draw track and curbs from precomputed masks."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.track_mask[y][x]:
                    if self.curb_mask[y][x]:
                        if (x + y) // 3 % 2 == 0:
                            color = self.CURB_COLOR
                        else:
                            color = Colors.WHITE
                    else:
                        color = self.TRACK_COLOR
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

    def draw_car(self):
        """Draw the player's car."""
        cx, cy = int(self.x), int(self.y)
        cos_a = math.cos(self.angle)
        sin_a = math.sin(self.angle)

        # Front
        fx = int(cx + cos_a * 2)
        fy = int(cy + sin_a * 2)
        if 0 <= fx < GRID_SIZE and 0 <= fy < GRID_SIZE:
            self.display.set_pixel(fx, fy, self.CAR_COLOR)

        # Body
        self.display.set_pixel(cx, cy, self.CAR_COLOR)

        # Back
        bx = int(cx - cos_a * 1)
        by = int(cy - sin_a * 1)
        if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
            self.display.set_pixel(bx, by, self.CAR_ACCENT)

        # Sides
        sx1 = int(cx - sin_a)
        sy1 = int(cy + cos_a)
        sx2 = int(cx + sin_a)
        sy2 = int(cy - cos_a)
        if 0 <= sx1 < GRID_SIZE and 0 <= sy1 < GRID_SIZE:
            self.display.set_pixel(sx1, sy1, self.CAR_ACCENT)
        if 0 <= sx2 < GRID_SIZE and 0 <= sy2 < GRID_SIZE:
            self.display.set_pixel(sx2, sy2, self.CAR_ACCENT)

    def draw_hud(self):
        """Draw track number, lap counter, and countdown timer."""
        self.display.draw_text_small(1, 1, f"T{self.level + 1}", Colors.GRAY)
        self.display.draw_text_small(14, 1,
                                     f"L:{self.lap}/{self.LAPS_TO_ADVANCE}",
                                     Colors.WHITE)
        secs = max(0, int(self.time_remaining))
        mins = secs // 60
        secs = secs % 60
        timer_color = Colors.RED if self.time_remaining < 10 else Colors.YELLOW
        self.display.draw_text_small(44, 1, f"{mins}:{secs:02d}", timer_color)

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
            self.display.draw_text_small(8, 10, "TIME UP!", Colors.RED)
            self.display.draw_text_small(4, 24, f"TRK:{self.level + 1}/5",
                                         Colors.WHITE)
            self.display.draw_text_small(4, 32, f"LAPS:{self.score}",
                                         Colors.WHITE)

        if selection == 0:
            self.display.draw_text_small(4, 48, ">PLAY AGAIN", Colors.YELLOW)
            self.display.draw_text_small(4, 56, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(4, 48, " PLAY AGAIN", Colors.GRAY)
            self.display.draw_text_small(4, 56, ">MENU", Colors.YELLOW)

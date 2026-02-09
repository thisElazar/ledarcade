"""
LASER MIRRORS — First-Person Puzzle Game
==========================================
Wolfenstein-style raycaster puzzle game. Walk around moody rooms,
rotate mirrors to redirect laser beams onto targets.

Controls:
  Left/Right  - Rotate view
  Up/Down     - Move forward/backward
  Space       - Rotate mirror you're facing
"""

import math
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

# ═══════════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════════

FOV = math.pi / 3  # 60 degree FOV
HALF = GRID_SIZE // 2
MOVE_SPEED = 2.5
ROT_SPEED = 2.5
MARGIN = 0.2
MIRROR_ANIM_DUR = 1.0  # seconds for mirror rotation animation

# Cell types
EMPTY = 0
WALL = 1
MIRROR_BK = 2   # backslash mirror: \   (θ=45°)
MIRROR_FW = 3   # forward slash mirror: /  (θ=135°)
EMITTER_N = 4   # fires north (beam goes -y)
EMITTER_S = 5   # fires south (beam goes +y)
EMITTER_E = 6   # fires east  (beam goes +x)
EMITTER_W = 7   # fires west  (beam goes -x)
TARGET = 8
MIRROR_V = 9    # vertical mirror: |   (θ=90°)
MIRROR_H = 10   # horizontal mirror: —  (θ=0°/180°)

EMITTER_DIRS = {
    EMITTER_N: (0, -1),
    EMITTER_S: (0, 1),
    EMITTER_E: (1, 0),
    EMITTER_W: (-1, 0),
}

# Mirror system — 4 orientations, 45° apart, each press rotates CCW
MIRROR_TYPES = {MIRROR_BK, MIRROR_FW, MIRROR_V, MIRROR_H}
MIRROR_ANGLES = {
    MIRROR_BK: math.pi / 4,       # 45°  (\)
    MIRROR_V:  math.pi / 2,       # 90°  (|)
    MIRROR_FW: 3 * math.pi / 4,   # 135° (/)
    MIRROR_H:  math.pi,           # 180° (—)
}
MIRROR_NEXT = {  # CCW rotation cycle
    MIRROR_BK: MIRROR_V,
    MIRROR_V:  MIRROR_FW,
    MIRROR_FW: MIRROR_H,
    MIRROR_H:  MIRROR_BK,
}
# Precompute cardinal-direction reflections for grid-based tracing
MIRROR_REFLECT = {}
for _mt, _theta in MIRROR_ANGLES.items():
    _a2 = 2 * _theta
    _c2, _s2 = round(math.cos(_a2)), round(math.sin(_a2))
    MIRROR_REFLECT[_mt] = {}
    for _d in [(0, -1), (0, 1), (1, 0), (-1, 0)]:
        MIRROR_REFLECT[_mt][_d] = (int(_d[0]*_c2 + _d[1]*_s2),
                                   int(_d[0]*_s2 - _d[1]*_c2))

# Colors
STONE_COLOR = (40, 45, 70)
STONE_DARK = (30, 34, 55)
MIRROR_COLOR = (140, 180, 220)
TARGET_UNLIT = (60, 80, 60)
TARGET_LIT = (40, 255, 80)
LASER_CORE = (255, 80, 20)
LASER_GLOW = (80, 30, 10)
CEIL_COLOR = (15, 18, 30)
FLOOR_LIGHT = (35, 38, 55)
FLOOR_DARK = (28, 30, 45)

# ═══════════════════════════════════════════════════════════════════
#  Levels — 6 puzzles (all emitters on south wall, fire north)
# ═══════════════════════════════════════════════════════════════════

W = WALL
B = MIRROR_BK   # backslash \
F = MIRROR_FW   # forward slash /
EN = EMITTER_N  # fires north (into room)
T = TARGET
_ = EMPTY

LEVELS = [
    # Level 1: One mirror, one target. Rotate mirror once.
    # Beam: E(5,7)↑ → M(5,5)  /→east→wall (wrong)  \→west→T(1,5) (correct)
    {
        'map': [
            [W, W, W, W, W, W, W, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, T, _, _, _, F, _, W],
            [W, _, _, _, _, _, _, W],
            [W, W, W, W, W,EN, W, W],
        ],
        'start': (2.5, 2.5, math.pi / 2),
        'par': 25,
    },
    # Level 2: Two mirrors, one target. Rotate both.
    # Beam: E(2,8)↑ → M1(2,5)  \→west (wrong)  /→east→ M2(5,5)  \→south (wrong)  /→north→T(5,2)
    {
        'map': [
            [W, W, W, W, W, W, W, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, T, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, B, _, _, B, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, W,EN, W, W, W, W, W],
        ],
        'start': (4.5, 1.5, math.pi * 0.75),
        'par': 30,
    },
    # Level 3: Three mirrors, one target. Rotate M1 and M3.
    # Beam: E(5,9)↑ → M1(5,7) /→east(wrong), need \→west →
    #   M2(2,7) already \→north → M3(2,4) /→east(wrong), need \→west → T(1,4)
    {
        'map': [
            [W, W, W, W, W, W, W, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, T, F, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, W],
            [W, _, B, _, _, F, _, W],
            [W, _, _, _, _, _, _, W],
            [W, W, W, W, W,EN, W, W],
        ],
        'start': (3.5, 1.5, math.pi / 2),
        'par': 35,
    },
    # Level 4: Two emitters, two mirrors, two targets.
    # E1(3,9)↑→M1(3,7) /→east→wall(5,7), need \→west→T1(1,7)
    # E2(7,9)↑→M2(7,7) \→west→wall(5,7), need /→east→T2(9,7)
    {
        'map': [
            [W, W, W, W, W, W, W, W, W, W, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, T, _, F, _, W, _, B, _, T, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, W, W,EN, W, W, W,EN, W, W, W],
        ],
        'start': (5.5, 2.5, math.pi / 2),
        'par': 35,
    },
    # Level 5: Maze with walls blocking. 3 mirrors, 1 target.
    # E(3,9)↑→M1(3,7) B(\)→west(wrong), need F(/)→east →
    #   M2(7,7) B(\) correct→north → M3(7,3) F(/)→east(wrong), need B(\)→west → T(1,3)
    {
        'map': [
            [W, W, W, W, W, W, W, W, W, W],
            [W, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, W],
            [W, T, _, _, _, _, _, F, _, W],
            [W, _, _, _, _, W, _, _, _, W],
            [W, _, _, _, _, W, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, W],
            [W, _, _, B, _, _, _, B, _, W],
            [W, _, _, _, _, _, _, _, _, W],
            [W, W, W,EN, W, W, W, W, W, W],
        ],
        'start': (1.5, 1.5, math.pi / 2),
        'par': 40,
    },
    # Level 6: Two emitters, three mirrors, two targets.
    # E1(2,9)↑→M1(2,6) B(\)→west(wrong), need F(/)→east→ M2(5,6) B(\)→south(wrong), need F(/)→north→T1(5,2)
    # E2(9,9)↑→M3(9,6) F(/)→east(wrong), need B(\)→west→T2(7,6)
    {
        'map': [
            [W, W, W, W, W, W, W, W, W, W, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, T, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, B, _, _, B, _, T, _, F, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, _, _, _, _, _, _, _, _, _, W],
            [W, W,EN, W, W, W, W, W, W,EN, W],
        ],
        'start': (5.5, 1.5, math.pi / 2),
        'par': 45,
    },
]


# ═══════════════════════════════════════════════════════════════════
#  Game Class
# ═══════════════════════════════════════════════════════════════════

class LaserMirrors(Game):
    name = "LASER MIRRORS"
    description = "Redirect the beam"
    category = "unique"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 0
        self.time = 0.0
        self.phase = 'title'
        self.phase_timer = 2.5
        self.level_elapsed = 0.0

        # Ray offsets for rendering
        self.ray_offsets = []
        for col in range(GRID_SIZE):
            self.ray_offsets.append((col / GRID_SIZE - 0.5) * FOV)

        # Z-buffer for laser rendering
        self.zbuf = [0.0] * GRID_SIZE

        # Beam cells for floor glow
        self.beam_cells = set()

        # Hint overlay timer
        self.hint_timer = 0.0

        self._load_level(0)

    def _load_level(self, idx):
        """Load a level map."""
        if idx >= len(LEVELS):
            self.phase = 'won'
            self.phase_timer = 4.0
            return

        lvl = LEVELS[idx]
        self.level = idx
        self.level_elapsed = 0.0

        # Deep copy map
        self.map = [row[:] for row in lvl['map']]
        self.map_h = len(self.map)
        self.map_w = len(self.map[0])

        # Player start
        sx, sy, sa = lvl['start']
        self.px = sx
        self.py = sy
        self.pa = sa

        # Find emitters and targets
        self.emitters = []
        self.targets = []
        for y in range(self.map_h):
            for x in range(self.map_w):
                c = self.map[y][x]
                if c in EMITTER_DIRS:
                    self.emitters.append((x, y, c))
                elif c == TARGET:
                    self.targets.append([x, y, 0.0])  # charge: 0.0 to 1.0

        # Trace laser beams
        self.beam_segments = []
        self.beam_cells = set()
        self.target_hit = set()  # which targets beam touches this frame
        self._trace_all_lasers()

        # Level clear state
        self.level_clear = False
        self.clear_timer = 0.0
        self.mirror_anims = {}  # {(mx,my): {from_theta, to_theta, progress, from_type, to_type}}

        # Show hints
        self.hint_timer = 4.0

        self.phase = 'playing'

    def _cell(self, x, y):
        if x < 0 or x >= self.map_w or y < 0 or y >= self.map_h:
            return WALL
        return self.map[y][x]

    def _is_solid(self, x, y):
        c = self._cell(x, y)
        return c != EMPTY

    def _collision(self, x, y):
        for dx in (-MARGIN, MARGIN):
            for dy in (-MARGIN, MARGIN):
                if self._is_solid(int(x + dx), int(y + dy)):
                    return True
        return False

    def _facing_cell(self):
        cos_a = math.cos(self.pa)
        sin_a = math.sin(self.pa)
        check_x = int(self.px + cos_a * 1.2)
        check_y = int(self.py + sin_a * 1.2)
        return check_x, check_y

    # ─────────────────────────────────────────────────────────────
    #  Laser tracing
    # ─────────────────────────────────────────────────────────────

    def _trace_all_lasers(self):
        self.beam_segments = []
        self.beam_cells = set()
        self.target_hit = set()
        for ex, ey, etype in self.emitters:
            dx, dy = EMITTER_DIRS[etype]
            self._trace_beam(ex, ey, dx, dy)

    def _trace_beam(self, start_x, start_y, dx, dy):
        cx, cy = start_x, start_y
        for _ in range(30):
            nx, ny = cx + dx, cy + dy

            if nx < 0 or nx >= self.map_w or ny < 0 or ny >= self.map_h:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break

            cell = self.map[ny][nx]

            if cell == WALL or cell in EMITTER_DIRS:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break

            if cell == TARGET:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                self.target_hit.add((nx, ny))
                break

            if cell in MIRROR_REFLECT:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                dx, dy = MIRROR_REFLECT[cell][(dx, dy)]
                cx, cy = nx, ny
                continue

            # Empty cell
            self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
            self.beam_cells.add((nx, ny))
            cx, cy = nx, ny

    # ─────────────────────────────────────────────────────────────
    #  Animated laser tracing (during mirror rotation)
    # ─────────────────────────────────────────────────────────────

    def _trace_all_lasers_animated(self):
        """Retrace all lasers with continuous-angle reflection for animating mirrors."""
        self.beam_segments = []
        self.beam_cells = set()
        self.target_hit = set()
        for ex, ey, etype in self.emitters:
            dx, dy = EMITTER_DIRS[etype]
            self._trace_beam_animated(ex, ey, dx, dy)

    def _trace_beam_animated(self, start_x, start_y, dx, dy):
        """Grid-based trace that uses continuous angles at rotating mirrors."""
        cx, cy = start_x, start_y
        for _ in range(30):
            nx, ny = cx + dx, cy + dy
            if nx < 0 or nx >= self.map_w or ny < 0 or ny >= self.map_h:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break
            cell = self.map[ny][nx]
            if cell == WALL or cell in EMITTER_DIRS:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break
            if cell == TARGET:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                self.target_hit.add((nx, ny))
                break
            if cell in MIRROR_REFLECT:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                if (nx, ny) in self.mirror_anims:
                    # Rotating mirror: compute interpolated reflection angle
                    anim = self.mirror_anims[(nx, ny)]
                    t = min(1.0, anim['progress'])
                    theta = anim['from_theta'] + t * (anim['to_theta'] - anim['from_theta'])
                    a2 = 2 * theta
                    cos2, sin2 = math.cos(a2), math.sin(a2)
                    ref_dx = dx * cos2 + dy * sin2
                    ref_dy = dx * sin2 - dy * cos2
                    self._trace_continuous(nx + 0.5, ny + 0.5, ref_dx, ref_dy)
                    return
                # Static mirror: use precomputed lookup
                dx, dy = MIRROR_REFLECT[cell][(dx, dy)]
                cx, cy = nx, ny
                continue
            # Empty cell
            self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
            self.beam_cells.add((nx, ny))
            cx, cy = nx, ny

    def _trace_continuous(self, ox, oy, dx, dy, depth=0):
        """Float-step trace for beams at arbitrary angles after a rotating mirror."""
        if depth > 10:
            return
        step_sz = 0.05
        cx, cy = ox, oy
        start_cell = (int(ox), int(oy))
        entered = set()
        for _ in range(600):
            cx += dx * step_sz
            cy += dy * step_sz
            gx, gy = int(cx), int(cy)
            if gx < 0 or gx >= self.map_w or gy < 0 or gy >= self.map_h:
                self.beam_segments.append((ox, oy, cx, cy))
                return
            if (gx, gy) != start_cell and (gx, gy) not in entered:
                entered.add((gx, gy))
                cell = self.map[gy][gx]
                if cell == WALL or cell in EMITTER_DIRS:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    return
                if cell == TARGET:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    self.beam_cells.add((gx, gy))
                    self.target_hit.add((gx, gy))
                    return
                if cell in MIRROR_TYPES:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    self.beam_cells.add((gx, gy))
                    # Reflect off static mirror using continuous formula
                    a2 = 2 * MIRROR_ANGLES[cell]
                    cos2, sin2 = math.cos(a2), math.sin(a2)
                    new_dx = dx * cos2 + dy * sin2
                    new_dy = dx * sin2 - dy * cos2
                    self._trace_continuous(gx + 0.5, gy + 0.5, new_dx, new_dy, depth + 1)
                    return
                self.beam_cells.add((gx, gy))
        self.beam_segments.append((ox, oy, cx, cy))

    # ─────────────────────────────────────────────────────────────
    #  Update
    # ─────────────────────────────────────────────────────────────

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.time += dt

        if self.phase == 'title':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.phase = 'playing'
            return

        if self.phase == 'won':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.state = GameState.GAME_OVER
            return

        if self.phase == 'level_clear':
            self.clear_timer -= dt
            if self.clear_timer <= 0:
                self._load_level(self.level + 1)
            return

        # Playing
        self.level_elapsed += dt
        if self.hint_timer > 0:
            self.hint_timer -= dt

        # Rotation
        if input_state.left:
            self.pa -= ROT_SPEED * dt
        if input_state.right:
            self.pa += ROT_SPEED * dt

        # Movement
        cos_a = math.cos(self.pa)
        sin_a = math.sin(self.pa)
        speed = MOVE_SPEED * dt

        nx, ny = self.px, self.py
        if input_state.up:
            nx += cos_a * speed
            ny += sin_a * speed
        if input_state.down:
            nx -= cos_a * speed * 0.6
            ny -= sin_a * speed * 0.6

        if not self._collision(nx, self.py):
            self.px = nx
        if not self._collision(self.px, ny):
            self.py = ny

        # Advance mirror rotation animations
        if self.mirror_anims:
            done = []
            for pos, anim in self.mirror_anims.items():
                anim['progress'] += dt / MIRROR_ANIM_DUR
                if anim['progress'] >= 1.0:
                    mx, my = pos
                    self.map[my][mx] = anim['to_type']
                    done.append(pos)
            for pos in done:
                del self.mirror_anims[pos]
            self._trace_all_lasers_animated()
            if not self.mirror_anims:
                self._trace_all_lasers()

        # Rotate mirror with Space (blocked during animation)
        if input_state.action_l and not self.mirror_anims:
            fx, fy = self._facing_cell()
            if 0 <= fx < self.map_w and 0 <= fy < self.map_h:
                c = self.map[fy][fx]
                if c in MIRROR_TYPES:
                    from_theta = MIRROR_ANGLES[c]
                    self.mirror_anims[(fx, fy)] = {
                        'from_theta': from_theta,
                        'to_theta': from_theta + math.pi / 4,
                        'progress': 0.0,
                        'from_type': c,
                        'to_type': MIRROR_NEXT[c],
                    }

        # Advance target charge (3 seconds to fully charge)
        for t in self.targets:
            if (t[0], t[1]) in self.target_hit:
                if t[2] < 1.0:
                    t[2] = min(1.0, t[2] + dt / 3.0)
            else:
                if t[2] < 1.0:  # completed targets stay locked
                    t[2] = max(0.0, t[2] - dt / 1.5)

        # Check win condition
        if self.targets and all(t[2] >= 1.0 for t in self.targets):
            if not self.level_clear:
                self.level_clear = True
                lvl = LEVELS[self.level]
                time_bonus = max(0, lvl['par'] - self.level_elapsed) * 10
                self.score += 100 + int(time_bonus)
                self.phase = 'level_clear'
                self.clear_timer = 2.0

    # ─────────────────────────────────────────────────────────────
    #  Raycaster
    # ─────────────────────────────────────────────────────────────

    def _cast_column(self, col, angle):
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        if abs(cos_a) < 1e-8:
            cos_a = 1e-8
        if abs(sin_a) < 1e-8:
            sin_a = 1e-8

        map_x = int(self.px)
        map_y = int(self.py)
        delta_x = abs(1.0 / cos_a)
        delta_y = abs(1.0 / sin_a)

        if cos_a < 0:
            step_x = -1
            side_dist_x = (self.px - map_x) * delta_x
        else:
            step_x = 1
            side_dist_x = (map_x + 1.0 - self.px) * delta_x

        if sin_a < 0:
            step_y = -1
            side_dist_y = (self.py - map_y) * delta_y
        else:
            step_y = 1
            side_dist_y = (map_y + 1.0 - self.py) * delta_y

        side = 0
        for _ in range(64):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= self.map_w or map_y < 0 or map_y >= self.map_h:
                break

            cell = self._cell(map_x, map_y)
            if cell != EMPTY and cell not in MIRROR_TYPES:
                if side == 0:
                    perp = (map_x - self.px + (1 - step_x) / 2) / cos_a
                else:
                    perp = (map_y - self.py + (1 - step_y) / 2) / sin_a
                if perp < 0.01:
                    perp = 0.01

                if side == 0:
                    wall_x = self.py + perp * sin_a
                else:
                    wall_x = self.px + perp * cos_a
                wall_x -= int(wall_x)

                return (perp, cell, wall_x, side, map_x, map_y)

        return None

    # ─────────────────────────────────────────────────────────────
    #  Drawing
    # ─────────────────────────────────────────────────────────────

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == 'title':
            self._draw_title()
            return

        if self.phase == 'won':
            self._draw_win()
            return

        if self.phase == 'level_clear':
            self._draw_level_clear()
            return

        pulse = 0.9 + 0.1 * math.sin(self.time * 0.5)
        eye_h = 0.5

        for col in range(GRID_SIZE):
            ray_angle = self.pa + self.ray_offsets[col]
            hit = self._cast_column(col, ray_angle)

            cos_r = math.cos(ray_angle)
            sin_r = math.sin(ray_angle)

            if not hit:
                self.zbuf[col] = 999.0
                for y in range(HALF):
                    self.display.set_pixel(col, y, CEIL_COLOR)
                for y in range(HALF, GRID_SIZE):
                    p = y - HALF
                    if p <= 0:
                        continue
                    row_dist = eye_h * GRID_SIZE / p
                    fx = self.px + cos_r * row_dist
                    fy = self.py + sin_r * row_dist
                    fcx, fcy = int(fx), int(fy)
                    checker = (fcx + fcy) % 2
                    fog_f = min(1.0, 2.0 / (row_dist + 0.5)) * pulse
                    base = FLOOR_LIGHT if checker == 0 else FLOOR_DARK
                    r = int(base[0] * fog_f)
                    g = int(base[1] * fog_f)
                    b = int(base[2] * fog_f)
                    # Rotating floor panel under mirrors
                    if self._cell(fcx, fcy) in MIRROR_TYPES:
                        r = int(r * 0.35)
                        g = int(g * 0.35)
                        b = int(b * 0.45)
                    # Beam floor glow
                    if (fcx, fcy) in self.beam_cells:
                        r = min(255, r + int(60 * fog_f))
                        g = min(255, g + int(20 * fog_f))
                    self.display.set_pixel(col, y, (r, g, b))
                continue

            perp, cell, wall_x, side, mx, my = hit
            self.zbuf[col] = perp

            line_height = int(GRID_SIZE / perp) if perp > 0 else GRID_SIZE
            draw_start = max(0, HALF - line_height // 2)
            draw_end = min(GRID_SIZE - 1, HALF + line_height // 2)

            fog = min(1.0, 2.5 / (perp + 0.5)) * pulse
            if side == 1:
                fog *= 0.75

            for y in range(0, draw_start):
                self.display.set_pixel(col, y, CEIL_COLOR)

            for y in range(draw_start, draw_end + 1):
                v = (y - (HALF - line_height // 2)) / max(1, line_height)
                r, g, b = self._wall_color(cell, wall_x, v, mx, my)
                r = min(255, int(r * fog))
                g = min(255, int(g * fog))
                b = min(255, int(b * fog))
                self.display.set_pixel(col, y, (r, g, b))

            for y in range(draw_end + 1, GRID_SIZE):
                p = y - HALF
                if p <= 0:
                    self.display.set_pixel(col, y, CEIL_COLOR)
                    continue
                row_dist = eye_h * GRID_SIZE / p
                fx = self.px + cos_r * row_dist
                fy = self.py + sin_r * row_dist
                fcx, fcy = int(fx), int(fy)
                checker = (fcx + fcy) % 2
                fog_f = min(1.0, 2.0 / (row_dist + 0.5)) * pulse
                base = FLOOR_LIGHT if checker == 0 else FLOOR_DARK
                glow_r, glow_g = 0, 0
                # Emitter glow
                for ex, ey, etype in self.emitters:
                    dist = abs(fcx - ex) + abs(fcy - ey)
                    if dist <= 2:
                        intensity = (3 - dist) / 3.0
                        glow_r += int(40 * intensity)
                        glow_g += int(15 * intensity)
                # Target glow (scales with charge)
                for t in self.targets:
                    if t[2] > 0.01:
                        dist = abs(fcx - t[0]) + abs(fcy - t[1])
                        if dist <= 2:
                            intensity = (3 - dist) / 3.0 * t[2]
                            glow_g += int(50 * intensity)
                # Rotating floor panel under mirrors
                if self._cell(fcx, fcy) in MIRROR_TYPES:
                    base = (int(base[0] * 0.35), int(base[1] * 0.35), int(base[2] * 0.45))
                # Beam floor glow
                if (fcx, fcy) in self.beam_cells:
                    glow_r += int(60 * fog_f)
                    glow_g += int(20 * fog_f)
                r = min(255, int(base[0] * fog_f) + glow_r)
                g = min(255, int(base[1] * fog_f) + glow_g)
                b = int(base[2] * fog_f)
                self.display.set_pixel(col, y, (r, g, b))

        # Render laser beams in screen space
        self._draw_laser_beams()

        # Render mirror sprites (prism on log)
        self._draw_mirror_sprites()

        # Crosshair
        ch = (100, 100, 120)
        self.display.set_pixel(31, 32, ch)
        self.display.set_pixel(32, 32, ch)
        self.display.set_pixel(31, 31, ch)
        self.display.set_pixel(32, 31, ch)

        # HUD
        self.display.draw_text_small(2, 1, f"L{self.level + 1}", (150, 200, 150))
        score_txt = str(self.score)
        stx = 63 - len(score_txt) * 4
        self.display.draw_text_small(stx, 1, score_txt, Colors.WHITE)

        # Par timer
        secs = int(self.level_elapsed)
        lvl = LEVELS[self.level]
        remaining = max(0, lvl['par'] - secs)
        timer_color = Colors.GREEN if remaining > 10 else (Colors.ORANGE if remaining > 5 else Colors.RED)
        timer_txt = str(remaining)
        tx = 63 - len(timer_txt) * 4
        self.display.draw_text_small(tx, 58, timer_txt, timer_color)

        # Instruction overlay
        if self.hint_timer > 0:
            self._draw_hints()

    def _wall_color(self, cell, u, v, cx, cy):
        if cell == WALL:
            bu = int(u * 4)
            bv = int(v * 4)
            fu = u * 4 - bu
            fv = v * 4 - bv
            if bv % 2 == 1:
                fu = (u * 4 + 0.5)
                fu = fu - int(fu)
            if fu < 0.06 or fv < 0.06:
                return STONE_DARK
            return STONE_COLOR

        if cell in MIRROR_TYPES:
            mp = 0.8 + 0.2 * math.sin(self.time * 2.0)
            # Check if this mirror is animating
            anim = self.mirror_anims.get((cx, cy))
            if anim:
                t = min(1.0, anim['progress'])
                diag = anim['from_theta'] + t * (anim['to_theta'] - anim['from_theta'])
                mp = 1.0  # bright during animation
            else:
                diag = MIRROR_ANGLES[cell]
            # Distance from (u,v) to diagonal line through center
            dist = abs((u - 0.5) * math.sin(diag) - (v - 0.5) * math.cos(diag))
            if dist < 0.11:
                return (int(220 * mp), int(240 * mp), 255)
            if u < 0.08 or u > 0.92 or v < 0.08 or v > 0.92:
                return (80, 90, 110)
            return (int(MIRROR_COLOR[0] * mp), int(MIRROR_COLOR[1] * mp), int(MIRROR_COLOR[2] * mp))

        if cell in EMITTER_DIRS:
            du = abs(u - 0.5)
            dv = abs(v - 0.5)
            dist = du * du + dv * dv
            ep = 0.7 + 0.3 * math.sin(self.time * 3.0)
            if dist < 0.08:
                return (min(255, int(255 * ep)), int(100 * ep), 20)
            if dist < 0.15:
                return (int(180 * ep), int(60 * ep), 20)
            return (60, 30, 20)

        if cell == TARGET:
            charge = 0.0
            for t in self.targets:
                if t[0] == cx and t[1] == cy:
                    charge = t[2]
                    break
            du = abs(u - 0.5)
            dv = abs(v - 0.5)
            dist = du * du + dv * dv
            if charge >= 1.0:
                # Fully charged — bright pulsing green
                tp = 0.8 + 0.2 * math.sin(self.time * 4.0)
                if dist < 0.1:
                    return (int(80 * tp), int(255 * tp), int(120 * tp))
                return (int(40 * tp), int(200 * tp), int(80 * tp))
            elif charge > 0.01:
                # Charging — interpolate from dim to bright based on charge
                c = charge
                if dist < 0.1:
                    return (int(60 + 40 * c), int(90 + 165 * c), int(60 + 60 * c))
                return (int(40 + 30 * c), int(70 + 130 * c), int(50 + 30 * c))
            else:
                # Uncharged — dim green ring
                if dist < 0.06:
                    return (100, 130, 100)
                if dist < 0.15:
                    return (70, 100, 70)
                return TARGET_UNLIT

        return STONE_COLOR

    def _draw_mirror_sprites(self):
        """Draw mirrors as small prism-on-log columns."""
        cos_pa = math.cos(self.pa)
        sin_pa = math.sin(self.pa)

        # Collect visible mirrors with depth
        sprites = []
        for y in range(self.map_h):
            for x in range(self.map_w):
                cell = self.map[y][x]
                if cell not in MIRROR_TYPES:
                    continue
                dx = x + 0.5 - self.px
                dy = y + 0.5 - self.py
                vz = dx * cos_pa + dy * sin_pa
                if vz <= 0.1:
                    continue
                vx = -dx * sin_pa + dy * cos_pa
                sprites.append((vz, vx, x, y, cell))

        # Sort back to front
        sprites.sort(key=lambda s: -s[0])

        for vz, vx, mx, my, cell in sprites:
            sx_center = int(HALF + vx * GRID_SIZE / vz)

            # Sprite size — prism top reaches laser height (eye level)
            sprite_w = max(2, int(0.15 * GRID_SIZE / vz))
            sprite_h = max(4, int(0.55 * GRID_SIZE / vz))

            # Anchored to floor
            sy_floor = int(HALF + 0.5 * GRID_SIZE / vz)
            sy_top = sy_floor - sprite_h
            sx_start = sx_center - sprite_w // 2

            fog = min(1.0, 2.5 / (vz + 0.5))

            # Animation state
            anim = self.mirror_anims.get((mx, my))
            if anim:
                glow = 1.0
            else:
                glow = 0.8 + 0.2 * math.sin(self.time * 2.0)

            log_start = sy_top + max(1, int(sprite_h * 0.55))

            for sx in range(sx_start, sx_start + sprite_w):
                if sx < 0 or sx >= GRID_SIZE:
                    continue
                if vz > self.zbuf[sx]:
                    continue

                for sy in range(max(0, sy_top), min(GRID_SIZE, sy_floor)):
                    if sy >= log_start:
                        # Log base (dark wood)
                        r = int(65 * fog)
                        g = int(40 * fog)
                        b = int(18 * fog)
                    else:
                        # Glass prism
                        r = int(170 * glow * fog)
                        g = int(195 * glow * fog)
                        b = min(255, int(235 * glow * fog))
                    self.display.set_pixel(sx, sy, (r, g, b))

    def _draw_laser_beams(self):
        cos_pa = math.cos(self.pa)
        sin_pa = math.sin(self.pa)

        for x1, y1, x2, y2 in self.beam_segments:
            pts = []
            for bx, by in [(x1, y1), (x2, y2)]:
                dx = bx - self.px
                dy = by - self.py
                vz = dx * cos_pa + dy * sin_pa
                vx = -dx * sin_pa + dy * cos_pa
                pts.append((vx, vz))

            if pts[0][1] <= 0.05 and pts[1][1] <= 0.05:
                continue

            # More steps for longer segments
            seg_len = max(abs(x2 - x1), abs(y2 - y1))
            steps = max(16, int(seg_len * 20))
            for i in range(steps + 1):
                t = i / steps
                vx = pts[0][0] * (1 - t) + pts[1][0] * t
                vz = pts[0][1] * (1 - t) + pts[1][1] * t
                if vz <= 0.05:
                    continue

                sx = int(HALF + vx * GRID_SIZE / vz)
                # Beam at wall midpoint (eye height)
                sy = HALF

                if sx < 0 or sx >= GRID_SIZE:
                    continue
                if vz > self.zbuf[sx]:
                    continue
                if sy < 0 or sy >= GRID_SIZE:
                    continue

                # 1px core
                self.display.set_pixel(sx, sy, LASER_CORE)

                # Subtle glow ±1
                for gy in (-1, 1):
                    gsy = sy + gy
                    if 0 <= gsy < GRID_SIZE:
                        pr, pg, pb = self.display.get_pixel(sx, gsy)
                        nr = min(255, pr + LASER_GLOW[0] * 2)
                        ng = min(255, pg + LASER_GLOW[1] * 2)
                        nb = min(255, pb + LASER_GLOW[2] * 2)
                        self.display.set_pixel(sx, gsy, (nr, ng, nb))

    def _draw_hints(self):
        alpha = min(1.0, self.hint_timer / 0.8)
        # Dark band
        y0, y1 = 18, 48
        if self.level > 0:
            y0, y1 = 22, 42
        for y in range(y0, y1):
            for x in range(GRID_SIZE):
                pr, pg, pb = self.display.get_pixel(x, y)
                f = 1.0 - 0.7 * alpha
                self.display.set_pixel(x, y, (int(pr * f), int(pg * f), int(pb * f)))

        c = (int(220 * alpha), int(220 * alpha), int(240 * alpha))
        h = (int(160 * alpha), int(180 * alpha), int(160 * alpha))

        if self.level == 0:
            self.display.draw_text_small(2, 20, "ARROWS:MOVE", c)
            self.display.draw_text_small(2, 28, "SPC:ROTATE", c)
            self.display.draw_text_small(2, 36, "LIGHT TARGETS", h)
            self.display.draw_text_small(2, 44, "WITH THE BEAM", h)
        else:
            self.display.draw_text_small(2, 24, f"LEVEL {self.level + 1}", c)
            n_targets = len(self.targets)
            n_mirrors = sum(1 for row in self.map for c in row if c in MIRROR_TYPES)
            self.display.draw_text_small(2, 32, f"{n_mirrors}M {n_targets}T", h)
            self.display.draw_text_small(2, 38, "SPC:ROTATE", h)

    def _draw_title(self):
        self.display.clear((10, 12, 25))
        beam_y = 28
        beam_x = int((self.time * 40) % 80) - 10
        for x in range(max(0, beam_x - 30), min(64, beam_x)):
            fade = max(0.2, 1.0 - (beam_x - x) / 30.0)
            r = int(255 * fade)
            g = int(80 * fade)
            self.display.set_pixel(x, beam_y, (r, g, 20))

        self.display.draw_text_small(10, 14, "LASER", LASER_CORE)
        self.display.draw_text_small(6, 22, "MIRRORS", MIRROR_COLOR)
        self.display.draw_text_small(2, 38, "ROTATE MIRRORS", (100, 120, 140))
        self.display.draw_text_small(2, 46, "REDIRECT BEAM", (100, 120, 140))
        if int(self.time * 3) % 2 == 0:
            self.display.draw_text_small(6, 57, "PRESS START", Colors.ORANGE)

    def _draw_win(self):
        self.display.clear((10, 15, 10))
        self.display.draw_text_small(6, 14, "ALL CLEAR", TARGET_LIT)
        self.display.draw_text_small(2, 26, "WELL DONE!", Colors.WHITE)
        self.display.draw_text_small(2, 38, f"SCORE:{self.score}", Colors.YELLOW)

    def _draw_level_clear(self):
        self.display.clear((10, 15, 10))
        self.display.draw_text_small(2, 10, f"LEVEL {self.level + 1}", Colors.GREEN)
        self.display.draw_text_small(2, 20, "CLEAR!", TARGET_LIT)
        lvl = LEVELS[self.level]
        time_bonus = max(0, lvl['par'] - self.level_elapsed) * 10
        self.display.draw_text_small(2, 32, "BASE:100", Colors.WHITE)
        self.display.draw_text_small(2, 40, f"TIME:+{int(time_bonus)}", Colors.YELLOW)
        self.display.draw_text_small(2, 52, f"TOTAL:{self.score}", Colors.ORANGE)

    def draw_game_over(self, selection: int = 0):
        if self.phase == 'won':
            self._draw_win()
        else:
            self.display.clear(Colors.BLACK)
            self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
            self.display.draw_text_small(2, 32, f"SCORE:{self.score}", Colors.WHITE)

        if selection == 0:
            self.display.draw_text_small(2, 54, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 54, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 54, ">MENU", Colors.YELLOW)

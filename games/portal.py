"""
PORTAL — Aperture Science Testing Initiative
=============================================
Portal-inspired first-person raycaster for the 64x64 LED arcade.
Navigate procedurally-selected test chambers using the portal gun.
Reach the exit before time runs out. Avoid turrets and toxic goo.

Controls:
  Left/Right  - Rotate view
  Up/Down     - Move forward/backward
  Left Btn    - Shoot blue portal
  Right Btn   - Shoot orange portal
"""

import math
import random
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

# ═══════════════════════════════════════════════════════════════════
#  Constants
# ═══════════════════════════════════════════════════════════════════

FOV = math.pi / 3  # 60 degree FOV
HALF = GRID_SIZE // 2
MOVE_SPEED = 2.8
ROT_SPEED = 2.8
MARGIN = 0.2
WALL_HEIGHT = 2.0

# Portal colors
BLUE_PORTAL = (40, 140, 255)
ORANGE_PORTAL = (255, 160, 40)

# Wall types
W = 1   # concrete (non-portalable)
P = 2   # white panel (portalable)
TW = 3  # turret wall

# Floor mark types
GOO = 1
EXIT_MARK = 2

# Face directions: N=0, E=1, S=2, W=3
FACE_DX = [0, 1, 0, -1]
FACE_DY = [-1, 0, 1, 0]

# GLaDOS quips between rooms
_QUIPS = [
    "BEGIN TESTING", "THINK WITH PORTALS", "IMPRESSIVE",
    "FOR SCIENCE", "YOU SURVIVED", "THE CAKE AWAITS",
    "WELL DONE", "STILL ALIVE", "SPEEDY THING",
    "REMARKABLE", "NOT BAD", "KEEP GOING",
]


# ═══════════════════════════════════════════════════════════════════
#  Room Templates
# ═══════════════════════════════════════════════════════════════════

def _parse_room(lines):
    """Parse room template strings into cell grid and floor marks."""
    cells = []
    marks = {}
    for y, line in enumerate(lines):
        row = []
        for x, ch in enumerate(line):
            if ch == 'W':
                row.append(W)
            elif ch == 'P':
                row.append(P)
            elif ch == 'T':
                row.append(TW)
            elif ch == 'G':
                row.append(0)
                marks[(x, y)] = GOO
            else:  # '.' or anything else = floor
                row.append(0)
        cells.append(row)
    return cells, marks


# Each room: map lines (12x12), entry (x, y, angle), exit (x, y),
# turret defs, time limit, and a GLaDOS quip.

_ROOM_DEFS = [
    # ── Room 0: Welcome ── Just walk to the exit. Learn controls.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'W..........W',
            'W..........W',
            'W..........W',
            'W..........W',
            'W..........W',
            'W..........W',
            'W..........W',
            'W..........W',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (2, 9, -math.pi / 2),   # facing north
        'exit': (9, 2),
        'turrets': [],
        'time': 15,
        'quip': 'BEGIN TESTING',
    },

    # ── Room 1: Portal 101 ── Goo divides room. Portal across.
    # P panels on east/west walls on both sides of goo.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'P..........P',
            'W..........W',
            'W..........W',
            'WGGGGGGGGGGW',
            'WGGGGGGGGGGW',
            'W..........W',
            'W..........W',
            'P..........P',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (5, 9, -math.pi / 2),
        'exit': (5, 2),
        'turrets': [],
        'time': 40,
        'quip': 'THINK WITH PORTALS',
    },

    # ── Room 2: The Divide ── Wall splits room, P panels to portal through.
    # Gap at top lets you SEE across but goo blocks walking.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'W....GG....W',
            'W....GG....W',
            'W....PP....W',
            'W....PP....W',
            'W....PP....W',
            'W....PP....W',
            'W....PP....W',
            'W....PP....W',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (2, 9, -math.pi / 2),
        'exit': (9, 2),
        'turrets': [],
        'time': 35,
        'quip': 'IMPRESSIVE',
    },

    # ── Room 3: Turret Alley ── Turret guards the direct path.
    # Portal past it using side walls.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'W..........W',
            'P..........P',
            'W..........W',
            'W..........W',
            'W....T.....W',
            'W..........W',
            'W..........W',
            'P..........P',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (2, 10, -math.pi / 2),
        'exit': (9, 1),
        'turrets': [
            {'x': 5, 'y': 5, 'dx': 0, 'dy': 1, 'rate': 2.5, 'warn': 0.6},
        ],
        'time': 30,
        'quip': 'TURRETS DEPLOYED',
    },

    # ── Room 4: Goo Bridge ── Wide goo field, P walls on far sides.
    # Must portal across a large gap.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'W..........W',
            'P..........P',
            'WGGGGGGGGGGW',
            'WGGGGGGGGGGW',
            'WGGGGGGGGGGW',
            'WGGGGGGGGGGW',
            'P..........P',
            'W..........W',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (5, 9, -math.pi / 2),
        'exit': (5, 1),
        'turrets': [],
        'time': 35,
        'quip': 'MIND THE GOO',
    },

    # ── Room 5: Crossfire ── Two turrets, need to portal around both.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'W..........W',
            'P..........P',
            'W..........W',
            'W.T........W',
            'W..........W',
            'W..........W',
            'W........T.W',
            'P..........P',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (2, 10, -math.pi / 2),
        'exit': (9, 1),
        'turrets': [
            {'x': 2, 'y': 4, 'dx': 1, 'dy': 0, 'rate': 2.0, 'warn': 0.5},
            {'x': 9, 'y': 7, 'dx': -1, 'dy': 0, 'rate': 2.5, 'warn': 0.5},
        ],
        'time': 30,
        'quip': 'THIS IS YOUR FAULT',
    },

    # ── Room 6: Zigzag ── Multiple walls force winding path. Portals shortcut.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'W..........W',
            'W..........W',
            'WWWWWWWWPP.W',
            'W..........W',
            'W..........W',
            'W.PPWWWWWWWW',
            'W..........W',
            'W..........W',
            'WWWWWWWWPP.W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (9, 10, -math.pi / 2),
        'exit': (9, 1),
        'turrets': [],
        'time': 25,
        'quip': 'EFFICIENCY MATTERS',
    },

    # ── Room 7: Gauntlet ── Goo + turret combo.
    {
        'lines': [
            'WWWWWWWWWWWW',
            'W..........W',
            'P..........P',
            'W..........W',
            'WGGGGGGGGGGW',
            'WGGGGGGGGGGW',
            'W..........W',
            'P....T.....P',
            'W..........W',
            'W..........W',
            'W..........W',
            'WWWWWWWWWWWW',
        ],
        'entry': (5, 9, -math.pi / 2),
        'exit': (5, 1),
        'turrets': [
            {'x': 5, 'y': 7, 'dx': 0, 'dy': -1, 'rate': 2.0, 'warn': 0.5},
        ],
        'time': 35,
        'quip': 'FOR SCIENCE',
    },
]


# ═══════════════════════════════════════════════════════════════════
#  Game Class
# ═══════════════════════════════════════════════════════════════════

class Portal(Game):
    name = "PORTAL"
    description = "Aperture Science"
    category = "modern"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.time = 0.0

        # Phase: 'title', 'playing', 'transition', 'falling', 'dead'
        self.phase = 'title'
        self.phase_timer = 2.5

        # Chamber progression
        self.chamber = 0
        self.room_order = list(range(len(_ROOM_DEFS)))
        self.round_num = 0  # how many times we've cycled through all rooms

        # Player
        self.px = 5.0
        self.py = 5.0
        self.pa = 0.0
        self.elevation = 0.0

        # Ray offsets (precomputed)
        self.ray_offsets = [(col / GRID_SIZE - 0.5) * FOV for col in range(GRID_SIZE)]

        # Current room state
        self.map = []
        self.map_w = 12
        self.map_h = 12
        self.floor_marks = {}

        # Portals: None or (cell_x, cell_y, face, height)
        self.blue_portal = None
        self.orange_portal = None
        self.portal_cooldown = 0.0

        # Shoot animation
        self.shoot_flash = 0.0
        self.shoot_color = None

        # Turrets + bullets
        self.turrets = []
        self.bullets = []

        # Death
        self.fall_timer = 0.0
        self.dead_timer = 0.0
        self.death_cause = None

        # Room timer
        self.room_timer = 0.0

        # Transition state
        self.trans_quip = ''
        self.trans_chamber = 0

    # ─────────────────────────────────────────────────────────────
    #  Room management
    # ─────────────────────────────────────────────────────────────

    def _load_room(self, room_idx):
        """Load a room template into the active map."""
        defn = _ROOM_DEFS[room_idx]
        self.map, self.floor_marks = _parse_room(defn['lines'])
        self.map_h = len(self.map)
        self.map_w = len(self.map[0]) if self.map else 12

        # Mark exit
        ex, ey = defn['exit']
        self.floor_marks[(ex, ey)] = EXIT_MARK
        self.exit_pos = (ex, ey)

        # Player spawn
        px, py, pa = defn['entry']
        self.px = px + 0.5
        self.py = py + 0.5
        self.pa = pa

        # Reset portals
        self.blue_portal = None
        self.orange_portal = None
        self.portal_cooldown = 0.0

        # Timer (tighter each round)
        base_time = defn['time']
        reduction = self.round_num * 3
        self.room_timer = max(10, base_time - reduction)

        # Turrets
        self.turrets = []
        for td in defn['turrets']:
            self.turrets.append({
                'x': td['x'], 'y': td['y'],
                'dx': td['dx'], 'dy': td['dy'],
                'rate': td['rate'], 'warn': td['warn'],
                'timer': td['rate'],
            })
        self.bullets = []

    def _next_room(self):
        """Advance to next chamber."""
        idx_in_order = self.chamber % len(self.room_order)
        if idx_in_order == 0 and self.chamber > 0:
            # New round — reshuffle and tighten timers
            self.round_num += 1
            random.shuffle(self.room_order)
        room_idx = self.room_order[idx_in_order]
        self._load_room(room_idx)

    # ─────────────────────────────────────────────────────────────
    #  Map helpers
    # ─────────────────────────────────────────────────────────────

    def _cell(self, x, y):
        if x < 0 or x >= self.map_w or y < 0 or y >= self.map_h:
            return W
        return self.map[y][x]

    def _is_wall(self, x, y):
        return self._cell(x, y) != 0

    def _is_portalable(self, x, y):
        return self._cell(x, y) == P

    def _solid(self, x, y):
        for dx in (-MARGIN, MARGIN):
            for dy in (-MARGIN, MARGIN):
                if self._is_wall(int(x + dx), int(y + dy)):
                    return True
        return False

    # ─────────────────────────────────────────────────────────────
    #  Portal system
    # ─────────────────────────────────────────────────────────────

    def _shoot_portal(self, color):
        """Cast ray and place portal on first portalable wall hit."""
        cos_a = math.cos(self.pa)
        sin_a = math.sin(self.pa)
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
            if self._cell(map_x, map_y) != 0:
                if self._is_portalable(map_x, map_y):
                    if side == 0:
                        face = 3 if step_x > 0 else 1
                    else:
                        face = 0 if step_y > 0 else 2
                    portal = (map_x, map_y, face, 0.0)
                    if color == 'blue':
                        if self.orange_portal != portal:
                            self.blue_portal = portal
                    else:
                        if self.blue_portal != portal:
                            self.orange_portal = portal
                    self.shoot_flash = 0.15
                    self.shoot_color = BLUE_PORTAL if color == 'blue' else ORANGE_PORTAL
                break

    def _has_portal(self, cell_x, cell_y, face):
        if self.blue_portal and self.blue_portal[:3] == (cell_x, cell_y, face):
            return ('blue', self.blue_portal[3])
        if self.orange_portal and self.orange_portal[:3] == (cell_x, cell_y, face):
            return ('orange', self.orange_portal[3])
        return None

    def _get_exit_portal(self, color):
        return self.orange_portal if color == 'blue' else self.blue_portal

    def _try_portal_traverse(self):
        if self.portal_cooldown > 0:
            return
        if not self.blue_portal or not self.orange_portal:
            return

        for color, portal in [('blue', self.blue_portal), ('orange', self.orange_portal)]:
            cx, cy, face, _ = portal
            if face == 0:
                portal_y = cy
                if abs(self.py - portal_y) < 0.5 and abs(self.px - (cx + 0.5)) < 0.8:
                    if math.sin(self.pa) > 0.1:
                        self._do_teleport(color)
                        return
            elif face == 2:
                portal_y = cy + 1
                if abs(self.py - portal_y) < 0.5 and abs(self.px - (cx + 0.5)) < 0.8:
                    if math.sin(self.pa) < -0.1:
                        self._do_teleport(color)
                        return
            elif face == 3:
                portal_x = cx
                if abs(self.px - portal_x) < 0.5 and abs(self.py - (cy + 0.5)) < 0.8:
                    if math.cos(self.pa) > 0.1:
                        self._do_teleport(color)
                        return
            elif face == 1:
                portal_x = cx + 1
                if abs(self.px - portal_x) < 0.5 and abs(self.py - (cy + 0.5)) < 0.8:
                    if math.cos(self.pa) < -0.1:
                        self._do_teleport(color)
                        return

    def _do_teleport(self, entry_color):
        exit_portal = self._get_exit_portal(entry_color)
        if not exit_portal:
            return
        ex, ey, eface, _ = exit_portal
        if eface == 0:
            self.px = ex + 0.5
            self.py = ey - 0.7
        elif eface == 2:
            self.px = ex + 0.5
            self.py = ey + 1.7
        elif eface == 3:
            self.px = ex - 0.7
            self.py = ey + 0.5
        elif eface == 1:
            self.px = ex + 1.7
            self.py = ey + 0.5
        odx = FACE_DX[eface]
        ody = FACE_DY[eface]
        self.pa = math.atan2(ody, odx)
        self.portal_cooldown = 0.4

    # ─────────────────────────────────────────────────────────────
    #  Turrets + Bullets
    # ─────────────────────────────────────────────────────────────

    def _update_turrets(self, dt):
        for t in self.turrets:
            t['timer'] -= dt
            if t['timer'] <= 0:
                t['timer'] = t['rate']
                self.bullets.append({
                    'x': float(t['x']) + 0.5 + t['dx'] * 0.6,
                    'y': float(t['y']) + 0.5 + t['dy'] * 0.6,
                    'dx': t['dx'], 'dy': t['dy'],
                    'speed': 6.0, 'life': 3.0,
                })

    def _update_bullets(self, dt):
        alive = []
        for b in self.bullets:
            b['x'] += b['dx'] * b['speed'] * dt
            b['y'] += b['dy'] * b['speed'] * dt
            b['life'] -= dt
            bx, by = int(b['x']), int(b['y'])
            if self._is_wall(bx, by):
                continue
            if b['life'] <= 0:
                continue
            dx = b['x'] - self.px
            dy = b['y'] - self.py
            if dx * dx + dy * dy < 0.3 * 0.3:
                self.death_cause = 'turret'
                self.phase = 'falling'
                self.fall_timer = 1.0
                self.bullets = []
                return
            alive.append(b)
        self.bullets = alive

    # ─────────────────────────────────────────────────────────────
    #  Update
    # ─────────────────────────────────────────────────────────────

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.time += dt

        if self.phase == 'title':
            self.phase_timer -= dt
            if self.phase_timer <= 0 or input_state.action_l or input_state.action_r:
                self.phase = 'transition'
                self.phase_timer = 1.5
                self.trans_quip = 'BEGIN TESTING'
                self.trans_chamber = 1
            return

        if self.phase == 'transition':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self._next_room()
                self.phase = 'playing'
            return

        if self.phase == 'falling':
            self.fall_timer -= dt
            self.elevation -= 3.0 * dt
            if self.fall_timer <= 0:
                self.phase = 'dead'
                self.dead_timer = 2.0
            return

        if self.phase == 'dead':
            self.dead_timer -= dt
            if self.dead_timer <= 0:
                self.state = GameState.GAME_OVER
            return

        # ── Playing ──

        # Timers
        if self.portal_cooldown > 0:
            self.portal_cooldown -= dt
        if self.shoot_flash > 0:
            self.shoot_flash -= dt

        # Room timer
        self.room_timer -= dt
        if self.room_timer <= 0:
            self.room_timer = 0
            self.death_cause = 'timeout'
            self.phase = 'falling'
            self.fall_timer = 1.0
            return

        # Portal shooting
        if input_state.action_l:
            self._shoot_portal('blue')
        if input_state.action_r:
            self._shoot_portal('orange')

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

        if input_state.left:
            self.pa -= ROT_SPEED * dt
        if input_state.right:
            self.pa += ROT_SPEED * dt

        # Collision
        if not self._solid(nx, self.py):
            self.px = nx
        if not self._solid(self.px, ny):
            self.py = ny

        # Goo check
        pcx, pcy = int(self.px), int(self.py)
        if self.floor_marks.get((pcx, pcy)) == GOO:
            self.death_cause = 'goo'
            self.phase = 'falling'
            self.fall_timer = 1.0
            return

        # Portal traversal
        self._try_portal_traverse()

        # Turrets
        if self.turrets:
            self._update_turrets(dt)
            self._update_bullets(dt)

        # Exit check
        pcx, pcy = int(self.px), int(self.py)
        if self.floor_marks.get((pcx, pcy)) == EXIT_MARK:
            # Room cleared!
            time_bonus = int(self.room_timer * (self.chamber + 1))
            base_pts = 100 + self.chamber * 50
            self.score += base_pts + time_bonus
            self.chamber += 1

            # Transition to next room
            room_idx = self.chamber % len(self.room_order)
            if room_idx < len(_ROOM_DEFS):
                quip = _ROOM_DEFS[self.room_order[room_idx % len(self.room_order)]]['quip']
            else:
                quip = random.choice(_QUIPS)
            self.trans_quip = quip
            self.trans_chamber = self.chamber + 1
            self.phase = 'transition'
            self.phase_timer = 1.5
            self.elevation = 0.0

    # ─────────────────────────────────────────────────────────────
    #  Raycaster + Drawing
    # ─────────────────────────────────────────────────────────────

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == 'title':
            self._draw_title()
            return

        if self.phase == 'transition':
            self._draw_transition()
            return

        if self.phase == 'dead':
            self._draw_dead()
            return

        # Render 3D view
        eye_h = self.elevation + 0.5
        for col in range(GRID_SIZE):
            ray_angle = self.pa + self.ray_offsets[col]
            self._cast_ray(col, ray_angle, eye_h)

        # Bullets
        if self.bullets:
            self._draw_bullets()

        # Falling overlay
        if self.phase == 'falling':
            alpha = min(1.0, 1.0 - self.fall_timer)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    pr, pg, pb = self.display.get_pixel(x, y)
                    pr = min(255, int(pr + 120 * alpha))
                    pg = int(pg * (1.0 - alpha * 0.7))
                    pb = int(pb * (1.0 - alpha * 0.7))
                    self.display.set_pixel(x, y, (pr, pg, pb))
            return

        # Shoot flash
        if self.shoot_flash > 0 and self.shoot_color:
            alpha = self.shoot_flash / 0.15
            r0, g0, b0 = self.shoot_color
            for x in range(28, 36):
                for y in range(28, 36):
                    pr, pg, pb = self.display.get_pixel(x, y)
                    self.display.set_pixel(x, y, (
                        min(255, int(pr + r0 * alpha * 0.5)),
                        min(255, int(pg + g0 * alpha * 0.5)),
                        min(255, int(pb + b0 * alpha * 0.5)),
                    ))

        # Portal HUD indicators
        if self.blue_portal:
            self.display.set_pixel(1, 1, BLUE_PORTAL)
            self.display.set_pixel(2, 1, BLUE_PORTAL)
            self.display.set_pixel(1, 2, BLUE_PORTAL)
        if self.orange_portal:
            self.display.set_pixel(62, 1, ORANGE_PORTAL)
            self.display.set_pixel(61, 1, ORANGE_PORTAL)
            self.display.set_pixel(62, 2, ORANGE_PORTAL)

        # Crosshair
        ch = (150, 150, 150)
        self.display.set_pixel(31, 32, ch)
        self.display.set_pixel(32, 32, ch)
        self.display.set_pixel(31, 31, ch)
        self.display.set_pixel(32, 31, ch)

        # Timer HUD
        secs = int(self.room_timer) + 1
        txt = str(secs)
        if secs <= 5:
            tc = Colors.RED
        elif secs <= 10:
            tc = Colors.ORANGE
        else:
            tc = Colors.WHITE
        tx = 63 - len(txt) * 4
        self.display.draw_text_small(tx, 5, txt, tc)

        # Score
        self.display.draw_text_small(2, 5, str(self.score), Colors.YELLOW)

        # Chamber number
        ch_txt = f"CH{self.chamber + 1}"
        self.display.draw_text_small(24, 1, ch_txt, (100, 100, 110))

        # Minimap
        self._draw_minimap()

    def _cast_ray(self, col, angle, eye_h):
        """DDA raycaster — renders one column."""
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

        hit = False
        side = 0
        hit_cell = 0
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
            if cell != 0:
                hit = True
                hit_cell = cell
                break

        if not hit:
            for y in range(HALF):
                self.display.set_pixel(col, y, (30, 30, 45))
            for y in range(HALF, GRID_SIZE):
                self._floor_pixel(col, y, cos_a, sin_a, eye_h)
            return

        # Perpendicular distance
        if side == 0:
            perp_dist = (map_x - self.px + (1 - step_x) / 2) / cos_a
        else:
            perp_dist = (map_y - self.py + (1 - step_y) / 2) / sin_a
        if perp_dist < 0.01:
            perp_dist = 0.01

        wh = WALL_HEIGHT
        scale = GRID_SIZE / perp_dist
        screen_top = int(HALF - wh * scale / 2)
        screen_bot = int(HALF + wh * scale / 2)
        draw_start = max(0, screen_top)
        draw_end = min(GRID_SIZE - 1, screen_bot)
        line_height = max(1, screen_bot - screen_top)

        # Texture u
        if side == 0:
            wall_x = self.py + perp_dist * sin_a
        else:
            wall_x = self.px + perp_dist * cos_a
        wall_x -= int(wall_x)

        # Fog + side shading
        fog = min(1.0, 2.5 / (perp_dist + 0.5))
        if side == 1:
            fog *= 0.75

        # Portal check
        if side == 0:
            face = 3 if step_x > 0 else 1
        else:
            face = 0 if step_y > 0 else 2
        portal_info = None
        portal_hit = self._has_portal(map_x, map_y, face)
        if portal_hit and wh > 0:
            p_color, p_height = portal_hit
            pv_top = max(0.0, (wh - (p_height + 1.0)) / wh)
            pv_bot = min(1.0, (wh - p_height) / wh)
            portal_info = (p_color, pv_top, pv_bot)

        # Ceiling
        for y in range(0, draw_start):
            self.display.set_pixel(col, y, (30, 30, 45))

        # Wall
        for y in range(draw_start, draw_end + 1):
            v = (y - screen_top) / line_height if line_height > 0 else 0.5
            r, g, b = self._wall_pixel(hit_cell, wall_x, v, portal_info)
            self.display.set_pixel(col, y, (int(r * fog), int(g * fog), int(b * fog)))

        # Floor
        for y in range(draw_end + 1, GRID_SIZE):
            self._floor_pixel(col, y, cos_a, sin_a, eye_h)

    def _floor_pixel(self, col, y, cos_a, sin_a, eye_h):
        """Render one floor pixel with floor casting."""
        p = y - HALF
        if p <= 0:
            self.display.set_pixel(col, y, (13, 10, 8))
            return
        row_dist = eye_h * GRID_SIZE / p
        if row_dist <= 0:
            self.display.set_pixel(col, y, (5, 2, 2))
            return
        fx = self.px + cos_a * row_dist
        fy = self.py + sin_a * row_dist
        fcx, fcy = int(fx), int(fy)
        mark = self.floor_marks.get((fcx, fcy))
        fog_f = min(1.0, 2.0 / (row_dist + 0.5))
        if mark == GOO:
            # Toxic green goo — bright and pulsing
            pulse = 0.8 + 0.2 * math.sin(self.time * 6.0 + fx * 2)
            r = int(30 * fog_f * pulse)
            g = int(200 * fog_f * pulse)
            b = int(40 * fog_f * pulse)
        elif mark == EXIT_MARK:
            pulse = 0.7 + 0.3 * math.sin(self.time * 4.0)
            r = int(30 * fog_f * pulse)
            g = int(220 * fog_f * pulse)
            b = int(30 * fog_f * pulse)
        else:
            checker = (fcx + fcy) % 2
            base = 45 if checker == 0 else 35
            r = int((base + 5) * fog_f)
            g = int((base + 2) * fog_f)
            b = int(base * fog_f)
        self.display.set_pixel(col, y, (r, g, b))

    def _wall_pixel(self, cell_type, u, v, portal_info):
        """Get wall pixel color."""
        # Portal rendering
        if portal_info:
            p_color, pv_top, pv_bot = portal_info
            pv_center = (pv_top + pv_bot) * 0.5
            pv_half = (pv_bot - pv_top) * 0.5
            if pv_half > 0.01 and 0.2 <= u <= 0.8 and pv_top + 0.02 <= v <= pv_bot - 0.02:
                du = (u - 0.5) / 0.3
                dv = (v - pv_center) / (pv_half * 0.85)
                if du * du + dv * dv <= 1.0:
                    base = BLUE_PORTAL if p_color == 'blue' else ORANGE_PORTAL
                    dist = du * du + dv * dv
                    if dist > 0.7:
                        return (min(255, base[0] + 80),
                                min(255, base[1] + 80),
                                min(255, base[2] + 80))
                    return base

        if cell_type == P:
            # White Aperture panels — bright and clean
            r, g, b = 200, 200, 210
            pu = int(u * 4)
            pv = int(v * 4)
            fu = u * 4 - pu
            fv = v * 4 - pv
            if fu < 0.08 or fu > 0.92 or fv < 0.08 or fv > 0.92:
                return (170, 170, 180)
            return (r, g, b)

        if cell_type == TW:
            # Turret wall — gray with pulsing red eye
            if 0.3 <= u <= 0.7 and 0.25 <= v <= 0.45:
                pulse = 0.5 + 0.5 * math.sin(self.time * 8.0)
                r = int(180 + 75 * pulse)
                return (r, 10, 10)
            if u < 0.05 or u > 0.95 or v < 0.05 or v > 0.95:
                return (50, 50, 55)
            return (80, 80, 90)

        # Concrete (default) — dark
        r, g, b = 90, 90, 100
        gu = int(u * 8)
        gv = int(v * 8)
        fu = u * 8 - gu
        fv = v * 8 - gv
        if fu < 0.06 or fv < 0.06:
            return (70, 70, 80)
        return (r, g, b)

    # ─────────────────────────────────────────────────────────────
    #  Minimap
    # ─────────────────────────────────────────────────────────────

    def _draw_minimap(self):
        """Draw small minimap in bottom-left corner."""
        ox, oy = 1, GRID_SIZE - self.map_h - 1  # offset on screen

        for my in range(self.map_h):
            for mx in range(self.map_w):
                sx = ox + mx
                sy = oy + my
                if sx >= GRID_SIZE or sy >= GRID_SIZE:
                    continue
                cell = self._cell(mx, my)
                mark = self.floor_marks.get((mx, my))
                if cell == P:
                    color = (140, 140, 150)  # white panels
                elif cell == TW:
                    color = (120, 30, 30)  # turret
                elif cell != 0:
                    color = (50, 50, 55)  # concrete
                elif mark == GOO:
                    color = (15, 80, 20)  # goo
                elif mark == EXIT_MARK:
                    pulse = 0.6 + 0.4 * math.sin(self.time * 4.0)
                    g = int(180 * pulse)
                    color = (20, g, 20)
                else:
                    color = (15, 12, 10)  # floor
                self.display.set_pixel(sx, sy, color)

        # Player dot
        pmx = ox + int(self.px)
        pmy = oy + int(self.py)
        if 0 <= pmx < GRID_SIZE and 0 <= pmy < GRID_SIZE:
            self.display.set_pixel(pmx, pmy, Colors.WHITE)
        # Direction indicator
        pdx = int(self.px + math.cos(self.pa) * 1.2)
        pdy = int(self.py + math.sin(self.pa) * 1.2)
        ddx = ox + pdx
        ddy = oy + pdy
        if 0 <= ddx < GRID_SIZE and 0 <= ddy < GRID_SIZE:
            self.display.set_pixel(ddx, ddy, (200, 200, 100))

        # Portal dots
        if self.blue_portal:
            bx = ox + self.blue_portal[0]
            by = oy + self.blue_portal[1]
            if 0 <= bx < GRID_SIZE and 0 <= by < GRID_SIZE:
                self.display.set_pixel(bx, by, BLUE_PORTAL)
        if self.orange_portal:
            orx = ox + self.orange_portal[0]
            ory = oy + self.orange_portal[1]
            if 0 <= orx < GRID_SIZE and 0 <= ory < GRID_SIZE:
                self.display.set_pixel(orx, ory, ORANGE_PORTAL)

    # ─────────────────────────────────────────────────────────────
    #  Bullets in 3D
    # ─────────────────────────────────────────────────────────────

    def _draw_bullets(self):
        cos_a = math.cos(self.pa)
        sin_a = math.sin(self.pa)
        for b in self.bullets:
            dx = b['x'] - self.px
            dy = b['y'] - self.py
            vz = dx * cos_a + dy * sin_a
            vx = -dx * sin_a + dy * cos_a
            if vz <= 0.1:
                continue
            sx = int(HALF + vx * GRID_SIZE / vz)
            sy = HALF
            if 0 <= sx < GRID_SIZE - 1 and 0 <= sy < GRID_SIZE - 1:
                self.display.set_pixel(sx, sy, (255, 60, 30))
                self.display.set_pixel(sx + 1, sy, (255, 60, 30))
                self.display.set_pixel(sx, sy + 1, (255, 60, 30))
                self.display.set_pixel(sx + 1, sy + 1, (255, 60, 30))

    # ─────────────────────────────────────────────────────────────
    #  HUD screens
    # ─────────────────────────────────────────────────────────────

    def _draw_title(self):
        self.display.clear((10, 10, 15))
        cx, cy = 32, 20
        for a_deg in range(0, 360, 3):
            a_rad = math.radians(a_deg)
            px = int(cx + 10 * math.cos(a_rad))
            py = int(cy + 10 * math.sin(a_rad))
            self.display.set_pixel(px, py, (200, 200, 210))
        for i in range(3):
            a_rad = math.radians(i * 120 + self.time * 30)
            x1 = int(cx + 3 * math.cos(a_rad))
            y1 = int(cy + 3 * math.sin(a_rad))
            x2 = int(cx + 8 * math.cos(a_rad))
            y2 = int(cy + 8 * math.sin(a_rad))
            self.display.draw_line(x1, y1, x2, y2, (180, 180, 190))
        self.display.draw_text_small(14, 35, "PORTAL", Colors.WHITE)
        self.display.draw_text_small(2, 44, "APERTURE SCI", (150, 150, 160))
        if int(self.time * 3) % 2 == 0:
            self.display.draw_text_small(6, 55, "PRESS START", Colors.ORANGE)

    def _draw_transition(self):
        self.display.clear((10, 10, 15))
        # Chamber number
        ch_txt = f"CHAMBER {self.trans_chamber:02d}"
        self.display.draw_text_small(2, 22, ch_txt, Colors.WHITE)
        # GLaDOS quip
        self.display.draw_text_small(2, 34, self.trans_quip, Colors.ORANGE)
        # Score
        if self.score > 0:
            self.display.draw_text_small(2, 48, str(self.score), Colors.YELLOW)

    def _draw_dead(self):
        self.display.clear((40, 5, 5))
        self.display.draw_text_small(2, 12, "SUBJECT LOST", Colors.RED)
        if self.death_cause == 'goo':
            self.display.draw_text_small(2, 24, "TOXIC GOO", Colors.WHITE)
        elif self.death_cause == 'turret':
            self.display.draw_text_small(2, 24, "SHOT DOWN", Colors.WHITE)
        elif self.death_cause == 'timeout':
            self.display.draw_text_small(2, 24, "TIME UP", Colors.WHITE)
        self.display.draw_text_small(2, 40, f"CHAMBER {self.chamber + 1}", (150, 150, 150))
        if self.score > 0:
            self.display.draw_text_small(2, 50, str(self.score), Colors.YELLOW)

    def draw_game_over(self, selection: int = 0):
        self.display.clear((30, 5, 5))
        self.display.draw_text_small(2, 8, "TESTING", Colors.RED)
        self.display.draw_text_small(2, 16, "TERMINATED", Colors.RED)
        if self.death_cause == 'goo':
            self.display.draw_text_small(2, 28, "TOXIC GOO", Colors.WHITE)
        elif self.death_cause == 'turret':
            self.display.draw_text_small(2, 28, "SHOT DOWN", Colors.WHITE)
        elif self.death_cause == 'timeout':
            self.display.draw_text_small(2, 28, "TIME UP", Colors.WHITE)
        self.display.draw_text_small(2, 40, f"CHAMBER {self.chamber + 1}", (150, 150, 150))
        if self.score > 0:
            self.display.draw_text_small(2, 48, str(self.score), Colors.YELLOW)
        if selection == 0:
            self.display.draw_text_small(2, 58, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 58, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 58, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 58, ">MENU", Colors.YELLOW)

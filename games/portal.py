"""
PORTAL — First-Person Puzzle Game
===================================
Portal-inspired first-person raycaster for the 64x64 LED arcade.
DDA raycaster with wall portals, companion cube, pressure plates,
and GLaDOS messages.

Controls:
  Left/Right  - Rotate view
  Up/Down     - Move forward/backward
  Space       - Shoot blue portal
  Z           - Shoot orange portal
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
WALL_HEIGHT = 2.0  # walls are 2 units tall (encloses upper levels)

# Portal colors
BLUE_PORTAL = (40, 140, 255)
ORANGE_PORTAL = (255, 160, 40)

# Wall types
W = 1   # concrete (non-portalable)
P = 2   # white panel (portalable)
D = 3   # door (locked)
U = 4   # door (unlocked / auto-open)
S = 5   # stair low (0.25)
S2 = 6  # stair mid (0.5)
S3 = 7  # stair high (0.75)
H = 8   # high wall (elevation 1.0)
PH = 9  # portalable panel at high elevation
G = 10  # gap / pit (elevation -1.0)
PP = 11 # pressure plate (floor marker, not a wall)
CC = 12 # companion cube start position (floor)
EX = 13 # exit trigger
PIT = 14 # pit/gap floor marker (renders as void, player falls in)
T = 15   # turret wall (solid, non-portalable)

# Face directions: N=0, E=1, S=2, W=3
FACE_DX = [0, 1, 0, -1]
FACE_DY = [-1, 0, 1, 0]
# Outward normal for each face (direction pointing away from wall INTO open space)
# If portal is on North face of a wall cell, it faces North (into cell above)
# Player exits heading outward from the face

# ═══════════════════════════════════════════════════════════════════
#  Level Map — 24 wide x 41 tall
# ═══════════════════════════════════════════════════════════════════

MAP_W = 24

# Cell types determine wall rendering and collision
# 0 = open floor, other values = wall types above
# Special floor markers stored in a separate layer

_M = [
    # ── Chamber 00 — Wakeup (rows 0-5) ──
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 0
    [W,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 1
    [W,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 2
    [W,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 3
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 4
    [W,W,U,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 5

    # ── Chamber 01 — First Portal (rows 6-12) ──
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 6
    [W,P,0,P,P,P,P,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 7
    [W,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 8
    [W,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 9
    [W,P,0,P,P,P,P,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 10
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 11
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 12

    # ── Chamber 02 — Thinking with Portals (rows 13-19) ──
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 13
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 14
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 15
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 16
    [W,W,0,W,W,W,W,W,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 17
    [W,W,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 18
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 19

    # ── Chamber 03 — Mind the Gap (rows 20-27) ──
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 20
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 21
    [W,P,0,0,0,0,0,0,0,0,0,0,P,W,W,W,W,W,W,W,W,W,W,W],  # 22
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 23 PIT
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 24 PIT
    [W,P,0,0,0,0,0,0,0,0,0,0,P,W,W,W,W,W,W,W,W,W,W,W],  # 25
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 26
    [W,W,W,W,W,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 27

    # ── Chamber 04 — The Bridge (rows 28-42) ──
    # Three zones separated by 3-row PIT gaps with middle platform.
    # P walls on cols 1 and 12 visible across gaps.
    [W,W,W,W,W,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 28 entry
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 29 near floor
    [W,P,0,0,0,0,0,0,0,0,0,0,P,W,W,W,W,W,W,W,W,W,W,W],  # 30 near P walls
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 31 PIT
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 32 PIT
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 33 PIT
    [W,P,0,0,0,0,0,0,0,0,0,0,P,W,W,W,W,W,W,W,W,W,W,W],  # 34 platform P
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 35 platform floor
    [W,P,0,0,0,0,0,0,0,0,0,0,P,W,W,W,W,W,W,W,W,W,W,W],  # 36 platform P
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 37 PIT
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 38 PIT
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 39 PIT
    [W,P,0,0,0,0,0,0,0,0,0,0,P,W,W,W,W,W,W,W,W,W,W,W],  # 40 far P walls
    [W,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 41 far floor
    [W,W,W,W,W,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 42 exit south

    # ── Chamber 05 — Turret Alley (rows 43-50) ──
    [W,W,W,W,W,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 43 corridor
    [W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 44 narrows
    [W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 45 approach
    [W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 46
    [W,W,T,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 47 cross + turret
    [W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 48
    [W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 49
    [W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 50

    # ── Corridor to Cube Room (rows 51-54) ──
    [W,W,W,W,W,0,0,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W,W,W],  # 51
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,W,W,W,W,W],  # 52
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,W,W,W,W,W],  # 53
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,W,W,W,W,W],  # 54

    # ── Chamber 06 — Companion Cube (rows 55-59) ──
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,0,W,W,W],  # 55
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,0,W,W,W],  # 56
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,D,W,W,W],  # 57
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,0,0,W,W],  # 58
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 59
]

MAP_H = len(_M)

# Floor height map (elevation per cell, 0.0 = ground default)
_HEIGHTS = {}

# Floor markers (non-wall special cells)
_FLOOR_MARKS = {}
_FLOOR_MARKS[(18, 56)] = PP   # pressure plate in cube room
_FLOOR_MARKS[(21, 58)] = EX   # exit trigger (through door east)

# Pit floor marks for ch03 gap (rows 23-24, cols 1-12)
for _c in range(1, 13):
    _FLOOR_MARKS[(_c, 23)] = PIT
    _FLOOR_MARKS[(_c, 24)] = PIT

# Pit floor marks for ch04 bridge gaps (rows 31-33, 37-39, cols 1-12)
for _c in range(1, 13):
    for _r in (31, 32, 33, 37, 38, 39):
        _FLOOR_MARKS[(_c, _r)] = PIT

# EX marks for scored level exits
_FLOOR_MARKS[(7, 27)] = EX    # ch03 exit (Mind the Gap)
_FLOOR_MARKS[(7, 42)] = EX    # ch04 exit (The Bridge)
_FLOOR_MARKS[(5, 50)] = EX    # ch05 exit (Turret Alley)

# Companion cube start position
_CUBE_START = (17, 56)

# Door links: door cell -> linked pressure plate cell
_DOOR_LINKS = {
    (20, 57): (18, 56),  # door D at (20,57), linked to plate at (18,56)
}

# Level definitions — scored chambers starting at ch03
_LEVELS = [
    {'name': 'MIND THE GAP',    'base': 200,  'time': 75},
    {'name': 'THE BRIDGE',      'base': 400,  'time': 90},
    {'name': 'TURRET ALLEY',    'base': 300,  'time': 60},
    {'name': 'COMPANION CUBE',  'base': 500,  'time': 90},
]

# Turret definitions (instantiated when entering turret level)
_TURRETS_DEF = [
    {'x': 2, 'y': 47, 'dx': 1, 'dy': 0, 'rate': 3.0, 'warn': 0.8},
]

# GLaDOS trigger zones: (cx, cy) -> (message_line1, message_line2, id)
_GLADOS_ZONES = {
    (2, 2):   ("WELCOME TO",     "APERTURE",       "wake"),
    (2, 4):   ("GO AHEAD",       "WALK AROUND",    "move"),
    (4, 8):   ("PORTALS ON",     "SPC:BLU Z:ORG",  "portals"),
    (5, 9):   ("WELL DONE",      "",                "done1"),
    (4, 14):  ("THINK WITH",     "PORTALS",         "think"),
    (2, 21):  ("MIND THE GAP",   "",                "gap"),
    (7, 29):  ("TWO JUMPS",      "USE THE PLATFORM","bridge"),
    (5, 44):  ("TURRET AHEAD",   "TIME YOUR MOVE",  "turret"),
    (17, 56): ("CUBE CAN'T TALK","BUT IT CAN HELP", "cube"),
    (21, 58): ("THE CAKE IS",    "A LIE",           "cake"),
}


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
        self.phase = 'title'
        self.phase_timer = 2.5
        self.time = 0.0

        # Build map
        self.map = [row[:] for row in _M]
        self.heights = dict(_HEIGHTS)
        self.floor_marks = dict(_FLOOR_MARKS)

        # Player
        self.px = 2.5
        self.py = 2.5
        self.pa = 0.0  # facing east
        self.elevation = 0.0

        # Ray offsets
        self.ray_offsets = []
        for col in range(GRID_SIZE):
            self.ray_offsets.append((col / GRID_SIZE - 0.5) * FOV)

        # Portals: None or (cell_x, cell_y, face)
        self.blue_portal = None
        self.orange_portal = None
        self.portal_cooldown = 0.0

        # Companion cube
        self.cube_x, self.cube_y = _CUBE_START
        self.cube_push_cooldown = 0.0

        # Doors state: set of (cx, cy) that are currently open
        self.open_doors = set()
        # Auto-open door for chamber 00
        self.auto_door_timer = 2.0
        self.auto_door_opened = False

        # GLaDOS messages
        self.glados_seen = set()
        self.glados_msg = None  # (line1, line2)
        self.glados_timer = 0.0

        # Win state
        self.won = False
        self.win_timer = 0.0

        # Shoot animation
        self.shoot_flash = 0.0
        self.shoot_color = None

        # Death state
        self.fall_timer = 0.0
        self.dead_timer = 0.0
        self.death_cause = None  # 'pit', 'turret', 'timeout'

        # Level system
        self.current_level = 0
        self.level_score = 0
        self.level_timer = 0.0
        self.level_active = False
        self.choice_selection = 0  # 0=NEXT, 1=STOP

        # Turrets + bullets
        self.turrets = []
        self.bullets = []

    # ─────────────────────────────────────────────────────────────
    #  Map helpers
    # ─────────────────────────────────────────────────────────────

    def _cell(self, x, y):
        """Get map cell value. Out of bounds = wall."""
        if x < 0 or x >= MAP_W or y < 0 or y >= MAP_H:
            return W
        return self.map[y][x]

    def _is_wall(self, x, y):
        """Check if cell is any solid wall type."""
        c = self._cell(x, y)
        if c == 0:
            return False
        if c == D:
            # Door: solid if locked
            return (x, y) not in self.open_doors
        if c == U:
            # Auto-open door: solid until opened
            return not self.auto_door_opened
        return True

    def _is_portalable(self, x, y):
        """Check if a wall cell can receive a portal."""
        c = self._cell(x, y)
        return c in (P, PH)

    def _floor_height(self, x, y):
        """Get floor height at cell."""
        return self.heights.get((x, y), 0.0)

    def _solid(self, x, y):
        """Collision check with margin. Pits are NOT solid — player falls in."""
        for dx in (-MARGIN, MARGIN):
            for dy in (-MARGIN, MARGIN):
                mx = int(x + dx)
                my = int(y + dy)
                if self._is_wall(mx, my):
                    return True
                # Cube blocks movement (unless pushing it)
                if mx == self.cube_x and my == self.cube_y:
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

            if map_x < 0 or map_x >= MAP_W or map_y < 0 or map_y >= MAP_H:
                break
            cell_val = self._cell(map_x, map_y)
            if cell_val != 0:
                # Skip open doors (same as _cast_ray)
                if cell_val == D and (map_x, map_y) in self.open_doors:
                    continue
                if cell_val == U and self.auto_door_opened:
                    continue
                # Hit a wall — determine face
                if self._is_portalable(map_x, map_y):
                    if side == 0:
                        face = 3 if step_x > 0 else 1  # hit from west or east
                    else:
                        face = 0 if step_y > 0 else 2  # hit from north or south
                    # Portal height = player's current floor level
                    p_h = self._floor_height(int(self.px), int(self.py))
                    portal = (map_x, map_y, face, p_h)
                    if color == 'blue':
                        # Don't place on exact same spot as other portal
                        if self.orange_portal != portal:
                            self.blue_portal = portal
                    else:
                        if self.blue_portal != portal:
                            self.orange_portal = portal
                    self.shoot_flash = 0.15
                    self.shoot_color = BLUE_PORTAL if color == 'blue' else ORANGE_PORTAL
                break

    def _has_portal(self, cell_x, cell_y, face):
        """Check if a portal exists on this wall face. Returns (color, height) or None."""
        if self.blue_portal and self.blue_portal[:3] == (cell_x, cell_y, face):
            return ('blue', self.blue_portal[3])
        if self.orange_portal and self.orange_portal[:3] == (cell_x, cell_y, face):
            return ('orange', self.orange_portal[3])
        return None

    def _get_exit_portal(self, color):
        """Get the other portal."""
        if color == 'blue':
            return self.orange_portal
        return self.blue_portal

    def _portal_outward(self, portal):
        """Get the outward direction vector for a portal face."""
        face = portal[2]
        return (FACE_DX[face], FACE_DY[face])

    def _try_portal_traverse(self, dt):
        """Check if player should traverse a portal."""
        if self.portal_cooldown > 0:
            return
        if not self.blue_portal or not self.orange_portal:
            return

        for color, portal in [('blue', self.blue_portal), ('orange', self.orange_portal)]:
            cx, cy, face, p_height = portal
            # Must be at the right floor level to enter
            if abs(self.elevation - p_height) > 0.6:
                continue
            odx, ody = self._portal_outward(portal)
            # The portal surface is at the boundary of the wall cell
            # For face N (0): surface at y=cy, player should be at y < cy
            # For face S (2): surface at y=cy+1, player should be at y > cy+1
            # For face W (3): surface at x=cx, player should be at x < cx
            # For face E (1): surface at x=cx+1, player should be at x > cx+1
            if face == 0:  # North face — player south of wall, moves south to enter
                portal_y = cy
                if abs(self.py - portal_y) < 0.5 and abs(self.px - (cx + 0.5)) < 0.8:
                    if math.sin(self.pa) > 0.1:  # moving south (toward wall)
                        self._do_teleport(color)
                        return
            elif face == 2:  # South face — player south of wall, moves north to enter
                portal_y = cy + 1
                if abs(self.py - portal_y) < 0.5 and abs(self.px - (cx + 0.5)) < 0.8:
                    if math.sin(self.pa) < -0.1:  # moving north (toward wall)
                        self._do_teleport(color)
                        return
            elif face == 3:  # West face — player west of wall, moves east to enter
                portal_x = cx
                if abs(self.px - portal_x) < 0.5 and abs(self.py - (cy + 0.5)) < 0.8:
                    if math.cos(self.pa) > 0.1:  # moving east (toward wall)
                        self._do_teleport(color)
                        return
            elif face == 1:  # East face — player east of wall, moves west to enter
                portal_x = cx + 1
                if abs(self.px - portal_x) < 0.5 and abs(self.py - (cy + 0.5)) < 0.8:
                    if math.cos(self.pa) < -0.1:  # moving west (toward wall)
                        self._do_teleport(color)
                        return

    def _do_teleport(self, entry_color):
        """Teleport player through portal."""
        exit_portal = self._get_exit_portal(entry_color)
        if not exit_portal:
            return
        ex, ey, eface, e_height = exit_portal
        odx, ody = self._portal_outward(exit_portal)

        # Position: 0.7 units out from exit portal face
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

        # Set facing to outward direction of exit
        self.pa = math.atan2(ody, odx)

        # Set elevation to exit portal's floor level
        self.elevation = e_height

        self.portal_cooldown = 0.4

    # ─────────────────────────────────────────────────────────────
    #  Cube + Plates
    # ─────────────────────────────────────────────────────────────

    def _try_push_cube(self, dx, dy):
        """Try to push cube one cell in direction (dx, dy)."""
        if self.cube_push_cooldown > 0:
            return False
        nx = self.cube_x + dx
        ny = self.cube_y + dy
        if not self._is_wall(nx, ny) and self.floor_marks.get((nx, ny)) != PIT and self._floor_height(nx, ny) >= 0:
            # Check cube doesn't go into another cube (only one cube)
            self.cube_x = nx
            self.cube_y = ny
            self.cube_push_cooldown = 0.3
            return True
        # Check if pushing into a portal
        if self._is_wall(nx, ny) and (self.blue_portal or self.orange_portal):
            # Determine which face we're pushing toward
            if dx == 1:
                face = 3  # pushing east, hitting west face of target
            elif dx == -1:
                face = 1
            elif dy == 1:
                face = 0  # pushing south, hitting north face of target
            else:
                face = 2
            portal_hit = self._has_portal(nx, ny, face)
            if portal_hit:
                p_color, _ = portal_hit
                exit_p = self._get_exit_portal(p_color)
                if exit_p:
                    ex, ey, eface = exit_p[0], exit_p[1], exit_p[2]
                    odx, ody = self._portal_outward(exit_p)
                    self.cube_x = ex + odx
                    self.cube_y = ey + ody
                    self.cube_push_cooldown = 0.3
                    return True
        return False

    def _update_plates(self):
        """Check pressure plates and update doors."""
        for door_pos, plate_pos in _DOOR_LINKS.items():
            px, py = plate_pos
            # Check if cube or player is on the plate
            on_plate = (self.cube_x == px and self.cube_y == py)
            on_plate = on_plate or (int(self.px) == px and int(self.py) == py)
            if on_plate:
                self.open_doors.add(door_pos)
            else:
                self.open_doors.discard(door_pos)

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
            self.win_timer -= dt
            if self.win_timer <= 0:
                self.state = GameState.GAME_OVER
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
                self.score = 0
                self.state = GameState.GAME_OVER
            return

        if self.phase == 'level_clear':
            self._update_level_clear(input_state)
            return

        # Timers
        if self.portal_cooldown > 0:
            self.portal_cooldown -= dt
        if self.cube_push_cooldown > 0:
            self.cube_push_cooldown -= dt
        if self.shoot_flash > 0:
            self.shoot_flash -= dt
        if self.glados_timer > 0:
            self.glados_timer -= dt
            if self.glados_timer <= 0:
                self.glados_msg = None

        # Level timer countdown
        if self.level_active and self.level_timer > 0:
            self.level_timer -= dt
            if self.level_timer <= 0:
                self.level_timer = 0
                self.death_cause = 'timeout'
                self.phase = 'falling'
                self.fall_timer = 1.0
                return

        # Auto door timer
        if not self.auto_door_opened:
            self.auto_door_timer -= dt
            if self.auto_door_timer <= 0:
                self.auto_door_opened = True

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

        # Check cube push
        if input_state.up:
            face_dir = self._cardinal_dir()
            fdx, fdy = FACE_DX[face_dir], FACE_DY[face_dir]
            target_cx = int(nx + fdx * 0.3)
            target_cy = int(ny + fdy * 0.3)
            if target_cx == self.cube_x and target_cy == self.cube_y:
                pushed = self._try_push_cube(fdx, fdy)
                if not pushed:
                    pass

        # Apply movement with collision
        if not self._solid(nx, self.py):
            self.px = nx
        if not self._solid(self.px, ny):
            self.py = ny

        # Pit fall detection — after movement applied
        pcx, pcy = int(self.px), int(self.py)
        if self.floor_marks.get((pcx, pcy)) == PIT:
            self.death_cause = 'pit'
            self.phase = 'falling'
            self.fall_timer = 1.0
            return

        # Portal traversal
        self._try_portal_traverse(dt)

        # Pressure plates
        self._update_plates()

        # Turret + bullet updates
        if self.turrets:
            self._update_turrets(dt)
            self._update_bullets(dt)

        # GLaDOS trigger zones
        cell_key = (int(self.px), int(self.py))
        if cell_key in _GLADOS_ZONES:
            line1, line2, zone_id = _GLADOS_ZONES[cell_key]
            if zone_id not in self.glados_seen:
                self.glados_seen.add(zone_id)
                self.glados_msg = (line1, line2)
                self.glados_timer = 3.0

        # Level activation — entering ch03 triggers scoring
        if not self.level_active and cell_key == (2, 21):
            self._start_level(0)

        # EX check — level exit or final win
        if self.floor_marks.get((pcx, pcy)) == EX:
            # Remove mark so it won't re-trigger
            del self.floor_marks[(pcx, pcy)]
            if not self.level_active:
                pass  # tutorial — no scoring
            elif self.current_level >= len(_LEVELS) - 1:
                # Final level complete
                lvl = _LEVELS[self.current_level]
                pts = lvl['base'] + int(self.level_timer * (self.current_level + 1) * 2)
                self.level_score += pts
                self.score = self.level_score
                self.phase = 'won'
                self.win_timer = 4.0
            else:
                # Level clear — show NEXT/STOP choice
                lvl = _LEVELS[self.current_level]
                self._level_pts = lvl['base'] + int(self.level_timer * (self.current_level + 1) * 2)
                self.level_score += self._level_pts
                self.phase = 'level_clear'
                self.choice_selection = 0

    def _cardinal_dir(self):
        """Get cardinal direction from angle. 0=N, 1=E, 2=S, 3=W."""
        a = self.pa % (2 * math.pi)
        # atan2 convention: 0=east, pi/2=south
        if a < 0:
            a += 2 * math.pi
        if a < math.pi * 0.25 or a >= math.pi * 1.75:
            return 1  # East
        elif a < math.pi * 0.75:
            return 2  # South
        elif a < math.pi * 1.25:
            return 3  # West
        else:
            return 0  # North

    # ─────────────────────────────────────────────────────────────
    #  Level system
    # ─────────────────────────────────────────────────────────────

    def _start_level(self, level_idx):
        """Activate a scored level."""
        self.level_active = True
        self.current_level = level_idx
        lvl = _LEVELS[level_idx]
        self.level_timer = float(lvl['time'])
        # Clear portals for fresh start
        self.blue_portal = None
        self.orange_portal = None
        # Activate turrets for turret level (index 2)
        if level_idx == 2:
            self.turrets = []
            for td in _TURRETS_DEF:
                self.turrets.append({
                    'x': td['x'], 'y': td['y'],
                    'dx': td['dx'], 'dy': td['dy'],
                    'rate': td['rate'], 'warn': td['warn'],
                    'timer': td['rate'],
                })
        else:
            self.turrets = []
            self.bullets = []

    def _update_level_clear(self, input_state):
        """Handle NEXT/STOP choice screen input."""
        if input_state.up_pressed or input_state.down_pressed:
            self.choice_selection = 1 - self.choice_selection
        if input_state.action_l or input_state.action_r:
            if self.choice_selection == 0:
                # NEXT level
                self._start_level(self.current_level + 1)
                self.phase = 'playing'
            else:
                # STOP — bank score
                self.score = self.level_score
                self.phase = 'won'
                self.win_timer = 4.0

    # ─────────────────────────────────────────────────────────────
    #  Turrets + Bullets
    # ─────────────────────────────────────────────────────────────

    def _update_turrets(self, dt):
        """Countdown turret timers, spawn bullets."""
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
        """Move bullets, check collisions."""
        alive = []
        for b in self.bullets:
            b['x'] += b['dx'] * b['speed'] * dt
            b['y'] += b['dy'] * b['speed'] * dt
            b['life'] -= dt
            # Wall hit
            bx, by = int(b['x']), int(b['y'])
            if self._is_wall(bx, by):
                continue
            # Life expired
            if b['life'] <= 0:
                continue
            # Player hit
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
    #  Raycaster + Drawing
    # ─────────────────────────────────────────────────────────────

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == 'title':
            self._draw_title()
            return

        if self.phase == 'won':
            self._draw_win()
            return

        if self.phase == 'dead':
            self._draw_dead()
            return

        if self.phase == 'level_clear':
            self._draw_level_clear()
            return

        # Column-by-column rendering (ceiling + wall + floor)
        eye_h = self.elevation + 0.5
        for col in range(GRID_SIZE):
            ray_angle = self.pa + self.ray_offsets[col]
            self._cast_ray(col, ray_angle, eye_h)

        # Bullet rendering
        if self.bullets:
            self._draw_bullets()

        # Falling overlay — red tint intensifies
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

        # Shoot flash overlay
        if self.shoot_flash > 0 and self.shoot_color:
            alpha = self.shoot_flash / 0.15
            r0, g0, b0 = self.shoot_color
            for x in range(28, 36):
                for y in range(28, 36):
                    pr, pg, pb = self.display.get_pixel(x, y)
                    nr = min(255, int(pr + r0 * alpha * 0.5))
                    ng = min(255, int(pg + g0 * alpha * 0.5))
                    nb = min(255, int(pb + b0 * alpha * 0.5))
                    self.display.set_pixel(x, y, (nr, ng, nb))

        # Portal HUD indicators (top corners)
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

        # Timer HUD (top-right area, below portal indicator)
        if self.level_active and self.level_timer > 0:
            secs = int(self.level_timer)
            txt = str(secs)
            if secs <= 5:
                tc = Colors.RED
            elif secs <= 15:
                tc = Colors.ORANGE
            else:
                tc = Colors.WHITE
            # Right-align: 4px per char
            tx = 63 - len(txt) * 4
            self.display.draw_text_small(tx, 5, txt, tc)

        # GLaDOS message overlay
        if self.glados_msg and self.glados_timer > 0:
            self._draw_glados()

    def _cast_ray(self, col, angle, eye_h):
        """DDA raycaster with portal rendering.
        Renders the full column: ceiling, wall, floor."""
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
        cube_hit = None  # (perp_dist, wall_x, side) — rendered as overlay
        for _ in range(64):
            if side_dist_x < side_dist_y:
                side_dist_x += delta_x
                map_x += step_x
                side = 0
            else:
                side_dist_y += delta_y
                map_y += step_y
                side = 1

            if map_x < 0 or map_x >= MAP_W or map_y < 0 or map_y >= MAP_H:
                break
            cell = self._cell(map_x, map_y)
            if cell != 0:
                if cell == D and (map_x, map_y) in self.open_doors:
                    continue
                if cell == U and self.auto_door_opened:
                    continue
                hit = True
                hit_cell = cell
                break

            # Companion cube — save hit but continue ray to find background
            if map_x == self.cube_x and map_y == self.cube_y and cube_hit is None:
                if side == 0:
                    cpd = (map_x - self.px + (1 - step_x) / 2) / cos_a
                else:
                    cpd = (map_y - self.py + (1 - step_y) / 2) / sin_a
                if cpd > 0.01:
                    cwx = self.py + cpd * sin_a if side == 0 else self.px + cpd * cos_a
                    cwx -= int(cwx)
                    cube_hit = (cpd, cwx, side)
                continue

        if not hit:
            # No wall — fill column with ceiling + floor casting
            for y in range(HALF):
                self.display.set_pixel(col, y, (30, 30, 45))
            for y in range(HALF, GRID_SIZE):
                p = y - HALF
                if p <= 0:
                    continue
                row_dist = eye_h * GRID_SIZE / p
                fx = self.px + cos_a * row_dist
                fy = self.py + sin_a * row_dist
                fcx, fcy = int(fx), int(fy)
                mark = self.floor_marks.get((fcx, fcy))
                fog_f = min(1.0, 2.0 / (row_dist + 0.5))
                if mark == PIT:
                    r, g, b = int(15 * fog_f), int(5 * fog_f), int(5 * fog_f)
                elif mark == PP:
                    r, g, b = int(180 * fog_f), int(150 * fog_f), int(30 * fog_f)
                elif mark == EX:
                    r, g, b = int(30 * fog_f), int(180 * fog_f), int(30 * fog_f)
                else:
                    checker = (fcx + fcy) % 2
                    base = 45 if checker == 0 else 35
                    r, g, b = int((base+5)*fog_f), int((base+2)*fog_f), int(base*fog_f)
                self.display.set_pixel(col, y, (r, g, b))
            return

        # Perpendicular distance
        if side == 0:
            perp_dist = (map_x - self.px + (1 - step_x) / 2) / cos_a
        else:
            perp_dist = (map_y - self.py + (1 - step_y) / 2) / sin_a
        if perp_dist < 0.01:
            perp_dist = 0.01

        cell_floor = 0.0
        wall_bottom = cell_floor
        if hit_cell == D:
            wh = 1.2   # door: shorter than walls (looks like a doorway)
        else:
            wh = WALL_HEIGHT
        wall_top = cell_floor + wh

        scale = GRID_SIZE / perp_dist
        screen_top = int(HALF - (wall_top - eye_h) * scale)
        screen_bot = int(HALF - (wall_bottom - eye_h) * scale)
        draw_start = max(0, screen_top)
        draw_end = min(GRID_SIZE - 1, screen_bot)
        line_height = max(1, screen_bot - screen_top)

        # Texture u coordinate
        if side == 0:
            wall_x = self.py + perp_dist * sin_a
        else:
            wall_x = self.px + perp_dist * cos_a
        wall_x -= int(wall_x)

        # Fog + side shading
        fog = min(1.0, 2.5 / (perp_dist + 0.5))
        if side == 1:
            fog *= 0.75

        # Portal on this face? Compute v-range for height-correct rendering
        if side == 0:
            face = 3 if step_x > 0 else 1
        else:
            face = 0 if step_y > 0 else 2
        portal_info = None
        portal_hit = self._has_portal(map_x, map_y, face)
        if portal_hit and wh > 0:
            p_color, p_height = portal_hit
            # Map portal (spans p_height to p_height+1.0) into v coordinates
            # v=0 is wall_top, v=1 is wall_bottom
            pv_top = max(0.0, (wall_top - (p_height + 1.0)) / wh)
            pv_bot = min(1.0, (wall_top - p_height) / wh)
            portal_info = (p_color, pv_top, pv_bot)

        # ── Render ceiling (above wall) ──
        for y in range(0, draw_start):
            self.display.set_pixel(col, y, (30, 30, 45))

        # ── Render wall ──
        for y in range(draw_start, draw_end + 1):
            v = (y - screen_top) / line_height if line_height > 0 else 0.5
            r, g, b = self._wall_pixel(hit_cell, wall_x, v, portal_info, map_x, map_y)
            r = int(r * fog)
            g = int(g * fog)
            b = int(b * fog)
            self.display.set_pixel(col, y, (r, g, b))

        # ── Render floor (below wall) with floor casting ──
        for y in range(draw_end + 1, GRID_SIZE):
            p = y - HALF
            if p <= 0:
                # Above horizon but below wall (distant elevated wall)
                self.display.set_pixel(col, y, (13, 10, 8))
                continue
            row_dist = eye_h * GRID_SIZE / p
            fx = self.px + cos_a * row_dist
            fy = self.py + sin_a * row_dist
            fcx, fcy = int(fx), int(fy)
            mark = self.floor_marks.get((fcx, fcy))
            fog_f = min(1.0, 2.0 / (row_dist + 0.5))
            if mark == PIT:
                r, g, b = int(15 * fog_f), int(5 * fog_f), int(5 * fog_f)
            elif mark == PP:
                r, g, b = int(180 * fog_f), int(150 * fog_f), int(30 * fog_f)
            elif mark == EX:
                r, g, b = int(30 * fog_f), int(180 * fog_f), int(30 * fog_f)
            else:
                checker = (fcx + fcy) % 2
                base = 45 if checker == 0 else 35
                r, g, b = int((base+5)*fog_f), int((base+2)*fog_f), int(base*fog_f)
            self.display.set_pixel(col, y, (r, g, b))

        # ── Overlay companion cube (rendered on top of background) ──
        if cube_hit:
            cpd, cwx, cside = cube_hit
            cube_floor_h = self._floor_height(self.cube_x, self.cube_y)
            cube_top = cube_floor_h + 1.0
            cscale = GRID_SIZE / cpd
            c_screen_top = int(HALF - (cube_top - eye_h) * cscale)
            c_screen_bot = int(HALF - (cube_floor_h - eye_h) * cscale)
            c_draw_start = max(0, c_screen_top)
            c_draw_end = min(GRID_SIZE - 1, c_screen_bot)
            c_line_h = max(1, c_screen_bot - c_screen_top)
            cfog = min(1.0, 2.5 / (cpd + 0.5))
            if cside == 1:
                cfog *= 0.75
            for y in range(c_draw_start, c_draw_end + 1):
                cv = (y - c_screen_top) / c_line_h if c_line_h > 0 else 0.5
                r, g, b = self._wall_pixel(CC, cwx, cv, None, self.cube_x, self.cube_y)
                self.display.set_pixel(col, y, (int(r * cfog), int(g * cfog), int(b * cfog)))

    def _wall_pixel(self, cell_type, u, v, portal_info, cx, cy):
        """Get wall pixel color based on type, with portal overlay.
        portal_info: None or (color_name, v_top, v_bot) for height-correct rendering."""
        # Portal rendering: player-sized oval within the portal's v-range
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

        if cell_type == CC:
            # Companion cube: thin gray frame, big pink heart fills the face
            edge = u < 0.12 or u > 0.88 or v < 0.12 or v > 0.88
            if edge:
                return (160, 155, 165)  # gray frame
            # Heart fills interior — glow near frame edge
            hu = abs(u - 0.5)
            hv = abs(v - 0.5)
            if hu > 0.3 or hv > 0.3:
                return (180, 130, 150)  # heart border/glow
            return (220, 100, 140)  # pink heart center

        if cell_type in (P, PH):
            # White Aperture panels
            r, g, b = 200, 200, 210
            # Panel grid lines
            pu = int(u * 4)
            pv = int(v * 4)
            fu = u * 4 - pu
            fv = v * 4 - pv
            if fu < 0.08 or fu > 0.92 or fv < 0.08 or fv > 0.92:
                return (170, 170, 180)
            return (r, g, b)

        if cell_type == D:
            # Door (locked) — frame + red lock indicator
            if u < 0.1 or u > 0.9 or v < 0.08 or v > 0.92:
                return (90, 85, 100)  # visible door frame
            if 0.35 <= u <= 0.65 and 0.25 <= v <= 0.45:
                return (180, 30, 30)  # red lock indicator
            if abs(v - 0.5) < 0.04:
                return (75, 70, 85)  # horizontal divider
            return (55, 50, 60)  # door body

        if cell_type == U:
            # Door (auto-open, shown as locked)
            return (60, 55, 65)

        if cell_type == T:
            # Turret — gray body with pulsing red eye
            if 0.3 <= u <= 0.7 and 0.25 <= v <= 0.45:
                # Eye region — pulse speed based on time
                pulse = 0.5 + 0.5 * math.sin(self.time * 8.0)
                r = int(180 + 75 * pulse)
                return (r, 10, 10)
            # Body — dark gray with subtle panel lines
            if u < 0.05 or u > 0.95 or v < 0.05 or v > 0.95:
                return (50, 50, 55)
            return (80, 80, 90)

        # Concrete (default)
        r, g, b = 90, 90, 100
        # Subtle grid lines
        gu = int(u * 8)
        gv = int(v * 8)
        fu = u * 8 - gu
        fv = v * 8 - gv
        if fu < 0.06 or fv < 0.06:
            return (70, 70, 80)
        return (r, g, b)

    # ─────────────────────────────────────────────────────────────
    #  HUD / Overlays
    # ─────────────────────────────────────────────────────────────

    def _draw_glados(self):
        """Draw GLaDOS message overlay."""
        line1, line2 = self.glados_msg
        # Dark band
        for y in range(26, 38):
            for x in range(GRID_SIZE):
                pr, pg, pb = self.display.get_pixel(x, y)
                self.display.set_pixel(x, y, (pr // 3, pg // 3, pb // 3))
        # Text
        self.display.draw_text_small(2, 28, line1, Colors.WHITE)
        if line2:
            self.display.draw_text_small(2, 34, line2, Colors.WHITE)

    def _draw_title(self):
        """Draw Portal title screen."""
        # Dark background
        self.display.clear((10, 10, 15))

        # Aperture logo (simple circle with segments)
        cx, cy = 32, 20
        for a_deg in range(0, 360, 3):
            a_rad = math.radians(a_deg)
            r = 10
            px = int(cx + r * math.cos(a_rad))
            py = int(cy + r * math.sin(a_rad))
            self.display.set_pixel(px, py, (200, 200, 210))

        # Aperture blades (3 lines)
        for i in range(3):
            a_rad = math.radians(i * 120 + self.time * 30)
            x1 = int(cx + 3 * math.cos(a_rad))
            y1 = int(cy + 3 * math.sin(a_rad))
            x2 = int(cx + 8 * math.cos(a_rad))
            y2 = int(cy + 8 * math.sin(a_rad))
            self.display.draw_line(x1, y1, x2, y2, (180, 180, 190))

        self.display.draw_text_small(14, 35, "PORTAL", Colors.WHITE)
        self.display.draw_text_small(2, 44, "APERTURE SCI", (150, 150, 160))
        # Flashing start text
        if int(self.time * 3) % 2 == 0:
            self.display.draw_text_small(6, 55, "PRESS START", Colors.ORANGE)

    def _draw_win(self):
        """Draw win screen with cake."""
        self.display.clear((10, 10, 15))

        # Simple cake pixel art
        cx, cy = 32, 22
        # Cake base (brown)
        for dx in range(-8, 9):
            for dy in range(0, 6):
                self.display.set_pixel(cx + dx, cy + dy, (139, 90, 43))
        # Frosting (white)
        for dx in range(-8, 9):
            self.display.set_pixel(cx + dx, cy, (240, 240, 240))
            self.display.set_pixel(cx + dx, cy - 1, (240, 240, 240))
        # Frosting drips
        for dx in range(-6, 7, 3):
            self.display.set_pixel(cx + dx, cy + 1, (240, 240, 240))
        # Cherry on top
        self.display.set_pixel(cx, cy - 2, (255, 30, 30))
        self.display.set_pixel(cx, cy - 3, (0, 150, 0))
        # Candle
        self.display.set_pixel(cx - 3, cy - 2, (255, 255, 200))
        self.display.set_pixel(cx - 3, cy - 3, (255, 200, 50))
        self.display.set_pixel(cx + 3, cy - 2, (255, 255, 200))
        self.display.set_pixel(cx + 3, cy - 3, (255, 200, 50))
        # Candle flames flicker
        if int(self.time * 6) % 2 == 0:
            self.display.set_pixel(cx - 3, cy - 4, (255, 150, 0))
            self.display.set_pixel(cx + 3, cy - 4, (255, 150, 0))

        # Plate
        for dx in range(-10, 11):
            self.display.set_pixel(cx + dx, cy + 6, (180, 180, 190))

        self.display.draw_text_small(2, 34, "THE CAKE IS", Colors.WHITE)
        self.display.draw_text_small(14, 42, "A LIE", Colors.ORANGE)
        if self.score > 0:
            self.display.draw_text_small(2, 54, str(self.score), Colors.GREEN)
        else:
            self.display.draw_text_small(6, 54, "YOU ESCAPED!", Colors.GREEN)

    def _draw_dead(self):
        """Draw death screen."""
        self.display.clear((40, 5, 5))
        self.display.draw_text_small(2, 16, "SUBJECT LOST", Colors.RED)
        if self.death_cause == 'pit':
            self.display.draw_text_small(2, 28, "YOU FELL", Colors.WHITE)
        elif self.death_cause == 'turret':
            self.display.draw_text_small(2, 28, "SHOT DOWN", Colors.WHITE)
        elif self.death_cause == 'timeout':
            self.display.draw_text_small(2, 28, "TIME UP", Colors.WHITE)
        self.display.draw_text_small(2, 40, "TESTING", (150, 150, 150))
        self.display.draw_text_small(2, 48, "TERMINATED", (150, 150, 150))

    def _draw_level_clear(self):
        """Draw NEXT/STOP level clear screen."""
        self.display.clear((10, 10, 15))
        self.display.draw_text_small(2, 4, "CHAMBER CLEAR", Colors.GREEN)

        lvl = _LEVELS[self.current_level]
        # Score breakdown
        self.display.draw_text_small(2, 14, lvl['name'], Colors.WHITE)
        self.display.draw_text_small(2, 22, "+" + str(self._level_pts), Colors.YELLOW)
        self.display.draw_text_small(2, 30, "TOTAL " + str(self.level_score), Colors.ORANGE)

        # NEXT / STOP selector
        if self.choice_selection == 0:
            self.display.draw_text_small(2, 44, ">NEXT LEVEL", Colors.YELLOW)
            self.display.draw_text_small(2, 52, " STOP:BANK", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 44, " NEXT LEVEL", Colors.GRAY)
            self.display.draw_text_small(2, 52, ">STOP:BANK", Colors.YELLOW)

    def _draw_bullets(self):
        """Draw bullets in screen space."""
        cos_a = math.cos(self.pa)
        sin_a = math.sin(self.pa)
        for b in self.bullets:
            # Transform to player-relative space
            dx = b['x'] - self.px
            dy = b['y'] - self.py
            # Rotate into view space (forward = cos_a, sin_a)
            vz = dx * cos_a + dy * sin_a   # depth (forward)
            vx = -dx * sin_a + dy * cos_a   # lateral
            if vz <= 0.1:
                continue
            # Project to screen
            sx = int(HALF + vx * GRID_SIZE / vz)
            sy = int(HALF)  # bullets at eye height
            if 0 <= sx < GRID_SIZE - 1 and 0 <= sy < GRID_SIZE - 1:
                self.display.set_pixel(sx, sy, (255, 60, 30))
                self.display.set_pixel(sx + 1, sy, (255, 60, 30))
                self.display.set_pixel(sx, sy + 1, (255, 60, 30))
                self.display.set_pixel(sx + 1, sy + 1, (255, 60, 30))

    def draw_game_over(self, selection: int = 0):
        """Draw game over/win screen with menu options."""
        if self.death_cause:
            # Death screen
            self.display.clear((30, 5, 5))
            self.display.draw_text_small(2, 10, "GAME OVER", Colors.RED)
            if self.death_cause == 'pit':
                self.display.draw_text_small(2, 22, "YOU FELL", Colors.WHITE)
            elif self.death_cause == 'turret':
                self.display.draw_text_small(2, 22, "SHOT DOWN", Colors.WHITE)
            elif self.death_cause == 'timeout':
                self.display.draw_text_small(2, 22, "TIME UP", Colors.WHITE)
            self.display.draw_text_small(2, 34, "SCORE: 0", Colors.GRAY)
        else:
            self._draw_win()
        # Menu options
        if selection == 0:
            self.display.draw_text_small(2, 54, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 54, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 54, ">MENU", Colors.YELLOW)

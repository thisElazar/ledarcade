"""
PORTAL — First-Person Puzzle Game
===================================
Portal-inspired first-person raycaster for the 64x64 LED arcade.
DDA raycaster with elevation system, wall portals with momentum,
companion cube, pressure plates, and GLaDOS messages.

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

# Face directions: N=0, E=1, S=2, W=3
FACE_DX = [0, 1, 0, -1]
FACE_DY = [-1, 0, 1, 0]
# Outward normal for each face (direction pointing away from wall INTO open space)
# If portal is on North face of a wall cell, it faces North (into cell above)
# Player exits heading outward from the face

# ═══════════════════════════════════════════════════════════════════
#  Level Map — 24 wide x 40 tall
# ═══════════════════════════════════════════════════════════════════

MAP_W = 24
MAP_H = 44  # updated by _M length

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
    # Open room with P walls on north/south edges (easily visible).
    # Player enters from col 2 (kept open). Exit corridor south at col 2.
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 6
    [W,P,0,P,P,P,P,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 7
    [W,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 8
    [W,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 9
    [W,P,0,P,P,P,P,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 10
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 11
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 12

    # ── Chamber 02 — Thinking with Portals (rows 13-19) ──
    # Two rooms separated by W barrier at col 7. P walls on each face
    # of barrier. Must portal through to reach exit on right side.
    # Entry from north (col 2). Exit south-east (col 12→col 2).
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 13
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 14
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 15
    [W,W,0,0,0,0,P,W,P,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 16
    [W,W,0,W,W,W,W,W,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 17
    [W,W,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 18
    [W,W,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 19

    # ── Chamber 03 — Vertical Thinking (rows 20-28) ──
    # Ground level left, stairs going right, upper platform right.
    # P walls at ground and upper for cross-elevation portaling.
    # Entry from north (col 2). Exit east on upper level.
    [W,0,0,0,0,P,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 20
    [W,0,0,0,0,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 21
    [W,0,0,0,0,P,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 22
    [W,W,W,W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 23
    [W,W,W,W,W,W,W,W,0,0,P,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 24
    [W,W,W,W,W,W,W,W,0,0,0,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 25
    [W,W,W,W,W,W,W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 26
    [W,W,W,W,W,W,W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 27
    [W,W,W,W,W,W,W,W,W,W,W,0,0,W,W,W,W,W,W,W,W,W,W,W],  # 28

    # ── Chamber 04 — Fling (rows 29-35) ──
    # Long room with descending stairs left, portal wall at bottom,
    # gap in middle, landing + portal wall on right side.
    # Entry from north (col 11-12). Exit south to ch05 (col 18).
    [W,W,0,0,0,0,0,0,0,0,P,0,0,W,W,P,0,0,0,0,0,W,W,W],  # 29
    [W,W,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,W,W,W],  # 30
    [W,W,0,0,0,0,0,0,0,0,P,0,0,W,W,P,0,0,0,0,0,W,W,W],  # 31
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,W,W,W,W,W],  # 32
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,W,W,W,W,W],  # 33
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,W,W,W,W,W],  # 34

    # ── Chamber 05 — Companion Cube (rows 36-41) ──
    # Room with cube and pressure plate controlling exit door.
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,0,W,W,W],  # 36
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,0,W,W,W],  # 37
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,D,W,W,W],  # 38
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,0,0,0,0,0,0,W,W],  # 39
    [W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W,W],  # 40
]

MAP_H = len(_M)  # 44

# Floor height map (elevation per cell, 0.0 = ground default)
_HEIGHTS = {}

# Chamber 03: stairs ascending east through row 21
_HEIGHTS[(6, 21)] = 0.25
_HEIGHTS[(7, 21)] = 0.5
_HEIGHTS[(8, 21)] = 0.75
_HEIGHTS[(9, 21)] = 1.0
# Upper platform at elevation 1.0 (rows 22-27)
for c in [8, 9]:
    _HEIGHTS[(c, 22)] = 1.0
    _HEIGHTS[(c, 23)] = 1.0
    _HEIGHTS[(c, 24)] = 1.0
for c in [8, 9, 10, 11, 12]:
    _HEIGHTS[(c, 25)] = 1.0
_HEIGHTS[(11, 26)] = 1.0
_HEIGHTS[(12, 26)] = 1.0
_HEIGHTS[(11, 27)] = 1.0
_HEIGHTS[(12, 27)] = 1.0
_HEIGHTS[(11, 28)] = 1.0
_HEIGHTS[(12, 28)] = 1.0
_HEIGHTS[(11, 29)] = 1.0
_HEIGHTS[(12, 29)] = 1.0

# Chamber 04: descending staircase west from entry (rows 29-31)
# Entry at (11,28)/(12,28) at elev 1.0 coming from ch03
# P walls at col 10 — stairs are cols 9->2 on rows 29-31
_HEIGHTS[(10, 30)] = 1.0  # smooth transition from upper platform to stairs
_HEIGHTS[(9, 29)] = 0.75
_HEIGHTS[(8, 29)] = 0.5
_HEIGHTS[(7, 29)] = 0.25
_HEIGHTS[(9, 30)] = 0.75
_HEIGHTS[(8, 30)] = 0.5
_HEIGHTS[(7, 30)] = 0.25
_HEIGHTS[(9, 31)] = 0.75
_HEIGHTS[(8, 31)] = 0.5
_HEIGHTS[(7, 31)] = 0.25
# Gap cells in chamber 04 (between the two portal-wall barriers)
for c in [12, 13]:
    _HEIGHTS[(c, 30)] = -1.0

# Floor markers (non-wall special cells)
_FLOOR_MARKS = {}
_FLOOR_MARKS[(18, 36)] = PP   # pressure plate in ch05
_FLOOR_MARKS[(21, 38)] = EX   # exit trigger (through door east)

# Companion cube start position
_CUBE_START = (17, 36)

# Door links: door cell -> linked pressure plate cell
_DOOR_LINKS = {
    (20, 37): (18, 36),  # door D at (20,37), linked to plate at (18,36)
}

# GLaDOS trigger zones: (cx, cy) -> (message_line1, message_line2, id)
_GLADOS_ZONES = {
    (2, 2):   ("WELCOME TO",     "APERTURE",       "wake"),
    (2, 4):   ("USE ARROWS",     "TO MOVE",         "move"),
    (4, 8):   ("PORTALS ON",     "SPC:BLU Z:ORG",   "portals"),
    (5, 9):   ("WELL DONE",      "",                 "done1"),
    (4, 14):  ("THINK WITH",     "PORTALS",          "think"),
    (3, 21):  ("VERTICAL",       "THINKING",         "vert"),
    (5, 30):  ("SPEEDY IN",      "SPEEDY OUT",       "fling"),
    (17, 36): ("CUBE CAN'T TALK","BUT IT CAN HELP",  "cube"),
    (21, 38): ("THE CAKE IS",    "A LIE",            "cake"),
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

        # Propagate floor heights to adjacent wall cells so elevated
        # walls render at the correct base height (multi-story support)
        for y in range(MAP_H):
            for x in range(MAP_W):
                if self.map[y][x] != 0 and (x, y) not in self.heights:
                    max_h = 0.0
                    for dx, dy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < MAP_W and 0 <= ny < MAP_H:
                            if self.map[ny][nx] == 0:
                                h = self.heights.get((nx, ny), 0.0)
                                if h > max_h:
                                    max_h = h
                    if max_h > 0:
                        self.heights[(x, y)] = max_h

        # Player
        self.px = 2.5
        self.py = 2.5
        self.pa = 0.0  # facing east
        self.elevation = 0.0
        self.velocity = 0.0

        # Ray offsets
        self.ray_offsets = []
        for col in range(GRID_SIZE):
            self.ray_offsets.append((col / GRID_SIZE - 0.5) * FOV)

        # Portals: None or (cell_x, cell_y, face)
        self.blue_portal = None
        self.orange_portal = None
        self.portal_cooldown = 0.0

        # No pre-placed portals — chamber 01 teaches shooting
        self.blue_portal = None

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

        # Checkpoint for gap falls
        self.checkpoint = (self.px, self.py, self.pa, self.elevation)

        # Win state
        self.won = False
        self.win_timer = 0.0

        # Shoot animation
        self.shoot_flash = 0.0
        self.shoot_color = None

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
        """Collision check with margin."""
        for dx in (-MARGIN, MARGIN):
            for dy in (-MARGIN, MARGIN):
                mx = int(x + dx)
                my = int(y + dy)
                if self._is_wall(mx, my):
                    return True
                # Cube blocks movement (unless pushing it)
                if mx == self.cube_x and my == self.cube_y:
                    return True
                # Gap: block if velocity too low
                h = self._floor_height(mx, my)
                if h <= -0.5 and self.velocity < 3.0:
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

        # Preserve velocity magnitude
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
        if not self._is_wall(nx, ny) and self._floor_height(nx, ny) >= 0:
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
        move_spd = max(MOVE_SPEED, self.velocity)
        speed = move_spd * dt
        moving = False

        # Determine current cell height and adjust speed for slopes
        cur_cell_x = int(self.px)
        cur_cell_y = int(self.py)
        cur_h = self._floor_height(cur_cell_x, cur_cell_y)

        nx, ny = self.px, self.py
        if input_state.up:
            nx += cos_a * speed
            ny += sin_a * speed
            moving = True
        if input_state.down:
            nx -= cos_a * speed * 0.6
            ny -= sin_a * speed * 0.6
            moving = True

        if input_state.left:
            self.pa -= ROT_SPEED * dt
        if input_state.right:
            self.pa += ROT_SPEED * dt

        # Check cube push
        if moving and input_state.up:
            # Determine facing cardinal direction
            face_dir = self._cardinal_dir()
            fdx, fdy = FACE_DX[face_dir], FACE_DY[face_dir]
            # Check if cube is in the cell we're moving into
            target_cx = int(nx + fdx * 0.3)
            target_cy = int(ny + fdy * 0.3)
            if target_cx == self.cube_x and target_cy == self.cube_y:
                pushed = self._try_push_cube(fdx, fdy)
                if not pushed:
                    # Can't push, block movement toward cube
                    pass

        # Apply movement with collision
        if not self._solid(nx, self.py):
            self.px = nx
        if not self._solid(self.px, ny):
            self.py = ny

        # Update velocity tracking — gradual decay preserves momentum
        if moving:
            new_h = self._floor_height(int(self.px), int(self.py))
            slope = self.elevation - new_h  # positive when going downhill
            if slope > 0.05:
                target_v = min(5.0, MOVE_SPEED * (1.0 + slope * 2.5))
                self.velocity = max(self.velocity, target_v)
            else:
                # Gradual decay toward base speed
                self.velocity = max(MOVE_SPEED, self.velocity - dt * 2.0)
        else:
            self.velocity = max(0, self.velocity - dt * 4.0)  # faster decay when stopped

        # Smooth elevation interpolation
        target_h = self._floor_height(int(self.px), int(self.py))
        if target_h >= -0.5:  # not a gap
            diff = target_h - self.elevation
            self.elevation += diff * min(1.0, 8.0 * dt)

        # Check for gap fall
        cell_h = self._floor_height(int(self.px), int(self.py))
        if cell_h <= -0.5 and self.velocity < 3.5:
            # Fall! Reset to checkpoint
            self.px, self.py, self.pa, self.elevation = self.checkpoint
            self.velocity = 0.0

        # Update checkpoint when on solid ground
        if cell_h >= 0:
            self.checkpoint = (self.px, self.py, self.pa, self.elevation)

        # Portal traversal
        self._try_portal_traverse(dt)

        # Pressure plates
        self._update_plates()

        # GLaDOS trigger zones
        cell_key = (int(self.px), int(self.py))
        if cell_key in _GLADOS_ZONES:
            line1, line2, zone_id = _GLADOS_ZONES[cell_key]
            if zone_id not in self.glados_seen:
                self.glados_seen.add(zone_id)
                self.glados_msg = (line1, line2)
                self.glados_timer = 3.0

        # Exit check
        if self.floor_marks.get((int(self.px), int(self.py))) == EX:
            self.phase = 'won'
            self.win_timer = 4.0
            self.score = 1000

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

        # Column-by-column rendering (ceiling + wall + steps + floor)
        eye_h = self.elevation + 0.5
        for col in range(GRID_SIZE):
            ray_angle = self.pa + self.ray_offsets[col]
            self._cast_ray(col, ray_angle, eye_h)

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

        # GLaDOS message overlay
        if self.glados_msg and self.glados_timer > 0:
            self._draw_glados()

    def _cast_ray(self, col, angle, eye_h):
        """DDA raycaster with elevation, step edges, and portal rendering.
        Renders the full column: ceiling, wall, stair steps, floor."""
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

        # Track floor height transitions for stair step rendering
        prev_floor_h = self._floor_height(int(self.px), int(self.py))
        step_edges = []

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

            # Open floor cell — check for height transition (stair edge)
            floor_h = self._floor_height(map_x, map_y)
            if abs(floor_h - prev_floor_h) > 0.05:
                if side == 0:
                    pd = (map_x - self.px + (1 - step_x) / 2) / cos_a
                else:
                    pd = (map_y - self.py + (1 - step_y) / 2) / sin_a
                if pd > 0.1:
                    lo = min(prev_floor_h, floor_h)
                    hi = max(prev_floor_h, floor_h)
                    step_edges.append((pd, lo, hi, side))
                prev_floor_h = floor_h

            # Companion cube renders as wall-like object
            if map_x == self.cube_x and map_y == self.cube_y:
                hit = True
                hit_cell = CC
                break

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
                if mark == PP:
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

        # Wall dimensions — vary by type
        cell_floor = self._floor_height(map_x, map_y)
        wall_bottom = cell_floor
        if hit_cell == CC:
            wh = 0.4   # small pushable cube
        elif hit_cell == D:
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
            if mark == PP:
                r, g, b = int(180 * fog_f), int(150 * fog_f), int(30 * fog_f)
            elif mark == EX:
                r, g, b = int(30 * fog_f), int(180 * fog_f), int(30 * fog_f)
            else:
                checker = (fcx + fcy) % 2
                base = 45 if checker == 0 else 35
                r, g, b = int((base+5)*fog_f), int((base+2)*fog_f), int(base*fog_f)
            self.display.set_pixel(col, y, (r, g, b))

        # ── Render stair step edges (small risers only) ──
        for pd, lo, hi, s in step_edges:
            if pd >= perp_dist:
                continue  # step is behind the wall
            if hi - lo > 0.4:
                continue  # skip large transitions (platform edges)
            sc = GRID_SIZE / pd
            sy_top = int(HALF - (hi - eye_h) * sc)
            sy_bot = int(HALF - (lo - eye_h) * sc)
            sf = min(1.0, 2.0 / (pd + 0.5))
            if s == 1:
                sf *= 0.8
            cr, cg, cb = int(95 * sf), int(90 * sf), int(100 * sf)
            for y in range(max(0, sy_top), min(GRID_SIZE, sy_bot + 1)):
                self.display.set_pixel(col, y, (cr, cg, cb))

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
            # Companion cube: gray body with prominent pink heart
            hu = abs(u - 0.5)
            hv = abs(v - 0.5)
            if hu < 0.25 and hv < 0.25:
                return (220, 100, 140)  # pink heart (big so visible on small cube)
            if hu < 0.35 and hv < 0.35:
                return (180, 130, 150)  # heart border/glow
            return (160, 155, 165)  # gray body

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
        self.display.draw_text_small(6, 54, "YOU ESCAPED!", Colors.GREEN)

    def draw_game_over(self, selection: int = 0):
        """Draw game over/win screen with menu options."""
        self._draw_win()
        # Overlay menu options
        if selection == 0:
            self.display.draw_text_small(2, 54, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 54, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 54, ">MENU", Colors.YELLOW)

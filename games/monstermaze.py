"""
3D Monster Maze - ZX81 Classic (1982)
======================================
Navigate a first-person maze to find the exit while a T-Rex hunts you.
Pre-computed wall rectangle rendering (faithful to original), 5-state Rex AI.

Controls:
  Left/Right  - Turn 90 degrees
  Up          - Step forward one cell (0.2s cooldown)
  Space       - Sprint forward 2 cells if both open
"""

import random
from collections import deque
from enum import Enum, auto
from arcade import Game, GameState, InputState, Display, Colors, GRID_SIZE

# =============================================================================
# Constants
# =============================================================================

MAZE_SIZE = 16  # 16x16 grid
VIEWPORT_H = 44  # 3D viewport height (y 0..43)
STATUS_Y = 44  # Status message row
HUD_Y = 52  # Bottom HUD row
MINIMAP_X = 52  # Minimap top-left x
MINIMAP_Y = 52  # Minimap top-left y
MINIMAP_SIZE = 12  # 12x12 pixels

# Directions: N=0, E=1, S=2, W=3
DX = [0, 1, 0, -1]
DY = [-1, 0, 1, 0]

# Depth geometry table for 3D rendering
# (xl, xr, yt, yb, wall_w)
DEPTH_TABLE = [
    (0, 63, 0, 43, 12),   # depth 0
    (12, 51, 4, 39, 8),   # depth 1
    (20, 43, 8, 35, 6),   # depth 2
    (26, 37, 12, 31, 4),  # depth 3
    (30, 33, 16, 27, 2),  # depth 4
    (31, 32, 19, 24, 1),  # depth 5
]

MAX_DEPTH = 6

# Wall shade by depth (white to dark gray)
WALL_SHADES = [
    (255, 255, 255),
    (200, 200, 200),
    (160, 160, 160),
    (120, 120, 120),
    (90, 90, 90),
    (70, 70, 70),
]

EDGE_SHADES = [
    (180, 180, 180),
    (140, 140, 140),
    (110, 110, 110),
    (80, 80, 80),
    (60, 60, 60),
    (50, 50, 50),
]

# Floor/ceiling colors
FLOOR_COLOR = (40, 40, 50)
CEIL_COLOR = (25, 25, 35)


class RexState(Enum):
    DORMANT = auto()
    HUNTING = auto()
    APPROACHING = auto()
    SEEN = auto()
    BEHIND = auto()


REX_MESSAGES = {
    RexState.DORMANT: "REX WAITS",
    RexState.HUNTING: "HE IS HUNTING",
    RexState.APPROACHING: "FOOTSTEPS...",
    RexState.SEEN: "RUN HE SEES U",
    RexState.BEHIND: "RUN! BEHIND U",
}

REX_INTERVALS = {
    RexState.DORMANT: 999.0,
    RexState.HUNTING: 0.8,
    RexState.APPROACHING: 0.6,
    RexState.SEEN: 0.4,
    RexState.BEHIND: 0.3,
}

REX_MSG_COLORS = {
    RexState.DORMANT: (100, 100, 100),
    RexState.HUNTING: (180, 180, 0),
    RexState.APPROACHING: (255, 160, 0),
    RexState.SEEN: (255, 80, 0),
    RexState.BEHIND: (255, 0, 0),
}

# Rex sprite colors
REX_BODY = (0, 200, 0)
REX_DETAIL = (0, 120, 0)
REX_EYE = (255, 0, 0)
REX_TEETH = (255, 255, 255)

# Exit colors
EXIT_COLOR = (255, 255, 100)
EXIT_GLOW = (255, 200, 50)


# =============================================================================
# Maze generation
# =============================================================================

def generate_maze():
    """Recursive backtracker on 16x16 grid. Carve from (13,13) stepping 2 cells."""
    walls = [[True] * MAZE_SIZE for _ in range(MAZE_SIZE)]

    def carve(x, y):
        walls[y][x] = False
        dirs = [0, 1, 2, 3]
        random.shuffle(dirs)
        for d in dirs:
            nx, ny = x + DX[d] * 2, y + DY[d] * 2
            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE and walls[ny][nx]:
                walls[y + DY[d]][x + DX[d]] = False
                carve(nx, ny)

    carve(13, 13)
    return walls


def bfs_distance(walls, sx, sy, tx, ty):
    """BFS shortest path length between two open cells. Returns -1 if unreachable."""
    if walls[sy][sx] or walls[ty][tx]:
        return -1
    if sx == tx and sy == ty:
        return 0
    visited = [[False] * MAZE_SIZE for _ in range(MAZE_SIZE)]
    visited[sy][sx] = True
    q = deque([(sx, sy, 0)])
    while q:
        cx, cy, dist = q.popleft()
        for d in range(4):
            nx, ny = cx + DX[d], cy + DY[d]
            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE and not walls[ny][nx] and not visited[ny][nx]:
                if nx == tx and ny == ty:
                    return dist + 1
                visited[ny][nx] = True
                q.append((nx, ny, dist + 1))
    return -1


def bfs_next_step(walls, sx, sy, tx, ty):
    """BFS from (sx,sy) to (tx,ty). Returns (nx,ny) for next step, or None."""
    if sx == tx and sy == ty:
        return None
    if walls[sy][sx] or walls[ty][tx]:
        return None
    visited = [[False] * MAZE_SIZE for _ in range(MAZE_SIZE)]
    visited[sy][sx] = True
    parent = {}
    q = deque([(sx, sy)])
    while q:
        cx, cy = q.popleft()
        for d in range(4):
            nx, ny = cx + DX[d], cy + DY[d]
            if 0 <= nx < MAZE_SIZE and 0 <= ny < MAZE_SIZE and not walls[ny][nx] and not visited[ny][nx]:
                visited[ny][nx] = True
                parent[(nx, ny)] = (cx, cy)
                if nx == tx and ny == ty:
                    # Trace back to find first step
                    cur = (tx, ty)
                    while parent[cur] != (sx, sy):
                        cur = parent[cur]
                    return cur
                q.append((nx, ny))
    return None


def manhattan(x1, y1, x2, y2):
    return abs(x1 - x2) + abs(y1 - y2)


# =============================================================================
# Game
# =============================================================================

class MonsterMaze(Game):
    name = "3D MONSTR MAZE"
    description = "Escape the T-Rex!"
    category = "retro"

    STEP_COOLDOWN = 0.2

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.level = 1
        self.steps = 0
        self._init_level()
        self.phase = 'title'
        self.phase_timer = 2.0

    def _init_level(self):
        """Generate maze and place player, exit, rex."""
        self.walls = generate_maze()
        self.visited = [[False] * MAZE_SIZE for _ in range(MAZE_SIZE)]

        # Player at (13,13) facing north
        self.px, self.py = 13, 13
        self.facing = 0  # North
        self.visited[self.py][self.px] = True
        self.step_cooldown = 0.0

        # Place exit in NW quadrant, manhattan >= 10 from start
        open_cells = []
        for y in range(MAZE_SIZE):
            for x in range(MAZE_SIZE):
                if not self.walls[y][x] and x < 8 and y < 8:
                    if manhattan(x, y, 13, 13) >= 10:
                        open_cells.append((x, y))
        if not open_cells:
            # Fallback: any open cell far enough
            for y in range(MAZE_SIZE):
                for x in range(MAZE_SIZE):
                    if not self.walls[y][x] and manhattan(x, y, 13, 13) >= 8:
                        open_cells.append((x, y))
        if not open_cells:
            open_cells = [(1, 1)]
        self.exit_x, self.exit_y = random.choice(open_cells)

        # Place Rex in north half, distance >= 6 from player
        rex_cells = []
        min_rex_dist = max(3, 6 - (self.level - 1))
        for y in range(MAZE_SIZE // 2):
            for x in range(MAZE_SIZE):
                if not self.walls[y][x] and (x, y) != (self.exit_x, self.exit_y):
                    if manhattan(x, y, 13, 13) >= min_rex_dist:
                        rex_cells.append((x, y))
        if not rex_cells:
            rex_cells = [(1, 5)]
        self.rex_x, self.rex_y = random.choice(rex_cells)
        self.rex_state = RexState.DORMANT
        self.rex_timer = 0.0
        self.rex_jaw_open = False
        self.rex_jaw_timer = 0.0
        self.player_moved = False

        # Animation timers
        self.flash_timer = 0.0
        self.flash_color = None
        self.caught_timer = 0.0
        self.escaped_timer = 0.0
        self.exit_pulse = 0.0

    def _speed_scale(self):
        return max(0.5, 1.0 - (self.level - 1) * 0.05)

    def _has_wall(self, x, y):
        """Check if cell (x,y) is a wall or out of bounds."""
        if x < 0 or x >= MAZE_SIZE or y < 0 or y >= MAZE_SIZE:
            return True
        return self.walls[y][x]

    def _los_check(self):
        """Check if Rex is visible straight ahead, up to 6 cells."""
        dx, dy = DX[self.facing], DY[self.facing]
        cx, cy = self.px, self.py
        for i in range(1, 7):
            cx += dx
            cy += dy
            if self._has_wall(cx, cy):
                return -1  # Wall blocks LOS
            if cx == self.rex_x and cy == self.rex_y:
                return i  # Rex at depth i
        return -1

    def _rex_dist(self):
        """BFS distance from rex to player."""
        return bfs_distance(self.walls, self.rex_x, self.rex_y, self.px, self.py)

    # -----------------------------------------------------------------
    # Update
    # -----------------------------------------------------------------

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.exit_pulse += dt * 4.0
        self.rex_jaw_timer += dt
        if self.rex_jaw_timer >= 0.3:
            self.rex_jaw_timer = 0.0
            self.rex_jaw_open = not self.rex_jaw_open

        # Phase handling
        if self.phase == 'title':
            self.phase_timer -= dt
            if self.phase_timer <= 0:
                self.phase = 'playing'
            return

        if self.phase == 'caught':
            self.caught_timer -= dt
            if self.caught_timer <= 0:
                self.state = GameState.GAME_OVER
            return

        if self.phase == 'escaped':
            self.escaped_timer -= dt
            if self.escaped_timer <= 0:
                self.level += 1
                self._init_level()
                self.phase = 'playing'
            return

        # Flash timer
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # Step cooldown
        if self.step_cooldown > 0:
            self.step_cooldown -= dt

        # Player input
        if input_state.left_pressed:
            self.facing = (self.facing - 1) % 4
        elif input_state.right_pressed:
            self.facing = (self.facing + 1) % 4
        elif input_state.up_pressed and self.step_cooldown <= 0:
            dx, dy = DX[self.facing], DY[self.facing]
            nx, ny = self.px + dx, self.py + dy
            if not self._has_wall(nx, ny):
                self.px, self.py = nx, ny
                self.visited[self.py][self.px] = True
                self.steps += 1
                self.step_cooldown = self.STEP_COOLDOWN
                self.player_moved = True
        elif input_state.action_l and self.step_cooldown <= 0:
            # Sprint: move forward 2 cells if both open
            dx, dy = DX[self.facing], DY[self.facing]
            nx1, ny1 = self.px + dx, self.py + dy
            nx2, ny2 = self.px + dx * 2, self.py + dy * 2
            if not self._has_wall(nx1, ny1) and not self._has_wall(nx2, ny2):
                self.px, self.py = nx2, ny2
                self.visited[ny1][nx1] = True
                self.visited[self.py][self.px] = True
                self.steps += 2
                self.step_cooldown = self.STEP_COOLDOWN * 1.5
                self.player_moved = True

        # Check exit
        if self.px == self.exit_x and self.py == self.exit_y:
            self.phase = 'escaped'
            self.escaped_timer = 1.5
            self.flash_timer = 0.3
            self.flash_color = (0, 255, 0)
            bonus = 100 * self.level + max(0, 500 - self.steps * 5)
            self.score += bonus
            return

        # Update Rex
        self._update_rex(dt)

        # Check caught
        if self.rex_x == self.px and self.rex_y == self.py:
            self.phase = 'caught'
            self.caught_timer = 2.0
            self.flash_timer = 0.3
            self.flash_color = (255, 0, 0)

    def _update_rex(self, dt):
        """Update Rex AI state machine and movement."""
        if self.rex_state == RexState.DORMANT:
            if self.player_moved:
                self.rex_state = RexState.HUNTING
                self.rex_timer = 0.0
            return

        dist = self._rex_dist()
        los = self._los_check()

        # State transitions
        if self.rex_state == RexState.HUNTING:
            if los > 0:
                self.rex_state = RexState.SEEN
            elif dist != -1 and dist <= 6:
                self.rex_state = RexState.APPROACHING
        elif self.rex_state == RexState.APPROACHING:
            if los > 0:
                self.rex_state = RexState.SEEN
            elif dist != -1 and dist <= 2:
                self.rex_state = RexState.BEHIND
            elif dist != -1 and dist > 8:
                self.rex_state = RexState.HUNTING
        elif self.rex_state == RexState.SEEN:
            if dist != -1 and dist <= 2:
                self.rex_state = RexState.BEHIND
            elif los <= 0:
                self.rex_state = RexState.APPROACHING
        elif self.rex_state == RexState.BEHIND:
            if dist != -1 and dist > 3:
                if los > 0:
                    self.rex_state = RexState.SEEN
                else:
                    self.rex_state = RexState.APPROACHING

        # Movement
        interval = REX_INTERVALS[self.rex_state] * self._speed_scale()
        self.rex_timer += dt
        if self.rex_timer >= interval:
            self.rex_timer = 0.0
            self._move_rex()

    def _move_rex(self):
        """Move Rex one step."""
        if self.rex_state == RexState.HUNTING:
            # Random wander
            dirs = [0, 1, 2, 3]
            random.shuffle(dirs)
            for d in dirs:
                nx, ny = self.rex_x + DX[d], self.rex_y + DY[d]
                if not self._has_wall(nx, ny):
                    self.rex_x, self.rex_y = nx, ny
                    return
        else:
            # BFS pursuit
            nxt = bfs_next_step(self.walls, self.rex_x, self.rex_y, self.px, self.py)
            if nxt:
                self.rex_x, self.rex_y = nxt

    # -----------------------------------------------------------------
    # Draw
    # -----------------------------------------------------------------

    def draw(self):
        self.display.clear(Colors.BLACK)

        if self.phase == 'title':
            self._draw_title()
            return

        if self.phase == 'caught':
            self._draw_caught()
            return

        # Draw floor and ceiling
        self._draw_floor_ceiling()

        # Draw 3D viewport
        self._draw_3d_view()

        # Flash overlay
        if self.flash_timer > 0 and self.flash_color:
            alpha = min(1.0, self.flash_timer / 0.15)
            r, g, b = self.flash_color
            fc = (int(r * alpha), int(g * alpha), int(b * alpha))
            for y in range(VIEWPORT_H):
                for x in range(GRID_SIZE):
                    pr, pg, pb = self.display.get_pixel(x, y)
                    nr = min(255, pr + fc[0])
                    ng = min(255, pg + fc[1])
                    nb = min(255, pb + fc[2])
                    self.display.set_pixel(x, y, (nr, ng, nb))

        # Status bar
        self._draw_status()

        # HUD + minimap
        self._draw_hud()
        self._draw_minimap()

    def _draw_title(self):
        self.display.draw_text_small(6, 14, "3D MONSTER", Colors.GREEN)
        self.display.draw_text_small(18, 22, "MAZE", Colors.GREEN)
        self.display.draw_text_small(2, 38, "FIND THE EXIT", Colors.YELLOW)
        self.display.draw_text_small(6, 50, f"LEVEL {self.level}", Colors.WHITE)

    def _draw_caught(self):
        """Draw Rex filling screen + message."""
        # Red-tinted background
        self.display.clear((40, 0, 0))

        # Big Rex face
        cx, cy = 32, 20
        # Head
        for dy in range(-8, 5):
            w = 10 - abs(dy) // 2
            for dx in range(-w, w + 1):
                self.display.set_pixel(cx + dx, cy + dy, REX_BODY)
        # Eyes
        self.display.set_pixel(cx - 4, cy - 3, REX_EYE)
        self.display.set_pixel(cx + 4, cy - 3, REX_EYE)
        self.display.set_pixel(cx - 3, cy - 3, REX_EYE)
        self.display.set_pixel(cx + 3, cy - 3, REX_EYE)
        # Mouth/teeth
        for dx in range(-6, 7):
            self.display.set_pixel(cx + dx, cy + 3, REX_DETAIL)
        for dx in range(-5, 6, 2):
            self.display.set_pixel(cx + dx, cy + 4, REX_TEETH)

        self.display.draw_text_small(6, 34, "REX GOT YOU", Colors.RED)
        self.display.draw_text_small(6, 46, f"SCORE:{self.score}", Colors.WHITE)

    def _draw_floor_ceiling(self):
        """Draw floor and ceiling gradient."""
        mid = VIEWPORT_H // 2
        for y in range(VIEWPORT_H):
            if y < mid:
                # Ceiling - darker near top
                shade = max(10, 25 - (mid - y))
                c = (shade, shade, shade + 5)
            else:
                # Floor - darker further away
                dist = y - mid
                shade = min(50, 20 + dist)
                c = (shade, shade, shade - 5 if shade > 5 else 0)
            for x in range(GRID_SIZE):
                self.display.set_pixel(x, y, c)

    def _draw_3d_view(self):
        """Render 3D maze view using pre-computed depth geometry."""
        dx, dy = DX[self.facing], DY[self.facing]
        # Left/right relative to facing
        ldx, ldy = DX[(self.facing - 1) % 4], DY[(self.facing - 1) % 4]
        rdx, rdy = DX[(self.facing + 1) % 4], DY[(self.facing + 1) % 4]

        # Render back-to-front
        max_d = min(MAX_DEPTH, len(DEPTH_TABLE))

        # First pass: determine what's visible at each depth
        render_list = []
        cx, cy = self.px, self.py
        for depth in range(max_d):
            fcx, fcy = cx + dx, cy + dy  # cell ahead
            left_wall = self._has_wall(cx + ldx, cy + ldy)
            right_wall = self._has_wall(cx + rdx, cy + rdy)
            front_wall = self._has_wall(fcx, fcy)

            # Check for Rex and Exit at this cell (ahead)
            rex_here = (not front_wall and fcx == self.rex_x and fcy == self.rex_y)
            exit_here = (not front_wall and fcx == self.exit_x and fcy == self.exit_y)
            # Also check current cell for depth 0
            if depth == 0:
                if cx == self.exit_x and cy == self.exit_y:
                    exit_here = True

            render_list.append({
                'depth': depth,
                'left_wall': left_wall,
                'right_wall': right_wall,
                'front_wall': front_wall,
                'rex': rex_here,
                'exit': exit_here,
            })

            if front_wall:
                break
            cx, cy = fcx, fcy

        # Draw back-to-front (reverse order)
        for entry in reversed(render_list):
            d = entry['depth']
            if d >= len(DEPTH_TABLE):
                continue
            xl, xr, yt, yb, wall_w = DEPTH_TABLE[d]
            h = yb - yt + 1
            shade = WALL_SHADES[d]
            edge = EDGE_SHADES[d]

            # Draw side walls
            if entry['left_wall']:
                self.display.draw_rect(xl, yt, wall_w, h, shade)
                # Edge line
                self.display.draw_line(xl + wall_w - 1, yt, xl + wall_w - 1, yb, edge)

            if entry['right_wall']:
                self.display.draw_rect(xr - wall_w + 1, yt, wall_w, h, shade)
                # Edge line
                self.display.draw_line(xr - wall_w + 1, yt, xr - wall_w + 1, yb, edge)

            # Front wall
            if entry['front_wall']:
                fw = xr - xl + 1
                self.display.draw_rect(xl, yt, fw, h, shade)
                # Edge border
                self.display.draw_line(xl, yt, xr, yt, edge)
                self.display.draw_line(xl, yb, xr, yb, edge)
                self.display.draw_line(xl, yt, xl, yb, edge)
                self.display.draw_line(xr, yt, xr, yb, edge)

            # Draw exit
            if entry['exit']:
                self._draw_exit(d + 1)

            # Draw Rex
            if entry['rex']:
                self._draw_rex(d + 1)

    def _draw_exit(self, depth):
        """Draw exit doorway at given depth."""
        if depth >= len(DEPTH_TABLE):
            return
        xl, xr, yt, yb, _ = DEPTH_TABLE[depth]
        mid_x = (xl + xr) // 2
        mid_y = (yt + yb) // 2
        hw = max(1, (xr - xl) // 4)
        hh = max(1, (yb - yt) // 3)

        # Pulsing brightness
        pulse = int(180 + 75 * (0.5 + 0.5 * (1.0 if int(self.exit_pulse) % 2 == 0 else 0.0)))
        pulse = min(255, pulse)
        color = (pulse, pulse, min(255, pulse // 2))

        # Draw doorway arch
        for dy in range(-hh, hh + 1):
            w = hw if dy >= 0 else max(1, hw - abs(dy) // 2)
            for ddx in range(-w, w + 1):
                px, py = mid_x + ddx, mid_y + dy
                if 0 <= px < GRID_SIZE and 0 <= py < VIEWPORT_H:
                    self.display.set_pixel(px, py, color)

    def _draw_rex(self, depth):
        """Draw Rex sprite at given corridor depth."""
        if depth > 6:
            return
        if depth >= len(DEPTH_TABLE):
            # Very far: tiny dot
            self.display.set_pixel(32, 22, REX_BODY)
            return

        xl, xr, yt, yb, _ = DEPTH_TABLE[depth]
        mid_x = (xl + xr) // 2
        mid_y = (yt + yb) // 2
        view_h = yb - yt

        if depth >= 5:
            # Tiny: 1-2 pixel dot
            self.display.set_pixel(mid_x, mid_y, REX_BODY)
            if depth == 5:
                self.display.set_pixel(mid_x, mid_y - 1, REX_BODY)
        elif depth >= 3:
            # Small: head + body (6-8px tall)
            size = max(3, view_h // 5)
            # Body
            for dy in range(-size, size + 1):
                w = max(1, size - abs(dy) // 2)
                for ddx in range(-w, w + 1):
                    self.display.set_pixel(mid_x + ddx, mid_y + dy, REX_BODY)
            # Eye
            self.display.set_pixel(mid_x, mid_y - size + 1, REX_EYE)
        else:
            # Large/medium: full rex
            body_h = max(6, view_h // 3)
            body_w = max(3, (xr - xl) // 6)

            # Body
            for dy in range(-body_h // 2, body_h // 2 + 1):
                w = body_w
                if dy < -body_h // 4:
                    w = max(1, body_w - 1)  # Narrow head
                for ddx in range(-w, w + 1):
                    self.display.set_pixel(mid_x + ddx, mid_y + dy, REX_BODY)

            # Head details
            head_y = mid_y - body_h // 2
            # Eyes
            ew = max(1, body_w - 1)
            self.display.set_pixel(mid_x - ew, head_y + 1, REX_EYE)
            self.display.set_pixel(mid_x + ew, head_y + 1, REX_EYE)

            # Jaw
            jaw_y = head_y + body_h // 4
            if self.rex_jaw_open:
                jaw_w = max(2, body_w)
                for ddx in range(-jaw_w, jaw_w + 1):
                    self.display.set_pixel(mid_x + ddx, jaw_y, REX_DETAIL)
                    self.display.set_pixel(mid_x + ddx, jaw_y + 1, REX_DETAIL)
                # Teeth
                for ddx in range(-jaw_w + 1, jaw_w, 2):
                    self.display.set_pixel(mid_x + ddx, jaw_y, REX_TEETH)
            else:
                jaw_w = max(2, body_w)
                for ddx in range(-jaw_w, jaw_w + 1):
                    self.display.set_pixel(mid_x + ddx, jaw_y, REX_DETAIL)

            # Arms (small)
            arm_y = mid_y
            self.display.set_pixel(mid_x - body_w - 1, arm_y, REX_DETAIL)
            self.display.set_pixel(mid_x + body_w + 1, arm_y, REX_DETAIL)

            # Legs
            leg_y = mid_y + body_h // 2
            lw = max(1, body_w - 1)
            self.display.set_pixel(mid_x - lw, leg_y, REX_BODY)
            self.display.set_pixel(mid_x - lw, leg_y + 1, REX_BODY)
            self.display.set_pixel(mid_x + lw, leg_y, REX_BODY)
            self.display.set_pixel(mid_x + lw, leg_y + 1, REX_BODY)

            # Tail
            tail_x = mid_x + body_w + 1
            tail_y = mid_y + body_h // 4
            self.display.set_pixel(tail_x, tail_y, REX_DETAIL)
            if depth <= 1:
                self.display.set_pixel(tail_x + 1, tail_y - 1, REX_DETAIL)

    def _draw_status(self):
        """Draw status message bar."""
        if self.phase == 'escaped':
            self.display.draw_text_small(2, STATUS_Y, "ESCAPED!", Colors.GREEN)
            lbl = f"L{self.level}"
            self.display.draw_text_small(50, STATUS_Y, lbl, Colors.CYAN)
            return

        msg = REX_MESSAGES.get(self.rex_state, "")
        color = REX_MSG_COLORS.get(self.rex_state, Colors.WHITE)

        # Flash text for BEHIND state
        if self.rex_state == RexState.BEHIND:
            if int(self.exit_pulse * 3) % 2 == 0:
                color = Colors.RED
            else:
                color = Colors.YELLOW

        self.display.draw_text_small(2, STATUS_Y, msg, color)
        lbl = f"L{self.level}"
        self.display.draw_text_small(50, STATUS_Y, lbl, Colors.CYAN)

    def _draw_hud(self):
        """Draw bottom HUD: facing direction and score."""
        dirs = ['N', 'E', 'S', 'W']
        self.display.draw_text_small(2, HUD_Y, dirs[self.facing], Colors.WHITE)
        score_str = f"S:{self.score:03d}"
        self.display.draw_text_small(10, HUD_Y, score_str, Colors.YELLOW)

    def _draw_minimap(self):
        """Draw 12x12 minimap centered on player, showing visited cells."""
        half = MINIMAP_SIZE // 2
        for my in range(MINIMAP_SIZE):
            for mx in range(MINIMAP_SIZE):
                # Map coords
                wx = self.px - half + mx
                wy = self.py - half + my
                sx = MINIMAP_X + mx
                sy = MINIMAP_Y + my

                if wx < 0 or wx >= MAZE_SIZE or wy < 0 or wy >= MAZE_SIZE:
                    self.display.set_pixel(sx, sy, (15, 15, 15))
                    continue

                if not self.visited[wy][wx]:
                    self.display.set_pixel(sx, sy, (15, 15, 15))
                    continue

                if self.walls[wy][wx]:
                    self.display.set_pixel(sx, sy, (60, 60, 60))
                else:
                    self.display.set_pixel(sx, sy, (30, 30, 30))

                # Player
                if wx == self.px and wy == self.py:
                    self.display.set_pixel(sx, sy, Colors.CYAN)
                # Exit (always show if visited)
                elif wx == self.exit_x and wy == self.exit_y:
                    self.display.set_pixel(sx, sy, Colors.YELLOW)
                # Rex (only in SEEN/BEHIND)
                elif (wx == self.rex_x and wy == self.rex_y and
                      self.rex_state in (RexState.SEEN, RexState.BEHIND)):
                    self.display.set_pixel(sx, sy, Colors.RED)

    def draw_game_over(self, selection: int = 0):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(4, 10, "GAME OVER", Colors.RED)
        self.display.draw_text_small(2, 22, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(2, 32, f"LEVEL:{self.level}", Colors.CYAN)

        if selection == 0:
            self.display.draw_text_small(2, 46, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 46, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 46, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 46, ">MENU", Colors.YELLOW)

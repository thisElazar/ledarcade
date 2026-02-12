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
import random
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
SPLITTER_BK = 11  # Half-silvered \: pass-through + BK-style reflection
SPLITTER_FW = 12  # Half-silvered /: pass-through + FW-style reflection
DOOR = 13         # Wall that opens when linked SWITCH is charged
SWITCH = 14       # Cyan target — when lit, opens linked DOOR

EMITTER_DIRS = {
    EMITTER_N: (0, -1),
    EMITTER_S: (0, 1),
    EMITTER_E: (1, 0),
    EMITTER_W: (-1, 0),
}

# Mirror system — 4 orientations, 45° apart, each press rotates CCW
MIRROR_TYPES = {MIRROR_BK, MIRROR_FW, MIRROR_V, MIRROR_H}
SPLITTER_TYPES = {SPLITTER_BK, SPLITTER_FW}
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

# Splitter reflection: maps incoming (dx,dy) -> reflected (dx,dy), same as corresponding mirror
# The pass-through component just continues (dx,dy) unchanged
SPLITTER_REFLECT = {
    SPLITTER_BK: MIRROR_REFLECT[MIRROR_BK],  # \ reflection
    SPLITTER_FW: MIRROR_REFLECT[MIRROR_FW],   # / reflection
}

# Colors
STONE_COLOR = (40, 45, 70)
STONE_DARK = (30, 34, 55)
MIRROR_COLOR = (140, 180, 220)
TARGET_UNLIT = (60, 80, 60)
TARGET_LIT = (40, 255, 80)
LASER_CORE = (255, 80, 20)
LASER_GLOW = (80, 30, 10)
SPLITTER_COLOR = (180, 200, 255)
SWITCH_UNLIT = (40, 80, 90)
SWITCH_LIT = (40, 255, 255)
DOOR_COLOR = (90, 70, 50)
DOOR_BAR = (50, 40, 30)
CEIL_COLOR = (15, 18, 30)
FLOOR_LIGHT = (35, 38, 55)
FLOOR_DARK = (28, 30, 45)

# ═══════════════════════════════════════════════════════════════════
#  Procedural Level Generation
# ═══════════════════════════════════════════════════════════════════

def difficulty_params(level_idx):
    """Map level number to generation parameters."""
    i = level_idx
    if i <= 2:      # Tier 1
        return dict(room_w=7, room_h=7, emitters=1, mirrors=(1, 2), targets=1,
                    splitters=0, door=False, decoys=(0, 1), walls=0, par_base=25, par_per=5)
    elif i <= 5:    # Tier 2
        return dict(room_w=8, room_h=9, emitters=1, mirrors=(2, 3), targets=(1, 2),
                    splitters=0, door=False, decoys=(1, 2), walls=0, par_base=30, par_per=5)
    elif i <= 8:    # Tier 3
        return dict(room_w=10, room_h=10, emitters=(1, 2), mirrors=(2, 3), targets=2,
                    splitters=1, door=False, decoys=(2, 3), walls=(1, 2), par_base=35, par_per=5)
    elif i <= 11:   # Tier 4
        return dict(room_w=11, room_h=11, emitters=(1, 2), mirrors=(3, 4), targets=(2, 3),
                    splitters=1, door=True, decoys=(2, 3), walls=(2, 3), par_base=40, par_per=5)
    else:           # Tier 5+
        s = min(i - 12, 20)
        w = min(14, 11 + s // 4)
        h = min(14, 11 + s // 4)
        return dict(room_w=w, room_h=h, emitters=(1, min(3, 1 + s // 5)),
                    mirrors=(3, min(8, 4 + s // 3)), targets=(2, min(5, 2 + s // 4)),
                    splitters=(1, min(2, 1 + s // 6)), door=(i % 2 == 1),
                    decoys=(2, min(6, 3 + s // 3)), walls=(2, min(6, 3 + s // 3)),
                    par_base=45, par_per=4)


def _pick(rng, val):
    """Pick a value from int or (min, max) tuple."""
    if isinstance(val, tuple):
        return rng.randint(val[0], val[1])
    if isinstance(val, bool):
        return val
    return val


def _opposite_dir(dx, dy):
    return (-dx, -dy)


def _get_turn_options(dx, dy):
    """Return list of (mirror_type, new_dx, new_dy) for turning a beam 90 degrees."""
    options = []
    for mt in (MIRROR_BK, MIRROR_FW):
        ref = MIRROR_REFLECT[mt].get((dx, dy))
        if ref and ref != (dx, dy) and ref != (-dx, -dy):
            options.append((mt, ref[0], ref[1]))
    return options


def _max_travel(grid, cx, cy, dx, dy, occupied, h, w):
    """How many cells beam can travel before hitting something."""
    dist = 0
    nx, ny = cx, cy
    while True:
        nx, ny = nx + dx, ny + dy
        if nx <= 0 or nx >= w - 1 or ny <= 0 or ny >= h - 1:
            break
        if grid[ny][nx] != EMPTY:
            break
        if (nx, ny) in occupied:
            break
        dist += 1
    return dist


def _room_is_connected(grid, h, w):
    """BFS flood fill — confirm all empty interior cells are reachable."""
    start = None
    for y in range(1, h - 1):
        for x in range(1, w - 1):
            if grid[y][x] == EMPTY:
                start = (x, y)
                break
        if start:
            break
    if not start:
        return True
    visited = {start}
    queue = [start]
    while queue:
        cx, cy = queue.pop()
        for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = cx + ddx, cy + ddy
            if 0 < nx < w - 1 and 0 < ny < h - 1 and (nx, ny) not in visited:
                if grid[ny][nx] == EMPTY:
                    visited.add((nx, ny))
                    queue.append((nx, ny))
    # Count all empty interior cells
    total = sum(1 for y in range(1, h - 1) for x in range(1, w - 1) if grid[y][x] == EMPTY)
    return len(visited) >= total


def _verify_solution(grid, emitters, targets, switches, door_link, h, w):
    """Trace all beams through grid, return (targets_hit, switches_hit) as sets of (x,y)."""
    targets_hit = set()
    switches_hit = set()

    def trace(sx, sy, ddx, ddy, depth=0):
        if depth > 12:
            return
        cx, cy = sx, sy
        for _ in range(50):
            nx, ny = cx + ddx, cy + ddy
            if nx < 0 or nx >= w or ny < 0 or ny >= h:
                break
            cell = grid[ny][nx]
            if cell == WALL or cell in EMITTER_DIRS:
                break
            if cell == TARGET:
                targets_hit.add((nx, ny))
                break
            if cell == SWITCH:
                switches_hit.add((nx, ny))
                break
            if cell == DOOR:
                # Door blocks unless switch is hit
                if door_link and (nx, ny) == door_link[1]:
                    switch_pos = door_link[0]
                    if switch_pos in switches_hit:
                        # Door is open - pass through
                        cx, cy = nx, ny
                        continue
                break
            if cell in MIRROR_REFLECT:
                ddx, ddy = MIRROR_REFLECT[cell][(ddx, ddy)]
                cx, cy = nx, ny
                continue
            if cell in SPLITTER_TYPES:
                # Pass through
                trace(nx, ny, ddx, ddy, depth + 1)
                # Reflect
                rdx, rdy = SPLITTER_REFLECT[cell][(ddx, ddy)]
                trace(nx, ny, rdx, rdy, depth + 1)
                return
            cx, cy = nx, ny

    for ex, ey, etype in emitters:
        ddx, ddy = EMITTER_DIRS[etype]
        trace(ex, ey, ddx, ddy)

    target_set = {(x, y) for x, y in targets}
    switch_set = {(x, y) for x, y in switches}
    return targets_hit >= target_set, switches_hit >= switch_set


def generate_level(level_idx, seed):
    """Generate a procedural level. Returns dict with 'map', 'start', 'par', 'door_link'."""
    rng = random.Random(seed)
    params = difficulty_params(level_idx)
    rw = params['room_w']
    rh = params['room_h']
    n_emitters = _pick(rng, params['emitters'])
    n_mirrors = _pick(rng, params['mirrors'])
    n_targets = _pick(rng, params['targets']) if isinstance(params['targets'], tuple) else params['targets']
    n_splitters = _pick(rng, params['splitters'])
    use_door = _pick(rng, params['door'])
    n_decoys = _pick(rng, params['decoys'])
    n_walls = _pick(rng, params['walls'])

    par = params['par_base'] + n_mirrors * params['par_per']

    for attempt in range(100):
        # Re-pick counts each attempt for variety
        a_rng = random.Random(seed + attempt)
        a_emitters = _pick(a_rng, params['emitters'])
        a_mirrors = _pick(a_rng, params['mirrors'])
        a_targets = _pick(a_rng, params['targets']) if isinstance(params['targets'], tuple) else params['targets']
        a_splitters = _pick(a_rng, params['splitters'])
        a_decoys = _pick(a_rng, params['decoys'])
        a_walls = _pick(a_rng, params['walls'])
        a_par = params['par_base'] + a_mirrors * params['par_per']
        result = _try_generate(a_rng, rw, rh, a_emitters, a_mirrors, a_targets,
                               a_splitters, use_door, a_decoys, a_walls, a_par)
        if result is not None:
            return result

    return _fallback_level(level_idx, rw, rh)


def _try_generate(rng, rw, rh, n_emitters, n_mirrors, n_targets,
                  n_splitters, use_door, n_decoys, n_walls, par):
    """Single attempt at generating a level. Returns dict or None."""
    # 1. Empty walled room
    grid = [[EMPTY] * rw for _ in range(rh)]
    for x in range(rw):
        grid[0][x] = WALL
        grid[rh - 1][x] = WALL
    for y in range(rh):
        grid[y][0] = WALL
        grid[y][rw - 1] = WALL

    occupied = set()  # cells reserved by beam paths / elements
    solution_mirrors = {}  # (x,y) -> mirror_type (correct orientation)
    emitters = []
    targets = []
    switches = []
    beam_path_cells = set()  # all cells the beam passes through

    # 2. Place emitters on border walls (fire inward)
    border_spots = []
    for x in range(2, rw - 2):
        border_spots.append((x, 0, EMITTER_S))      # top wall, fires south
        border_spots.append((x, rh - 1, EMITTER_N))  # bottom wall, fires north
    for y in range(2, rh - 2):
        border_spots.append((0, y, EMITTER_E))       # left wall, fires east
        border_spots.append((rw - 1, y, EMITTER_W))  # right wall, fires west

    rng.shuffle(border_spots)
    placed_emitters = 0
    for ex, ey, etype in border_spots:
        if placed_emitters >= n_emitters:
            break
        # Don't place two emitters adjacent
        too_close = False
        for px, py, _ in emitters:
            if abs(ex - px) + abs(ey - py) < 3:
                too_close = True
                break
        if too_close:
            continue
        grid[ey][ex] = etype
        emitters.append((ex, ey, etype))
        occupied.add((ex, ey))
        placed_emitters += 1

    if placed_emitters < n_emitters:
        return None

    # 3. Build solution beam paths from each emitter
    mirrors_placed = 0
    splitters_placed = 0
    targets_placed = 0

    # Calculate targets per emitter
    targets_per_emitter = []
    remaining_targets = n_targets
    for i in range(n_emitters):
        if i == n_emitters - 1:
            targets_per_emitter.append(max(1, remaining_targets))
        else:
            t = max(1, remaining_targets // (n_emitters - i))
            targets_per_emitter.append(t)
            remaining_targets -= t

    for ei, (ex, ey, etype) in enumerate(emitters):
        dx, dy = EMITTER_DIRS[etype]
        cx, cy = ex, ey
        n_tgt = targets_per_emitter[ei]
        tgt_placed_this = 0
        path_mirrors = 0
        max_path_mirrors = n_mirrors - mirrors_placed if ei == n_emitters - 1 else max(1, (n_mirrors - mirrors_placed) // (n_emitters - ei))

        for step in range(30):
            # Travel 1-5 cells in current direction
            max_d = _max_travel(grid, cx, cy, dx, dy, occupied, rh, rw)
            if max_d < 1:
                break

            # Allow short travel (1 cell) for mirror turns; prefer 2+ for targets
            min_travel = 1
            travel = rng.randint(min_travel, min(5, max_d))

            # Mark beam path cells
            for d in range(1, travel + 1):
                bx, by = cx + dx * d, cy + dy * d
                beam_path_cells.add((bx, by))

            # Move to end of travel
            cx, cy = cx + dx * travel, cy + dy * travel

            # Decide: place target or place mirror to turn
            need_more_targets = tgt_placed_this < n_tgt
            need_more_mirrors = path_mirrors < max_path_mirrors

            # Try splitter first if we have them to place
            if splitters_placed < n_splitters and need_more_mirrors and need_more_targets and rng.random() < 0.4:
                # Place splitter: beam passes through AND reflects
                turn_opts = _get_turn_options(dx, dy)
                if turn_opts:
                    mt, rdx, rdy = rng.choice(turn_opts)
                    spl_type = SPLITTER_BK if mt == MIRROR_BK else SPLITTER_FW
                    grid[cy][cx] = spl_type
                    occupied.add((cx, cy))
                    splitters_placed += 1

                    # Fork: reflected beam needs a target
                    fork_max = _max_travel(grid, cx, cy, rdx, rdy, occupied, rh, rw)
                    if fork_max >= 1:
                        fork_travel = rng.randint(1, min(4, fork_max))
                        for d in range(1, fork_travel + 1):
                            beam_path_cells.add((cx + rdx * d, cy + rdy * d))
                        ftx, fty = cx + rdx * fork_travel, cy + rdy * fork_travel
                        if 0 < ftx < rw - 1 and 0 < fty < rh - 1 and grid[fty][ftx] == EMPTY and (ftx, fty) not in occupied:
                            grid[fty][ftx] = TARGET
                            targets.append((ftx, fty))
                            occupied.add((ftx, fty))
                            beam_path_cells.add((ftx, fty))
                            tgt_placed_this += 1
                            targets_placed += 1

                    # Pass-through beam continues in same direction
                    continue

            if not need_more_mirrors or (not need_more_targets and rng.random() < 0.5):
                # Place target
                if 0 < cx < rw - 1 and 0 < cy < rh - 1 and grid[cy][cx] == EMPTY and (cx, cy) not in occupied:
                    grid[cy][cx] = TARGET
                    targets.append((cx, cy))
                    occupied.add((cx, cy))
                    beam_path_cells.add((cx, cy))
                    tgt_placed_this += 1
                    targets_placed += 1
                break
            else:
                # Place mirror to turn
                turn_opts = _get_turn_options(dx, dy)
                if not turn_opts:
                    break
                mt, ndx, ndy = rng.choice(turn_opts)
                if 0 < cx < rw - 1 and 0 < cy < rh - 1 and grid[cy][cx] == EMPTY:
                    grid[cy][cx] = mt
                    solution_mirrors[(cx, cy)] = mt
                    occupied.add((cx, cy))
                    mirrors_placed += 1
                    path_mirrors += 1
                    dx, dy = ndx, ndy
                else:
                    break

        # If we still need targets for this emitter, path failed
        if tgt_placed_this < n_tgt:
            return None

    if targets_placed < n_targets:
        return None

    # 4. Door/switch (if enabled and we have at least 2 targets)
    door_link = None
    if use_door and len(targets) >= 2:
        # Convert last target to switch, add door on another beam path
        sw_x, sw_y = targets[-1]
        grid[sw_y][sw_x] = SWITCH
        switches.append((sw_x, sw_y))
        targets.pop()
        targets_placed -= 1

        # Place door: find a cell on a beam path before another target
        door_placed = False
        for tx, ty in targets[:1]:
            # Walk backwards along beam to find a spot for a door
            for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                dx2, dy2 = tx + ddx, ty + ddy
                if (dx2, dy2) in beam_path_cells and grid[dy2][dx2] == EMPTY and (dx2, dy2) not in occupied:
                    grid[dy2][dx2] = DOOR
                    occupied.add((dx2, dy2))
                    door_link = ((sw_x, sw_y), (dx2, dy2))
                    door_placed = True
                    break
            if door_placed:
                break

        if not door_placed:
            # Revert switch back to target
            grid[sw_y][sw_x] = TARGET
            targets.append((sw_x, sw_y))
            targets_placed += 1
            switches.clear()

    # 5. Verify solution
    ok_t, ok_s = _verify_solution(grid, emitters,
                                  targets, switches, door_link, rh, rw)
    if not ok_t:
        return None
    if switches and not ok_s:
        return None

    # 6. Interior walls (short 1-3 cell segments)
    walls_placed = 0
    wall_attempts = 0
    while walls_placed < n_walls and wall_attempts < 40:
        wall_attempts += 1
        wx = rng.randint(2, rw - 3)
        wy = rng.randint(2, rh - 3)
        if grid[wy][wx] != EMPTY or (wx, wy) in occupied:
            continue
        # Don't block beam path or be adjacent to beam path
        if (wx, wy) in beam_path_cells:
            continue
        too_close = False
        for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            if (wx + ddx, wy + ddy) in beam_path_cells:
                too_close = True
                break
        if too_close:
            continue
        # Place wall and check connectivity
        grid[wy][wx] = WALL
        if _room_is_connected(grid, rh, rw):
            occupied.add((wx, wy))
            walls_placed += 1
            # Try extending wall 1-2 more cells
            wdx, wdy = rng.choice([(0, 1), (0, -1), (1, 0), (-1, 0)])
            for ext in range(rng.randint(0, 2)):
                ewx, ewy = wx + wdx * (ext + 1), wy + wdy * (ext + 1)
                if 1 < ewx < rw - 2 and 1 < ewy < rh - 2:
                    if grid[ewy][ewx] == EMPTY and (ewx, ewy) not in occupied and (ewx, ewy) not in beam_path_cells:
                        adj_beam = False
                        for ddx2, ddy2 in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                            if (ewx + ddx2, ewy + ddy2) in beam_path_cells:
                                adj_beam = True
                                break
                        if adj_beam:
                            break
                        grid[ewy][ewx] = WALL
                        if _room_is_connected(grid, rh, rw):
                            occupied.add((ewx, ewy))
                            walls_placed += 1
                        else:
                            grid[ewy][ewx] = EMPTY
                            break
                else:
                    break
        else:
            grid[wy][wx] = EMPTY

    # 7. Scramble solution mirrors to random wrong orientations
    all_orientations = [MIRROR_BK, MIRROR_V, MIRROR_FW, MIRROR_H]
    for (mx, my), correct in solution_mirrors.items():
        wrong = [o for o in all_orientations if o != correct]
        grid[my][mx] = rng.choice(wrong)

    # 8. Decoy mirrors — placed near beam path or between elements
    decoys_placed = 0
    decoy_attempts = 0
    while decoys_placed < n_decoys and decoy_attempts < 60:
        decoy_attempts += 1
        dx = rng.randint(1, rw - 2)
        dy = rng.randint(1, rh - 2)
        if grid[dy][dx] != EMPTY or (dx, dy) in occupied:
            continue
        # Prefer cells near beam path (within 2)
        near_beam = False
        for bx, by in beam_path_cells:
            if abs(dx - bx) + abs(dy - by) <= 2:
                near_beam = True
                break
        if not near_beam and rng.random() < 0.6:
            continue
        grid[dy][dx] = rng.choice(all_orientations)
        occupied.add((dx, dy))
        decoys_placed += 1

    # 8b. Verify scrambled state is NOT already solved
    already_t, already_s = _verify_solution(grid, emitters, targets, switches, door_link, rh, rw)
    if already_t and (not switches or already_s):
        # Puzzle is already solved in its initial state — reject this attempt
        return None

    # 9. Player start — empty cell off beam path, preferring outer cells
    start = None
    candidates = []
    for y in range(1, rh - 1):
        for x in range(1, rw - 1):
            if grid[y][x] == EMPTY and (x, y) not in beam_path_cells:
                # Distance from center
                dist_edge = min(x, y, rw - 1 - x, rh - 1 - y)
                candidates.append((dist_edge, x, y))
    if candidates:
        # Sort by distance to edge (prefer outer cells)
        candidates.sort(key=lambda c: c[0])
        # Pick from top third
        pool = candidates[:max(1, len(candidates) // 3)]
        _, sx, sy = rng.choice(pool)
        # Face toward room center
        cx_center = rw / 2.0
        cy_center = rh / 2.0
        angle = math.atan2(cy_center - sy, cx_center - sx)
        start = (sx + 0.5, sy + 0.5, angle)
    else:
        # Fallback: any empty cell
        for y in range(1, rh - 1):
            for x in range(1, rw - 1):
                if grid[y][x] == EMPTY:
                    start = (x + 0.5, y + 0.5, math.pi / 2)
                    break
            if start:
                break
    if not start:
        return None

    return {
        'map': grid,
        'start': start,
        'par': par,
        'door_link': door_link,
    }


def _fallback_level(level_idx, rw, rh):
    """Guaranteed simple solvable level if generation fails."""
    rw = max(7, rw)
    rh = max(7, rh)
    grid = [[EMPTY] * rw for _ in range(rh)]
    for x in range(rw):
        grid[0][x] = WALL
        grid[rh - 1][x] = WALL
    for y in range(rh):
        grid[y][0] = WALL
        grid[y][rw - 1] = WALL

    # Emitter on bottom wall firing north
    ex = rw // 2
    grid[rh - 1][ex] = EMITTER_N

    # Mirror in middle, wrong orientation
    mx, my = ex, rh // 2
    grid[my][mx] = MIRROR_FW  # / — wrong, needs \ to send west

    # Target on left
    grid[my][1] = TARGET

    return {
        'map': grid,
        'start': (2.5, 2.5, math.pi / 2),
        'par': 30,
        'door_link': None,
    }


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
        """Load a level map via procedural generation."""
        lvl = generate_level(idx, seed=hash(('lm', idx)))
        self.level = idx
        self.level_elapsed = 0.0
        self.level_par = lvl['par']

        # Deep copy map
        self.map = [row[:] for row in lvl['map']]
        self.map_h = len(self.map)
        self.map_w = len(self.map[0])

        # Player start
        sx, sy, sa = lvl['start']
        self.px = sx
        self.py = sy
        self.pa = sa

        # Door/switch state
        self.door_link = lvl.get('door_link')  # ((sw_x,sw_y), (door_x,door_y)) or None
        self.door_open = False
        self.switch_hit = set()
        self.switch_charge = 0.0

        # Find emitters, targets, switches
        self.emitters = []
        self.targets = []
        self.switches = []
        for y in range(self.map_h):
            for x in range(self.map_w):
                c = self.map[y][x]
                if c in EMITTER_DIRS:
                    self.emitters.append((x, y, c))
                elif c == TARGET:
                    self.targets.append([x, y, 0.0])  # charge: 0.0 to 1.0
                elif c == SWITCH:
                    self.switches.append([x, y, 0.0])

        # Trace laser beams
        self.beam_segments = []
        self.beam_cells = set()
        self.target_hit = set()
        self._trace_all_lasers()

        # Level clear state
        self.level_clear = False
        self.clear_timer = 0.0
        self.mirror_anims = {}

        # Show hints only on first level
        self.hint_timer = 4.0 if idx == 0 else 0.0

        self.phase = 'playing'

    def _cell(self, x, y):
        if x < 0 or x >= self.map_w or y < 0 or y >= self.map_h:
            return WALL
        return self.map[y][x]

    def _is_solid(self, x, y):
        c = self._cell(x, y)
        if c == DOOR and self.door_open:
            return False
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
        self.switch_hit = set()
        for ex, ey, etype in self.emitters:
            dx, dy = EMITTER_DIRS[etype]
            self._trace_beam(ex, ey, dx, dy)

    def _trace_beam(self, start_x, start_y, dx, dy, depth=0):
        if depth > 10:
            return
        cx, cy = start_x, start_y
        for _ in range(50):
            nx, ny = cx + dx, cy + dy

            if nx < 0 or nx >= self.map_w or ny < 0 or ny >= self.map_h:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break

            cell = self.map[ny][nx]

            if cell == DOOR:
                if self.door_open:
                    cell = EMPTY  # treat as passable
                else:
                    self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                    break

            if cell == WALL or cell in EMITTER_DIRS:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break

            if cell == TARGET:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                self.target_hit.add((nx, ny))
                break

            if cell == SWITCH:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                self.switch_hit.add((nx, ny))
                break

            if cell in SPLITTER_TYPES:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                # Fork: reflected beam
                rdx, rdy = SPLITTER_REFLECT[cell][(dx, dy)]
                self._trace_beam(nx, ny, rdx, rdy, depth + 1)
                # Pass through: continue in same direction
                cx, cy = nx, ny
                continue

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
        self.switch_hit = set()
        for ex, ey, etype in self.emitters:
            dx, dy = EMITTER_DIRS[etype]
            self._trace_beam_animated(ex, ey, dx, dy)

    def _trace_beam_animated(self, start_x, start_y, dx, dy, depth=0):
        """Grid-based trace that uses continuous angles at rotating mirrors."""
        if depth > 10:
            return
        cx, cy = start_x, start_y
        for _ in range(50):
            nx, ny = cx + dx, cy + dy
            if nx < 0 or nx >= self.map_w or ny < 0 or ny >= self.map_h:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break
            cell = self.map[ny][nx]
            if cell == DOOR:
                if self.door_open:
                    cell = EMPTY
                else:
                    self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                    break
            if cell == WALL or cell in EMITTER_DIRS:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                break
            if cell == TARGET:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                self.target_hit.add((nx, ny))
                break
            if cell == SWITCH:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                self.switch_hit.add((nx, ny))
                break
            if cell in SPLITTER_TYPES:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                rdx, rdy = SPLITTER_REFLECT[cell][(dx, dy)]
                self._trace_beam_animated(nx, ny, rdx, rdy, depth + 1)
                cx, cy = nx, ny
                continue
            if cell in MIRROR_REFLECT:
                self.beam_segments.append((cx + 0.5, cy + 0.5, nx + 0.5, ny + 0.5))
                self.beam_cells.add((nx, ny))
                if (nx, ny) in self.mirror_anims:
                    anim = self.mirror_anims[(nx, ny)]
                    t = min(1.0, anim['progress'])
                    theta = anim['from_theta'] + t * (anim['to_theta'] - anim['from_theta'])
                    a2 = 2 * theta
                    cos2, sin2 = math.cos(a2), math.sin(a2)
                    ref_dx = dx * cos2 + dy * sin2
                    ref_dy = dx * sin2 - dy * cos2
                    self._trace_continuous(nx + 0.5, ny + 0.5, ref_dx, ref_dy)
                    return
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
                if cell == DOOR:
                    if self.door_open:
                        cell = EMPTY
                    else:
                        self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                        return
                if cell == WALL or cell in EMITTER_DIRS:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    return
                if cell == TARGET:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    self.beam_cells.add((gx, gy))
                    self.target_hit.add((gx, gy))
                    return
                if cell == SWITCH:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    self.beam_cells.add((gx, gy))
                    self.switch_hit.add((gx, gy))
                    return
                if cell in SPLITTER_TYPES:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    self.beam_cells.add((gx, gy))
                    # Reflect using splitter's mirror angle
                    spl_mirror = MIRROR_BK if cell == SPLITTER_BK else MIRROR_FW
                    a2 = 2 * MIRROR_ANGLES[spl_mirror]
                    cos2, sin2 = math.cos(a2), math.sin(a2)
                    new_dx = dx * cos2 + dy * sin2
                    new_dy = dx * sin2 - dy * cos2
                    self._trace_continuous(gx + 0.5, gy + 0.5, new_dx, new_dy, depth + 1)
                    # Pass through continues
                    ox, oy = gx + 0.5, gy + 0.5
                    start_cell = (gx, gy)
                    entered = set()
                    continue
                if cell in MIRROR_TYPES:
                    self.beam_segments.append((ox, oy, gx + 0.5, gy + 0.5))
                    self.beam_cells.add((gx, gy))
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
        if (input_state.action_l or input_state.action_r) and not self.mirror_anims:
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

        # Advance switch charge (3 seconds)
        for s in self.switches:
            if (s[0], s[1]) in self.switch_hit:
                if s[2] < 1.0:
                    s[2] = min(1.0, s[2] + dt / 3.0)
            else:
                if s[2] < 1.0:
                    s[2] = max(0.0, s[2] - dt / 1.5)

        # Door opening: when switch fully charged, open linked door
        if self.door_link and not self.door_open and self.switches:
            if all(s[2] >= 1.0 for s in self.switches):
                self.door_open = True
                # Retrace beams now that door is open
                self._trace_all_lasers()

        # Check win condition — all targets charged
        if self.targets and all(t[2] >= 1.0 for t in self.targets):
            if not self.level_clear:
                self.level_clear = True
                time_bonus = max(0, self.level_par - self.level_elapsed) * 10
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
            # Open doors are passable
            if cell == DOOR and self.door_open:
                cell = EMPTY
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
        remaining = max(0, self.level_par - secs)
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
                tp = 0.85 + 0.15 * math.sin(self.time * 4.0)
                if dist < 0.1:
                    return (int(140 * tp), int(255 * tp), int(180 * tp))
                return (int(100 * tp), int(245 * tp), int(140 * tp))
            elif charge > 0.01:
                # Charging — interpolate from dim to nearly full brightness
                c = charge
                if dist < 0.1:
                    return (int(60 + 80 * c), int(90 + 165 * c), int(60 + 120 * c))
                return (int(40 + 60 * c), int(70 + 175 * c), int(50 + 90 * c))
            else:
                # Uncharged — dim green ring
                if dist < 0.06:
                    return (100, 130, 100)
                if dist < 0.15:
                    return (70, 100, 70)
                return TARGET_UNLIT

        if cell in SPLITTER_TYPES:
            # Translucent glass prism with diamond pattern
            mp = 0.8 + 0.2 * math.sin(self.time * 3.0)
            diag = MIRROR_ANGLES[MIRROR_BK if cell == SPLITTER_BK else MIRROR_FW]
            dist = abs((u - 0.5) * math.sin(diag) - (v - 0.5) * math.cos(diag))
            # Rainbow-tinted prism center
            if dist < 0.13:
                phase = self.time * 2.0 + u * 3.0
                r = int((200 + 55 * math.sin(phase)) * mp)
                g = int((180 + 55 * math.sin(phase + 2.1)) * mp)
                b = int((220 + 35 * math.sin(phase + 4.2)) * mp)
                return (min(255, r), min(255, g), min(255, b))
            # Diamond shape in center
            diamond = abs(u - 0.5) + abs(v - 0.5)
            if diamond < 0.25:
                return (int(200 * mp), int(220 * mp), min(255, int(255 * mp)))
            if u < 0.08 or u > 0.92 or v < 0.08 or v > 0.92:
                return (70, 80, 110)
            return (int(SPLITTER_COLOR[0] * mp * 0.7), int(SPLITTER_COLOR[1] * mp * 0.7), int(SPLITTER_COLOR[2] * mp * 0.7))

        if cell == SWITCH:
            charge = 0.0
            for s in self.switches:
                if s[0] == cx and s[1] == cy:
                    charge = s[2]
                    break
            du = abs(u - 0.5)
            dv = abs(v - 0.5)
            dist = du * du + dv * dv
            if charge >= 1.0:
                tp = 0.85 + 0.15 * math.sin(self.time * 4.0)
                if dist < 0.1:
                    return (int(80 * tp), int(255 * tp), int(255 * tp))
                return (int(60 * tp), int(240 * tp), int(245 * tp))
            elif charge > 0.01:
                c = charge
                if dist < 0.1:
                    return (int(40 + 40 * c), int(80 + 175 * c), int(90 + 165 * c))
                return (int(30 + 30 * c), int(70 + 170 * c), int(80 + 165 * c))
            else:
                if dist < 0.06:
                    return (80, 120, 130)
                if dist < 0.15:
                    return (50, 90, 100)
                return SWITCH_UNLIT

        if cell == DOOR:
            # Iron gate: vertical bars pattern
            bar_u = u * 6.0
            bar_idx = int(bar_u)
            bar_frac = bar_u - bar_idx
            # Vertical bars
            if bar_frac < 0.3 and bar_idx % 2 == 0:
                return DOOR_BAR
            # Horizontal crossbar
            if 0.45 < v < 0.55:
                return DOOR_BAR
            return DOOR_COLOR

        return STONE_COLOR

    def _draw_mirror_sprites(self):
        """Draw mirrors and splitters as small prism-on-log columns."""
        cos_pa = math.cos(self.pa)
        sin_pa = math.sin(self.pa)

        # Collect visible mirrors and splitters with depth
        sprites = []
        for y in range(self.map_h):
            for x in range(self.map_w):
                cell = self.map[y][x]
                if cell not in MIRROR_TYPES and cell not in SPLITTER_TYPES:
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

            is_splitter = cell in SPLITTER_TYPES

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
                    elif is_splitter:
                        # Rainbow-tinted prism for splitter
                        phase = self.time * 2.5 + sy * 0.3
                        r = min(255, int((180 + 60 * math.sin(phase)) * glow * fog))
                        g = min(255, int((170 + 60 * math.sin(phase + 2.1)) * glow * fog))
                        b = min(255, int((220 + 35 * math.sin(phase + 4.2)) * glow * fog))
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
        for y in range(y0, y1):
            for x in range(GRID_SIZE):
                pr, pg, pb = self.display.get_pixel(x, y)
                f = 1.0 - 0.7 * alpha
                self.display.set_pixel(x, y, (int(pr * f), int(pg * f), int(pb * f)))

        c = (int(220 * alpha), int(220 * alpha), int(240 * alpha))
        h = (int(160 * alpha), int(180 * alpha), int(160 * alpha))

        self.display.draw_text_small(2, 20, "LIGHT TARGET", c)
        self.display.draw_text_small(2, 28, "BY BOUNCING", c)
        self.display.draw_text_small(2, 36, "THE BEAM", c)
        self.display.draw_text_small(2, 44, "PRESS:ROTATE", h)

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

    def _draw_level_clear(self):
        self.display.clear((10, 15, 10))
        self.display.draw_text_small(2, 10, f"LEVEL {self.level + 1}", Colors.GREEN)
        self.display.draw_text_small(2, 20, "CLEAR!", TARGET_LIT)
        time_bonus = max(0, self.level_par - self.level_elapsed) * 10
        self.display.draw_text_small(2, 32, "BASE:100", Colors.WHITE)
        self.display.draw_text_small(2, 40, f"TIME:+{int(time_bonus)}", Colors.YELLOW)
        self.display.draw_text_small(2, 52, f"TOTAL:{self.score}", Colors.ORANGE)

    def draw_game_over(self, selection: int = 0):
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 20, "GAME OVER", Colors.RED)
        self.display.draw_text_small(2, 32, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(2, 40, f"LEVEL:{self.level + 1}", (150, 200, 150))

        if selection == 0:
            self.display.draw_text_small(2, 54, ">RETRY", Colors.YELLOW)
            self.display.draw_text_small(34, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 54, " RETRY", Colors.GRAY)
            self.display.draw_text_small(34, 54, ">MENU", Colors.YELLOW)

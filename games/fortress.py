"""
Fortress - Rampart-style castle siege
=====================================
Choose a castle on the coast, then survive round after round of three timed
phases: place cannons inside your walls, shell the ships bombarding you, and
patch the breaches with falling-block wall pieces before the clock runs out.
Fail to wall off a castle and you surrender.

The whole coast fits on the panel at 3px per tile. The camera zooms in for
cannon placement and the round's result, atlas style, and pulls back out for
battle and building so every breach is visible at once.

Controls:
  Joystick - Move the cursor or crosshair
  Space    - Rotate the wall piece (build); fire or place a cannon
  Z        - Place the wall piece (build); fire or place a cannon
"""

import math
import random
from collections import deque

from arcade import Game, GameState, InputState, Display, Colors

# ── Map ──────────────────────────────────────────────────────────
MW, MH = 20, 18            # tiles
TILE = 3                   # art pixels per tile at the base zoom
PW, PH = MW * TILE, MH * TILE   # 60 x 54 art pixels
OX, OY = 2, 10             # where the play window sits on the panel
HALF_W, HALF_H = 30, 27    # half the play window, panel pixels

EMPTY, SEA, CASTLE, KEEP, WALL, CANNON, RUBBLE = range(7)
PASSABLE = (EMPTY, SEA, RUBBLE)

CASTLE_CENTRES = [(5, 3), (4, 15), (9, 9)]
RING = 4                   # the chosen castle starts with a 9x9 wall ring

# Wall pieces, 1 to 5 blocks as in the original, weighted toward the middle
PIECES = [
    ([(0, 0)], 1),
    ([(0, 0), (1, 0)], 3),
    ([(0, 0), (1, 0), (2, 0)], 3),
    ([(0, 0), (1, 0), (0, 1)], 4),
    ([(0, 0), (1, 0), (2, 0), (3, 0)], 2),
    ([(0, 0), (1, 0), (2, 0), (2, 1)], 3),
    ([(0, 0), (1, 0), (1, 1), (2, 1)], 2),
    ([(0, 0), (1, 0), (2, 0), (1, 1)], 3),
    ([(0, 0), (1, 0), (0, 1), (1, 1)], 2),
    ([(0, 0), (1, 0), (2, 0), (2, 1), (2, 2)], 1),
    ([(1, 0), (0, 1), (1, 1), (2, 1), (1, 2)], 1),
]

# Phases
SELECT, INTRO, CANNONS, BATTLE, BUILD, RESULT, SURRENDER = range(7)
PHASE_COLOR = {CANNONS: (255, 200, 40), BATTLE: (255, 70, 50), BUILD: (90, 210, 255)}

# Palette
SEA_DEEP, SEA_SHALLOW = (18, 48, 110), (34, 86, 150)
STONE, STONE_DARK = (190, 190, 205), (120, 120, 135)
CASTLE_A, CASTLE_B = (150, 150, 170), (100, 100, 120)
KEEP_BLUE = (60, 80, 200)
CANNON_BODY, CANNON_HUB, CANNON_MUZZLE = (25, 25, 30), (90, 90, 100), (255, 220, 60)
RUBBLE_COLOR = (110, 95, 80)
TERRITORY = (90, 170, 70)
HULL, HULL_TROOP, SAIL = (110, 70, 40), (170, 40, 40), (240, 240, 240)
GRUNT = (230, 40, 40)
PIECE, PIECE_BAD, PIECE_EDGE = (150, 230, 255), (255, 90, 90), (255, 255, 255)
CROSS = (255, 60, 60)

SHIP_SCORE = {'small': 100, 'big': 300, 'troop': 500}
SHIP_HP = {'small': 1, 'big': 3, 'troop': 2}
SHIP_W = {'small': 6, 'big': 9, 'troop': 6}


def _coast_x(ty):
    """Land/sea boundary for a tile row, in tiles. Never below 13.5, so the
    castles' starting rings (x <= 13) always sit on land."""
    return 15.5 + 1.2 * math.sin(ty * 0.55) + 0.8 * math.sin(ty * 1.3 + 2.0)


def _height(tx, ty):
    d = max(0.0, _coast_x(ty) - tx) / 16
    bump = 0.5 + 0.5 * math.sin(tx * 0.7 + ty * 0.4) * math.sin(ty * 0.9 - tx * 0.2)
    return min(1.0, d * 0.8 + bump * 0.35 * d)


def _land_color(h, shade):
    if h < 0.25:
        c = (60, 120, 50)
    elif h < 0.5:
        c = (105, 135, 55)
    elif h < 0.75:
        c = (140, 125, 70)
    else:
        c = (160, 140, 110)
    return tuple(max(0, min(255, int(v * shade))) for v in c)


def _mix(a, b, t):
    return tuple(int(a[i] + (b[i] - a[i]) * t) for i in range(3))


class Fortress(Game):
    name = "FORTRESS"
    description = "Wall off castles, sink ships"
    category = "arcade"
    GUIDE = {
        'desc': 'Castle siege in three timed phases: place cannons inside your walls, shell the ships bombarding you, then patch the breaches with falling-block wall pieces before the clock runs out. Fail to wall off a castle from the sea and you surrender. Left button rotates a wall piece and right button places it; either button fires or sets a cannon.',
        'how': 'Pick a castle, then each round runs cannons, battle, build. Cannons go on your territory, one more per castle you hold. In battle, aim the crosshair and fire: sloops sink in one hit, galleons in three, and red troop ships land grunts who squat on your land so you cannot build there. Wall pieces go anywhere on land, but rubble from cannon hits cannot be built on until the next round. The map edge counts as a wall; only the sea side must be closed. Each castle walled off scores 1000 plus 10 per tile of territory, enclosed grunts are captured for 100, and ships pay 100, 300 or 500. Every round adds ships and shortens the build clock.',
        'legend': {
            'R2': 'Round number.',
            'C2': 'Cannons still to place.',
            'S4': 'Ships still afloat.',
            'bar under the score': 'Phase timer.',
            'green tint': 'Your territory: cannons may go here.',
            'grey crumbs': 'Rubble: cannot be built on this round.',
        },
    }

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    # ── Setup ────────────────────────────────────────────────────

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.round = 1
        self.sea = [[tx >= _coast_x(ty) for tx in range(MW)] for ty in range(MH)]
        self.grid = [[SEA if self.sea[ty][tx] else EMPTY for tx in range(MW)] for ty in range(MH)]
        for (cx, cy) in CASTLE_CENTRES:
            for dy in (-1, 0, 1):
                for dx in (-1, 0, 1):
                    self.grid[cy + dy][cx + dx] = KEEP if dx == dy == 0 else CASTLE
        self._bake_terrain()
        self.castle = None          # index into CASTLE_CENTRES
        self.cannons = []           # {tx, ty, cool}  top-left of a 2x2
        self.ships = []
        self.balls = []
        self.grunts = []            # {tx, ty, t}
        self.fx = []
        self.inside = set()
        self.enclosed = []
        self.cannons_left = 0
        self.timer = self.timer_max = 8.0
        self.banner = []
        self.banner_t = 0.0
        self.sel = 0
        self.cur = [0, 0]
        self.cross = [0.0, 0.0]
        self.piece = []
        self.view = [HALF_W, HALF_H, 3.0]       # art-px centre + px per tile
        self.target = [HALF_W, HALF_H, 3.0]
        self._held = {}
        self._blink = 0.0
        self._phase_done = 0.0
        self._set_phase(SELECT, 8.0, ['CHOOSE CASTLE'])
        self._rebake()

    def _bake_terrain(self):
        """Hillshaded land and a shallow-water band, atlas style, at 3px/tile."""
        self.terrain = []
        for ay in range(PH):
            ty = ay // TILE
            row = []
            for ax in range(PW):
                tx = ax // TILE
                if self.sea[ty][tx]:
                    row.append(SEA_SHALLOW if tx < _coast_x(ty) + 1.2 else SEA_DEEP)
                else:
                    h = _height(tx + (ax % TILE) / 3, ty + (ay % TILE) / 3)
                    slope = _height(tx - 1, ty) - _height(tx, ty)
                    row.append(_land_color(h, 1.0 + slope * 3.5))
            self.terrain.append(row)

    # ── Phase plumbing ───────────────────────────────────────────

    def _set_phase(self, phase, seconds, banner=None):
        self.phase = phase
        self.timer = self.timer_max = seconds
        self._phase_done = 0.0
        self._held = {}
        if banner:
            self.banner, self.banner_t = banner, 1.4

    def _castle_centre(self):
        return CASTLE_CENTRES[self.castle if self.castle is not None else 0]

    # ── Grid helpers ─────────────────────────────────────────────

    def _kind(self, tx, ty):
        if 0 <= tx < MW and 0 <= ty < MH:
            return self.grid[ty][tx]
        return None

    def _grunt_at(self, tx, ty):
        return any(g['tx'] == tx and g['ty'] == ty for g in self.grunts)

    def _buildable(self, tx, ty):
        return self._kind(tx, ty) == EMPTY and not self._grunt_at(tx, ty)

    def _compute_territory(self):
        """Flood from the sea through passable tiles. Everything the sea can't
        reach is yours; a castle is enclosed when nothing around it is reachable.
        The map edge counts as a wall."""
        outside = set()
        q = deque()
        for ty in range(MH):
            for tx in range(MW):
                if self.grid[ty][tx] == SEA:
                    outside.add((tx, ty))
                    q.append((tx, ty))
        while q:
            tx, ty = q.popleft()
            for nx, ny in ((tx + 1, ty), (tx - 1, ty), (tx, ty + 1), (tx, ty - 1)):
                if 0 <= nx < MW and 0 <= ny < MH and (nx, ny) not in outside \
                        and self.grid[ny][nx] in PASSABLE:
                    outside.add((nx, ny))
                    q.append((nx, ny))
        self.inside = {(tx, ty) for ty in range(MH) for tx in range(MW)
                       if (tx, ty) not in outside}
        self.enclosed = []
        for i, (cx, cy) in enumerate(CASTLE_CENTRES):
            halo = [(cx + dx, cy + dy) for dy in range(-2, 3) for dx in range(-2, 3)
                    if max(abs(dx), abs(dy)) == 2 and 0 <= cx + dx < MW and 0 <= cy + dy < MH]
            if all(t not in outside for t in halo):
                self.enclosed.append(i)

    def _cannon_ready(self, c):
        return c['cool'] <= 0 and (c['tx'], c['ty']) in self.inside

    # ── Art (3px/tile world image, rebuilt when the grid changes) ──

    def _rebake(self):
        art = [row[:] for row in self.terrain]
        for ty in range(MH):
            for tx in range(MW):
                k = self.grid[ty][tx]
                x0, y0 = tx * TILE, ty * TILE
                if k in (EMPTY, RUBBLE) and (tx, ty) in self.inside:
                    for dy in range(TILE):
                        r = art[y0 + dy]
                        for dx in range(TILE):
                            r[x0 + dx] = _mix(r[x0 + dx], TERRITORY, 0.4)
                if k == WALL:
                    for dy in range(TILE):
                        for dx in range(TILE):
                            art[y0 + dy][x0 + dx] = STONE_DARK if (dx == 2 or dy == 2) else STONE
                elif k == CASTLE:
                    for dy in range(TILE):
                        for dx in range(TILE):
                            art[y0 + dy][x0 + dx] = CASTLE_A if (dx + dy) % 2 == 0 else CASTLE_B
                elif k == KEEP:
                    for dy in range(TILE):
                        for dx in range(TILE):
                            art[y0 + dy][x0 + dx] = KEEP_BLUE if (dx, dy) == (1, 1) else STONE
                elif k == RUBBLE:
                    for (dx, dy) in ((0, 0), (2, 1), (1, 2)):
                        art[y0 + dy][x0 + dx] = RUBBLE_COLOR
        for c in self.cannons:
            x0, y0 = c['tx'] * TILE, c['ty'] * TILE
            for dy in range(6):
                for dx in range(6):
                    col = CANNON_BODY
                    if 2 <= dx <= 3 and 2 <= dy <= 3:
                        col = CANNON_HUB
                    if dx == 5 and dy == 2:
                        col = CANNON_MUZZLE
                    art[y0 + dy][x0 + dx] = col
        self.art = art

    # ── Input helpers ────────────────────────────────────────────

    def _steps(self, inp, dt):
        """Tile steps this frame: one on press, then auto-repeat while held."""
        out = []
        for name, step in (('up', (0, -1)), ('down', (0, 1)), ('left', (-1, 0)), ('right', (1, 0))):
            if getattr(inp, name):
                t = self._held.get(name)
                if t is None:
                    self._held[name] = 0.0
                    out.append(step)
                else:
                    t += dt
                    if t >= 0.28:
                        t -= 0.09
                        out.append(step)
                    self._held[name] = t
            else:
                self._held.pop(name, None)
        return out

    # ── Update ───────────────────────────────────────────────────

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return
        dt = min(dt, 0.1)
        self._blink += dt
        if self.banner_t > 0:
            self.banner_t -= dt
        for f in self.fx:
            f['t'] += dt
        self.fx = [f for f in self.fx if f['t'] < 0.3]
        self.timer -= dt

        handler = {SELECT: self._up_select, INTRO: self._up_intro, CANNONS: self._up_cannons,
                   BATTLE: self._up_battle, BUILD: self._up_build, RESULT: self._up_result,
                   SURRENDER: self._up_surrender}[self.phase]
        handler(input_state, dt)
        self._move_camera(dt)

    def _move_camera(self, dt):
        k = min(1.0, dt * 6)
        for i in range(3):
            self.view[i] += (self.target[i] - self.view[i]) * k
        self._clamp_view(self.view)

    def _clamp_view(self, v):
        hw, hh = HALF_W * TILE / v[2], HALF_H * TILE / v[2]
        v[0] = min(max(v[0], hw), PW - hw)
        v[1] = min(max(v[1], hh), PH - hh)

    def _look(self, cx, cy, scale):
        self.target = [cx, cy, scale]
        self._clamp_view(self.target)

    # Choosing a castle
    def _up_select(self, inp, dt):
        for dx, dy in self._steps(inp, dt):
            self.sel = (self.sel + (1 if dx + dy > 0 else -1)) % len(CASTLE_CENTRES)
        if inp.action_l or inp.action_r or self.timer <= 0:
            self.castle = self.sel
            cx, cy = self._castle_centre()
            for dy in range(-RING, RING + 1):
                for dx in range(-RING, RING + 1):
                    if max(abs(dx), abs(dy)) == RING and self._kind(cx + dx, cy + dy) == EMPTY:
                        self.grid[cy + dy][cx + dx] = WALL
            self._compute_territory()
            self._rebake()
            self.view = [cx * TILE + 1, cy * TILE + 1, 9.0]
            self._clamp_view(self.view)
            self._look(HALF_W, HALF_H, 3.0)
            self.banner_t = 0.0
            self._set_phase(INTRO, 1.4)

    def _up_intro(self, inp, dt):
        if self.timer <= 0:
            self._start_cannons()

    # Cannons
    def _start_cannons(self):
        self.cannons_left = 1 + max(1, len(self.enclosed))
        cx, cy = self._castle_centre()
        self.cur = [min(MW - 2, cx + 2), max(0, cy - 3)]
        self._set_phase(CANNONS, 10.0, ['PLACE CANNONS'])

    def _cannon_legal(self, tx, ty):
        return all(self._buildable(tx + dx, ty + dy) and (tx + dx, ty + dy) in self.inside
                   for dx in (0, 1) for dy in (0, 1))

    def _up_cannons(self, inp, dt):
        for dx, dy in self._steps(inp, dt):
            self.cur[0] = min(MW - 2, max(0, self.cur[0] + dx))
            self.cur[1] = min(MH - 2, max(0, self.cur[1] + dy))
        self._look((self.cur[0] + 1) * TILE, (self.cur[1] + 1) * TILE, 6.0)
        if (inp.action_l or inp.action_r) and self.cannons_left > 0 and self._cannon_legal(*self.cur):
            tx, ty = self.cur
            self.cannons.append({'tx': tx, 'ty': ty, 'cool': 0.0})
            for dx in (0, 1):
                for dy in (0, 1):
                    self.grid[ty + dy][tx + dx] = CANNON
            self._rebake()
            self.cannons_left -= 1
        if self.cannons_left <= 0 or self.timer <= 0:
            self._start_battle()

    # Battle
    def _start_battle(self):
        n = min(8, 2 + self.round)
        kinds = ['small'] * n
        if self.round >= 2:
            kinds[0] = 'big'
        if self.round >= 3:
            kinds[1] = 'troop'
        if self.round >= 5:
            kinds[2] = 'big'
        rows = random.sample(range(1, MH - 1), n)
        self.ships = []
        for i, (kind, ty) in enumerate(zip(kinds, rows)):
            coast = _coast_x(ty)
            station = (coast + 1.2 + random.uniform(0, max(0.5, MW - 2.5 - coast))) * TILE
            self.ships.append({
                'kind': kind, 'hp': SHIP_HP[kind], 'ty': ty,
                'x': float(PW + 8 + i * 7), 'y': float(ty * TILE),
                'station': min(station, PW - 2), 'fire': random.uniform(1.5, 3.0),
                'unload': 3.0, 'landed': 0, 'sink': None,
            })
        cx, cy = self._castle_centre()
        self.cross = [min(PW - 1.0, (_coast_x(cy) + 1) * TILE), cy * TILE + 1.0]
        self.balls = []
        self._look(HALF_W, HALF_H, 3.0)
        self._set_phase(BATTLE, min(28.0, 16.0 + 1.5 * self.round), ['BATTLE'])

    def _player_walls(self):
        return [(tx, ty) for ty in range(MH) for tx in range(MW) if self.grid[ty][tx] == WALL]

    def _up_battle(self, inp, dt):
        # Crosshair
        speed = 36 * dt
        self.cross[0] = min(PW - 1.0, max(0.0, self.cross[0] + inp.dx * speed))
        self.cross[1] = min(PH - 1.0, max(0.0, self.cross[1] + inp.dy * speed))
        for c in self.cannons:
            c['cool'] -= dt
        if inp.action_l or inp.action_r:
            ready = [c for c in self.cannons if self._cannon_ready(c)]
            if ready:
                c = min(ready, key=lambda c: abs((c['tx'] + 1) * TILE - self.cross[0])
                        + abs((c['ty'] + 1) * TILE - self.cross[1]))
                x0, y0 = (c['tx'] + 1) * TILE, (c['ty'] + 1) * TILE
                dist = math.hypot(self.cross[0] - x0, self.cross[1] - y0)
                self.balls.append({'x0': x0, 'y0': y0, 'x1': self.cross[0], 'y1': self.cross[1],
                                   't': 0.0, 'dur': 0.45 + dist / 90, 'mine': True})
                c['cool'] = 1.4

        # Ships
        for s in self.ships:
            if s['sink'] is not None:
                s['sink'] += dt
                continue
            if s['x'] > s['station']:
                s['x'] = max(s['station'], s['x'] - 9 * dt)
                continue
            s['fire'] -= dt
            if s['fire'] <= 0:
                s['fire'] = max(1.4, random.uniform(2.6, 3.8) - 0.25 * self.round)
                walls = self._player_walls()
                if self.cannons and random.random() < 0.1:
                    c = random.choice(self.cannons)
                    tgt = (c['tx'] + random.randint(0, 1), c['ty'] + random.randint(0, 1))
                elif walls:
                    # Ships pound the stretch of wall facing them, so damage
                    # concentrates into a breach rather than scattered holes
                    picks = random.sample(walls, min(8, len(walls)))
                    tgt = min(picks, key=lambda w: abs(w[0] * TILE - s['x']) + abs(w[1] * TILE - s['y']))
                else:
                    cx, cy = self._castle_centre()
                    tgt = (cx + random.randint(-3, 3), cy + random.randint(-3, 3))
                x1, y1 = tgt[0] * TILE + 1, tgt[1] * TILE + 1
                self.balls.append({'x0': s['x'] + 2, 'y0': s['y'] + 1, 'x1': x1, 'y1': y1,
                                   't': 0.0, 'dur': 1.3, 'mine': False, 'tile': tgt})
            if s['kind'] == 'troop' and s['landed'] < 3 and len(self.grunts) < 6:
                s['unload'] -= dt
                if s['unload'] <= 0:
                    s['unload'] = 3.0
                    tx = int(_coast_x(s['ty'])) - 1
                    while tx > 0 and not self._buildable(tx, s['ty']):
                        tx -= 1
                    if tx > 0:
                        self.grunts.append({'tx': tx, 'ty': s['ty'], 't': 0.0})
                        s['landed'] += 1
        self.ships = [s for s in self.ships if s['sink'] is None or s['sink'] < 0.9]

        # Cannonballs
        for b in self.balls:
            b['t'] += dt
            if b['t'] >= b['dur']:
                self._impact(b)
        self.balls = [b for b in self.balls if b['t'] < b['dur']]

        # Grunts march on your castle
        cx, cy = self._castle_centre()
        for g in self.grunts:
            g['t'] += dt
            if g['t'] < 0.7:
                continue
            g['t'] = 0.0
            dx = (cx > g['tx']) - (cx < g['tx'])
            dy = (cy > g['ty']) - (cy < g['ty'])
            for nx, ny in ((g['tx'] + dx, g['ty']), (g['tx'], g['ty'] + dy)):
                if (nx, ny) != (g['tx'], g['ty']) and self._buildable(nx, ny):
                    g['tx'], g['ty'] = nx, ny
                    break

        afloat = [s for s in self.ships if s['sink'] is None]
        if self.timer <= 0 or (not afloat and not self.balls):
            self._phase_done += dt
            if self._phase_done > 0.6 or self.timer <= 0:
                self.ships = []
                self.balls = []
                self._start_build()

    def _impact(self, b):
        x, y = b['x1'], b['y1']
        self.fx.append({'x': x, 'y': y, 't': 0.0})
        if b['mine']:
            for s in self.ships:
                if s['sink'] is None and s['x'] - 1 <= x <= s['x'] + SHIP_W[s['kind']] \
                        and abs(s['y'] + 1 - y) <= 2.5:
                    s['hp'] -= 1
                    if s['hp'] <= 0:
                        s['sink'] = 0.0
                        self.score += SHIP_SCORE[s['kind']]
            tx, ty = int(x) // TILE, int(y) // TILE
            before = len(self.grunts)
            self.grunts = [g for g in self.grunts if abs(g['tx'] - tx) + abs(g['ty'] - ty) > 1]
            self.score += 50 * (before - len(self.grunts))
        else:
            tx, ty = b['tile']
            k = self._kind(tx, ty)
            if k == WALL:
                self.grid[ty][tx] = RUBBLE
                self._rebake()
            elif k == CANNON:
                for c in self.cannons:
                    if c['tx'] <= tx <= c['tx'] + 1 and c['ty'] <= ty <= c['ty'] + 1:
                        self.cannons.remove(c)
                        for dx in (0, 1):
                            for dy in (0, 1):
                                self.grid[c['ty'] + dy][c['tx'] + dx] = RUBBLE
                        break
                self._rebake()

    # Build
    def _start_build(self):
        self._new_piece()
        cx, cy = self._castle_centre()
        self.cur = [cx + 3, cy]
        self._clamp_piece()
        self._look(HALF_W, HALF_H, 3.0)
        self._set_phase(BUILD, max(10.0, 26.0 - 2 * self.round), ['BUILD'])

    def _new_piece(self):
        shapes, weights = zip(*PIECES)
        self.piece = list(random.choices(shapes, weights)[0])

    def _rotate(self):
        cells = [(-y, x) for (x, y) in self.piece]
        mx, my = min(x for x, _ in cells), min(y for _, y in cells)
        self.piece = [(x - mx, y - my) for (x, y) in cells]
        self._clamp_piece()

    def _clamp_piece(self):
        w = max(x for x, _ in self.piece) + 1
        h = max(y for _, y in self.piece) + 1
        self.cur[0] = min(MW - w, max(0, self.cur[0]))
        self.cur[1] = min(MH - h, max(0, self.cur[1]))

    def _piece_legal(self):
        return all(self._buildable(self.cur[0] + x, self.cur[1] + y) for (x, y) in self.piece)

    def _up_build(self, inp, dt):
        for dx, dy in self._steps(inp, dt):
            self.cur[0] += dx
            self.cur[1] += dy
        self._clamp_piece()
        if inp.action_l:
            self._rotate()
        if inp.action_r and self._piece_legal():
            for (x, y) in self.piece:
                self.grid[self.cur[1] + y][self.cur[0] + x] = WALL
            self._rebake()
            self._new_piece()
            self._clamp_piece()
        if self.timer <= 0:
            self._finish_build()

    # Result
    def _finish_build(self):
        self._compute_territory()
        # Rubble clears for next round, captured grunts are taken
        for ty in range(MH):
            for tx in range(MW):
                if self.grid[ty][tx] == RUBBLE:
                    self.grid[ty][tx] = EMPTY
        captured = [g for g in self.grunts if (g['tx'], g['ty']) in self.inside]
        self.grunts = [g for g in self.grunts if g not in captured]
        self._rebake()
        if not self.enclosed:
            self._look(HALF_W, HALF_H, 3.0)
            self._set_phase(SURRENDER, 2.2, ['SURRENDER'])
            return
        if self.castle not in self.enclosed:
            self.castle = self.enclosed[0]
        land = sum(1 for (tx, ty) in self.inside if self.grid[ty][tx] == EMPTY)
        pts = 1000 * len(self.enclosed) + 10 * land + 100 * len(captured)
        self.score += pts
        cx, cy = self._castle_centre()
        self._look(cx * TILE + 1, cy * TILE + 1, 5.0)
        n = len(self.enclosed)
        self._set_phase(RESULT, 2.6, [f'{n} CASTLE{"S" if n > 1 else ""}', f'+{pts}'])
        self.banner_t = 2.6

    def _up_result(self, inp, dt):
        if self.timer <= 0:
            self.round += 1
            self._start_cannons()

    def _up_surrender(self, inp, dt):
        if self.timer <= 0:
            self.state = GameState.GAME_OVER

    def game_over_stat(self):
        return f"ROUND:{self.round}"

    # ── Draw ─────────────────────────────────────────────────────

    def draw(self):
        d = self.display
        d.clear(Colors.BLACK)
        ov = {}
        self._draw_sprites(ov)
        self._blit_world(ov)
        self._draw_hud()
        if self.banner_t > 0 and self.banner:
            self._draw_banner()

    def _blit_world(self, ov):
        cx, cy, s = self.view
        k = TILE / s
        vx0, vy0 = cx - HALF_W * k, cy - HALF_H * k
        xs = [min(PW - 1, max(0, int(vx0 + X * k))) for X in range(2 * HALF_W)]
        ys = [min(PH - 1, max(0, int(vy0 + Y * k))) for Y in range(2 * HALF_H)]
        art, put = self.art, self.display.set_pixel
        for Y, ay in enumerate(ys):
            row = art[ay]
            py = OY + Y
            for X, ax in enumerate(xs):
                c = ov.get((ax, ay))
                put(OX + X, py, row[ax] if c is None else c)

    def _draw_sprites(self, ov):
        def put(ax, ay, col):
            ax, ay = int(ax), int(ay)
            if 0 <= ax < PW and 0 <= ay < PH:
                ov[(ax, ay)] = col

        on = int(self._blink * 4) % 2 == 0

        for g in self.grunts:
            x, y = g['tx'] * TILE + 1, g['ty'] * TILE
            put(x, y, GRUNT)
            put(x, y + 1, GRUNT)
            put(x, y + 2, (120, 20, 20))

        for s in self.ships:
            x, y, w = int(s['x']), int(s['y']), SHIP_W[s['kind']]
            hull = HULL_TROOP if s['kind'] == 'troop' else HULL
            if s['sink'] is not None:
                hull = _mix(hull, SEA_DEEP, min(1.0, s['sink'] / 0.9))
                y += int(s['sink'] * 2)
            for dx in range(w):
                put(x + dx, y + 1, hull)
                put(x + dx, y + 2, hull)
            masts = (w // 2,) if w < 9 else (2, 6)
            for m in masts:
                put(x + m, y, SAIL if s['sink'] is None else hull)
                if w >= 9:
                    put(x + m + 1, y, SAIL if s['sink'] is None else hull)

        for b in self.balls:
            p = b['t'] / b['dur']
            x = b['x0'] + (b['x1'] - b['x0']) * p
            y = b['y0'] + (b['y1'] - b['y0']) * p
            h = max(2.0, math.hypot(b['x1'] - b['x0'], b['y1'] - b['y0']) * 0.22)
            put(x, y, (20, 20, 20))
            put(x, y - h * math.sin(math.pi * p), Colors.WHITE if b['mine'] else (255, 200, 120))

        for f in self.fx:
            r = int(f['t'] / 0.08)
            col = (255, 240, 120) if r == 0 else (255, 140, 40)
            if r == 0:
                for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
                    put(f['x'] + dx, f['y'] + dy, col)
            else:
                for i in range(8):
                    a = i * math.pi / 4
                    put(f['x'] + r * math.cos(a), f['y'] + r * math.sin(a), col)

        if self.phase == SELECT:
            cx, cy = CASTLE_CENTRES[self.sel]
            if on:
                for t in range(-2, 3):
                    for (dx, dy) in ((t, -2), (t, 2), (-2, t), (2, t)):
                        put((cx + dx) * TILE + 1, (cy + dy) * TILE + 1, Colors.WHITE)
        elif self.phase == CANNONS:
            tx, ty = self.cur
            col = Colors.WHITE if self._cannon_legal(tx, ty) else PIECE_BAD
            if on or not self._cannon_legal(tx, ty):
                x0, y0 = tx * TILE, ty * TILE
                for i in range(6):
                    put(x0 + i, y0, col)
                    put(x0 + i, y0 + 5, col)
                    put(x0, y0 + i, col)
                    put(x0 + 5, y0 + i, col)
        elif self.phase == BATTLE:
            x, y = self.cross
            for t in (-2, -1, 1, 2):
                put(x + t, y, CROSS)
                put(x, y + t, CROSS)
        elif self.phase == BUILD:
            col = PIECE if self._piece_legal() else PIECE_BAD
            for (x, y) in self.piece:
                x0, y0 = (self.cur[0] + x) * TILE, (self.cur[1] + y) * TILE
                for dy in range(TILE):
                    for dx in range(TILE):
                        put(x0 + dx, y0 + dy, PIECE_EDGE if (dx == 0 or dy == 0) else col)
        elif self.phase == RESULT and on:
            for (tx, ty) in self.inside:
                if self.grid[ty][tx] == EMPTY:
                    put(tx * TILE + 1, ty * TILE + 1, Colors.WHITE)

    def _draw_hud(self):
        d = self.display
        d.draw_text_small(1, 1, f"{self.score}", Colors.WHITE)
        rnd = f"R{self.round}"
        d.draw_text_small(63 - 4 * len(rnd), 1, rnd, Colors.GRAY)
        if self.phase == CANNONS:
            d.draw_text_small(36, 1, f"C{self.cannons_left}", PHASE_COLOR[CANNONS])
        elif self.phase == BATTLE:
            afloat = sum(1 for s in self.ships if s['sink'] is None)
            d.draw_text_small(36, 1, f"S{afloat}", PHASE_COLOR[BATTLE])
        col = PHASE_COLOR.get(self.phase)
        if col and self.timer_max > 0:
            w = max(0, min(62, int(62 * self.timer / self.timer_max)))
            dim = tuple(c // 5 for c in col)
            for x in range(1, 63):
                for y in (7, 8):
                    d.set_pixel(x, y, col if x <= w else dim)

    def _draw_banner(self):
        d = self.display
        lines = self.banner[:2]
        top = OY + 20
        for y in range(top, top + 7 * len(lines) + 3):
            for x in range(OX, OX + 2 * HALF_W):
                d.set_pixel(x, y, (0, 0, 0))
        for i, text in enumerate(lines):
            x = (64 - (4 * len(text) - 1)) // 2
            d.draw_text_small(x, top + 2 + 7 * i, text, Colors.WHITE if i == 0 else Colors.YELLOW)

"""
Bloons TD - LED Arcade
======================
Tower defense: bloons follow a serpentine path, place towers to pop them,
survive 20 waves. Economy system with lives and money.

Controls:
  Arrows    - Move placement cursor (fine 2px grid)
  Space     - Place tower / select existing tower
  Z         - Cycle tower type / upgrade selected tower
  Space+Z   - Start next wave
"""

import math
import random
from arcade import Game, GameState, Display, Colors, InputState

# Phases
PHASE_PLACE = 0
PHASE_WAVE = 1
PHASE_WAVE_END = 2

# Display
BG_COLOR = (20, 60, 20)
PATH_COLOR = (160, 130, 80)
PATH_WIDTH = 2

# Path waypoints (serpentine, 4 horizontal passes)
PATH_WAYPOINTS = [
    (-2, 10),    # Entry left
    (58, 10),    # Right
    (58, 22),    # Down
    (6, 22),     # Left
    (6, 34),     # Down
    (58, 34),    # Right
    (58, 46),    # Down
    (6, 46),     # Left
    (6, 58),     # Down
    (30, 58),    # Exit
]

# Precompute path segments and total length
def _build_path():
    segments = []
    total = 0.0
    for i in range(len(PATH_WAYPOINTS) - 1):
        x0, y0 = PATH_WAYPOINTS[i]
        x1, y1 = PATH_WAYPOINTS[i + 1]
        length = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
        segments.append((x0, y0, x1, y1, length, total))
        total += length
    return segments, total

PATH_SEGMENTS, PATH_TOTAL = _build_path()

def pos_on_path(dist):
    """Get (x, y) position at distance along path."""
    if dist <= 0:
        return PATH_WAYPOINTS[0]
    if dist >= PATH_TOTAL:
        return PATH_WAYPOINTS[-1]
    for x0, y0, x1, y1, seg_len, seg_start in PATH_SEGMENTS:
        if dist <= seg_start + seg_len:
            t = (dist - seg_start) / seg_len if seg_len > 0 else 0
            return (x0 + (x1 - x0) * t, y0 + (y1 - y0) * t)
    return PATH_WAYPOINTS[-1]

# Bloon types: (name, color, speed, child_index, rbe)
BLOON_TYPES = [
    ('red',    (255, 40, 40),    20.0, -1, 1),
    ('blue',   (40, 80, 255),    24.0,  0, 2),
    ('green',  (40, 200, 40),    28.0,  1, 3),
    ('yellow', (255, 255, 40),   32.0,  2, 4),
    ('pink',   (255, 120, 160),  36.0,  3, 5),
]

# Tower types: (name, color, cost, range, fire_rate, special)
TOWER_DART    = 0
TOWER_TACK    = 1
TOWER_CANNON  = 2
TOWER_ICE     = 3

TOWER_DEFS = [
    {'name': 'DART',   'color': (139, 90, 43),   'cost': 150, 'range': 12, 'rate': 1.0,
     'special': 'single', 'upgrade_cost': 100, 'up_range': 15, 'up_rate': 1.5},
    {'name': 'TACK',   'color': (255, 140, 40),  'cost': 250, 'range': 8,  'rate': 0.7,
     'special': 'tack',   'upgrade_cost': 150, 'up_range': 10, 'up_rate': 1.0},
    {'name': 'CANNON', 'color': (140, 140, 140), 'cost': 400, 'range': 15, 'rate': 0.5,
     'special': 'splash', 'upgrade_cost': 200, 'up_range': 18, 'up_rate': 0.7},
    {'name': 'ICE',    'color': (100, 180, 255),  'cost': 300, 'range': 10, 'rate': 0.3,
     'special': 'slow',   'upgrade_cost': 150, 'up_range': 13, 'up_rate': 0.5},
]

SPLASH_RADIUS = 4.0
SLOW_FACTOR = 0.5
SLOW_DURATION = 2.0

# Projectile speed
PROJ_SPEED = 100.0

# Grid for placement (2x2 cells = 32x32 grid for fine control)
CELL_SIZE = 2

# Economy
START_MONEY = 500
START_LIVES = 20

# Waves: list of groups, each group = (type_index, count, interval)
WAVES = [
    # W1-3: Reds
    [(0, 8, 0.8)],
    [(0, 12, 0.7)],
    [(0, 16, 0.6)],
    # W4-6: Blues appear
    [(0, 10, 0.6), (1, 4, 0.8)],
    [(1, 8, 0.7), (0, 6, 0.5)],
    [(1, 12, 0.6), (0, 8, 0.5)],
    # W7-9: Greens
    [(0, 8, 0.5), (1, 6, 0.6), (2, 4, 0.8)],
    [(1, 8, 0.5), (2, 6, 0.7)],
    [(2, 10, 0.6), (1, 6, 0.5)],
    # W10: Rush
    [(0, 30, 0.2)],
    # W11-15: Yellows and pinks
    [(2, 8, 0.5), (3, 4, 0.8)],
    [(3, 8, 0.6), (2, 6, 0.5)],
    [(3, 10, 0.5), (4, 2, 1.0)],
    [(4, 4, 0.8), (3, 8, 0.5)],
    [(4, 6, 0.7), (3, 6, 0.5), (2, 8, 0.4)],
    # W16-19: Heavy mixed
    [(4, 8, 0.6), (3, 10, 0.4)],
    [(4, 10, 0.5), (3, 8, 0.4), (2, 10, 0.3)],
    [(4, 12, 0.5), (3, 10, 0.4)],
    [(4, 14, 0.4), (3, 12, 0.3), (2, 10, 0.3)],
    # W20: Final
    [(4, 20, 0.3), (3, 15, 0.3), (2, 10, 0.2)],
]

# Path occupancy set for placement validation
def _build_path_pixels():
    """Get set of (gx, gy) grid cells that the path passes through."""
    occupied = set()
    # Walk path at 1px resolution
    dist = 0.0
    while dist <= PATH_TOTAL:
        x, y = pos_on_path(dist)
        # Mark cells within PATH_WIDTH of path center
        for dx in range(-PATH_WIDTH, PATH_WIDTH + 1):
            for dy in range(-PATH_WIDTH, PATH_WIDTH + 1):
                gx = int((x + dx)) // CELL_SIZE
                gy = int((y + dy)) // CELL_SIZE
                occupied.add((gx, gy))
        dist += 1.0
    return occupied

PATH_CELLS = _build_path_pixels()


class BloonsTD(Game):
    name = "BLOONS TD"
    description = "Tower defense with bloons"
    category = "modern"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0
        self.money = START_MONEY
        self.lives = START_LIVES
        self.wave_num = 0
        self.phase = PHASE_PLACE

        # Cursor
        self.cursor_gx = 16  # grid x (0..30)
        self.cursor_gy = 8   # grid y (0..30)
        self.cursor_blink = 0.0
        self.selected_tower_type = TOWER_DART
        self.selected_tower = None  # index into self.towers if selecting existing

        # Towers: list of dicts
        self.towers = []
        # Bloons on field
        self.bloons = []
        # Projectiles
        self.projectiles = []

        # Wave spawning state
        self.spawn_queue = []
        self.spawn_timer = 0.0
        self.wave_active = False

        # Move repeat timer
        self.move_timer = 0.0
        self.move_delay = 0.15

        # Wave end timer
        self.wave_end_timer = 0.0

    def _can_place(self, gx, gy):
        """Check if tower can be placed at grid cell."""
        if (gx, gy) in PATH_CELLS:
            return False
        # Tower sprite is 3x3 pixels starting at (gx*2, gy*2)
        px = gx * CELL_SIZE
        py = gy * CELL_SIZE
        # Must fit on screen (3x3 sprite)
        if px < 0 or px + 3 > 64 or py < 0 or py + 3 > 64:
            return False
        # Check no overlap with existing towers (3x3 sprites need >=3px apart)
        for t in self.towers:
            if abs(t['gx'] - gx) < 2 and abs(t['gy'] - gy) < 2:
                return False
        return True

    def _tower_at(self, gx, gy):
        """Return tower index if cursor overlaps a tower's footprint."""
        for i, t in enumerate(self.towers):
            # Tower occupies 3x3 pixels = roughly 2 grid cells in each axis
            if abs(t['gx'] - gx) <= 1 and abs(t['gy'] - gy) <= 1:
                return i
        return None

    def _start_wave(self):
        """Begin spawning the next wave."""
        if self.wave_num >= len(WAVES):
            return
        wave = WAVES[self.wave_num]
        self.spawn_queue = []
        for type_idx, count, interval in wave:
            for i in range(count):
                self.spawn_queue.append((type_idx, interval))
        self.spawn_timer = 0.0
        self.wave_active = True
        self.phase = PHASE_WAVE

    def _spawn_bloon(self, type_idx):
        """Spawn a bloon at path start."""
        _, color, speed, child_idx, rbe = BLOON_TYPES[type_idx]
        self.bloons.append({
            'type': type_idx,
            'dist': 0.0,
            'speed': speed,
            'alive': True,
            'slow_timer': 0.0,
        })

    def _pop_bloon(self, bloon):
        """Pop a bloon, spawn child, earn money."""
        bloon['alive'] = False
        type_idx = bloon['type']
        _, _, _, child_idx, _ = BLOON_TYPES[type_idx]
        self.money += 1
        self.score += 1

        if child_idx >= 0:
            _, _, speed, _, _ = BLOON_TYPES[child_idx]
            self.bloons.append({
                'type': child_idx,
                'dist': bloon['dist'],
                'speed': speed,
                'alive': True,
                'slow_timer': bloon['slow_timer'],
            })

    def _bloon_escapes(self, bloon):
        """Bloon reached end of path."""
        bloon['alive'] = False
        _, _, _, _, rbe = BLOON_TYPES[bloon['type']]
        self.lives -= rbe
        if self.lives <= 0:
            self.lives = 0
            self.state = GameState.GAME_OVER

    # ==== UPDATE ====

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.cursor_blink += dt

        if self.phase == PHASE_PLACE:
            self._update_place(input_state, dt)
        elif self.phase == PHASE_WAVE:
            self._update_place(input_state, dt)  # Can still place during wave
            self._update_wave(dt)
        elif self.phase == PHASE_WAVE_END:
            self._update_wave_end(input_state, dt)

    def _update_place(self, inp, dt):
        # Cursor movement with repeat
        moved = False
        if inp.up_pressed or inp.down_pressed or inp.left_pressed or inp.right_pressed:
            self.move_timer = 0.0
            moved = True
        elif inp.up or inp.down or inp.left or inp.right:
            self.move_timer += dt
            if self.move_timer >= self.move_delay:
                self.move_timer -= self.move_delay
                moved = True

        if moved:
            if inp.up or inp.up_pressed:
                self.cursor_gy = max(0, self.cursor_gy - 1)
            if inp.down or inp.down_pressed:
                self.cursor_gy = min(30, self.cursor_gy + 1)
            if inp.left or inp.left_pressed:
                self.cursor_gx = max(0, self.cursor_gx - 1)
            if inp.right or inp.right_pressed:
                self.cursor_gx = min(30, self.cursor_gx + 1)
            self.selected_tower = None

        # Space: place tower or select existing
        if inp.action_l:
            existing = self._tower_at(self.cursor_gx, self.cursor_gy)
            if existing is not None:
                self.selected_tower = existing
            elif self._can_place(self.cursor_gx, self.cursor_gy):
                tdef = TOWER_DEFS[self.selected_tower_type]
                if self.money >= tdef['cost']:
                    self.money -= tdef['cost']
                    self.towers.append({
                        'gx': self.cursor_gx,
                        'gy': self.cursor_gy,
                        'type': self.selected_tower_type,
                        'upgraded': False,
                        'cooldown': 0.0,
                    })
                    self.selected_tower = len(self.towers) - 1

        # Z: cycle tower type / upgrade selected tower
        if inp.action_r:
            if self.selected_tower is not None:
                # Try upgrade
                t = self.towers[self.selected_tower]
                tdef = TOWER_DEFS[t['type']]
                if not t['upgraded'] and self.money >= tdef['upgrade_cost']:
                    self.money -= tdef['upgrade_cost']
                    t['upgraded'] = True
            else:
                # Cycle tower type
                self.selected_tower_type = (self.selected_tower_type + 1) % len(TOWER_DEFS)

        # Both buttons together during PLACE phase: start next wave
        if inp.action_l and inp.action_r_held and self.phase == PHASE_PLACE:
            if self.wave_num < len(WAVES):
                self._start_wave()
        elif inp.action_r and inp.action_l_held and self.phase == PHASE_PLACE:
            if self.wave_num < len(WAVES):
                self._start_wave()

    def _update_wave(self, dt):
        # Spawn bloons
        if self.spawn_queue:
            self.spawn_timer -= dt
            if self.spawn_timer <= 0:
                type_idx, interval = self.spawn_queue.pop(0)
                self._spawn_bloon(type_idx)
                self.spawn_timer = interval

        # Move bloons
        alive_bloons = []
        for bloon in self.bloons:
            if not bloon['alive']:
                continue
            speed = bloon['speed']
            if bloon['slow_timer'] > 0:
                speed *= SLOW_FACTOR
                bloon['slow_timer'] -= dt
            bloon['dist'] += speed * dt

            if bloon['dist'] >= PATH_TOTAL:
                self._bloon_escapes(bloon)
                if self.state == GameState.GAME_OVER:
                    return
            else:
                alive_bloons.append(bloon)

        self.bloons = [b for b in self.bloons if b['alive']]

        # Tower firing
        for tower in self.towers:
            tower['cooldown'] -= dt
            if tower['cooldown'] > 0:
                continue

            tdef = TOWER_DEFS[tower['type']]
            t_range = tdef['up_range'] if tower['upgraded'] else tdef['range']
            t_rate = tdef['up_rate'] if tower['upgraded'] else tdef['rate']

            tx = tower['gx'] * CELL_SIZE + CELL_SIZE // 2
            ty = tower['gy'] * CELL_SIZE + CELL_SIZE // 2

            if tdef['special'] == 'slow':
                # Ice tower: area slow, no projectile
                slowed = False
                for bloon in self.bloons:
                    if not bloon['alive']:
                        continue
                    bx, by = pos_on_path(bloon['dist'])
                    dist = math.sqrt((bx - tx) ** 2 + (by - ty) ** 2)
                    if dist <= t_range:
                        bloon['slow_timer'] = SLOW_DURATION
                        slowed = True
                if slowed:
                    tower['cooldown'] = 1.0 / t_rate
                continue

            # Find target: furthest along path within range
            best = None
            best_dist = -1
            for bloon in self.bloons:
                if not bloon['alive']:
                    continue
                bx, by = pos_on_path(bloon['dist'])
                dist = math.sqrt((bx - tx) ** 2 + (by - ty) ** 2)
                if dist <= t_range and bloon['dist'] > best_dist:
                    best = bloon
                    best_dist = bloon['dist']

            if best is None:
                continue

            tower['cooldown'] = 1.0 / t_rate
            bx, by = pos_on_path(best['dist'])

            if tdef['special'] == 'tack':
                # Fire 8 directions
                for angle in range(0, 360, 45):
                    rad = math.radians(angle)
                    self.projectiles.append({
                        'x': float(tx), 'y': float(ty),
                        'vx': math.cos(rad) * PROJ_SPEED,
                        'vy': math.sin(rad) * PROJ_SPEED,
                        'type': 'tack',
                        'life': 0.15,
                    })
            elif tdef['special'] == 'splash':
                # Fire toward target
                dx = bx - tx
                dy = by - ty
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    self.projectiles.append({
                        'x': float(tx), 'y': float(ty),
                        'vx': (dx / dist) * PROJ_SPEED,
                        'vy': (dy / dist) * PROJ_SPEED,
                        'type': 'splash',
                        'life': dist / PROJ_SPEED + 0.05,
                        'target_x': bx, 'target_y': by,
                    })
            else:
                # Single dart toward target
                dx = bx - tx
                dy = by - ty
                dist = math.sqrt(dx * dx + dy * dy)
                if dist > 0:
                    self.projectiles.append({
                        'x': float(tx), 'y': float(ty),
                        'vx': (dx / dist) * PROJ_SPEED,
                        'vy': (dy / dist) * PROJ_SPEED,
                        'type': 'dart',
                        'life': dist / PROJ_SPEED + 0.05,
                    })

        # Move projectiles
        new_projs = []
        for proj in self.projectiles:
            proj['x'] += proj['vx'] * dt
            proj['y'] += proj['vy'] * dt
            proj['life'] -= dt

            if proj['life'] <= 0:
                # Splash damage on expire
                if proj['type'] == 'splash':
                    for bloon in self.bloons:
                        if not bloon['alive']:
                            continue
                        bx, by = pos_on_path(bloon['dist'])
                        dist = math.sqrt((bx - proj['x']) ** 2 + (by - proj['y']) ** 2)
                        if dist <= SPLASH_RADIUS:
                            self._pop_bloon(bloon)
                continue

            # Check hit bloons
            hit = False
            for bloon in self.bloons:
                if not bloon['alive']:
                    continue
                bx, by = pos_on_path(bloon['dist'])
                dist = math.sqrt((bx - proj['x']) ** 2 + (by - proj['y']) ** 2)
                if dist < 2.0:
                    self._pop_bloon(bloon)
                    hit = True
                    if proj['type'] != 'tack':
                        break  # Single hit for dart/splash proj

            if not hit:
                new_projs.append(proj)
            elif proj['type'] == 'tack':
                pass  # Tack consumed on hit
            # Dart/splash consumed on hit

        self.projectiles = new_projs

        # Clean dead bloons
        self.bloons = [b for b in self.bloons if b['alive']]

        # Check wave end
        if not self.spawn_queue and len(self.bloons) == 0:
            self.wave_active = False
            self.wave_num += 1
            # Wave completion bonus
            self.money += 10 + self.wave_num * 5
            if self.wave_num >= len(WAVES):
                # Won!
                self.state = GameState.WIN
            else:
                self.phase = PHASE_WAVE_END
                self.wave_end_timer = 1.5

    def _update_wave_end(self, inp, dt):
        self.wave_end_timer -= dt
        if self.wave_end_timer <= 0 or inp.action_l or inp.action_r:
            self.phase = PHASE_PLACE
            self.selected_tower = None

    # ==== DRAW ====

    def draw(self):
        self.display.clear(BG_COLOR)

        if self.state == GameState.WIN:
            self._draw_win()
            return

        self._draw_path()
        self._draw_towers()
        self._draw_bloons()
        self._draw_projectiles()
        self._draw_cursor()
        self._draw_hud()

        if self.phase == PHASE_WAVE_END:
            self._draw_wave_end()

    def _draw_path(self):
        """Draw path by connecting waypoints."""
        for i in range(len(PATH_WAYPOINTS) - 1):
            x0, y0 = PATH_WAYPOINTS[i]
            x1, y1 = PATH_WAYPOINTS[i + 1]
            # Draw thick path (multiple lines)
            if x0 == x1:
                # Vertical segment
                ymin, ymax = min(y0, y1), max(y0, y1)
                for y in range(ymin, ymax + 1):
                    for dx in range(-1, 2):
                        self.display.set_pixel(x0 + dx, y, PATH_COLOR)
            else:
                # Horizontal segment
                xmin, xmax = min(x0, x1), max(x0, x1)
                for x in range(xmin, xmax + 1):
                    for dy in range(-1, 2):
                        self.display.set_pixel(x, y0 + dy, PATH_COLOR)

    def _draw_towers(self):
        """Draw all towers as 3x3 sprites."""
        for i, tower in enumerate(self.towers):
            tdef = TOWER_DEFS[tower['type']]
            px = tower['gx'] * CELL_SIZE
            py = tower['gy'] * CELL_SIZE
            color = tdef['color']
            # 3x3 sprite centered in 4x4 cell
            for dy in range(3):
                for dx in range(3):
                    self.display.set_pixel(px + dx, py + dy, color)
            # Upgrade indicator
            if tower['upgraded']:
                self.display.set_pixel(px + 1, py, Colors.YELLOW)

            # Range circle when selected
            if self.selected_tower == i:
                t_range = tdef['up_range'] if tower['upgraded'] else tdef['range']
                cx = px + CELL_SIZE // 2
                cy = py + CELL_SIZE // 2
                self.display.draw_circle(cx, cy, t_range, (60, 60, 60))

    def _draw_bloons(self):
        """Draw bloons as colored dots on path."""
        for bloon in self.bloons:
            if not bloon['alive']:
                continue
            bx, by = pos_on_path(bloon['dist'])
            _, color, _, _, _ = BLOON_TYPES[bloon['type']]
            ix, iy = int(bx), int(by)
            self.display.set_pixel(ix, iy, color)
            # Slow indicator: slight blue tint
            if bloon['slow_timer'] > 0:
                self.display.set_pixel(ix, iy, (100, 180, 255))

    def _draw_projectiles(self):
        """Draw projectiles."""
        for proj in self.projectiles:
            ix, iy = int(proj['x']), int(proj['y'])
            if proj['type'] == 'dart':
                self.display.set_pixel(ix, iy, Colors.WHITE)
            elif proj['type'] == 'tack':
                self.display.set_pixel(ix, iy, Colors.ORANGE)
            elif proj['type'] == 'splash':
                self.display.set_pixel(ix, iy, Colors.GRAY)

    def _draw_cursor(self):
        """Draw placement cursor."""
        px = self.cursor_gx * CELL_SIZE
        py = self.cursor_gy * CELL_SIZE
        blink = int(self.cursor_blink * 4) % 2 == 0

        if not blink:
            return

        # Color: green if can place, red if not
        existing = self._tower_at(self.cursor_gx, self.cursor_gy)
        if existing is not None:
            color = Colors.CYAN  # Selecting existing tower
        elif self._can_place(self.cursor_gx, self.cursor_gy):
            tdef = TOWER_DEFS[self.selected_tower_type]
            color = Colors.GREEN if self.money >= tdef['cost'] else Colors.YELLOW
        else:
            color = Colors.RED

        # 3x3 outline (tower footprint)
        for i in range(3):
            self.display.set_pixel(px + i, py, color)
            self.display.set_pixel(px + i, py + 2, color)
            self.display.set_pixel(px, py + i, color)
            self.display.set_pixel(px + 2, py + i, color)

        # Show range preview when placing
        if existing is None and self._can_place(self.cursor_gx, self.cursor_gy):
            tdef = TOWER_DEFS[self.selected_tower_type]
            cx = px + 1
            cy = py + 1
            self.display.draw_circle(cx, cy, tdef['range'], (40, 40, 40))

    def _draw_hud(self):
        """Draw HUD info."""
        # Top bar background
        self.display.draw_rect(0, 0, 64, 7, Colors.BLACK)

        # Money top-left
        self.display.draw_text_small(2, 1, f"${self.money}", Colors.YELLOW)

        # Lives top-right
        lives_text = f"L:{self.lives}"
        self.display.draw_text_small(44, 1, lives_text, Colors.RED)

        # Bottom bar
        self.display.draw_rect(0, 58, 64, 6, Colors.BLACK)

        # Wave number
        wn = self.wave_num + 1
        if self.phase == PHASE_WAVE or self.wave_active:
            self.display.draw_text_small(2, 59, f"W{wn}", Colors.WHITE)
        elif self.wave_num < len(WAVES):
            self.display.draw_text_small(2, 59, f"W{wn}", Colors.GRAY)
        else:
            self.display.draw_text_small(2, 59, "WIN", Colors.GREEN)

        # Selected tower type and cost / GO hint
        if self.selected_tower is not None:
            t = self.towers[self.selected_tower]
            tdef = TOWER_DEFS[t['type']]
            if t['upgraded']:
                self.display.draw_text_small(20, 59, f"{tdef['name']}+", Colors.CYAN)
            else:
                cost = tdef['upgrade_cost']
                self.display.draw_text_small(20, 59, f"UP${cost}", Colors.CYAN)
        else:
            tdef = TOWER_DEFS[self.selected_tower_type]
            self.display.draw_text_small(20, 59, f"{tdef['name']}", tdef['color'])
            # Show GO hint during place phase
            if self.phase == PHASE_PLACE and self.wave_num < len(WAVES):
                self.display.draw_text_small(48, 59, "GO", Colors.GREEN)

    def _draw_wave_end(self):
        """Show wave completion message."""
        self.display.draw_rect(10, 26, 44, 12, Colors.BLACK)
        self.display.draw_text_small(12, 28, "WAVE", Colors.GREEN)
        self.display.draw_text_small(12, 34, "CLEAR!", Colors.GREEN)

    def _draw_win(self):
        """Victory screen."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(10, 16, "YOU WIN!", Colors.YELLOW)
        self.display.draw_text_small(6, 28, f"SCORE:{self.score}", Colors.WHITE)
        self.display.draw_text_small(6, 38, f"LIVES:{self.lives}", Colors.GREEN)
        self.display.draw_text_small(4, 52, "BTN:MENU", Colors.GRAY)

    def draw_game_over(self, selection=0):
        """Override game over to show TD-specific stats."""
        self.display.clear(Colors.BLACK)
        self.display.draw_text_small(8, 10, "GAME OVER", Colors.RED)
        self.display.draw_text_small(6, 22, f"WAVE:{self.wave_num}", Colors.WHITE)
        self.display.draw_text_small(6, 30, f"SCORE:{self.score}", Colors.WHITE)

        if selection == 0:
            self.display.draw_text_small(4, 44, ">PLAY AGAIN", Colors.YELLOW)
            self.display.draw_text_small(4, 54, " MENU", Colors.GRAY)
        else:
            self.display.draw_text_small(4, 44, " PLAY AGAIN", Colors.GRAY)
            self.display.draw_text_small(4, 54, ">MENU", Colors.YELLOW)

"""
Sand Game - LED Arcade
======================
Falling sand particle physics sandbox inspired by Powder Game (dan-ball.jp).
Place materials and watch them interact: sand falls, water flows, fire burns,
gunpowder explodes, acid dissolves, lava melts ice.

Controls:
  Joystick     - Move cursor
  Space (hold) - Paint selected material
  Both buttons - Toggle material select mode
"""

import random
import math
from arcade import Game, GameState, Display, Colors, InputState

# Material IDs
EMPTY     = 0
SAND      = 1
WATER     = 2
STONE     = 3
FIRE      = 4
OIL       = 5
GUNPOWDER = 6
ACID      = 7
LAVA      = 8
ICE       = 9
STEAM     = 10
WOOD      = 11
PLANT     = 12
ERASE     = 13

# Material properties: (name, color_rgb, behavior, density)
# behavior: 'none','powder','liquid','gas','solid','grow','erase'
MATERIALS = [
    ("EMPTY",     (0, 0, 0),         'none',   0),
    ("SAND",      (194, 178, 128),    'powder', 90),
    ("WATER",     (40, 80, 200),      'liquid', 50),
    ("STONE",     (128, 128, 128),    'solid',  100),
    ("FIRE",      (255, 140, 20),     'gas',    -5),
    ("OIL",       (80, 50, 20),       'liquid', 30),
    ("GUNPOWDER", (60, 60, 60),       'powder', 85),
    ("ACID",      (80, 255, 40),      'liquid', 55),
    ("LAVA",      (255, 80, 10),      'liquid', 95),
    ("ICE",       (160, 220, 255),    'solid',  45),
    ("STEAM",     (200, 200, 210),    'gas',    -10),
    ("WOOD",      (120, 70, 30),      'solid',  100),
    ("PLANT",     (30, 160, 30),      'grow',   100),
    ("ERASE",     (255, 255, 255),    'erase',  0),
]

W = 64
H = 64
SIM_TOP = 7  # rows 0-6 are HUD

# Mode constants
MODE_PLAY = 0
MODE_SELECT = 1


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def mat_color(mat_id, var=0):
    """Get material color with variation applied."""
    r, g, b = MATERIALS[mat_id][1]
    r = clamp(r + var, 0, 255)
    g = clamp(g + var, 0, 255)
    b = clamp(b + var, 0, 255)
    return (r, g, b)


class SandGame(Game):
    name = "SANDGAME"
    description = "Falling sand physics sandbox"
    category = "modern"

    def __init__(self, display: Display):
        super().__init__(display)
        self.reset()

    def reset(self):
        self.state = GameState.PLAYING
        self.score = 0

        # Grid arrays
        self.grid = [[EMPTY] * W for _ in range(H)]
        self.updated = [[False] * W for _ in range(H)]
        self.life = [[0] * W for _ in range(H)]
        self.color_var = [[0] * W for _ in range(H)]

        # Wind grid: (wx, wy) force per cell, decays each frame
        self.wind_x = [[0.0] * W for _ in range(H)]
        self.wind_y = [[0.0] * W for _ in range(H)]

        # Cursor
        self.cx = W // 2
        self.cy = H // 2
        self.blink_timer = 0.0

        # Material selection
        self.selected = SAND
        self.mode = MODE_PLAY

        # Input timing
        self.move_timer = 0.0
        self.btn_hold_time = 0.0   # how long button has been held
        self.btn_was_held = False   # was button held last frame
        self.painting = False       # are we in paint mode (held past threshold)

    def _set_cell(self, x, y, mat_id):
        """Set a cell to a material with fresh properties."""
        self.grid[y][x] = mat_id
        if mat_id == FIRE:
            # Fire is very short-lived: ~3-8 frames (like original Powder Game)
            self.life[y][x] = random.randint(3, 8)
        elif mat_id == STEAM:
            # Steam doesn't move, just fades: handled by per-frame % chance
            self.life[y][x] = 0
        else:
            self.life[y][x] = 0
        self.color_var[y][x] = random.randint(-15, 15)
        self.updated[y][x] = True

    def _swap(self, x1, y1, x2, y2):
        """Swap two cells."""
        self.grid[y1][x1], self.grid[y2][x2] = self.grid[y2][x2], self.grid[y1][x1]
        self.life[y1][x1], self.life[y2][x2] = self.life[y2][x2], self.life[y1][x1]
        self.color_var[y1][x1], self.color_var[y2][x2] = self.color_var[y2][x2], self.color_var[y1][x1]
        self.updated[y1][x1] = True
        self.updated[y2][x2] = True

    def _in_sim(self, x, y):
        return 0 <= x < W and SIM_TOP <= y < H

    def _empty_at(self, x, y):
        return self._in_sim(x, y) and self.grid[y][x] == EMPTY

    def _mat_at(self, x, y):
        if 0 <= x < W and 0 <= y < H:
            return self.grid[y][x]
        return -1

    def _density(self, mat_id):
        if 0 <= mat_id < len(MATERIALS):
            return MATERIALS[mat_id][3]
        return 0

    def _behavior(self, mat_id):
        if 0 <= mat_id < len(MATERIALS):
            return MATERIALS[mat_id][2]
        return 'none'

    def _explode(self, cx, cy, radius):
        """Explosion at (cx,cy) destroying non-stone in radius, spawning fire + wind."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist_sq = dx * dx + dy * dy
                if dist_sq <= radius * radius:
                    nx, ny = cx + dx, cy + dy
                    if self._in_sim(nx, ny):
                        m = self.grid[ny][nx]
                        if m != STONE:
                            if random.random() < 0.4:
                                self._set_cell(nx, ny, FIRE)
                            else:
                                self._set_cell(nx, ny, EMPTY)
                        # Outward wind from explosion
                        dist = max(1.0, dist_sq ** 0.5)
                        strength = 3.0 / dist
                        self.wind_x[ny][nx] += dx / dist * strength
                        self.wind_y[ny][nx] += dy / dist * strength

    def _update_powder(self, x, y):
        """Update a powder particle (sand, gunpowder)."""
        # Try straight down
        if self._empty_at(x, y + 1):
            self._swap(x, y, x, y + 1)
            return
        # Density swap: sink through lighter liquids
        below = self._mat_at(x, y + 1)
        if below > 0 and self._behavior(below) in ('liquid', 'gas') and self._density(self.grid[y][x]) > self._density(below):
            self._swap(x, y, x, y + 1)
            return
        # Try diagonals (randomized)
        dirs = [(-1, 1), (1, 1)]
        if random.random() < 0.5:
            dirs.reverse()
        for dx, dy in dirs:
            nx = x + dx
            if self._empty_at(nx, y + 1):
                self._swap(x, y, nx, y + 1)
                return
            nb = self._mat_at(nx, y + 1)
            if nb > 0 and self._behavior(nb) in ('liquid', 'gas') and self._density(self.grid[y][x]) > self._density(nb):
                self._swap(x, y, nx, y + 1)
                return

    def _update_liquid(self, x, y):
        """Update a liquid particle (water, oil, acid, lava)."""
        mat = self.grid[y][x]
        dens = self._density(mat)
        # Try straight down
        if self._empty_at(x, y + 1):
            self._swap(x, y, x, y + 1)
            return
        below = self._mat_at(x, y + 1)
        if below > 0 and self._behavior(below) in ('liquid', 'gas') and dens > self._density(below):
            self._swap(x, y, x, y + 1)
            return
        # Try diagonals down
        dirs = [(-1, 1), (1, 1)]
        if random.random() < 0.5:
            dirs.reverse()
        for dx, dy in dirs:
            nx = x + dx
            if self._empty_at(nx, y + 1):
                self._swap(x, y, nx, y + 1)
                return
            nb = self._mat_at(nx, y + 1)
            if nb > 0 and self._behavior(nb) in ('liquid', 'gas') and dens > self._density(nb):
                self._swap(x, y, nx, y + 1)
                return
        # Spread horizontally (1-3 cells)
        spread = random.randint(1, 3)
        d = 1 if random.random() < 0.5 else -1
        for i in range(1, spread + 1):
            nx = x + d * i
            if self._empty_at(nx, y):
                self._swap(x, y, nx, y)
                return
            elif not self._in_sim(nx, y) or self.grid[y][nx] != EMPTY:
                break
        # Try the other direction
        d = -d
        for i in range(1, spread + 1):
            nx = x + d * i
            if self._empty_at(nx, y):
                self._swap(x, y, nx, y)
                return
            elif not self._in_sim(nx, y) or self.grid[y][nx] != EMPTY:
                break

    def _update_fire(self, x, y):
        """Update fire: very short-lived, rises slightly, spreads to neighbors."""
        self.life[y][x] -= 1
        if self.life[y][x] <= 0:
            self._set_cell(x, y, EMPTY)
            return
        # Fire generates upward wind
        self.wind_y[y][x] -= 0.4
        if self._in_sim(x, y - 1):
            self.wind_y[y - 1][x] -= 0.2
        # Fire rises (try up, up-diagonal, or random drift)
        if random.random() < 0.6:
            if self._empty_at(x, y - 1):
                self._swap(x, y, x, y - 1)
                return
        dirs = [(-1, -1), (1, -1)]
        if random.random() < 0.5:
            dirs.reverse()
        for dx, dy in dirs:
            if random.random() < 0.3 and self._empty_at(x + dx, y + dy):
                self._swap(x, y, x + dx, y + dy)
                return
        # Random horizontal drift
        if random.random() < 0.2:
            dx = 1 if random.random() < 0.5 else -1
            if self._empty_at(x + dx, y):
                self._swap(x, y, x + dx, y)

    def _update_steam(self, x, y):
        """Steam: stationary, ~10% chance to vanish each frame (like original)."""
        if random.random() < 0.10:
            self._set_cell(x, y, EMPTY)
            return
        # Slight random drift (steam doesn't actively rise in original,
        # but we give it very slight upward tendency for visual interest)
        if random.random() < 0.15:
            dx = random.choice([-1, 0, 0, 1])
            dy = random.choice([-1, -1, 0])
            if self._empty_at(x + dx, y + dy):
                self._swap(x, y, x + dx, y + dy)

    def _update_plant(self, x, y):
        """Plant grows vine-like: upward bias, clings to surfaces, water accelerates."""
        # Base growth chance: 1.5% dry, 8% if water nearby
        has_water = False
        water_pos = None
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            if self._mat_at(x + dx, y + dy) == WATER:
                has_water = True
                water_pos = (x + dx, y + dy)
                break

        chance = 0.08 if has_water else 0.015
        if random.random() > chance:
            return

        # Has a solid/plant neighbor to cling to? (vine grows on surfaces)
        has_support = False
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nm = self._mat_at(x + dx, y + dy)
            if nm in (STONE, WOOD, SAND, PLANT):
                has_support = True
                break
        # Also count the cell below as support
        if self._mat_at(x, y + 1) not in (EMPTY, -1):
            has_support = True

        # Growth directions: strong upward bias, slight sideways
        grow_dirs = [(0, -1), (0, -1), (0, -1),   # up (3x weight)
                     (-1, 0), (1, 0),              # sideways
                     (-1, -1), (1, -1)]            # diagonal up
        random.shuffle(grow_dirs)

        for dx, dy in grow_dirs:
            nx, ny = x + dx, y + dy
            if not self._empty_at(nx, ny):
                continue
            # For non-upward growth, require support nearby
            if dy >= 0 and not has_support:
                continue
            self._set_cell(nx, ny, PLANT)
            # Consume water if available
            if water_pos:
                self._set_cell(water_pos[0], water_pos[1], EMPTY)
            return

    def _check_interactions(self, x, y):
        """Check and apply material interactions for cell at (x,y)."""
        mat = self.grid[y][x]
        if mat == EMPTY:
            return

        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            nm = self._mat_at(nx, ny)
            if nm >= 0:
                neighbors.append((nx, ny, nm))

        if mat == FIRE:
            for nx, ny, nm in neighbors:
                if nm == WOOD:
                    # Wood burns slowly but steadily
                    if random.random() < 0.08:
                        self._set_cell(nx, ny, FIRE)
                elif nm == PLANT:
                    # Plant burns fast and clean (vine-like)
                    if random.random() < 0.45:
                        self._set_cell(nx, ny, FIRE)
                elif nm == OIL:
                    # Oil is highly flammable - catches almost instantly
                    if random.random() < 0.5:
                        self._set_cell(nx, ny, FIRE)
                        # Oil fire produces extra fire in nearby empty cells
                        for ddx, ddy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                            if self._empty_at(nx + ddx, ny + ddy) and random.random() < 0.3:
                                self._set_cell(nx + ddx, ny + ddy, FIRE)
                elif nm == GUNPOWDER:
                    self._explode(nx, ny, 5)
                    return
                elif nm == ICE:
                    if random.random() < 0.12:
                        self._set_cell(nx, ny, WATER)
                elif nm == SAND:
                    # Fire can turn sand to glass-like (stone) at low rate
                    pass

        elif mat == WATER:
            for nx, ny, nm in neighbors:
                if nm == FIRE:
                    # Water extinguishes fire
                    self._set_cell(nx, ny, STEAM)
                elif nm == LAVA:
                    # Water + lava = stone + steam
                    self._set_cell(nx, ny, STONE)
                    self._set_cell(x, y, STEAM)
                    return
                elif nm == ICE:
                    # Water freezes on contact with ice
                    if random.random() < 0.06:
                        self._set_cell(x, y, ICE)
                        return

        elif mat == LAVA:
            for nx, ny, nm in neighbors:
                if nm == WATER:
                    # Lava + water = steam + stone
                    self._set_cell(nx, ny, STEAM)
                    self._set_cell(x, y, STONE)
                    return
                elif nm == STONE:
                    # Lava converts stone into more lava (key original mechanic)
                    if random.random() < 0.02:
                        self._set_cell(nx, ny, LAVA)
                elif nm == WOOD:
                    if random.random() < 0.15:
                        self._set_cell(nx, ny, FIRE)
                elif nm == PLANT:
                    if random.random() < 0.5:
                        self._set_cell(nx, ny, FIRE)
                elif nm == ICE:
                    if random.random() < 0.15:
                        self._set_cell(nx, ny, WATER)
                elif nm == OIL:
                    if random.random() < 0.4:
                        self._set_cell(nx, ny, FIRE)
                elif nm == GUNPOWDER:
                    self._explode(nx, ny, 5)
                    return

        elif mat == ACID:
            # Acid dissolves almost everything (like original: eats through
            # all materials except stone). Acid self-consumes in the process.
            for nx, ny, nm in neighbors:
                if nm in (WOOD, SAND, ICE, PLANT, GUNPOWDER, OIL):
                    # Easy to dissolve
                    if random.random() < 0.15:
                        self._set_cell(nx, ny, EMPTY)
                        if random.random() < 0.3:
                            self._set_cell(x, y, EMPTY)
                            return
                elif nm == WATER:
                    # Acid destroys water (1:4 ratio in original)
                    if random.random() < 0.20:
                        self._set_cell(nx, ny, EMPTY)
                elif nm == LAVA:
                    # Acid and lava both consumed
                    if random.random() < 0.08:
                        self._set_cell(nx, ny, EMPTY)
                        self._set_cell(x, y, EMPTY)
                        return
                # Stone resists acid (like glass in original)

        elif mat == ICE:
            # Ice freezes adjacent water
            for nx, ny, nm in neighbors:
                if nm == WATER:
                    if random.random() < 0.04:
                        self._set_cell(nx, ny, ICE)

    def _apply_wind(self):
        """Apply wind forces to non-solid particles, then decay wind."""
        for y in range(H - 1, SIM_TOP - 1, -1):
            for x in range(W):
                wx = self.wind_x[y][x]
                wy = self.wind_y[y][x]
                if abs(wx) < 0.3 and abs(wy) < 0.3:
                    # Decay small wind to zero
                    self.wind_x[y][x] = 0.0
                    self.wind_y[y][x] = 0.0
                    continue

                mat = self.grid[y][x]
                if mat == EMPTY:
                    # Propagate wind to neighbors (diffuse)
                    for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                        nx, ny = x + dx, y + dy
                        if self._in_sim(nx, ny):
                            self.wind_x[ny][nx] += wx * 0.1
                            self.wind_y[ny][nx] += wy * 0.1
                elif mat != EMPTY:
                    behav = self._behavior(mat)
                    # Wind moves non-solid, non-grow particles
                    if behav in ('powder', 'liquid', 'gas'):
                        # Convert wind force to displacement (probabilistic)
                        dx = 1 if wx > 0.5 else (-1 if wx < -0.5 else 0)
                        dy = 1 if wy > 0.5 else (-1 if wy < -0.5 else 0)
                        if dx != 0 or dy != 0:
                            nx, ny = x + dx, y + dy
                            if self._empty_at(nx, ny):
                                self._swap(x, y, nx, ny)

                # Decay wind
                self.wind_x[y][x] *= 0.7
                self.wind_y[y][x] *= 0.7

    def _simulate(self):
        """Run one frame of physics simulation."""
        # Clear updated flags
        for y in range(H):
            for x in range(W):
                self.updated[y][x] = False

        # Apply wind forces before main sim
        self._apply_wind()

        # Randomize horizontal scan direction
        x_range = list(range(W))
        if random.random() < 0.5:
            x_range.reverse()

        # Scan bottom-to-top for falling particles
        for y in range(H - 1, SIM_TOP - 1, -1):
            for x in x_range:
                if self.updated[y][x]:
                    continue
                mat = self.grid[y][x]
                if mat == EMPTY:
                    continue

                behav = self._behavior(mat)
                if behav == 'powder':
                    self._update_powder(x, y)
                elif behav == 'liquid':
                    self._update_liquid(x, y)
                elif mat == FIRE:
                    self._update_fire(x, y)
                elif mat == STEAM:
                    self._update_steam(x, y)
                elif behav == 'grow':
                    self._update_plant(x, y)

                # Check interactions at current cell position
                if self._in_sim(x, y) and self.grid[y][x] != EMPTY:
                    self._check_interactions(x, y)

        # Second pass: check interactions for particles that landed in new spots
        for y in range(H - 1, SIM_TOP - 1, -1):
            for x in x_range:
                mat = self.grid[y][x]
                if mat != EMPTY and self.updated[y][x]:
                    self._check_interactions(x, y)

    def update(self, input_state: InputState, dt: float):
        if self.state != GameState.PLAYING:
            return

        self.blink_timer += dt

        if self.mode == MODE_SELECT:
            self._update_select_mode(input_state, dt)
        else:
            self._update_play_mode(input_state, dt)

        # Unified button handling: either button counts the same
        btn_now = input_state.action_l_held or input_state.action_r_held
        if btn_now:
            self.btn_hold_time += dt
            if self.btn_hold_time >= 0.15:
                self.painting = True
        else:
            if self.btn_was_held and self.btn_hold_time < 0.15:
                # Quick tap: toggle mode
                self.mode = MODE_SELECT if self.mode == MODE_PLAY else MODE_PLAY
            self.btn_hold_time = 0.0
            self.painting = False
        self.btn_was_held = btn_now

        # Run simulation every frame regardless of mode
        self._simulate()

    def _update_play_mode(self, inp: InputState, dt: float):
        """Handle input in play mode."""
        # Cursor movement (with repeat)
        self.move_timer += dt
        rate = 0.08  # seconds between moves when held
        if inp.any_direction:
            if inp.up_pressed or inp.down_pressed or inp.left_pressed or inp.right_pressed:
                self.move_timer = 0.0
                self.cx = clamp(self.cx + inp.dx, 0, W - 1)
                self.cy = clamp(self.cy + inp.dy, SIM_TOP, H - 1)
            elif self.move_timer >= rate:
                self.move_timer = 0.0
                self.cx = clamp(self.cx + inp.dx, 0, W - 1)
                self.cy = clamp(self.cy + inp.dy, SIM_TOP, H - 1)

        # Paint material with 2x2 brush while button held past tap threshold
        if self.painting:
            for dy in range(2):
                for dx in range(2):
                    bx, by = self.cx + dx, self.cy + dy
                    if self.selected == ERASE:
                        if self._in_sim(bx, by):
                            self._set_cell(bx, by, EMPTY)
                    else:
                        if self._in_sim(bx, by) and self.grid[by][bx] == EMPTY:
                            self._set_cell(bx, by, self.selected)

    def _update_select_mode(self, inp: InputState, dt: float):
        """Handle input in material select mode."""
        if inp.up_pressed:
            self.selected = (self.selected - 1) % len(MATERIALS)
            if self.selected == EMPTY:
                self.selected = ERASE
        if inp.down_pressed:
            self.selected = (self.selected + 1) % len(MATERIALS)
            if self.selected == EMPTY:
                self.selected = SAND

    def draw(self):
        self.display.clear()

        if self.mode == MODE_SELECT:
            self._draw_select_screen()
        else:
            self._draw_play_screen()

    def _draw_play_screen(self):
        """Draw the simulation grid and HUD."""
        # Draw HUD: material name in its color
        name = MATERIALS[self.selected][0]
        color = MATERIALS[self.selected][1]
        if self.selected == EMPTY:
            color = (128, 128, 128)
        self.display.draw_text_small(2, 1, name, color)

        # Divider line
        for x in range(W):
            self.display.set_pixel(x, SIM_TOP - 1, (40, 40, 40))

        # Draw grid
        for y in range(SIM_TOP, H):
            for x in range(W):
                mat = self.grid[y][x]
                if mat != EMPTY:
                    c = mat_color(mat, self.color_var[y][x])
                    # Fire flicker: cycle red-orange-yellow
                    if mat == FIRE:
                        flicker = random.randint(-40, 40)
                        c = (clamp(c[0] + flicker, 100, 255),
                             clamp(c[1] + flicker, 0, 200),
                             clamp(random.randint(0, 30), 0, 255))
                    elif mat == LAVA:
                        flicker = random.randint(-20, 20)
                        c = (clamp(c[0] + flicker, 0, 255),
                             clamp(c[1] + flicker // 2, 0, 255),
                             clamp(c[2], 0, 255))
                    elif mat == ACID:
                        # Acid glows
                        flicker = random.randint(-10, 20)
                        c = (clamp(c[0] + flicker, 0, 255),
                             clamp(c[1] + flicker, 0, 255),
                             clamp(c[2], 0, 255))
                    self.display.set_pixel(x, y, c)

        # Draw cursor (blink between white and material color)
        blink = int(self.blink_timer * 6) % 2 == 0
        if blink:
            cursor_color = (255, 255, 255)
        else:
            cursor_color = MATERIALS[self.selected][1]
            if self.selected == EMPTY:
                cursor_color = (128, 128, 128)
        self.display.set_pixel(self.cx, self.cy, cursor_color)

    def _draw_select_screen(self):
        """Draw the full-screen material selection list."""
        # Calculate scroll offset so selected item is visible
        items_visible = 8  # how many fit on screen
        total = len(MATERIALS) - 1  # skip EMPTY (index 0)
        # Map selected (1-13) to list index (0-12)
        sel_idx = self.selected - 1
        scroll = max(0, min(sel_idx - items_visible // 2, total - items_visible))

        y = 2
        for i in range(scroll, min(scroll + items_visible, total)):
            mat_id = i + 1  # skip EMPTY
            name = MATERIALS[mat_id][0]
            color = MATERIALS[mat_id][1]
            if mat_id == self.selected:
                # Highlight: draw '>' prefix
                self.display.draw_text_small(2, y, ">", (255, 255, 255))
                self.display.draw_text_small(6, y, name, color)
            else:
                self.display.draw_text_small(6, y, name, (color[0] // 2, color[1] // 2, color[2] // 2))
            y += 7

"""
Sand Game - LED Arcade
======================
Falling sand particle physics sandbox inspired by Powder Game (dan-ball.jp).
Place materials and watch them interact: sand falls, water flows, fire burns,
gunpowder explodes, acid dissolves, lava melts ice.

Controls:
  Joystick     - Move cursor
  Button (tap) - Toggle material select mode
  Button (hold)- Paint selected material
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
GAS       = 13
METAL     = 14
NITRO     = 15
FUSE      = 16
VINE      = 17
ERASE     = 18

# Material properties: (name, color_rgb, behavior, density)
# behavior: 'none','powder','liquid','gas_up','solid','grow','vine','fuse','erase'
MATERIALS = [
    ("EMPTY",     (0, 0, 0),         'none',   0),
    ("SAND",      (194, 178, 128),    'powder', 90),
    ("WATER",     (40, 80, 200),      'liquid', 50),
    ("STONE",     (128, 128, 128),    'solid',  100),
    ("FIRE",      (255, 140, 20),     'gas_up', -5),
    ("OIL",       (80, 50, 20),       'liquid', 30),
    ("GUNPOWDER", (60, 60, 60),       'powder', 85),
    ("ACID",      (80, 255, 40),      'liquid', 55),
    ("LAVA",      (255, 80, 10),      'liquid', 95),
    ("ICE",       (160, 220, 255),    'solid',  45),
    ("STEAM",     (200, 200, 210),    'gas_up', -10),
    ("WOOD",      (120, 70, 30),      'solid',  100),
    ("PLANT",     (30, 160, 30),      'grow',   100),
    ("GAS",       (220, 180, 200),    'gas_up', -8),
    ("METAL",     (90, 95, 105),      'solid',  100),
    ("NITRO",     (100, 200, 80),     'liquid', 60),
    ("FUSE",      (140, 100, 60),     'fuse',   100),
    ("VINE",      (20, 200, 20),      'vine',   100),
    ("ERASE",     (255, 255, 255),    'erase',  0),
]

W = 64
H = 64
SIM_TOP = 7  # rows 0-6 are HUD

# Mode constants
MODE_PLAY = 0
MODE_SELECT = 1

WIND_MAX = 10.0  # clamp wind values

# Thermal properties: material -> (emit_temp or None, conductivity)
THERMAL = {
    EMPTY:     (None, 0.6),
    SAND:      (None, 0.25),
    WATER:     (None, 0.4),
    STONE:     (None, 0.2),
    FIRE:      (400,  1.0),
    OIL:       (None, 0.15),
    GUNPOWDER: (None, 0.2),
    ACID:      (None, 0.4),
    LAVA:      (600,  0.8),
    ICE:       (-30,  0.5),
    STEAM:     (105,  0.4),
    WOOD:      (None, 0.1),
    PLANT:     (None, 0.1),
    GAS:       (None, 0.5),
    METAL:     (None, 0.9),
    NITRO:     (None, 0.35),
    FUSE:      (None, 0.1),
    VINE:      (None, 0.1),
}

# Wind drag: material-specific overrides and behavior defaults
WIND_DRAG = {GAS: 0.8, STEAM: 0.7, FIRE: 0.6, LAVA: 0.0}
DRAG_POWDER = 0.65
DRAG_LIQUID = 0.2


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
    name = "POWDER GAME"
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

        # Wind grid: force per cell
        self.wind_x = [[0.0] * W for _ in range(H)]
        self.wind_y = [[0.0] * W for _ in range(H)]

        # Temperature grid (room temp = 20)
        self.temp = [[20.0] * W for _ in range(H)]

        # Cursor
        self.cx = W // 2
        self.cy = H // 2
        self.blink_timer = 0.0

        # Material selection
        self.selected = SAND
        self.mode = MODE_PLAY

        # Input timing
        self.move_timer = 0.0
        self.btn_hold_time = 0.0
        self.btn_was_held = False
        self.painting = False

    def _set_cell(self, x, y, mat_id):
        """Set a cell to a material with fresh properties."""
        self.grid[y][x] = mat_id
        if mat_id == FIRE:
            self.life[y][x] = random.randint(3, 8)
            self.temp[y][x] = 400.0
        elif mat_id == LAVA:
            self.life[y][x] = 0
            self.temp[y][x] = 600.0
        elif mat_id == ICE:
            self.life[y][x] = 0
            self.temp[y][x] = -20.0
        elif mat_id == FUSE:
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
        self.temp[y1][x1], self.temp[y2][x2] = self.temp[y2][x2], self.temp[y1][x1]
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

    def _add_wind(self, x, y, wx, wy):
        """Add wind at position, clamped."""
        if self._in_sim(x, y):
            self.wind_x[y][x] = clamp(self.wind_x[y][x] + wx, -WIND_MAX, WIND_MAX)
            self.wind_y[y][x] = clamp(self.wind_y[y][x] + wy, -WIND_MAX, WIND_MAX)

    def _explode(self, cx, cy, radius):
        """Explosion at (cx,cy) destroying non-stone in radius, spawning fire + wind."""
        for dy in range(-radius, radius + 1):
            for dx in range(-radius, radius + 1):
                dist_sq = dx * dx + dy * dy
                if dist_sq <= radius * radius:
                    nx, ny = cx + dx, cy + dy
                    if self._in_sim(nx, ny):
                        m = self.grid[ny][nx]
                        if m == STONE or m == METAL:
                            pass  # survives
                        elif random.random() < 0.4:
                            self._set_cell(nx, ny, FIRE)
                        else:
                            self._set_cell(nx, ny, EMPTY)
                        # Outward wind from explosion
                        dist = max(1.0, dist_sq ** 0.5)
                        strength = 2.0 / dist
                        self._add_wind(nx, ny, dx / dist * strength, dy / dist * strength)

    def _update_powder(self, x, y):
        """Update a powder particle (sand, gunpowder)."""
        if self._empty_at(x, y + 1):
            self._swap(x, y, x, y + 1)
            return
        below = self._mat_at(x, y + 1)
        if below > 0 and self._behavior(below) in ('liquid', 'gas_up') and self._density(self.grid[y][x]) > self._density(below):
            self._swap(x, y, x, y + 1)
            return
        dirs = [(-1, 1), (1, 1)]
        if random.random() < 0.5:
            dirs.reverse()
        for dx, dy in dirs:
            nx = x + dx
            if self._empty_at(nx, y + 1):
                self._swap(x, y, nx, y + 1)
                return
            nb = self._mat_at(nx, y + 1)
            if nb > 0 and self._behavior(nb) in ('liquid', 'gas_up') and self._density(self.grid[y][x]) > self._density(nb):
                self._swap(x, y, nx, y + 1)
                return

    def _update_liquid(self, x, y):
        """Update a liquid particle (water, oil, acid, lava, nitro)."""
        mat = self.grid[y][x]
        dens = self._density(mat)
        if self._empty_at(x, y + 1):
            self._swap(x, y, x, y + 1)
            return
        below = self._mat_at(x, y + 1)
        if below > 0 and self._behavior(below) in ('liquid', 'gas_up') and dens > self._density(below):
            self._swap(x, y, x, y + 1)
            return
        dirs = [(-1, 1), (1, 1)]
        if random.random() < 0.5:
            dirs.reverse()
        for dx, dy in dirs:
            nx = x + dx
            if self._empty_at(nx, y + 1):
                self._swap(x, y, nx, y + 1)
                return
            nb = self._mat_at(nx, y + 1)
            if nb > 0 and self._behavior(nb) in ('liquid', 'gas_up') and dens > self._density(nb):
                self._swap(x, y, nx, y + 1)
                return
        # Spread horizontally
        spread = random.randint(1, 3)
        d = 1 if random.random() < 0.5 else -1
        for i in range(1, spread + 1):
            nx = x + d * i
            if self._empty_at(nx, y):
                self._swap(x, y, nx, y)
                return
            elif not self._in_sim(nx, y) or self.grid[y][nx] != EMPTY:
                break
        d = -d
        for i in range(1, spread + 1):
            nx = x + d * i
            if self._empty_at(nx, y):
                self._swap(x, y, nx, y)
                return
            elif not self._in_sim(nx, y) or self.grid[y][nx] != EMPTY:
                break

    def _update_gas_element(self, x, y):
        """Update GAS: floats upward, repels self, extremely wind-sensitive."""
        # Rise
        if self._empty_at(x, y - 1):
            self._swap(x, y, x, y - 1)
            return
        # Diagonal up
        dirs = [(-1, -1), (1, -1)]
        if random.random() < 0.5:
            dirs.reverse()
        for dx, dy in dirs:
            if self._empty_at(x + dx, y + dy):
                self._swap(x, y, x + dx, y + dy)
                return
        # Horizontal spread (gas repels itself)
        d = 1 if random.random() < 0.5 else -1
        if self._empty_at(x + d, y):
            self._swap(x, y, x + d, y)

    def _update_fire(self, x, y):
        """Update fire: very short-lived, rises slightly."""
        self.life[y][x] -= 1
        if self.life[y][x] <= 0:
            self._set_cell(x, y, EMPTY)
            return
        # Fire rises
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
        if random.random() < 0.2:
            dx = 1 if random.random() < 0.5 else -1
            if self._empty_at(x + dx, y):
                self._swap(x, y, x + dx, y)

    def _update_steam(self, x, y):
        """Steam: mostly stationary, ~10% chance to vanish each frame."""
        if random.random() < 0.10:
            self._set_cell(x, y, EMPTY)
            return
        if random.random() < 0.15:
            dx = random.choice([-1, 0, 0, 1])
            dy = random.choice([-1, -1, 0])
            if self._empty_at(x + dx, y + dy):
                self._swap(x, y, x + dx, y + dy)

    def _update_fuse(self, x, y):
        """Fuse: when lit (life>0), burns slowly with sparks, ignites neighbors."""
        if self.life[y][x] <= 0:
            return  # unlit, do nothing
        self.life[y][x] -= 1
        if self.life[y][x] <= 0:
            # Fuse consumed: spawn spark (fire)
            self._set_cell(x, y, FIRE)
            return
        # Sparks fly off randomly
        if random.random() < 0.3:
            dx = random.choice([-1, 0, 1])
            dy = random.choice([-1, 0, 1])
            if self._empty_at(x + dx, y + dy):
                self._set_cell(x + dx, y + dy, FIRE)
        # Spread flame to adjacent fuse
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nm = self._mat_at(x + dx, y + dy)
            if nm == FUSE and self._in_sim(x + dx, y + dy) and self.life[y + dy][x + dx] == 0:
                self.life[y + dy][x + dx] = random.randint(8, 15)  # slow burn
                self.updated[y + dy][x + dx] = True
            elif nm == GUNPOWDER:
                self._explode(x + dx, y + dy, 5)
            elif nm == NITRO:
                self._explode(x + dx, y + dy, 7)

    def _update_plant(self, x, y):
        """Plant grows vine-like: upward bias, clings to surfaces, water accelerates."""
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

        has_support = False
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nm = self._mat_at(x + dx, y + dy)
            if nm in (STONE, WOOD, SAND, PLANT, METAL):
                has_support = True
                break
        if self._mat_at(x, y + 1) not in (EMPTY, -1):
            has_support = True

        grow_dirs = [(0, -1), (0, -1), (0, -1),
                     (-1, 0), (1, 0),
                     (-1, -1), (1, -1)]
        random.shuffle(grow_dirs)

        for dx, dy in grow_dirs:
            nx, ny = x + dx, y + dy
            if not self._empty_at(nx, ny):
                continue
            if dy >= 0 and not has_support:
                continue
            self._set_cell(nx, ny, PLANT)
            if water_pos:
                self._set_cell(water_pos[0], water_pos[1], EMPTY)
            return

    def _update_vine(self, x, y):
        """Vine: grows on EVERYTHING (even fire/liquid), burns extremely fast."""
        if random.random() > 0.06:
            return
        # Vine grows into any adjacent cell that isn't stone/metal/vine
        grow_dirs = [(0, -1), (0, 1), (-1, 0), (1, 0),
                     (-1, -1), (1, -1), (-1, 1), (1, 1)]
        random.shuffle(grow_dirs)
        for dx, dy in grow_dirs:
            nx, ny = x + dx, y + dy
            if not self._in_sim(nx, ny):
                continue
            nm = self.grid[ny][nx]
            if nm == EMPTY:
                self._set_cell(nx, ny, VINE)
                return
            # Vine can overgrow non-solid materials (except stone/metal/vine)
            if nm not in (STONE, METAL, VINE, WOOD) and self._behavior(nm) != 'solid':
                self._set_cell(nx, ny, VINE)
                return

    def _check_interactions(self, x, y):
        """Check and apply direct (non-thermal) material interactions."""
        mat = self.grid[y][x]
        if mat == EMPTY:
            return

        neighbors = []
        for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nx, ny = x + dx, y + dy
            nm = self._mat_at(nx, ny)
            if nm >= 0:
                neighbors.append((nx, ny, nm))

        if mat == WATER:
            for nx, ny, nm in neighbors:
                if nm == FIRE:
                    self._set_cell(nx, ny, STEAM)
                    self.temp[ny][nx] = 100.0
                elif nm == LAVA:
                    self._set_cell(nx, ny, STONE)
                    self.temp[ny][nx] = 80.0
                    self._set_cell(x, y, STEAM)
                    self.temp[y][x] = 100.0
                    return
                elif nm == METAL:
                    if random.random() < 0.005:
                        self._set_cell(nx, ny, SAND)

        elif mat == LAVA:
            for nx, ny, nm in neighbors:
                if nm == WATER:
                    self._set_cell(nx, ny, STEAM)
                    self.temp[ny][nx] = 100.0
                    self._set_cell(x, y, STONE)
                    self.temp[y][x] = 80.0
                    return
                elif nm == STONE:
                    if random.random() < 0.02:
                        self._set_cell(nx, ny, LAVA)
                elif nm == METAL:
                    if random.random() < 0.03:
                        self._set_cell(nx, ny, LAVA)

        elif mat == ACID:
            for nx, ny, nm in neighbors:
                if nm in (WOOD, SAND, ICE, PLANT, GUNPOWDER, OIL, FUSE, VINE, NITRO):
                    if random.random() < 0.15:
                        self._set_cell(nx, ny, EMPTY)
                        if random.random() < 0.3:
                            self._set_cell(x, y, EMPTY)
                            return
                elif nm == METAL:
                    if random.random() < 0.03:
                        self._set_cell(nx, ny, EMPTY)
                        if random.random() < 0.5:
                            self._set_cell(x, y, EMPTY)
                            return
                elif nm == WATER:
                    if random.random() < 0.20:
                        self._set_cell(nx, ny, EMPTY)
                elif nm == LAVA:
                    if random.random() < 0.08:
                        self._set_cell(nx, ny, EMPTY)
                        self._set_cell(x, y, EMPTY)
                        return

    def _generate_wind(self):
        """Step A: heat sources inject wind with turbulence."""
        for y in range(SIM_TOP, H):
            for x in range(W):
                mat = self.grid[y][x]
                if mat == FIRE:
                    self._add_wind(x, y, random.uniform(-0.8, 0.8), -1.2)
                elif mat == LAVA:
                    self._add_wind(x, y, random.uniform(-1.4, 1.4), -1.8)
                elif mat == STEAM:
                    self._add_wind(x, y, random.uniform(-0.3, 0.3), -0.6)

    def _propagate_wind(self):
        """Step B: wind propagates via advection (directional) + diffusion."""
        new_wx = [[0.0] * W for _ in range(H)]
        new_wy = [[0.0] * W for _ in range(H)]

        for y in range(SIM_TOP, H):
            for x in range(W):
                wx = self.wind_x[y][x]
                wy = self.wind_y[y][x]
                if abs(wx) < 0.05 and abs(wy) < 0.05:
                    continue

                # Normalize wind direction for advection weighting
                mag = (wx * wx + wy * wy) ** 0.5
                if mag > 0.01:
                    dir_x = wx / mag
                    dir_y = wy / mag
                else:
                    dir_x = dir_y = 0.0

                diffuse = 0.08   # isotropic spread (creates eddies)
                advect = 0.45    # strong directional push
                total_sent = 0.0

                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if not self._in_sim(nx, ny):
                        continue
                    nm = self.grid[ny][nx]
                    behav = self._behavior(nm) if nm != EMPTY else 'none'
                    if behav in ('solid', 'fuse') and nm != ICE:
                        continue  # blocked by solid

                    # Advection: how aligned is this neighbor with wind flow?
                    dot = dir_x * dx + dir_y * dy  # -1 to 1
                    share = diffuse + advect * max(dot, 0.0)
                    new_wx[ny][nx] += wx * share
                    new_wy[ny][nx] += wy * share
                    total_sent += share

                # Keep remainder (more kept when blocked on sides)
                kept = max(1.0 - total_sent, 0.0)
                new_wx[y][x] += wx * kept
                new_wy[y][x] += wy * kept

        # Decay, turbulence perturbation, and apply
        for y in range(SIM_TOP, H):
            for x in range(W):
                vx = new_wx[y][x] * 0.94
                vy = new_wy[y][x] * 0.94
                # Turbulence: wind drifts randomly as it flows
                if abs(vx) > 0.1 or abs(vy) > 0.1:
                    vx += random.uniform(-0.15, 0.15)
                    vy += random.uniform(-0.15, 0.15)
                self.wind_x[y][x] = clamp(vx, -WIND_MAX, WIND_MAX)
                self.wind_y[y][x] = clamp(vy, -WIND_MAX, WIND_MAX)
                if abs(self.wind_x[y][x]) < 0.05:
                    self.wind_x[y][x] = 0.0
                if abs(self.wind_y[y][x]) < 0.05:
                    self.wind_y[y][x] = 0.0

    def _apply_wind(self):
        """Step C: wind displaces particles based on drag coefficients."""
        for y in range(H - 1, SIM_TOP - 1, -1):
            for x in range(W):
                wx = self.wind_x[y][x]
                wy = self.wind_y[y][x]
                if abs(wx) < 0.05 and abs(wy) < 0.05:
                    continue

                mat = self.grid[y][x]
                if mat == EMPTY:
                    continue

                # Get drag coefficient
                if mat in WIND_DRAG:
                    drag = WIND_DRAG[mat]
                else:
                    behav = self._behavior(mat)
                    if behav == 'powder':
                        drag = DRAG_POWDER
                    elif behav == 'liquid':
                        drag = DRAG_LIQUID
                    else:
                        drag = 0.0  # solid, plant, vine, fuse

                if drag <= 0.0:
                    continue

                force = (wx * wx + wy * wy) ** 0.5 * drag
                moved = False

                # Horizontal displacement
                if abs(wx) * drag > 0.05 and random.random() < abs(wx) * drag:
                    dx = 1 if wx > 0 else -1
                    nx = x + dx
                    if self._empty_at(nx, y):
                        self._swap(x, y, nx, y)
                        moved = True
                    elif self._in_sim(nx, y) and self.grid[y][nx] != EMPTY:
                        # Swap with lighter material (wind pushes through)
                        nm = self.grid[y][nx]
                        if self._density(nm) < self._density(mat) and self._behavior(nm) not in ('solid', 'fuse'):
                            self._swap(x, y, nx, y)
                            moved = True

                # Vertical displacement
                cur_mat = self.grid[y][x]
                if cur_mat != EMPTY and abs(wy) * drag > 0.05 and random.random() < abs(wy) * drag:
                    dy = 1 if wy > 0 else -1
                    ny = y + dy
                    if self._empty_at(x, ny):
                        self._swap(x, y, x, ny)
                    elif self._in_sim(x, ny) and self.grid[ny][x] != EMPTY:
                        nm = self.grid[ny][x]
                        if self._density(nm) < self._density(cur_mat) and self._behavior(nm) not in ('solid', 'fuse'):
                            self._swap(x, y, x, ny)

    def _conduct_temp(self):
        """Spread temperature via conduction; heat sources emit."""
        new_temp = [row[:] for row in self.temp]

        for y in range(SIM_TOP, H):
            for x in range(W):
                mat = self.grid[y][x]
                emit, cond = THERMAL.get(mat, (None, 0.3))
                t = self.temp[y][x]

                # Heat sources drive toward emit_temp
                if emit is not None:
                    t += (emit - t) * 0.3

                # Average with neighbors weighted by conductivity
                n_sum = 0.0
                c_sum = 0.0
                for dx, dy in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                    nx, ny = x + dx, y + dy
                    if self._in_sim(nx, ny):
                        nm = self.grid[ny][nx]
                        _, nc = THERMAL.get(nm, (None, 0.3))
                        n_sum += self.temp[ny][nx] * nc
                        c_sum += nc

                if c_sum > 0:
                    avg = n_sum / c_sum
                    t += (avg - t) * 0.15

                # Empty cells cool toward ambient
                if mat == EMPTY:
                    t += (20.0 - t) * 0.05

                new_temp[y][x] = max(-50.0, min(800.0, t))

        self.temp = new_temp

    def _check_phase_trans(self):
        """Check temperature-based phase transitions."""
        for y in range(SIM_TOP, H):
            for x in range(W):
                mat = self.grid[y][x]
                if mat == EMPTY:
                    continue
                t = self.temp[y][x]

                if mat == ICE and t > 5:
                    self._set_cell(x, y, WATER)
                elif mat == WATER and t < -5:
                    self._set_cell(x, y, ICE)
                elif mat == WATER and t > 105:
                    self._set_cell(x, y, STEAM)
                elif mat == STEAM and t < 60:
                    self._set_cell(x, y, WATER)
                elif mat == WOOD and t > 250:
                    self._set_cell(x, y, FIRE)
                elif mat == OIL and t > 180:
                    self._set_cell(x, y, FIRE)
                elif mat == GAS and t > 120:
                    self._set_cell(x, y, FIRE)
                elif mat == GUNPOWDER and t > 200:
                    self._explode(x, y, 5)
                elif mat == NITRO and t > 100:
                    self._explode(x, y, 7)
                elif mat == PLANT and t > 220:
                    self._set_cell(x, y, FIRE)
                elif mat == VINE and t > 180:
                    self._set_cell(x, y, FIRE)
                elif mat == FUSE and self.life[y][x] == 0 and t > 200:
                    self.life[y][x] = random.randint(8, 15)
                elif mat == SAND and t > 700:
                    self._set_cell(x, y, LAVA)

    def _simulate(self):
        """Run one frame of physics simulation."""
        for y in range(H):
            for x in range(W):
                self.updated[y][x] = False

        # Wind pipeline: generate → propagate → apply
        self._generate_wind()
        self._propagate_wind()
        self._apply_wind()

        # Temperature: conduct heat, then check phase transitions
        self._conduct_temp()
        self._check_phase_trans()

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

                # Probabilistic movement — slower relative speed on small grid
                # Powder/liquid skip ~40% of frames, gas ~30%
                if behav == 'powder':
                    if random.random() < 0.6:
                        self._update_powder(x, y)
                elif behav == 'liquid':
                    if random.random() < 0.6:
                        self._update_liquid(x, y)
                elif mat == FIRE:
                    if random.random() < 0.7:
                        self._update_fire(x, y)
                elif mat == STEAM:
                    if random.random() < 0.7:
                        self._update_steam(x, y)
                elif mat == GAS:
                    if random.random() < 0.7:
                        self._update_gas_element(x, y)
                elif behav == 'grow':
                    self._update_plant(x, y)
                elif behav == 'vine':
                    self._update_vine(x, y)
                elif behav == 'fuse':
                    self._update_fuse(x, y)

                # Check interactions
                if self._in_sim(x, y) and self.grid[y][x] != EMPTY:
                    self._check_interactions(x, y)

        # Second pass: interactions for moved particles
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
                self.mode = MODE_SELECT if self.mode == MODE_PLAY else MODE_PLAY
            self.btn_hold_time = 0.0
            self.painting = False
        self.btn_was_held = btn_now

        self._simulate()

    def _update_play_mode(self, inp: InputState, dt: float):
        """Handle input in play mode."""
        self.move_timer += dt
        rate = 0.08
        if inp.any_direction:
            if inp.up_pressed or inp.down_pressed or inp.left_pressed or inp.right_pressed:
                self.move_timer = 0.0
                self.cx = clamp(self.cx + inp.dx, 0, W - 1)
                self.cy = clamp(self.cy + inp.dy, SIM_TOP, H - 1)
            elif self.move_timer >= rate:
                self.move_timer = 0.0
                self.cx = clamp(self.cx + inp.dx, 0, W - 1)
                self.cy = clamp(self.cy + inp.dy, SIM_TOP, H - 1)

        # Paint material with 2x2 brush while button held (overwrites)
        if self.painting:
            for dy in range(2):
                for dx in range(2):
                    bx, by = self.cx + dx, self.cy + dy
                    if self._in_sim(bx, by):
                        if self.selected == ERASE:
                            self._set_cell(bx, by, EMPTY)
                        else:
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
                        flicker = random.randint(-10, 20)
                        c = (clamp(c[0] + flicker, 0, 255),
                             clamp(c[1] + flicker, 0, 255),
                             clamp(c[2], 0, 255))
                    elif mat == FUSE and self.life[y][x] > 0:
                        # Lit fuse glows orange-red
                        c = (255, clamp(80 + random.randint(-30, 30), 0, 255), 0)
                    elif mat == GAS:
                        # Gas shimmer
                        flicker = random.randint(-10, 10)
                        c = (clamp(c[0] + flicker, 0, 255),
                             clamp(c[1] + flicker, 0, 255),
                             clamp(c[2] + flicker, 0, 255))
                    elif mat == NITRO:
                        # Nitro pulses slightly
                        flicker = random.randint(-8, 8)
                        c = (clamp(c[0] + flicker, 0, 255),
                             clamp(c[1] + flicker, 0, 255),
                             clamp(c[2] + flicker, 0, 255))
                    # Temperature tinting
                    t = self.temp[y][x]
                    if t > 100:
                        heat = min((t - 100) / 300.0, 1.0)
                        c = (min(c[0] + int(heat * 80), 255),
                             max(c[1] - int(heat * 30), 0),
                             c[2])
                    elif t < 0:
                        cold = min(-t / 30.0, 1.0)
                        c = (max(c[0] - int(cold * 20), 0),
                             c[1],
                             min(c[2] + int(cold * 60), 255))
                    self.display.set_pixel(x, y, c)

        # Draw cursor
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
        items_visible = 8
        total = len(MATERIALS) - 1  # skip EMPTY
        sel_idx = self.selected - 1
        scroll = max(0, min(sel_idx - items_visible // 2, total - items_visible))

        y = 2
        for i in range(scroll, min(scroll + items_visible, total)):
            mat_id = i + 1
            name = MATERIALS[mat_id][0]
            color = MATERIALS[mat_id][1]
            if mat_id == self.selected:
                self.display.draw_text_small(2, y, ">", (255, 255, 255))
                self.display.draw_text_small(6, y, name, color)
            else:
                self.display.draw_text_small(6, y, name, (color[0] // 2, color[1] // 2, color[2] // 2))
            y += 7

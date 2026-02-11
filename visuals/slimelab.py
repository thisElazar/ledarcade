"""
Slime Lab - Colony Competition Parameter Explorer
==================================================
Explore the growth_chance x attack_power parameter space of the
Slime Mold competing colonies simulation with joystick controls.

Controls:
  Left/Right - Adjust growth chance (frontier expansion rate)
  Up/Down    - Adjust attack power (border takeover rate)
  Button     - Reseed colonies
  Both       - Commit params to settings
"""

import random
import math
from . import Visual, Display, GRID_SIZE
import settings

COLONY_COLORS = [
    (255, 50, 50),    # Red
    (50, 255, 50),    # Green
    (50, 100, 255),   # Blue
    (255, 255, 50),   # Yellow
    (255, 50, 255),   # Magenta
    (50, 255, 255),   # Cyan
]

# Named regions in growth_chance x attack_power space
_REGIONS = [
    ('COLD WAR',    0.05, 0.10, 0.02, 0.06),
    ('CREEPING',    0.05, 0.12, 0.10, 0.20),
    ('BALANCED',    0.12, 0.22, 0.08, 0.15),
    ('BLITZ',       0.25, 0.40, 0.02, 0.08),
    ('TOTAL WAR',   0.25, 0.40, 0.15, 0.30),
    ('EROSION',     0.05, 0.12, 0.20, 0.30),
]


def _nearest_region(growth, attack):
    for name, g_lo, g_hi, a_lo, a_hi in _REGIONS:
        if g_lo <= growth <= g_hi and a_lo <= attack <= a_hi:
            return name
    return ''


class SlimeLab(Visual):
    name = "SLIME LAB"
    description = "Explore Slime parameter space"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0

        self.growth_chance = settings.get('slime_lab_growth', 0.15)
        self.attack_power = settings.get('slime_lab_attack', 0.10)

        self.num_colonies = 6

        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.strength = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.age = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]

        self.colony_base_power = {}
        for i in range(1, self.num_colonies + 1):
            self.colony_base_power[i] = random.uniform(0.95, 1.05)

        self._cached_counts = {}
        self._cached_total = 0

        self._spawn_colonies()

        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _spawn_colonies(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = 0
                self.strength[y][x] = 0.0
                self.age[y][x] = 0

        for colony_id in range(1, self.num_colonies + 1):
            for _ in range(50):
                cx = random.randint(8, GRID_SIZE - 8)
                cy = random.randint(8, GRID_SIZE - 8)
                too_close = False
                for y in range(GRID_SIZE):
                    for x in range(GRID_SIZE):
                        if self.grid[y][x] > 0:
                            dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                            if dist < 15:
                                too_close = True
                                break
                    if too_close:
                        break
                if not too_close:
                    break
            for dy in range(-1, 2):
                for dx in range(-1, 2):
                    nx, ny = cx + dx, cy + dy
                    if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                        if random.random() < 0.7:
                            self.grid[ny][nx] = colony_id
                            self.strength[ny][nx] = 1.0
                            self.age[ny][nx] = 0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.growth_chance = max(0.02, round(self.growth_chance - 0.02, 2))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.growth_chance = min(0.40, round(self.growth_chance + 0.02, 2))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.attack_power = min(0.30, round(self.attack_power + 0.02, 2))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.attack_power = max(0.02, round(self.attack_power - 0.02, 2))
            self.param_overlay_timer = 2.0
            consumed = True
        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('slime_lab_growth', round(self.growth_chance, 2))
                settings.set('slime_lab_attack', round(self.attack_power, 2))
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l or input_state.action_r:
                self._spawn_colonies()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def _get_colony_counts(self):
        counts = {}
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                c = self.grid[y][x]
                if c > 0:
                    counts[c] = counts.get(c, 0) + 1
        return counts

    def _get_colony_power(self, colony_id):
        total_cells = self._cached_total
        if total_cells == 0:
            return 1.0
        my_cells = self._cached_counts.get(colony_id, 0)
        base = self.colony_base_power.get(colony_id, 1.0)
        if my_cells == 0:
            return base
        share = my_cells / total_cells
        if share < 0.10:
            modifier = 1.0 + (0.10 - share) * 3
        elif share > 0.40:
            modifier = 1.0 + (share - 0.40) * 0.5
        else:
            modifier = 1.0
        return base * modifier

    def _count_neighbors(self, x, y):
        counts = {}
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                    colony = self.grid[ny][nx]
                    if colony > 0:
                        s = self.strength[ny][nx]
                        counts[colony] = counts.get(colony, 0) + s
        return counts

    def _growth_step(self):
        frontier = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] == 0:
                    neighbors = self._count_neighbors(x, y)
                    if neighbors:
                        frontier.append((x, y, neighbors))
        random.shuffle(frontier)
        for x, y, neighbors in frontier:
            if random.random() > self.growth_chance:
                continue
            winner = max(neighbors, key=neighbors.get)
            strength = neighbors[winner] * self._get_colony_power(winner)
            same_count = sum(1 for dy in (-1, 0, 1) for dx in (-1, 0, 1)
                             if (dx != 0 or dy != 0) and
                             0 <= x + dx < GRID_SIZE and
                             0 <= y + dy < GRID_SIZE and
                             self.grid[y + dy][x + dx] == winner)
            if same_count > 3 and random.random() > 0.3:
                continue
            self.grid[y][x] = winner
            self.strength[y][x] = min(1.0, strength * 0.3)
            self.age[y][x] = 0

    def _competition_step(self):
        attacks = []
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                colony = self.grid[y][x]
                if colony == 0:
                    continue
                my_strength = self.strength[y][x] * self._get_colony_power(colony)
                neighbors = self._count_neighbors(x, y)
                for enemy, enemy_strength in neighbors.items():
                    if enemy != colony:
                        enemy_power = enemy_strength * self._get_colony_power(enemy)
                        if enemy_power > my_strength * 1.2:
                            attacks.append((x, y, colony, enemy, enemy_power - my_strength))
        for x, y, old_colony, new_colony, advantage in attacks:
            if random.random() < advantage * self.attack_power:
                self.grid[y][x] = new_colony
                self.strength[y][x] = 0.5
                self.age[y][x] = 0

        new_strength = [[0.0] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                colony = self.grid[y][x]
                if colony == 0:
                    continue
                neighbors = self._count_neighbors(x, y)
                same = neighbors.get(colony, 0)
                enemies = sum(s for c, s in neighbors.items() if c != colony)
                cell_age = self.age[y][x]
                if enemies > 0:
                    new_strength[y][x] = max(0.1, self.strength[y][x] - 0.02)
                elif same > 3:
                    new_strength[y][x] = min(1.0, self.strength[y][x] + 0.01)
                else:
                    new_strength[y][x] = self.strength[y][x]
                if cell_age > 10:
                    decay = (cell_age - 10) * 0.003
                    new_strength[y][x] = max(0.1, new_strength[y][x] - decay)
                if enemies > 0 and self.strength[y][x] > 0.8:
                    if random.random() < 0.01:
                        new_strength[y][x] = 0.3
                if new_strength[y][x] < 0.05:
                    self.grid[y][x] = 0
                    new_strength[y][x] = 0
                    self.age[y][x] = 0
        self.strength = new_strength

    def update(self, dt: float):
        self.time += dt
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] > 0:
                    self.age[y][x] += dt

        self.step_timer += dt
        if self.step_timer >= 0.08:
            self.step_timer = 0
            self._cached_counts = self._get_colony_counts()
            self._cached_total = sum(self._cached_counts.values())
            self._growth_step()
            self._competition_step()

        # Reset if one colony completely fills
        total_area = GRID_SIZE * GRID_SIZE
        for count in self._cached_counts.values():
            if count >= total_area:
                if random.random() < 0.02:
                    self._spawn_colonies()
                break

        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

    def draw(self):
        self.display.clear((0, 0, 0))
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                colony = self.grid[y][x]
                if colony > 0:
                    base = COLONY_COLORS[(colony - 1) % len(COLONY_COLORS)]
                    s = self.strength[y][x]
                    brightness = 0.3 + 0.7 * s
                    self.display.set_pixel(x, y, (
                        int(base[0] * brightness),
                        int(base[1] * brightness),
                        int(base[2] * brightness),
                    ))

        if self.param_overlay_timer > 0:
            alpha = min(1.0, self.param_overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            region = _nearest_region(self.growth_chance, self.attack_power)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "grow=%.2f" % self.growth_chance, c)
                self.display.draw_text_small(2, 14, "atk=%.2f" % self.attack_power, c)
            else:
                self.display.draw_text_small(2, 2, "grow=%.2f" % self.growth_chance, c)
                self.display.draw_text_small(2, 8, "atk=%.2f" % self.attack_power, c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVED", c)

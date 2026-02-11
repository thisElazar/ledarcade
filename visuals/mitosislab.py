"""
Mitosis Lab - Cell Colony Parameter Explorer
=============================================
Explore the growth_rate x competition_strength parameter space
of the Mitosis cell division simulation with joystick controls.

Controls:
  Left/Right - Adjust growth rate
  Up/Down    - Adjust competition strength
  Button     - Cycle palette + reseed
  Both       - Commit params to settings
"""

import random
import math
from . import Visual, Display, GRID_SIZE
import settings

# Named regions in growth_rate x competition_strength space
_REGIONS = [
    ('GENTLE',     0.3, 0.8,  0.1, 0.3),
    ('BALANCED',   1.0, 1.6,  0.3, 0.7),
    ('BLOOMING',   2.0, 3.0,  0.1, 0.4),
    ('AGGRESSIVE', 1.8, 3.0,  1.0, 2.0),
    ('STARVED',    0.3, 0.8,  1.0, 2.0),
    ('FRENZY',     2.0, 3.0,  0.5, 1.0),
]


def _nearest_region(growth, comp):
    for name, g_lo, g_hi, c_lo, c_hi in _REGIONS:
        if g_lo <= growth <= g_hi and c_lo <= comp <= c_hi:
            return name
    return ''


class _Colony:
    __slots__ = ('x', 'y', 'radius', 'energy', 'age', 'generation',
                 'growth_rate', 'hue_offset', 'alive')

    def __init__(self, x, y, radius=2.0, energy=1.0, generation=0):
        self.x = x
        self.y = y
        self.radius = radius
        self.energy = energy
        self.age = 0.0
        self.generation = generation
        self.growth_rate = random.uniform(0.8, 1.2)
        self.hue_offset = random.uniform(-0.1, 0.1)
        self.alive = True

    def area(self):
        return math.pi * self.radius * self.radius


class MitosisLab(Visual):
    name = "MITOSIS LAB"
    description = "Explore Mitosis parameter space"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0

        self.base_growth_rate = settings.get('mitosis_lab_growth', 1.2)
        self.competition_strength = settings.get('mitosis_lab_comp', 0.5)

        self.split_radius = 6.5
        self.min_radius = 2.0
        self.max_colonies = 40
        self.fade_rate = 0.35
        self.energy_from_area = 0.008

        self.palette_idx = settings.get('mitosis_lab_palette', 0)
        self.palettes = [
            # Classic green (biological)
            ((0, 0, 0), (20, 70, 30), (50, 140, 60), (100, 200, 100), (180, 255, 180)),
            # Electric blue
            ((0, 0, 0), (20, 40, 120), (50, 100, 200), (100, 160, 255), (200, 220, 255)),
            # Magenta pulse
            ((0, 0, 0), (80, 20, 100), (150, 50, 170), (200, 100, 220), (255, 180, 255)),
            # Fire bands
            ((0, 0, 0), (120, 30, 0), (200, 80, 0), (255, 160, 50), (255, 230, 150)),
            # Cyan glow
            ((0, 0, 0), (0, 80, 90), (30, 150, 160), (80, 210, 210), (180, 255, 255)),
            # Gold automata
            ((0, 0, 0), (90, 60, 10), (170, 120, 30), (230, 180, 60), (255, 230, 140)),
            # Radioactive
            ((0, 0, 0), (30, 90, 0), (80, 180, 0), (160, 230, 50), (220, 255, 150)),
            # Vaporwave
            ((0, 0, 0), (120, 40, 90), (200, 80, 150), (100, 180, 220), (220, 200, 255)),
        ]
        self.palette_idx = self.palette_idx % len(self.palettes)

        self.colonies = []
        self._seed_colonies()

        self.buffer = [[(0, 0, 0) for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]

        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _seed_colonies(self):
        self.colonies = []
        num_seeds = random.randint(3, 6)
        for _ in range(num_seeds):
            x = random.uniform(12, GRID_SIZE - 12)
            y = random.uniform(12, GRID_SIZE - 12)
            radius = random.uniform(2.5, 3.5)
            self.colonies.append(_Colony(x, y, radius, energy=0.8))

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.base_growth_rate = max(0.3, round(self.base_growth_rate - 0.1, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.base_growth_rate = min(3.0, round(self.base_growth_rate + 0.1, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.competition_strength = min(2.0, round(self.competition_strength + 0.1, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.competition_strength = max(0.1, round(self.competition_strength - 0.1, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('mitosis_lab_growth', round(self.base_growth_rate, 1))
                settings.set('mitosis_lab_comp', round(self.competition_strength, 1))
                settings.set('mitosis_lab_palette', self.palette_idx)
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l or input_state.action_r:
                self.palette_idx = (self.palette_idx + 1) % len(self.palettes)
                self._seed_colonies()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def update(self, dt: float):
        self.time += dt

        for colony in self.colonies:
            if not colony.alive:
                continue
            colony.age += dt
            growth = self.base_growth_rate * colony.growth_rate * colony.energy * dt
            colony.radius += growth
            colony.energy += colony.area() * self.energy_from_area * dt
            colony.energy -= self.fade_rate * dt
            colony.energy = max(0.0, min(1.5, colony.energy))
            max_age = 15 - colony.generation * 2
            if colony.energy <= 0.1 or colony.age > max(5, max_age):
                colony.alive = False
                continue
            margin = colony.radius + 2
            if colony.x < margin:
                colony.x = margin
            elif colony.x > GRID_SIZE - margin:
                colony.x = GRID_SIZE - margin
            if colony.y < margin:
                colony.y = margin
            elif colony.y > GRID_SIZE - margin:
                colony.y = GRID_SIZE - margin

        # Mitosis
        new_colonies = []
        for colony in self.colonies:
            if colony.alive and colony.radius >= self.split_radius:
                if len(self.colonies) + len(new_colonies) < self.max_colonies:
                    angle = random.uniform(0, math.pi * 2)
                    offset = colony.radius * 0.4
                    new_radius = colony.radius * 0.6
                    colony.x += math.cos(angle) * offset
                    colony.y += math.sin(angle) * offset
                    colony.radius = new_radius
                    colony.energy *= 0.4
                    colony.age = 0
                    colony.generation += 1
                    daughter = _Colony(
                        colony.x - math.cos(angle) * offset * 2,
                        colony.y - math.sin(angle) * offset * 2,
                        new_radius,
                        energy=colony.energy,
                        generation=colony.generation,
                    )
                    daughter.age = 0
                    daughter.hue_offset = colony.hue_offset + random.uniform(-0.05, 0.05)
                    new_colonies.append(daughter)
        self.colonies.extend(new_colonies)

        # Competition
        for i, c1 in enumerate(self.colonies):
            if not c1.alive:
                continue
            for c2 in self.colonies[i + 1:]:
                if not c2.alive:
                    continue
                dx = c2.x - c1.x
                dy = c2.y - c1.y
                dist = math.sqrt(dx * dx + dy * dy)
                overlap = (c1.radius + c2.radius) - dist
                if overlap > 0:
                    if dist > 0.1:
                        push = overlap * 0.3
                        nx, ny = dx / dist, dy / dist
                        c1.x -= nx * push * 0.5
                        c1.y -= ny * push * 0.5
                        c2.x += nx * push * 0.5
                        c2.y += ny * push * 0.5
                    if c1.area() > c2.area():
                        transfer = self.competition_strength * dt
                        c2.energy -= transfer
                        c1.energy += transfer * 0.5
                    else:
                        transfer = self.competition_strength * dt
                        c1.energy -= transfer
                        c2.energy += transfer * 0.5

        self.colonies = [c for c in self.colonies if c.alive]

        if len(self.colonies) < 3 and random.random() < 0.02:
            x = random.uniform(10, GRID_SIZE - 10)
            y = random.uniform(10, GRID_SIZE - 10)
            if len(self.colonies) < self.max_colonies:
                self.colonies.append(_Colony(x, y, radius=2.5, energy=1.0))

        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

    def draw(self):
        palette = self.palettes[self.palette_idx]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.buffer[y][x] = (0, 0, 0)

        for colony in self.colonies:
            if not colony.alive:
                continue
            r = int(colony.radius) + 3
            x0 = max(0, int(colony.x) - r)
            x1 = min(GRID_SIZE, int(colony.x) + r + 1)
            y0 = max(0, int(colony.y) - r)
            y1 = min(GRID_SIZE, int(colony.y) + r + 1)
            for py in range(y0, y1):
                for px in range(x0, x1):
                    dx = px - colony.x
                    dy = py - colony.y
                    dist = math.sqrt(dx * dx + dy * dy)
                    if dist < colony.radius + 1:
                        if dist < colony.radius - 1:
                            intensity = 1.0
                        else:
                            intensity = max(0, colony.radius + 1 - dist) / 2
                        intensity *= 0.5 + colony.energy * 0.5
                        intensity = max(0, min(1, intensity))
                        idx = intensity * (len(palette) - 1)
                        idx_low = int(idx)
                        idx_high = min(len(palette) - 1, idx_low + 1)
                        t = idx - idx_low
                        c_low = palette[idx_low]
                        c_high = palette[idx_high]
                        color = (
                            int(c_low[0] + (c_high[0] - c_low[0]) * t),
                            int(c_low[1] + (c_high[1] - c_low[1]) * t),
                            int(c_low[2] + (c_high[2] - c_low[2]) * t),
                        )
                        existing = self.buffer[py][px]
                        self.buffer[py][px] = (
                            max(existing[0], color[0]),
                            max(existing[1], color[1]),
                            max(existing[2], color[2]),
                        )

        sp = self.display.set_pixel
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                sp(x, y, self.buffer[y][x])

        if self.param_overlay_timer > 0:
            alpha = min(1.0, self.param_overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            region = _nearest_region(self.base_growth_rate, self.competition_strength)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "grow=%.1f" % self.base_growth_rate, c)
                self.display.draw_text_small(2, 14, "comp=%.1f" % self.competition_strength, c)
            else:
                self.display.draw_text_small(2, 2, "grow=%.1f" % self.base_growth_rate, c)
                self.display.draw_text_small(2, 8, "comp=%.1f" % self.competition_strength, c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVED", c)

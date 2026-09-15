"""
Jellyfish Lab - Particle Life Rule Explorer
============================================
Cycle named attraction-matrix presets and species counts to
explore the emergent regimes of Particle Life.

Controls:
  Left/Right - Cycle preset rules
  Up/Down    - Adjust species count (3-6)
  Button     - Reseed particles (keep rules)
  Both       - Commit preset + species to settings
"""

import random
import math
from . import Visual, Display, GRID_SIZE
import settings

_SPECIES_COLORS = [
    (255, 50, 50),
    (50, 255, 80),
    (60, 120, 255),
    (255, 240, 40),
    (40, 240, 240),
    (240, 80, 240),
]

_PRESET_NAMES = [
    'RANDOM', 'ORBITS', 'SYMBIOSIS', 'PREDATOR',
    'FLOCKING', 'CHAOS', 'MOLECULES',
]


def _build_matrix(preset_idx, n):
    name = _PRESET_NAMES[preset_idx]
    m = [[0.0] * n for _ in range(n)]

    if name == 'RANDOM':
        for i in range(n):
            for j in range(n):
                m[i][j] = random.uniform(-1.0, 1.0)

    elif name == 'ORBITS':
        for i in range(n):
            m[i][i] = -0.2
            m[i][(i + 1) % n] = 0.8
            m[i][(i - 1) % n] = -0.5

    elif name == 'SYMBIOSIS':
        for i in range(n):
            for j in range(n):
                m[i][j] = -0.4
            m[i][i] = 0.3
        for k in range(0, n - 1, 2):
            m[k][k + 1] = 0.9
            m[k + 1][k] = 0.9
        if n % 2:
            m[n - 1][n - 1] = 0.7

    elif name == 'PREDATOR':
        for i in range(n):
            for j in range(n):
                m[i][j] = 0.3
            m[i][i] = 0.1
        for j in range(n):
            m[0][j] = -0.8
            m[j][0] = -0.6
        m[0][0] = 0.2

    elif name == 'FLOCKING':
        for i in range(n):
            for j in range(n):
                m[i][j] = 0.2
            m[i][i] = 0.7

    elif name == 'CHAOS':
        for i in range(n):
            for j in range(n):
                m[i][j] = random.choice([-0.9, 0.9])

    elif name == 'MOLECULES':
        for i in range(n):
            for j in range(n):
                m[i][j] = -0.7
            m[i][i] = 0.9

    return m


class _Particle:
    __slots__ = ('x', 'y', 'vx', 'vy', 'species')

    def __init__(self, x, y, species):
        self.x = x
        self.y = y
        self.vx = 0.0
        self.vy = 0.0
        self.species = species


_NUM_PARTICLES = 180
_INTERACTION_RADIUS = 18.0
_FRICTION = 0.95
_MIN_DISTANCE = 2.0
_FORCE_SCALE = 5.0
_MAX_SPEED = 3.0


class ParticleLifeLab(Visual):
    name = "JELLYFISH LAB"
    description = "Explore Jellyfish rules"
    category = "automata"
    GUIDE = {
        'desc': 'Explore Particle Life regimes. Cycle named attraction-matrix presets — orbits, symbiosis, flocking, chaos — and adjust species count to see how the same rules scale.',
        'credit': 'Jeffrey Ventrella, 2007',
    }

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.preset_idx = settings.get('plife_lab_preset', 0) % len(_PRESET_NAMES)
        self.num_species = settings.get('plife_lab_species', 4)
        self.num_species = max(3, min(6, self.num_species))

        self.attraction = _build_matrix(self.preset_idx, self.num_species)
        self._spawn()

        self.param_overlay_timer = 2.5
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _spawn(self):
        self.particles = []
        for i in range(_NUM_PARTICLES):
            sp = i % self.num_species
            self.particles.append(_Particle(
                random.uniform(0, GRID_SIZE),
                random.uniform(0, GRID_SIZE),
                sp,
            ))

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.left_pressed:
            self.preset_idx = (self.preset_idx - 1) % len(_PRESET_NAMES)
            self.attraction = _build_matrix(self.preset_idx, self.num_species)
            self._spawn()
            self.param_overlay_timer = 2.5
            consumed = True
        if input_state.right_pressed:
            self.preset_idx = (self.preset_idx + 1) % len(_PRESET_NAMES)
            self.attraction = _build_matrix(self.preset_idx, self.num_species)
            self._spawn()
            self.param_overlay_timer = 2.5
            consumed = True

        if input_state.up_pressed:
            if self.num_species < 6:
                self.num_species += 1
                self.attraction = _build_matrix(self.preset_idx, self.num_species)
                self._spawn()
                self.param_overlay_timer = 2.5
            consumed = True
        if input_state.down_pressed:
            if self.num_species > 3:
                self.num_species -= 1
                self.attraction = _build_matrix(self.preset_idx, self.num_species)
                self._spawn()
                self.param_overlay_timer = 2.5
            consumed = True

        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('plife_lab_preset', self.preset_idx)
                settings.set('plife_lab_species', self.num_species)
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l or input_state.action_r:
                self._spawn()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def update(self, dt: float):
        self.time += dt

        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

        particles = self.particles
        attraction = self.attraction
        radius = _INTERACTION_RADIUS
        radius_sq = radius * radius
        min_dist = _MIN_DISTANCE
        force_scale = _FORCE_SCALE
        grid = GRID_SIZE
        half_grid = grid * 0.5

        for p in particles:
            fx = 0.0
            fy = 0.0
            for q in particles:
                if p is q:
                    continue
                dx = q.x - p.x
                if dx > half_grid:
                    dx -= grid
                elif dx < -half_grid:
                    dx += grid
                dy = q.y - p.y
                if dy > half_grid:
                    dy -= grid
                elif dy < -half_grid:
                    dy += grid
                dist_sq = dx * dx + dy * dy
                if dist_sq > radius_sq or dist_sq < 0.01:
                    continue
                dist = math.sqrt(dist_sq)
                if dist < min_dist:
                    repel = (min_dist - dist) / min_dist
                    inv = 1.0 / dist
                    fx -= dx * inv * repel * force_scale
                    fy -= dy * inv * repel * force_scale
                else:
                    g = attraction[p.species][q.species]
                    norm = (dist - min_dist) / (radius - min_dist)
                    envelope = norm / 0.3 if norm < 0.3 else (1.0 - norm) / 0.7
                    mag = g * envelope * force_scale
                    inv = 1.0 / dist
                    fx += dx * inv * mag
                    fy += dy * inv * mag

            p.vx += fx * dt
            p.vy += fy * dt
            spd_sq = p.vx * p.vx + p.vy * p.vy
            if spd_sq > _MAX_SPEED * _MAX_SPEED:
                spd = math.sqrt(spd_sq)
                p.vx = p.vx / spd * _MAX_SPEED
                p.vy = p.vy / spd * _MAX_SPEED

        for p in particles:
            p.vx *= _FRICTION
            p.vy *= _FRICTION
            p.x = (p.x + p.vx) % grid
            p.y = (p.y + p.vy) % grid

    def draw(self):
        self.display.clear((0, 0, 0))
        colors = _SPECIES_COLORS
        sp = self.display.set_pixel

        for p in self.particles:
            px = int(p.x) % GRID_SIZE
            py = int(p.y) % GRID_SIZE
            sp(px, py, colors[p.species])
            spd_sq = p.vx * p.vx + p.vy * p.vy
            if spd_sq > 0.5:
                c = colors[p.species]
                glow = (c[0] // 3, c[1] // 3, c[2] // 3)
                tx = int(p.x - p.vx * 0.8) % GRID_SIZE
                ty = int(p.y - p.vy * 0.8) % GRID_SIZE
                sp(tx, ty, glow)

        if self.param_overlay_timer > 0:
            alpha = min(1.0, self.param_overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            self.display.draw_text_small(2, 2, _PRESET_NAMES[self.preset_idx], c)
            self.display.draw_text_small(2, 8, "%d SPECIES" % self.num_species, c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVED", c)

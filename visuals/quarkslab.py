"""
Quarks Lab - Quark CA Parameter Explorer
=========================================
Explore the num_quarks x move_radius parameter space of the
Quarks cellular automaton with joystick controls.

Controls:
  Left/Right - Adjust number of quarks (hotspots)
  Up/Down    - Adjust roam radius
  Button     - Cycle palette + reseed
  Both       - Commit params to settings
"""

import random
import math
from . import Visual, Display, GRID_SIZE
import settings

# Named regions in num_quarks x move_radius space
_REGIONS = [
    ('LONE MANDALA', 1,  2,   2, 10),
    ('ISLANDS',      2,  4,   4, 14),
    ('DRIFTERS',     3,  6,  15, 28),
    ('SWARM',        7, 12,   4, 14),
    ('CHAOS',        7, 12,  20, 40),
    ('ORBITING',     3,  5,  28, 40),
]


def _nearest_region(num_q, radius):
    for name, q_lo, q_hi, r_lo, r_hi in _REGIONS:
        if q_lo <= num_q <= q_hi and r_lo <= radius <= r_hi:
            return name
    return ''


class QuarksLab(Visual):
    name = "QUARKS LAB"
    description = "Explore Quarks parameter space"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.base_interval = 0.1
        self.min_interval = 0.05

        self.num_quarks = settings.get('quarks_lab_num', 5)
        self.move_radius = settings.get('quarks_lab_radius', 17)

        self.palette_idx = settings.get('quarks_lab_palette', 0)
        self._build_palettes()
        self.palette_idx = self.palette_idx % len(self.palettes)
        self.colors = self.palettes[self.palette_idx]

        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.prev_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.blend = 0.0
        self._init_pattern()

        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _build_palettes(self):
        self.palettes = [
            self._make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150),
                                 (100, 255, 100), (255, 255, 0), (255, 100, 0),
                                 (150, 0, 100)]),
            self._make_gradient([(150, 0, 100), (255, 100, 0), (255, 255, 0),
                                 (100, 255, 100), (0, 200, 150), (0, 100, 200),
                                 (20, 0, 80)]),
            self._make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150),
                                 (100, 200, 200), (200, 230, 255)]),
            self._make_gradient([(40, 0, 0), (150, 30, 0), (255, 100, 0),
                                 (255, 200, 50), (255, 255, 200)]),
            self._make_gradient([(0, 20, 0), (0, 80, 40), (50, 150, 50),
                                 (150, 220, 100), (220, 255, 180)]),
            self._make_gradient([(40, 0, 60), (100, 0, 150), (200, 50, 200),
                                 (255, 150, 220), (255, 220, 255)]),
            self._make_banded_rainbow(16),
            self._make_banded_rainbow(8),
            self._make_mono_bands((0, 100, 255), 10),
            self._make_mono_bands((255, 50, 50), 10),
        ]

    @staticmethod
    def _make_gradient(key_colors):
        gradient = []
        segments = len(key_colors) - 1
        per_segment = max(1, 256 // segments)
        for i in range(256):
            seg = min(i // per_segment, segments - 1)
            t = (i % per_segment) / per_segment
            c1 = key_colors[seg]
            c2 = key_colors[seg + 1]
            gradient.append((
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            ))
        return gradient

    @staticmethod
    def _make_banded_rainbow(num_bands):
        rainbow = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211),
        ]
        gradient = []
        for i in range(256):
            cycle_pos = (i * num_bands * len(rainbow)) / 256
            color_idx = int(cycle_pos) % len(rainbow)
            next_idx = (color_idx + 1) % len(rainbow)
            t = cycle_pos % 1.0
            c1 = rainbow[color_idx]
            c2 = rainbow[next_idx]
            gradient.append((
                int(c1[0] + (c2[0] - c1[0]) * t),
                int(c1[1] + (c2[1] - c1[1]) * t),
                int(c1[2] + (c2[2] - c1[2]) * t),
            ))
        return gradient

    @staticmethod
    def _make_mono_bands(base_color, num_bands):
        gradient = []
        for i in range(256):
            band_pos = (i * num_bands * 2) / 256
            brightness = (math.sin(band_pos * math.pi) + 1) / 2
            gradient.append((
                int(base_color[0] * brightness),
                int(base_color[1] * brightness),
                int(base_color[2] * brightness),
            ))
        return gradient

    def _init_pattern(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = random.randint(0, 255)
                self.prev_grid[y][x] = self.grid[y][x]

        self.seeds = []
        for _ in range(self.num_quarks):
            shape = random.choice(['pinwheel', 'pinwheel', 'donut'])
            seed = {
                'base_x': random.uniform(0, GRID_SIZE),
                'base_y': random.uniform(0, GRID_SIZE),
                'phase': random.uniform(0, math.pi * 2),
                'freq': random.uniform(0.8, 1.5),
                'shape': shape,
                'move_radius': self.move_radius,
                'move_speed_x': random.uniform(0.15, 0.35) * random.choice([-1, 1]),
                'move_speed_y': random.uniform(0.15, 0.35) * random.choice([-1, 1]),
                'move_phase_x': random.uniform(0, math.pi * 2),
                'move_phase_y': random.uniform(0, math.pi * 2),
                'rot_speed': random.uniform(0.4, 1.0) * random.choice([-1, 1]),
                'rot_phase': random.uniform(0, math.pi * 2),
            }
            if shape == 'pinwheel':
                seed['arm_length'] = random.randint(2, 3)
                seed['num_arms'] = random.choice([3, 4])
            else:
                seed['inner_radius'] = 1
                seed['outer_radius'] = 2
            self.seeds.append(seed)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.num_quarks = max(1, self.num_quarks - 1)
            self._init_pattern()
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.num_quarks = min(12, self.num_quarks + 1)
            self._init_pattern()
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.move_radius = min(40, self.move_radius + 2)
            for s in self.seeds:
                s['move_radius'] = self.move_radius
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.move_radius = max(2, self.move_radius - 2)
            for s in self.seeds:
                s['move_radius'] = self.move_radius
            self.param_overlay_timer = 2.0
            consumed = True
        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('quarks_lab_num', self.num_quarks)
                settings.set('quarks_lab_radius', self.move_radius)
                settings.set('quarks_lab_palette', self.palette_idx)
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l or input_state.action_r:
                self.palette_idx = (self.palette_idx + 1) % len(self.palettes)
                self.colors = self.palettes[self.palette_idx]
                self._init_pattern()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt
        if self.update_timer >= self.base_interval:
            self.update_timer = 0.0
            self._step_ca()
        self.blend = min(1.0, self.update_timer / self.base_interval)
        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

    def _step_ca(self):
        grid = self.grid
        nxt = self.next_grid
        prev = self.prev_grid

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                prev[y][x] = grid[y][x]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                total = 0
                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        total += grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE]
                nxt[y][x] = (total // 8 + 1) % 256

        self.grid, self.next_grid = self.next_grid, self.grid

        # Inject energy from quarks
        for seed in self.seeds:
            r = seed['move_radius']
            move_x = math.sin(self.time * seed['move_speed_x'] + seed['move_phase_x']) * r
            move_y = math.sin(self.time * seed['move_speed_y'] + seed['move_phase_y']) * r
            cx = int(seed['base_x'] + move_x) % GRID_SIZE
            cy = int(seed['base_y'] + move_y) % GRID_SIZE
            val = int(128 + 127 * math.sin(self.time * seed['freq'] + seed['phase']))
            angle = self.time * seed['rot_speed'] + seed['rot_phase']

            if seed['shape'] == 'pinwheel':
                num_arms = seed['num_arms']
                arm_length = seed['arm_length']
                for arm in range(num_arms):
                    arm_angle = angle + (arm * 2 * math.pi / num_arms)
                    for dist in range(arm_length + 1):
                        px = int(cx + math.cos(arm_angle) * dist) % GRID_SIZE
                        py = int(cy + math.sin(arm_angle) * dist) % GRID_SIZE
                        self.grid[py][px] = val
            else:
                num_points = 12
                for i in range(num_points):
                    point_angle = angle + (i * 2 * math.pi / num_points)
                    rad = (seed['inner_radius'] + seed['outer_radius']) / 2
                    px = int(cx + math.cos(point_angle) * rad) % GRID_SIZE
                    py = int(cy + math.sin(point_angle) * rad) % GRID_SIZE
                    self.grid[py][px] = val

    def draw(self):
        colors = self.colors
        grid = self.grid
        prev = self.prev_grid
        t = self.blend
        sp = self.display.set_pixel

        for y in range(GRID_SIZE):
            row = grid[y]
            prev_row = prev[y]
            for x in range(GRID_SIZE):
                cc = colors[row[x]]
                pc = colors[prev_row[x]]
                if pc == cc:
                    sp(x, y, cc)
                else:
                    sp(x, y, (
                        int(pc[0] + (cc[0] - pc[0]) * t),
                        int(pc[1] + (cc[1] - pc[1]) * t),
                        int(pc[2] + (cc[2] - pc[2]) * t),
                    ))

        if self.param_overlay_timer > 0:
            alpha = min(1.0, self.param_overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            region = _nearest_region(self.num_quarks, self.move_radius)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "q=%d r=%d" % (self.num_quarks, self.move_radius), c)
            else:
                self.display.draw_text_small(2, 2, "q=%d r=%d" % (self.num_quarks, self.move_radius), c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVED", c)

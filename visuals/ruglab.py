"""
Rug Lab - Averaging CA Parameter Explorer
==========================================
Explore the increment x num_states parameter space of the Rug
cellular automaton with joystick controls.

Controls:
  Left/Right - Adjust increment (the +N in the rug rule)
  Up/Down    - Adjust num_states (mod value)
  Button     - Cycle palette + reseed
  Both       - Commit params to settings
"""

import random
import math
from . import Visual, Display, GRID_SIZE
import settings

# Named regions
_REGIONS = [
    ('CLASSIC',     1,  1,  256, 256),
    ('BOLD BANDS',  1,  1,   16,  48),
    ('FAST CYCLE',  2,  4,  128, 256),
    ('FINE CARPET', 1,  1,   64, 128),
    ('PSYCHEDELIC', 5,  8,   64, 128),
    ('STATIC',      9, 12,   16,  32),
]


def _nearest_region(inc, states):
    for name, i_lo, i_hi, s_lo, s_hi in _REGIONS:
        if i_lo <= inc <= i_hi and s_lo <= states <= s_hi:
            return name
    return ''


class RugLab(Visual):
    name = "RUG LAB"
    description = "Explore Rug CA parameter space"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.base_interval = 0.08
        self.min_interval = 0.05

        self.increment = settings.get('rug_lab_inc', 1)
        self.num_states = settings.get('rug_lab_states', 256)

        self.palette_idx = settings.get('rug_lab_palette', 0)
        self._build_palettes()
        self.palette_idx = self.palette_idx % len(self.palettes)
        self.colors = self.palettes[self.palette_idx]

        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.prev_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.blend = 0.0
        self.edge_val = random.randint(50, 200)
        self._init_pattern()

        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _build_palettes(self):
        self.palettes = [
            self._make_banded_rainbow(16),
            self._make_banded_rainbow(8),
            self._make_mono_bands((0, 100, 255), 10),
            self._make_mono_bands((255, 50, 50), 10),
            self._make_mono_bands((50, 255, 100), 10),
            self._make_mono_bands((255, 200, 50), 10),
            self._make_mono_bands((200, 100, 255), 10),
            self._make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150),
                                 (100, 255, 100), (255, 255, 0), (255, 100, 0),
                                 (150, 0, 100)]),
            self._make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150),
                                 (100, 200, 200), (200, 230, 255)]),
        ]

    def _make_gradient(self, key_colors):
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

    def _make_banded_rainbow(self, num_bands):
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

    def _make_mono_bands(self, base_color, num_bands):
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
                self.grid[y][x] = 0
                self.prev_grid[y][x] = 0
        self.edge_val = random.randint(50, 200)
        for i in range(GRID_SIZE):
            self.grid[0][i] = self.edge_val
            self.grid[GRID_SIZE - 1][i] = self.edge_val
            self.grid[i][0] = self.edge_val
            self.grid[i][GRID_SIZE - 1] = self.edge_val

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.increment = max(1, self.increment - 1)
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.increment = min(12, self.increment + 1)
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.num_states = min(256, self.num_states + 8)
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.num_states = max(16, self.num_states - 8)
            self._clamp_grid()
            self.param_overlay_timer = 2.0
            consumed = True
        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('rug_lab_inc', self.increment)
                settings.set('rug_lab_states', self.num_states)
                settings.set('rug_lab_palette', self.palette_idx)
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

    def _clamp_grid(self):
        ns = self.num_states
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] >= ns:
                    self.grid[y][x] = self.grid[y][x] % ns

    def _get_cell(self, x, y):
        if x < 0 or x >= GRID_SIZE or y < 0 or y >= GRID_SIZE:
            return self.edge_val
        return self.grid[y][x]

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
        inc = self.increment
        ns = self.num_states
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.prev_grid[y][x] = self.grid[y][x]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                total = 0
                total += self._get_cell(x - 1, y - 1)
                total += self._get_cell(x,     y - 1)
                total += self._get_cell(x + 1, y - 1)
                total += self._get_cell(x - 1, y)
                total += self._get_cell(x + 1, y)
                total += self._get_cell(x - 1, y + 1)
                total += self._get_cell(x,     y + 1)
                total += self._get_cell(x + 1, y + 1)
                self.next_grid[y][x] = (total // 8 + inc) % ns

        self.grid, self.next_grid = self.next_grid, self.grid

        if random.random() < 0.02:
            self.edge_val = (self.edge_val + random.choice([-1, 1])) % ns

    def draw(self):
        colors = self.colors
        grid = self.grid
        prev = self.prev_grid
        ns = self.num_states
        t = self.blend
        sp = self.display.set_pixel

        for y in range(GRID_SIZE):
            row = grid[y]
            prev_row = prev[y]
            for x in range(GRID_SIZE):
                ci = row[x] * 255 // max(1, ns - 1)
                pi = prev_row[x] * 255 // max(1, ns - 1)
                cc = colors[min(ci, 255)]
                pc = colors[min(pi, 255)]
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
            region = _nearest_region(self.increment, self.num_states)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "inc=%d" % self.increment, c)
                self.display.draw_text_small(2, 14, "states=%d" % self.num_states, c)
            else:
                self.display.draw_text_small(2, 2, "inc=%d" % self.increment, c)
                self.display.draw_text_small(2, 8, "states=%d" % self.num_states, c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVED", c)

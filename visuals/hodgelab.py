"""
Hodge Lab - Hodgepodge Machine Parameter Explorer
==================================================
Explore the g (growth) x n (max states) parameter space of the
Hodgepodge Machine with joystick controls.

Controls:
  Left/Right - Adjust g (infection growth constant)
  Up/Down    - Adjust n (max states / ill state)
  Button     - Cycle palette + reseed
  Both       - Commit params to settings
"""

import random
import math
from . import Visual, Display, GRID_SIZE
import settings

# Named regions in g x n space
_REGIONS = [
    ('SLOW PULSES',   1.0,  3.0,   8,  32),
    ('BZ CLASSIC',    4.0,  7.0,  48,  80),
    ('TIGHT SPIRALS', 8.0, 12.0,  48,  80),
    ('TURBULENCE',   13.0, 20.0,   8, 128),
    ('SUBTLE WAVES',  2.0,  4.0,  80, 128),
    ('BOLD BANDS',    4.0,  8.0,   8,  24),
]


def _nearest_region(g, n):
    for name, g_lo, g_hi, n_lo, n_hi in _REGIONS:
        if g_lo <= g <= g_hi and n_lo <= n <= n_hi:
            return name
    return ''


class HodgeLab(Visual):
    name = "HODGE LAB"
    description = "Explore Hodgepodge parameter space"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.base_interval = 0.1
        self.min_interval = 0.05

        self.g = settings.get('hodge_lab_g', 5.0)
        self.n = settings.get('hodge_lab_n', 63)
        self.k1 = 2
        self.k2 = 3

        self.palette_idx = settings.get('hodge_lab_palette', 0)
        self._build_palettes()
        self.palette_idx = self.palette_idx % len(self.palettes)
        self.colors = self.palettes[self.palette_idx]

        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._randomize()

        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _build_palettes(self):
        n = self.n
        self.palettes = [
            self._make_gradient([(20, 0, 80), (0, 100, 200), (0, 200, 150),
                                 (100, 255, 100), (255, 255, 0), (255, 100, 0),
                                 (150, 0, 100)], n),
            self._make_gradient([(150, 0, 100), (255, 100, 0), (255, 255, 0),
                                 (100, 255, 100), (0, 200, 150), (0, 100, 200),
                                 (20, 0, 80)], n),
            self._make_gradient([(0, 0, 40), (0, 50, 100), (0, 150, 150),
                                 (100, 200, 200), (200, 230, 255)], n),
            self._make_gradient([(40, 0, 0), (150, 30, 0), (255, 100, 0),
                                 (255, 200, 50), (255, 255, 200)], n),
            self._make_gradient([(0, 20, 0), (0, 80, 40), (50, 150, 50),
                                 (150, 220, 100), (220, 255, 180)], n),
            self._make_gradient([(40, 0, 60), (100, 0, 150), (200, 50, 200),
                                 (255, 150, 220), (255, 220, 255)], n),
            self._make_banded_rainbow(8, n),
            self._make_banded_rainbow(4, n),
        ]

    @staticmethod
    def _make_gradient(key_colors, n):
        num_colors = n + 1
        segments = len(key_colors) - 1
        per_segment = max(1, num_colors // segments)
        gradient = []
        for i in range(num_colors):
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
    def _make_banded_rainbow(num_bands, n):
        rainbow = [
            (255, 0, 0), (255, 127, 0), (255, 255, 0),
            (0, 255, 0), (0, 0, 255), (75, 0, 130), (148, 0, 211),
        ]
        num_colors = n + 1
        gradient = []
        for i in range(num_colors):
            cycle_pos = (i * num_bands * len(rainbow)) / num_colors
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

    def _randomize(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if random.random() < 0.2:
                    self.grid[y][x] = random.randint(1, self.n)
                else:
                    self.grid[y][x] = 0

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.g = max(1.0, round(self.g - 0.5, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.g = min(20.0, round(self.g + 0.5, 1))
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.n = min(128, self.n + 4)
            self._build_palettes()
            self.palette_idx = self.palette_idx % len(self.palettes)
            self.colors = self.palettes[self.palette_idx]
            self._clamp_grid()
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.n = max(8, self.n - 4)
            self._build_palettes()
            self.palette_idx = self.palette_idx % len(self.palettes)
            self.colors = self.palettes[self.palette_idx]
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
                settings.set('hodge_lab_g', round(self.g, 1))
                settings.set('hodge_lab_n', self.n)
                settings.set('hodge_lab_palette', self.palette_idx)
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
                self._randomize()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def _clamp_grid(self):
        n = self.n
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] > n:
                    self.grid[y][x] = n

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt
        if self.update_timer >= self.base_interval:
            self.update_timer = 0.0
            self._step_ca()
        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

    def _step_ca(self):
        n = self.n
        k1 = self.k1
        k2 = self.k2
        g = int(self.g)
        grid = self.grid
        nxt = self.next_grid

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = grid[y][x]
                infected = 0
                ill = 0
                total = state

                for dy in (-1, 0, 1):
                    for dx in (-1, 0, 1):
                        if dx == 0 and dy == 0:
                            continue
                        nb = grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE]
                        total += nb
                        if nb == n:
                            ill += 1
                        elif nb > 0:
                            infected += 1

                if state == 0:
                    new_state = (infected // k1) + (ill // k2)
                    nxt[y][x] = min(new_state, n)
                elif state == n:
                    nxt[y][x] = 0
                else:
                    avg = total // 9
                    nxt[y][x] = min(avg + g, n)

        self.grid, self.next_grid = self.next_grid, self.grid

        alive = any(self.grid[y][x] > 0
                     for y in range(GRID_SIZE) for x in range(GRID_SIZE))
        if not alive:
            self._randomize()

    def draw(self):
        colors = self.colors
        grid = self.grid
        sp = self.display.set_pixel
        for y in range(GRID_SIZE):
            row = grid[y]
            for x in range(GRID_SIZE):
                sp(x, y, colors[row[x]])

        if self.param_overlay_timer > 0:
            alpha = min(1.0, self.param_overlay_timer / 0.5)
            c = (int(255 * alpha), int(255 * alpha), int(255 * alpha))
            region = _nearest_region(self.g, self.n)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "g=%.1f n=%d" % (self.g, self.n), c)
            else:
                self.display.draw_text_small(2, 2, "g=%.1f n=%d" % (self.g, self.n), c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 14, "SAVED", c)

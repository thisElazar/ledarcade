"""
Cyclic Lab - Cyclic CA Parameter Explorer
==========================================
Explore the num_states x threshold parameter space of the
cyclic cellular automaton with joystick controls.

Controls:
  Left/Right - Adjust num_states (number of cyclic states)
  Up/Down    - Adjust threshold (neighbors needed to advance)
  Button     - Cycle palette + reseed
  Both       - Commit params to settings
"""

import random
from . import Visual, Display, GRID_SIZE
import settings

# Named regions
_REGIONS = [
    ('DEMONS',       10, 14, 1, 1),
    ('BOLD SPIRALS',  4,  6, 1, 1),
    ('FINE SPIRALS', 18, 24, 1, 1),
    ('DEFECTS',       8, 16, 2, 3),
    ('FROZEN',       16, 28, 4, 5),
    ('MINIMAL',       3,  4, 1, 1),
]

PALETTE_NAMES = ["rainbow", "fire", "ocean", "forest", "neon", "ice"]


def _nearest_region(states, threshold):
    for name, s_lo, s_hi, t_lo, t_hi in _REGIONS:
        if s_lo <= states <= s_hi and t_lo <= threshold <= t_hi:
            return name
    return ''


def _hue_to_rgb(hue):
    h = hue * 6.0
    sector = int(h) % 6
    frac = h - int(h)
    if sector == 0:
        return (255, int(255 * frac), 0)
    elif sector == 1:
        return (int(255 * (1.0 - frac)), 255, 0)
    elif sector == 2:
        return (0, 255, int(255 * frac))
    elif sector == 3:
        return (0, int(255 * (1.0 - frac)), 255)
    elif sector == 4:
        return (int(255 * frac), 0, 255)
    else:
        return (255, 0, int(255 * (1.0 - frac)))


def _build_color_table(n, palette_name):
    table = []
    for i in range(n):
        t = i / n
        if palette_name == "rainbow":
            table.append(_hue_to_rgb(t))
        elif palette_name == "fire":
            if t < 0.25:
                r, g, b = int(80 + 175 * (t / 0.25)), 0, 0
            elif t < 0.5:
                tt = (t - 0.25) / 0.25
                r, g, b = 255, int(140 * tt), 0
            elif t < 0.75:
                tt = (t - 0.5) / 0.25
                r, g, b = 255, int(140 + 115 * tt), int(50 * tt)
            else:
                tt = (t - 0.75) / 0.25
                r, g, b = 255, 255, int(50 + 205 * tt)
            table.append((r, g, b))
        elif palette_name == "ocean":
            if t < 0.33:
                tt = t / 0.33
                r, g, b = 0, int(40 * tt), int(80 + 175 * tt)
            elif t < 0.66:
                tt = (t - 0.33) / 0.33
                r, g, b = 0, int(40 + 215 * tt), 255
            else:
                tt = (t - 0.66) / 0.34
                r, g, b = int(100 * tt), 255, int(255 - 55 * tt)
            table.append((r, g, b))
        elif palette_name == "forest":
            if t < 0.33:
                tt = t / 0.33
                r, g, b = 0, int(60 + 130 * tt), int(20 * tt)
            elif t < 0.66:
                tt = (t - 0.33) / 0.33
                r, g, b = int(80 * tt), int(190 + 65 * tt), 0
            else:
                tt = (t - 0.66) / 0.34
                r, g, b = int(80 + 175 * tt), 255, int(50 * tt)
            table.append((r, g, b))
        elif palette_name == "neon":
            hue = (0.75 + t * 0.5) % 1.0
            table.append(_hue_to_rgb(hue))
        elif palette_name == "ice":
            if t < 0.33:
                tt = t / 0.33
                r, g, b = int(255 - 155 * tt), int(255 - 55 * tt), 255
            elif t < 0.66:
                tt = (t - 0.33) / 0.33
                r, g, b = int(100 - 80 * tt), int(200 - 120 * tt), 255
            else:
                tt = (t - 0.66) / 0.34
                r, g, b = int(20 + 100 * tt), int(80 - 80 * tt), int(255 - 55 * tt)
            table.append((r, g, b))
    return table


NEIGHBORS = [
    (-1, -1), (0, -1), (1, -1),
    (-1,  0),          (1,  0),
    (-1,  1), (0,  1), (1,  1),
]


class CyclicLab(Visual):
    name = "CYCLIC LAB"
    description = "Explore cyclic CA parameter space"
    category = "automata"

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.base_interval = 0.08
        self.min_interval = 0.05

        self.num_states = settings.get('cyclic_lab_states', 12)
        self.threshold = settings.get('cyclic_lab_threshold', 1)
        self.palette_idx = settings.get('cyclic_lab_palette', 0) % len(PALETTE_NAMES)
        self._rebuild_colors()

        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.prev_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.blend = 0.0
        self._randomize()

        self.param_overlay_timer = 2.0
        self.saved_timer = 0.0
        self.confirm_timer = 0.0
        self._both_held_prev = False

    def _rebuild_colors(self):
        self.color_table = _build_color_table(
            self.num_states, PALETTE_NAMES[self.palette_idx])

    def _randomize(self):
        n = self.num_states
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = random.randint(0, n - 1)

    def handle_input(self, input_state) -> bool:
        consumed = False
        if input_state.left_pressed:
            self.num_states = max(3, self.num_states - 1)
            self._rebuild_colors()
            self._clamp_grid()
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.right_pressed:
            self.num_states = min(28, self.num_states + 1)
            self._rebuild_colors()
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.up_pressed:
            self.threshold = min(5, self.threshold + 1)
            self.param_overlay_timer = 2.0
            consumed = True
        if input_state.down_pressed:
            self.threshold = max(1, self.threshold - 1)
            self.param_overlay_timer = 2.0
            consumed = True
        both_held = input_state.action_l_held and input_state.action_r_held
        both_released = self._both_held_prev and not both_held
        if both_released:
            self.confirm_timer = 3.0
            consumed = True
        elif self.confirm_timer > 0 and not both_held:
            if input_state.action_r:
                settings.set('cyclic_lab_states', self.num_states)
                settings.set('cyclic_lab_threshold', self.threshold)
                settings.set('cyclic_lab_palette', self.palette_idx)
                self.saved_timer = 1.5
                self.confirm_timer = 0.0
                consumed = True
            elif input_state.action_l:
                self.confirm_timer = 0.0
                consumed = True
        elif not both_held:
            if input_state.action_l or input_state.action_r:
                self.palette_idx = (self.palette_idx + 1) % len(PALETTE_NAMES)
                self._rebuild_colors()
                self._randomize()
                consumed = True
        self._both_held_prev = both_held
        return consumed

    def _clamp_grid(self):
        n = self.num_states
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x] >= n:
                    self.grid[y][x] = self.grid[y][x] % n
                if self.prev_grid[y][x] >= n:
                    self.prev_grid[y][x] = self.prev_grid[y][x] % n

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt
        effective_interval = max(self.base_interval, self.min_interval)
        if self.update_timer >= effective_interval:
            self.update_timer = 0.0
            self._step_ca()
        self.blend = min(1.0, self.update_timer / effective_interval)
        if self.param_overlay_timer > 0:
            self.param_overlay_timer = max(0.0, self.param_overlay_timer - dt)
        if self.saved_timer > 0:
            self.saved_timer = max(0.0, self.saved_timer - dt)
        if self.confirm_timer > 0:
            self.confirm_timer = max(0.0, self.confirm_timer - dt)

    def _step_ca(self):
        n = self.num_states
        th = self.threshold
        grid = self.grid
        nxt = self.next_grid

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.prev_grid[y][x] = grid[y][x]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = grid[y][x]
                successor = (state + 1) % n
                count = 0
                for dx, dy in NEIGHBORS:
                    if grid[(y + dy) % GRID_SIZE][(x + dx) % GRID_SIZE] == successor:
                        count += 1
                        if count >= th:
                            break
                if count >= th:
                    nxt[y][x] = successor
                else:
                    nxt[y][x] = state

        self.grid, self.next_grid = self.next_grid, self.grid

    def draw(self):
        colors = self.color_table
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
            region = _nearest_region(self.num_states, self.threshold)
            if region:
                self.display.draw_text_small(2, 2, region, c)
                self.display.draw_text_small(2, 8, "states=%d" % self.num_states, c)
                self.display.draw_text_small(2, 14, "thresh=%d" % self.threshold, c)
            else:
                self.display.draw_text_small(2, 2, "states=%d" % self.num_states, c)
                self.display.draw_text_small(2, 8, "thresh=%d" % self.threshold, c)

        if self.confirm_timer > 0 and self.saved_timer <= 0:
            alpha = min(1.0, self.confirm_timer / 0.5)
            c = (int(255 * alpha), int(220 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVE?", c)
        if self.saved_timer > 0:
            alpha = min(1.0, self.saved_timer / 0.5)
            c = (int(80 * alpha), int(255 * alpha), int(80 * alpha))
            self.display.draw_text_small(2, 20, "SAVED", c)

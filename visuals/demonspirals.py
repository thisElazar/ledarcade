"""
Demon Spirals - Cyclic Cellular Automaton
=========================================
Cyclic CA from David Griffeath. N states cycle around, cells advance
when neighbors have successor state. Self-organizes from random noise
into mesmerizing rotating spiral patterns.

Controls:
  Up/Down     - Change color palette
  Left/Right  - Adjust speed
  Space       - Randomize
  Escape      - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


class DemonSpirals(Visual):
    name = "CYCLIC"
    description = "Cyclic CA spirals"
    category = "automata"

    # Moore neighborhood offsets (8 surrounding cells)
    NEIGHBORS = [
        (-1, -1), (0, -1), (1, -1),
        (-1,  0),          (1,  0),
        (-1,  1), (0,  1), (1,  1),
    ]

    PALETTE_NAMES = ["rainbow", "fire", "ocean", "forest", "neon", "ice"]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.speed = 1.0
        self.base_interval = 0.08
        self.min_interval = 0.05

        # Number of cyclic states (read committed LAB defaults)
        import settings as _s
        self.num_states = _s.get('cyclic_lab_states', 12)
        self.threshold = _s.get('cyclic_lab_threshold', 1)

        # Color palette
        self.palette_index = 0
        self._build_color_table()

        # Double-buffered grids + smoothing
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.prev_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.blend = 0.0

        # Staleness detection
        self.generation = 0
        self.stale_check_interval = 200
        self.prev_state_hash = None

        self._randomize()

    def _build_color_table(self):
        """Map each state 0..N-1 to colors based on current palette."""
        n = self.num_states
        palette = self.PALETTE_NAMES[self.palette_index]
        self.color_table = []

        for i in range(n):
            t = i / n  # 0.0 to ~1.0
            if palette == "rainbow":
                self.color_table.append(self._hue_to_rgb(t))
            elif palette == "fire":
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
                self.color_table.append((r, g, b))
            elif palette == "ocean":
                if t < 0.33:
                    tt = t / 0.33
                    r, g, b = 0, int(40 * tt), int(80 + 175 * tt)
                elif t < 0.66:
                    tt = (t - 0.33) / 0.33
                    r, g, b = 0, int(40 + 215 * tt), 255
                else:
                    tt = (t - 0.66) / 0.34
                    r, g, b = int(100 * tt), 255, int(255 - 55 * tt)
                self.color_table.append((r, g, b))
            elif palette == "forest":
                if t < 0.33:
                    tt = t / 0.33
                    r, g, b = 0, int(60 + 130 * tt), int(20 * tt)
                elif t < 0.66:
                    tt = (t - 0.33) / 0.33
                    r, g, b = int(80 * tt), int(190 + 65 * tt), 0
                else:
                    tt = (t - 0.66) / 0.34
                    r, g, b = int(80 + 175 * tt), 255, int(50 * tt)
                self.color_table.append((r, g, b))
            elif palette == "neon":
                hue = (0.75 + t * 0.5) % 1.0
                self.color_table.append(self._hue_to_rgb(hue))
            elif palette == "ice":
                if t < 0.33:
                    tt = t / 0.33
                    r, g, b = int(255 - 155 * tt), int(255 - 55 * tt), 255
                elif t < 0.66:
                    tt = (t - 0.33) / 0.33
                    r, g, b = int(100 - 80 * tt), int(200 - 120 * tt), 255
                else:
                    tt = (t - 0.66) / 0.34
                    r, g, b = int(20 + 100 * tt), int(80 - 80 * tt), int(255 - 55 * tt)
                self.color_table.append((r, g, b))

    @staticmethod
    def _hue_to_rgb(hue):
        """Convert a hue (0.0-1.0) to a fully saturated RGB tuple."""
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

    def _randomize(self):
        """Fill grid with uniform random states."""
        n = self.num_states
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = random.randint(0, n - 1)
        self.generation = 0
        self.prev_state_hash = None

    def _compute_state_hash(self):
        """Compute a fast hash of the grid for staleness detection."""
        h = 0
        step = max(1, GRID_SIZE // 16)
        for y in range(0, GRID_SIZE, step):
            for x in range(0, GRID_SIZE, step):
                h = (h * 31 + self.grid[y][x]) & 0xFFFFFFFF
        return h

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.palette_index = (self.palette_index + 1) % len(self.PALETTE_NAMES)
            self._build_color_table()
            consumed = True

        if input_state.down_pressed:
            self.palette_index = (self.palette_index - 1) % len(self.PALETTE_NAMES)
            self._build_color_table()
            consumed = True

        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True

        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        if (input_state.action_l or input_state.action_r):
            self._randomize()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt

        effective_interval = max(self.base_interval / self.speed, self.min_interval)

        if self.update_timer >= effective_interval:
            self.update_timer = 0
            self._step_ca()

        # Blend factor for smooth interpolation between CA states
        self.blend = min(1.0, self.update_timer / effective_interval)

    def _step_ca(self):
        """One step of the cyclic cellular automaton."""
        n = self.num_states

        # Save current state for interpolation
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.prev_grid[y][x] = self.grid[y][x]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = self.grid[y][x]
                successor = (state + 1) % n

                # Check Moore neighborhood for the successor state
                count = 0
                for dx, dy in self.NEIGHBORS:
                    nx = (x + dx) % GRID_SIZE
                    ny = (y + dy) % GRID_SIZE
                    if self.grid[ny][nx] == successor:
                        count += 1
                        if count >= self.threshold:
                            break

                if count >= self.threshold:
                    self.next_grid[y][x] = successor
                else:
                    self.next_grid[y][x] = state

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid
        self.generation += 1

        # Periodic staleness detection
        if self.generation % self.stale_check_interval == 0:
            current_hash = self._compute_state_hash()
            if current_hash == self.prev_state_hash:
                self._randomize()
            else:
                self.prev_state_hash = current_hash

    def draw(self):
        colors = self.color_table
        grid = self.grid
        prev = self.prev_grid
        t = self.blend
        set_pixel = self.display.set_pixel

        for y in range(GRID_SIZE):
            row = grid[y]
            prev_row = prev[y]
            for x in range(GRID_SIZE):
                curr_color = colors[row[x]]
                prev_color = colors[prev_row[x]]

                if prev_color == curr_color:
                    set_pixel(x, y, curr_color)
                else:
                    color = (
                        int(prev_color[0] + (curr_color[0] - prev_color[0]) * t),
                        int(prev_color[1] + (curr_color[1] - prev_color[1]) * t),
                        int(prev_color[2] + (curr_color[2] - prev_color[2]) * t),
                    )
                    set_pixel(x, y, color)

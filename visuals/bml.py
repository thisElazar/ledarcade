"""
Gridlock - BML Traffic Model
=============================
Biham-Middleton-Levine 2D cellular automaton on a 64x64 grid.
Two car species: blue (moves north on even steps) and red (moves east
on odd steps). A car moves only if its target cell is empty. Toroidal wrap.

At low density (~0.20) diagonal stripes self-organize. Near critical
density (~0.32) free-flow and gridlock coexist. Above ~0.36 total freeze.

Controls:
  Up/Down  - Adjust density
  Space    - Reset with current density
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


# Cell states
EMPTY = 0
RED = 1    # Moves east
BLUE = 2   # Moves north


class BML(Visual):
    name = "GRIDLOCK"
    description = "BML traffic model"
    category = "road_rail"

    RED_COLOR = (255, 60, 60)
    BLUE_COLOR = (80, 120, 255)
    ROAD_BG = (20, 20, 25)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.05
        self.density = 0.28
        self.step_parity = 0  # 0 = red moves, 1 = blue moves
        self.grid = [[EMPTY] * GRID_SIZE for _ in range(GRID_SIZE)]
        self._populate()

    def _populate(self):
        """Fill grid at current density with equal red/blue."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = EMPTY

        cells = [(x, y) for y in range(GRID_SIZE) for x in range(GRID_SIZE)]
        random.shuffle(cells)
        n_cars = int(len(cells) * self.density)
        for i in range(n_cars):
            x, y = cells[i]
            self.grid[y][x] = RED if i % 2 == 0 else BLUE

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            self.density = min(0.50, self.density + 0.02)
            self._populate()
            consumed = True

        if input_state.down_pressed:
            self.density = max(0.10, self.density - 0.02)
            self._populate()
            consumed = True

        if input_state.action_l or input_state.action_r:
            self._populate()
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()

    def _step(self):
        """Advance one BML step."""
        new_grid = [row[:] for row in self.grid]

        if self.step_parity == 0:
            # Red cars move east
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x] == RED:
                        nx = (x + 1) % GRID_SIZE
                        if self.grid[y][nx] == EMPTY:
                            new_grid[y][x] = EMPTY
                            new_grid[y][nx] = RED
        else:
            # Blue cars move north
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    if self.grid[y][x] == BLUE:
                        ny = (y - 1) % GRID_SIZE
                        if self.grid[ny][x] == EMPTY:
                            new_grid[y][x] = EMPTY
                            new_grid[ny][x] = BLUE

        self.grid = new_grid
        self.step_parity = 1 - self.step_parity

    def draw(self):
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                cell = self.grid[y][x]
                if cell == RED:
                    self.display.set_pixel(x, y, self.RED_COLOR)
                elif cell == BLUE:
                    self.display.set_pixel(x, y, self.BLUE_COLOR)
                else:
                    self.display.set_pixel(x, y, self.ROAD_BG)

        # HUD: density
        d_str = f"D {self.density:.2f}"
        self.display.draw_text_small(2, 1, d_str, (180, 180, 180))

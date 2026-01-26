"""
Life - Conway's Game of Life
============================
Cellular automaton simulation with edge wrapping.

Controls:
  Space     - Pause/Resume
  Left      - Step backward (when paused)
  Right     - Step forward (when paused)
  Up        - Randomize (dense)
  Down      - Randomize (sparse)
  Escape    - Exit
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class Life(Visual):
    name = "LIFE"
    description = "Conway's Game of Life"
    category = "automata"

    MAX_HISTORY = 100  # How many states to remember for rewinding

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.1  # Time between generations
        self.paused = False
        self.generation = 0

        # Grid of cells (True = alive, False = dead)
        self.grid = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]

        # History for stepping backward
        self.history = []

        self._randomize(0.3)

    def _randomize(self, density):
        """Fill grid with random cells at given density."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = random.random() < density
        self.generation = 0
        self.history = []  # Clear history on randomize

    def _copy_grid(self):
        """Return a copy of the current grid."""
        return [row[:] for row in self.grid]

    def _count_neighbors(self, x, y):
        """Count live neighbors with edge wrapping."""
        count = 0
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                # Wrap at edges
                nx = (x + dx) % GRID_SIZE
                ny = (y + dy) % GRID_SIZE
                if self.grid[ny][nx]:
                    count += 1
        return count

    def _step_forward(self):
        """Advance one generation."""
        # Save current state to history
        if len(self.history) >= self.MAX_HISTORY:
            self.history.pop(0)
        self.history.append(self._copy_grid())

        new_grid = [[False] * GRID_SIZE for _ in range(GRID_SIZE)]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                neighbors = self._count_neighbors(x, y)
                alive = self.grid[y][x]

                # Conway's rules:
                # - Live cell with 2-3 neighbors survives
                # - Dead cell with exactly 3 neighbors becomes alive
                # - All other cells die or stay dead
                if alive:
                    new_grid[y][x] = neighbors in (2, 3)
                else:
                    new_grid[y][x] = neighbors == 3

        self.grid = new_grid
        self.generation += 1

    def _step_backward(self):
        """Go back one generation if history available."""
        if self.history:
            self.grid = self.history.pop()
            self.generation = max(0, self.generation - 1)

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.action:
            # Space toggles pause/resume
            self.paused = not self.paused
            consumed = True

        if input_state.up:
            # Dense randomize
            self._randomize(0.45)
            consumed = True

        if input_state.down:
            # Sparse randomize
            self._randomize(0.15)
            consumed = True

        if self.paused:
            if input_state.right:
                self._step_forward()
                consumed = True
            if input_state.left:
                self._step_backward()
                consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt

        if not self.paused:
            self.step_timer += dt
            if self.step_timer >= self.step_interval:
                self.step_timer = 0
                self._step_forward()

                # Auto-randomize if population too low
                population = sum(sum(row) for row in self.grid)
                if population < 10:
                    self._randomize(0.3)

    def draw(self):
        self.display.clear(Colors.BLACK)

        # Color based on time for visual interest
        hue = (self.time * 0.05) % 1.0
        h = hue * 6.0
        i = int(h)
        f = h - i

        if i == 0:
            color = (255, int(255 * f), 0)
        elif i == 1:
            color = (int(255 * (1 - f)), 255, 0)
        elif i == 2:
            color = (0, 255, int(255 * f))
        elif i == 3:
            color = (0, int(255 * (1 - f)), 255)
        elif i == 4:
            color = (int(255 * f), 0, 255)
        else:
            color = (255, 0, int(255 * (1 - f)))

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                if self.grid[y][x]:
                    self.display.set_pixel(x, y, color)

        # Show pause indicator
        if self.paused:
            self.display.draw_text_small(2, 2, "||", Colors.WHITE)

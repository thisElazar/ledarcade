"""
Star Wars - Generations Cellular Automaton
==========================================
Generations rule 345/2/4 by Mirek Wojtowicz. Four-state CA that
produces dynamic space-battle-like formations with haulers,
shooters, and self-organizing colonies.

Controls:
  Up/Down     - Change color palette
  Left/Right  - Adjust speed
  Space       - Randomize
  Escape      - Exit
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


class StarWarsCA(Visual):
    name = "STARWARS"
    description = "Generations 345/2/4"
    category = "automata"

    # Generations rule 345/2/4
    NUM_STATES = 4          # 0=dead, 1=alive, 2=dying-1, 3=dying-2
    BIRTH = {2}             # Dead cell becomes alive with exactly 2 alive neighbors
    SURVIVAL = {3, 4, 5}   # Alive cell survives with 3, 4, or 5 alive neighbors

    # Color palettes: each maps states 0-3 to colors
    PALETTES = [
        # Space battle (default): black, cyan-white, blue, indigo
        ((0, 0, 0), (220, 255, 255), (40, 80, 200), (25, 10, 80)),
        # Fire: black, bright yellow, orange, dark red
        ((0, 0, 0), (255, 240, 80), (255, 120, 20), (100, 20, 0)),
        # Matrix: black, bright green, medium green, dark green
        ((0, 0, 0), (100, 255, 100), (0, 150, 50), (0, 50, 20)),
        # Plasma: black, white, magenta, dark purple
        ((0, 0, 0), (255, 255, 255), (220, 50, 220), (60, 0, 80)),
        # Amber: black, bright amber, medium orange, dark brown
        ((0, 0, 0), (255, 200, 50), (180, 100, 20), (60, 30, 5)),
        # Ice: black, bright white, light blue, deep blue
        ((0, 0, 0), (240, 250, 255), (100, 180, 255), (20, 40, 120)),
    ]

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.update_timer = 0.0
        self.speed = 1.0
        self.base_interval = 0.1
        self.min_interval = 0.05
        self.density = 0.25
        self.generation = 0

        # Palette
        self.palette_index = 0

        # Grids + smoothing
        self.grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.next_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.prev_grid = [[0] * GRID_SIZE for _ in range(GRID_SIZE)]
        self.blend = 0.0

        self._randomize()

    def _randomize(self):
        """Fill grid with random state-0 and state-1 cells at current density."""
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.grid[y][x] = 1 if random.random() < self.density else 0
        self.generation = 0

    def _count_alive_neighbors(self, x, y):
        """Count Moore neighbors in state 1 (alive) with edge wrapping."""
        count = 0
        for dy in (-1, 0, 1):
            ny = (y + dy) % GRID_SIZE
            row = self.grid[ny]
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx = (x + dx) % GRID_SIZE
                if row[nx] == 1:
                    count += 1
        return count

    def _step(self):
        """Advance one generation using Generations rule 345/2/4."""
        grid = self.grid
        next_grid = self.next_grid
        num_states = self.NUM_STATES
        birth = self.BIRTH
        survival = self.SURVIVAL

        # Save current state for interpolation
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                self.prev_grid[y][x] = grid[y][x]

        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                state = grid[y][x]

                if state == 0:
                    # Dead cell: check birth condition
                    neighbors = self._count_alive_neighbors(x, y)
                    next_grid[y][x] = 1 if neighbors in birth else 0

                elif state == 1:
                    # Alive cell: check survival condition
                    neighbors = self._count_alive_neighbors(x, y)
                    next_grid[y][x] = 1 if neighbors in survival else 2

                else:
                    # Dying cell: age toward death
                    next_state = state + 1
                    next_grid[y][x] = 0 if next_state >= num_states else next_state

        # Swap grids
        self.grid, self.next_grid = self.next_grid, self.grid
        self.generation += 1

    def _count_active(self):
        """Count cells that are not dead (states 1, 2, or 3)."""
        count = 0
        for y in range(GRID_SIZE):
            row = self.grid[y]
            for x in range(GRID_SIZE):
                if row[x] > 0:
                    count += 1
        return count

    def handle_input(self, input_state) -> bool:
        consumed = False

        if (input_state.action_l or input_state.action_r):
            self._randomize()
            consumed = True

        if input_state.up_pressed:
            self.palette_index = (self.palette_index + 1) % len(self.PALETTES)
            consumed = True
        if input_state.down_pressed:
            self.palette_index = (self.palette_index - 1) % len(self.PALETTES)
            consumed = True

        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        return consumed

    def update(self, dt: float):
        self.time += dt
        self.update_timer += dt

        effective_interval = max(self.base_interval / self.speed, self.min_interval)

        if self.update_timer >= effective_interval:
            self.update_timer = 0
            self._step()

            # Auto-randomize if the grid is nearly dead
            if self.generation % 20 == 0:
                if self._count_active() < 15:
                    self._randomize()

        # Blend factor for smooth interpolation between CA states
        self.blend = min(1.0, self.update_timer / effective_interval)

    def draw(self):
        display = self.display
        grid = self.grid
        prev = self.prev_grid
        colors = self.PALETTES[self.palette_index]
        t = self.blend

        display.clear(Colors.BLACK)

        for y in range(GRID_SIZE):
            row = grid[y]
            prev_row = prev[y]
            for x in range(GRID_SIZE):
                curr_state = row[x]
                prev_state = prev_row[x]

                if curr_state == 0 and prev_state == 0:
                    continue

                curr_color = colors[curr_state]
                prev_color = colors[prev_state]

                if prev_color == curr_color:
                    display.set_pixel(x, y, curr_color)
                else:
                    color = (
                        int(prev_color[0] + (curr_color[0] - prev_color[0]) * t),
                        int(prev_color[1] + (curr_color[1] - prev_color[1]) * t),
                        int(prev_color[2] + (curr_color[2] - prev_color[2]) * t),
                    )
                    if color[0] > 0 or color[1] > 0 or color[2] > 0:
                        display.set_pixel(x, y, color)

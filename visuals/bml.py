"""
Gridlock - BML Traffic Model
=============================
Biham-Middleton-Levine traffic on a one-way street grid. Eastbound avenues
run across, northbound streets run up; a car advances only if the next
intersection is clear, and the two directions take turns. Toroidal, so
traffic leaving one edge re-enters the other.

Below a critical density the two flows interleave and the grid self-organises
into diagonal bands of free movement. Above it, one blocked car stalls the
car behind it, and the jam locks the whole city solid.

Controls:
  Up/Down  - Adjust density
  Action   - Reset with current density
"""

import random
from . import Visual, Display, Colors, GRID_SIZE


# Cell states
EMPTY = 0
RED = 1    # Eastbound, on the avenues
BLUE = 2   # Northbound, on the streets

# The lattice is coarse enough that each cell is a city block, not a pixel:
# a 4px pitch leaves 1px of roadway and a 3px block between intersections.
PITCH = 4
L = GRID_SIZE // PITCH   # 16 x 16 intersections

# On this lattice flow stays above 0.8 up to ~0.40 and locks solid at 0.50
# (measured: 5/5 trials gridlock, median 162 steps), so the sweep needs to
# reach past 0.50 for the transition to be the thing you actually watch.
DENSITY_MIN = 0.10
DENSITY_MAX = 0.60
DENSITY_START = 0.30
SWEEP_DWELL = 10.0     # seconds at each density before adding more traffic


class BML(Visual):
    name = "GRIDLOCK"
    description = "BML traffic model"
    category = "road_rail"
    GUIDE = {
        'desc': 'The BML traffic model. Cars move east or north on alternating steps. Below a critical density, traffic flows. Above it, the system jams completely. A phase transition you can see.',
        'credit': 'Biham, Middleton & Levine, 1992',
        'legend': {
            'D#': 'Traffic density: fraction of intersections occupied by cars.',
        },
    }

    # Roadway greys are split by axis rather than dashed: the eastbound
    # avenues run warm and the northbound streets cool, matching the two car
    # colours, so the one-way structure is legible at 1px without markings.
    AVENUE_COLOR = (58, 50, 46)
    STREET_COLOR = (44, 48, 60)
    INTERSECTION = (66, 64, 70)
    BLOCK_COLORS = [(12, 12, 16), (15, 14, 18), (10, 11, 15), (17, 16, 20)]

    RED_COLOR = (255, 70, 60)
    BLUE_COLOR = (90, 130, 255)
    RED_STOPPED = (120, 20, 18)
    BLUE_STOPPED = (30, 45, 110)

    def __init__(self, display: Display):
        super().__init__(display)

    def reset(self):
        self.time = 0.0
        self.step_timer = 0.0
        self.step_interval = 0.09   # cars glide one block per step
        self.density = DENSITY_START
        self.step_parity = 0        # 0 = eastbound moves, 1 = northbound
        self.grid = [[EMPTY] * L for _ in range(L)]
        self.moves = []             # (x0, y0, x1, y1, color, wrapped)
        self._recent = []           # (moved, movers) for the last two steps
        self.idle_timer = 0.0
        self.auto_sweep = True
        self.sweep_timer = 0.0
        self.hold_timer = 0.0
        self._build_city()
        self._populate()

    def _build_city(self):
        """Pre-bake the streetscape: roads, intersections, blocks."""
        rng = random.Random(7)      # stable city, independent of traffic seed
        bg = [[self.BLOCK_COLORS[0]] * GRID_SIZE for _ in range(GRID_SIZE)]
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                on_avenue = (y % PITCH) == 0
                on_street = (x % PITCH) == 0
                if on_avenue and on_street:
                    bg[y][x] = self.INTERSECTION
                elif on_avenue:
                    bg[y][x] = self.AVENUE_COLOR
                elif on_street:
                    bg[y][x] = self.STREET_COLOR
                else:
                    bg[y][x] = rng.choice(self.BLOCK_COLORS)
        self.background = bg

    def _populate(self):
        """Fill the grid at current density with equal eastbound/northbound."""
        for j in range(L):
            for i in range(L):
                self.grid[j][i] = EMPTY

        cells = [(i, j) for j in range(L) for i in range(L)]
        random.shuffle(cells)
        n_cars = int(len(cells) * self.density)
        for k in range(n_cars):
            i, j = cells[k]
            self.grid[j][i] = RED if k % 2 == 0 else BLUE
        self.moves = []
        self._recent = []

    def _add_cars(self, density):
        """Raise the density by dropping cars into empty intersections.

        Adding to the live configuration rather than re-rolling it is what
        lets the jam grow out of the flowing state you were just watching --
        a fresh random fill every step would show only disconnected snapshots.
        """
        target = int(L * L * min(DENSITY_MAX, density))
        empty = [(i, j) for j in range(L) for i in range(L)
                 if self.grid[j][i] == EMPTY]
        current = L * L - len(empty)
        if target <= current:
            return
        random.shuffle(empty)
        for k in range(min(target - current, len(empty))):
            i, j = empty[k]
            self.grid[j][i] = RED if k % 2 == 0 else BLUE
        self.density = sum(1 for j in range(L) for i in range(L)
                           if self.grid[j][i] != EMPTY) / (L * L)

    @property
    def flow(self):
        """Fraction of cars that moved across the last full east+north pair.

        Measuring a single step would call total gridlock every time the
        blocked species takes its turn.
        """
        moved = sum(m for m, _ in self._recent)
        movers = sum(v for _, v in self._recent)
        return (moved / movers) if movers else 1.0

    def handle_input(self, input_state) -> bool:
        consumed = False

        if input_state.up_pressed:
            # Up adds traffic to the city that's already running; down has to
            # rebuild, since you can't un-jam by removing arbitrary cars.
            self._add_cars(self.density + 0.02)
            self._idle_reset()
            consumed = True

        if input_state.down_pressed:
            self.density = max(DENSITY_MIN, self.density - 0.02)
            self._populate()
            self._idle_reset()
            consumed = True

        if input_state.action_l or input_state.action_r:
            self.density = DENSITY_START
            self._populate()
            self._idle_reset()
            consumed = True

        return consumed

    def _idle_reset(self):
        self.idle_timer = 0.0
        self.auto_sweep = False
        self.hold_timer = 0.0

    def update(self, dt: float):
        self.time += dt
        self.step_timer += dt
        if self.step_timer >= self.step_interval:
            self.step_timer -= self.step_interval
            self._step()
        self._update_sweep(dt)

    def _update_sweep(self, dt):
        """Unattended, drive the city from free flow into total gridlock."""
        if not self.auto_sweep:
            self.idle_timer += dt
            if self.idle_timer >= 8.0:
                self.auto_sweep = True
                self.sweep_timer = 0.0
                self.density = DENSITY_START
                self._populate()
            return

        if self.hold_timer > 0:
            self.hold_timer -= dt
            if self.hold_timer <= 0:
                self.density = DENSITY_START
                self._populate()
            return

        if self.flow <= 0.0 and len(self._recent) == 2:
            self.hold_timer = 6.0    # sit on the frozen city
            return

        self.sweep_timer += dt
        if self.density >= DENSITY_MAX:
            # Topped out and still moving: a jam at this density takes a few
            # hundred steps to nucleate, so wait it out rather than resetting
            # on top of it. Bail eventually in case this seed never locks.
            if self.sweep_timer >= 90.0:
                self.sweep_timer = 0.0
                self.density = DENSITY_START
                self._populate()
            return

        if self.sweep_timer >= SWEEP_DWELL:
            self.sweep_timer -= SWEEP_DWELL
            self._add_cars(self.density + 0.05)

    def _step(self):
        """Advance one BML step, recording each move so it can be animated."""
        grid = self.grid
        new_grid = [row[:] for row in grid]
        moves = []
        movers = 0
        moved = 0

        if self.step_parity == 0:
            for j in range(L):
                y = j * PITCH
                row = grid[j]
                for i in range(L):
                    if row[i] != RED:
                        continue
                    movers += 1
                    ni = i + 1
                    wrapped = ni >= L
                    if wrapped:
                        ni = 0
                    if row[ni] == EMPTY:
                        new_grid[j][i] = EMPTY
                        new_grid[j][ni] = RED
                        moved += 1
                        moves.append((i * PITCH, y, (i + 1) * PITCH, y,
                                      self.RED_COLOR, wrapped))
        else:
            for j in range(L):
                for i in range(L):
                    if grid[j][i] != BLUE:
                        continue
                    movers += 1
                    nj = j - 1
                    wrapped = nj < 0
                    if wrapped:
                        nj = L - 1
                    if grid[nj][i] == EMPTY:
                        new_grid[j][i] = EMPTY
                        new_grid[nj][i] = BLUE
                        moved += 1
                        moves.append((i * PITCH, j * PITCH,
                                      i * PITCH, (j - 1) * PITCH,
                                      self.BLUE_COLOR, wrapped))

        self.grid = new_grid
        self.moves = moves
        self._recent.append((moved, movers))
        if len(self._recent) > 2:
            self._recent.pop(0)
        self.step_parity = 1 - self.step_parity

    # -- drawing ------------------------------------------------------

    def draw(self):
        d = self.display
        set_pixel = d.set_pixel

        bg = self.background
        for y in range(GRID_SIZE):
            row = bg[y]
            for x in range(GRID_SIZE):
                set_pixel(x, y, row[x])

        # Cars that are held up sit at their intersection in brake-light
        # colours, so a jam reads as a stalled queue rather than a still frame.
        moving_species = RED if self.step_parity == 0 else BLUE
        for j in range(L):
            row = self.grid[j]
            y = j * PITCH
            for i in range(L):
                cell = row[i]
                if cell == EMPTY:
                    continue
                if cell == RED:
                    blocked = self._blocked(i, j, RED)
                    col = self.RED_STOPPED if blocked else self.RED_COLOR
                else:
                    blocked = self._blocked(i, j, BLUE)
                    col = self.BLUE_STOPPED if blocked else self.BLUE_COLOR
                set_pixel(i * PITCH, y, col)

        # Cars that did move glide across the block during the interval,
        # so the eye follows traffic down a street instead of watching a
        # lattice strobe.
        t = min(1.0, self.step_timer / self.step_interval)
        for x0, y0, x1, y1, col, wrapped in self.moves:
            x = round(x0 + (x1 - x0) * t)
            y = round(y0 + (y1 - y0) * t)
            self._plot_car(x, y, col)
            if wrapped:
                # A wrapping car is drawn twice: leaving one edge (the plot
                # above, which clips off-screen) and entering the opposite
                # one, shifted a full grid back along the axis it travels.
                self._plot_car(x - GRID_SIZE if x1 != x0 else x,
                               y + GRID_SIZE if y1 != y0 else y,
                               col)

        self._draw_hud()

    def _blocked(self, i, j, species):
        """True if this car is the one whose turn it is and it cannot move."""
        if species == RED:
            if self.step_parity != 0:
                return False
            return self.grid[j][(i + 1) % L] != EMPTY
        if self.step_parity != 1:
            return False
        return self.grid[(j - 1) % L][i] != EMPTY

    def _plot_car(self, x, y, col):
        if 0 <= x < GRID_SIZE and 0 <= y < GRID_SIZE:
            self.display.set_pixel(x, y, col)

    def _draw_hud(self):
        d = self.display
        # Dark plate so the readout stays legible over the streetscape.
        d.draw_rect(0, 0, 33, 7, (0, 0, 0), filled=True)
        d.draw_text_small(1, 1, f"D{self.density:.2f}"[:5], (170, 170, 180))

        if self.flow > 0.75:
            label, col = "FLOWING", (90, 220, 110)
        elif self.flow > 0.25:
            label, col = "SLOW", (230, 190, 60)
        elif self.flow > 0.02:
            label, col = "JAMMING", (240, 130, 40)
        else:
            label, col = "GRIDLOCK", (255, 60, 50)
        w = len(label) * 4
        d.draw_rect(GRID_SIZE - w - 1, GRID_SIZE - 7, w + 1, 7, (0, 0, 0),
                    filled=True)
        d.draw_text_small(GRID_SIZE - w, GRID_SIZE - 6, label, col)

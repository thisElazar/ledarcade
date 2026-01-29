"""
Fireflies - Synchronized Flashing
==================================
Fireflies with internal oscillators gradually synchronize their
flashing through local coupling, creating mesmerizing waves of
coordinated light from initial chaos (Kuramoto model).

Controls:
  Up/Down     - Change color palette
  Left/Right  - Adjust speed
  Space       - Randomize phases
  Escape      - Exit
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


# --- Spatial hashing for fast neighbor lookups ---

class SpatialGrid:
    """Partitions the grid into cells for O(1) neighbor queries."""

    def __init__(self, cell_size):
        self.cell_size = cell_size
        self.cols = math.ceil(GRID_SIZE / cell_size)
        self.rows = math.ceil(GRID_SIZE / cell_size)
        self.cells = {}

    def clear(self):
        self.cells.clear()

    def _key(self, x, y):
        return (int(x // self.cell_size), int(y // self.cell_size))

    def insert(self, firefly):
        key = self._key(firefly.x, firefly.y)
        if key not in self.cells:
            self.cells[key] = []
        self.cells[key].append(firefly)

    def query(self, x, y, radius):
        """Return all fireflies within radius of (x, y)."""
        results = []
        r_cells = int(math.ceil(radius / self.cell_size))
        cx, cy = int(x // self.cell_size), int(y // self.cell_size)

        for dy in range(-r_cells, r_cells + 1):
            for dx in range(-r_cells, r_cells + 1):
                key = (cx + dx, cy + dy)
                bucket = self.cells.get(key)
                if bucket:
                    for f in bucket:
                        ddx = f.x - x
                        ddy = f.y - y
                        if ddx * ddx + ddy * ddy <= radius * radius:
                            results.append(f)
        return results


# --- Individual firefly ---

class Firefly:
    """A single firefly oscillator with position, phase, and frequency."""

    __slots__ = ('x', 'y', 'phase', 'natural_freq', 'brightness',
                 'flash_age', 'nudge_accum')

    def __init__(self, x, y, phase, natural_freq):
        self.x = x
        self.y = y
        self.phase = phase
        self.natural_freq = natural_freq
        self.brightness = 0.0      # cached brightness for drawing
        self.flash_age = 1.0       # time since last flash (starts old)
        self.nudge_accum = 0.0     # accumulated phase nudge this frame


# --- Main visual ---

class Fireflies(Visual):
    name = "FIREFLIES"
    description = "Synchronized flashing"
    category = "nature"

    # Population
    NUM_FIREFLIES = 300

    # Oscillator defaults
    BASE_FREQUENCY = 1.8          # radians per second (~0.29 Hz, ~3.5s cycle)
    FREQ_SPREAD = 0.15            # +/- random variation in natural frequency

    # Coupling defaults
    DEFAULT_COUPLING_STRENGTH = 0.12
    DEFAULT_COUPLING_RADIUS = 8.0

    # Spatial grid cell size (should be >= max coupling radius)
    SPATIAL_CELL_SIZE = 10

    # Two-pi constant
    TWO_PI = 2.0 * math.pi

    # Color palettes: (bright_color, dim_color, bg_tint)
    PALETTES = [
        # Warm amber (default)
        ((255, 220, 50), (40, 20, 0), (0, 3, 5)),
        # Cool blue
        ((100, 180, 255), (5, 10, 30), (0, 1, 4)),
        # Forest green
        ((80, 255, 80), (5, 25, 5), (1, 3, 1)),
        # Purple
        ((200, 120, 255), (20, 5, 30), (2, 0, 4)),
        # White
        ((255, 255, 255), (20, 20, 20), (2, 2, 3)),
        # Red
        ((255, 80, 40), (30, 5, 0), (3, 0, 0)),
    ]
    PALETTE_NAMES = ["amber", "blue", "green", "purple", "white", "red"]

    def __init__(self, display: Display):
        super().__init__(display)

    # ------------------------------------------------------------------
    # Reset / initialization
    # ------------------------------------------------------------------

    def reset(self):
        """Reset the visual to initial state with random phases."""
        self.time = 0.0
        self.speed = 1.0

        # Tunable parameters
        self.coupling_strength = self.DEFAULT_COUPLING_STRENGTH
        self.coupling_radius = self.DEFAULT_COUPLING_RADIUS

        # Color palette
        self.palette_index = 0

        # Spatial acceleration structure
        self.spatial = SpatialGrid(self.SPATIAL_CELL_SIZE)

        # Create firefly population
        self.fireflies = []
        self._populate()

        # Pre-compute background nighttime canvas
        self._build_background()

    def _populate(self):
        """Scatter fireflies across the grid with random initial phases."""
        self.fireflies.clear()

        # Use a Poisson-disk-ish scatter: random but avoiding exact overlap
        occupied = set()
        attempts = 0
        max_attempts = self.NUM_FIREFLIES * 6

        while len(self.fireflies) < self.NUM_FIREFLIES and attempts < max_attempts:
            x = random.randint(0, GRID_SIZE - 1)
            y = random.randint(0, GRID_SIZE - 1)
            key = (x, y)
            attempts += 1
            if key in occupied:
                continue
            occupied.add(key)

            phase = random.uniform(0.0, self.TWO_PI)
            freq = self.BASE_FREQUENCY + random.uniform(
                -self.FREQ_SPREAD, self.FREQ_SPREAD
            )
            self.fireflies.append(Firefly(x, y, phase, freq))

    def _build_background(self):
        """Pre-compute a subtle nighttime background texture."""
        bg_tint = self.PALETTES[self.palette_index][2]
        self.bg = [[(0, 0, 0)] * GRID_SIZE for _ in range(GRID_SIZE)]
        random.seed(42)  # deterministic so it doesn't flicker on reset
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                # Very faint noise in the palette's bg tint
                r = random.randint(0, max(1, bg_tint[0]))
                g = random.randint(0, max(1, bg_tint[1]))
                b = random.randint(0, max(1, bg_tint[2]))
                self.bg[y][x] = (r, g, b)
        random.seed()  # restore true randomness

    # ------------------------------------------------------------------
    # Input
    # ------------------------------------------------------------------

    def handle_input(self, input_state) -> bool:
        """Handle user input for adjusting parameters."""
        consumed = False

        # Space: randomize all phases (restart synchronization from chaos)
        if (input_state.action_l or input_state.action_r):
            for f in self.fireflies:
                f.phase = random.uniform(0.0, self.TWO_PI)
                f.flash_age = 1.0
            consumed = True

        # Up/Down: cycle color palette
        if input_state.up_pressed:
            self.palette_index = (self.palette_index + 1) % len(self.PALETTES)
            self._build_background()
            consumed = True
        if input_state.down_pressed:
            self.palette_index = (self.palette_index - 1) % len(self.PALETTES)
            self._build_background()
            consumed = True

        # Left/Right: speed
        if input_state.left:
            self.speed = max(0.2, self.speed - 0.2)
            consumed = True
        if input_state.right:
            self.speed = min(3.0, self.speed + 0.2)
            consumed = True

        return consumed

    # ------------------------------------------------------------------
    # Update (Kuramoto model step)
    # ------------------------------------------------------------------

    def update(self, dt: float):
        """Advance all firefly oscillators and apply coupling."""
        self.time += dt
        scaled_dt = dt * self.speed

        # Rebuild spatial hash each frame
        self.spatial.clear()
        for f in self.fireflies:
            self.spatial.insert(f)

        coupling = self.coupling_strength
        radius = self.coupling_radius
        two_pi = self.TWO_PI

        # --- Phase 1: Advance phases and detect flashes ---
        flashers = []
        for f in self.fireflies:
            f.nudge_accum = 0.0
            f.phase += f.natural_freq * scaled_dt
            f.flash_age += scaled_dt

            # Check for flash (phase crosses 2pi)
            if f.phase >= two_pi:
                f.phase -= two_pi
                f.flash_age = 0.0
                flashers.append(f)

        # --- Phase 2: Coupling — flashers nudge neighbors ---
        if coupling > 0.0:
            sin = math.sin
            for flasher in flashers:
                neighbors = self.spatial.query(
                    flasher.x, flasher.y, radius
                )
                fp = flasher.phase
                for nb in neighbors:
                    if nb is not flasher:
                        # Kuramoto coupling: nudge toward flasher's phase
                        nb.nudge_accum += coupling * sin(fp - nb.phase)

            # Apply accumulated nudges
            for f in self.fireflies:
                if f.nudge_accum != 0.0:
                    f.phase += f.nudge_accum
                    # Keep phase in [0, 2pi)
                    if f.phase < 0.0:
                        f.phase += two_pi
                    elif f.phase >= two_pi:
                        f.phase -= two_pi

        # --- Phase 3: Compute brightness for drawing ---
        cos = math.cos
        for f in self.fireflies:
            # Smooth brightness: peaks at phase=0 (flash moment)
            f.brightness = (1.0 + cos(f.phase)) * 0.5

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(self):
        """Render fireflies onto the display."""
        display = self.display
        bright_color, dim_color, _ = self.PALETTES[self.palette_index]

        # Paint nighttime background
        bg = self.bg
        for y in range(GRID_SIZE):
            row = bg[y]
            for x in range(GRID_SIZE):
                display.set_pixel(x, y, row[x])

        # Draw each firefly
        br, bg_r, bb = bright_color
        dr, dg, db = dim_color
        # Precompute delta for interpolation
        delta_r = br - dr
        delta_g = bg_r - dg
        delta_b = bb - db

        for f in self.fireflies:
            b = f.brightness

            if b < 0.01:
                continue

            # Nonlinear ramp so the flash pops
            b2 = b * b

            r = int(dr + delta_r * b2)
            g = int(dg + delta_g * b2)
            bl = int(db + delta_b * b2)

            display.set_pixel(f.x, f.y, (r, g, bl))

            # Glow halo for bright fireflies
            if b2 > 0.25:
                glow = b2 * 0.35
                gr = int(dr * glow)
                gg = int(dg * glow) if dg > 0 else int(delta_g * glow * 0.15)
                gb = int(db * glow) if db > 0 else int(delta_b * glow * 0.1)
                halo_color = (max(1, gr), max(1, gg), max(1, gb))

                fx, fy = f.x, f.y
                if fx > 0:
                    display.set_pixel(fx - 1, fy, self._add_color(
                        bg[fy][fx - 1], halo_color))
                if fx < GRID_SIZE - 1:
                    display.set_pixel(fx + 1, fy, self._add_color(
                        bg[fy][fx + 1], halo_color))
                if fy > 0:
                    display.set_pixel(fx, fy - 1, self._add_color(
                        bg[fy - 1][fx], halo_color))
                if fy < GRID_SIZE - 1:
                    display.set_pixel(fx, fy + 1, self._add_color(
                        bg[fy + 1][fx], halo_color))

    @staticmethod
    def _add_color(base, add):
        """Additive blend two RGB tuples, clamped to 255."""
        return (
            min(255, base[0] + add[0]),
            min(255, base[1] + add[1]),
            min(255, base[2] + add[2]),
        )

"""
Evolution - Fitness Landscapes
=================================
Populations evolve on fitness landscapes. Watch organisms climb peaks,
get trapped on local optima, and occasionally make the leap to higher
fitness through mutation. A shifting landscape makes today's winners
tomorrow's losers.

Controls:
  Left/Right  - Mutation rate (low = exploitation, high = exploration)
  Up/Down     - Cycle landscape type
  Space       - Mass extinction (kill 80%)
"""

import random
import math
from . import Visual, Display, Colors, GRID_SIZE


# ---------------------------------------------------------------------------
# Landscape types
# ---------------------------------------------------------------------------

LANDSCAPE_NAMES = ["SINGLE PEAK", "DOUBLE PEAK", "RUGGED", "SHIFTING"]


def _gaussian(x, mu, sigma, height=1.0):
    """Unnormalized Gaussian."""
    return height * math.exp(-0.5 * ((x - mu) / sigma) ** 2)


def _landscape_single(x, _t):
    """Single central peak."""
    return _gaussian(x, 32.0, 12.0)


def _landscape_double(x, _t):
    """Two peaks -- local optimum at x~18 (h=0.7), global at x~46 (h=1.0)."""
    return max(_gaussian(x, 18.0, 8.0, 0.70),
               _gaussian(x, 46.0, 9.0, 1.00))


class _RuggedLandscape:
    """Sum of random Gaussians -- regenerated each time landscape is selected."""

    def __init__(self):
        self.regenerate()

    def regenerate(self):
        n = random.randint(6, 8)
        self.peaks = []
        for _ in range(n):
            mu = random.uniform(4, 60)
            sigma = random.uniform(3.0, 10.0)
            height = random.uniform(0.3, 1.0)
            self.peaks.append((mu, sigma, height))
        # Normalize so max is ~1.0
        raw_max = max(self(x, 0) for x in range(GRID_SIZE))
        if raw_max > 0:
            for i, (mu, sigma, h) in enumerate(self.peaks):
                self.peaks[i] = (mu, sigma, h / raw_max)

    def __call__(self, x, _t):
        return sum(_gaussian(x, mu, sigma, h) for mu, sigma, h in self.peaks)


def _landscape_shifting(x, t):
    """Single peak that drifts sinusoidally over time."""
    center = 32.0 + 18.0 * math.sin(t * 2.0 * math.pi / 200.0)
    return _gaussian(x, center, 11.0)


# ---------------------------------------------------------------------------
# Color helpers
# ---------------------------------------------------------------------------

def _lerp_color(c1, c2, t):
    """Linearly interpolate between two RGB tuples."""
    t = max(0.0, min(1.0, t))
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )


# Terrain gradient: base -> mid -> peak
_TERRAIN_BASE = (15, 30, 10)       # dark mossy green
_TERRAIN_MID = (50, 90, 25)        # earthy green
_TERRAIN_HIGH = (180, 160, 60)     # warm gold
_TERRAIN_PEAK = (255, 240, 200)    # bright cream

# Organism colors by fitness
_ORG_LOW = (180, 40, 30)           # dim red
_ORG_MID = (60, 200, 180)         # teal
_ORG_HIGH = (220, 255, 255)       # bright cyan-white


def _terrain_color(height_frac):
    """Map a normalized height (0-1) to a terrain color."""
    if height_frac < 0.33:
        return _lerp_color(_TERRAIN_BASE, _TERRAIN_MID, height_frac / 0.33)
    elif height_frac < 0.66:
        return _lerp_color(_TERRAIN_MID, _TERRAIN_HIGH, (height_frac - 0.33) / 0.33)
    else:
        return _lerp_color(_TERRAIN_HIGH, _TERRAIN_PEAK, (height_frac - 0.66) / 0.34)


def _organism_color(fitness):
    """Map fitness (0-1) to organism dot color."""
    if fitness < 0.5:
        return _lerp_color(_ORG_LOW, _ORG_MID, fitness / 0.5)
    else:
        return _lerp_color(_ORG_MID, _ORG_HIGH, (fitness - 0.5) / 0.5)


# ---------------------------------------------------------------------------
# The Visual
# ---------------------------------------------------------------------------

class Evolution(Visual):
    name = "EVOLUTION"
    description = "Fitness landscapes"
    category = "science"

    def __init__(self, display: Display):
        self._rugged = _RuggedLandscape()
        super().__init__(display)

    # ---- landscape helpers ----

    def _get_landscape_fn(self):
        idx = self.landscape_idx
        if idx == 0:
            return _landscape_single
        elif idx == 1:
            return _landscape_double
        elif idx == 2:
            return self._rugged
        else:
            return _landscape_shifting

    def _fitness(self, x):
        """Return fitness at position x for current landscape and generation."""
        return max(0.0, min(1.0, self._get_landscape_fn()(x, self.generation)))

    def _build_landscape_heights(self):
        """Pre-compute landscape height at every x for drawing."""
        self._heights = [self._fitness(x) for x in range(GRID_SIZE)]

    # ---- lifecycle ----

    def reset(self):
        self.time = 0.0

        # Landscape
        self.landscape_idx = 0      # 0=single, 1=double, 2=rugged, 3=shifting

        # Population
        self.mutation_rate = 2.0     # gaussian std dev in x-units
        self.mutation_min = 0.5
        self.mutation_max = 8.0
        self.carrying_capacity = 120

        # Generation timing
        self.gen_timer = 0.0
        self.gen_interval = 0.10     # seconds per generation
        self.generation = 0

        # Organisms: list of x-positions (floats 0-63)
        self.organisms = [random.uniform(0, GRID_SIZE - 1)
                          for _ in range(self.carrying_capacity)]

        # Extinction flash
        self.flash_timer = 0.0

        # Overlay
        self.overlay_timer = 2.0
        self.overlay_lines = [LANDSCAPE_NAMES[self.landscape_idx],
                              f"MUT {self.mutation_rate:.1f}"]

        # Pre-compute heights
        self._build_landscape_heights()

        # Mean fitness (for display)
        self._mean_fitness = 0.0
        self._update_mean_fitness()

    # ---- input ----

    def handle_input(self, input_state) -> bool:
        consumed = False

        # Left/Right: mutation rate (continuous)
        if input_state.left:
            self.mutation_rate = max(self.mutation_min,
                                     round(self.mutation_rate - 0.05, 2))
            self.overlay_lines = [f"MUT {self.mutation_rate:.1f}"]
            self.overlay_timer = 1.5
            consumed = True
        if input_state.right:
            self.mutation_rate = min(self.mutation_max,
                                     round(self.mutation_rate + 0.05, 2))
            self.overlay_lines = [f"MUT {self.mutation_rate:.1f}"]
            self.overlay_timer = 1.5
            consumed = True

        # Up/Down: cycle landscape (single press)
        if input_state.up_pressed:
            self.landscape_idx = (self.landscape_idx + 1) % len(LANDSCAPE_NAMES)
            if self.landscape_idx == 2:
                self._rugged.regenerate()
            self._build_landscape_heights()
            self.overlay_lines = [LANDSCAPE_NAMES[self.landscape_idx]]
            self.overlay_timer = 1.5
            consumed = True
        if input_state.down_pressed:
            self.landscape_idx = (self.landscape_idx - 1) % len(LANDSCAPE_NAMES)
            if self.landscape_idx == 2:
                self._rugged.regenerate()
            self._build_landscape_heights()
            self.overlay_lines = [LANDSCAPE_NAMES[self.landscape_idx]]
            self.overlay_timer = 1.5
            consumed = True

        # Action: mass extinction
        if input_state.action_l or input_state.action_r:
            self._mass_extinction()
            consumed = True

        return consumed

    # ---- simulation ----

    def _mass_extinction(self):
        """Kill 80% of population randomly."""
        if len(self.organisms) < 5:
            return
        random.shuffle(self.organisms)
        survivors = max(3, len(self.organisms) // 5)
        self.organisms = self.organisms[:survivors]
        self.flash_timer = 0.3
        self.overlay_lines = ["EXTINCTION", f"POP {len(self.organisms)}"]
        self.overlay_timer = 1.5

    def _step_generation(self):
        """Run one generation of selection + reproduction + mutation."""
        self.generation += 1

        if not self.organisms:
            # Re-seed if somehow empty
            self.organisms = [random.uniform(0, GRID_SIZE - 1) for _ in range(20)]
            return

        # Calculate fitness for each organism
        fitnesses = [self._fitness(x) for x in self.organisms]

        # Roulette wheel selection: probability proportional to fitness
        total_fitness = sum(fitnesses)
        if total_fitness <= 0:
            # All at zero fitness -- random survival
            total_fitness = len(fitnesses)
            fitnesses = [1.0] * len(fitnesses)

        # Build cumulative distribution
        cum = []
        running = 0.0
        for f in fitnesses:
            running += f / total_fitness
            cum.append(running)

        # Produce next generation
        target_pop = self.carrying_capacity
        new_organisms = []
        for _ in range(target_pop):
            # Pick a parent via roulette
            r = random.random()
            # Binary search
            lo, hi = 0, len(cum) - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if cum[mid] < r:
                    lo = mid + 1
                else:
                    hi = mid
            parent_x = self.organisms[lo]

            # Offspring with mutation
            child_x = parent_x + random.gauss(0, self.mutation_rate)
            child_x = max(0.0, min(GRID_SIZE - 1.0, child_x))
            new_organisms.append(child_x)

        # If over capacity keep the fittest (shouldn't happen with fixed target)
        if len(new_organisms) > self.carrying_capacity:
            scored = [(self._fitness(x), x) for x in new_organisms]
            scored.sort(reverse=True)
            new_organisms = [x for _, x in scored[:self.carrying_capacity]]

        self.organisms = new_organisms
        self._update_mean_fitness()

    def _update_mean_fitness(self):
        if self.organisms:
            self._mean_fitness = sum(self._fitness(x) for x in self.organisms) / len(self.organisms)
        else:
            self._mean_fitness = 0.0

    def update(self, dt: float):
        self.time += dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Extinction flash fade
        if self.flash_timer > 0:
            self.flash_timer -= dt

        # Shifting landscape needs continuous height rebuild
        if self.landscape_idx == 3:
            self._build_landscape_heights()

        # Generation stepping
        self.gen_timer += dt
        if self.gen_timer >= self.gen_interval:
            self.gen_timer -= self.gen_interval
            self._step_generation()

    # ---- drawing ----

    def draw(self):
        d = self.display

        # --- Background (dark sky above terrain, red-tinted during extinction) ---
        flash_alpha = min(1.0, self.flash_timer / 0.15) if self.flash_timer > 0 else 0.0
        sky_base = (3, 3, 12)
        if flash_alpha > 0:
            sky_base = (int(3 + 100 * flash_alpha), int(3 * (1.0 - 0.5 * flash_alpha)),
                        int(12 * (1.0 - 0.5 * flash_alpha)))
        for y in range(GRID_SIZE):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, sky_base)

        # --- Draw terrain (filled from landscape line down to bottom) ---
        # Map heights: height 1.0 -> y=4 (near top), height 0.0 -> y=55 (near bottom)
        # Leave room at top for overlay and bottom for info
        y_top = 4
        y_bottom = 55
        y_range = y_bottom - y_top

        # Compute screen y for each landscape column
        landscape_y = []
        for x in range(GRID_SIZE):
            h = self._heights[x]
            screen_y = int(y_bottom - h * y_range)
            screen_y = max(y_top, min(y_bottom, screen_y))
            landscape_y.append(screen_y)

        # Fill terrain columns
        for x in range(GRID_SIZE):
            surface_y = landscape_y[x]
            h = self._heights[x]
            for y in range(surface_y, y_bottom + 1):
                # Depth below surface -> darker
                depth_frac = (y - surface_y) / max(1, y_bottom - surface_y)
                # Color based on height at surface, dimmed by depth
                base_color = _terrain_color(h)
                dim = max(0.15, 1.0 - depth_frac * 0.7)
                color = (int(base_color[0] * dim),
                         int(base_color[1] * dim),
                         int(base_color[2] * dim))
                # Flash tint
                if self.flash_timer > 0:
                    flash_alpha = min(1.0, self.flash_timer / 0.15)
                    color = (min(255, int(color[0] + 100 * flash_alpha)),
                             int(color[1] * (1.0 - 0.5 * flash_alpha)),
                             int(color[2] * (1.0 - 0.5 * flash_alpha)))
                d.set_pixel(x, y, color)

            # Bright edge pixel at surface
            edge_color = _terrain_color(h)
            bright = (min(255, edge_color[0] + 40),
                      min(255, edge_color[1] + 40),
                      min(255, edge_color[2] + 40))
            d.set_pixel(x, surface_y, bright)

        # --- Population density heatmap at bottom rows (56-59) ---
        # Bin organisms into x buckets
        density = [0] * GRID_SIZE
        for ox in self.organisms:
            bx = int(max(0, min(GRID_SIZE - 1, ox)))
            density[bx] += 1
        max_density = max(max(density), 1)

        for x in range(GRID_SIZE):
            if density[x] > 0:
                intensity = density[x] / max_density
                # Warm glow
                r = int(60 + 140 * intensity)
                g = int(20 + 60 * intensity)
                b = int(5 + 15 * intensity)
                for y in range(56, 60):
                    d.set_pixel(x, y, (r, g, b))

        # --- Draw organisms as dots on the landscape surface ---
        for ox in self.organisms:
            bx = int(max(0, min(GRID_SIZE - 1, ox)))
            sy = landscape_y[bx]
            fit = self._fitness(ox)
            color = _organism_color(fit)
            # Draw dot 1 pixel above surface
            dot_y = sy - 1
            if 0 <= dot_y < GRID_SIZE:
                d.set_pixel(bx, dot_y, color)
            # For high density, also draw at surface
            if density[bx] > 2 and 0 <= sy < GRID_SIZE:
                dimmed = (color[0] // 2, color[1] // 2, color[2] // 2)
                d.set_pixel(bx, sy, dimmed)
            # Extra bright dot 2 above surface for very fit organisms
            if fit > 0.8:
                dot_y2 = sy - 2
                if 0 <= dot_y2 < GRID_SIZE:
                    glow = (min(255, color[0] + 30),
                            min(255, color[1] + 30),
                            min(255, color[2] + 30))
                    d.set_pixel(bx, dot_y2, glow)

        # --- Mean fitness line (thin horizontal, subtle) ---
        mean_screen_y = int(y_bottom - self._mean_fitness * y_range)
        mean_screen_y = max(y_top, min(y_bottom, mean_screen_y))
        for x in range(0, GRID_SIZE, 2):  # dashed line
            if 0 <= mean_screen_y < GRID_SIZE:
                d.set_pixel(x, mean_screen_y, (100, 100, 60))

        # --- Generation counter (bottom-right, subtle) ---
        gen_str = f"G{self.generation}"
        self.display.draw_text_small(GRID_SIZE - len(gen_str) * 4 - 2, 60,
                                     gen_str, (80, 80, 80))

        # --- Population count (bottom-left, subtle) ---
        pop_str = f"N{len(self.organisms)}"
        self.display.draw_text_small(2, 60, pop_str, (80, 80, 80))

        # --- HUD overlay (fading) ---
        if self.overlay_timer > 0:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            for i, line in enumerate(self.overlay_lines):
                self.display.draw_text_small(2, 1 + i * 7, line, oc)

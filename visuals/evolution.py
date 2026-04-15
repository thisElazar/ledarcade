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
    """Single peak that drifts sinusoidally over time (period=120 gens)."""
    center = 32.0 + 18.0 * math.sin(t * 2.0 * math.pi / 120.0)
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

# Organism colors by fitness (pink-to-white for max terrain contrast)
_ORG_LOW = (200, 50, 80)           # pink
_ORG_MID = (255, 160, 220)        # light pink
_ORG_HIGH = (255, 255, 255)       # bright white


def _terrain_color(height_frac):
    """Map a normalized height (0-1) to a terrain color."""
    if height_frac < 0.33:
        return _lerp_color(_TERRAIN_BASE, _TERRAIN_MID, height_frac / 0.33)
    elif height_frac < 0.66:
        return _lerp_color(_TERRAIN_MID, _TERRAIN_HIGH, (height_frac - 0.33) / 0.33)
    else:
        return _lerp_color(_TERRAIN_HIGH, _TERRAIN_PEAK, (height_frac - 0.66) / 0.34)


def _organism_color(fitness):
    """Map fitness (0-1) to organism dot color (pink-to-white)."""
    if fitness < 0.5:
        return _lerp_color(_ORG_LOW, _ORG_MID, fitness / 0.5)
    else:
        return _lerp_color(_ORG_MID, _ORG_HIGH, (fitness - 0.5) / 0.5)


def _apply_hue_tint(color, hue):
    """Apply lineage hue tint by shifting R and B channels."""
    angle = hue * 2.0 * math.pi
    r_shift = math.sin(angle) * 20.0
    b_shift = math.cos(angle) * 20.0
    return (
        max(0, min(255, int(color[0] + r_shift))),
        color[1],
        max(0, min(255, int(color[2] + b_shift))),
    )


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


# ---------------------------------------------------------------------------
# The Visual
# ---------------------------------------------------------------------------

class Evolution(Visual):
    name = "EVOLUTION"
    description = "Fitness landscapes"
    category = "science_macro"

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

    def _current_peak_x(self):
        """Return the x position of the current landscape peak."""
        center = 32.0 + 18.0 * math.sin(self.generation * 2.0 * math.pi / 120.0)
        return center

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

        # Organisms: list of (x_position, fitness_cache, hue, alive)
        self.organisms = []
        for _ in range(self.carrying_capacity):
            x = random.uniform(0, GRID_SIZE - 1)
            self.organisms.append([x, 0.0, random.random(), True])
        # Fitness will be computed after landscape heights are built

        # Extinction state
        self.flash_timer = 0.0
        self.extinction_phase = 0      # 0=none, 1=white flash, 2=death particles, 3=desat
        self.extinction_timer = 0.0
        self.death_particles = []      # list of [x, y, age] for falling particles
        self.extinction_active = False

        # Overlay
        self.overlay_timer = 2.0
        self.overlay_lines = [LANDSCAPE_NAMES[self.landscape_idx],
                              f"MUT {self.mutation_rate:.1f}"]

        # Pre-compute heights
        self._build_landscape_heights()

        # Update cached fitness values
        for org in self.organisms:
            org[1] = self._fitness(org[0])

        # Mean fitness history for sparkline (last 64 values)
        self._mean_fitness = 0.0
        self._update_mean_fitness()
        self._fitness_history = [self._mean_fitness] * 64

        # Shifting peak tracking (for indicators)
        self._peak_trail = []  # last 8 peak x positions

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
        """Kill 80% of population with dramatic multi-phase extinction."""
        if len(self.organisms) < 5:
            return
        random.shuffle(self.organisms)
        survivors = max(3, len(self.organisms) // 5)
        killed = self.organisms[survivors:]
        self.organisms = self.organisms[:survivors]

        # Record death particle positions for animation
        self.death_particles = []
        for org in killed:
            bx = int(_clamp(org[0], 0, GRID_SIZE - 1))
            # Approximate surface y
            h = self._heights[bx]
            sy = int(55 - h * 45)
            sy = max(10, min(55, sy))
            self.death_particles.append([bx, sy - 1, 0.0])

        # Start extinction sequence
        self.extinction_active = True
        self.extinction_phase = 1
        self.extinction_timer = 0.15  # phase 1 duration
        self.flash_timer = 1.15       # total extinction visibility

        self.overlay_lines = ["EXTINCTION", f"POP {len(self.organisms)}"]
        self.overlay_timer = 1.5

    def _step_generation(self):
        """Run one generation of selection + reproduction + mutation."""
        self.generation += 1

        if not self.organisms:
            # Re-seed if somehow empty
            self.organisms = []
            for _ in range(20):
                x = random.uniform(0, GRID_SIZE - 1)
                self.organisms.append([x, 0.0, random.random(), True])
            return

        # Calculate fitness for each organism
        fitnesses = [self._fitness(org[0]) for org in self.organisms]
        for i, f in enumerate(fitnesses):
            self.organisms[i][1] = f

        # Determine fitness threshold for top 20%
        sorted_fit = sorted(fitnesses, reverse=True)
        top20_threshold = sorted_fit[max(0, len(sorted_fit) // 5 - 1)] if sorted_fit else 0.5

        # Roulette wheel selection: probability proportional to fitness
        total_fitness = sum(fitnesses)
        if total_fitness <= 0:
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
            lo, hi = 0, len(cum) - 1
            while lo < hi:
                mid = (lo + hi) // 2
                if cum[mid] < r:
                    lo = mid + 1
                else:
                    hi = mid
            parent = self.organisms[lo]
            parent_x = parent[0]
            parent_hue = parent[2]

            # Offspring with mutation
            child_x = parent_x + random.gauss(0, self.mutation_rate)
            child_x = max(0.0, min(GRID_SIZE - 1.0, child_x))

            # Hue mutation
            child_hue = parent_hue + random.gauss(0, 0.02)
            child_hue = max(0.0, min(1.0, child_hue))

            child_fit = self._fitness(child_x)
            new_organisms.append([child_x, child_fit, child_hue, True])

        # If over capacity keep the fittest
        if len(new_organisms) > self.carrying_capacity:
            new_organisms.sort(key=lambda o: o[1], reverse=True)
            new_organisms = new_organisms[:self.carrying_capacity]

        self.organisms = new_organisms
        self._update_mean_fitness()

        # Update fitness sparkline history
        self._fitness_history.append(self._mean_fitness)
        if len(self._fitness_history) > 64:
            self._fitness_history = self._fitness_history[-64:]

        # Track shifting peak positions
        if self.landscape_idx == 3:
            px = self._current_peak_x()
            self._peak_trail.append(px)
            if len(self._peak_trail) > 8:
                self._peak_trail = self._peak_trail[-8:]

    def _update_mean_fitness(self):
        if self.organisms:
            self._mean_fitness = sum(self._fitness(o[0]) for o in self.organisms) / len(self.organisms)
        else:
            self._mean_fitness = 0.0

    def update(self, dt: float):
        self.time += dt

        # Overlay fade
        if self.overlay_timer > 0:
            self.overlay_timer -= dt

        # Extinction sequence phases
        if self.extinction_active:
            self.extinction_timer -= dt
            if self.extinction_timer <= 0:
                if self.extinction_phase == 1:
                    # Transition to phase 2: death particles
                    self.extinction_phase = 2
                    self.extinction_timer = 0.6
                elif self.extinction_phase == 2:
                    # Transition to phase 3: desaturated terrain
                    self.extinction_phase = 3
                    self.extinction_timer = 0.4
                else:
                    # End extinction sequence
                    self.extinction_active = False
                    self.extinction_phase = 0
                    self.death_particles = []

            # Animate death particles falling
            if self.extinction_phase == 2:
                for p in self.death_particles:
                    p[2] += dt  # age
                    p[1] += dt * 4.0  # fall speed: ~4 px/s

        # Flash timer (total extinction visibility)
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

        # --- Clear background ---
        d.clear((2, 2, 8))

        # --- Fitness sparkline (rows 0-7) ---
        self._draw_sparkline(d)

        # --- Shifting peak indicators (row 9-10 area) ---
        if self.landscape_idx == 3:
            self._draw_peak_indicators(d)

        # --- Draw terrain (filled from landscape line down to bottom) ---
        # Map heights: height 1.0 -> y=10 (near top), height 0.0 -> y=55 (near bottom)
        y_top = 10
        y_bottom = 55
        y_range = y_bottom - y_top

        # Compute screen y for each landscape column
        landscape_y = []
        for x in range(GRID_SIZE):
            h = self._heights[x]
            screen_y = int(y_bottom - h * y_range)
            screen_y = max(y_top, min(y_bottom, screen_y))
            landscape_y.append(screen_y)

        # Extinction desaturation factor (phase 3)
        desat = 0.0
        if self.extinction_active and self.extinction_phase == 3:
            desat = min(1.0, self.extinction_timer / 0.4) * 0.25

        # Fill terrain columns
        for x in range(GRID_SIZE):
            surface_y = landscape_y[x]
            h = self._heights[x]
            for y in range(surface_y, y_bottom + 1):
                # Depth below surface -> darker
                depth_frac = (y - surface_y) / max(1, y_bottom - surface_y)
                base_color = _terrain_color(h)
                dim = max(0.15, 1.0 - depth_frac * 0.7)

                r = int(base_color[0] * dim)
                g = int(base_color[1] * dim)
                b = int(base_color[2] * dim)

                # Geological strata: every 4th row below surface, darken by 15%
                depth_from_surface = y - surface_y
                if depth_from_surface > 0 and depth_from_surface % 4 == 0:
                    r = int(r * 0.85)
                    g = int(g * 0.85)
                    b = int(b * 0.85)

                # Subtle dither: add +8 brightness on pattern
                if (x + y) % 3 == 0:
                    r = min(255, r + 8)
                    g = min(255, g + 8)
                    b = min(255, b + 8)

                # Extinction phase 3: desaturate G and B
                if desat > 0:
                    g = int(g * (1.0 - desat))
                    b = int(b * (1.0 - desat))

                d.set_pixel(x, y, (r, g, b))

            # Bright surface highlight pixel
            edge_color = _terrain_color(h)
            bright = (min(255, edge_color[0] + 40),
                      min(255, edge_color[1] + 40),
                      min(255, edge_color[2] + 40))
            d.set_pixel(x, surface_y, bright)

            # 1px shadow just below surface
            if surface_y + 1 <= y_bottom:
                shadow_base = _terrain_color(h)
                shadow = (int(shadow_base[0] * 0.8),
                          int(shadow_base[1] * 0.8),
                          int(shadow_base[2] * 0.8))
                d.set_pixel(x, surface_y + 1, shadow)

        # --- Population density histogram (rows 56-59) ---
        self._draw_density_histogram(d, landscape_y)

        # --- Draw organisms on the landscape surface ---
        self._draw_organisms(d, landscape_y)

        # --- Draw death particles during extinction phase 2 ---
        if self.extinction_active and self.extinction_phase == 2:
            self._draw_death_particles(d)

        # --- White flash during extinction phase 1 ---
        if self.extinction_active and self.extinction_phase == 1:
            alpha = min(1.0, self.extinction_timer / 0.15)
            flash_brightness = int(255 * alpha)
            fc = (flash_brightness, flash_brightness, flash_brightness)
            for y in range(GRID_SIZE):
                for x in range(GRID_SIZE):
                    existing = d.get_pixel(x, y)
                    blended = (min(255, existing[0] + fc[0]),
                               min(255, existing[1] + fc[1]),
                               min(255, existing[2] + fc[2]))
                    d.set_pixel(x, y, blended)

        # --- EXTINCTION text visible for full duration ---
        if self.extinction_active:
            ext_alpha = min(1.0, self.flash_timer / 0.3) if self.flash_timer > 0 else 0.0
            if ext_alpha > 0:
                eb = int(255 * ext_alpha)
                d.draw_text_small(2, 1, "EXTINCTION", (eb, int(eb * 0.3), int(eb * 0.2)))

        # --- Generation counter (bottom-right, subtle) ---
        gen_str = f"G{self.generation}"
        d.draw_text_small(GRID_SIZE - len(gen_str) * 4 - 2, 60,
                          gen_str, (80, 80, 80))

        # --- Population count (bottom-left, subtle) ---
        pop_str = f"N{len(self.organisms)}"
        d.draw_text_small(2, 60, pop_str, (80, 80, 80))

        # --- HUD overlay (fading) ---
        if self.overlay_timer > 0 and not self.extinction_active:
            alpha = min(1.0, self.overlay_timer / 0.5)
            brightness = int(220 * alpha)
            oc = (brightness, brightness, brightness)
            for i, line in enumerate(self.overlay_lines):
                d.draw_text_small(2, 1 + i * 7, line, oc)

    def _draw_sparkline(self, d):
        """Draw fitness sparkline in rows 0-7."""
        sparkline_bg = (5, 5, 15)
        # Fill sparkline background
        for y in range(8):
            for x in range(GRID_SIZE):
                d.set_pixel(x, y, sparkline_bg)

        # Draw the sparkline
        history = self._fitness_history
        n = len(history)
        if n < 2:
            return

        # Map last 64 values to columns 0-63
        start = max(0, n - 64)
        for col in range(min(64, n)):
            idx = start + col
            if idx >= n:
                break
            val = history[idx]
            # Map fitness [0,1] to y position within rows 0-7
            # fitness 1.0 -> y=0 (top), fitness 0.0 -> y=7 (bottom)
            py = int(7 - val * 7)
            py = max(0, min(7, py))
            # Draw green dot
            d.set_pixel(col, py, (30, 220, 60))
            # Draw dim trail below
            for ty in range(py + 1, 8):
                d.set_pixel(col, ty, (8, 40, 12))

    def _draw_peak_indicators(self, d):
        """Draw shifting peak indicators (SHIFTING mode only)."""
        if not self._peak_trail:
            return

        # Current peak position: bright yellow downward triangle
        peak_x = int(_clamp(self._current_peak_x(), 0, GRID_SIZE - 1))
        # Triangle: 1px at y=9, 3px at y=10
        d.set_pixel(peak_x, 9, (255, 220, 40))
        for dx in range(-1, 2):
            px = peak_x + dx
            if 0 <= px < GRID_SIZE:
                d.set_pixel(px, 10, (255, 220, 40))

        # Trail dots: last 8 peak positions, fading brightness
        trail_len = len(self._peak_trail)
        for i, px_val in enumerate(self._peak_trail):
            # Brightness decays from 60% (newest) to 10% (oldest)
            if trail_len <= 1:
                frac = 0.6
            else:
                frac = 0.1 + 0.5 * (i / (trail_len - 1))
            brightness = int(255 * frac)
            tx = int(_clamp(px_val, 0, GRID_SIZE - 1))
            d.set_pixel(tx, 9, (brightness, int(brightness * 0.86), int(brightness * 0.16)))

    def _draw_density_histogram(self, d, landscape_y):
        """Draw mini bar chart at rows 56-59."""
        # Bin organisms into x buckets and track average fitness per column
        density = [0] * GRID_SIZE
        fitness_sum = [0.0] * GRID_SIZE
        for org in self.organisms:
            bx = int(_clamp(org[0], 0, GRID_SIZE - 1))
            density[bx] += 1
            fitness_sum[bx] += org[1]
        max_density = max(max(density), 1)

        for x in range(GRID_SIZE):
            if density[x] > 0:
                # Bar height: 0-4px, mapped proportionally
                bar_h = min(4, max(1, int(density[x] / max_density * 4 + 0.5)))
                # Average fitness in this column
                avg_fit = fitness_sum[x] / density[x]
                # Color: low fitness = warm orange, high fitness = bright cyan
                r = int(255 * (1.0 - avg_fit) + 40 * avg_fit)
                g = int(120 * (1.0 - avg_fit) + 230 * avg_fit)
                b = int(20 * (1.0 - avg_fit) + 255 * avg_fit)
                for dy in range(bar_h):
                    d.set_pixel(x, 59 - dy, (r, g, b))

    def _draw_organisms(self, d, landscape_y):
        """Draw organisms as multi-pixel figures on the landscape."""
        # Sort organisms into columns for stacking
        columns = {}  # x_int -> list of (fitness, hue)
        for org in self.organisms:
            bx = int(_clamp(org[0], 0, GRID_SIZE - 1))
            if bx not in columns:
                columns[bx] = []
            columns[bx].append((org[1], org[2]))  # fitness, hue

        # Determine top-20% fitness threshold
        all_fits = [org[1] for org in self.organisms]
        if all_fits:
            sorted_fits = sorted(all_fits, reverse=True)
            top20_idx = max(0, len(sorted_fits) // 5 - 1)
            top20_threshold = sorted_fits[top20_idx]
        else:
            top20_threshold = 1.0

        for bx, org_list in columns.items():
            surface_y = landscape_y[bx]
            # Sort by fitness descending so fittest draw on top (closest to surface)
            org_list.sort(key=lambda o: o[0], reverse=True)
            # Cap visible organisms at 4 per column
            visible = org_list[:4]

            stack_offset = 0
            for fit, hue in visible:
                base_color = _organism_color(fit)
                color = _apply_hue_tint(base_color, hue)

                is_elite = fit >= top20_threshold

                # Body pixel (at surface - 1 - offset)
                body_y = surface_y - 1 - stack_offset
                if 0 <= body_y < GRID_SIZE:
                    d.set_pixel(bx, body_y, color)

                # Head pixel (at surface - 2 - offset)
                head_y = surface_y - 2 - stack_offset
                if 0 <= head_y < GRID_SIZE:
                    # Slightly brighter head
                    head_color = (min(255, color[0] + 20),
                                  min(255, color[1] + 20),
                                  min(255, color[2] + 20))
                    d.set_pixel(bx, head_y, head_color)

                # Antenna pixel for elite organisms (top 20%)
                if is_elite:
                    ant_y = surface_y - 3 - stack_offset
                    if 0 <= ant_y < GRID_SIZE:
                        ant_color = (min(255, color[0] + 40),
                                     min(255, color[1] + 40),
                                     min(255, color[2] + 40))
                        d.set_pixel(bx, ant_y, ant_color)
                    # Each elite organism takes 3 pixels of space
                    stack_offset += 3
                else:
                    # Each normal organism takes 2 pixels of space
                    stack_offset += 2

    def _draw_death_particles(self, d):
        """Draw falling death particles during extinction phase 2."""
        for p in self.death_particles:
            px, py, age = int(p[0]), int(p[1]), p[2]
            if 0 <= px < GRID_SIZE and 0 <= py < GRID_SIZE:
                # Fade from red to dark over the 0.6s phase
                fade = max(0.0, 1.0 - age / 0.6)
                r = int(200 * fade)
                g = int(30 * fade)
                b = int(20 * fade)
                if r > 0 or g > 0 or b > 0:
                    d.set_pixel(px, py, (r, g, b))
